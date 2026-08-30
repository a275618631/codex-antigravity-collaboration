# Codex × Antigravity local bridge

This directory contains the small local MCP server used by the two desktop
clients on this Mac.

## Transport model

Both clients launch `bridge_server.py` over MCP stdio. Each client gets its own
server process, while both processes use the same locked JSONL mailbox at:

```text
~/.codex/agent-bridge/
```

This is a local mailbox, not a network service, daemon, broker, or command
executor. Messages are plain text and should not contain secrets or data that
the other runtime is not allowed to see.

## Tools

- `bridge_send`: send to `codex`, `antigravity`, or `all`.
- `bridge_receive`: read messages addressed to the current runtime; use the
  returned `next` value as `after` for the next read.
- `bridge_status`: check the local mailbox and runtime identity.
- `bridge_ping`: check that the MCP process is reachable.

The model must call `bridge_receive` to read messages; MCP does not push an
unsolicited message into an already running model turn.

## Configuration

Codex uses `~/.codex/config.toml` with agent id `codex`. Antigravity uses
`~/.gemini/config/mcp_config.json` with agent id `antigravity`. Both point to
the same server script and mailbox path.

After editing either configuration, start a new session or restart the
corresponding desktop app so its MCP tool list is rebuilt.
