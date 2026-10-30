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

## B1–B5 implementation status

The control-plane implementation and its tests now cover the handoff acceptance
cases:

- **B1 — approval-bound plan:** the approval digest binds goal, repository,
  base SHA, operation type, exact write-set, and approved tasks. Empty scopes
  are read-only; unsafe relative paths and resolved paths outside the repo are
  rejected. Writes fail closed when policy is absent, and DENY precedes routing.
- **B2 — result contract:** v2 packets bind goal/task/attempt/delivery IDs,
  approved plan/task digests, repository, and base SHA. The adapter requires
  matching trusted transport identity. The v1 adapter remains available but
  treats acceptance as UNVERIFIED; a legacy boolean cannot establish PASS.
- **B3 — ingestion and discovered work:** state writes use a cross-process lock
  and revision counter. Delivery IDs are idempotent only for the same digest;
  changed content is rejected. Newly discovered work is validated as a whole
  for duplicate IDs, dependencies/cycles, and parent plus approved write scope
  before any task is committed.
- **B4 — Parent completion:** all required tasks, an integration task, every
  Parent acceptance criterion with evidence, and zero unresolved blockers are
  required. FAILED, all-cancelled, and incomplete states do not complete.
- **B5 — recovery:** stale in-flight work and unknown runtime side effects move
  to `NEEDS_RECONCILIATION`; recovery inspects known external IDs and never
  blindly resubmits an uncertain operation.

Verification on this branch: `python -m unittest discover -s tests -v` — **79
passed**; JSON Schema parsing and `git diff --check` passed. The historical
115/4/1 report in Drive still cannot be tied to source and logs in this checkout,
so it remains unverified. The four historical mac-health failures likewise
need their original logs and matching source for diagnosis.

These results verify local control-plane behavior with tests and mock adapters.
They do not prove a live Parent Goal round trip, desktop mailbox, Antigravity
runtime integration, OS isolation, or authorization for unattended or
cross-repository writes. Keep those gates closed until independently verified.

The GitHub inbox/runner and OS isolation gates remain separate from this local
integration. Read-only CLI evidence does not establish a desktop mailbox or a
full live Parent Goal round trip.
