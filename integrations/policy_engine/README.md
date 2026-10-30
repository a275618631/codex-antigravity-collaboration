# Policy Engine Integration Descriptor

## Identity

- Repository: `a275618631/agent-tool-policy-engine`
- Verified branch: `codex/staging` at `188421cb92ab772cb29e39f3e03fe6a52d91bbd3`
- Verified tag: `v0.1.1-staging` at `d0c43dc1920f6d7339411149c7add3f5753096d2`
- Relationship: external safety component; this repository must not copy or merge its code.

## Contract

The integration boundary takes a task/action context and returns exactly one of:

- `ALLOW`
- `REQUIRE_APPROVAL`
- `DENY`

The control plane evaluates this decision before any router. `REQUIRE_APPROVAL` enters `HUMAN_GATE`; `DENY` enters `BLOCKED`. Routing, including System One, cannot override either decision.

## Current limitation and fail-safe behavior

No live Policy Engine API endpoint or executable adapter was verified in this worktree. The control plane therefore defaults to an explicit local `ALLOW` policy only for test/dev construction. A production adapter must fail closed (`REQUIRE_APPROVAL` or `DENY`) on unavailable, malformed, stale, or unverifiable decisions.

## Evidence

The external repository metadata, `codex/staging`, and `v0.1.1-staging` were read remotely on 2026-10-15. No Policy Engine source was copied, changed, or executed.
