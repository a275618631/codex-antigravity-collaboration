"""Offline Phase 2 evaluator for normalized and typed System One predictions.

The evaluator is deliberately independent of Ollama. It consumes a frozen JSONL
case file and a JSONL prediction file, so validation and metric tests do not
change the local model/server state.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROUTES = {"codex", "antigravity", "local", "human_review"}
SPLITS = {"development", "calibration", "holdout"}
RISK_TIERS = {"low", "medium", "high", "critical"}
REQUIRED_ACTIONS = {"route", "strong_model", "human_review"}
REVIEW_STATUSES = {"synthetic_fixture", "pending", "human_adjudicated", "locked_holdout"}
FAILURE_STATUSES = {"error", "fallback", "timeout"}
ABSTENTION_STATUSES = FAILURE_STATUSES | {"abstain"}
MIN_LATENCY_SAMPLES = 5


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
        rows.append(value)
    return rows


def _require_text(row: dict[str, Any], name: str, row_number: int) -> str:
    value = row.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"case row {row_number}: {name} must be a non-empty string")
    return value.strip()


def validate_cases(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Validate the corpus contract and return records keyed by case ID."""

    cases: dict[str, dict[str, Any]] = {}
    for row_number, row in enumerate(rows, 1):
        case_id = _require_text(row, "case_id", row_number)
        if case_id in cases:
            raise ValueError(f"duplicate case_id: {case_id}")
        source_type = _require_text(row, "source_type", row_number)
        if source_type not in {"synthetic", "user_approved_redacted"}:
            raise ValueError(f"case {case_id}: unsupported source_type {source_type!r}")
        split = _require_text(row, "split", row_number)
        if split not in SPLITS:
            raise ValueError(f"case {case_id}: unsupported split {split!r}")
        if source_type == "synthetic" and split != "development":
            raise ValueError(f"case {case_id}: synthetic fixtures must use development split")
        if not isinstance(row.get("input"), (str, dict)):
            raise ValueError(f"case {case_id}: input must be a string or object")
        candidates = row.get("candidate_routes")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError(f"case {case_id}: candidate_routes must be a non-empty list")
        if any(not isinstance(route, str) or not route.strip() for route in candidates):
            raise ValueError(f"case {case_id}: candidate_routes must contain text labels")
        if len(set(candidates)) != len(candidates):
            raise ValueError(f"case {case_id}: candidate_routes must be unique")
        gold_route = _require_text(row, "gold_route", row_number)
        if gold_route not in candidates:
            raise ValueError(f"case {case_id}: gold_route is not a candidate route")
        required_action = row.get("required_action", "human_review" if row.get("must_escalate") else "route")
        if required_action not in REQUIRED_ACTIONS:
            raise ValueError(f"case {case_id}: unsupported required_action {required_action!r}")
        safe_routes = row.get("minimum_safe_routes")
        if not isinstance(safe_routes, list) or not safe_routes:
            raise ValueError(f"case {case_id}: minimum_safe_routes must be a non-empty list")
        if any(not isinstance(route, str) or not route.strip() for route in safe_routes):
            raise ValueError(f"case {case_id}: minimum_safe_routes must contain route labels")
        allowed_routes = set(candidates) | {"abstain"}
        if any(route not in allowed_routes for route in safe_routes):
            raise ValueError(f"case {case_id}: minimum_safe_routes contains an unknown route")
        if gold_route not in safe_routes:
            raise ValueError(f"case {case_id}: minimum_safe_routes must include gold_route")
        risk_tier = _require_text(row, "risk_tier", row_number)
        if risk_tier not in RISK_TIERS:
            raise ValueError(f"case {case_id}: unsupported risk_tier {risk_tier!r}")
        if not isinstance(row.get("must_escalate"), bool):
            raise ValueError(f"case {case_id}: must_escalate must be boolean")
        if not isinstance(row.get("deterministic_policy_expectation"), str) or not row[
            "deterministic_policy_expectation"
        ].strip():
            raise ValueError(f"case {case_id}: deterministic policy expectation is required")
        if not isinstance(row.get("label_rationale"), str) or not row["label_rationale"].strip():
            raise ValueError(f"case {case_id}: label rationale is required")
        if not isinstance(row.get("review_status"), str) or not row["review_status"].strip():
            raise ValueError(f"case {case_id}: review_status is required")
        if row["review_status"] not in REVIEW_STATUSES:
            raise ValueError(f"case {case_id}: unsupported review_status {row['review_status']!r}")
        if source_type == "synthetic" and row["review_status"] != "synthetic_fixture":
            raise ValueError(f"case {case_id}: synthetic cases must use synthetic_fixture review_status")
        if source_type == "user_approved_redacted" and row["review_status"] == "synthetic_fixture":
            raise ValueError(f"case {case_id}: user cases cannot use synthetic_fixture review_status")
        if split == "holdout" and row["review_status"] != "locked_holdout":
            raise ValueError(f"case {case_id}: holdout cases must use locked_holdout review_status")
        if row["review_status"] == "locked_holdout" and split != "holdout":
            raise ValueError(f"case {case_id}: locked_holdout review_status requires holdout split")
        cases[case_id] = row
    if not cases:
        raise ValueError("case corpus is empty")
    return cases


