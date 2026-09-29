# Runbook — GitHub local handoff (2026-09-29)

## One-time preparation

1. Create a dedicated **private** task-inbox repository and a non-sensitive test repository.
2. Install Python 3.11+ and verify `git` and `codex` are available.
3. Copy `github_handoff/config.example.json` outside Git, restrict its permissions, and set exact actor/repository/host/scope allowlists plus local clone/worktree paths.
4. Provide a least-privilege fine-grained GitHub token to the receiver process through the configured environment variable. Do not paste it into chat, Issue, config, or logs.
5. Run `doctor`, then mock/unit tests, then `dry-run`.

## Open and approve from phone or web

1. Create an Issue using **Codex local task**. Keep paths repository-relative and choose the configured primary host.
2. Review the final Issue and compute its digest locally. A GitHub label or Issue claim is not approval.
3. From an allowlisted GitHub account, post the exact approval command with a fresh nonce and host.
4. Run `once`. The phone can follow the single progress comment and any manually authorized PR.

For Gemini, share the same Issue URL or a redacted Task Brief manually. This MVP does not claim automatic web-chat synchronization.

## Query, cancel, and recover

- `status` reconciles stale in-progress records to Blocked after the configured timeout.
- `stop` removes the local run marker; terminate an active foreground `once` process with the normal OS interrupt. The interrupted task remains recoverable and is reconciled on restart.
- To cancel before execution, remove the approval or close the Issue before the next poll. Production activation should add a reviewed cancellation label/comment workflow before unattended scheduling.
- On failure, inspect only the restricted local evidence directory, correct the cause, edit the Issue if scope changes, and issue a new digest/nonce approval.
- Worktrees are deliberately retained for inspection. Remove one only after verifying its exact path and preserving wanted changes.

## Start/stop and uninstall

The MVP `start`/`stop` commands manage only a local marker. The macOS and Windows scripts run `doctor`; they do not install LaunchAgents, Scheduled Tasks, or services. Formal background activation requires the single authorization listed in the final report.

To uninstall, stop the foreground process, remove the explicitly configured state/worktree directory after review, remove the external config, and remove the token from OS credential storage. No remote data is automatically deleted.
