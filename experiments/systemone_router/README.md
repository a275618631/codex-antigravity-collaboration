# Ollama System One Router PoC

Phase 1 validates the local Ollama System One runtime and its typed `choice`, `noul`, and `score` responses. It does not implement agent routing or security policy.

## Scope and safety

- System One output is a routing or risk hint only.
- Deterministic policy remains the security decision layer.
- Any System One, model, schema, transport, or numeric validation failure requires fallback to a stronger model, human review, or rejection.
- This PoC does not call tools, change production routing, or connect to the Policy Engine.

## Reproduce

Use Python 3.12 and install the pinned official client in an isolated environment:

```powershell
python -m venv .venv-systemone
.\.venv-systemone\Scripts\python.exe -m pip install ollama==0.6.3
```

Ensure Ollama is running and `tev1:0.8b` is available, then run:

```powershell
.\.venv-systemone\Scripts\python.exe experiments\systemone_router\smoke.py `
  --output experiments\systemone_router\results\phase1_smoke.json
```

The script runs three requests for each response type and controlled failure probes. The first request is labeled cold only when `/api/ps` shows the model was not already loaded; later requests are recorded as warm. The invalid numeric checks use local fixtures to verify fail-closed validation.

See [RUNTIME_AUDIT.md](RUNTIME_AUDIT.md) for the captured environment and gate outcome. The JSON file contains raw successful responses and measured latencies; do not use it as a routing benchmark or correctness calibration set.

## Phase 2

The complete evaluation sequence, dataset contract, metric definitions, project comparisons, ownership, and gates are in [PLAN.md](PLAN.md). The plan is for an isolated PoC only; it does not authorize production routing, Policy Engine changes, or edits to `main`.
