"""Property-based tests (Lesson 4).

Each test states a rule from .kiro/specs/study-tracker/requirements.md that must hold for
ALL inputs, and Hypothesis generates hundreds of random cases (shrinking any failure to a
minimal example). The properties are listed in the "Correctness properties" section of
design.md with the requirement each one validates.

Requires the dev dependency in requirements-dev.txt. If Hypothesis is not installed these
tests are skipped so the stdlib-only app and its example tests still run.
"""
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    raise unittest.SkipTest("hypothesis not installed: pip install -r requirements-dev.txt")

from studystreak.store import (MAX_MINUTES, MAX_NOTE, MAX_SUBJECT, Session, Store,
                               ValidationError, compute_longest_streak, compute_streak,
                               make_session)

TODAY = date(2026, 9, 26)
# database=None: no .hypothesis/ folder in the repo; failures still shrink and print.
PBT = settings(max_examples=150, deadline=None, database=None,
               suppress_health_check=[HealthCheck.too_slow])

# ---- strategies -------------------------------------------------------------
printable = st.characters(exclude_categories=("Cs", "Cc"))
subjects = st.text(printable, min_size=1, max_size=MAX_SUBJECT).filter(lambda s: s.strip())
notes = st.text(st.characters(exclude_categories=("Cs", "Cc"), include_characters="\t\n\r"),
                max_size=MAX_NOTE)
control_chars = st.characters(categories=("Cc",)).filter(lambda c: c not in "\t\n\r")
minutes = st.integers(min_value=1, max_value=MAX_MINUTES)
past_dates = st.dates(min_value=date(2026, 1, 1), max_value=TODAY)
any_dates = st.dates(min_value=date(2025, 12, 1), max_value=TODAY + timedelta(days=30))


@st.composite
def sessions(draw) -> Session:
    return make_session(draw(subjects), draw(minutes), draw(past_dates).isoformat(),
                        draw(notes), today=TODAY)


session_lists = st.lists(sessions(), max_size=25)


def store_with(tmp: str, items: list[Session], goal: int | None = None) -> Store:
    store = Store(Path(tmp) / "data.json")
    store.sessions = list(items)
    store.weekly_goal = goal
    store.save()
    return store


def reference_streak(days: set[date], today: date) -> int:
    """Obviously-correct, slow version of the streak rule (Requirement 4.2-4.3)."""
    for end in (today, today - timedelta(days=1)):
        if end in days:
            n = 0
            while end - timedelta(days=n) in days:
                n += 1
            return n
    return 0


