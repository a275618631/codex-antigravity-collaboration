"""Small standard-library control plane; transports and runtimes remain adapters.

This deliberately persists only the Parent Goal / task graph state needed for safe
restart.  It is not a queue, broker, dashboard, scheduler, or database service.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol


class TaskState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"
    READY = "READY"
    RUNNING = "RUNNING"
    DELEGATED = "DELEGATED"
    WAITING_FOR_AGENT = "WAITING_FOR_AGENT"
    INTEGRATING_RESULT = "INTEGRATING_RESULT"
    VALIDATING = "VALIDATING"
    BLOCKED = "BLOCKED"
    HUMAN_GATE = "HUMAN_GATE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL = {TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.CANCELLED.value}
RESULT_FIELDS = {
    "task_id", "status", "summary", "artifacts_changed", "tests_run", "evidence",
    "unresolved", "newly_discovered_work", "recommended_next", "risks", "acceptance_passed",
}


class ResultPacketError(ValueError):
    """Raised when an adapter gives the control plane an unsafe result packet."""


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class AgentAdapter(Protocol):
    """Thin adapter contract; agent-specific payloads must normalize to Result Packet."""

    def health(self) -> Mapping[str, Any]: ...
    def capabilities(self) -> Mapping[str, Any]: ...
    def submit(self, task_packet: Mapping[str, Any]) -> str: ...
    def status(self, task_id: str) -> Mapping[str, Any]: ...
    def cancel(self, task_id: str) -> Mapping[str, Any]: ...
    def collect_result(self, task_id: str) -> Mapping[str, Any]: ...


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ResultPacketError(f"{field} must be a list")
    return value


def normalize_result_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize canonical v3 packets and the current control-plane envelope."""
    if not isinstance(packet, Mapping):
        raise ResultPacketError("result packet must be an object")
    source = packet.get("result_packet", packet)
    if not isinstance(source, Mapping):
        raise ResultPacketError("result_packet must be an object")
    changes = source.get("artifacts_changed", source.get("changes", {}))
    if isinstance(changes, Mapping):
        changed = list(changes.get("modified_files", [])) + list(changes.get("created_files", []))
    else:
        changed = changes
    validations = source.get("validation_results", {})
    tests = source.get("tests_run", validations.get("tests_run", [])) if isinstance(validations, Mapping) else source.get("tests_run", [])
    passed = source.get("acceptance_passed", validations.get("passed") if isinstance(validations, Mapping) else None)
    normalized = {
        "task_id": source.get("task_id"),
        "status": source.get("status"),
        "summary": source.get("summary"),
        "artifacts_changed": changed,
        "tests_run": tests,
        "evidence": source.get("evidence"),
        "unresolved": source.get("unresolved", source.get("remaining_work", [])),
        "newly_discovered_work": source.get("newly_discovered_work", []),
        "recommended_next": source.get("recommended_next", source.get("recommendation", "")),
        "risks": source.get("risks", source.get("risks_and_limitations", [])),
        "acceptance_passed": passed,
    }
    missing = [field for field in RESULT_FIELDS if normalized.get(field) is None]
    if missing:
        raise ResultPacketError("missing result fields: " + ", ".join(sorted(missing)))
    if normalized["status"] not in {"SUCCESS", "PARTIAL", "FAILED", "BLOCKED"}:
        raise ResultPacketError("unsupported result status")
    if not isinstance(normalized["task_id"], str) or not normalized["task_id"]:
        raise ResultPacketError("task_id must be a non-empty string")
    if not isinstance(normalized["summary"], str) or not isinstance(normalized["recommended_next"], str):
        raise ResultPacketError("summary and recommended_next must be strings")
    for field in ("artifacts_changed", "tests_run", "evidence", "unresolved", "newly_discovered_work", "risks"):
        _list(normalized[field], field)
    if not isinstance(normalized["acceptance_passed"], bool):
        raise ResultPacketError("acceptance_passed must be boolean")
    return normalized


