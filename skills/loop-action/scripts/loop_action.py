#!/usr/bin/env python3
"""Check and queue the loop-action block that each scheduled agent report ends with.

Standard library only. Reads reports, writes nothing, calls no network.
"""
import argparse
import datetime as dt
import pathlib
import re
import sys

BLOCK = re.compile(r"^[ \t]*```loop-action[ \t]*\n(.*?)^[ \t]*```", re.S | re.M)
REQUIRED = ("date", "action", "owner", "effort", "horizon_days", "consumer", "artifact")
MAX_WORDS = 20


def blocks(text):
    out = []
    for raw in BLOCK.findall(text):
        fields = {}
        for line in raw.splitlines():
            key, sep, value = line.strip().partition(":")
            if sep:
                fields[key.strip()] = value.strip()
        out.append(fields)
    return out


def problems(path, root):
    """Return (fields, list of problems) for one report."""
    found = blocks(path.read_text(encoding="utf-8", errors="replace"))
    if len(found) != 1:
        return {}, [f"needs exactly one loop-action block, found {len(found)}"]
    f = found[0]
    idle = f.get("action", "").lower() == "none"
    required = ("date", "action", "consumer") if idle else REQUIRED
    errs = [f"missing field: {k}" for k in required if not f.get(k)]
    if f.get("date"):
        try:
            dt.date.fromisoformat(f["date"])
        except ValueError:
            errs.append("date must be YYYY-MM-DD")
    if idle:
        return f, errs
    if len(f.get("action", "").split()) >= MAX_WORDS:
        errs.append(f"action must be under {MAX_WORDS} words")
    if f.get("owner") and f["owner"] not in ("human", "agent"):
        errs.append("owner must be human or agent")
    if f.get("horizon_days") and not re.fullmatch(r"[1-9][0-9]{0,3}", f["horizon_days"]):
        errs.append("horizon_days must be a whole number from 1 to 9999")
    target = f.get("artifact", "").split("#")[0]
    if target and not (root / target).exists():
        errs.append(f"artifact does not exist: {target}")
    return f, errs


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("command", choices=("check", "queue"))
    p.add_argument("reports", nargs="+", type=pathlib.Path)
    p.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."),
                   help="folder that artifact paths are relative to")
    p.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    args = p.parse_args(argv)

    bad = 0
    live, expired = [], []
    for path in args.reports:
        if not path.is_file():
            fields, errs = {}, ["report not found"]
        else:
            fields, errs = problems(path, args.root)
        if errs:
            bad += 1
            for e in errs:
                print(f"FAIL {path}: {e}")
            continue
        if args.command == "check":
            print(f"ok   {path}")
        elif fields["action"].lower() != "none":
            age = (args.today - dt.date.fromisoformat(fields["date"])).days
            late = age > int(fields["horizon_days"]) * 3
            (expired if late else live).append((age, fields))

    if args.command == "queue":
        for title, rows in (("Open", live), ("Expired", expired)):
            print(f"{title} ({len(rows)})")
            for age, f in sorted(rows, key=lambda r: -r[0]):
                print(f"  {age:>3}d  {f['owner']:<5}  {f['effort']:<4}  {f['action']}")
                print(f"        -> {f['artifact']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
