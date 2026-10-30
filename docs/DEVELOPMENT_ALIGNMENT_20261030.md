# Development alignment — 2026-10-30

This is an engineering handoff, not a replacement for the project's Drive
CURRENT entry: https://drive.google.com/drive/folders/1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s.

## Baseline

- GitHub main: `3a04e3ff6f35489d36d3fa1ec74b59a9d267a977`.
- Base: PR #10 head `8b0534d62529da4aa1b982d73c1df8bfca6a5ff6`.
- Integrated control-plane branch: `be3ba65350e7d96eef49470ed0a7346353aa3ad0`.
- Duplicate handoff conflicts were resolved using PR #10's newer implementation.
  The control-plane branch's missing-token preflight was retained separately.
- PR #8, #10, #12 and #13 remain separate open pull requests. The prior
  checkout's uncommitted PR #12 changes were not used or modified.

## Evidence and next work

The B1–B5 uncommitted changes and the prior 115/4/1 test run reported in Drive
were not found in the available worktrees. The control plane here is the older
`be3ba65` implementation; passing its mock tests does not establish the B1–B5
safety properties. Do not run it for unattended or cross-repository writes.

Continue with the acceptance cases in the project handoff:
https://docs.google.com/document/d/1vMTLbeRmlv2-YXn_4b1M6akg9VY1nG_gLCtDIfCiH2I/edit.
Implement and verify approval-bound scope and fail-closed policy, versioned
result packets, atomic idempotent ingestion and locking, evidence-based Parent
completion, and interrupted-runtime reconciliation. Investigate the four
historical mac-health failures when the original logs and matching source are
available; their cause is unverified in this checkout.

The GitHub inbox/runner and OS isolation gates remain separate from this local
integration. Read-only CLI evidence does not establish a desktop mailbox or a
full live Parent Goal round trip.
