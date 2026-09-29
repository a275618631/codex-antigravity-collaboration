# Security and threat model — GitHub local handoff (2026-09-29)

## Trust boundary

GitHub Issue text, comments, links, labels, repository names, and model output are untrusted. The receiver trusts only its local configuration, an exact allowlist, GitHub-authenticated actor fields returned by the API, and an approval comment whose digest matches the current parsed task.

An approval is valid only when the task actor, approver, repository, host, and every read/write scope are allowlisted; the approval was posted after the latest Issue edit; its nonce has never been consumed; and its SHA-256 digest matches the current task. Editing the Issue or changing scope requires a new approval.

## Controls

- Issue content is parsed into fixed fields and passed to Codex through stdin. It is never interpolated into a shell command.
- Git, Codex, and helper commands use argument arrays. Dangerous sandbox-bypass flags are absent.
- Execution uses `workspace-write` only inside a dedicated Git worktree below the configured worktree root. A future read-only analysis mode should use `read-only` by default.
- State is atomically replaced and records consumed nonces, task digests, terminal status, timeout, and interrupted/stale execution.
- GitHub reads use ETag caching and bounded retry/backoff. Writes are serialized and progress is intended to reuse one comment with a minimum update interval.
- Token input is process-scoped through an environment variable. Never run `gh auth token`, print a token, persist it in config, commit it, or include it in prompts/logs.
- Redaction removes common token/password patterns and user home path prefixes before progress output. Detailed evidence stays in the restricted local state directory.
- Success is fail-closed: exit code zero, no timeout/cancellation, and a valid structured Result Packet are all required.
- The requested model may be recorded, but the actual model and token usage remain `N/A` unless the CLI explicitly emits trustworthy evidence.

## Residual risks

- A compromised authorized GitHub account can approve malicious natural-language work within an allowlisted scope.
- Prefix-based repository-relative scope controls require the Codex sandbox and worktree boundary as defense in depth; symbolic-link escape testing remains important before production.
- Environment variables may be readable by privileged local processes. Prefer OS credential storage that injects a process-scoped token at launch.
- The MVP is a polling client, not a hardened multi-tenant runner. Use one private inbox, one primary host, and one active write task.

References: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/), [Codex CLI reference](https://developers.openai.com/codex/cli/reference/), [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), and [GitHub token guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation).
