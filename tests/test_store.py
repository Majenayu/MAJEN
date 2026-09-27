import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from studystreak.store import (Store, StoreError, ValidationError, compute_streak,
                               make_session)

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


if __name__ == "__main__":
    unittest.main()
