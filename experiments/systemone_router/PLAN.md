# System One Router PoC — Phase 2 Evaluation Plan

Plan revision: 2026-11-06
Project: `codex-antigravity-collaboration`
Scope: isolated experiment on `poc/ollama-systemone-router`; no production routing.

## Current state and authority

- Phase 0 and Phase 1 are complete: local Ollama `0.40.7`, `ollama-python 0.6.3`, `tev1:0.8b`, and the `choice` / `noul` / `score` smoke plus five failure probes were exercised on 2026-11-06. See `RUNTIME_AUDIT.md` and `results/phase1_smoke.json`.
- Runtime/smoke evidence is V3. Routing-adoption evidence remains V2; nine smoke requests are not a benchmark.
- The project Drive Current and current engineering plan still classify System One as exploratory/not adopted. This plan is a user-authorized isolated PoC only; it does not revise the production architecture or authorize implementation in `routing/`, the Policy Engine, `main`, or any live runtime.
- The deterministic Policy Engine remains the sole security authority. System One can only emit a routing/risk hint. Errors, uncertainty, invalid output, or high-risk cases must escalate to a strong model or human; they must never lower a deterministic policy result.

## Decision question

On a frozen, representative, human-labeled routing corpus, does a small System One model reduce routing cost/latency while keeping false downgrades acceptably low versus (a) deterministic rules and (b) a generative-router baseline? If evidence is too small, biased, or unstable, the answer is “inconclusive,” not “pass.”

## Guardrails

1. No tool execution, production enforcement, Gateway, daemon, Broker, database, LiteLLM, Envoy/Kubernetes, new framework, Policy Engine changes, credentials, destructive actions, merge, or edits to `main`.
2. Keep all work under `experiments/systemone_router/`. Benchmark inputs must be synthetic or user-approved and redacted; never place production prompts, secrets, personal data, repository contents, or credentials in fixtures or Drive.
3. Pin runtime/model/SDK versions and model digests per run. Do not silently upgrade the host Ollama service during a run. Candidate models requiring a newer runtime are deferred until a separately recorded, controlled runtime change is approved.
4. Keep calibration and holdout cases disjoint. Freeze the holdout labels before tuning thresholds; do not tune on holdout results.
5. Treat confidence as an uncalibrated score until measured. Never infer tool permission from any model output.

## Work packages and ownership

| ID | Work package | Owner | Output / gate |
|---|---|---|---|
| P2-0 | Freeze environment, branch/base, installed model inventory, and evidence inventory | Lead (Sol) | `RUNTIME_AUDIT.md` addendum; environment fingerprint; no host mutation |
| P2-1 | Define schema and assemble 40-case corpus: 30 development/calibration + 10 locked holdout; at least 10 high-risk/escalation cases | Data owner (Luna worker); human adjudicates real cases | `data/cases.jsonl`, `data/README.md`, label-review record. Synthetic cases are explicitly marked and cannot be called “real.” |
| P2-2 | Implement reproducible metrics/evaluation runner and deterministic rules baseline | Benchmark owner (Luna worker) | versioned rules/config, raw result JSON, summary; validation tests |
| P2-3 | Establish generative baseline | Lead + benchmark owner | Reproduce an existing router only if a concrete implementation is found and licensed/available. Otherwise record “not present in repo” and use a clearly labeled prompt baseline only if the user-approved local model is available; no production router is invented. |
| P2-4 | Run `tev1:0.8b` on the frozen corpus; assess candidate `d3:2b` / larger model only after runtime compatibility and hardware checks | Benchmark owner | Per-model digest/config/raw results; failures are explicit fallback, never low-risk defaults |
| P2-5 | Calibrate thresholds on development/calibration split; lock and evaluate holdout once | Lead + independent reviewer | Threshold record, confusion matrices, confidence intervals, false downgrade/upgrade and abstention rates |
| P2-6 | Failure, adversarial, and synthetic risk suite; repeatability and latency/resource measurements | Independent reviewer | Failure matrix, cold/warm p50/p95, concurrency/resource notes; no claims from smoke-only samples |
| P2-7 | A–E decision and writeback | Lead (Sol) | Decision memo in Drive and repo evidence; remain exploratory unless all gates pass |

