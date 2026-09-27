"""Local JSON API + static page. Bound to 127.0.0.1 only; there is no auth."""
from __future__ import annotations

import json
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .store import Store, ValidationError

HOST = "127.0.0.1"
MAX_BODY = 10 * 1024
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
            if self.path == "/":
                body = STATIC.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/sessions":
                with lock:
                    self._json(HTTPStatus.OK, [asdict(s) for s in store.list()])
            elif self.path == "/api/stats":
                with lock:
                    self._json(HTTPStatus.OK, store.stats())
            else:
                self._error(HTTPStatus.NOT_FOUND, "not found")

        def do_POST(self) -> None:
            if self.path != "/api/sessions":
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid Content-Length")
            if length <= 0 or length > MAX_BODY:
                return self._error(HTTPStatus.BAD_REQUEST, "body required, max 10 KB")
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._error(HTTPStatus.BAD_REQUEST, "body must be JSON")
            if not isinstance(data, dict):
                return self._error(HTTPStatus.BAD_REQUEST, "body must be a JSON object")
            try:
                with lock:
                    s = store.add(data.get("subject"), data.get("minutes"),
                                  data.get("date"), data.get("note", ""))
            except ValidationError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            self._json(HTTPStatus.CREATED, asdict(s))

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
