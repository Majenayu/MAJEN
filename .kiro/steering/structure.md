---
inclusion: fileMatch
fileMatchPattern: ["studystreak/**/*.py", "tests/**/*.py"]
---

# Project structure

```
studystreak/
  __main__.py   entry point for `python -m studystreak`
  store.py      Session model, validation, JSON persistence, stats and streak logic
  cli.py        argparse CLI (add, list, delete, stats, serve)
  server.py     http.server JSON API + serves static/index.html
  static/
    index.html  web UI
tests/
  test_store.py   unit tests for validation, persistence, stats, streak
  test_server.py  API tests against a server on an ephemeral port
scripts/
  commit-reminder.ps1  daily "did you commit real work?" reminder (never commits)
```

Rules:
- All business logic lives in `store.py`. `cli.py` and `server.py` only parse input and format output.
- Every new behaviour in `store.py` gets a test in `tests/test_store.py`.
