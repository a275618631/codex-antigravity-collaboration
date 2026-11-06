from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.systemone_router.evaluate import (
    evaluate,
    latency_summary,
    validate_cases,
    validate_predictions,
)


CASES_PATH = Path(__file__).parents[1] / "data" / "cases.jsonl"


def load_cases() -> dict[str, dict[str, object]]:
    rows = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines()]
    return validate_cases(rows)


def test_synthetic_canary_is_development_only() -> None:
    cases = load_cases()
    assert len(cases) == 10
    assert {case["source_type"] for case in cases.values()} == {"synthetic"}
    assert {case["split"] for case in cases.values()} == {"development"}
    assert sum(bool(case["must_escalate"]) for case in cases.values()) == 5


def test_perfect_normalized_predictions_and_latency() -> None:
    cases = load_cases()
    rows = [
        {"case_id": case_id, "route": case["gold_route"], "latency_ms": index + 1}
        for index, (case_id, case) in enumerate(cases.items())
    ]
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "deterministic_fixture")

    assert result["route_accuracy"] == 1.0
    assert result["false_downgrade"] == {"numerator": 0, "denominator": 5, "rate": 0.0, "case_ids": []}
    assert result["escalation_count"] == 5
    assert result["evidence_status"] == "synthetic_non_adoption"
    assert result["adoption_gate"] is False
    assert result["latency_ms"]["status"] == "measured"
    assert result["latency_ms"]["sample_count"] == 10


def test_typed_systemone_response_and_bad_high_risk_route_are_counted() -> None:
    cases = load_cases()
    rows = []
    for case_id, case in cases.items():
        if case_id == "syn-006":
            rows.append({"case_id": case_id, "route": "local"})
        else:
            rows.append(
                {
                    "case_id": case_id,
                    "response": {
                        "answers": {
                            "choice": {
                                "type": "choice",
                                "choice": case["gold_route"],
                                "probabilities": {
                                    candidate: 1.0 if candidate == case["gold_route"] else 0.0
                                    for candidate in case["candidate_routes"]
                                },
                                "confidence": 0.8,
                            }
                        }
                    },
                    "latency_ms": 10,
                }
            )
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "systemone_fixture")

    assert result["false_downgrade"]["numerator"] == 1
    assert result["false_downgrade"]["case_ids"] == ["syn-006"]
    assert result["failure_count"] == 0


@pytest.mark.parametrize(
    "choice_patch, message",
    [
        ({"choice": "not-a-candidate"}, "not a candidate"),
        ({"probabilities": {"codex": 1.0}}, "must match candidate"),
        (
            {
                "probabilities": {
                    "codex": float("nan"),
                    "antigravity": 0.0,
                    "local": 0.0,
                    "human_review": 0.0,
                }
            },
            "must be finite",
        ),
        (
            {
                "probabilities": {
                    "codex": 0.8,
                    "antigravity": 0.0,
                    "local": 0.0,
                    "human_review": 0.0,
                }
            },
            "sum to",
        ),
        ({"confidence": 1.5}, "must be <= 1"),
    ],
)
def test_invalid_typed_response_is_rejected(choice_patch: dict[str, object], message: str) -> None:
    cases = load_cases()
    case = cases["syn-001"]
    choice = {
        "type": "choice",
        "choice": "codex",
        "probabilities": {candidate: 0.25 for candidate in case["candidate_routes"]},
        "confidence": 0.8,
    }
    choice.update(choice_patch)
    with pytest.raises(ValueError, match=message):
        validate_predictions(
            [{"case_id": "syn-001", "response": {"answers": {"choice": choice}}}], cases
        )


def test_explicit_fallback_row_is_accepted() -> None:
    cases = load_cases()
    rows = [
        {"case_id": case_id, "status": "fallback", "route": "abstain", "escalate": True}
        for case_id in cases
    ]
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "systemone_fixture")
    assert result["failure_count"] == 10
    assert result["false_downgrade"]["numerator"] == 0


def test_escalate_flag_does_not_make_lower_route_safe() -> None:
    cases = load_cases()
    rows = [
        {"case_id": case_id, "route": "local", "escalate": True}
        if case["required_action"] == "human_review"
        else {"case_id": case_id, "route": case["gold_route"]}
        for case_id, case in cases.items()
    ]
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "unsafe_escalation_fixture")
    assert result["false_downgrade"]["numerator"] == 5


