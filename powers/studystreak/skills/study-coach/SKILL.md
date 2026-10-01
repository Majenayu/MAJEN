---
name: study-coach
description: Log study sessions and coach the user using their StudyStreak data. Use when the user mentions studying, logging study time, their streak, weekly study goal, or which subject they are neglecting.
---

# Study coach

Use the `studystreak` MCP tools. Never invent numbers; always read them from the tools.

## Logging
- "I studied X for N minutes" -> `log_session` with `subject` and `minutes`.
  Add `date` (YYYY-MM-DD) only if the user names a past day. Never log future dates.
- Confirm with one line: subject, minutes, date.

## Check-in ("how am I doing?")
1. `get_stats` for streak, longest streak and weekly progress.
2. `daily_breakdown` with `days: 7` to find zero-minute days.
3. Reply in at most 4 short lines:
   - current streak vs longest streak
   - this week's minutes vs goal (or suggest a goal if none)
   - the subject with the fewest minutes in `by_subject`
   - one concrete next step for today

## Goals
- Only call `set_weekly_goal` when the user explicitly asks to set or clear a goal.
- If a tool returns `isError`, show the error message and ask for corrected input.
