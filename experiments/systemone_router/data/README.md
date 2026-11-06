# Phase 2 synthetic canary

`cases.jsonl` is a small offline development fixture for validating the Phase 2
evaluation harness. It intentionally contains synthetic tasks only; it is not a
real-user corpus and must not be used to claim routing quality or safety.

Contract highlights:

- every record has `source_type: "synthetic"` and `split: "development"`;
- `minimum_safe_routes` is the explicit minimum-capability/review allow-list;
  `human_review` fixtures allow only `human_review` or explicit `abstain`;
- `required_action` distinguishes ordinary routing from `strong_model` and
  `human_review` requirements;
- labels are explicit and human-authored fixture labels, not model-generated;
- high-risk records use `gold_route: "human_review"` and
  `must_escalate: true`;
- no record contains private prompts, credentials, repository contents, or tool
  calls.

Use the evaluator with pre-recorded predictions (no Ollama connection):

```powershell
python experiments/systemone_router/evaluate.py `
  --cases experiments/systemone_router/data/cases.jsonl `
  --predictions path\to\predictions.jsonl `
  --method systemone `
  --output experiments/systemone_router/results/phase2_canary.json
```

Prediction rows may use normalized `route`, `escalate`, `confidence`, and
`latency_ms` fields. A typed System One response can instead be placed in a
`response` object. For a typed response, `answers.choice` is required with a
candidate `choice`, a `probabilities` object containing exactly every candidate
with finite values in `[0, 1]` whose sum is within `0.02` of `1.0`, and finite
`confidence` in `[0, 1]`. Normalized rows may omit confidence. Invalid typed
responses are rejected by the evaluator; the live runner records them as an
explicit `fallback`/`abstain` row. Errors or abstentions must never become a
low-risk route.

The evaluator's `false_downgrade` metric checks membership in
`minimum_safe_routes`; an `escalate: true` flag alone cannot make a lower route
safe. Synthetic-only output is marked `evidence_status:
synthetic_non_adoption` and `adoption_gate: false`. The adoption gate remains
`false`/`BLOCKED` unless there are at least 30 `user_approved_redacted` cases
with `human_adjudicated` or `locked_holdout` status, at least 10 high/critical
reviewed cases, and at least one locked holdout case; source type alone never
implies adjudication. Failed criteria are listed in `adoption_gate_status`.
