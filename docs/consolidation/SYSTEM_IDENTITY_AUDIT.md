# System Identity Audit

**Audit date:** 2026-10-15
**Rule:** Folder names alone were never used as relationship evidence.

| Artifact | Canonical Identity | Role | Relationship | Repo/Drive | Current Status | Evidence | Keep Separate? | Merge Into Core? | Archive Candidate? | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| `codex-antigravity-collaboration` | canonical repo | CORE_MODULE | root implementation | GitHub / local clone | active | remote metadata; `main` `7a48104` | no | n/a | no | canonical manifest and protocol identify it as source of truth |
| `local_bridge` | bridge evidence | CORE_MODULE | existing local transport | canonical repo | historical/current code, live status unverified | repository README and test source | no | already core | no | no current two-runtime live evidence |
| PR #8 / `github_handoff` | GitHub Local Handoff | CORE_MODULE | module of canonical repo | draft PR / Drive module folder | integration branch includes it | PR metadata, 26 current tests | no | yes | no | matches private-inbox transport boundary |
| `control_plane` | Agent Orchestration | CORE_MODULE | module of canonical repo | integration branch | mock-validated | 9 tests and persisted state implementation | no | yes | no | minimal implementation, no broker or DB |
| `agent-tool-policy-engine` | Policy Engine | LINKED_COMPONENT | external safety component | private GitHub repo / Drive folder | external | verified repo, branch, and tag | yes | no | no | independent security lifecycle |
| System One | System One Router | EXPERIMENT | optional routing provider | interface only | unverified | no current smoke, API, benchmark, or failure evidence | yes | no | no | cannot be promoted from architecture alone |
| `codex-handoff-validation-20261015` | temporary worktree | HISTORICAL | validation checkout | local filesystem | local-only | Git worktree points to PR #8 head | yes | no | yes | disposable validation evidence; preserve only while useful |
| workspace root / other local repos | unclassified unrelated projects | UNRELATED | none established | local filesystem | not included | remote/README evidence does not connect them to this system | yes | no | no decision | no relationship inferred from names |

## Drive identity record

| Folder ID | Previous display name | Current display name at audit | Classification | Action |
|---|---|---|---|---|
| `1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s` | `2026-08-21_雙平台Agent協作架構`, `2026-09-02_雙平台Agent協作架構` | `本地多Agent協作系統` | canonical project | renamed in place on 2026-10-15; Folder ID unchanged |
| `1J9Z2PhOJMiZxk3TS-nRwnJa5YXtEezwi` | `2026-09-29_GitHub本地Codex自動交接MVP` | same | SAME_SYSTEM_MODULE | link as module; do not copy contents |
| `1VBxnHwT6oEo6h9WMJJZh5PouAA2_lE1E` | `2026-08-24_Thin-Agent-Tool-Policy-Engine` | same | EXTERNAL_LINKED_COMPONENT | link only; do not move or merge |

No Drive folder was deleted, moved, or archived during the audit. The canonical folder was renamed in place only after its stable ID and relationship records were written.
