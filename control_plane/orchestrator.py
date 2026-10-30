"""Small standard-library control plane; transports and runtimes remain adapters.

This deliberately persists only the Parent Goal / task graph state needed for safe
restart.  It is not a queue, broker, dashboard, scheduler, or database service.
"""

from __future__ import annotations

import copy
import hashlib
import json
import ntpath
import os
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
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
    NEEDS_RECONCILIATION = "NEEDS_RECONCILIATION"


TERMINAL = {TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.CANCELLED.value}
RESULT_V1_FIELDS = {
    "task_id", "status", "summary", "artifacts_changed", "tests_run", "evidence",
    "unresolved", "newly_discovered_work", "recommended_next", "risks", "acceptance_passed",
}
RESULT_V2_FIELDS = {
    "schema_version", "goal_id", "task_id", "attempt_id", "delivery_id",
    "approved_plan_digest", "task_digest", "repo", "base_sha", "status", "summary",
    "artifacts_changed", "tests_run", "acceptance", "unresolved",
    "newly_discovered_work", "recommended_next", "risks",
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
    """Normalize v2 result packets and adapt legacy packets without inventing PASS."""
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
        "schema_version": source.get("schema_version", 1),
        "goal_id": source.get("goal_id"),
        "task_id": source.get("task_id"),
        "attempt_id": source.get("attempt_id"),
        "delivery_id": source.get("delivery_id"),
        "approved_plan_digest": source.get("approved_plan_digest"),
        "task_digest": source.get("task_digest"),
        "repo": source.get("repo"),
        "base_sha": source.get("base_sha"),
        "status": source.get("status"),
        "summary": source.get("summary"),
        "artifacts_changed": changed,
        "tests_run": tests,
        "evidence": source.get("evidence", []),
        "unresolved": source.get("unresolved", source.get("remaining_work", [])),
        "newly_discovered_work": source.get("newly_discovered_work", []),
        "recommended_next": source.get("recommended_next", source.get("recommendation", "")),
        "risks": source.get("risks", source.get("risks_and_limitations", [])),
        "acceptance": source.get("acceptance", []),
        "acceptance_passed": passed if passed is not None else False,
        "legacy_acceptance_unverified": version_is_legacy(source),
    }
    version = normalized["schema_version"]
    if version not in (1, 2):
        raise ResultPacketError("unsupported result schema_version")
    required = RESULT_V2_FIELDS if version == 2 else RESULT_V1_FIELDS
    missing = [field for field in required if normalized.get(field) is None]
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
    if version == 2:
        if set(source) != RESULT_V2_FIELDS:
            raise ResultPacketError("v2 result packet contains missing or unsupported fields")
        for field in ("goal_id", "attempt_id", "delivery_id", "approved_plan_digest", "task_digest", "repo", "base_sha"):
            if not isinstance(normalized[field], str) or not normalized[field]:
                raise ResultPacketError(f"{field} must be a non-empty string")
        if normalized["delivery_id"] != normalized["delivery_id"].strip():
            raise ResultPacketError("delivery_id must not contain surrounding whitespace")
        if not isinstance(normalized["acceptance"], list):
            raise ResultPacketError("acceptance must be an array")
        criterion_ids: set[str] = set()
        for item in normalized["acceptance"]:
            if not isinstance(item, Mapping) or not isinstance(item.get("criterion_id"), str) or item.get("status") not in {"PASS", "FAIL", "UNVERIFIED"}:
                raise ResultPacketError("acceptance entries require criterion_id and PASS/FAIL/UNVERIFIED status")
            if item["status"] == "PASS" and not item.get("evidence_ref"):
                raise ResultPacketError("PASS acceptance requires evidence_ref")
            if item["criterion_id"] in criterion_ids:
                raise ResultPacketError("acceptance criterion IDs must be unique")
            criterion_ids.add(item["criterion_id"])
        for item in normalized["tests_run"]:
            if not isinstance(item, Mapping) or not isinstance(item.get("name"), str) or item.get("status") not in {"PASS", "FAIL", "UNVERIFIED"} or not isinstance(item.get("evidence_ref"), str):
                raise ResultPacketError("v2 tests_run entries require name, status, and evidence_ref")
    return normalized


