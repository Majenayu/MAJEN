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
