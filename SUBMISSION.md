# Kiro University final exam: submission guide

Deadline: Mon 5 Oct 2026, 23:59 PT = **Tue 6 Oct, 12:29 PM IST**.
After you submit, do not commit or push to this repo until 19 Oct.

## 1. Finish the two things only you can do (15 min)

### a. MCP config (Lesson 6)
Kiro blocks the agent from writing this file, so create `.kiro/settings/mcp.json` yourself:

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

Then in Kiro open the MCP Servers panel and check both show as connected.
If `studystreak` fails, run `pip install -e .` in this folder first.

### b. Install the power (Lesson 5)
1. Powers panel (Ghosty with lightning) -> Add Custom Power -> Import power from a folder.
2. Pick `powers/studystreak` and click Install.
3. In a new chat type: `I studied AIML for 40 minutes`. Kiro should call `log_session`.
4. Then: `how am I doing this week?` It should call `get_stats` and `daily_breakdown`.

Commit and push the config:
```powershell
git add .kiro/settings/mcp.json
git commit -m "Add workspace MCP config for StudyStreak and git servers"
git push
```

## 2. Record the demo video (2 min 30 s max)

Use Windows Game Bar (Win+Alt+R starts/stops) or OBS. Speak over it or add captions.
Prepare first:
```powershell
$env:STUDYSTREAK_DATA = "$env:TEMP\studystreak-demo.json"
Remove-Item $env:STUDYSTREAK_DATA -ErrorAction SilentlyContinue
python -m studystreak demo
python -m studystreak serve
```
Open http://127.0.0.1:8765 in a browser, and Kiro with the repo next to it.

| Time | Show | Say |
|---|---|---|
| 0:00-0:15 | Web page | "StudyStreak tracks study sessions, streaks and a weekly goal. Built with Kiro." |
| 0:15-0:40 | Add a session, edit it, filter by subject, Download CSV | "It runs locally: CLI, web UI, and an MCP server." |
| 0:40-0:55 | `.kiro/specs/study-tracker/requirements.md`, then tasks.md | "Lesson 1: every feature started as a requirement in the spec." |
| 0:55-1:05 | `.kiro/steering/tech.md` | "Lesson 2: steering keeps Kiro on stdlib-only, localhost-only, textContent." |
| 1:05-1:15 | Save a .py file, show the hook running tests | "Lesson 3: hooks run tests on save and check the spec after each task." |
| 1:15-1:35 | `tests/test_properties.py` + run it, design.md properties table | "Lesson 4: 13 properties from the requirements; they found two real CSV bugs." |
| 1:35-1:55 | Kiro chat: "I studied AIML for 40 minutes", web page refreshes | "Lessons 5 and 6: my own MCP server, packaged as a power." |
| 1:55-2:15 | Switch to `study-coach` agent: "how am I doing this week?" | "Lesson 7: a custom agent limited to StudyStreak tools, reads pre-approved." |
| 2:15-2:30 | `powers/studystreak/` folder | "Bonus 2: the power is packaged in the repo for anyone to install." |

Upload to YouTube as **Unlisted** (or Public). Open the link in a private window to
confirm it plays while signed out.

## 3. Social post

Post on LinkedIn (tag **@kiro**) or X (tag **@kirodotdev**). Paste the YouTube link so it
shows as a video. Template:

```
I built StudyStreak for the Kiro University Challenge: a local-first study tracker with
streaks, weekly goals and a 7-day chart, usable from a CLI, a web page, or by chatting with
Kiro. I wrote my own MCP server and packaged it as a Kiro power, so I can log study time
just by telling Kiro what I studied.

Repo: https://github.com/Majenayu/MAJEN
Demo: <YOUTUBE LINK>

Built with @kiro for the Kiro University Challenge 🎓
#KiroUniversity #BuildWithKiro
```
On X replace `@kiro` with `@kirodotdev` and shorten to fit. Check both hashtags and the tag
are present before posting; missing one can disqualify the entry.

## 4. Entry form (kiro.dev/2026/university -> Submit your final exam build)

- Email: the one you check. Credits are sent there.
- GitHub repo: https://github.com/Majenayu/MAJEN
- Demo video: your YouTube link
- Social post: link to your live post
- Description (2-3 sentences): reuse the first paragraph of the post.
- How each lesson was used:

```
Lesson 1 Specs: All 15 features were written as EARS requirements, a design and a task list in .kiro/specs/study-tracker before any code, and built task by task.
Lesson 2 Steering: product.md and tech.md (always) and structure.md (fileMatch) keep Kiro on stdlib-only code, 127.0.0.1 binding, atomic writes and textContent rendering.
Lesson 3 Hooks: run-tests-on-save runs the test suite on every .py save; spec-check-after-task makes Kiro verify tests and spec docs after each completed task.
Lesson 4 Property-based testing: tests/test_properties.py checks 13 correctness properties derived from the requirements with Hypothesis; it found two real CSV export bugs that are now fixed.
Lesson 5 Powers: I installed my StudyStreak power in Kiro and log and review study sessions by chatting; its keywords activate it on demand.
Lesson 6 MCP: I wrote studystreak/mcp_server.py, a stdio MCP server with five tools, and configured it plus the git MCP server in .kiro/settings/mcp.json.
Lesson 7 Custom agents: study-coach is limited to StudyStreak MCP tools with read tools pre-approved; code-reviewer is read-only and reviews diffs through the git MCP server.
Bonus 2 Package a power: powers/studystreak contains plugin.json, mcp.json, a study-coach skill and steering, installable from this repo.
```

Only claim Bonus 1 (Kiro Web / cloud sessions) if you actually open this project in Kiro Web
or a cloud session and show it in the video. It needs a paid plan.

## 5. Final checks, then stop

- [ ] `.kiro/settings/mcp.json` committed and pushed
- [ ] Video plays signed out, under 3 minutes
- [ ] Post is public with both hashtags and the right tag
- [ ] Form submitted with the correct email
- [ ] Reminder turned off: `Unregister-ScheduledTask -TaskName StudyStreakCommitReminder -Confirm:$false`
- [ ] No more commits until 19 Oct
