# StudyStreak Kiro power

Lets Kiro log your study sessions and coach you on streaks and weekly goals.

Contents:
- `plugin.json`: power manifest (name, description, activation keywords)
- `mcp.json`: the StudyStreak MCP server, run with `uvx` straight from this GitHub repo
- `skills/study-coach/SKILL.md`: how Kiro should log sessions and give check-ins
- `dev.kiro/steering/studystreak.md`: tool reference and validation rules

## Install
Requires [uv](https://docs.astral.sh/uv/) (for `uvx`) and Python 3.10+.

1. In Kiro, open the Powers panel and choose Add Custom Power.
2. Pick Import power from a folder and select this `powers/studystreak` folder,
   or Import power from GitHub with `https://github.com/Majenayu/MAJEN`.
3. Click Install, then say something like "log 45 minutes of maths" or "how is my study streak?".

## Try it
- "I studied AIML for 40 minutes"
- "How am I doing this week?"
- "Set my weekly study goal to 300 minutes"
