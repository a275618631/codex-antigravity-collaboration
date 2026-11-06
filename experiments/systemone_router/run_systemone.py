"""Opt-in localhost runner for the Phase 2 System One prediction JSONL.

This module never pulls a model, starts/stops Ollama, invokes tools, or changes
the host runtime. It only calls ``Client.systemone`` on an already-running
localhost endpoint. Any transport or typed-schema error becomes an explicit
``fallback``/``abstain`` row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:  # Supports both package imports in tests and direct script execution.
    from .evaluate import _read_jsonl, normalize_prediction, validate_cases
except ImportError:  # pragma: no cover - exercised by the CLI entry point.
    from evaluate import _read_jsonl, normalize_prediction, validate_cases


DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "tev1:0.8b"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_local_host(host: str) -> str:
    """Allow only explicit localhost URLs; reject remote or credentialed URLs."""

    parsed = urlparse(host)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOCAL_HOSTS:
        raise ValueError("host must be an http(s) localhost URL")
    if parsed.username or parsed.password:
        raise ValueError("host must not include credentials")
    return host.rstrip("/")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported response type: {type(value)!r}")


def response_digest(response: Any) -> tuple[Any, str]:
    payload = _jsonable(response)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return payload, hashlib.sha256(encoded).hexdigest()


def _question(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "choice",
        "instructions": "Choose the best routing hint for this task; do not authorize tools.",
        "criteria": {route: f"Routing candidate: {route}" for route in case["candidate_routes"]},
    }


def _error_status(error: BaseException) -> str:
    name = type(error).__name__.lower()
    return "timeout" if "timeout" in name else "fallback"


def _safe_error_message(error: BaseException) -> str:
    """Return a non-sensitive error category, never raw transport text."""

    return f"{type(error).__name__} raised during local System One evaluation"


def _fallback_row(
    case: dict[str, Any], config: dict[str, Any], started: float, error: BaseException
) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "source_type": case["source_type"],
        "split": case["split"],
        "status": _error_status(error),
        "route": "abstain",
        "escalate": True,
        "fallback_required": True,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "model": config["model"],
        "response_digest": None,
        "config": config,
        "error_type": type(error).__name__,
        "error_message": _safe_error_message(error),
    }


def run_cases(
    cases: dict[str, dict[str, Any]], client: Any, config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run already-loaded cases through an injected client, with fail-closed rows."""

    rows: list[dict[str, Any]] = []
    for case in cases.values():
        started = time.perf_counter()
        if client is None:
            rows.append(_fallback_row(case, config, started, RuntimeError("Ollama SDK unavailable")))
            continue
        try:
            response = client.systemone(
                model=config["model"],
                state=case["input"],
                questions={"choice": _question(case)},
                keep_alive=config["keep_alive"],
            )
            payload, digest = response_digest(response)
            row: dict[str, Any] = {
                "case_id": case["case_id"],
                "source_type": case["source_type"],
                "split": case["split"],
                "status": "ok",
                "fallback_required": False,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "model": config["model"],
                "response_digest": digest,
                "config": config,
                "response": payload,
            }
            try:
                normalized = normalize_prediction(row, case)
            except (TypeError, ValueError) as error:
                row.update(
                    {
                        "status": "fallback",
                        "route": "abstain",
                        "escalate": True,
                        "fallback_required": True,
                        "error_type": "InvalidTypedResponse",
                        "error_message": "typed response failed schema validation",
                    }
                )
            else:
                row.update(
                    {
                        "route": normalized["route"],
                        "escalate": normalized["escalate"],
                        "confidence": normalized["confidence"],
                    }
                )
            rows.append(row)
        except Exception as error:  # SDK transport and server errors are fallback paths.
            rows.append(_fallback_row(case, config, started, error))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--keep-alive", default="5m")
    args = parser.parse_args()
    host = validate_local_host(args.host)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    cases = validate_cases(_read_jsonl(args.cases))
    config = {
        "host": host,
        "model": args.model,
        "timeout_seconds": args.timeout,
        "keep_alive": args.keep_alive,
        "tools_enabled": False,
        "auto_pull": False,
    }
    try:
        import ollama

        client = ollama.Client(host=host, timeout=args.timeout)
    except Exception:
        client = None
    rows = run_cases(cases, client, config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"case_count": len(rows), "output": str(args.output), "config": config}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
