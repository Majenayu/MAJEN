---
inclusion: always
---

# Product: StudyStreak

StudyStreak is a small, local-first study-session tracker for students.

## Problem
Students lose track of how much they actually study and which subjects they neglect.

## Core features
- Log a study session: subject, minutes, optional note, date (defaults to today).
- See totals: overall minutes, minutes per subject, number of sessions.
- Streak: consecutive days (ending today or yesterday) with at least one session.
- Delete a mistaken session.
- Two interfaces over the same data: a CLI and a local web page.

## Non-goals
- No accounts, cloud sync, or multi-user support.
- No third-party dependencies.

## Principles
- Data stays on the user's machine in a single JSON file.
- Invalid input is rejected with a clear message, never silently stored.