def test_explicit_abstention_is_safe_and_not_a_false_downgrade() -> None:
    cases = load_cases()
    rows = [
        {"case_id": case_id, "status": "abstain", "escalate": True}
        if case["must_escalate"]
        else {"case_id": case_id, "route": case["gold_route"]}
        for case_id, case in cases.items()
    ]
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "systemone_fixture")

    assert result["false_downgrade"]["numerator"] == 0
    assert result["abstention_count"] == 5
    assert result["escalation_count"] == 5


def test_schema_rejects_synthetic_holdout() -> None:
    rows = [json.loads(CASES_PATH.read_text(encoding="utf-8").splitlines()[0])]
    rows[0]["split"] = "holdout"
    with pytest.raises(ValueError, match="synthetic fixtures"):
        validate_cases(rows)


def test_missing_prediction_is_rejected() -> None:
    cases = load_cases()
    with pytest.raises(ValueError, match="missing predictions"):
        validate_predictions([{"case_id": "syn-001", "route": "codex"}], cases)


def test_latency_summary_is_suppressed_for_small_samples() -> None:
    result = latency_summary([1, 2, 3, 4])
    assert result == {"status": "insufficient_sample", "sample_count": 4, "required_sample_count": 5}


def test_review_status_is_allow_listed() -> None:
    rows = [json.loads(CASES_PATH.read_text(encoding="utf-8").splitlines()[0])]
    rows[0]["review_status"] = "unreviewed_but_trusted"
    with pytest.raises(ValueError, match="unsupported review_status"):
        validate_cases(rows)


def test_user_approved_source_type_does_not_imply_adjudication() -> None:
    cases = load_cases()
    for case in cases.values():
        case["source_type"] = "user_approved_redacted"
        case["review_status"] = "pending"
    rows = [
        {"case_id": case_id, "route": case["gold_route"]}
        for case_id, case in cases.items()
    ]
    predictions = validate_predictions(rows, cases)
    result = evaluate(cases, predictions, "review_status_fixture")
    assert result["adoption_gate"] is False
    assert result["adoption_gate_status"]["status"] == "BLOCKED"
    assert result["dataset_readiness_gate"]["reviewed_case_count"] == 0
    assert result["evidence_status"] == "unadjudicated_non_adoption"


def test_dataset_readiness_does_not_imply_adoption() -> None:
    source = list(load_cases().values())
    cases_rows = []
    predictions_rows = []
    for index in range(40):
        case = dict(source[index % len(source)])
        case["case_id"] = f"reviewed-{index + 1:02d}"
        case["source_type"] = "user_approved_redacted"
        if index < 10:
            case["split"] = "holdout"
            case["review_status"] = "locked_holdout"
        else:
            case["split"] = "development" if index < 25 else "calibration"
            case["review_status"] = "human_adjudicated"
        if index < 10:
            case["risk_tier"] = "high"
        cases_rows.append(case)
        predictions_rows.append({"case_id": case["case_id"], "route": "codex"})

    cases = validate_cases(cases_rows)
    predictions = validate_predictions(predictions_rows, cases)
    result = evaluate(cases, predictions, "poor_fixture")

    assert result["dataset_readiness_gate"]["passed"] is True
    assert result["route_accuracy"] < 1.0
    assert result["adoption_gate"] is False
    assert result["adoption_gate_status"]["status"] == "BLOCKED"


def test_numeric_strings_are_rejected() -> None:
    cases = load_cases()
    with pytest.raises(ValueError, match="must be a JSON number"):
        validate_predictions(
            [{"case_id": "syn-001", "route": "codex", "latency_ms": "12.5"}], cases
        )


def test_boolean_confidence_and_latency_are_rejected() -> None:
    cases = load_cases()
    with pytest.raises(ValueError, match="must be a JSON number"):
        validate_predictions([{"case_id": "syn-001", "route": "codex", "confidence": True}], cases)
    with pytest.raises(ValueError, match="must be a JSON number"):
        validate_predictions([{"case_id": "syn-001", "route": "codex", "latency_ms": False}], cases)