class ValidationProperties(unittest.TestCase):
    @PBT
    @given(subjects, minutes, past_dates, notes)
    def test_valid_input_is_accepted_and_normalised(self, subject, mins, day, note):
        """P1 (Req 1.1-1.2): any in-range input is stored trimmed with its exact values."""
        s = make_session(subject, mins, day.isoformat(), note, today=TODAY)
        self.assertEqual((s.subject, s.minutes, s.date, s.note),
                         (subject.strip(), mins, day.isoformat(), note.strip()))

    @PBT
    @given(st.one_of(st.integers(max_value=0), st.integers(min_value=MAX_MINUTES + 1)))
    def test_out_of_range_minutes_always_rejected(self, mins):
        """P2 (Req 1.5): minutes outside 1..1440 are never accepted."""
        with self.assertRaises(ValidationError):
            make_session("Maths", mins, today=TODAY)

    @PBT
    @given(subjects, control_chars, st.integers(min_value=0, max_value=60))
    def test_control_characters_always_rejected(self, text, ch, pos):
        """P2b (Req 1.7): a control character anywhere in subject or note is rejected."""
        pos = min(pos, len(text))
        dirty = (text[:pos] + ch + text[pos:])[:MAX_SUBJECT]
        if ch not in dirty.strip():
            # Truncation dropped it, or str.strip() removes it as whitespace (e.g. \x1c-\x1f
            # at either end), so it can never be stored; nothing to reject.
            return
        with self.assertRaises(ValidationError):
            make_session(dirty, 10, today=TODAY)
        with self.assertRaises(ValidationError):
            make_session("Maths", 10, note=dirty, today=TODAY)

    @PBT
    @given(st.dates(min_value=TODAY + timedelta(days=1), max_value=date(2100, 1, 1)))
    def test_future_dates_always_rejected(self, day):
        """P3 (Req 1.6): a date after today is never accepted."""
        with self.assertRaises(ValidationError):
            make_session("Maths", 10, day.isoformat(), today=TODAY)

    @PBT
    @given(session_lists, sessions(), st.sampled_from([
        {"minutes": 0}, {"minutes": MAX_MINUTES + 1}, {"subject": "  "},
        {"date": (TODAY + timedelta(days=1)).isoformat()}, {"id": "x"}, {}]))
    def test_invalid_edit_never_changes_data(self, others, target, bad_change):
        """P4 (Req 12.2, 12.4): a rejected edit leaves every session and the file unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            store = store_with(tmp, others + [target])
            before = [*store.sessions]
            with self.assertRaises(ValidationError):
                store.update(target.id, bad_change, today=TODAY)
            self.assertEqual(store.sessions, before)
            self.assertEqual(Store(store.path).sessions, before)


class PersistenceProperties(unittest.TestCase):
    @PBT
    @given(session_lists, st.one_of(st.none(), st.integers(min_value=1, max_value=10080)))
    def test_save_load_round_trip(self, items, goal):
        """P5 (Req 5.1-5.2, 7.1): whatever is saved loads back identically."""
        with tempfile.TemporaryDirectory() as tmp:
            store = store_with(tmp, items, goal)
            reloaded = Store(store.path)
            self.assertEqual(reloaded.sessions, items)
            self.assertEqual(reloaded.weekly_goal, goal)
            self.assertFalse(store.path.with_suffix(".json.tmp").exists())


class StatsProperties(unittest.TestCase):
    @PBT
    @given(session_lists)
    def test_totals_are_consistent(self, items):
        """P6 (Req 4.1): total = sum of sessions = sum of per-subject totals."""
        with tempfile.TemporaryDirectory() as tmp:
            st_ = store_with(tmp, items).stats(today=TODAY)
            self.assertEqual(st_["sessions"], len(items))
            self.assertEqual(st_["total_minutes"], sum(s.minutes for s in items))
            self.assertEqual(sum(e["minutes"] for e in st_["by_subject"]), st_["total_minutes"])
            keys = [e["subject"].casefold() for e in st_["by_subject"]]
            self.assertEqual(len(keys), len(set(keys)))  # grouped case-insensitively
            mins = [e["minutes"] for e in st_["by_subject"]]
            self.assertEqual(mins, sorted(mins, reverse=True))

    @PBT
    @given(st.sets(any_dates, max_size=40), st.dates(min_value=date(2026, 1, 1), max_value=TODAY))
    def test_streak_matches_reference_and_never_exceeds_longest(self, days, today):
        """P7 (Req 4.2-4.3, 9.1): streak equals the reference rule and is <= longest streak."""
        days = {d for d in days if d <= today}
        streak = compute_streak(days, today)
        self.assertEqual(streak, reference_streak(days, today))
        self.assertLessEqual(streak, compute_longest_streak(days))
        self.assertLessEqual(compute_longest_streak(days), len(days))

    @PBT
    @given(st.sets(past_dates, max_size=30))
    def test_studying_today_never_lowers_streak(self, days):
        """P8 (Req 4.2): logging a session today can only keep or grow the streak."""
        self.assertGreaterEqual(compute_streak(days | {TODAY}, TODAY), compute_streak(days, TODAY))
        self.assertGreaterEqual(compute_streak(days | {TODAY}, TODAY), 1)

    @PBT
    @given(session_lists, st.one_of(st.none(), st.integers(min_value=1, max_value=10080)))
    def test_weekly_percent_is_bounded(self, items, goal):
        """P9 (Req 7.4): percent is None without a goal, otherwise within 0..100."""
        with tempfile.TemporaryDirectory() as tmp:
            week = store_with(tmp, items, goal).week(TODAY)
            if goal is None:
                self.assertIsNone(week["percent"])
            else:
                self.assertTrue(0 <= week["percent"] <= 100)

    @PBT
    @given(session_lists, st.integers(min_value=1, max_value=90))
    def test_daily_covers_window_exactly(self, items, n):
        """P10 (Req 13.1-13.2): N consecutive days ending today; minutes match the window."""
        with tempfile.TemporaryDirectory() as tmp:
            rows = store_with(tmp, items).daily(n, today=TODAY)
            self.assertEqual(len(rows), n)
            self.assertEqual(rows[-1]["date"], TODAY.isoformat())
            for a, b in zip(rows, rows[1:]):
                self.assertEqual(date.fromisoformat(b["date"]) - date.fromisoformat(a["date"]),
                                 timedelta(days=1))
            start = TODAY - timedelta(days=n - 1)
            expected = sum(s.minutes for s in items if start <= date.fromisoformat(s.date) <= TODAY)
            self.assertEqual(sum(r["minutes"] for r in rows), expected)


class ListAndExportProperties(unittest.TestCase):
    @PBT
    @given(session_lists)
    def test_filters_partition_the_list(self, items):
        """P11 (Req 2.1, 10.1-10.3): lists are newest first and subject filters partition them."""
        with tempfile.TemporaryDirectory() as tmp:
            store = store_with(tmp, items)
            listed = store.list()
            self.assertEqual([s.date for s in listed], sorted((s.date for s in items), reverse=True))
            seen = []
            for name in store.subjects():
                part = store.list(name)
                self.assertTrue(all(s.subject.casefold() == name.casefold() for s in part))
                seen.extend(s.id for s in part)
            self.assertEqual(sorted(seen), sorted(s.id for s in items))

    @PBT
    @given(session_lists)
    def test_csv_round_trips_and_neutralises_formulas(self, items):
        """P12 (Req 8.1-8.3): CSV parses back to the same rows; risky cells get a ' prefix."""
        with tempfile.TemporaryDirectory() as tmp:
            text = store_with(tmp, items).export_csv()
        rows = list(csv.reader(io.StringIO(text, newline="")))
        self.assertEqual(rows[0], ["date", "subject", "minutes", "note", "id"])
        by_id = {s.id: s for s in items}
        self.assertEqual(sorted(r[4] for r in rows[1:]), sorted(by_id))
        for day, subject, mins, note, sid in rows[1:]:
            s = by_id[sid]
            self.assertEqual((day, mins), (s.date, str(s.minutes)))
            for cell, original in ((subject, s.subject), (note, s.note)):
                risky = original.startswith(("=", "+", "-", "@", "\t", "\r"))
                self.assertEqual(cell, "'" + original if risky else original)


if __name__ == "__main__":
    unittest.main()
