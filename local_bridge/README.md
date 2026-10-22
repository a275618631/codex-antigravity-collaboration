# Codex × Antigravity local bridge

This directory contains the small local MCP server used by the two desktop
clients on Windows or macOS.

The Windows-compatible implementation is recorded by local commit `6d0cc96`.
It uses `msvcrt` byte-range locking on Windows and `fcntl` locking on POSIX
systems. The MCP tools and JSONL mailbox format are unchanged.

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

## Validation boundary

Run the existing bridge test from the repository root:

```powershell
python -m unittest local_bridge.test_bridge_server -v
```

On Windows installations where `python` is not on `PATH` and `py -3` cannot
find an installed runtime, use the repository verification entry point. It
prefers `CODEX_PYTHON`, then the Codex bundled Python runtime, then `py -3`
and `python`:

```powershell
pwsh -File scripts/verify-github-handoff-windows.ps1
```

The local two-process test is PASS. It is a mailbox transport test and does not
by itself prove runtime authentication. A separate bounded real
Codex → MCP Bridge → Antigravity → Codex nonce probe passed on 2026-10-20;
see the repository-level
[`LIVE_HANDOFF_EVIDENCE_20261020.md`](../LIVE_HANDOFF_EVIDENCE_20261020.md).
