# StudyStreak

A small, local-first study-session tracker. Log what you studied and for how long, then see
totals per subject, your daily and longest streak, weekly goal progress and a 7-day chart.
Use it from a CLI, a local web page, or by chatting with Kiro through its MCP server.
The app is Python 3.10+, standard library only.

## Run

```powershell
pip install -e .                 # optional: adds `studystreak` and `studystreak-mcp` commands

# CLI
python -m studystreak add "Maths" 45 --note "calculus"
python -m studystreak add "Physics" 30 --date 2026-09-25
python -m studystreak subject "Maths"     # detailed stats for one subject
python -m studystreak summary             # one-screen overview of everything
python -m studystreak summary --json      # same data as JSON (also: stats --json)
python -m studystreak stats              # includes this week's progress
python -m studystreak daily --days 7     # minutes per day, text bar chart
python -m studystreak goal 300           # weekly goal in minutes
python -m studystreak goal --clear
python -m studystreak export --out sessions.csv   # or omit --out to print
python -m studystreak edit 02a799f8 --minutes 50 --note "fixed"
python -m studystreak delete 02a799f8     # id or unique id prefix

# Web UI at http://127.0.0.1:8765
python -m studystreak serve
```

### Demo with sample data

```powershell
$env:STUDYSTREAK_DATA = "$env:TEMP\studystreak-demo.json"   # keep demo data separate
python -m studystreak demo
python -m studystreak serve
```

`demo` only works on an empty store, so it never mixes with your real sessions.

Data lives in `~/.studystreak/data.json`, or wherever `STUDYSTREAK_DATA` points.
The web server binds to 127.0.0.1 only and has no authentication, so don't expose it.

## Use it from Kiro (MCP)

`studystreak-mcp` is an MCP server over stdio with five tools: `log_session`,
`list_sessions`, `get_stats`, `daily_breakdown` and `set_weekly_goal`. It reads and
writes the same data file as the CLI and web UI. Workspace config, `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "studystreak": {
      "command": "python",
      "args": ["-m", "studystreak.mcp_server"],
      "autoApprove": ["get_stats", "list_sessions", "daily_breakdown"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."],
      "autoApprove": ["git_status", "git_log", "git_diff_unstaged", "git_diff_staged", "git_show"]
    }
  }
}
```

Or install the packaged power in `powers/studystreak/` (see its README).

## Test

```powershell
pip install -r requirements-dev.txt     # Hypothesis, for property-based tests
python -m unittest discover -s tests -t . -v
```

## Troubleshooting

- **The `studystreak` MCP server shows as failed in Kiro.** Run `pip install -e .` in this
  folder first so the `studystreak` package is importable, then reconnect the server.
- **Demo data mixed with my real sessions.** The `demo` command only runs on an empty store.
  Point `STUDYSTREAK_DATA` at a separate file before running it, e.g.
  `$env:STUDYSTREAK_DATA = "$env:TEMP\studystreak-demo.json"`.
- **`git push` prints progress as red error text in PowerShell.** That is PowerShell flagging
  git's normal stderr output; the push still succeeds. Check with `git status` (should say
  your branch is up to date).

## How Kiro was used

| Lesson | Where |
|---|---|
| 1. Spec-driven development | `.kiro/specs/study-tracker/` 15 requirements, design, task list built in order |
| 2. Steering | `.kiro/steering/` product, tech (always) and structure (fileMatch) |
| 3. Hooks | `.kiro/hooks/run-tests-on-save.json` runs the suite on every `.py` save |
| 4. Property-based testing | `tests/test_properties.py`, 13 properties linked to requirements in design.md; found 2 real CSV bugs |
| 5. Powers | `powers/studystreak/` installed in Kiro and used to log sessions by chat |
| 6. MCP | `studystreak/mcp_server.py` (own server) + `git` server in `.kiro/settings/mcp.json` |
| 7. Custom agents | `.kiro/agents/code-reviewer.md` (read-only + git MCP) and `.kiro/agents/study-coach.md` (StudyStreak tools only, read tools pre-approved) |
| Bonus 2. Package a power | `powers/studystreak/` plugin.json, mcp.json, skill, steering |
| Extra | `.kiro/skills/add-api-endpoint/` workflow skill |

## Daily commit reminder

`scripts/commit-reminder.ps1` pops up a reminder at 20:00 if you haven't committed today.
It never commits for you, and it stops after the submission date.


.
