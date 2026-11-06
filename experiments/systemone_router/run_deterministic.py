"""Transparent, offline keyword baseline for the synthetic Phase 2 corpus.

This deliberately small rule set exists only to validate the comparison
pipeline. It does not read labels, review status, risk metadata, or gold actions
when routing, and is not intended for production use.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

try:
    from .evaluate import _read_jsonl, evaluate, validate_cases, validate_predictions
except ImportError:  # pragma: no cover - direct script entry point
    from evaluate import _read_jsonl, evaluate, validate_cases, validate_predictions


RULE_VERSION = "synthetic-keyword-baseline-v1"
REVIEW_TERMS = (
    "delete",
    "production",
    "backup",
    "approval",
    "api token",
    "third party",
    "ignore all safety",
    "unreviewed shell",
    "access controls",
    "ambiguous",
    "underspecified",
    "external account setting",
)


def route_input(value: Any) -> str:
    """Apply fixed text rules without consulting corpus labels or annotations."""

    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    lowered = text.casefold()
    if any(term in lowered for term in REVIEW_TERMS):
        return "human_review"
    if "offline" in lowered or "local" in lowered:
        return "local"
    if "google drive" in lowered or "browser" in lowered:
        return "antigravity"
    return "codex"


def predict(cases: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id, case in cases.items():
        started = time.perf_counter()
        route = route_input(case["input"])
        latency_ms = (time.perf_counter() - started) * 1000
        rows.append(
            {
                "case_id": case_id,
                "status": "ok",
                "route": route,
                "escalate": route == "human_review",
                "latency_ms": round(latency_ms, 3),
                "method": RULE_VERSION,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--predictions-output", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    args = parser.parse_args()

    cases = validate_cases(_read_jsonl(args.cases))
    rows = predict(cases)
    predictions = validate_predictions(rows, cases)
    metrics = evaluate(cases, predictions, RULE_VERSION)
    args.predictions_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.predictions_output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    args.metrics_output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rule_version": RULE_VERSION, "metrics_output": str(args.metrics_output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
