from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import platform
import socketserver
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
import ollama
from ollama import Client


BASE_URL = "http://127.0.0.1:11434"
MODEL = "tev1:0.8b"


class StallHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.recv(4096)
        time.sleep(2)


def as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(f"unsupported response type: {type(value)!r}")


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is non-finite")
    return number


def probability(value: Any, label: str) -> float:
    number = finite_number(value, label)
    if number < 0 or number > 1:
        raise ValueError(f"{label} is outside [0, 1]")
    return number


def validate_answer(kind: str, response: Any, criteria: Any) -> dict[str, Any]:
    payload = as_dict(response)
    answers = payload.get("answers")
    if not isinstance(answers, dict) or kind not in answers:
        raise ValueError(f"missing answer: {kind}")
    answer = answers[kind]
    if not isinstance(answer, dict) or answer.get("type") != kind:
        raise ValueError(f"unexpected answer type for {kind}")

    if kind == "choice":
        probs = answer.get("probabilities")
        if not isinstance(probs, dict) or set(probs) != set(criteria):
            raise ValueError("choice probabilities do not match requested candidates")
        if answer.get("choice") not in criteria:
            raise ValueError("choice is not one of the requested criteria")
        total = sum(probability(v, f"choice probability {k}") for k, v in probs.items())
        if abs(total - 1.0) > 0.02:
            raise ValueError(f"choice probabilities sum to {total}")
        probability(answer.get("confidence"), "choice confidence")
    elif kind == "noul":
        probability(answer.get("noul"), "noul")
    elif kind == "score":
        score = finite_number(answer.get("score"), "score")
        if score < 0 or score > len(criteria) - 1:
            raise ValueError("score is outside the requested scale")
        probs = answer.get("probabilities")
        expected = {str(i) for i in range(len(criteria))}
        if not isinstance(probs, dict) or set(probs) != expected:
            raise ValueError("score probabilities do not match requested scale")
        total = sum(probability(v, f"score probability {k}") for k, v in probs.items())
        if abs(total - 1.0) > 0.02:
            raise ValueError(f"score probabilities sum to {total}")
        probability(answer.get("confidence"), "score confidence")
    else:
        raise ValueError(f"unknown answer kind: {kind}")
    return payload


def timed_call(call: Callable[[], Any]) -> tuple[Any, float]:
    started = time.perf_counter()
    result = call()
    return result, round((time.perf_counter() - started) * 1000, 3)


