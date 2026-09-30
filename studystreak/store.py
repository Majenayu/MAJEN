"""Session model, validation, JSON persistence, stats and streak logic."""
from __future__ import annotations

import csv
import io
import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

MAX_SUBJECT = 60
MAX_NOTE = 200
MAX_MINUTES = 1440
MAX_WEEKLY_GOAL = 7 * 1440
FILE_VERSION = 1


class ValidationError(ValueError):
    """Raised when user input is rejected."""


class StoreError(RuntimeError):
    """Raised when the data file cannot be read safely."""


@dataclass
class Session:
    id: str
    subject: str
    minutes: int
    date: str
    note: str = ""


def default_path() -> Path:
    env = os.environ.get("STUDYSTREAK_DATA")
    return Path(env) if env else Path.home() / ".studystreak" / "data.json"


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f"invalid date {value!r}, expected YYYY-MM-DD") from None


def make_session(
    subject: object,
    minutes: object,
    date_str: object = None,
    note: object = "",
    today: date | None = None,
) -> Session:
    """Validate raw input and build a Session."""
    today = today or date.today()

    if not isinstance(subject, str) or not subject.strip():
        raise ValidationError("subject is required")
    subject = subject.strip()
    if len(subject) > MAX_SUBJECT:
        raise ValidationError(f"subject must be at most {MAX_SUBJECT} characters")

    # bool is a subclass of int; reject it explicitly.
    if isinstance(minutes, bool):
        raise ValidationError("minutes must be a whole number")
    if isinstance(minutes, str):
        try:
            minutes = int(minutes.strip())
        except ValueError:
            raise ValidationError("minutes must be a whole number") from None
    if not isinstance(minutes, int):
        raise ValidationError("minutes must be a whole number")
    if not 1 <= minutes <= MAX_MINUTES:
        raise ValidationError(f"minutes must be between 1 and {MAX_MINUTES}")

    if date_str in (None, ""):
        day = today
    elif isinstance(date_str, str):
        day = _parse_date(date_str)
    else:
        raise ValidationError("date must be a string in YYYY-MM-DD format")
    if day > today:
        raise ValidationError("date cannot be in the future")

    if note is None:
        note = ""
    if not isinstance(note, str):
        raise ValidationError("note must be text")
    note = note.strip()
    if len(note) > MAX_NOTE:
        raise ValidationError(f"note must be at most {MAX_NOTE} characters")

    return Session(id=uuid.uuid4().hex, subject=subject, minutes=minutes,
                   date=day.isoformat(), note=note)


def validate_goal(minutes: object) -> int | None:
    """Return a valid weekly goal in minutes, or None to clear it."""
    if minutes is None:
        return None
    if isinstance(minutes, bool):
        raise ValidationError("goal must be a whole number of minutes")
    if isinstance(minutes, str):
        text = minutes.strip()
        if text == "":
            return None
        try:
            minutes = int(text)
        except ValueError:
            raise ValidationError("goal must be a whole number of minutes") from None
    if not isinstance(minutes, int):
        raise ValidationError("goal must be a whole number of minutes")
    if not 1 <= minutes <= MAX_WEEKLY_GOAL:
        raise ValidationError(f"goal must be between 1 and {MAX_WEEKLY_GOAL} minutes")
    return minutes


def week_start(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())


CSV_FIELDS = ["date", "subject", "minutes", "note", "id"]
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Neutralise spreadsheet formula injection by prefixing risky cells with a quote."""
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def sessions_to_csv(sessions: list[Session]) -> str:
    """Render sessions as CSV text with a header row."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_FIELDS)
    for s in sessions:
        writer.writerow([s.date, _csv_safe(s.subject), s.minutes, _csv_safe(s.note), s.id])
    return buf.getvalue()


def compute_streak(days: set[date], today: date) -> int:
    """Consecutive days with a session, ending today or yesterday."""
    if today in days:
        cursor = today
    elif today - timedelta(days=1) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def compute_longest_streak(days: set[date]) -> int:
    """Longest run of consecutive days with at least one session, at any time."""
    best = 0
    for d in days:
        if d - timedelta(days=1) in days:
            continue  # not the start of a run
        length = 1
        while d + timedelta(days=length) in days:
            length += 1
        best = max(best, length)
    return best


