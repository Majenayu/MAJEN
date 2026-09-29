# Requirements: StudyStreak study tracker

## Introduction
A local tool for students to log study sessions and see totals and a daily streak,
usable from a CLI and a local web page.

## Requirement 1: Log a session
**User story:** As a student, I want to log what I studied and for how long, so that I can track my effort.

Acceptance criteria:
1. WHEN the user adds a session with a subject and minutes THEN the system SHALL store it with a unique id and today's date.
2. WHEN a date (YYYY-MM-DD) is provided THEN the system SHALL store that date instead of today.
3. IF the subject is empty or only whitespace THEN the system SHALL reject it with an error.
4. IF the subject is longer than 60 characters or the note longer than 200 characters THEN the system SHALL reject it.
5. IF minutes is not an integer between 1 and 1440 THEN the system SHALL reject it.
6. IF the date is invalid or in the future THEN the system SHALL reject it.

## Requirement 2: View sessions
**User story:** As a student, I want to list my sessions, so that I can review what I did.

Acceptance criteria:
1. WHEN the user lists sessions THEN the system SHALL return them newest date first.
2. WHEN no sessions exist THEN the system SHALL return an empty list without error.

## Requirement 3: Delete a session
**User story:** As a student, I want to delete a mistaken entry.

Acceptance criteria:
1. WHEN the user deletes an existing id THEN the system SHALL remove it and persist the change.
2. IF the id does not exist THEN the system SHALL report "not found" and change nothing.

## Requirement 4: Stats and streak
**User story:** As a student, I want totals and a streak, so that I stay motivated and spot neglected subjects.

Acceptance criteria:
1. The system SHALL report total minutes, session count, and minutes per subject (case-insensitive grouping, largest first).
2. The streak SHALL be the number of consecutive days with at least one session, ending today, or ending yesterday if nothing is logged today yet.
3. IF the most recent session is older than yesterday THEN the streak SHALL be 0.

## Requirement 5: Persistence
1. The system SHALL store data in a single JSON file at `STUDYSTREAK_DATA` or `~/.studystreak/data.json`.
2. Writes SHALL be atomic so a crash cannot leave a half-written file.
3. IF the file is missing THEN the system SHALL start with no sessions.

## Requirement 6: Web UI
1. WHEN the user runs `serve` THEN the system SHALL serve a page on 127.0.0.1 only.
2. The page SHALL allow adding, listing, deleting sessions and show stats and streak.
3. The JSON API SHALL return 400 with an error message for invalid input and 404 for unknown ids.
4. User-provided text SHALL be rendered as text, never as HTML.

## Requirement 7: Weekly goal
**User story:** As a student, I want to set a weekly study target in minutes, so that I can see whether I'm on track this week.

Acceptance criteria:
1. WHEN the user sets a goal between 1 and 10080 minutes THEN the system SHALL persist it.
2. IF the goal is not a whole number in that range THEN the system SHALL reject it and keep the old goal.
3. WHEN the user clears the goal THEN the system SHALL store no goal.
4. Stats SHALL include this week's minutes (Monday to Sunday containing today), the goal, and percent of goal reached (capped at 100, null when no goal).
5. The web page and CLI SHALL let the user set and clear the goal and SHALL show weekly progress.

## Requirement 8: CSV export
**User story:** As a student, I want to export my sessions to CSV, so that I can analyse them in a spreadsheet or back them up.

Acceptance criteria:
1. WHEN the user exports THEN the system SHALL produce CSV with header `date,subject,minutes,note,id` and one row per session, newest date first.
2. Commas, quotes and newlines in text SHALL be escaped per standard CSV rules.
3. IF a subject or note starts with `=`, `+`, `-`, `@`, tab or carriage return THEN the system SHALL prefix it with `'` to prevent spreadsheet formula injection.
4. The CLI SHALL print CSV to stdout or write it to a file with `--out`; the web page SHALL offer a download link.

## Requirement 9: Longest streak
**User story:** As a student, I want to see my best-ever streak, so that a broken streak doesn't erase my progress.

Acceptance criteria:
1. Stats SHALL include `longest_streak`: the longest run of consecutive days with a session, at any time.
2. WHEN there are no sessions THEN `longest_streak` SHALL be 0.
3. The CLI `stats` output and the web page SHALL show it.

## Requirement 10: Filter by subject
**User story:** As a student, I want to see sessions for one subject, so that I can review a single course.

Acceptance criteria:
1. WHEN a subject filter is given THEN the system SHALL list only sessions with that subject, case-insensitively, newest first.
2. WHEN the filter is empty THEN the system SHALL list all sessions.
3. The system SHALL expose the distinct subject names for building a filter control.
4. The CLI `list --subject` and a web dropdown SHALL apply the filter.

## Requirement 11: Demo data
**User story:** As a presenter, I want to fill the app with sample sessions, so that I can demo it without typing entries.

Acceptance criteria:
1. WHEN the user runs `demo` on an empty store THEN the system SHALL add sample sessions across several subjects over recent days, with gaps, and set a weekly goal.
2. IF the store already has sessions THEN the system SHALL refuse and change nothing.
3. IF `--days` is outside 1..60 THEN the system SHALL reject it.
