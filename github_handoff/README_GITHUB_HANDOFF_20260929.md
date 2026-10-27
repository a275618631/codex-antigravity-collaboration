# GitHub → local Codex handoff MVP (2026-09-29)

This receiver polls one private GitHub inbox and executes only a separately approved, allowlisted task on one configured host. It uses the Python standard library, creates a dedicated Git worktree, passes a bounded Task Packet to `codex exec` over stdin, and updates one redacted progress comment through Queued, Running, Validating, Reporting, and terminal states.

The supported chat surfaces are personal ChatGPT Plus and Google AI Pro Gemini on web/mobile. They create and review a Task Brief; GitHub remains the only task, approval, and status ledger. This project does not claim native chat writeback.

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
python3 -m github_handoff --config ~/.config/github-handoff/config.json watch
python3 -m github_handoff --config ~/.config/github-handoff/config.json status
```

`watch` is a foreground polling loop with a crash-recoverable single-writer lock and bounded error backoff. `start` and `stop` only create/remove its local run marker. They intentionally do not install or activate a daemon.

Generate a token-free prefilled Issue URL from a reviewed Task Brief:

```bash
python3 -m github_handoff --config ~/.config/github-handoff/config.json issue-link --body-file task-brief.md
```

Cancel an approved task before execution with a trusted post-edit comment:

```text
/codex-cancel task=<Task-ID> host=<configured-host>
```

Human Gate and task state are tracked separately in the local state file:

- a well-formed task without a trusted approval remains `Awaiting Approval` with `human_gate=PENDING`; the executor is not called;
- a trusted, post-edit approval moves the task through `Queued` with `human_gate=APPROVED`;
- a `Completed` executor outcome is accepted only with a strict-schema Result Packet whose transport matches the approved task; a missing, malformed, mismatched, or non-success packet is fail-closed as `Blocked`;
- an invalid approval, scope failure, runtime failure, malformed executor outcome, or interrupted execution is fail-closed with `human_gate=BLOCKED` and a terminal `Failed` or `Blocked` execution state;
- trusted cancellation is terminal `Cancelled` with `human_gate=CANCELLED`, including cancellation after approval but before executor start.

States: Draft → Awaiting Approval → Queued → Running → Validating → Reporting → Completed. Failed, Blocked, and Cancelled are terminal states. This local gate does not itself perform a desktop handoff; `doctor` remains fail-closed as `LIVE_BLOCKED` when it cannot independently observe authenticated handshake evidence, even if a separately recorded bounded runtime probe has passed.

No lockfile is needed because the runtime has no third-party Python dependency. The GitHub token is read only from the configured process environment variable.
