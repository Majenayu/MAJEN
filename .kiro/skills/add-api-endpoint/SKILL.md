---
name: add-api-endpoint
description: Add a new JSON API endpoint to the StudyStreak server end to end (store logic, handler, test, UI). Use when asked to add or change an /api route.
---

# Add a StudyStreak API endpoint

Follow these steps in order. Do not skip the tests.

1. Business logic first. Add a method to `Store` in `studystreak/store.py`.
   Validate input by raising `ValidationError`. Accept an optional `today` parameter
   if the logic depends on the date.
2. Unit test it in `tests/test_store.py`, including at least one invalid-input case.
3. Route it in `studystreak/server.py` inside the matching `do_GET` / `do_POST` / `do_DELETE`.
   - Wrap store calls in `with lock:`.
   - Map `ValidationError` to 400 and missing records to 404 using `self._error`.
   - Keep request bodies under `MAX_BODY`.
4. API test in `tests/test_server.py` covering success and one error status.
5. UI (if user-facing): call it from `studystreak/static/index.html` via `api()`,
   render with `textContent`, and give new controls an accessible label.
6. Document the route in the API table in `.kiro/specs/study-tracker/design.md`.
7. Run `python -m unittest discover -s tests -t .` and confirm everything passes.