@dataclass
class ManualLeadRouter:
    """User-selected lead is always authoritative over automatic suggestions."""
    lead: str

    def select(self, _: Mapping[str, Any]) -> str:
        if self.lead not in {"codex", "antigravity", "recommend"}:
            raise ValueError("lead must be codex, antigravity, or recommend")
        return "codex" if self.lead == "recommend" else self.lead


class DeterministicRouter:
    def select(self, task: Mapping[str, Any]) -> str:
        return str(task.get("owner_agent", "codex"))


class CapabilityRouter:
    def select(self, task: Mapping[str, Any], registry: Mapping[str, Any]) -> str:
        required = set(task.get("required_roles", []))
        for name, entry in registry.get("agents", {}).items():
            if required.issubset(set(entry.get("roles", []))):
                return name
        return "codex"


class SystemOneRouter:
    """Reserved experimental provider; it must never be required for dispatch."""

    experimental = True

    def select(self, _: Mapping[str, Any]) -> str:
        raise RuntimeError("System One routing is not enabled without separately verified evidence")


class PassiveAdapter:
    """Contract-shaped adapter used until a runtime-specific transport is verified."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def health(self) -> Mapping[str, Any]:
        return {"agent": self.agent_id, "available": False, "reason": "adapter transport not configured"}

    def capabilities(self) -> Mapping[str, Any]:
        return {"agent": self.agent_id, "verified": False}

    def submit(self, task_packet: Mapping[str, Any]) -> str:
        raise RuntimeError(f"{self.agent_id} adapter transport is not configured")

    def status(self, task_id: str) -> Mapping[str, Any]:
        return {"task_id": task_id, "state": "UNKNOWN"}

    def cancel(self, task_id: str) -> Mapping[str, Any]:
        return {"task_id": task_id, "cancelled": False}

    def collect_result(self, task_id: str) -> Mapping[str, Any]:
        raise RuntimeError(f"{self.agent_id} has no collected result for {task_id}")


class CodexAdapter(PassiveAdapter):
    def __init__(self):
        super().__init__("codex")


class AntigravityAdapter(PassiveAdapter):
    def __init__(self):
        super().__init__("antigravity")


class ControlPlane:
    """Persistent task graph with policy-first dispatch and automatic result ingestion."""

    def __init__(self, state_file: Path | str, policy: Callable[[Mapping[str, Any]], PolicyDecision] | None = None):
        self.state_file = Path(state_file)
        self.policy = policy or (lambda _: PolicyDecision.ALLOW)
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {"schema_version": 1, "goals": {}, "deliveries": []}
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("goals"), dict):
            raise ValueError("unsupported or corrupt control-plane state")
        return data

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="control-plane-", suffix=".json", dir=self.state_file.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.state, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_name, self.state_file)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise

    def create_goal(self, goal_id: str, objective: str, lead_agent: str, acceptance_criteria: list[str]) -> dict[str, Any]:
        if goal_id in self.state["goals"]:
            raise ValueError(f"goal already exists: {goal_id}")
        lead = ManualLeadRouter(lead_agent).select({})
        goal = {"id": goal_id, "objective": objective, "lead_agent": lead, "acceptance_criteria": acceptance_criteria,
                "state": TaskState.PLANNING.value, "tasks": {}, "created_at": utcnow(), "updated_at": utcnow()}
        self.state["goals"][goal_id] = goal
        self._save()
        return copy.deepcopy(goal)

    def add_task(self, goal_id: str, task: Mapping[str, Any]) -> dict[str, Any]:
        goal = self._goal(goal_id)
        task_id = str(task.get("id", ""))
        if not task_id or task_id in goal["tasks"]:
            raise ValueError("task id must be unique and non-empty")
        dependencies = list(task.get("dependencies", []))
        if any(dependency not in goal["tasks"] for dependency in dependencies):
            raise ValueError("dependencies must reference existing tasks")
        record = {"id": task_id, "objective": str(task.get("objective", "")), "owner_agent": str(task.get("owner_agent", goal["lead_agent"])),
                  "dependencies": dependencies, "write_scope": list(task.get("write_scope", [])), "acceptance_criteria": list(task.get("acceptance_criteria", [])),
                  "human_gate_reason": task.get("human_gate_reason"), "state": TaskState.CREATED.value,
                  "state_history": [{"state": TaskState.CREATED.value, "at": utcnow()}], "result": None, "updated_at": utcnow()}
        if not record["objective"]:
            raise ValueError("task objective is required")
        goal["tasks"][task_id] = record
        goal["updated_at"] = utcnow()
        self._save()
        return copy.deepcopy(record)

    def request_plan_approval(self, goal_id: str) -> None:
        goal = self._goal(goal_id)
        if not goal["tasks"]:
            raise ValueError("a goal needs at least one task")
        goal["state"] = TaskState.AWAITING_PLAN_APPROVAL.value
        goal["updated_at"] = utcnow()
        self._save()

    def approve_plan(self, goal_id: str) -> None:
        goal = self._goal(goal_id)
        if goal["state"] != TaskState.AWAITING_PLAN_APPROVAL.value:
            raise ValueError("plan is not awaiting approval")
        goal["state"] = TaskState.READY.value
        self._refresh_readiness(goal)
        goal["updated_at"] = utcnow()
        self._save()

    def next_task(self, goal_id: str) -> dict[str, Any] | None:
        goal = self._goal(goal_id)
        if goal["state"] in {TaskState.HUMAN_GATE.value, TaskState.BLOCKED.value, TaskState.COMPLETED.value}:
            return None
        self._refresh_readiness(goal)
        ready = sorted((task for task in goal["tasks"].values() if task["state"] == TaskState.READY.value), key=lambda item: item["id"])
        if not ready:
            self._update_goal_terminal_state(goal)
            self._save()
            return None
        task = ready[0]
        decision = self.policy(task)
        if decision == PolicyDecision.DENY:
            task.update(state=TaskState.BLOCKED.value, policy_decision=decision.value, updated_at=utcnow())
            goal["state"] = TaskState.BLOCKED.value
            self._save()
            return None
        if decision == PolicyDecision.REQUIRE_APPROVAL or task.get("human_gate_reason"):
            task.update(state=TaskState.HUMAN_GATE.value, policy_decision=decision.value, updated_at=utcnow())
            goal["state"] = TaskState.HUMAN_GATE.value
            self._save()
            return None
        self._transition(task, TaskState.RUNNING.value)
        goal["state"] = TaskState.RUNNING.value
        goal["updated_at"] = utcnow()
        self._save()
        return copy.deepcopy(task)

    def mark_delegated(self, goal_id: str, task_id: str, external_id: str) -> None:
        task = self._task(goal_id, task_id)
        if task["state"] != TaskState.RUNNING.value:
            raise ValueError("only a running task can be delegated")
        self._transition(task, TaskState.DELEGATED.value)
        self._transition(task, TaskState.WAITING_FOR_AGENT.value)
        task.update(delegated_to=task["owner_agent"], external_id=external_id)
        self._goal(goal_id)["state"] = TaskState.WAITING_FOR_AGENT.value
        self._save()

    def ingest_result(self, goal_id: str, packet: Mapping[str, Any], delivery_id: str) -> dict[str, Any]:
        if delivery_id in self.state["deliveries"]:
            return {"duplicate": True, "goal": copy.deepcopy(self._goal(goal_id))}
        result = normalize_result_packet(packet)
        task = self._task(goal_id, result["task_id"])
        if task["state"] not in {TaskState.RUNNING.value, TaskState.WAITING_FOR_AGENT.value, TaskState.DELEGATED.value}:
            raise ValueError("result is not expected for this task state")
        self._validate_write_scope(task, result["artifacts_changed"])
        goal = self._goal(goal_id)
        self._transition(task, TaskState.INTEGRATING_RESULT.value)
        task["result"] = result
        self._transition(task, TaskState.VALIDATING.value)
        if result["status"] == "SUCCESS" and result["acceptance_passed"] and not result["unresolved"]:
            self._transition(task, TaskState.COMPLETED.value)
        elif result["status"] == "FAILED" or not result["acceptance_passed"]:
            self._transition(task, TaskState.FAILED.value)
        else:
            self._transition(task, TaskState.BLOCKED.value)
        for discovered in result["newly_discovered_work"]:
            if not isinstance(discovered, Mapping):
                raise ResultPacketError("newly_discovered_work entries must be task objects")
            self.add_task(goal_id, discovered)
        self.state["deliveries"].append(delivery_id)
        self._refresh_readiness(goal)
        self._update_goal_terminal_state(goal)
        goal["updated_at"] = utcnow()
        self._save()
        return {"duplicate": False, "goal": copy.deepcopy(goal), "task": copy.deepcopy(task)}

    def approve_human_gate(self, goal_id: str, task_id: str) -> None:
        task = self._task(goal_id, task_id)
        if task["state"] != TaskState.HUMAN_GATE.value:
            raise ValueError("task is not waiting at a human gate")
        task.update(state=TaskState.READY.value, human_gate_reason=None, updated_at=utcnow())
        goal = self._goal(goal_id)
        goal["state"] = TaskState.READY.value
        self._save()

    def recover_stale(self, stale_before: datetime) -> list[str]:
        recovered: list[str] = []
        for goal in self.state["goals"].values():
            for task in goal["tasks"].values():
                changed_at = datetime.fromisoformat(task["updated_at"])
                if task["state"] == TaskState.WAITING_FOR_AGENT.value and changed_at < stale_before:
                    task.update(state=TaskState.BLOCKED.value, stale_recovery=True, updated_at=utcnow())
                    recovered.append(task["id"])
                    goal["state"] = TaskState.BLOCKED.value
        if recovered:
            self._save()
        return recovered

    def snapshot(self, goal_id: str) -> dict[str, Any]:
        return copy.deepcopy(self._goal(goal_id))

    def _goal(self, goal_id: str) -> dict[str, Any]:
        try:
            return self.state["goals"][goal_id]
        except KeyError as error:
            raise ValueError(f"unknown goal: {goal_id}") from error

    def _task(self, goal_id: str, task_id: str) -> dict[str, Any]:
        goal = self._goal(goal_id)
        try:
            return goal["tasks"][task_id]
        except KeyError as error:
            raise ValueError(f"unknown task: {task_id}") from error

    @staticmethod
    def _transition(task: dict[str, Any], state: str) -> None:
        task["state"] = state
        task["updated_at"] = utcnow()
        task.setdefault("state_history", []).append({"state": state, "at": task["updated_at"]})

    @staticmethod
    def _validate_write_scope(task: Mapping[str, Any], changed: list[Any]) -> None:
        allowed = list(task.get("write_scope", []))
        for path in changed:
            if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts:
                raise ResultPacketError("changed path is not repository-relative")
            if allowed and not any(path == root or path.startswith(root.rstrip("/") + "/") for root in allowed):
                raise ResultPacketError(f"changed path outside approved write scope: {path}")

    @staticmethod
    def _refresh_readiness(goal: dict[str, Any]) -> None:
        for task in goal["tasks"].values():
            if task["state"] == TaskState.CREATED.value:
                dependency_states = [goal["tasks"][item]["state"] for item in task["dependencies"]]
                if any(state in {TaskState.FAILED.value, TaskState.BLOCKED.value, TaskState.CANCELLED.value} for state in dependency_states):
                    task["state"] = TaskState.BLOCKED.value
                elif all(state == TaskState.COMPLETED.value for state in dependency_states):
                    task["state"] = TaskState.READY.value

    @staticmethod
    def _update_goal_terminal_state(goal: dict[str, Any]) -> None:
        states = [task["state"] for task in goal["tasks"].values()]
        if any(state == TaskState.BLOCKED.value for state in states):
            goal["state"] = TaskState.BLOCKED.value
        elif any(state == TaskState.HUMAN_GATE.value for state in states):
            goal["state"] = TaskState.HUMAN_GATE.value
        elif any(state == TaskState.FAILED.value for state in states):
            goal["state"] = TaskState.FAILED.value
        elif states and all(state in TERMINAL for state in states):
            goal["state"] = TaskState.COMPLETED.value