def _finite(value: Any, name: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a JSON number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and number < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return number


def _typed_choice(response: dict[str, Any], case: dict[str, Any], case_id: str) -> tuple[str, float]:
    """Extract and strictly validate a typed System One ``choice`` answer.

    Typed responses must include probabilities and confidence. Normalized
    prediction rows may omit confidence, but a raw typed response is accepted
    only when every candidate has a finite probability in [0, 1] and the sum is
    within 0.02 of one. This keeps malformed model output on the explicit
    fallback path instead of silently treating it as a route.
    """

    answers = response.get("answers")
    if not isinstance(answers, dict):
        raise ValueError(f"prediction {case_id}: typed response is missing answers")
    choice = answers.get("choice")
    if not isinstance(choice, dict) or choice.get("type") != "choice":
        raise ValueError(f"prediction {case_id}: typed response is missing a choice answer")
    candidates = set(case["candidate_routes"])
    route = choice.get("choice")
    if not isinstance(route, str) or route not in candidates:
        raise ValueError(f"prediction {case_id}: typed choice is not a candidate route")
    probabilities = choice.get("probabilities")
    if not isinstance(probabilities, dict) or set(probabilities) != candidates:
        raise ValueError(f"prediction {case_id}: typed probabilities must match candidate routes")
    total = 0.0
    for candidate in candidates:
        value = probabilities[candidate]
        if isinstance(value, bool):
            raise ValueError(f"prediction {case_id}: typed probability must be numeric")
        total += _finite(value, f"prediction {case_id} probability {candidate}", minimum=0, maximum=1)
    if abs(total - 1.0) > 0.02:
        raise ValueError(f"prediction {case_id}: typed probabilities sum to {total:g}")
    confidence = choice.get("confidence")
    if isinstance(confidence, bool):
        raise ValueError(f"prediction {case_id}: typed confidence must be numeric")
    return route, _finite(confidence, f"prediction {case_id} confidence", minimum=0, maximum=1)


def normalize_prediction(row: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Normalize a prediction row, including a typed System One choice response."""

    case_id = row.get("case_id")
    if not isinstance(case_id, str) or case_id != case["case_id"]:
        raise ValueError("prediction case_id does not match its case")
    status = row.get("status", "ok")
    if not isinstance(status, str) or not status.strip():
        raise ValueError(f"prediction {case_id}: status must be text")
    status = status.strip().lower()

    route = row.get("route", row.get("action"))
    confidence = row.get("confidence")
    response = row.get("response")
    if response is not None:
        if not isinstance(response, dict):
            raise ValueError(f"prediction {case_id}: typed response must be an object")
        route, confidence = _typed_choice(response, case, case_id)

    escalate = row.get("escalate", False)
    if not isinstance(escalate, bool):
        raise ValueError(f"prediction {case_id}: escalate must be boolean")
    if status in ABSTENTION_STATUSES:
        escalate = True
    if route is None and escalate:
        route = "abstain"
    if not isinstance(route, str) or not route.strip():
        raise ValueError(f"prediction {case_id}: route is required unless it explicitly abstains")
    route = route.strip()
    if route not in set(case["candidate_routes"]) | {"abstain"}:
        raise ValueError(f"prediction {case_id}: unknown route {route!r}")
    if confidence is not None:
        confidence = _finite(confidence, f"prediction {case_id} confidence", minimum=0, maximum=1)
    latency_ms = row.get("latency_ms")
    if latency_ms is not None:
        latency_ms = _finite(latency_ms, f"prediction {case_id} latency_ms", minimum=0)
    return {
        "case_id": case_id,
        "route": route,
        "escalate": escalate or route == "abstain",
        "status": status,
        "confidence": confidence,
        "latency_ms": latency_ms,
    }


def validate_predictions(
    rows: Iterable[dict[str, Any]], cases: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    predictions: dict[str, dict[str, Any]] = {}
    for row_number, row in enumerate(rows, 1):
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id not in cases:
            raise ValueError(f"prediction row {row_number}: unknown case_id")
        if case_id in predictions:
            raise ValueError(f"duplicate prediction case_id: {case_id}")
        predictions[case_id] = normalize_prediction(row, cases[case_id])
    missing = sorted(set(cases) - set(predictions))
    if missing:
        raise ValueError(f"missing predictions for case(s): {', '.join(missing)}")
    return predictions


def _percentile(values: list[float], percentile: float) -> float:
    if len(values) == 1:
        return round(values[0], 3)
    position = (len(values) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(values[lower], 3)
    value = values[lower] + (values[upper] - values[lower]) * (position - lower)
    return round(value, 3)


def latency_summary(values: Iterable[float | None]) -> dict[str, Any]:
    samples = sorted(float(value) for value in values if value is not None)
    if len(samples) < MIN_LATENCY_SAMPLES:
        return {
            "status": "insufficient_sample",
            "sample_count": len(samples),
            "required_sample_count": MIN_LATENCY_SAMPLES,
        }
    return {
        "status": "measured",
        "sample_count": len(samples),
        "min_ms": round(samples[0], 3),
        "p50_ms": _percentile(samples, 50),
        "p95_ms": _percentile(samples, 95),
        "max_ms": round(samples[-1], 3),
    }


def _macro_f1(confusion: dict[str, Counter[str]], labels: set[str]) -> float | None:
    scores: list[float] = []
    for label in sorted(labels):
        true_positive = confusion.get(label, Counter()).get(label, 0)
        actual = sum(confusion.get(label, Counter()).values())
        predicted = sum(row.get(label, 0) for row in confusion.values())
        if actual == 0 and predicted == 0:
            continue
        precision = true_positive / predicted if predicted else 0.0
        recall = true_positive / actual if actual else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return round(sum(scores) / len(scores), 4) if scores else None


def evaluate(
    cases: dict[str, dict[str, Any]], predictions: dict[str, dict[str, Any]], method: str
) -> dict[str, Any]:
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    false_downgrade_cases: list[str] = []
    false_upgrade_cases: list[str] = []
    escalation_count = 0
    abstention_count = 0
    failure_count = 0
    correct_count = 0
    labels: set[str] = set()
    for case_id, case in cases.items():
        prediction = predictions[case_id]
        gold = case["gold_route"]
        route = prediction["route"]
        labels.update({gold, route})
        confusion[gold][route] += 1
        if route == gold:
            correct_count += 1
        is_escalation = (
            prediction["escalate"]
            or route == "human_review"
            or prediction["status"] in ABSTENTION_STATUSES
        )
        if is_escalation:
            escalation_count += 1
        if route == "abstain" or prediction["status"] in ABSTENTION_STATUSES:
            abstention_count += 1
        if prediction["status"] in FAILURE_STATUSES:
            failure_count += 1
        requires_safe_action = (
            case.get("required_action", "human_review" if case["must_escalate"] else "route") != "route"
            or bool(case["must_escalate"])
            or gold == "human_review"
        )
        if requires_safe_action and route not in set(case["minimum_safe_routes"]):
            false_downgrade_cases.append(case_id)
        if not requires_safe_action and (prediction["escalate"] or route == "human_review"):
            false_upgrade_cases.append(case_id)

    downgrade_denominator = sum(
        1
        for case in cases.values()
        if case.get("required_action", "human_review" if case["must_escalate"] else "route") != "route"
        or case["must_escalate"]
        or case["gold_route"] == "human_review"
    )
    route_count = len(cases)
    confusion_json = {
        gold: {predicted: row[predicted] for predicted in sorted(labels)}
        for gold, row in sorted(confusion.items())
    }
    reviewed_cases = [
        case
        for case in cases.values()
        if case["source_type"] == "user_approved_redacted"
        and case["review_status"] in {"human_adjudicated", "locked_holdout"}
    ]
    high_risk_reviewed = [case for case in reviewed_cases if case["risk_tier"] in {"high", "critical"}]
    development_calibration = [
        case for case in reviewed_cases if case["split"] in {"development", "calibration"}
    ]
    locked_holdout = [
        case
        for case in cases.values()
        if case["source_type"] == "user_approved_redacted"
        and case["split"] == "holdout"
        and case["review_status"] == "locked_holdout"
    ]
    dataset_readiness_reasons: list[str] = []
    if len(reviewed_cases) < 40:
        dataset_readiness_reasons.append(f"reviewed_cases={len(reviewed_cases)}; required>=40")
    if len(development_calibration) < 30:
        dataset_readiness_reasons.append(
            f"development_calibration_cases={len(development_calibration)}; required>=30"
        )
    if len(locked_holdout) < 10:
        dataset_readiness_reasons.append(f"locked_holdout_cases={len(locked_holdout)}; required>=10")
    if len(high_risk_reviewed) < 10:
        dataset_readiness_reasons.append(
            f"high_critical_reviewed={len(high_risk_reviewed)}; required>=10"
        )
    dataset_ready = not dataset_readiness_reasons
    if all(case["source_type"] == "synthetic" for case in cases.values()):
        evidence_status = "synthetic_non_adoption"
    elif dataset_ready:
        evidence_status = "adjudicated_candidate"
    else:
        evidence_status = "unadjudicated_non_adoption"
    return {
        "method": method,
        "evidence_status": evidence_status,
        "dataset_readiness_gate": {
            "status": "PASS" if dataset_ready else "BLOCKED",
            "passed": dataset_ready,
            "reasons": dataset_readiness_reasons,
            "reviewed_case_count": len(reviewed_cases),
            "development_calibration_case_count": len(development_calibration),
            "high_critical_reviewed_count": len(high_risk_reviewed),
            "locked_holdout_case_count": len(locked_holdout),
        },
        "adoption_gate": False,
        "adoption_gate_status": {
            "status": "BLOCKED",
            "reasons": [
                "adoption is not assessed by this per-run evaluator; it requires baseline comparison, locked-holdout performance, uncertainty analysis, and independent A-E review"
            ],
        },
        "case_count": route_count,
        "source_type_counts": dict(Counter(case["source_type"] for case in cases.values())),
        "split_counts": dict(Counter(case["split"] for case in cases.values())),
        "route_accuracy": round(correct_count / route_count, 4) if route_count else None,
        "macro_f1": _macro_f1(confusion, labels),
        "confusion_matrix": confusion_json,
        "false_downgrade": {
            "numerator": len(false_downgrade_cases),
            "denominator": downgrade_denominator,
            "rate": round(len(false_downgrade_cases) / downgrade_denominator, 4)
            if downgrade_denominator
            else None,
            "case_ids": false_downgrade_cases,
        },
        "required_action_counts": dict(Counter(
            case.get("required_action", "human_review" if case["must_escalate"] else "route")
            for case in cases.values()
        )),
        "false_upgrade": {
            "numerator": len(false_upgrade_cases),
            "denominator": route_count - downgrade_denominator,
            "case_ids": false_upgrade_cases,
        },
        "escalation_count": escalation_count,
        "abstention_count": abstention_count,
        "failure_count": failure_count,
        "latency_ms": latency_summary(prediction["latency_ms"] for prediction in predictions.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--method", default="unknown", help="label for the evaluated producer")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = validate_cases(_read_jsonl(args.cases))
    predictions = validate_predictions(_read_jsonl(args.predictions), cases)
    result = evaluate(cases, predictions, args.method)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
