from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.systemone_router.evaluate import validate_cases
from experiments.systemone_router.run_systemone import (
    run_cases,
    validate_local_host,
)


CASES_PATH = Path(__file__).parents[1] / "data" / "cases.jsonl"


def load_cases() -> dict[str, dict[str, object]]:
    rows = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines()]
    return validate_cases(rows)


class FakeClient:
    def __init__(self, *, invalid: bool = False, error: BaseException | None = None) -> None:
        self.invalid = invalid
        self.error = error
        self.calls: list[dict[str, object]] = []

    def systemone(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        criteria = kwargs["questions"]["choice"]["criteria"]  # type: ignore[index]
        candidates = list(criteria)
        probabilities = {candidate: 1.0 / len(candidates) for candidate in candidates}
        if self.invalid:
            probabilities[candidates[0]] = 0.9
        return {
            "answers": {
                "choice": {
                    "type": "choice",
                    "choice": candidates[0],
                    "probabilities": probabilities,
                    "confidence": 0.75,
                }
            }
        }


def config() -> dict[str, object]:
    return {
        "host": "http://127.0.0.1:11434",
        "model": "tev1:0.8b",
        "timeout_seconds": 1.0,
        "keep_alive": "5m",
        "tools_enabled": False,
        "auto_pull": False,
    }


def test_local_host_guard_rejects_remote_and_credentials() -> None:
    assert validate_local_host("http://localhost:11434") == "http://localhost:11434"
    with pytest.raises(ValueError, match="localhost"):
        validate_local_host("https://ollama.example.invalid")
    with pytest.raises(ValueError, match="credentials"):
        validate_local_host("http://user:pass@127.0.0.1:11434")


def test_mocked_client_emits_normalized_success_rows() -> None:
    cases = load_cases()
    client = FakeClient()
    rows = run_cases(cases, client, config())
    assert len(rows) == 10
    assert {row["status"] for row in rows} == {"ok"}
    assert all(row["source_type"] == "synthetic" for row in rows)
    assert all(row["split"] == "development" for row in rows)
    assert all(len(row["response_digest"]) == 64 for row in rows)
    assert len(client.calls) == 10
    assert all(call["keep_alive"] == "5m" for call in client.calls)


def test_invalid_typed_response_becomes_explicit_fallback() -> None:
    cases = load_cases()
    rows = run_cases(cases, FakeClient(invalid=True), config())
    assert {row["status"] for row in rows} == {"fallback"}
    assert all(row["route"] == "abstain" for row in rows)
    assert all(row["fallback_required"] is True for row in rows)
    assert all(row["error_type"] == "InvalidTypedResponse" for row in rows)


def test_transport_error_becomes_fallback_without_retry_or_pull() -> None:
    cases = load_cases()
    client = FakeClient(error=TimeoutError("synthetic timeout"))
    rows = run_cases(cases, client, config())
    assert {row["status"] for row in rows} == {"timeout"}
    assert all(row["response_digest"] is None for row in rows)
    assert len(client.calls) == 10
