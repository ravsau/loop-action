# loop-action

**Make every scheduled agent report end with one next action.**

For people who run agents on cron or `/loop` and have reports piling up unread. A Claude Code skill and one Python script.

```text
FAIL examples/reports/2026-01-16.md: needs exactly one loop-action block, found 0
Open (1)
    3d  human  10m   Send the draft reply to the one open customer thread
        -> examples/reports/2026-01-15.md#draft
Expired (0)
```

## Install in Claude Code

```text
/plugin marketplace add ravsau/loop-action
/plugin install loop-action@loop-action
```

Then ask: `Add a loop-action block to my daily report job`.

## Try it without installing

You need Python 3.9 or later. The example reports are made-up data.

```bash
git clone https://github.com/ravsau/loop-action && cd loop-action
python3 skills/loop-action/scripts/loop_action.py queue examples/reports/*.md --today 2026-01-18
```

The command prints the output above and exits 1, because one example report names no next step.

## The block

```text
date: 2026-01-15
action: Send the draft reply to the one open customer thread
owner: human
effort: 10m
horizon_days: 3
consumer: me
artifact: examples/reports/2026-01-15.md#draft
```

Put those lines in a fenced block tagged `loop-action` at the end of the report.

| Check | Fails when |
|---|---|
| One block | a report has none, or more than one |
| Action | 20 words or more |
| Owner | not `human` or `agent` |
| Artifact | the file does not exist (the anchor is not checked) |
| Idle run | write `action: none` with `date` and `consumer` |

`queue` lists actions oldest first. An action expires after `horizon_days * 3`. The script keeps no state, so it cannot mark an action done.

The script reads the files you name, writes nothing and makes no network calls.

## Test

```bash
python3 tests/test_loop_action.py
```

## Want a hosted version?

If you want one page that collects open actions from all your agent jobs, [open this pre-filled issue](https://github.com/ravsau/loop-action/issues/new?title=I+want+a+hosted+version).

MIT License
