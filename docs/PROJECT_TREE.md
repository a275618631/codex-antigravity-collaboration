# Local Multi Agent Collaboration System Project Tree

## Root system

**System ID:** `local-multi-agent-collaboration`
**Canonical engineering repository:** `a275618631/codex-antigravity-collaboration`
**Canonical Drive folder ID:** `1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s`

```text
local-multi-agent-collaboration
|- core-collaboration                    implemented
|  |- Task / Result Packet
|  |- bounded delegation
|  `- Shared Skills / canonical manifest
|- github-local-handoff                  in progress
|  |- PR #8 source module
|  `- private-inbox, self-hosted-runner transport path
|- agent-orchestration                   implemented as contract + mock-tested control plane
|  |- durable Parent Goal / task graph
|  |- state machine / completion contract
|  `- Human Gate / restart recovery
|- agent-adapters                        partial
|  |- Codex contract
|  |- Antigravity contract
|  `- Future Agent contract
|- routing                               partial
|  |- Manual Lead / deterministic / capability routing
|  `- System One (experiment only)
`- agent-tool-policy-engine              external linked safety component
```

## Module register

| Module | Role | Status | Source | Owner agent | Dependency / blocker | Next action | Evidence |
|---|---|---|---|---|---|---|---|
| `core-collaboration` | packets, bounded delegation, shared skills | IMPLEMENTED | canonical repo main | Codex / Antigravity | Runtime interop needs current evidence | Keep protocol as source of truth | `shared/rules/`, `CANONICAL_MANIFEST.json` |
| `github-local-handoff` | private GitHub Issue to local Codex transport | IN_PROGRESS | PR #8 and this integration branch | Codex | No configured private inbox token or registered runner | Create private inbox and register a least-privilege runner | 26 receiver tests pass today |
| `agent-orchestration` | Parent Goal and task graph control plane | IMPLEMENTED (mock only) | `control_plane/` | Codex | Live Antigravity transport unavailable | Wire a verified adapter into disposable E2E | 9 orchestration tests pass |
| `agent-adapters` | isolate runtime-specific transports | PARTIAL | `control_plane/orchestrator.py` | Codex | Passive contracts only | Verify Codex and Antigravity transports separately | adapter contract + registry |
| `routing` | select lead / worker without overriding policy | PARTIAL | `control_plane/orchestrator.py` | Codex | System One lacks current smoke evidence | Retain only experimental interface | unit-tested policy precedence |
| `policy-engine` | safety decision authority | EXTERNAL | `a275618631/agent-tool-policy-engine` | Policy Engine | Integration protocol is descriptor-only | Test the real decision interface before enforcement | `codex/staging`, `v0.1.1-staging` |

## Human Gate

Only a protected-main merge, runner registration/token provisioning, live private-inbox E2E, production deploy, credential access, external communication, destructive Drive change, or a policy exception requires user action. Normal local tests, worktree-safe changes, and result ingestion do not.
