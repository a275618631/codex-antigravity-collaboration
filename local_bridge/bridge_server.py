#!/usr/bin/env python3
"""Local MCP mailbox shared by the Codex and Antigravity desktop clients.

Each MCP client starts its own stdio instance.  Instances communicate through
the same append-only JSONL mailbox, so no background service or credentials
are required.  The bridge is intentionally local-only and exposes only
message transport/status tools; it does not execute commands from messages.
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import uuid


SERVER_NAME = "codex-antigravity-bridge"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"
MAX_MESSAGE_BYTES = 16_384
MAX_SUBJECT_BYTES = 512
MAX_LIMIT = 100
AGENT_ID_RE = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")


def _text_size(value: str) -> int:
    return len(value.encode("utf-8"))


def _error(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}


class Mailbox:
    def __init__(self) -> None:
        configured = os.environ.get("CODEX_ANTIGRAVITY_BRIDGE_HOME")
        self.root = Path(configured).expanduser() if configured else Path.home() / ".codex" / "agent-bridge"
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.messages_path = self.root / "messages.jsonl"
        self.lock_path = self.root / ".messages.lock"
        self.lock_path.touch(mode=0o600, exist_ok=True)
        os.chmod(self.lock_path, 0o600)
        self.agent_id = os.environ.get("CODEX_ANTIGRAVITY_BRIDGE_AGENT", "unknown")
        if not AGENT_ID_RE.fullmatch(self.agent_id):
            raise ValueError("CODEX_ANTIGRAVITY_BRIDGE_AGENT must be a simple agent identifier")

    def _locked(self, exclusive: bool):
        handle = self.lock_path.open("a+")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        return handle

    def send(self, arguments: dict) -> dict:
        target = str(arguments.get("target", "all"))
        message = str(arguments.get("message", ""))
        subject = str(arguments.get("subject", ""))
        correlation_id = arguments.get("correlation_id")
        if target != "all" and not AGENT_ID_RE.fullmatch(target):
            return _error("target must be 'all' or a simple agent identifier")
        if not message.strip():
            return _error("message is required")
        if _text_size(message) > MAX_MESSAGE_BYTES:
            return _error(f"message exceeds {MAX_MESSAGE_BYTES} UTF-8 bytes")
        if _text_size(subject) > MAX_SUBJECT_BYTES:
            return _error(f"subject exceeds {MAX_SUBJECT_BYTES} UTF-8 bytes")
        if correlation_id is not None and not isinstance(correlation_id, str):
            return _error("correlation_id must be a string when provided")

        record = {
            "message_id": uuid.uuid4().hex,
            "created_at": _now(),
            "sender": self.agent_id,
            "target": target,
            "subject": subject,
            "message": message,
        }
        if correlation_id:
            record["correlation_id"] = correlation_id

        with self._locked(True) as lock:
            with self.messages_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(self.messages_path, 0o600)
            lock.flush()
        return {"content": [{"type": "text", "text": json.dumps(record, ensure_ascii=False)}]}

    def receive(self, arguments: dict) -> dict:
        after = arguments.get("after")
        if after is not None and not isinstance(after, str):
            return _error("after must be a message_id or ISO timestamp")
        try:
            limit = max(1, min(int(arguments.get("limit", 20)), MAX_LIMIT))
        except (TypeError, ValueError):
            return _error("limit must be an integer")
        include_own = bool(arguments.get("include_own", False))
        messages: list[dict] = []
        with self._locked(False):
            if self.messages_path.exists():
                records = []
                for line in self.messages_path.read_text(encoding="utf-8").splitlines():
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    records.append(record)

                cursor_index = -1
                if after:
                    cursor_index = next(
                        (index for index, record in enumerate(records) if record.get("message_id") == after),
                        -1,
                    )
                for index, record in enumerate(records):
                    if record.get("target") not in ("all", self.agent_id):
                        continue
                    if not include_own and record.get("sender") == self.agent_id:
                        continue
                    if after and cursor_index >= 0 and index <= cursor_index:
                        continue
                    if after and cursor_index < 0 and record.get("created_at", "") <= after:
                        continue
                    messages.append(record)
                    if len(messages) >= limit:
                        break

        latest = messages[-1]["message_id"] if messages else after
        payload = {"agent": self.agent_id, "messages": messages, "next": latest}
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}

    def status(self) -> dict:
        count = 0
        latest = None
        with self._locked(False):
            if self.messages_path.exists():
                for line in self.messages_path.read_text(encoding="utf-8").splitlines():
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    count += 1
                    latest = record
        payload = {
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "agent": self.agent_id,
            "transport": "stdio",
            "mailbox": str(self.root),
            "message_count": count,
            "latest_message_id": latest.get("message_id") if latest else None,
            "latest_created_at": latest.get("created_at") if latest else None,
        }
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


TOOLS = [
    {
        "name": "bridge_send",
        "description": "Send a bounded text message to Codex, Antigravity, or both through the local shared mailbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Recipient agent id, or 'all'.", "default": "all"},
                "subject": {"type": "string", "description": "Short subject.", "default": ""},
                "message": {"type": "string", "description": "Message body; max 16,384 UTF-8 bytes."},
                "correlation_id": {"type": "string", "description": "Optional id linking a reply to a request."},
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    },
    {
        "name": "bridge_receive",
        "description": "Read messages addressed to this desktop agent from the local shared mailbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "after": {"type": "string", "description": "Optional message id or ISO timestamp cursor."},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIMIT, "default": 20},
                "include_own": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bridge_status",
        "description": "Report local bridge connectivity and mailbox status without reading message bodies.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "bridge_ping",
        "description": "Confirm that the local Codex–Antigravity bridge is reachable.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def handle(request: dict, mailbox: Mailbox) -> dict | None:
    request_id = request.get("id")
    method = request.get("method")
    if request_id is None and method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "initialize":
        params = request.get("params") or {}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params") or {}
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if tool_name == "bridge_send":
            result = mailbox.send(arguments)
        elif tool_name == "bridge_receive":
            result = mailbox.receive(arguments)
        elif tool_name == "bridge_status":
            result = mailbox.status()
        elif tool_name == "bridge_ping":
            result = {"content": [{"type": "text", "text": json.dumps({"ok": True, "agent": mailbox.agent_id})}]}
        else:
            result = _error(f"unknown tool: {tool_name}")
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    try:
        mailbox = Mailbox()
    except Exception as exc:
        print(f"bridge startup failed: {exc}", file=sys.stderr)
        return 1
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
            response = handle(request, mailbox)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            request_id = None
            try:
                request_id = json.loads(raw).get("id")
            except Exception:
                pass
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(exc)}}
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
