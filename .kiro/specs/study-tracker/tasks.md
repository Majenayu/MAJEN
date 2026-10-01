# Implementation plan

- [x] 1. Store and model
  - [x] 1.1 `Session` dataclass, `ValidationError`, `make_session` with all validation rules
    - _Requirements: 1.1-1.6_
  - [x] 1.2 `Store` load/save with atomic write and missing-file handling
    - _Requirements: 5.1-5.3_
  - [x] 1.3 `list`, `delete`
    - _Requirements: 2.1, 2.2, 3.1, 3.2_
  - [x] 1.4 `stats` and `compute_streak`
    - _Requirements: 4.1-4.3_
  - [x] 1.5 Unit tests in `tests/test_store.py`

- [x] 2. CLI
  - [x] 2.1 `add`, `list`, `delete`, `stats`, `serve` subcommands in `cli.py` and `__main__.py`
    - _Requirements: 1, 2, 3, 4_

- [x] 3. Web
  - [x] 3.1 JSON API in `server.py` bound to 127.0.0.1
    - _Requirements: 6.1, 6.3_
  - [x] 3.2 `static/index.html` UI using `textContent` only
    - _Requirements: 6.2, 6.4_
  - [x] 3.3 API tests in `tests/test_server.py`

- [x] 4. Tooling
  - [x] 4.1 README with run instructions
  - [x] 4.2 Daily commit reminder script (reminds only, never commits)

- [x] 5. Weekly goal
  - [x] 5.1 `Store.set_goal`, persisted `weekly_goal`, `week` block in `stats`
    - _Requirements: 7.1-7.4_
  - [x] 5.2 Unit tests for goal validation, clearing, persistence, week boundaries
  - [x] 5.3 `PUT /api/goal` route and API tests
    - _Requirements: 7.1-7.3_
  - [x] 5.4 CLI `goal` subcommand and weekly line in `stats`
    - _Requirements: 7.5_
  - [x] 5.5 Web UI goal form and progress bar
    - _Requirements: 7.5_

- [x] 6. CSV export
  - [x] 6.1 `sessions_to_csv` with formula-injection guard and `Store.export_csv`
    - _Requirements: 8.1-8.3_
  - [x] 6.2 Unit tests for header, ordering, escaping, injection guard
  - [x] 6.3 `GET /api/export.csv` route and API test
    - _Requirements: 8.4_
  - [x] 6.4 CLI `export [--out FILE]` and web download link
    - _Requirements: 8.4_

- [x] 7. Longest streak
  - [x] 7.1 `compute_longest_streak` and `longest_streak` in stats, with unit tests
    - _Requirements: 9.1, 9.2_
  - [x] 7.2 Show it in CLI `stats` and a web card
    - _Requirements: 9.3_

- [x] 8. Subject filter
  - [x] 8.1 `Store.list(subject)` and `Store.subjects()`, with unit tests
    - _Requirements: 10.1-10.3_
  - [x] 8.2 `GET /api/sessions?subject=` and `GET /api/subjects`, with API tests
    - _Requirements: 10.1-10.3_
  - [x] 8.3 CLI `list --subject` and web dropdown
    - _Requirements: 10.4_

- [x] 9. Demo data
  - [x] 9.1 `Store.seed_demo` (empty store only), with unit tests
    - _Requirements: 11.1-11.3_
  - [x] 9.2 CLI `demo [--days N]` and README demo instructions
    - _Requirements: 11.1_

- [x] 10. Edit a session
  - [x] 10.1 `Store.update` with field allow-list and re-validation, with unit tests
    - _Requirements: 12.1-12.4_
  - [x] 10.2 `PATCH /api/sessions/{id}` with API tests
    - _Requirements: 12.1-12.4_
  - [x] 10.3 CLI `edit` and web Edit / Cancel edit buttons
    - _Requirements: 12.5_

- [x] 11. Daily breakdown
  - [x] 11.1 `Store.daily(days)` zero-filled, validated 1..90, with unit tests
    - _Requirements: 13.1-13.3_
  - [x] 11.2 `GET /api/daily?days=` with API tests
    - _Requirements: 13.1-13.3_
  - [x] 11.3 CLI `daily` text chart and web "Last 7 days" table chart
    - _Requirements: 13.4_
