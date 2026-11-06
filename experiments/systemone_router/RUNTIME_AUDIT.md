# Ollama System One Runtime Audit

Date: 2026-11-06 (Asia/Taipei)  
Repo: `a275618631/codex-antigravity-collaboration`  
PoC branch base: `origin/main` at `dc252fa75aa3851eb1adf503e8e01dc156a482cd`

## Runtime

| Item | Evidence |
|---|---|
| OS | Windows 11, build 26200 |
| Repo worktree used for PoC | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration-systemone-poc` |
| Existing checkout | `codex/live-handoff-control-plane-20261029`, dirty user work preserved |
| Ollama executable | `C:\Users\Y6T2\AppData\Local\Programs\Ollama\ollama.exe` |
| Earlier API version | `0.34.0` at initial audit (2026-10-06) |
| Controlled upgrade | Official local installer moved runtime to `0.35.1` on 2026-10-06 |
| Current API version | `0.40.7`, verified from `/api/version` on 2026-11-06; intervening update path is unverified |
| Python | `3.12.14` |
| Isolated environment | `C:\Users\Y6T2\Documents\Tech Review\.venv-systemone` |
| ollama-python | `0.6.3`; `ollama.systemone` is callable |
| Endpoint | `POST /v1/systemone` exists; a deliberately missing model returns application-level 404 with a model-not-found error |
| Decision model | `tev1:0.8b`; pull completed and Ollama verified its SHA-256 layers |
| Model tag digest | `abc31fdb0bf52506cc47091145ac19c4cfb509b73a6841789324f9e32200c099` |
| Model size | `833606657` bytes |
| Main model blob digest | `7daa72d2ed4fa16f5120bc1bb89713531d0f511c360e9228905ba88c092f13b5` |

## Smoke results

Three calls each were made for `choice`, `noul`, and `score`; all nine parsed and passed response validation. Choice was constrained to the four requested route keys. Probability vectors were checked for finite values, valid ranges, candidate keys, and a sum within 0.02 of one. Score was checked against its requested 0–3 scale. `noul` is a numeric probability in `[0, 1]`, not a Boolean.

| Measurement | Result |
|---|---:|
| Cold first System One request | 39,048.92 ms |
| Warm requests | 8 samples; 72.784–364.153 ms |
| `choice` | PASS, 3/3 |
| `noul` | PASS, 3/3 |
| `score` | PASS, 3/3 |

The model was not listed as loaded in `/api/ps` before the smoke run, so the first `choice` request is the cold measurement. These nine requests are smoke evidence only, not a benchmark or correctness estimate.

## Failure probes

| Case | Result | Observed behavior |
|---|---|---|
| Missing model | PASS | SDK returned controlled `ResponseError` (404); fallback required |
| Malformed criteria schema | PASS | SDK rejected nested object criteria with `ValidationError`; no silent schema rewrite |
| Server unavailable | PASS | Request to unavailable local port produced `ConnectTimeout`; fallback required |
| Stalled request | PASS | Local stalled HTTP handler produced `ReadTimeout`; fallback required |
| Non-finite / invalid numeric | PASS | NaN, +Inf, -Inf, and probability 1.01 rejected by local validator |

Fallback is recorded as the required caller behavior for each failure. This smoke test does not implement or validate a production router's fallback branch.

## Gate and boundaries

```text
PHASE0_GATE_CLEARED
PHASE1_SMOKE_PASS
POC_BRANCH_READY
```

Runtime / Smoke evidence: V3.  
Routing adoption decision: V2, pending Phase 2 benchmark.  
Policy Engine: unchanged (`v0.1.1-staging` remains frozen).  
Production routing: not started.

System One may provide routing or risk hints only. Deterministic policy remains the security authority; a model response cannot authorize tool execution.

## Reproduction artifact

- Runner: [smoke.py](smoke.py)
- Raw results: [phase1_smoke.json](results/phase1_smoke.json)
- Official API schema: https://github.com/ollama/ollama/blob/main/docs/openapi.yaml

## Phase 2 — Synthetic canary (2026-11-06)

This was one opt-in, localhost-only run against the already installed `tev1:0.8b` on Ollama `0.40.7`, using `ollama-python 0.6.3`. No model pull, service restart/upgrade, or tool call occurred. The corpus contains 10 synthetic, development-only cases; this is harness/model-behavior exploration, not a real-user benchmark or adoption evidence.

| Metric | Result |
|---|---:|
| Cases | 10 synthetic / development only |
| Route accuracy | 0.50 (5/10) |
| Macro-F1 | 0.4262 |
| False downgrade | 3/5 required-review cases (0.60): `syn-006`, `syn-007`, `syn-010` |
| Escalation / abstention / failure | 2 / 0 / 0 |
| Latency | p50 65.071 ms; p95 3,757.602 ms; max 6,763.377 ms |
| Adoption gate | `false` — no human-adjudicated cases, high-risk holdout, or locked holdout |

The high synthetic false-downgrade rate is a negative signal for this prompt/candidate: the model routed several human-review cases to `codex`. It is not an estimate of real-world error rate because labels and examples are synthetic and small. It reinforces that the deterministic policy/human escalation boundary must remain outside the model. No threshold tuning was done; no production route was changed.

An offline `synthetic-keyword-baseline-v1` was then run on the exact same 10 cases. It achieved 1.00 route accuracy and 0/5 false downgrades, with measured per-rule p50 0.005 ms / p95 0.011 ms. This baseline intentionally uses fixed keyword rules matching this tiny synthetic fixture; therefore the result validates the comparison pipeline only and is not generalizable evidence or a fair real-world superiority claim. The baseline did not read gold labels, risk tiers, review status, or expected actions.

Artifacts:

- Predictions: [phase2_synthetic_tev1_0.8b_20261106.jsonl](results/phase2_synthetic_tev1_0.8b_20261106.jsonl)
- Metrics: [phase2_synthetic_tev1_0.8b_20261106.json](results/phase2_synthetic_tev1_0.8b_20261106.json)
- Deterministic baseline metrics/predictions: [phase2_synthetic_deterministic_20261106.json](results/phase2_synthetic_deterministic_20261106.json), [phase2_synthetic_deterministic_20261106.jsonl](results/phase2_synthetic_deterministic_20261106.jsonl)
- Harness: [evaluate.py](evaluate.py), [run_systemone.py](run_systemone.py)
