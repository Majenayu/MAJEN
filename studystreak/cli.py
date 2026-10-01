"""argparse CLI: add, list, delete, stats, serve."""
from __future__ import annotations

import argparse
import sys

from .store import Store, StoreError, ValidationError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studystreak", description="Track study sessions and streaks.")
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="log a study session")
    add.add_argument("subject")
    add.add_argument("minutes")
    add.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    add.add_argument("--note", default="")

    ls = sub.add_parser("list", help="list sessions, newest first")
    ls.add_argument("--subject", help="only show this subject (case-insensitive)")

    rm = sub.add_parser("delete", help="delete a session by id (or unique id prefix)")
    rm.add_argument("id")

    ed = sub.add_parser("edit", help="edit a session by id (or unique id prefix)")
    ed.add_argument("id")
    ed.add_argument("--subject")
    ed.add_argument("--minutes")
    ed.add_argument("--date", help="YYYY-MM-DD")
    ed.add_argument("--note")

    sub.add_parser("stats", help="show totals, streak and weekly progress")

    subject_p = sub.add_parser("subject", help="show a summary for one subject")
    subject_p.add_argument("name")

    demo = sub.add_parser("demo", help="fill an empty store with sample data for demos")
    demo.add_argument("--days", type=int, default=14)

    exp = sub.add_parser("export", help="export sessions as CSV")
    exp.add_argument("--out", help="file to write; prints to stdout if omitted")

    daily = sub.add_parser("daily", help="minutes per day for recent days")
    daily.add_argument("--days", default="7", help="how many days, 1-90 (default 7)")

    goal = sub.add_parser("goal", help="set or clear the weekly goal in minutes")
    grp = goal.add_mutually_exclusive_group(required=True)
    grp.add_argument("minutes", nargs="?")
    grp.add_argument("--clear", action="store_true")

    srv = sub.add_parser("serve", help="run the local web UI")
    srv.add_argument("--port", type=int, default=8765)
    return p


def _resolve_id(store: Store, prefix: str) -> str | None:
    matches = [s.id for s in store.sessions if s.id.startswith(prefix)]
    return matches[0] if len(matches) == 1 else None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        store = Store()
    except StoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.command == "add":
        try:
            s = store.add(args.subject, args.minutes, args.date, args.note)
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"added {s.id[:8]}  {s.date}  {s.subject}  {s.minutes} min")
        return 0

    if args.command == "list":
        sessions = store.list(args.subject)
        if not sessions:
            print("no sessions yet")
        for s in sessions:
            note = f"  - {s.note}" if s.note else ""
            print(f"{s.id[:8]}  {s.date}  {s.subject:<20} {s.minutes:>4} min{note}")
        return 0

    if args.command == "delete":
        full = _resolve_id(store, args.id)
        if not full or not store.delete(full):
            print(f"error: no unique session matches {args.id!r}", file=sys.stderr)
            return 1
        print(f"deleted {full[:8]}")
        return 0

    if args.command == "edit":
        full = _resolve_id(store, args.id)
        if not full:
            print(f"error: no unique session matches {args.id!r}", file=sys.stderr)
            return 1
        changes = {k: v for k, v in (("subject", args.subject), ("minutes", args.minutes),
                                     ("date", args.date), ("note", args.note)) if v is not None}
        try:
            s = store.update(full, changes)
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"updated {s.id[:8]}  {s.date}  {s.subject}  {s.minutes} min")
        return 0

    if args.command == "stats":
        st = store.stats()
        print(f"total: {st['total_minutes']} min across {st['sessions']} sessions")
        print(f"streak: {st['streak']} day(s)  (longest: {st['longest_streak']})")
        wk = st["week"]
        if wk["goal"]:
            print(f"this week: {wk['minutes']} / {wk['goal']} min ({wk['percent']}%)")
        else:
            print(f"this week: {wk['minutes']} min (no goal set)")
        for e in st["by_subject"]:
            print(f"  {e['subject']:<20} {e['minutes']:>5} min")
        return 0

    if args.command == "subject":
        sm = store.subject_summary(args.name)
        if sm is None:
            print(f"no sessions for {args.name!r}", file=sys.stderr)
            return 1
        print(f"subject:        {sm['subject']}")
        print(f"sessions:       {sm['sessions']}")
        print(f"total minutes:  {sm['total_minutes']}")
        print(f"average/session:{sm['average_minutes']:.1f} min")
        print(f"streak:         {sm['streak']} day(s)")
        print(f"longest streak: {sm['longest_streak']} day(s)")
        print(f"first session:  {sm['first_date']}")
        print(f"last session:   {sm['last_date']}")
        return 0

    if args.command == "demo":
        try:
            n = store.seed_demo(days=args.days)
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            print("tip: point STUDYSTREAK_DATA at a new file to keep demo data separate",
                  file=sys.stderr)
            return 2
        print(f"added {n} demo session(s) to {store.path}")
        return 0

    if args.command == "export":
        text = store.export_csv()
        if args.out:
            # utf-8-sig so Excel detects the encoding correctly.
            with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
                fh.write(text)
            print(f"exported {len(store.sessions)} session(s) to {args.out}")
        else:
            # stdout is in text mode and translates "\n" itself; avoid "\r\r\n".
            sys.stdout.write(text.replace("\r\n", "\n"))
        return 0

    if args.command == "daily":
        try:
            rows = store.daily(args.days)
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        peak = max((r["minutes"] for r in rows), default=0) or 1
        for r in rows:
            bar = "#" * round(30 * r["minutes"] / peak)
            print(f"{r['date']}  {r['minutes']:>5} min  {bar}")
        return 0

    if args.command == "goal":
        try:
            g = store.set_goal(None if args.clear else args.minutes)
        except ValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"weekly goal set to {g} min" if g else "weekly goal cleared")
        return 0

    if args.command == "serve":
        from .server import serve
        serve(store, port=args.port)
        return 0

    return 1
