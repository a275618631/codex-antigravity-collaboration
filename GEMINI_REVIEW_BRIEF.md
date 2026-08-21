# Gemini Review Brief

## Purpose

Critically review this repository **before public GitHub release**.

The goal is **not** to add features. The goal is to make the existing architecture more precise, credible, minimal, and defensible.

## Review standard

Review as if you are:

- a senior distributed-systems engineer;
- an AI agent/runtime architect;
- a security-conscious open-source maintainer;
- a skeptical GitHub reader seeing the project for the first time.

## Non-negotiable constraints

1. **Do not expand scope.**
2. **Do not introduce a new framework unless an existing claim is technically impossible without it.**
3. Preserve the thesis: **native capabilities first; complexity must be earned.**
4. Keep Codex + Antigravity as the implemented reference case.
5. Keep local privacy routing and multi-host coordination clearly labeled as future directions unless evidence proves otherwise.
6. Do not turn this into an installation tutorial.
7. Do not use marketing language.
8. Do not claim enterprise security, zero-risk anonymization, production readiness, or full autonomy.
9. Treat shared-skill synchronization as **Partial** until the known canonical-source drift is independently resolved.
10. Prefer deleting or tightening text over adding new concepts.

## Files to review

- `README.md`
- `README.zh-TW.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN_PRINCIPLES.md`
- `docs/PRIVACY_AND_TRUST.md`
- `docs/STATUS_AND_ROADMAP.md`
- `docs/REFERENCES.md`

## Review questions

### Positioning

- Is the project clearly a reference architecture / case study rather than a new agent framework?
- Is the core thesis obvious within the first screen of the README?
- Are any names or claims larger than the actual implementation?

### Architecture

- Are runtime-internal parallelism, vertical delegation, inter-runtime delegation, and inter-host delegation cleanly separated?
- Is bounded delegation technically coherent?
- Does the staged coordination model avoid premature distributed infrastructure?
- Is distributed write ownership explained without implying global serialization?

### Evidence

- Is every capability correctly labeled Implemented / Partial / Planned / Exploratory?
- Does any roadmap item accidentally read like a current feature?
- Are there claims that require evidence not currently present?

### Privacy

- Is pseudonymization clearly distinguished from encryption?
- Is the local LLM correctly treated as an advisory semantic classifier rather than the sole security authority?
- Are residual semantic re-identification risks stated clearly?
- Does anything imply enterprise compliance or zero leakage?

### Open-source quality

- Is any section redundant?
- Could any paragraph be 30–50% shorter without losing meaning?
- Are external references authoritative and current?
- Are archived projects clearly labeled as historical/design references?
- Does the repository contain enough substance to justify publication without turning into a tutorial?

## Required output

Return exactly these sections:

### 1. Release decision
`READY / READY WITH FIXES / NOT READY`

### 2. Must-fix
Only issues that would materially hurt credibility, correctness, security framing, or public interpretation.

### 3. Should-fix
Important clarity or maintainability improvements.

### 4. Delete or simplify
Text/concepts that should be removed rather than expanded.

### 5. Unsupported or overstated claims
Quote the exact claim and explain the problem.

### 6. Final positioning
Provide one revised one-sentence repository description only if the current one is materially weaker.

### 7. Score
Score 0–10 for:
- architecture clarity;
- scope discipline;
- evidence discipline;
- security framing;
- open-source usefulness.

Do **not** propose unrelated features, frameworks, dashboards, databases, vector stores, or orchestration layers.