def version_is_legacy(source: Mapping[str, Any]) -> bool:
    # The v1 contract has no criterion-level evidence references. A legacy
    # boolean or summary validation flag cannot establish acceptance.
    return source.get("schema_version", 1) == 1


def _serialized_mutation(method):
    """Serialize state mutations across threads/processes and reload under lock."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._exclusive():
            self.state = self._load()
            before = copy.deepcopy(self.state)
            try:
                return method(self, *args, **kwargs)
            except Exception:
                self.state = before
                raise
    return wrapped


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

    def __init__(self, state_file: Path | str, policy: Callable[[Mapping[str, Any]], PolicyDecision] | None = None, *, repo_root: Path | str | None = None):
        self.state_file = Path(state_file)
        self.policy = policy
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else None
        self._thread_lock = threading.RLock()
        self.state = self._load()

    @contextmanager
    def _exclusive(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.state_file.with_suffix(self.state_file.suffix + ".lock")
        with self._thread_lock, lock_path.open("a+b") as lock_file:
            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                lock_file.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {"schema_version": 2, "revision": 0, "goals": {}, "deliveries": {}}
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        if data.get("schema_version") not in {1, 2} or not isinstance(data.get("goals"), dict):
            raise ValueError("unsupported or corrupt control-plane state")
        if isinstance(data.get("deliveries"), list):
            data["deliveries"] = {item: "legacy" for item in data["deliveries"]}
        data["schema_version"] = 2
        data.setdefault("revision", 0)
        data.setdefault("deliveries", {})
        return data

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["schema_version"] = 2
        self.state["revision"] = int(self.state.get("revision", 0)) + 1
        fd, temp_name = tempfile.mkstemp(prefix="control-plane-", suffix=".json", dir=self.state_file.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.state, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_name, self.state_file)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise

    @staticmethod
    def _validate_repo_path(path: Any) -> str:
        if not isinstance(path, str) or not path.strip() or path != path.strip():
            raise ResultPacketError("scope path must be a non-empty repository-relative string")
        normalized = path.replace("\\", "/")
        windows_path = PureWindowsPath(path)
        if (normalized.startswith("/") or path.startswith(("\\\\", "//")) or windows_path.is_absolute()
                or ntpath.splitdrive(path)[0] or any(part in {"..", ""} for part in normalized.split("/"))):
            raise ResultPacketError("scope path must be repository-relative and may not escape with '..'")
        if "." in normalized.split("/") or any(part in {".", ""} for part in PurePosixPath(normalized).parts):
            raise ResultPacketError("scope path is not normalized")
        return normalized

    def _path_resolves_inside_repo(self, relative: str) -> bool:
        if self.repo_root is None:
            return False
        root = self.repo_root.resolve()
        candidate = (root / Path(*PurePosixPath(relative).parts)).resolve()
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False

    @staticmethod
    def _plan_digest(goal: Mapping[str, Any]) -> str:
        payload = {
            "goal_id": goal["id"], "objective": goal["objective"], "repo": goal["repo"],
            "base_sha": goal["base_sha"], "write_set": goal.get("approved_write_set", []),
            "operation_type": goal.get("operation_type"),
            "acceptance_criteria": goal["acceptance_criteria"],
            "tasks": [{key: goal["tasks"][task_id][key] for key in ("id", "objective", "owner_agent", "dependencies", "write_scope", "acceptance_criteria", "operation_type", "required", "integration")}
                      for task_id in sorted(goal.get("approved_task_ids", goal["tasks"]))],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _task_digest(goal: Mapping[str, Any], task: Mapping[str, Any]) -> str:
        payload = {"approved_plan_digest": goal["approved_plan_digest"], "repo": goal["repo"],
                   "base_sha": goal["base_sha"], "task": {key: task[key] for key in (
                       "id", "objective", "owner_agent", "dependencies", "write_scope",
                       "acceptance_criteria", "operation_type", "required", "integration")}}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @_serialized_mutation
    def create_goal(self, goal_id: str, objective: str, lead_agent: str, acceptance_criteria: list[str], *, repo: str = "", base_sha: str = "", integration_required: bool = True) -> dict[str, Any]:
        if goal_id in self.state["goals"]:
            raise ValueError(f"goal already exists: {goal_id}")
        lead = ManualLeadRouter(lead_agent).select({})
        goal = {"id": goal_id, "objective": objective, "lead_agent": lead, "acceptance_criteria": acceptance_criteria,
                "repo": repo, "base_sha": base_sha, "integration_required": integration_required,
                "state": TaskState.PLANNING.value, "tasks": {}, "created_at": utcnow(), "updated_at": utcnow()}
        self.state["goals"][goal_id] = goal
        self._save()
        return copy.deepcopy(goal)

    @_serialized_mutation
    def add_task(self, goal_id: str, task: Mapping[str, Any]) -> dict[str, Any]:
        goal = self._goal(goal_id)
        task_id = str(task.get("id", ""))
        if not task_id or task_id in goal["tasks"]:
            raise ValueError("task id must be unique and non-empty")
        dependencies = list(task.get("dependencies", []))
        if any(dependency not in goal["tasks"] for dependency in dependencies):
            raise ValueError("dependencies must reference existing tasks")
        write_scope = [self._validate_repo_path(path) for path in task.get("write_scope", [])]
        operation_type = str(task.get("operation_type", "write" if write_scope else "read"))
        if operation_type not in {"read", "write"} or (operation_type == "read" and write_scope) or (operation_type == "write" and not write_scope):
            raise ValueError("operation_type must match whether write_scope is empty")
        for scope_path in write_scope:
            self._validate_repo_path(scope_path)
        record = {"id": task_id, "objective": str(task.get("objective", "")), "owner_agent": str(task.get("owner_agent", goal["lead_agent"])),
                  "dependencies": dependencies, "write_scope": write_scope, "acceptance_criteria": list(task.get("acceptance_criteria", [])),
                  "operation_type": operation_type, "required": bool(task.get("required", True)),
                  "integration": bool(task.get("integration", False)),
                  "human_gate_reason": task.get("human_gate_reason"), "state": TaskState.CREATED.value,
                  "state_history": [{"state": TaskState.CREATED.value, "at": utcnow()}], "result": None, "updated_at": utcnow()}
        if not record["objective"]:
            raise ValueError("task objective is required")
        if goal.get("plan_approved"):
            raise ValueError("approved task graphs can only expand through validated result ingestion")
        goal["tasks"][task_id] = record
        goal["updated_at"] = utcnow()
        self._save()
        return copy.deepcopy(record)

    @_serialized_mutation
    def request_plan_approval(self, goal_id: str) -> None:
        goal = self._goal(goal_id)
        if not goal["tasks"]:
            raise ValueError("a goal needs at least one task")
        goal["state"] = TaskState.AWAITING_PLAN_APPROVAL.value
        goal["updated_at"] = utcnow()
        self._save()

    @_serialized_mutation
    def approve_plan(self, goal_id: str, *, repo: str, base_sha: str, write_set: list[str], operation_type: str) -> str:
        goal = self._goal(goal_id)
        if goal["state"] != TaskState.AWAITING_PLAN_APPROVAL.value:
            raise ValueError("plan is not awaiting approval")
        if not repo or not base_sha or operation_type not in {"read", "write"}:
            raise ValueError("approval requires repo, base_sha, and operation_type")
        actual_scope = sorted({path for task in goal["tasks"].values() for path in task["write_scope"]})
        approved_scope = sorted({self._validate_repo_path(path) for path in write_set})
        if any(self._validate_repo_path(path) is None for path in approved_scope):
            raise ValueError("invalid write scope")
        if actual_scope != approved_scope or (not approved_scope and operation_type != "read") or (approved_scope and operation_type != "write"):
            raise ValueError("approval does not match task write-set or operation type")
        if goal.get("repo") and repo != goal["repo"]:
            raise ValueError("approval repository does not match goal")
        if goal.get("base_sha") and base_sha != goal["base_sha"]:
            raise ValueError("approval base SHA does not match goal")
        goal["repo"], goal["base_sha"] = repo, base_sha
        goal["approved_write_set"] = approved_scope
        goal["operation_type"] = operation_type
        goal["approved_task_ids"] = sorted(goal["tasks"])
        goal["approved_plan_digest"] = self._plan_digest(goal)
        goal["plan_approved"] = True
        for task in goal["tasks"].values():
            task["task_digest"] = self._task_digest(goal, task)
        goal["state"] = TaskState.READY.value
        self._refresh_readiness(goal)
        goal["updated_at"] = utcnow()
        self._save()
        return goal["approved_plan_digest"]

    @_serialized_mutation
    def next_task(self, goal_id: str) -> dict[str, Any] | None:
        goal = self._goal(goal_id)
        if goal["state"] in {TaskState.HUMAN_GATE.value, TaskState.BLOCKED.value, TaskState.COMPLETED.value, TaskState.FAILED.value}:
            return None
        if any(task["state"] == TaskState.NEEDS_RECONCILIATION.value for task in goal["tasks"].values()):
            goal["state"] = TaskState.NEEDS_RECONCILIATION.value
            self._save()
            return None
        if not goal.get("plan_approved") or not goal.get("approved_plan_digest") or self._plan_digest(goal) != goal["approved_plan_digest"]:
            goal["state"] = TaskState.HUMAN_GATE.value
            goal["gate_reason"] = "approved plan digest missing or changed"
            self._save()
            return None
        self._refresh_readiness(goal)
        ready = sorted((task for task in goal["tasks"].values() if task["state"] == TaskState.READY.value), key=lambda item: item["id"])
        if not ready:
            self._update_goal_terminal_state(goal)
            self._save()
            return None
        task = ready[0]
        operation_type = task["operation_type"]
        if not goal.get("repo") or not goal.get("base_sha") or (operation_type == "write" and any(not self._path_resolves_inside_repo(path) for path in task["write_scope"])):
            task.update(state=TaskState.BLOCKED.value, policy_decision=PolicyDecision.DENY.value, updated_at=utcnow())
            goal.update(state=TaskState.BLOCKED.value, gate_reason="missing repo/base or unverified repository path")
            self._save()
            return None
        if operation_type == "write" and self.policy is None:
            decision = PolicyDecision.DENY
        else:
            try:
                decision = self.policy(task) if self.policy else PolicyDecision.ALLOW
            except Exception:
                decision = PolicyDecision.DENY
        if not isinstance(decision, PolicyDecision):
            decision = PolicyDecision.DENY
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
        task["attempt_id"] = str(uuid.uuid4())
        self._transition(task, TaskState.RUNNING.value)
        goal["state"] = TaskState.RUNNING.value
        goal["updated_at"] = utcnow()
        self._save()
        dispatch_packet = copy.deepcopy(task)
        dispatch_packet.update(repo=goal["repo"], base_sha=goal["base_sha"],
                               approved_plan_digest=goal["approved_plan_digest"],
                               approved_write_set=copy.deepcopy(goal["approved_write_set"]))
        return dispatch_packet

    @_serialized_mutation
    def mark_delegated(self, goal_id: str, task_id: str, external_id: str | None) -> None:
        task = self._task(goal_id, task_id)
        if task["state"] != TaskState.RUNNING.value:
            raise ValueError("only a running task can be delegated")
        self._transition(task, TaskState.DELEGATED.value)
        task.update(delegated_to=task["owner_agent"], external_id=external_id,
                    submission_pending=external_id is None)
        if external_id is not None:
            self._transition(task, TaskState.WAITING_FOR_AGENT.value)
        self._goal(goal_id)["state"] = task["state"]
        self._save()

    @_serialized_mutation
    def ingest_result(self, goal_id: str, packet: Mapping[str, Any], delivery_id: str, *, trusted_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        result = normalize_result_packet(packet)
        packet_digest = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        goal = self._goal(goal_id)
        task = self._task(goal_id, result["task_id"])
        if result["schema_version"] == 2:
            expected = {"goal_id": goal_id, "repo": goal["repo"], "base_sha": goal["base_sha"], "approved_plan_digest": goal["approved_plan_digest"]}
            if any(result[field] != value for field, value in expected.items()):
                raise ResultPacketError("result packet does not match approved goal identity")
            if result["delivery_id"] != delivery_id:
                raise ResultPacketError("delivery_id does not match transport envelope")
            if not task.get("attempt_id") or result["attempt_id"] != task["attempt_id"]:
                raise ResultPacketError("attempt_id does not match the active task attempt")
            if result["task_digest"] != task["task_digest"]:
                raise ResultPacketError("task_digest does not match the approved task")
            if not isinstance(trusted_context, Mapping):
                raise ResultPacketError("v2 result requires trusted transport identity")
            trusted_fields = ("goal_id", "task_id", "attempt_id", "delivery_id", "approved_plan_digest", "task_digest", "repo", "base_sha")
            if any(trusted_context.get(field) != result[field] for field in trusted_fields):
                raise ResultPacketError("result packet identity does not match trusted transport")
        prior_digest = self.state["deliveries"].get(delivery_id)
        if prior_digest is not None:
            if prior_digest not in {"legacy", packet_digest}:
                raise ResultPacketError("delivery_id was reused with a different packet digest")
            return {"duplicate": True, "goal": copy.deepcopy(goal)}
        if task["state"] not in {TaskState.RUNNING.value, TaskState.WAITING_FOR_AGENT.value, TaskState.DELEGATED.value}:
            raise ValueError("result is not expected for this task state")
        self._validate_write_scope(task, result["artifacts_changed"])
        allowed_criteria = set(goal.get("acceptance_criteria", [])) | set(task.get("acceptance_criteria", []))
        if any(item["criterion_id"] not in allowed_criteria for item in result["acceptance"]):
            raise ResultPacketError("result contains an unknown acceptance criterion")
        for evidence in result["acceptance"]:
            if evidence["status"] == "PASS":
                goal.setdefault("acceptance_results", {})[evidence["criterion_id"]] = {
                    "status": "PASS", "evidence_ref": evidence["evidence_ref"], "task_id": task["id"]}
        self._transition(task, TaskState.INTEGRATING_RESULT.value)
        task["result"] = result
        self._transition(task, TaskState.VALIDATING.value)
        required_criteria = set(task.get("acceptance_criteria", []))
        acceptance_by_id = {item["criterion_id"]: item["status"] for item in result["acceptance"]}
        criteria_passed = (all(acceptance_by_id.get(item) == "PASS" for item in required_criteria)
                           if required_criteria else bool(result["tests_run"]) and all(
                               isinstance(test, Mapping) and test.get("status") == "PASS" and test.get("evidence_ref")
                               for test in result["tests_run"]))
        legacy_passed = result["schema_version"] == 1 and result["acceptance_passed"] and not result["legacy_acceptance_unverified"]
        if result["status"] == "FAILED" or any(item["status"] == "FAIL" for item in result["acceptance"]):
            self._transition(task, TaskState.FAILED.value)
        elif result["status"] == "SUCCESS" and (criteria_passed or legacy_passed) and not result["unresolved"]:
            self._transition(task, TaskState.COMPLETED.value)
        else:
            self._transition(task, TaskState.BLOCKED.value)
        discovered_records = self._validate_discovered_work(goal, task, result["newly_discovered_work"])
        for record in discovered_records:
            goal["tasks"][record["id"]] = record
        self.state["deliveries"][delivery_id] = packet_digest
        self._refresh_readiness(goal)
        self._update_goal_terminal_state(goal)
        goal["updated_at"] = utcnow()
        self._save()
        return {"duplicate": False, "goal": copy.deepcopy(goal), "task": copy.deepcopy(task)}

    @_serialized_mutation
    def approve_human_gate(self, goal_id: str, task_id: str) -> None:
        task = self._task(goal_id, task_id)
        if task["state"] != TaskState.HUMAN_GATE.value:
            raise ValueError("task is not waiting at a human gate")
        task.update(state=TaskState.READY.value, human_gate_reason=None, updated_at=utcnow())
        goal = self._goal(goal_id)
        goal["state"] = TaskState.READY.value
        self._save()

    @_serialized_mutation
    def cancel_task(self, goal_id: str, task_id: str) -> None:
        task = self._task(goal_id, task_id)
        if task["state"] in TERMINAL:
            raise ValueError("terminal task cannot be cancelled")
        self._transition(task, TaskState.CANCELLED.value)
        goal = self._goal(goal_id)
        self._refresh_readiness(goal)
        self._update_goal_terminal_state(goal)
        goal["updated_at"] = utcnow()
        self._save()

    @_serialized_mutation
    def recover_stale(self, stale_before: datetime) -> list[str]:
        recovered: list[str] = []
        for goal in self.state["goals"].values():
            for task in goal["tasks"].values():
                changed_at = datetime.fromisoformat(task["updated_at"])
                if task["state"] in {TaskState.RUNNING.value, TaskState.DELEGATED.value, TaskState.WAITING_FOR_AGENT.value,
                                      TaskState.INTEGRATING_RESULT.value, TaskState.VALIDATING.value} and changed_at < stale_before:
                    task.update(state=TaskState.NEEDS_RECONCILIATION.value, stale_recovery=True, updated_at=utcnow())
                    recovered.append(task["id"])
                    goal["state"] = TaskState.NEEDS_RECONCILIATION.value
        if recovered:
            self._save()
        return recovered

    @_serialized_mutation
    def reconcile_runtime(self, adapters: Mapping[str, AgentAdapter]) -> list[str]:
        """Inspect in-flight work without retrying unknown side effects."""
        changed: list[str] = []
        active = {TaskState.RUNNING.value, TaskState.DELEGATED.value, TaskState.WAITING_FOR_AGENT.value,
                  TaskState.INTEGRATING_RESULT.value, TaskState.VALIDATING.value}
        for goal in self.state["goals"].values():
            for task in goal["tasks"].values():
                if task["state"] not in active:
                    continue
                adapter = adapters.get(task.get("delegated_to") or task["owner_agent"])
                status: Mapping[str, Any] = {}
                if adapter is not None and task.get("external_id"):
                    try:
                        status = adapter.status(task["external_id"])
                    except Exception:
                        status = {"state": "UNKNOWN"}
                runtime_state = str(status.get("state", "UNKNOWN")).upper()
                if task["state"] == TaskState.WAITING_FOR_AGENT.value and runtime_state in {"RUNNING", "QUEUED", "WAITING"}:
                    continue
                task.update(state=TaskState.NEEDS_RECONCILIATION.value,
                            reconciliation_reason="external side effect or collected result cannot be confirmed",
                            observed_runtime_state=runtime_state, updated_at=utcnow())
                task.setdefault("state_history", []).append({"state": TaskState.NEEDS_RECONCILIATION.value, "at": task["updated_at"]})
                goal["state"] = TaskState.NEEDS_RECONCILIATION.value
                goal["updated_at"] = task["updated_at"]
                changed.append(task["id"])
        if changed:
            self._save()
        return changed

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

    def _validate_write_scope(self, task: Mapping[str, Any], changed: list[Any]) -> None:
        allowed = [self._validate_repo_path(item) for item in task.get("write_scope", [])]
        for path in changed:
            normalized = self._validate_repo_path(path)
            if not allowed or not any(normalized == root or normalized.startswith(root.rstrip("/") + "/") for root in allowed):
                raise ResultPacketError(f"changed path outside approved write scope: {path}")
            if not self._path_resolves_inside_repo(normalized):
                raise ResultPacketError(f"changed path resolves outside the repository: {path}")

    def _validate_discovered_work(self, goal: Mapping[str, Any], parent: Mapping[str, Any], items: list[Any]) -> list[dict[str, Any]]:
        if not isinstance(items, list):
            raise ResultPacketError("newly_discovered_work must be an array")
        pending: dict[str, dict[str, Any]] = {}
        existing_ids = set(goal["tasks"])
        approved_scope = set(goal.get("approved_write_set", []))
        parent_scope = set(parent.get("write_scope", []))
        for item in items:
            if not isinstance(item, Mapping):
                raise ResultPacketError("newly_discovered_work entries must be task objects")
            task_id = item.get("id")
            objective = item.get("objective")
            if not isinstance(task_id, str) or not task_id or task_id in existing_ids or task_id in pending:
                raise ResultPacketError("newly discovered task IDs must be unique and non-empty")
            if not isinstance(objective, str) or not objective.strip():
                raise ResultPacketError("newly discovered task objective is required")
            scope = [self._validate_repo_path(path) for path in item.get("write_scope", [])]
            if any(not any(candidate == root or candidate.startswith(root.rstrip("/") + "/") for root in allowed)
                   for candidate in scope for allowed in (approved_scope, parent_scope)):
                raise ResultPacketError("newly discovered work exceeds its parent approved scope")
            operation = item.get("operation_type", "write" if scope else "read")
            if operation not in {"read", "write"} or (operation == "write") != bool(scope):
                raise ResultPacketError("newly discovered operation_type does not match write_scope")
            dependencies = item.get("dependencies", [])
            if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
                raise ResultPacketError("newly discovered dependencies must be task ID arrays")
            pending[task_id] = {"id": task_id, "objective": objective.strip(),
                "owner_agent": str(item.get("owner_agent", parent["owner_agent"])),
                "dependencies": dependencies, "write_scope": scope,
                "acceptance_criteria": list(item.get("acceptance_criteria", [])),
                "operation_type": operation, "required": bool(item.get("required", True)),
                "integration": bool(item.get("integration", False)),
                "human_gate_reason": item.get("human_gate_reason"), "state": TaskState.CREATED.value,
                "state_history": [{"state": TaskState.CREATED.value, "at": utcnow()}],
                "result": None, "updated_at": utcnow(), "discovered_under": parent["id"]}
            pending[task_id]["task_digest"] = self._task_digest(goal, pending[task_id])
        known = existing_ids | set(pending)
        for task_id, item in pending.items():
            if task_id in item["dependencies"] or any(dep not in known for dep in item["dependencies"]):
                raise ResultPacketError("newly discovered dependencies must be valid and non-cyclic")
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ResultPacketError("newly discovered dependency cycle")
            if task_id in visited or task_id not in pending:
                return
            visiting.add(task_id)
            for dependency in pending[task_id]["dependencies"]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)
        for task_id in pending:
            visit(task_id)
        return list(pending.values())

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
        if any(state == TaskState.NEEDS_RECONCILIATION.value for state in states):
            goal["state"] = TaskState.NEEDS_RECONCILIATION.value
        elif any(state == TaskState.FAILED.value for state in states):
            goal["state"] = TaskState.FAILED.value
        elif any(state == TaskState.BLOCKED.value for state in states):
            goal["state"] = TaskState.BLOCKED.value
        elif any(state == TaskState.HUMAN_GATE.value for state in states):
            goal["state"] = TaskState.HUMAN_GATE.value
        elif any(state == TaskState.FAILED.value for state in states) or (states and all(state == TaskState.CANCELLED.value for state in states)):
            goal["state"] = TaskState.FAILED.value
        else:
            required = [task for task in goal["tasks"].values() if task.get("required", True)]
            if not required or not all(task["state"] == TaskState.COMPLETED.value for task in required):
                return
            integration_ok = not goal.get("integration_required", True) or any(
                task.get("integration") or task["id"].lower() == "integration"
                for task in required if task["state"] == TaskState.COMPLETED.value)
            parent_criteria = goal.get("acceptance_criteria", [])
            acceptance = goal.get("acceptance_results", {})
            criteria_ok = bool(parent_criteria) and all(
                acceptance.get(criterion, {}).get("status") == "PASS" and acceptance.get(criterion, {}).get("evidence_ref")
                for criterion in parent_criteria)
            no_unresolved = all(not task.get("result", {}).get("unresolved") for task in required)
            if integration_ok and criteria_ok and no_unresolved:
                goal["state"] = TaskState.COMPLETED.value
