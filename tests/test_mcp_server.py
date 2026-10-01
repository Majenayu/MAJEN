import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from studystreak.mcp_server import TOOLS, McpServer
from studystreak.store import Store

ROOT = Path(__file__).resolve().parent.parent


class McpHandlerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "data.json"
        self.server = McpServer(lambda: Store(path))

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, name, arguments=None, msg_id=1):
        return self.server.handle({"jsonrpc": "2.0", "id": msg_id, "method": "tools/call",
                                   "params": {"name": name, "arguments": arguments or {}}})

    def payload(self, response):
        self.assertFalse(response["result"]["isError"], response)
        return json.loads(response["result"]["content"][0]["text"])

    def test_initialize_negotiates_version(self):
        r = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2024-11-05"}})
        self.assertEqual(r["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("tools", r["result"]["capabilities"])
        r = self.server.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                                "params": {"protocolVersion": "1999-01-01"}})
        self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")

    def test_notifications_get_no_response(self):
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_tools_list(self):
        r = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertEqual(names, [t["name"] for t in TOOLS])
        for t in r["result"]["tools"]:
            self.assertEqual(t["inputSchema"]["type"], "object")

    def test_log_then_stats_list_daily_goal(self):
        s = self.payload(self.call("log_session", {"subject": "AIML", "minutes": 40}))
        self.assertEqual(s["subject"], "AIML")
        self.assertEqual(self.payload(self.call("get_stats"))["total_minutes"], 40)
        self.assertEqual(len(self.payload(self.call("list_sessions", {"subject": "aiml"}))), 1)
        self.assertEqual(len(self.payload(self.call("daily_breakdown", {"days": 3}))), 3)
        self.assertEqual(self.payload(self.call("set_weekly_goal", {"minutes": 200})), {"weekly_goal": 200})
        self.assertEqual(self.payload(self.call("get_stats"))["week"]["percent"], 20)

    def test_tool_errors_are_reported_not_raised(self):
        for name, args in [("log_session", {"subject": "", "minutes": 5}),
                           ("log_session", {"subject": "X"}),
                           ("log_session", {"subject": "X", "minutes": 5, "id": "hack"}),
                           ("list_sessions", {"limit": 0}),
                           ("daily_breakdown", {"days": 500}),
                           ("set_weekly_goal", {})]:
            with self.subTest(name=name, args=args):
                r = self.call(name, args)
                self.assertTrue(r["result"]["isError"])
                self.assertTrue(r["result"]["content"][0]["text"].startswith("error:"))

    def test_protocol_errors(self):
        self.assertEqual(self.call("nope")["error"]["code"], -32602)
        r = self.server.handle({"jsonrpc": "2.0", "id": 9, "method": "resources/list"})
        self.assertEqual(r["error"]["code"], -32601)
        self.assertEqual(self.server.handle({"id": 1, "method": "ping"})["error"]["code"], -32600)
        self.assertEqual(self.server.handle([1, 2])["error"]["code"], -32600)


class McpStdioTests(unittest.TestCase):
    def test_end_to_end_over_stdio(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "STUDYSTREAK_DATA": str(Path(tmp) / "d.json"),
                   "PYTHONPATH": str(ROOT)}
            messages = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                            "clientInfo": {"name": "test", "version": "0"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "log_session", "arguments": {"subject": "Maths", "minutes": 25}}},
                "not json",
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "get_stats", "arguments": {}}},
            ]
            stdin = "\n".join(m if isinstance(m, str) else json.dumps(m) for m in messages) + "\n"
            proc = subprocess.run([sys.executable, "-m", "studystreak.mcp_server"], input=stdin,
                                  capture_output=True, text=True, encoding="utf-8",
                                  env=env, cwd=tmp, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            replies = [json.loads(line) for line in proc.stdout.splitlines()]
            self.assertEqual([r.get("id") for r in replies], [1, 2, None, 3])
            self.assertEqual(replies[2]["error"]["code"], -32700)
            stats = json.loads(replies[3]["result"]["content"][0]["text"])
            self.assertEqual(stats["total_minutes"], 25)


if __name__ == "__main__":
    unittest.main()
