# GitHub → local Codex handoff MVP (2026-09-29)

This receiver polls one private GitHub inbox and executes only a separately approved, allowlisted task on one configured host. It uses the Python standard library, creates a dedicated Git worktree, passes a bounded Task Packet to `codex exec` over stdin, and writes a redacted progress summary back to one issue comment.

The GitHub Issue is data, not a command. Approval requires a trusted comment created after the latest issue edit:

```text
/codex-approve digest=<64-lowercase-hex> nonce=<unique-8+-character-value> host=<configured-host>
```

Compute the digest locally after reviewing the final Issue:

```shell
python3 -c "from github_handoff.core import parse_task,task_digest; import sys; print(task_digest(parse_task(sys.stdin.read())))" < issue-body.txt
```

Run from the repository root:

```shell
python3 -m github_handoff --config ~/.config/github-handoff/config.json doctor
python3 -m github_handoff --config ~/.config/github-handoff/config.json dry-run
python3 -m github_handoff --config ~/.config/github-handoff/config.json once
python3 -m github_handoff --config ~/.config/github-handoff/config.json status
```

`start` and `stop` only create/remove a local run marker. They intentionally do not install or activate a daemon. See the dated runbook for deployment choices and recovery.

States: Draft → Awaiting Approval → Queued → Running → Validating → Reporting → Completed. Failed, Blocked, and Cancelled are terminal states.

No lockfile is needed because the runtime has no third-party Python dependency. The GitHub token is read only from the configured process environment variable.
