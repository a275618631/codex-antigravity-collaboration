# Consolidation Result

The repository now models one stable system with modules rather than competing projects. The canonical repository remains `a275618631/codex-antigravity-collaboration`; GitHub engineering state remains primary, while Drive is limited to a human-readable index, archive, and handoff role.

## Minimal diff applied

- Integrated the PR #8 handoff implementation into the isolated integration branch, without merging main.
- Added `control_plane/` for durable Parent Goal/task state, packet normalization, automatic next-task readiness, Human Gates, policy-first dispatch, duplicate protection, and restart recovery.
- Added the registry, relationship graph, system map, and policy integration descriptor.
- Added a non-active GitHub workflow template intended only for a private inbox and labeled self-hosted runner.

## Intentionally not created

- no new orchestrator repository;
- no broker, message queue, database, vector DB, dashboard, universal scheduler, gateway, or custom auth system;
- no Policy Engine source copy;
- no System One production dependency.

## Evidence boundary

The control-plane chain is validated with mocks. The 26-test GitHub receiver unit suite is currently runnable and passes, including duplicate, redaction, stale recovery, scope, and structured-result tests. A live GitHub or Antigravity handoff remains blocked pending the configured private transport and runtime access described in `CURRENT_STATE.md`.