class Store:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_path()
        self.sessions: list[Session] = []
        self.weekly_goal: int | None = None
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.sessions = []
            self.weekly_goal = None
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
            self.sessions = [Session(**s) for s in raw.get("sessions", [])]
            self.weekly_goal = validate_goal(raw.get("weekly_goal"))
        except (json.JSONDecodeError, TypeError, AttributeError, ValidationError) as exc:
            raise StoreError(f"data file {self.path} is corrupt: {exc}") from exc

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {"version": FILE_VERSION, "sessions": [asdict(s) for s in self.sessions],
                   "weekly_goal": self.weekly_goal}
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # atomic on the same filesystem

    def add(self, subject: object, minutes: object, date_str: object = None,
            note: object = "", today: date | None = None) -> Session:
        session = make_session(subject, minutes, date_str, note, today)
        self.sessions.append(session)
        self.save()
        return session

    def list(self, subject: str | None = None) -> list[Session]:
        """Sessions newest date first, optionally only one subject (case-insensitive)."""
        items = self.sessions
        if subject and subject.strip():
            key = subject.strip().casefold()
            items = [s for s in items if s.subject.casefold() == key]
        return sorted(items, key=lambda s: s.date, reverse=True)

    def subjects(self) -> list[str]:
        """Distinct subject names (first spelling seen), sorted case-insensitively."""
        seen: dict[str, str] = {}
        for s in self.sessions:
            seen.setdefault(s.subject.casefold(), s.subject)
        return sorted(seen.values(), key=str.casefold)

    EDITABLE_FIELDS = ("subject", "minutes", "date", "note")

    def update(self, session_id: str, changes: dict, today: date | None = None) -> Session | None:
        """Edit fields of an existing session. Returns None if the id is unknown.

        Only keys in EDITABLE_FIELDS are allowed; the merged result is re-validated with
        the same rules as a new session, and nothing is saved if validation fails.
        """
        unknown = set(changes) - set(self.EDITABLE_FIELDS)
        if unknown:
            raise ValidationError(f"cannot edit field(s): {', '.join(sorted(unknown))}")
        if not changes:
            raise ValidationError("nothing to change")
        for i, current in enumerate(self.sessions):
            if current.id != session_id:
                continue
            merged = {**asdict(current), **changes}
            fresh = make_session(merged["subject"], merged["minutes"], merged["date"],
                                 merged["note"], today=today)
            fresh.id = current.id
            self.sessions[i] = fresh
            self.save()
            return fresh
        return None

    def delete(self, session_id: str) -> bool:
        before = len(self.sessions)
        self.sessions = [s for s in self.sessions if s.id != session_id]
        if len(self.sessions) == before:
            return False
        self.save()
        return True

    def seed_demo(self, today: date | None = None, days: int = 14) -> int:
        """Fill an EMPTY store with sample sessions for demos. Returns sessions added.

        Refuses to touch a store that already has data so real history is never mixed
        with sample data.
        """
        if self.sessions:
            raise ValidationError("demo data can only be added to an empty store")
        if not 1 <= days <= 60:
            raise ValidationError("days must be between 1 and 60")
        today = today or date.today()
        subjects = ["Maths", "Physics", "AIML", "English"]
        added = 0
        for offset in range(days):
            if offset in (4, 9):  # leave gaps so current and longest streak differ
                continue
            day = today - timedelta(days=offset)
            subject = subjects[offset % len(subjects)]
            minutes = 20 + (offset * 7) % 50
            self.sessions.append(make_session(subject, minutes, day.isoformat(),
                                              "demo", today=today))
            added += 1
        self.weekly_goal = 300
        self.save()
        return added

    def export_csv(self) -> str:
        """All sessions as CSV, newest date first."""
        return sessions_to_csv(self.list())

    def set_goal(self, minutes: object) -> int | None:
        """Set (or clear with None) the weekly goal. Invalid input leaves the old goal."""
        self.weekly_goal = validate_goal(minutes)
        self.save()
        return self.weekly_goal

    def week(self, today: date | None = None) -> dict:
        today = today or date.today()
        start = week_start(today)
        end = start + timedelta(days=6)
        minutes = sum(s.minutes for s in self.sessions
                      if start <= date.fromisoformat(s.date) <= end)
        goal = self.weekly_goal
        percent = min(100, round(100 * minutes / goal)) if goal else None
        return {"start": start.isoformat(), "minutes": minutes, "goal": goal, "percent": percent}

    def stats(self, today: date | None = None) -> dict:
        today = today or date.today()
        by_subject: dict[str, dict] = {}
        for s in self.sessions:
            key = s.subject.casefold()
            entry = by_subject.setdefault(key, {"subject": s.subject, "minutes": 0})
            entry["minutes"] += s.minutes
        grouped = sorted(by_subject.values(), key=lambda e: (-e["minutes"], e["subject"].casefold()))
        days = {date.fromisoformat(s.date) for s in self.sessions}
        return {
            "total_minutes": sum(s.minutes for s in self.sessions),
            "sessions": len(self.sessions),
            "by_subject": grouped,
            "streak": compute_streak(days, today),
            "longest_streak": compute_longest_streak(days),
            "week": self.week(today),
        }
