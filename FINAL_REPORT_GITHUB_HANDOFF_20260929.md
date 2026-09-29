# Final report — GitHub → local Codex handoff MVP (2026-09-29)

## ADHD summary

1. Final status: **PARTIAL** — implementation and mock/unit validation complete; authorized real E2E is blocked.
2. Mac real E2E: **BLOCKED / NOT RUN**.
3. Windows: **NOT VERIFIED**; bundled Python ran unit tests, but normal system Python is absent.
4. ChatGPT → automatic local Codex: **not production-ready until the one-time authorization/setup below**.
5. Phone status/result: designed through one GitHub Issue progress comment; real writeback not authorized or tested.
6. Automated tests: **22 PASS / 0 FAIL**; JSON, PowerShell, shell, canonical validation, and diff whitespace checks passed.
7. Delivery: local branch `codex/github-local-handoff-mvp-20260929`; local commit created; no push or PR was performed.
8. Manual work: one consolidated authorization for private test repos/token, Python install, host config, real smoke, optional service activation, push/PR.
9. Known risks: real GitHub API/worktree/Codex path and symlink escape behavior remain unverified; unattended cancellation is limited.
10. Next minimum item: run the authorized private-repo smoke test in foreground `once` mode.

## Delivered

- Standard-library receiver with fixed Issue parser, canonical Task Packet prompt, compatible Task/Result transport schemas, actor/digest/repository/host/scope/nonce approval, edit invalidation, atomic persistence, deduplication, stale recovery, timeout/cancellation primitives, and redaction.
- ETag-aware polling with bounded rate-limit/backoff handling; serialized and bounded Issue result reporting.
- Safe Codex command construction using arguments/stdin, isolated worktree, `workspace-write`, JSONL, output schema, last-message file, ephemeral session, and fail-closed structured result validation.
- CLI: `doctor`, `status`, `once`, `dry-run`, `start`, and `stop`. Start/stop do not install a service.
- GitHub Issue template, configuration example, Python dependency metadata (zero runtime dependencies), platform verification scripts, security model, runbook, and tests.

## Validation evidence

- Bundled Python `unittest discover -s tests -v`: 22 tests, all passed.
- Bundled Python `compileall`: passed.
- JSON load of all handoff JSON files: passed.
- PowerShell parser for the Windows verification script: passed.
- `bash -n` for the macOS verification script: passed.
- `git diff --check`: passed.
- `pwsh -File scripts/validate-canonical-skills.ps1`: `PASS: 13 Skills; frontmatter, descriptions, names, references, and manifest hashes validated.`
- Existing `local_bridge` was unchanged. Its Python test was not run on Windows because it imports macOS-only `fcntl`; live two-runtime interop is **NOT VERIFIED**.

## One consolidated authorization request

Authorize these reversible steps together when ready: create/select one private inbox and one non-sensitive test repo; grant a fine-grained, least-privilege token to the receiver process; install/confirm Python 3.11+ on the primary host; populate the local allowlist/config; run one foreground real smoke from Issue creation through approval, isolated worktree execution, tests, and Issue writeback; then optionally commit/push this branch and create a Draft PR. Separately decide whether to install a reviewed LaunchAgent or Scheduled Task. Recovery is to stop the foreground receiver, revoke the token, remove only the configured worktree/state directory after inspection, and close the test Issue/PR.

## Canonical and metrics impact

`CANONICAL_MANIFEST.json`, Shared Skills, the shared protocol, and `local_bridge` required no change. The receiver consumes the existing packet contract through a backward-compatible transport envelope. Human handoff count and execution duration will be recorded per real task; actual model and token usage are `N/A` unless emitted by the CLI. No savings percentage is claimed.

References: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/), [Codex CLI reference](https://developers.openai.com/codex/cli/reference/), and [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).
