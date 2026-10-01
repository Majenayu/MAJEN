# StudyStreak power

Data lives on the user's machine in `~/.studystreak/data.json` (or `STUDYSTREAK_DATA`).
The MCP tools read and write that same file, so sessions logged through Kiro also show
up in the `studystreak` CLI and the local web UI at http://127.0.0.1:8765.

Tools:
| Tool | Use for |
|---|---|
| `log_session` | Recording a session (subject, minutes, optional date and note) |
| `list_sessions` | Reviewing recent sessions, optionally one subject |
| `get_stats` | Totals, per-subject minutes, current and longest streak, weekly goal |
| `daily_breakdown` | Minutes per day over the last N days |
| `set_weekly_goal` | Setting or clearing the weekly goal, only on explicit request |

Validation (enforced by the server, explain it if a call fails):
subject 1-60 chars, minutes 1-1440, date not in the future, note up to 200 chars,
weekly goal 1-10080 minutes.
