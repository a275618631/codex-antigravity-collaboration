# Status and Roadmap

Checked against the private reference environment on **2026-08-29**.

This file is intentionally conservative. If two implementation reports disagree, the lower-confidence status is used until the discrepancy is resolved.

## Status definitions

- **Implemented** — exercised in the current reference environment with direct evidence.
- **Partial** — implemented direction exists, but validation or convergence is incomplete.
- **Planned** — architecture and intended approach are defined; no production implementation claim.
- **Exploratory** — a possible future direction; no commitment or dependency.

## Current implementation

| Area | Status | Evidence boundary |
|---|---|---|
| Codex read-only preflight | **Implemented** | Executed in the private environment. |
| Codex low-friction approval/sandbox baseline | **Implemented** | Configuration was applied and read back. |
| Antigravity permission baseline | **Implemented** | Fine-grained allow/ask/deny configuration was exercised in the private environment. |
| Codex → Antigravity bridge smoke path | **Implemented** | Read-only smoke response passed. |
| Common Task / Result packet | **Implemented** | Used by the collaboration protocol. |
| Bounded external delegation | **Implemented** | One-hop guard is part of the current protocol and validation. |
| Bounded read-only Debate | **Implemented** | Two-round maximum is part of the current protocol. |
| Platform-native parallel agents | **Implemented / Native** | Relies on platform capabilities rather than project code. |
| Shared skill source | **Partial** | The v3.1 canonical source and all 20 manifest restore targets now hash-verify in the private environment; the public `main` manifest still has two stale source paths pending PR #2. |
| Google project-context/notebook usage | **Implemented in private environment** | Useful in the working setup but not a portable requirement of this public architecture. |
| Local-model bidirectional communication | **Experimental** | Exercised separately from the current privacy-aware trust model. |

## Known limitation: shared skills

A previous QA pass found multiple same-name Skills with divergent content in the private reference environment. The
2026-08-29 closure audit now verifies the active v3.1 canonical set and all 20 live restore targets, but the public
`main` branch still points two adapter entries at obsolete source paths until PR #2 is merged.

Therefore the public project should **not** claim that all agent runtimes already consume a perfectly synchronized canonical skill tree.

The architectural direction remains:

> one portable method → one canonical source → thin platform adapters only where necessary.

Promotion from **Partial** to **Implemented** requires a new duplicate/drift scan with a documented canonical source.

## Near-term planned direction

### Privacy-aware local/cloud routing — Planned

Keep the scope small:

1. deterministic secret/PII detection;
2. local classification;
3. context minimization;
4. reversible pseudonymization for allowed classes;
5. local restore;
6. leakage evaluation.

Do not build a new security framework. Prefer mature detection primitives and a thin local policy layer.

### Local model as a private/offline lane — Planned integration

The local model should support:

- restricted or offline tasks;
- network-constrained environments;
- semantic sensitivity classification;
- selected low-risk automation.

It should complement, not replace, deterministic policy.

## Exploratory direction

### Multi-host coordination

Start with shared workspaces across machines.

Only move to a dedicated agent interoperability layer when tasks need explicit cross-host request/result transport.

[A2A](https://github.com/a2aproject/A2A) is a relevant standard to evaluate before inventing a custom agent-to-agent protocol.

### Thin broker

A broker is **not** part of the current design.

Introduce one only if concrete requirements appear for:

- leases;
- heartbeat/liveness;
- retries;
- distributed task state;
- concurrency ownership;
- real-time scheduling.

## Promotion criteria

A roadmap item becomes **Implemented** only when:

1. there is a runnable or observable implementation;
2. the behavior is exercised end-to-end;
3. failure cases are tested;
4. security/permission behavior is documented;
5. rollback or safe-disable behavior exists;
6. the public wording matches the evidence.

## Conditions that do *not* justify a new component

Do not add infrastructure merely because:

- multiple models exist;
- multiple agents exist;
- a diagram looks cleaner with a central server;
- another framework is popular;
- a shared folder feels unsophisticated.

The project should remain smaller than the problem it solves.