One writer per file/write-set. Reviewer reads and challenges labels, leakage, and metrics but does not edit the benchmark owner’s files concurrently.

## Corpus contract

Target 40 unique cases. Initial composition: 15 routine capability routes; 10 ambiguous/underspecified or low-confidence requests; 10 high-risk/privacy/tool/approval-boundary requests; 5 adversarial, noisy, or prompt-injection-like requests. Categories may overlap, but every case has one primary expected action and an explicit risk tier.

Each JSONL record must include: `case_id`, `source_type` (`synthetic` or `user_approved_redacted`), `split` (`development`, `calibration`, `holdout`), `input`, `candidate_routes`, `gold_route`, `minimum_safe_routes`, `risk_tier`, `must_escalate`, `deterministic_policy_expectation`, `label_rationale`, and `review_status`. `minimum_safe_routes` explicitly lists the routes that meet the minimum capability/review level for this case (for example, a human-only case permits only `human_review`; a case requiring a strong model may permit `codex` or `human_review`). An `escalate=true` boolean alone never makes an unsafe route safe; the predicted destination must meet the minimum. Explicit `abstain`/failure is safe only when fallback is required. No model may author its own gold label. Holdout labels are adjudicated and frozen before threshold selection. If fewer than 30 human-adjudicated cases or fewer than 10 high-risk cases are available, report the limitation and stop adoption claims; synthetic fixtures may still validate the harness.

## Baselines and measurements

- Deterministic baseline: transparent, versioned rules over explicit capabilities/privacy/risk signals; unresolved and high-risk inputs escalate. Record rule coverage and rule version.
- Generative baseline: identify the actual existing router in accessible project artifacts first. Repo inspection so far found no executable generative router under the PoC branch. Do not describe a newly created prompt harness as the existing production router.
- System One candidates: start with the already installed `tev1:0.8b`; compare larger/alternative models only after compatibility, licensing, and machine resource review. `d3:2b` is a research candidate, not an assumed winner.
- Primary safety metric: **false downgrade rate** = cases whose evaluated route is not in the case's `minimum_safe_routes` (except explicit abstention/fallback). An escalation flag without an acceptable destination does not clear this metric. Report numerator/denominator and exact cases; also report the rate for high-risk cases and all cases.
- Secondary metrics: false upgrade, abstention/escalation, route accuracy, confusion matrix, macro-F1, per-risk recall, fallback rate, malformed/error rate, and cold/warm latency/resource use (p50/p95 where sample count permits).
- Any false downgrade in a high-risk holdout case blocks a positive adoption recommendation. Zero observed events in a small sample is not proof of safety; include uncertainty and sample-size caveats.

## Execution sequence

1. Verify clean PoC branch, base SHA, installed runtime/model, and no pending download. Record exact versions/digests; do not reinstall or pull duplicate model layers.
2. Add schema, validator, and a small synthetic harness canary; unit-test split leakage, missing/unknown labels, invalid probabilities, unavailable server/model, timeout, and deterministic fallback.
3. Prepare the 40-case corpus. Mark generated cases `synthetic`; request sanitized real-case examples from the project owner only if real-workflow representativeness is required. Do not block harness validation on that request.
4. Run deterministic baseline first, then System One. Run any available generative baseline on the same prompt/corpus and record when it is not comparable.
5. Calibrate thresholds only on development/calibration splits; freeze config and corpus hashes; evaluate holdout once.
6. Run high-risk/adversarial/failure tests and latency repeats. Pin model digest and machine/runtime metadata.
7. Independent review challenges labels and false-downgrade calculations. Produce decision A–E: A adopt for a narrowly scoped non-security routing hint; B continue PoC; C retain deterministic-only; D switch candidate project/runtime; E stop. No branch from B or A enables production routing.
8. Update the Drive Current only with status and links after plan/evidence are verified. Keep the Policy Engine unchanged.

## Candidate ecosystem review (2026-11-06)

