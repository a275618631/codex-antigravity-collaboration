import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from control_plane.orchestrator import ControlPlane, PolicyDecision, ResultPacketError, TaskState
from github_handoff.core import SafetyError, validate_result_packet_data


class Runtime:
    def __init__(self, state, cancelled=True):
        self.state = state
        self.cancelled = cancelled

    def status(self, _external_id):
        return {"state": self.state}

    def cancel(self, _external_id):
        return {"cancelled": self.cancelled}


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.path = Path(self.temp.name) / "state.json"
        self.plane = ControlPlane(self.path, lambda _: PolicyDecision.ALLOW, repo_root=self.root,
                                  evidence_verifier=lambda evidence: evidence.get("evidence_ref") in {"test-log-1", "acceptance-log-1"},
                                  approval_verifier=lambda _: True, artifact_verifier=lambda _: True)
        self.plane.create_goal("goal", "prove safe continuation", "codex", ["all tasks pass"],
                               repo="example/repo", base_sha="abc123")
        self.plane.add_task("goal", {"id": "a", "objective": "lead work", "write_scope": ["src"]})
        self.plane.add_task("goal", {"id": "b", "objective": "worker work", "owner_agent": "antigravity",
                                     "dependencies": ["a"], "write_scope": ["src"]})
        self.plane.add_task("goal", {"id": "integration", "objective": "integrate and validate",
                                     "dependencies": ["b"], "write_scope": ["src"], "integration": True})
        self.approve()

    def tearDown(self):
        self.temp.cleanup()

    def approve(self, plane=None, goal_id="goal"):
        plane = plane or self.plane
        plane.request_plan_approval(goal_id)
        return plane.approve_plan(goal_id, repo="example/repo", base_sha="abc123",
                                  write_set=["src"], operation_type="write")

    def result(self, goal_id, task_id, dispatch=None, *, changed=None, discovered=None,
               status="SUCCESS", acceptance_status="PASS", delivery_id=None):
        dispatch = dispatch or self.plane.snapshot(goal_id)["tasks"][task_id]
        goal = self.plane.snapshot(goal_id)
        delivery_id = delivery_id or f"delivery-{task_id}"
        packet = {
            "schema_version": 2,
            "goal_id": goal_id,
            "task_id": task_id,
            "attempt_id": dispatch["attempt_id"],
            "delivery_id": delivery_id,
            "approved_plan_digest": goal["approved_plan_digest"],
            "task_digest": dispatch["task_digest"],
            "repo": goal["repo"],
            "base_sha": goal["base_sha"],
            "status": status,
            "summary": "work completed",
            "artifacts_changed": changed if changed is not None else ["src/output.txt"],
            "tests_run": [{"name": "unit", "status": "PASS", "evidence_ref": "test-log-1"}],
            "acceptance": ([{"criterion_id": "all tasks pass", "status": acceptance_status,
                             "evidence_ref": "acceptance-log-1"}] if dispatch.get("integration") or task_id.lower() == "integration" or acceptance_status != "PASS" else []),
            "unresolved": [],
            "newly_discovered_work": discovered or [],
            "recommended_next": "continue",
            "risks": [],
        }
        trusted = {key: packet[key] for key in (
            "goal_id", "task_id", "attempt_id", "delivery_id", "approved_plan_digest",
            "task_digest", "repo", "base_sha")}
        return packet, trusted, delivery_id

    def ingest_success(self, task_id, dispatch=None, **kwargs):
        packet, trusted, delivery_id = self.result("goal", task_id, dispatch, **kwargs)
        return self.plane.ingest_result("goal", packet, delivery_id, trusted_context=trusted)

    def test_approved_digest_binds_repo_base_and_exact_write_set(self):
        digest = self.plane.snapshot("goal")["approved_plan_digest"]
        self.assertEqual(len(digest), 64)
        self.assertEqual(self.plane.snapshot("goal")["approved_write_set"], ["src"])
        plane = ControlPlane(Path(self.temp.name) / "mismatch.json")
        plane.create_goal("mismatch", "x", "codex", ["x"], repo="example/repo", base_sha="abc123")
        plane.add_task("mismatch", {"id": "task", "objective": "x", "write_scope": ["src"]})
        plane.request_plan_approval("mismatch")
        with self.assertRaisesRegex(ValueError, "repository"):
            plane.approve_plan("mismatch", repo="other/repo", base_sha="abc123",
                               write_set=["src"], operation_type="write")

    def test_read_only_operation_requires_empty_write_set(self):
        plane = ControlPlane(Path(self.temp.name) / "read.json")
        plane.create_goal("read", "inspect", "codex", ["inspect"], repo="example/repo", base_sha="abc123",
                          integration_required=False)
        plane.add_task("read", {"id": "inspect", "objective": "inspect", "operation_type": "read"})
        plane.request_plan_approval("read")
        self.assertEqual(len(plane.approve_plan("read", repo="example/repo", base_sha="abc123",
                                                 write_set=[], operation_type="read")), 64)
        self.assertEqual(plane.next_task("read")["id"], "inspect")

    def test_github_receiver_and_control_plane_have_separate_result_schemas(self):
        repo = Path(__file__).parents[1]
        receiver_schema = json.loads((repo / "github_handoff" / "result.schema.json").read_text(encoding="utf-8"))
        control_schema = json.loads((repo / "control_plane" / "result.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(receiver_schema["required"], ["result_packet"])
        self.assertEqual(len(control_schema["oneOf"]), 3)
        with self.assertRaisesRegex(SafetyError, "strict schema"):
            validate_result_packet_data({"schema_version": 2}, "task")

    def test_unsafe_paths_are_rejected(self):
        for path in ("../secret", "C:/secret", "\\\\server\\share", "src/../secret"):
            with self.subTest(path=path):
                plane = ControlPlane(Path(self.temp.name) / (str(abs(hash(path))) + ".json"), repo_root=self.root)
                plane.create_goal("g", "x", "codex", ["x"], repo="r", base_sha="sha")
                with self.assertRaises(ValueError):
                    plane.add_task("g", {"id": "t", "objective": "x", "write_scope": [path]})

    def test_missing_write_policy_fails_closed(self):
        plane = ControlPlane(Path(self.temp.name) / "no-policy.json", repo_root=self.root)
        plane.create_goal("g", "x", "codex", ["x"], repo="r", base_sha="sha")
        plane.add_task("g", {"id": "t", "objective": "x", "write_scope": ["src"]})
        plane.request_plan_approval("g")
        plane.approve_plan("g", repo="r", base_sha="sha", write_set=["src"], operation_type="write")
        self.assertIsNone(plane.next_task("g"))
        self.assertEqual(plane.snapshot("g")["tasks"]["t"]["policy_decision"], "DENY")

    def test_policy_receives_approved_repo_and_plan_context(self):
        observed = {}
        def policy(context):
            observed.update(context)
            return PolicyDecision.ALLOW
        plane = ControlPlane(Path(self.temp.name) / "policy-context.json", policy)
        plane.create_goal("g", "inspect", "codex", ["done"], repo="owner/repo", base_sha="abc123",
                          integration_required=False)
        plane.add_task("g", {"id": "read", "objective": "read", "operation_type": "read"})
        plane.request_plan_approval("g")
        digest = plane.approve_plan("g", repo="owner/repo", base_sha="abc123", write_set=[], operation_type="read")
        plane.next_task("g")
        self.assertEqual(observed["repo"], "owner/repo")
        self.assertEqual(observed["base_sha"], "abc123")
        self.assertEqual(observed["approved_plan_digest"], digest)
        self.assertEqual(observed["execution_actor"], "codex")

    def test_policy_denial_precedes_routing(self):
        plane = ControlPlane(Path(self.temp.name) / "deny.json", lambda _: PolicyDecision.DENY, repo_root=self.root)
        plane.create_goal("deny", "x", "codex", ["x"], repo="r", base_sha="sha")
        plane.add_task("deny", {"id": "task", "objective": "x", "write_scope": ["src"]})
        plane.request_plan_approval("deny")
        plane.approve_plan("deny", repo="r", base_sha="sha", write_set=["src"], operation_type="write")
        self.assertIsNone(plane.next_task("deny"))
        self.assertEqual(plane.snapshot("deny")["state"], TaskState.BLOCKED.value)

    def test_v2_identity_and_trusted_transport_are_required(self):
        dispatch = self.plane.next_task("goal")
        packet, trusted, delivery = self.result("goal", "a", dispatch)
        with self.assertRaisesRegex(ResultPacketError, "trusted transport"):
            self.plane.ingest_result("goal", packet, delivery)
        tampered = copy.deepcopy(trusted)
        tampered["task_id"] = "b"
        with self.assertRaisesRegex(ResultPacketError, "trusted transport"):
            self.plane.ingest_result("goal", packet, delivery, trusted_context=tampered)

    def test_result_v2_completes_tasks_and_parent_only_with_evidence(self):
        for task_id in ("a", "b", "integration"):
            dispatch = self.plane.next_task("goal")
            self.assertEqual(dispatch["id"], task_id)
            self.ingest_success(task_id, dispatch)
        goal = self.plane.snapshot("goal")
        self.assertEqual(goal["state"], TaskState.COMPLETED.value)
        self.assertEqual(goal["acceptance_results"]["all tasks pass"]["status"], "VERIFIED_PASS")
        self.assertTrue(goal["tasks"]["integration"]["evidence_verification"]["acceptance"][0]["verified"])

    def test_duplicate_delivery_id_same_digest_is_noop_but_changed_digest_rejected(self):
        dispatch = self.plane.next_task("goal")
        packet, trusted, delivery = self.result("goal", "a", dispatch)
        first = self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        second = self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        with self.assertRaisesRegex(ResultPacketError, "trusted transport"):
            self.plane.ingest_result("goal", packet, delivery)
        changed = copy.deepcopy(packet)
        changed["summary"] = "different content"
        with self.assertRaisesRegex(ResultPacketError, "reused"):
            self.plane.ingest_result("goal", changed, delivery, trusted_context=trusted)

    def test_legacy_adapter_does_not_invent_acceptance_pass(self):
        dispatch = self.plane.next_task("goal")
        legacy = {"task_id": "a", "status": "SUCCESS", "summary": "done",
                  "artifacts_changed": ["src/out"], "tests_run": ["unit"], "evidence": [],
                  "unresolved": [], "newly_discovered_work": [], "recommended_next": "continue",
                  "risks": [], "acceptance_passed": True}
        self.plane.ingest_result("goal", legacy, "legacy-delivery")
        task = self.plane.snapshot("goal")["tasks"]["a"]
        self.assertTrue(task["result"]["legacy_acceptance_unverified"])
        self.assertEqual(task["state"], TaskState.BLOCKED.value)

    def test_v1_self_reported_tests_never_complete_task(self):
        self.plane.next_task("goal")
        legacy = {"task_id": "a", "status": "SUCCESS", "summary": "done",
                  "artifacts_changed": ["src/out"], "tests_run": [{"name": "unit", "status": "PASS", "evidence_ref": "test-log-1"}],
                  "evidence": [], "unresolved": [], "newly_discovered_work": [],
                  "recommended_next": "continue", "risks": [], "acceptance_passed": True}
        self.plane.ingest_result("goal", legacy, "legacy-tests")
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.BLOCKED.value)

    def test_failed_acceptance_cannot_complete(self):
        dispatch = self.plane.next_task("goal")
        self.ingest_success("a", dispatch, acceptance_status="FAIL")
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.FAILED.value)
        self.assertEqual(self.plane.snapshot("goal")["state"], TaskState.FAILED.value)

    def test_write_scope_and_symlink_escape_are_rejected(self):
        self.plane.next_task("goal")
        packet, trusted, delivery = self.result("goal", "a", changed=["secrets/token.txt"])
        with self.assertRaisesRegex(ResultPacketError, "write scope"):
            self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        packet, trusted, delivery = self.result("goal", "a", changed=["src/file.txt"], delivery_id="symlink")
        with patch.object(self.plane, "_path_resolves_inside_repo", return_value=False):
            with self.assertRaisesRegex(ResultPacketError, "outside the repository"):
                self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)

    def test_new_work_batch_is_atomic_and_scoped(self):
        dispatch = self.plane.next_task("goal")
        bad_batch = [
            {"id": "new1", "objective": "allowed", "dependencies": [], "write_scope": ["src"]},
            {"id": "new2", "objective": "escape", "dependencies": [], "write_scope": ["secrets"]},
        ]
        packet, trusted, delivery = self.result("goal", "a", dispatch, discovered=bad_batch)
        with self.assertRaisesRegex(ResultPacketError, "exceeds"):
            self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        self.assertNotIn("new1", self.plane.snapshot("goal")["tasks"])
        valid = [{"id": "new1", "objective": "allowed", "dependencies": [], "write_scope": ["src"]},
                 {"id": "new2", "objective": "depends", "dependencies": ["new1"], "write_scope": ["src"]}]
        packet, trusted, delivery = self.result("goal", "a", dispatch, discovered=valid, delivery_id="valid-batch")
        self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        snapshot = self.plane.snapshot("goal")
        self.assertIn("new1", snapshot["tasks"])
        self.assertIn("new2", snapshot["tasks"])
        self.assertEqual(snapshot["tasks"]["new1"]["state"], TaskState.PENDING_REVIEW.value)
        self.assertIsNone(self.plane.next_task("goal"))

    def test_legacy_delivery_without_digest_requires_reconciliation(self):
        self.plane.state["deliveries"]["historical"] = None
        self.plane._save()
        dispatch = self.plane.next_task("goal")
        packet, trusted, _ = self.result("goal", "a", dispatch, delivery_id="historical")
        with self.assertRaisesRegex(ResultPacketError, "digest is unavailable"):
            self.plane.ingest_result("goal", packet, "historical", trusted_context=trusted)

    def test_snapshot_refreshes_from_shared_state_file(self):
        stale = ControlPlane(self.path, lambda _: PolicyDecision.ALLOW, repo_root=self.root,
                             evidence_verifier=lambda _: True)
        self.plane.next_task("goal")
        self.assertEqual(stale.snapshot("goal")["tasks"]["a"]["state"], TaskState.RUNNING.value)

    def test_discovered_work_requires_human_approval_and_new_plan_revision(self):
        dispatch = self.plane.next_task("goal")
        discovered = [{"id": "new-task", "objective": "reviewed work", "dependencies": [], "write_scope": ["src"]}]
        self.ingest_success("a", dispatch, discovered=discovered)
        goal_before = self.plane.snapshot("goal")
        self.assertEqual(goal_before["state"], TaskState.PENDING_REVIEW.value)
        old_digest = goal_before["approved_plan_digest"]
        self.assertIsNone(self.plane.next_task("goal"))
        new_digest = self.plane.approve_discovered_task("goal", "new-task", approver="codex-lead")
        goal_after = self.plane.snapshot("goal")
        self.assertNotEqual(new_digest, old_digest)
        self.assertEqual(goal_after["plan_revision"], 2)
        self.assertEqual(goal_after["tasks"]["new-task"]["approved_by"], "codex-lead")
        self.assertEqual(goal_after["tasks"]["a"]["state"], TaskState.READY.value)
        self.assertIsNone(goal_after.get("acceptance_results", {}).get("all tasks pass"))

    def test_discovered_work_approval_fails_closed_without_trusted_approver(self):
        dispatch = self.plane.next_task("goal")
        self.ingest_success("a", dispatch, discovered=[{"id": "awaiting", "objective": "needs approval",
                                                          "dependencies": [], "write_scope": ["src"]}])
        self.plane.approval_verifier = None
        with self.assertRaisesRegex(ValueError, "trusted approval verifier"):
            self.plane.approve_discovered_task("goal", "awaiting", approver="claimed-lead")
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["awaiting"]["state"], TaskState.PENDING_REVIEW.value)

    def test_recovery_never_blindly_resubmits_unknown_side_effect(self):
        dispatch = self.plane.next_task("goal")
        self.plane.mark_delegated("goal", "a", None)
        recovered = self.plane.recover_stale(datetime.now(timezone.utc) + timedelta(seconds=1))
        self.assertEqual(recovered, ["a"])
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.NEEDS_RECONCILIATION.value)
        self.assertIsNone(self.plane.next_task("goal"))

    def test_reconcile_unknown_submission_but_preserve_confirmed_running_task(self):
        self.plane.next_task("goal")
        self.plane.mark_delegated("goal", "a", "external-1")
        self.assertEqual(self.plane.reconcile_runtime({"codex": Runtime("RUNNING")}), [])
        self.assertEqual(self.plane.reconcile_runtime({"codex": Runtime("UNKNOWN")}), ["a"])
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.NEEDS_RECONCILIATION.value)

    def test_overlapping_write_scopes_are_serialized(self):
        plane = ControlPlane(Path(self.temp.name) / "overlap.json", lambda _: PolicyDecision.ALLOW,
                             repo_root=self.root, evidence_verifier=lambda _: True)
        plane.create_goal("overlap", "x", "codex", ["done"], repo="r", base_sha="sha", integration_required=False)
        plane.add_task("overlap", {"id": "a", "objective": "write a", "write_scope": ["src"]})
        plane.add_task("overlap", {"id": "b", "objective": "write b", "write_scope": ["SRC/nested"]})
        plane.request_plan_approval("overlap")
        plane.approve_plan("overlap", repo="r", base_sha="sha", write_set=["src", "SRC/nested"], operation_type="write")
        self.assertEqual(plane.next_task("overlap")["id"], "a")
        self.assertIsNone(plane.next_task("overlap"))

    def test_active_cancel_requires_runtime_confirmation(self):
        dispatch = self.plane.next_task("goal")
        self.plane.mark_delegated("goal", "a", "external-a")
        runtime = Runtime("RUNNING", cancelled=True)
        self.plane.cancel_task("goal", "a", adapters={"codex": runtime})
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.CANCEL_REQUESTED.value)
        runtime.state = "CANCELLED"
        self.assertEqual(self.plane.reconcile_runtime({"codex": runtime}), ["a"])
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.CANCELLED.value)

    def test_active_cancel_without_runtime_confirmation_needs_reconciliation(self):
        self.plane.next_task("goal")
        self.plane.cancel_task("goal", "a")
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.NEEDS_RECONCILIATION.value)

    def test_parent_acceptance_requires_verified_evidence_from_integration_task(self):
        dispatch = self.plane.next_task("goal")
        packet, trusted, delivery = self.result("goal", "a", dispatch)
        packet["acceptance"] = [{"criterion_id": "all tasks pass", "status": "PASS", "evidence_ref": "acceptance-log-1"}]
        self.plane.ingest_result("goal", packet, delivery, trusted_context=trusted)
        self.assertNotIn("all tasks pass", self.plane.snapshot("goal").get("acceptance_results", {}))

    def test_unverified_evidence_cannot_complete_v2_task(self):
        dispatch = self.plane.next_task("goal")
        self.plane.evidence_verifier = lambda _: False
        self.ingest_success("a", dispatch)
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.BLOCKED.value)

    def test_write_result_without_artifact_verifier_cannot_complete(self):
        dispatch = self.plane.next_task("goal")
        self.plane.artifact_verifier = None
        self.ingest_success("a", dispatch)
        task = self.plane.snapshot("goal")["tasks"]["a"]
        self.assertEqual(task["state"], TaskState.BLOCKED.value)
        self.assertFalse(task["artifact_verification"]["verified"])

    def test_artifact_verifier_receives_repo_base_digest_and_scope(self):
        observed = {}
        self.plane.artifact_verifier = lambda context: (observed.update(context) or True)
        dispatch = self.plane.next_task("goal")
        self.ingest_success("a", dispatch)
        self.assertEqual(observed["repo"], "example/repo")
        self.assertEqual(observed["base_sha"], "abc123")
        self.assertEqual(observed["write_scope"], ["src"])
        self.assertEqual(observed["reported_changed_paths"], ["src/output.txt"])

    def test_all_cancelled_or_incomplete_parent_never_completes(self):
        plane = ControlPlane(Path(self.temp.name) / "cancel.json", lambda _: PolicyDecision.ALLOW, repo_root=self.root)
        plane.create_goal("cancel", "x", "codex", ["parent criterion"], repo="r", base_sha="sha",
                          integration_required=False)
        plane.add_task("cancel", {"id": "task", "objective": "x", "operation_type": "read"})
        plane.request_plan_approval("cancel")
        plane.approve_plan("cancel", repo="r", base_sha="sha", write_set=[], operation_type="read")
        plane.cancel_task("cancel", "task")
        self.assertEqual(plane.snapshot("cancel")["state"], TaskState.FAILED.value)

    def test_restart_preserves_v2_identity_and_state(self):
        dispatch = self.plane.next_task("goal")
        self.plane.mark_delegated("goal", "a", "external-1")
        restarted = ControlPlane(self.path, lambda _: PolicyDecision.ALLOW, repo_root=self.root,
                                 evidence_verifier=lambda _: True, approval_verifier=lambda _: True)
        task = restarted.snapshot("goal")["tasks"]["a"]
        self.assertEqual(task["attempt_id"], dispatch["attempt_id"])
        self.assertEqual(task["state"], TaskState.WAITING_FOR_AGENT.value)


if __name__ == "__main__":
    unittest.main()
