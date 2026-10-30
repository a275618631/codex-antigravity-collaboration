# Roadmap

> Historical 2026-10-15 snapshot. Use the project Drive CURRENT entry and the
> 2026-10-30 design handoff for the current development sequence.

## 1. Validate the private transport

- Register one Windows self-hosted runner in a dedicated private operational inbox repository.
- Set restricted labels and a runner-local config path; do not expose any token in repository configuration, issues, logs, or workflow inputs.
- Execute `doctor`, `dry-run`, a disposable private-repo task, result writeback, deduplication, and redaction checks.

## 2. Validate live adapters

- Verify Codex and Antigravity health/capabilities/authentication separately.
- Run one disposable Codex -> Antigravity -> Codex handoff with no user copy/paste.
- Keep mock evidence distinct from live evidence.

## 3. Attach Policy Engine safely

- Verify the exact external Policy Engine decision interface.
- Add a fail-closed production adapter and policy-denial integration tests.

## 4. Consider System One only after evidence

System One remains a `Decision B | Worth PoC | Evidence V2` experiment until compatible runtime, smoke, failure tests, and benchmark evidence exist. It cannot become a policy authority or a required routing dependency.