- **Ollama System One** remains the lowest-friction candidate because Phase 1 is already demonstrated locally. It is suitable for this isolated evaluation, not proof of route quality.
- **llama.cpp server** is the best alternative if exact GGUF/model-server control or runtime footprint becomes the bottleneck; it adds deployment and model lifecycle work. It is not needed before benchmarking the current local setup.
- **Aurelio semantic-router** is a useful non-generative/embedding-routing comparator if the target task is intent/capability selection; its v1 API is a breaking rewrite, so pin the tested version.
- **RouteLLM** is not the Windows/lightweight default: heavier dependencies and its System One integration proposals are not a stable merged dependency. **vLLM Semantic Router** is likely over-scoped for a local Windows PoC.
- `tev1:0.8b` is an experimental smoke model, not a presumed production candidate. Research checked on 2026-11-06 identifies Ollama `0.40.14` as the latest stable release and `d3:2b` as requiring at least `0.40.9`; the verified host is `0.40.7`, so `d3:2b` is currently incompatible. Do not update the shared host or pull `d3:2b` during this benchmark without a separately approved controlled runtime change. First run the existing pinned `tev1:0.8b` harness; only use `d3:2b` after runtime upgrade/compatibility and resource verification. Avoid adding multi-modal models or non-commercial models to this text-routing PoC.
- Community reports around long/multimodal requests, runner/KV-cache contamination, decision-head compatibility, and prompt/temperature sensitivity are individual reports, not universal root causes. Mitigations: bounded input, text-only corpus, process/model restart between contaminated runs, pin model/runtime, and test on the local target.

Sources to recheck before any runtime/model upgrade:

- Ollama Decision API: https://docs.ollama.com/capabilities/decision
- Ollama OpenAPI: https://github.com/ollama/ollama/blob/main/docs/openapi.yaml
- Ollama releases: https://github.com/ollama/ollama/releases
- `d3` and `tev1` model cards: https://ollama.com/library/d3 and https://ollama.com/library/tev1
- llama.cpp server: https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- semantic-router: https://github.com/aurelio-labs/semantic-router
- RouteLLM: https://github.com/lm-sys/RouteLLM
- vLLM Semantic Router: https://github.com/vllm-project/semantic-router
- Ollama issues reviewed: https://github.com/ollama/ollama/issues/19062, https://github.com/ollama/ollama/issues/19090, https://github.com/ollama/ollama/issues/19292, https://github.com/ollama/ollama/issues/18760, https://github.com/ollama/ollama/issues/19137

## Acceptance and stop conditions

- `PLAN_READY`: this plan and human-facing counterpart exist, scope/owners/gates agree, and no conflict with the production Current is implied.
- `HARNESS_READY`: deterministic, System One, and failure paths execute reproducibly on synthetic fixtures; tests pass and raw evidence is retained.
- `EVALUATION_READY`: corpus schema valid, at least 30 human-adjudicated cases and 10 high-risk cases; split hashes frozen; baselines identified.
- `BENCHMARK_COMPLETE`: all candidates run or are explicitly marked unavailable; holdout run once; metrics and uncertainty reported; independent review complete.
- Stop and mark `BLOCKED` for insufficient human labels, host mutation/admin requirement, runtime incompatibility, reproducibility failure, any unexplained high-risk downgrade, or a request to connect production routing/policy.

## Current execution checkpoint

Phase 0/1: `PASS` (V3 runtime/smoke). Phase 2 plan and Repo/Drive writeback: `PASS`. Offline synthetic harness: `23 tests PASS`. One live localhost-only synthetic canary ran against the already-installed `tev1:0.8b`: route accuracy `0.50`, false downgrade `3/5` required-review cases (`0.60`), p95 `3,757.602 ms`; this is a small synthetic-only negative signal, not a real-world rate or adoption result. Dataset readiness is a separate gate (40 reviewed total, 30 development/calibration, 10 locked holdout, including 10 high/critical); even passing it cannot set adoption `PASS` in the per-run evaluator. Adoption requires baseline comparison, locked-holdout performance, uncertainty analysis, and independent A–E review. The real-workflow corpus is not present in the repo and must not be fabricated from private project data. Next: establish a transparent deterministic baseline, then request only human-approved redacted cases for any adoption evaluation.
