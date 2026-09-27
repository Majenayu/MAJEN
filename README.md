# StudyStreak

A small, local-first study-session tracker. Log what you studied and for how long,
then see totals per subject and your daily streak, from a CLI or a local web page.
Python 3.10+, standard library only.

## Run

```powershell
# CLI
python -m studystreak add "Maths" 45 --note "calculus"
python -m studystreak add "Physics" 30 --date 2026-09-25
python -m studystreak list
python -m studystreak stats
python -m studystreak delete 02a799f8     # id or unique id prefix

# Web UI at http://127.0.0.1:8765
python -m studystreak serve
```

Data lives in `~/.studystreak/data.json`, or wherever `STUDYSTREAK_DATA` points.
The web server binds to 127.0.0.1 only and has no authentication, so don't expose it.

## Test

```powershell
python -m unittest discover -s tests -t . -v
```

## How Kiro was used

| Feature | Where |
|---|---|
| Steering | `.kiro/steering/` product, tech and structure rules (always + fileMatch) |
| Spec | `.kiro/specs/study-tracker/` requirements, design, tasks |
| Hooks | `.kiro/hooks/run-tests-on-save.json` runs tests on every `.py` save |
| MCP | `.kiro/settings/mcp.json` git server (`uvx mcp-server-git`), used by the reviewer agent |
| Custom agent | `.kiro/agents/code-reviewer.md` read-only reviewer |
| Skill | `.kiro/skills/add-api-endpoint/` repeatable workflow for new routes |

## Daily commit reminder

`scripts/commit-reminder.ps1` pops up a reminder at 20:00 if you haven't committed today.
It never commits for you, and it stops after the submission date.
