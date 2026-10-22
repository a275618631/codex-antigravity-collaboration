# Windows Codex Runtime → Mac Exact Handoff

## Status

- Source runtime: Windows Codex Desktop / CLI
- Canonical repository: `a275618631/codex-antigravity-collaboration`
- Delivery branch: `codex/windows-canonical-final-20260910`
- Merge status: PR required; this branch must not be merged by the handoff author.
- `SAFE FOR MAC SYNC`: `NO` until the PR is reviewed and merged into the canonical branch.

## Portable artifacts

The following artifacts are the portable convergence set:

- `CANONICAL_MANIFEST.json`
- `shared/skills/GLOBAL_CORE/file-organizer/SKILL.md`
- `shared/skills/GLOBAL_CORE/pr-review-agent/SKILL.md`
- Existing canonical Global Core Skills referenced by `CANONICAL_MANIFEST.json`

The manifest is the source of truth for canonical paths, runtime, scope, version, hash, and restore target.

## Windows verified runtime facts

- Codex Native-First: PASS
- Native coding, planning, and subagent paths: PASS
- `.agents/skills`: primary user Skill runtime
- `.codex/skills`: retained and duplicate entries soft-disabled; do not delete
- Wave 1 generic Skills: soft-disabled; do not restore unless a regression is reproduced
- Codex Local Memory: fully OFF
- Hooks: 0
- Plugin/MCP inventory: unchanged; no automatic scope migration
- Model, reasoning defaults, Ox routing, credentials, and OAuth: unchanged
- Worktree upstream refresh: best-effort
- Worktree keep count: 10

## Mac application order

1. Wait for the canonical PR to merge.
2. Confirm the merged canonical commit and re-read `CANONICAL_MANIFEST.json`.
3. Pull only the manifest-listed portable artifacts into the Mac canonical/runtime locations.
4. Keep Mac-local paths, caches, session state, credentials, OAuth state, GUI state, and plugin caches out of the sync.
5. Reconcile Mac-local configuration separately; do not copy the Windows `config.toml` wholesale.
6. Run Mac startup, Skill discovery, Native coding, Native planning, subagent, and retained Skill smoke tests.
7. Set `SAFE FOR MAC SYNC = YES` only after the merged branch and Mac regression checks both pass.

## Antigravity notes

The following are Windows-local verified observations, not portable Codex artifacts:

- Security Preset: Custom
- Outside workspace: Always Ask
- Terminal Auto Execution: Always Proceed
- Artifact Review: Always Proceed

Do not transfer these values to Mac without a separate platform-specific review.

## Explicit exclusions

- Windows absolute paths
- `.codex/skills` deletion or archive operation
- Plugin/MCP removal or project-scope migration
- Hooks, daemons, frameworks, or packages
- Model/Ox routing changes
- Credentials, API keys, tokens, OAuth state, cookies, or `.env`
- Session databases, telemetry, plugin caches, and private GUI state
