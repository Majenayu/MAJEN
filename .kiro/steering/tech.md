---
inclusion: always
---

# Tech stack and conventions

- Python 3.10+, standard library only. Do not add pip dependencies.
- Web server: `http.server` bound to `127.0.0.1` only. There is no auth, so never bind to `0.0.0.0`.
- Storage: one JSON file, path from `STUDYSTREAK_DATA` env var, default `~/.studystreak/data.json`.
  Writes go to a temp file and are atomically replaced.
- Tests: `unittest`, run with `python -m unittest discover -s tests -v`.
- Style: type hints on public functions, dataclasses for records, no global mutable state.
- Frontend: a single static `index.html` with vanilla JS. Render user text with
  `textContent`, never `innerHTML`, to avoid XSS.

## Commands
- Run tests: `python -m unittest discover -s tests -v`
- CLI: `python -m studystreak add "Maths" 45 --note "calculus"`
- Web UI: `python -m studystreak serve` then open http://127.0.0.1:8765
