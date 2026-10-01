---
inclusion: always
---

# Tech stack and conventions

- Python 3.10+. The app (`studystreak/`) uses the standard library only. Do not add runtime
  dependencies. The only dev dependency is Hypothesis, pinned in `requirements-dev.txt`
  and used only by `tests/test_properties.py`.
- Web server: `http.server` bound to `127.0.0.1` only. There is no auth, so never bind to `0.0.0.0`.
- MCP server: `studystreak/mcp_server.py`, JSON-RPC over stdio. Never print anything but
  protocol messages to stdout; diagnostics go to stderr.
- Storage: one JSON file, path from `STUDYSTREAK_DATA` env var, default `~/.studystreak/data.json`.
  Writes go to a temp file and are atomically replaced.
- Tests: `unittest`. Example tests for specific cases, property tests (Hypothesis) for rules
  that must hold for all inputs. Each property's docstring names the requirement it validates.
- Style: type hints on public functions, dataclasses for records, no global mutable state.
- Frontend: a single static `index.html` with vanilla JS. Render user text with
  `textContent`, never `innerHTML`, to avoid XSS.

## Commands
- Dev setup: `pip install -r requirements-dev.txt` then `pip install -e .`
- Run tests: `python -m unittest discover -s tests -t . -v`
- CLI: `python -m studystreak add "Maths" 45 --note "calculus"`
- Web UI: `python -m studystreak serve` then open http://127.0.0.1:8765
- MCP server: `studystreak-mcp` (or `python -m studystreak.mcp_server`)