def exercise_kind(
    client: Client,
    kind: str,
    state: Any,
    question: dict[str, Any],
    criteria: Any,
    first_request_is_cold: bool,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for index in range(3):
        response, latency_ms = timed_call(
            lambda: client.systemone(
                model=MODEL,
                state=state,
                questions={kind: question},
                keep_alive="5m",
            )
        )
        payload = validate_answer(kind, response, criteria)
        attempts.append(
            {
                "attempt": index + 1,
                "latency_ms": latency_ms,
                "temperature": "cold" if first_request_is_cold and index == 0 else "warm",
                "response": payload,
            }
        )
    return {"status": "PASS", "attempts": attempts}


def expected_error(name: str, call: Callable[[], Any]) -> dict[str, Any]:
    try:
        call()
    except Exception as exc:  # SDK and transport exceptions differ by failure surface.
        return {
            "status": "PASS",
            "fallback_required": True,
            "error_type": type(exc).__name__,
            "message": str(exc)[:500],
        }
    return {"status": "FAIL", "fallback_required": True, "message": f"{name} unexpectedly succeeded"}


def version_at_least(actual: str, required: str) -> bool:
    try:
        actual_parts = tuple(int(part) for part in actual.split(".")[:3])
        required_parts = tuple(int(part) for part in required.split(".")[:3])
    except (AttributeError, ValueError):
        return False
    return actual_parts >= required_parts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    client = Client(host=BASE_URL, timeout=120)
    with httpx.Client(base_url=BASE_URL, timeout=10) as http:
        version = http.get("/api/version").json()
        tags = http.get("/api/tags").json()
        loaded_before = http.get("/api/ps").json().get("models", [])

    model_info = next((m for m in tags.get("models", []) if m.get("name") == MODEL), None)
    results: dict[str, Any] = {
        "date": datetime.now(timezone.utc).astimezone().isoformat(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "ollama_python": importlib.metadata.version("ollama"),
        "sdk_has_systemone": callable(getattr(ollama, "systemone", None)),
        "server_version": version.get("version"),
        "model": MODEL,
        "model_metadata": model_info,
        "model_was_loaded_before_smoke": any(
            item.get("name") == MODEL or item.get("model") == MODEL for item in loaded_before
        ),
        "cold_latency_ms": None,
        "warm_latency_ms": [],
        "smoke": {},
        "failures": {},
    }

    choice_criteria = {
        "codex": "Repository implementation and engineering",
        "antigravity": "Google ecosystem or browser-heavy work",
        "local": "Private or offline work",
        "human_review": "High-risk or ambiguous work requiring review",
    }
    results["smoke"]["choice"] = exercise_kind(
        client,
        "choice",
        {"task": "請修正 Python repository 中 failing unit tests"},
        {"type": "choice", "instructions": "Which route should handle this task?", "criteria": choice_criteria},
        choice_criteria,
        first_request_is_cold=not results["model_was_loaded_before_smoke"],
    )

    noul_question = {"type": "noul", "instructions": "Does this task require explicit approval?"}
    for kind, (state, question, criteria) in [
        (
            "noul",
            (
                "Delete production data without approval",
                noul_question,
                None,
            ),
        ),
        (
            "score",
            (
                {"task": "Force push the production branch and delete recovery tags"},
                {
                    "type": "score",
                    "instructions": "Rate the escalation level.",
                    "criteria": ["Low risk", "Review recommended", "Approval required", "Deny"],
                },
                ["Low risk", "Review recommended", "Approval required", "Deny"],
            ),
        ),
    ]:
        results["smoke"][kind] = exercise_kind(
            client, kind, state, question, criteria, first_request_is_cold=False
        )

    all_latencies = [
        attempt["latency_ms"]
        for case in results["smoke"].values()
        for attempt in case.get("attempts", [])
    ]
    first_cold = next(
        (
            attempt["latency_ms"]
            for case in results["smoke"].values()
            for attempt in case.get("attempts", [])
            if attempt["temperature"] == "cold"
        ),
        None,
    )
    results["cold_latency_ms"] = first_cold
    results["warm_latency_ms"] = [
        attempt["latency_ms"]
        for case in results["smoke"].values()
        for attempt in case.get("attempts", [])
        if attempt["temperature"] == "warm"
    ]

    results["failures"]["missing_model"] = expected_error(
        "missing model",
        lambda: client.systemone(
            model="systemone-model-does-not-exist",
            state="probe",
            questions={"route": {"type": "noul", "instructions": "Is this a probe?"}},
        ),
    )
    results["failures"]["bad_schema"] = expected_error(
        "bad schema",
        lambda: client.systemone(
            model=MODEL,
            state="probe",
            questions={
                "route": {
                    "type": "choice",
                    "instructions": "Pick one.",
                    "criteria": {"a": {"nested": "unsupported"}, "b": "valid"},
                }
            },
        ),
    )
    unavailable = Client(host="http://127.0.0.1:9", timeout=0.5)
    results["failures"]["server_down"] = expected_error(
        "server down",
        lambda: unavailable.systemone(
            model=MODEL,
            state="probe",
            questions={"route": {"type": "noul", "instructions": "Is this a probe?"}},
        ),
    )
    with socketserver.TCPServer(("127.0.0.1", 0), StallHandler) as server:
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        stalled = Client(host=f"http://127.0.0.1:{server.server_address[1]}", timeout=0.1)
        results["failures"]["timeout"] = expected_error(
            "timeout",
            lambda: stalled.systemone(
                model=MODEL,
                state="probe",
                questions={"route": {"type": "noul", "instructions": "Is this a probe?"}},
            ),
        )
        thread.join(timeout=3)

    invalid_numeric_cases = {
        "nan": float("nan"),
        "positive_infinity": float("inf"),
        "negative_infinity": float("-inf"),
        "out_of_range": 1.01,
    }
    invalid_numeric_results = {
        label: expected_error(
            label,
            lambda value=value: validate_answer(
                "noul",
                {"answers": {"noul": {"type": "noul", "noul": value}}},
                None,
            ),
        )
        for label, value in invalid_numeric_cases.items()
    }
    results["failures"]["invalid_numeric"] = {
        "status": "PASS" if all(v["status"] == "PASS" for v in invalid_numeric_results.values()) else "FAIL",
        "cases": invalid_numeric_results,
    }

    checks = [
        all(test.get("status") == "PASS" for test in results["smoke"].values()),
        all(test.get("status") == "PASS" for test in results["failures"].values()),
        model_info is not None,
        "decision" in (model_info or {}).get("capabilities", []),
        results["sdk_has_systemone"],
        version_at_least(str(results["server_version"]), "0.35.0"),
        results["cold_latency_ms"] is not None,
        len(results["warm_latency_ms"]) >= 1,
    ]
    results["phase1_gate"] = "PHASE1_SMOKE_PASS" if all(checks) else "PHASE1_SMOKE_FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "phase1_gate": results["phase1_gate"],
                "model_digest": (model_info or {}).get("digest"),
                "cold_latency_ms": results["cold_latency_ms"],
                "warm_samples": len(results["warm_latency_ms"]),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0 if results["phase1_gate"] == "PHASE1_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
