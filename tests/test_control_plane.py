import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from control_plane.orchestrator import ControlPlane, PolicyDecision, ResultPacketError, TaskState


def success(task_id, *, changed=None, discovered=None):
    return {
        "task_id": task_id, "status": "SUCCESS", "summary": "complete",
        "artifacts_changed": changed or ["src/output.txt"], "tests_run": ["unit"], "evidence": ["unit passed"],
        "unresolved": [], "newly_discovered_work": discovered or [], "recommended_next": "continue",
        "risks": [], "acceptance_passed": True,
    }


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state.json"
        self.plane = ControlPlane(self.path)
        self.plane.create_goal("goal", "prove automatic continuation", "codex", ["all tasks pass"])
        self.plane.add_task("goal", {"id": "a", "objective": "lead work", "write_scope": ["src"]})
        self.plane.add_task("goal", {"id": "b", "objective": "worker work", "owner_agent": "antigravity", "dependencies": ["a"], "write_scope": ["src"]})
        self.plane.add_task("goal", {"id": "c", "objective": "integration", "dependencies": ["b"], "write_scope": ["src"]})
        self.plane.request_plan_approval("goal")
        self.plane.approve_plan("goal")

    def tearDown(self):
        self.temp.cleanup()

    def test_mock_codex_antigravity_codex_continues_without_user_copy(self):
        self.assertEqual(self.plane.next_task("goal")["id"], "a")
        self.plane.ingest_result("goal", success("a"), "delivery-a")
        task_b = self.plane.next_task("goal")
        self.assertEqual(task_b["id"], "b")
        self.plane.mark_delegated("goal", "b", "antigravity-1")
        self.plane.ingest_result("goal", success("b"), "delivery-b")
        self.assertEqual(self.plane.next_task("goal")["id"], "c")
        self.plane.ingest_result("goal", success("c"), "delivery-c")
        self.assertEqual(self.plane.snapshot("goal")["state"], TaskState.COMPLETED.value)

    def test_duplicate_delivery_is_safe(self):
        self.plane.next_task("goal")
        self.plane.ingest_result("goal", success("a"), "same")
        self.assertTrue(self.plane.ingest_result("goal", success("a"), "same")["duplicate"])

    def test_malformed_result_is_rejected(self):
        self.plane.next_task("goal")
        with self.assertRaises(ResultPacketError):
            self.plane.ingest_result("goal", {"task_id": "a"}, "bad")

    def test_worker_success_with_failed_acceptance_fails_task(self):
        self.plane.next_task("goal")
        packet = success("a")
        packet["acceptance_passed"] = False
        self.plane.ingest_result("goal", packet, "failed-tests")
        self.assertEqual(self.plane.snapshot("goal")["tasks"]["a"]["state"], TaskState.FAILED.value)

    def test_write_scope_violation_is_rejected(self):
        self.plane.next_task("goal")
        with self.assertRaisesRegex(ResultPacketError, "write scope"):
            self.plane.ingest_result("goal", success("a", changed=["secrets/token.txt"]), "scope")

    def test_new_required_work_is_added_and_blocks_premature_completion(self):
        self.plane.next_task("goal")
        packet = success("a", discovered=[{"id": "discovered", "objective": "new required work", "dependencies": [], "write_scope": ["src"]}])
        self.plane.ingest_result("goal", packet, "new-work")
        snapshot = self.plane.snapshot("goal")
        self.assertIn("discovered", snapshot["tasks"])
        self.assertNotEqual(snapshot["state"], TaskState.COMPLETED.value)

    def test_policy_denial_precedes_routing(self):
        plane = ControlPlane(Path(self.temp.name) / "deny.json", lambda _: PolicyDecision.DENY)
        plane.create_goal("deny", "x", "codex", ["x"])
        plane.add_task("deny", {"id": "task", "objective": "x"})
        plane.request_plan_approval("deny")
        plane.approve_plan("deny")
        self.assertIsNone(plane.next_task("deny"))
        self.assertEqual(plane.snapshot("deny")["state"], TaskState.BLOCKED.value)

    def test_human_gate_pauses_only_gated_task(self):
        plane = ControlPlane(Path(self.temp.name) / "gate.json")
        plane.create_goal("gate", "x", "codex", ["x"])
        plane.add_task("gate", {"id": "task", "objective": "x", "human_gate_reason": "production deploy"})
        plane.request_plan_approval("gate")
        plane.approve_plan("gate")
        self.assertIsNone(plane.next_task("gate"))
        self.assertEqual(plane.snapshot("gate")["state"], TaskState.HUMAN_GATE.value)
        plane.approve_human_gate("gate", "task")
        self.assertEqual(plane.next_task("gate")["id"], "task")

    def test_restart_and_stale_recovery_are_durable(self):
        self.plane.next_task("goal")
        self.plane.ingest_result("goal", success("a"), "first")
        self.plane.next_task("goal")
        self.plane.mark_delegated("goal", "b", "worker")
        restarted = ControlPlane(self.path)
        self.assertEqual(restarted.snapshot("goal")["tasks"]["b"]["state"], TaskState.WAITING_FOR_AGENT.value)
        recovered = restarted.recover_stale(datetime.now(timezone.utc) + timedelta(seconds=1))
        self.assertEqual(recovered, ["b"])


if __name__ == "__main__":
    unittest.main()
