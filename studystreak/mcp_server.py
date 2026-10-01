"""StudyStreak MCP server: lets Kiro log and query study sessions.

Speaks the Model Context Protocol over stdio (JSON-RPC 2.0, one JSON message per line).
Standard library only. Business logic stays in store.py; this module only maps
tool calls to Store methods and formats results.

Run:  python -m studystreak.mcp_server     (or the `studystreak-mcp` console script)
Data: same file as the CLI and web UI (STUDYSTREAK_DATA or ~/.studystreak/data.json).
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any, Callable

from . import __version__
from .store import Store, StoreError, ValidationError

SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_LIST_LIMIT = 100

TOOLS: list[dict] = [
    {
        "name": "log_session",
        "description": "Log a study session. Date defaults to today (YYYY-MM-DD, not in the future).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "What was studied, 1-60 chars"},
                "minutes": {"type": "integer", "minimum": 1, "maximum": 1440},
                "date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                "note": {"type": "string", "description": "Optional, up to 200 chars"},
            },
            "required": ["subject", "minutes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_sessions",
        "description": "List study sessions newest first, optionally for one subject.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Case-insensitive subject filter"},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIST_LIMIT, "default": 20},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_stats",
        "description": "Totals, minutes per subject, current and longest streak, and weekly goal progress.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "daily_breakdown",
        "description": "Minutes studied per day for the last N days (1-90, default 7), oldest first.",
        "inputSchema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "minimum": 1, "maximum": 90, "default": 7}},
            "additionalProperties": False,
        },
    },
    {
        "name": "set_weekly_goal",
        "description": "Set the weekly study goal in minutes (1-10080), or null to clear it.",
        "inputSchema": {
            "type": "object",
            "properties": {"minutes": {"type": ["integer", "null"], "minimum": 1, "maximum": 10080}},
            "required": ["minutes"],
            "additionalProperties": False,
        },
    },
]
_TOOL_NAMES = {t["name"] for t in TOOLS}


class ToolError(Exception):
    """A tool call failed in a way the model should see (returned with isError)."""


def _limit(value: object) -> int:
    if value is None:
        return 20
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_LIST_LIMIT:
        raise ToolError(f"limit must be an integer between 1 and {MAX_LIST_LIMIT}")
    return value


class McpServer:
    def __init__(self, store_factory: Callable[[], Store] = Store) -> None:
        # A fresh Store per call so edits made in the CLI or web UI are always visible.
        self.store_factory = store_factory

    # -- tools ---------------------------------------------------------
    def call_tool(self, name: str, args: dict) -> Any:
        if name not in _TOOL_NAMES:
            raise ToolError(f"unknown tool: {name}")
        allowed = set(next(t for t in TOOLS if t["name"] == name)["inputSchema"]["properties"])
        extra = set(args) - allowed
        if extra:
            raise ToolError(f"unexpected argument(s): {', '.join(sorted(extra))}")
        store = self.store_factory()
        if name == "log_session":
            for key in ("subject", "minutes"):
                if key not in args:
                    raise ToolError(f"{key} is required")
            s = store.add(args["subject"], args["minutes"], args.get("date"), args.get("note", ""))
            return asdict(s)
        if name == "list_sessions":
            limit = _limit(args.get("limit"))
            return [asdict(s) for s in store.list(args.get("subject"))[:limit]]
        if name == "get_stats":
            return store.stats()
        if name == "daily_breakdown":
            return store.daily(args.get("days", 7))
        if name == "set_weekly_goal":
            if "minutes" not in args:
                raise ToolError("minutes is required (null clears the goal)")
            return {"weekly_goal": store.set_goal(args["minutes"])}
        raise ToolError(f"unknown tool: {name}")  # pragma: no cover

    # -- JSON-RPC ------------------------------------------------------
    @staticmethod
    def _result(msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    def handle(self, msg: object) -> dict | None:
        """Handle one decoded JSON-RPC message. Returns the response, or None for notifications."""
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
            return self._error(msg.get("id") if isinstance(msg, dict) else None, -32600, "invalid request")
        method, msg_id = msg["method"], msg.get("id")
        is_notification = "id" not in msg
        params = msg.get("params") or {}
        if not isinstance(params, dict):
            return None if is_notification else self._error(msg_id, -32602, "params must be an object")

        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
            return self._result(msg_id, {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "studystreak", "version": __version__},
                "instructions": "Use these tools to log and review the user's study sessions.",
            })
        if is_notification:
            return None  # e.g. notifications/initialized, notifications/cancelled
        if method == "ping":
            return self._result(msg_id, {})
        if method == "tools/list":
            return self._result(msg_id, {"tools": TOOLS})
        if method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            if not isinstance(name, str) or not isinstance(args, dict):
                return self._error(msg_id, -32602, "tools/call needs a name and an arguments object")
            if name not in _TOOL_NAMES:
                return self._error(msg_id, -32602, f"unknown tool: {name}")
            try:
                payload = self.call_tool(name, args)
            except (ToolError, ValidationError, StoreError) as exc:
                return self._result(msg_id, {"content": [{"type": "text", "text": f"error: {exc}"}],
                                             "isError": True})
            return self._result(msg_id, {
                "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                "isError": False,
            })
        return self._error(msg_id, -32601, f"method not found: {method}")


def main() -> int:
    # MCP stdio: stdout carries protocol messages only; diagnostics go to stderr.
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    server = McpServer()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            response: dict | None = McpServer._error(None, -32700, "parse error")
        else:
            try:
                response = server.handle(msg)
            except Exception as exc:  # never crash the session on one bad call
                print(f"studystreak-mcp: internal error: {exc!r}", file=sys.stderr)
                msg_id = msg.get("id") if isinstance(msg, dict) else None
                response = McpServer._error(msg_id, -32603, "internal error")
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
