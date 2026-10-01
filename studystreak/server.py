"""Local JSON API + static page. Bound to 127.0.0.1 only; there is no auth."""
from __future__ import annotations

import json
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .store import Store, ValidationError

HOST = "127.0.0.1"
MAX_BODY = 10 * 1024
MAX_DRAIN = 1024 * 1024  # never read more than this from a rejected request
STATIC = Path(__file__).parent / "static" / "index.html"


def make_handler(store: Store) -> type[BaseHTTPRequestHandler]:
    lock = threading.Lock()  # serialise writes to the shared store

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:  # keep test output clean
            pass

        def _json(self, status: int, payload: object) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, message: str) -> None:
            self._json(status, {"error": message})

        def do_GET(self) -> None:
            url = urlsplit(self.path)
            path = url.path
            if path == "/":
                body = STATIC.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/sessions":
                subject = parse_qs(url.query).get("subject", [None])[0]
                with lock:
                    self._json(HTTPStatus.OK, [asdict(s) for s in store.list(subject)])
            elif path == "/api/daily":
                days = parse_qs(url.query).get("days", ["7"])[0]
                try:
                    with lock:
                        result = store.daily(days)
                except ValidationError as exc:
                    return self._error(HTTPStatus.BAD_REQUEST, str(exc))
                self._json(HTTPStatus.OK, result)
            elif path == "/api/subjects":
                with lock:
                    self._json(HTTPStatus.OK, store.subjects())
            elif path == "/api/export.csv":
                with lock:
                    body = store.export_csv().encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="studystreak.csv"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/stats":
                with lock:
                    self._json(HTTPStatus.OK, store.stats())
            else:
                self._error(HTTPStatus.NOT_FOUND, "not found")

        def _read_json_object(self) -> dict | None:
            """Parse a JSON object body, or send a 400 and return None."""
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._error(HTTPStatus.BAD_REQUEST, "invalid Content-Length")
                return None
            if length <= 0 or length > MAX_BODY:
                # Drain a bounded amount of the unread body so the client receives the
                # 400 instead of a connection reset (seen on Windows), then close.
                if 0 < length <= MAX_DRAIN:
                    self.rfile.read(length)
                self.close_connection = True
                self._error(HTTPStatus.BAD_REQUEST, "body required, max 10 KB")
                return None
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._error(HTTPStatus.BAD_REQUEST, "body must be JSON")
                return None
            if not isinstance(data, dict):
                self._error(HTTPStatus.BAD_REQUEST, "body must be a JSON object")
                return None
            return data

        def do_PUT(self) -> None:
            if self.path != "/api/goal":
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            data = self._read_json_object()
            if data is None:
                return
            if "minutes" not in data:
                return self._error(HTTPStatus.BAD_REQUEST, "minutes is required (use null to clear)")
            try:
                with lock:
                    goal = store.set_goal(data["minutes"])
            except ValidationError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            self._json(HTTPStatus.OK, {"weekly_goal": goal})

        def do_POST(self) -> None:
            if self.path != "/api/sessions":
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            data = self._read_json_object()
            if data is None:
                return
            try:
                with lock:
                    s = store.add(data.get("subject"), data.get("minutes"),
                                  data.get("date"), data.get("note", ""))
            except ValidationError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            self._json(HTTPStatus.CREATED, asdict(s))

        def do_PATCH(self) -> None:
            prefix = "/api/sessions/"
            if not self.path.startswith(prefix) or len(self.path) == len(prefix):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            data = self._read_json_object()
            if data is None:
                return
            try:
                with lock:
                    s = store.update(self.path[len(prefix):], data)
            except ValidationError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            if s is None:
                return self._error(HTTPStatus.NOT_FOUND, "session not found")
            self._json(HTTPStatus.OK, asdict(s))

        def do_DELETE(self) -> None:
            prefix = "/api/sessions/"
            if not self.path.startswith(prefix) or len(self.path) == len(prefix):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            with lock:
                ok = store.delete(self.path[len(prefix):])
            if not ok:
                return self._error(HTTPStatus.NOT_FOUND, "session not found")
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()

    return Handler


def make_server(store: Store, port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((HOST, port), make_handler(store))


def serve(store: Store, port: int = 8765) -> None:
    httpd = make_server(store, port)
    print(f"StudyStreak running at http://{HOST}:{httpd.server_port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
