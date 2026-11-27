import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "loop-action" / "scripts"))
import loop_action  # noqa: E402

GOOD = """```loop-action
date: 2026-01-15
action: Send the draft
owner: human
effort: 10m
horizon_days: 3
consumer: me
artifact: r.md#draft
```
"""


class LoopActionTest(unittest.TestCase):
    def run_on(self, text, command="check", today="2026-01-16"):
        with tempfile.TemporaryDirectory() as d:
            report = pathlib.Path(d, "r.md")
            report.write_text(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = loop_action.main([command, str(report), "--root", d, "--today", today])
            return code, out.getvalue()

    def test_good_block_passes(self):
        self.assertEqual(self.run_on(GOOD)[0], 0)

    def test_no_block_and_two_blocks_fail(self):
        self.assertEqual(self.run_on("# report")[0], 1)
        self.assertEqual(self.run_on(GOOD + GOOD)[0], 1)

    def test_missing_artifact_fails(self):
        self.assertIn("artifact does not exist", self.run_on(GOOD.replace("r.md#", "no.md#"))[1])

    def test_bad_fields_fail(self):
        for old, new in (("human", "bot"), ("days: 3", "days: soon"), ("2026-01-15", "today"),
                         ("Send the draft", "word " * 20), ("consumer: me\n", "")):
            self.assertEqual(self.run_on(GOOD.replace(old, new))[0], 1, new)

    def test_none_needs_only_date_and_consumer(self):
        text = "```loop-action\ndate: 2026-01-15\naction: none\nconsumer: me\n```\n"
        self.assertEqual(self.run_on(text)[0], 0)

    def test_expiry_is_after_three_horizons(self):
        self.assertIn("Open (1)", self.run_on(GOOD, "queue", "2026-01-24")[1])
        self.assertIn("Expired (1)", self.run_on(GOOD, "queue", "2026-01-25")[1])

    def test_indented_example_in_prose_is_counted(self):
        self.assertEqual(self.run_on("    " + GOOD.replace("\n", "\n    ") + "\n" + GOOD)[0], 1)


if __name__ == "__main__":
    unittest.main()
