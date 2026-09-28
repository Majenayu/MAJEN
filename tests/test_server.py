import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from studystreak.server import make_server
from studystreak.store import Store


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "data.json")
        self.httpd = make_server(self.store, port=0)
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def request(self, method, path, body=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as res:
                text = res.read().decode()
                return res.status, (json.loads(text) if text and "json" in res.headers["Content-Type"] else text)
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode())

    def test_binds_localhost_only(self):
        self.assertEqual(self.httpd.server_address[0], "127.0.0.1")

    def test_index_page(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("StudyStreak", body)
        self.assertNotIn(".innerHTML", body)  # no HTML injection sinks

    def test_add_list_stats_delete(self):
        status, s = self.request("POST", "/api/sessions", {"subject": "Maths", "minutes": 25})
        self.assertEqual(status, 201)
        status, items = self.request("GET", "/api/sessions")
        self.assertEqual((status, [i["id"] for i in items]), (200, [s["id"]]))
        status, st = self.request("GET", "/api/stats")
        self.assertEqual((st["total_minutes"], st["streak"]), (25, 1))
        status, _ = self.request("DELETE", f"/api/sessions/{s['id']}")
        self.assertEqual(status, 204)
        self.assertEqual(self.request("GET", "/api/sessions")[1], [])

    def test_validation_error_is_400(self):
        status, body = self.request("POST", "/api/sessions", {"subject": "", "minutes": 25})
        self.assertEqual(status, 400)
        self.assertIn("subject", body["error"])

    def test_bad_json_is_400(self):
        self.assertEqual(self.request("POST", "/api/sessions", raw=b"{oops")[0], 400)
        self.assertEqual(self.request("POST", "/api/sessions", body=[1, 2])[0], 400)

    def test_oversized_body_is_400(self):
        big = {"subject": "M", "minutes": 5, "note": "x" * 20000}
        self.assertEqual(self.request("POST", "/api/sessions", big)[0], 400)

    def test_set_and_clear_goal(self):
        self.request("POST", "/api/sessions", {"subject": "Maths", "minutes": 30})
        status, body = self.request("PUT", "/api/goal", {"minutes": 120})
        self.assertEqual((status, body), (200, {"weekly_goal": 120}))
        week = self.request("GET", "/api/stats")[1]["week"]
        self.assertEqual((week["minutes"], week["goal"], week["percent"]), (30, 120, 25))
        status, body = self.request("PUT", "/api/goal", {"minutes": None})
        self.assertEqual((status, body), (200, {"weekly_goal": None}))
        self.assertIsNone(self.request("GET", "/api/stats")[1]["week"]["percent"])

    def test_invalid_goal_is_400(self):
        self.assertEqual(self.request("PUT", "/api/goal", {"minutes": 0})[0], 400)
        self.assertEqual(self.request("PUT", "/api/goal", {})[0], 400)
        self.assertEqual(self.request("PUT", "/api/nope", {"minutes": 5})[0], 404)

    def test_unknown_delete_and_path_are_404(self):
        self.assertEqual(self.request("DELETE", "/api/sessions/missing")[0], 404)
        self.assertEqual(self.request("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
