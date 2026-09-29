import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from studystreak.store import (Store, StoreError, ValidationError, compute_longest_streak,
                               compute_streak, make_session, validate_goal, week_start)

TODAY = date(2026, 9, 26)


class MakeSessionTests(unittest.TestCase):
    def test_defaults_to_today_and_trims(self):
        s = make_session("  Maths ", 45, today=TODAY)
        self.assertEqual((s.subject, s.minutes, s.date, s.note), ("Maths", 45, "2026-09-26", ""))
        self.assertEqual(len(s.id), 32)

    def test_explicit_date_and_string_minutes(self):
        s = make_session("Physics", "30", "2026-09-20", "waves", today=TODAY)
        self.assertEqual((s.minutes, s.date, s.note), (30, "2026-09-20", "waves"))

    def test_rejects_bad_subject(self):
        for bad in ["", "   ", None, 5, "x" * 61]:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                make_session(bad, 10, today=TODAY)

    def test_subject_length_boundary(self):
        self.assertEqual(len(make_session("x" * 60, 10, today=TODAY).subject), 60)

    def test_rejects_bad_minutes(self):
        for bad in [0, -1, 1441, 1.5, "abc", True, None]:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                make_session("Maths", bad, today=TODAY)

    def test_minutes_boundaries(self):
        self.assertEqual(make_session("M", 1, today=TODAY).minutes, 1)
        self.assertEqual(make_session("M", 1440, today=TODAY).minutes, 1440)

    def test_rejects_bad_dates(self):
        for bad in ["2026-13-01", "yesterday", "2026-09-27", 20260926]:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                make_session("Maths", 10, bad, today=TODAY)

    def test_rejects_long_note(self):
        with self.assertRaises(ValidationError):
            make_session("Maths", 10, note="n" * 201, today=TODAY)


class StreakTests(unittest.TestCase):
    def days(self, *offsets):
        return {TODAY - timedelta(days=o) for o in offsets}

    def test_empty(self):
        self.assertEqual(compute_streak(set(), TODAY), 0)

    def test_ending_today(self):
        self.assertEqual(compute_streak(self.days(0, 1, 2), TODAY), 3)

    def test_ending_yesterday_still_counts(self):
        self.assertEqual(compute_streak(self.days(1, 2), TODAY), 2)

    def test_gap_breaks_streak(self):
        self.assertEqual(compute_streak(self.days(0, 1, 3, 4), TODAY), 2)

    def test_stale_is_zero(self):
        self.assertEqual(compute_streak(self.days(2, 3), TODAY), 0)

    def test_longest_streak(self):
        self.assertEqual(compute_longest_streak(set()), 0)
        self.assertEqual(compute_longest_streak(self.days(0)), 1)
        # runs: 0-1 (2 days) and 5-8 (4 days); the older run is longer
        self.assertEqual(compute_longest_streak(self.days(0, 1, 5, 6, 7, 8)), 4)

    def test_longest_streak_in_stats_survives_broken_current_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "d.json")
            for d in ["2026-09-10", "2026-09-11", "2026-09-12"]:
                store.add("Maths", 10, d, today=TODAY)
            st = store.stats(today=TODAY)
            self.assertEqual((st["streak"], st["longest_streak"]), (0, 3))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "data.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_is_empty(self):
        self.assertEqual(Store(self.path).list(), [])

    def test_persistence_round_trip(self):
        store = Store(self.path)
        s = store.add("Maths", 45, "2026-09-25", "calc", today=TODAY)
        reloaded = Store(self.path)
        self.assertEqual(reloaded.sessions, [s])
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())
        self.assertEqual(json.loads(self.path.read_text())["version"], 1)

    def test_invalid_add_does_not_persist(self):
        store = Store(self.path)
        with self.assertRaises(ValidationError):
            store.add("", 10)
        self.assertFalse(self.path.exists())

    def test_list_newest_first(self):
        store = Store(self.path)
        store.add("A", 10, "2026-09-20", today=TODAY)
        store.add("B", 10, "2026-09-25", today=TODAY)
        self.assertEqual([s.subject for s in store.list()], ["B", "A"])

    def test_filter_by_subject_and_subjects(self):
        store = Store(self.path)
        store.add("Maths", 10, "2026-09-20", today=TODAY)
        store.add("physics", 10, "2026-09-21", today=TODAY)
        store.add("maths", 10, "2026-09-22", today=TODAY)
        self.assertEqual([s.date for s in store.list(" MATHS ")], ["2026-09-22", "2026-09-20"])
        self.assertEqual(store.list("Chemistry"), [])
        self.assertEqual(len(store.list("")), 3)
        self.assertEqual(store.subjects(), ["Maths", "physics"])

    def test_delete(self):
        store = Store(self.path)
        s = store.add("A", 10, today=TODAY)
        self.assertFalse(store.delete("nope"))
        self.assertTrue(store.delete(s.id))
        self.assertEqual(Store(self.path).sessions, [])

    def test_stats(self):
        store = Store(self.path)
        store.add("Maths", 30, "2026-09-26", today=TODAY)
        store.add("maths", 20, "2026-09-25", today=TODAY)
        store.add("Physics", 40, "2026-09-25", today=TODAY)
        st = store.stats(today=TODAY)
        self.assertEqual(st["total_minutes"], 90)
        self.assertEqual(st["sessions"], 3)
        self.assertEqual(st["by_subject"], [{"subject": "Maths", "minutes": 50},
                                            {"subject": "Physics", "minutes": 40}])
        self.assertEqual(st["streak"], 2)

    def test_corrupt_file_raises_and_is_not_overwritten(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json")
        with self.assertRaises(StoreError):
            Store(self.path)
        self.assertEqual(self.path.read_text(), "{not json")


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "data.json")

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        import csv as _csv
        return list(_csv.reader(self.store.export_csv().splitlines()))

    def test_empty_export_has_header_only(self):
        self.assertEqual(self.rows(), [["date", "subject", "minutes", "note", "id"]])

    def test_export_newest_first_and_escapes_commas_quotes(self):
        self.store.add("Maths", 30, "2026-09-20", 'limits, "epsilon"', today=TODAY)
        s = self.store.add("AIML", 45, "2026-09-25", today=TODAY)
        rows = self.rows()
        self.assertEqual(rows[1], ["2026-09-25", "AIML", "45", "", s.id])
        self.assertEqual(rows[2][3], 'limits, "epsilon"')

    def test_formula_injection_is_neutralised(self):
        self.store.add("=HYPERLINK(\"x\")", 10, note="+cmd", today=TODAY)
        self.store.add("-dash", 10, note="@sum", today=TODAY)
        cells = [c for row in self.rows()[1:] for c in row[1:4:2]]
        self.assertEqual(sorted(cells), sorted(["'=HYPERLINK(\"x\")", "'+cmd", "'-dash", "'@sum"]))


class GoalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "data.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_validate_goal(self):
        self.assertEqual(validate_goal(300), 300)
        self.assertEqual(validate_goal(" 60 "), 60)
        self.assertEqual(validate_goal(10080), 10080)
        self.assertIsNone(validate_goal(None))
        self.assertIsNone(validate_goal(""))
        for bad in [0, -5, 10081, 2.5, "lots", True]:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_goal(bad)

    def test_week_start_is_monday(self):
        self.assertEqual(week_start(TODAY), date(2026, 9, 21))       # Saturday -> Monday
        self.assertEqual(week_start(date(2026, 9, 21)), date(2026, 9, 21))
        self.assertEqual(week_start(date(2026, 9, 27)), date(2026, 9, 21))  # Sunday

    def test_set_goal_persists_and_clears(self):
        store = Store(self.path)
        store.set_goal(300)
        self.assertEqual(Store(self.path).weekly_goal, 300)
        store.set_goal(None)
        self.assertIsNone(Store(self.path).weekly_goal)

    def test_invalid_goal_keeps_old_goal(self):
        store = Store(self.path)
        store.set_goal(300)
        with self.assertRaises(ValidationError):
            store.set_goal(0)
        self.assertEqual(store.weekly_goal, 300)
        self.assertEqual(Store(self.path).weekly_goal, 300)

    def test_week_progress_counts_only_this_week(self):
        store = Store(self.path)
        store.add("Maths", 60, "2026-09-20", today=TODAY)   # previous Sunday, excluded
        store.add("Maths", 90, "2026-09-21", today=TODAY)   # Monday, included
        store.add("AIML", 30, "2026-09-26", today=TODAY)    # today, included
        self.assertEqual(store.week(TODAY),
                         {"start": "2026-09-21", "minutes": 120, "goal": None, "percent": None})
        store.set_goal(300)
        self.assertEqual(store.stats(TODAY)["week"]["percent"], 40)
        store.set_goal(100)
        self.assertEqual(store.week(TODAY)["percent"], 100)  # capped

    def test_old_file_without_goal_loads(self):
        self.path.write_text('{"version": 1, "sessions": []}')
        self.assertIsNone(Store(self.path).weekly_goal)

    def test_corrupt_goal_in_file_raises(self):
        self.path.write_text('{"version": 1, "sessions": [], "weekly_goal": -3}')
        with self.assertRaises(StoreError):
            Store(self.path)


if __name__ == "__main__":
    unittest.main()
