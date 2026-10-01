---
inclusion: fileMatch
fileMatchPattern: ["studystreak/**/*.py", "tests/**/*.py", "powers/**"]
---

# Project structure

```
studystreak/
  __main__.py    entry point for `python -m studystreak`
  store.py       Session model, validation, JSON persistence, stats and streak logic
  cli.py         argparse CLI (add, list, edit, delete, stats, daily, goal, export, demo, serve)
  server.py      http.server JSON API + serves static/index.html
  mcp_server.py  MCP server over stdio for Kiro (log_session, get_stats, ...)
  static/
    index.html   web UI
tests/
  test_store.py       example tests for validation, persistence, stats, streak
  test_server.py      API tests against a server on an ephemeral port
  test_mcp_server.py  MCP handler tests + end-to-end stdio test
  test_properties.py  property-based tests (Hypothesis), one per correctness property
powers/studystreak/   Kiro power: plugin.json, mcp.json, skills/, dev.kiro/steering/
scripts/
  commit-reminder.ps1 daily "did you commit real work?" reminder (never commits)
pyproject.toml        package metadata and the `studystreak-mcp` console script
```

Rules:
- All business logic lives in `store.py`. `cli.py`, `server.py` and `mcp_server.py` only
  parse input and format output.
- Every new behaviour in `store.py` gets a test in `tests/test_store.py`, and a property in
  `tests/test_properties.py` when it is a rule over all inputs.
- New MCP tools must be added to `TOOLS`, the power's steering table and design.md.
