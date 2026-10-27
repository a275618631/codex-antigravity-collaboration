import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
import sys
import subprocess

from github_handoff.core import (GitHubAPI, MockGitHubAPI, SafetyError, StateStore, build_codex_command,
    parse_task, process_once, progress_summary, reconcile, redact, result_packet_state, run_codex, task_digest,
    validate_changed_paths, validate_lineage, validate_result_packet, verify_approval)

BODY = """## Task ID
GH-1
## Goal
Update docs
## Target Repo
OWNER/example
## Base Branch
main
## Read Scope
- src
- tests
## Write Scope
- src
## Forbidden
- secrets
## Acceptance
- tests pass
## Host
host-a
## Lane
standard
## Risk
low
"""

def config(state):
    return {"host_id":"host-a", "allowed_task_actors":["owner"], "allowed_approvers":["owner"],
        "allowed_repos":{"OWNER/example":{"base_branches":["main"],"read_scope":["src","tests"],"write_scope":["src"]}},
        "state_file":str(state), "report_interval_seconds":300, "stale_seconds":1}

def issue(body=BODY, actor="owner", nonce="nonce-123456"):
    digest = task_digest(parse_task(body))
    return {"number":1,"body":body,"author":actor,"body_updated_at":"2026-01-01T00:00:00Z",
        "comments":[{"author":"owner","created_at":"2026-01-01T00:00:01Z","body":f"/codex-approve digest={digest} nonce={nonce} host=host-a"}]}

def completed_outcome():
    packet = {"task_id":"GH-1", "responder":"Codex", "status":"SUCCESS", "summary":"done",
        "changes":[], "evidence":[], "validation_results":[], "risks_and_limitations":[],
        "remaining_work":[], "recommendation":"none", "transport":{
            "issue":1, "task_digest":task_digest(parse_task(BODY)), "host":"host-a",
            "approval_actor":"owner", "approval_nonce":"nonce-123456", "state":"Running"}}
    return {"status":"Completed", "tests":"PASS", "result_packet":{"result_packet":packet}}

class ContractTests(unittest.TestCase):
    def test_parse_and_digest_stable(self): self.assertEqual(task_digest(parse_task(BODY)), task_digest(parse_task(BODY)))
    def test_missing_field_rejected(self):
        with self.assertRaises(SafetyError): parse_task("## Task ID\nx")
        with self.assertRaisesRegex(SafetyError, "string"): parse_task(None)
    def test_optional_origin_metadata_is_validated(self):
        body = BODY + "## Origin Surface\nchatgpt_plus\n## Client\nmobile\n## Parent Task ID\nPARENT-1\n## Revision\n2\n"
        task = parse_task(body)
        self.assertEqual(task["Origin Surface"], "chatgpt_plus")
        self.assertEqual(task["Client"], "mobile")
        self.assertEqual(task["Parent Task ID"], "PARENT-1")
        self.assertEqual(task["Revision"], 2)

    def test_optional_metadata_rejects_invalid_revision_and_surface(self):
        with self.assertRaisesRegex(SafetyError, "revision"):
            parse_task(BODY + "## Revision\n0\n")
        with self.assertRaisesRegex(SafetyError, "origin surface"):
            parse_task(BODY + "## Origin Surface\nunknown\n")
    def test_actor_rejected(self):
        with self.assertRaisesRegex(SafetyError, "actor"): verify_approval(issue(actor="intruder"), parse_task(BODY), config("x"), {"used_nonces":[]})
    def test_host_rejected(self):
        altered = BODY.replace("host-a", "host-b")
        with self.assertRaisesRegex(SafetyError, "host"): verify_approval(issue(altered), parse_task(altered), config("x"), {"used_nonces":[]})
    def test_repo_rejected(self):
        altered = BODY.replace("OWNER/example", "OWNER/not-allowed")
        with self.assertRaisesRegex(SafetyError, "repo"): verify_approval(issue(altered), parse_task(altered), config("x"), {"used_nonces":[]})
    def test_base_branch_rejected(self):
        altered = BODY.replace("## Base Branch\nmain", "## Base Branch\nrelease")
        with self.assertRaisesRegex(SafetyError, "base branch"): verify_approval(issue(altered), parse_task(altered), config("x"), {"used_nonces":[]})
    def test_scope_rejected(self):
        for scope in ("../private", "src/../private", r"src\..\private", "C:/private"):
            with self.subTest(scope=scope):
                altered = BODY.replace("- src\n## Forbidden", f"- {scope}\n## Forbidden")
                with self.assertRaises(SafetyError):
                    verify_approval(issue(altered), parse_task(altered), config("x"), {"used_nonces":[]})

    def test_empty_write_scope_is_rejected_before_execution(self):
        body = BODY.replace("## Write Scope\n- src\n", "## Write Scope\n")
        with self.assertRaisesRegex(SafetyError, "Write Scope"):
            parse_task(body)

        task = parse_task(BODY); task["Write Scope"] = []
        candidate = issue()
        digest = task_digest(task)
        candidate["comments"][0]["body"] = f"/codex-approve digest={digest} nonce=nonce-123456 host=host-a"
        with self.assertRaisesRegex(SafetyError, "write scope"):
            verify_approval(candidate, task, config("x"), {"used_nonces": []})
    def test_edit_invalidates_digest(self):
        changed = BODY.replace("Update docs", "Update code")
        candidate = issue(); candidate["body"] = changed
        with self.assertRaisesRegex(SafetyError, "invalidated"): verify_approval(candidate, parse_task(changed), config("x"), {"used_nonces":[]})
    def test_nonce_one_time(self):
        with self.assertRaisesRegex(SafetyError, "already used"): verify_approval(issue(), parse_task(BODY), config("x"), {"used_nonces":["nonce-123456"]})
    def test_approval_must_follow_edit(self):
        candidate=issue(); candidate["body_updated_at"]="2026-01-01T00:00:02Z"
        with self.assertRaisesRegex(SafetyError, "latest issue edit"): verify_approval(candidate, parse_task(BODY), config("x"), {"used_nonces":[]})
    def test_dry_run_no_state_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); result=process_once(MockGitHubAPI([issue()]), config(Path(tmp)/"state.json"), store, dry_run=True)
            self.assertTrue(result[0]["dry_run"]); self.assertEqual(store.load()["tasks"], {})
    def test_unapproved_task_is_recorded_at_human_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = issue(); candidate["comments"] = []
            store = StateStore(Path(tmp) / "state.json"); calls = []
            result = process_once(MockGitHubAPI([candidate]), config(Path(tmp) / "state.json"), store,
                executor=lambda task: calls.append(task))
            self.assertEqual(result[0]["state"], "Awaiting Approval")
            self.assertEqual(result[0]["human_gate"], "PENDING")
            self.assertEqual(store.load()["tasks"]["GH-1"]["state"], "Awaiting Approval")
            self.assertEqual(store.load()["tasks"]["GH-1"]["human_gate"], "PENDING")
            self.assertEqual(calls, [])
    def test_invalid_human_gate_blocks_before_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json"); calls = []
            result = process_once(MockGitHubAPI([issue(actor="intruder")]), config(Path(tmp) / "state.json"), store,
                executor=lambda task: calls.append(task))
            self.assertEqual(result[0]["state"], "Rejected")
            self.assertEqual(store.load()["tasks"]["GH-1"]["state"], "Blocked")
            self.assertEqual(store.load()["tasks"]["GH-1"]["human_gate"], "BLOCKED")
            self.assertEqual(calls, [])
    def test_complete_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); api=MockGitHubAPI([issue()]); executor=lambda task:completed_outcome()
            self.assertEqual(process_once(api, config(Path(tmp)/"state.json"), store, executor=executor)[0]["state"], "Completed")
            self.assertEqual(store.load()["tasks"]["GH-1"]["human_gate"], "APPROVED")
            self.assertEqual(process_once(api, config(Path(tmp)/"state.json"), store, executor=executor), [])
    def test_restart_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); data=store.load(); data["tasks"]["x"]={
                "state":"Running", "human_gate":"APPROVED", "updated_at":"2020-01-01T00:00:00+00:00"}; store.save(data)
            self.assertEqual(reconcile(store, 1), 1)
            self.assertEqual(store.load()["tasks"]["x"]["state"], "Blocked")
            self.assertEqual(store.load()["tasks"]["x"]["human_gate"], "BLOCKED")
    def test_safe_command(self):
        command=build_codex_command(Path("worktree"),Path("schema"),Path("out")); self.assertIn("workspace-write", command); self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
    def test_unsafe_model_rejected(self):
        with self.assertRaisesRegex(SafetyError, "model"): build_codex_command(Path("w"),Path("s"),Path("o"),"model; command")
    def test_redaction(self): self.assertNotIn("ghp_", redact("token=ghp_abcdefghijklmnopqrstuvwxyz"))
    def test_redaction_covers_additional_credential_shapes(self):
        value = " ".join((
            "github_pat_abcdefghijklmnopqrstuvwxyz1234567890",
            "AKIA1234567890ABCDEF",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturepayload123",
            "-----BEGIN RSA PRIVATE KEY-----",
            "https://alice:password@example.invalid/repo",
        ))
        redacted = redact(value)
        for secret in ("github_pat_", "AKIA1234567890ABCDEF", "eyJhbGciOiJIUzI1NiJ9", "PRIVATE KEY", "alice:password@"):
            self.assertNotIn(secret, redacted)

    def test_result_transport_must_match_expected(self):
        expected = {"issue": 1, "task_digest": "a" * 64, "host": "host-a",
                    "approval_actor": "owner", "approval_nonce": "nonce-123456", "state": "Running"}
        payload = {"result_packet": {"task_id": "GH-1", "responder": "Codex", "status": "SUCCESS",
            "summary": "done", "changes": [], "evidence": [], "validation_results": [],
            "risks_and_limitations": [], "remaining_work": [], "recommendation": "none",
            "transport": expected}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"; path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(validate_result_packet(path, "GH-1", expected), payload)
            tampered = json.loads(json.dumps(payload)); tampered["result_packet"]["transport"]["host"] = "host-b"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(SafetyError, "transport"):
                validate_result_packet(path, "GH-1", expected)

    def test_result_packet_enforces_strict_schema_types_and_keys(self):
        payload = {"result_packet": {"task_id": "GH-1", "responder": "Codex", "status": "SUCCESS",
            "summary": "done", "changes": [], "evidence": [], "validation_results": [],
            "risks_and_limitations": [], "remaining_work": [], "recommendation": "none",
            "transport": {"issue": 1, "task_digest": "a" * 64, "host": "host-a",
                "approval_actor": "owner", "approval_nonce": "nonce-123456", "state": "Running"}}}
        invalid_results = []
        extra_key = json.loads(json.dumps(payload)); extra_key["result_packet"]["extra"] = "not allowed"
        invalid_results.append(extra_key)
        wrong_type = json.loads(json.dumps(payload)); wrong_type["result_packet"]["changes"] = "not-an-array"
        invalid_results.append(wrong_type)
        wrong_responder = json.loads(json.dumps(payload)); wrong_responder["result_packet"]["responder"] = "Gemini"
        invalid_results.append(wrong_responder)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            for result in invalid_results:
                with self.subTest(result=result):
                    path.write_text(json.dumps(result), encoding="utf-8")
                    with self.assertRaisesRegex(SafetyError, "strict schema"):
                        validate_result_packet(path, "GH-1")
    def test_result_packet_status_mapping_is_fail_closed(self):
        for packet_status, receiver_status in (("SUCCESS", "Completed"), ("FAILED", "Failed"),
                                                ("PARTIAL", "Blocked"), ("BLOCKED", "Blocked")):
            self.assertEqual(result_packet_state({"result_packet": {"status": packet_status}}), receiver_status)
    def test_cancel_runner(self):
        event=threading.Event(); event.set(); result=run_codex([sys.executable,"-c","import time; time.sleep(5)"], "x", 5, event); self.assertEqual(result["status"], "Cancelled")
    def test_runner_does_not_inherit_receiver_token(self):
        previous = os.environ.get("GH_TOKEN"); os.environ["GH_TOKEN"] = "github_pat_not-for-child-process-1234567890"
        code = 'import json,os; print(json.dumps({"type":"probe","has_token":"GH_TOKEN" in os.environ})); print(json.dumps({"type":"turn.completed"}))'
        try: result = run_codex([sys.executable, "-c", code], "x", 5)
        finally:
            if previous is None: os.environ.pop("GH_TOKEN", None)
            else: os.environ["GH_TOKEN"] = previous
        self.assertEqual(result["status"], "Completed")
        self.assertFalse(result["events"][0]["has_token"])
    def test_runner_requires_success_terminal_event(self):
        result=run_codex([sys.executable,"-c","print('{}')"], "x", 5)
        self.assertEqual(result["status"], "Failed")
    def test_runner_accepts_success_terminal_event(self):
        result=run_codex([sys.executable,"-c",'print(\'{"type":"turn.completed"}\')'], "x", 5)
        self.assertEqual(result["status"], "Completed")
    def test_runner_rejects_invalid_jsonl(self):
        result=run_codex([sys.executable,"-c","print('not-json')"], "x", 5)
        self.assertEqual(result["status"], "Failed")
    def test_result_schema_is_strict_for_every_object(self):
        schema=json.loads((Path(__file__).parents[1]/"github_handoff"/"result.schema.json").read_text(encoding="utf-8"))
        def visit(node):
            if isinstance(node,dict):
                if node.get("type")=="object": self.assertIs(node.get("additionalProperties"),False)
                for value in node.values(): visit(value)
            elif isinstance(node,list):
                for value in node: visit(value)
        visit(schema)
    def test_progress_summary_excludes_raw_events_and_logs(self):
        summary=progress_summary({"task_id":"x","state":"Completed","result":{"status":"Completed",
            "stdout":"secret log","stderr":"private path","events":[{"type":"turn.completed"}],
            "changed_files":["docs/a.txt"],"result_packet":{"result_packet":{"status":"SUCCESS","summary":"done"}}}})
        self.assertNotIn("secret log",summary); self.assertNotIn("private path",summary); self.assertNotIn("turn.completed",summary)
        self.assertIn("docs/a.txt",summary); self.assertIn("done",summary)
    def test_changed_path_outside_scope_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); subprocess.run(["git","init","-q",str(root)],check=True)
            subprocess.run(["git","-C",str(root),"config","user.email","test@example.invalid"],check=True)
            subprocess.run(["git","-C",str(root),"config","user.name","Test"],check=True)
            (root/"src").mkdir(); (root/"src"/"ok.txt").write_text("ok",encoding="utf-8")
            subprocess.run(["git","-C",str(root),"add","src/ok.txt"],check=True); subprocess.run(["git","-C",str(root),"commit","-qm","base"],check=True)
            (root/"outside.txt").write_text("bad",encoding="utf-8")
            baseline = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            with self.assertRaisesRegex(SafetyError,"outside approved write scope"): validate_changed_paths(root,["src"],baseline)
    def test_ignored_untracked_path_outside_scope_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); subprocess.run(["git","init","-q",str(root)],check=True)
            subprocess.run(["git","-C",str(root),"config","user.email","test@example.invalid"],check=True)
            subprocess.run(["git","-C",str(root),"config","user.name","Test"],check=True)
            (root/"src").mkdir(); (root/"src"/"ok.txt").write_text("ok",encoding="utf-8")
            (root/".gitignore").write_text("ignored/\n",encoding="utf-8")
            subprocess.run(["git","-C",str(root),"add","."],check=True); subprocess.run(["git","-C",str(root),"commit","-qm","base"],check=True)
            (root/"ignored").mkdir(); (root/"ignored"/"secret.txt").write_text("bad",encoding="utf-8")
            baseline = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            with self.assertRaisesRegex(SafetyError,"outside approved write scope"): validate_changed_paths(root,["src"],baseline)

    def test_committed_out_of_scope_path_is_rejected_against_initial_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            (root / "src").mkdir(); (root / "src" / "ok.txt").write_text("ok", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "src/ok.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            baseline = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            (root / "outside.txt").write_text("out of scope", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "outside.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "agent commit"], check=True)
            with self.assertRaisesRegex(SafetyError, "outside approved write scope"):
                validate_changed_paths(root, ["src"], baseline)
    def test_executor_exception_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); api=MockGitHubAPI([issue()])
            result=process_once(api, config(Path(tmp)/"state.json"), store, executor=lambda task: (_ for _ in ()).throw(RuntimeError("boom")))
            self.assertEqual(result[0]["state"], "Blocked"); self.assertEqual(store.load()["tasks"]["GH-1"]["state"], "Blocked")
            self.assertEqual(store.load()["tasks"]["GH-1"]["human_gate"], "BLOCKED")

    def test_invalid_executor_outcome_is_blocked_without_sticking_in_running(self):
        for outcome in (None, {}, {"status": "Running"}, {"status": []}, {"status": {"state": "Completed"}}):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                store = StateStore(Path(tmp) / "state.json")
                result = process_once(MockGitHubAPI([issue()]), config(Path(tmp) / "state.json"), store,
                    executor=lambda task: outcome)
                record = store.load()["tasks"]["GH-1"]
                self.assertEqual(result[0]["state"], "Blocked")
                self.assertEqual(record["state"], "Blocked")
                self.assertEqual(record["human_gate"], "BLOCKED")

    def test_executor_failure_and_cancellation_close_human_gate(self):
        for status, expected_gate in (("Failed", "BLOCKED"), ("Blocked", "BLOCKED"),
                                      ("Cancelled", "CANCELLED")):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                store = StateStore(Path(tmp) / "state.json")
                result = process_once(MockGitHubAPI([issue()]), config(Path(tmp) / "state.json"), store,
                    executor=lambda task: {"status": status})
                record = store.load()["tasks"]["GH-1"]
                self.assertEqual(result[0]["state"], status)
                self.assertEqual(record["state"], status)
                self.assertEqual(record["human_gate"], expected_gate)

    def test_completed_executor_with_invalid_result_packet_is_blocked_before_validation(self):
        malformed_outcomes = (
            {"status": "Completed"},
            {"status": "Completed", "result_packet": None},
            {"status": "Completed", "result_packet": []},
            {"status": "Completed", "result_packet": {"result_packet": []}},
            {"status": "Completed", "result_packet": {"result_packet": {"status": []}}},
            {"status": "Completed", "result_packet": {"result_packet": {"status": "FAILED"}}},
        )
        for outcome in malformed_outcomes:
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                store = StateStore(Path(tmp) / "state.json")
                api = MockGitHubAPI([issue()])
                result = process_once(api, config(Path(tmp) / "state.json"), store,
                    executor=lambda task: outcome)
                record = store.load()["tasks"]["GH-1"]
                self.assertEqual(result[0]["state"], "Blocked")
                self.assertEqual(record["state"], "Blocked")
                self.assertEqual(record["human_gate"], "BLOCKED")
                reported_states = [json.loads(body.split("```json\n", 1)[1].rsplit("\n```", 1)[0])["state"]
                    for _, _, body in api.calls]
                self.assertEqual(reported_states, ["Queued", "Running", "Blocked"])

    def test_progress_summary_ignores_malformed_executor_packet(self):
        summary = progress_summary({"task_id": "GH-1", "state": "Completed", "result": {
            "status": "Completed", "result_packet": {"result_packet": []}}})
        self.assertIn('"state": "Completed"', summary)
        self.assertNotIn('"result_packet":', summary)

    def test_progress_uses_one_comment_and_updates_each_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json"); api = MockGitHubAPI([issue()])
            result = process_once(api, config(Path(tmp) / "state.json"), store,
                executor=lambda task: completed_outcome())
            self.assertEqual(result[0]["state"], "Completed")
            self.assertEqual(sum(call[0] is None for call in api.calls), 1)
            states = []
            for _, _, body in api.calls:
                encoded = body.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
                states.append(json.loads(encoded)["state"])
            self.assertEqual(states, ["Queued", "Running", "Validating", "Reporting", "Completed"])
            self.assertIsNotNone(store.load()["tasks"]["GH-1"].get("progress_comment_id"))

    def test_same_task_id_with_new_digest_is_rejected_as_new_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"; store = StateStore(path); api = MockGitHubAPI([issue()])
            process_once(api, config(path), store, executor=lambda task: completed_outcome())
            changed = BODY.replace("Update docs", "Update code")
            api.issues = [issue(changed)]
            result = process_once(api, config(path), store, executor=lambda task: completed_outcome())
            self.assertEqual(result[0]["state"], "Rejected")
            self.assertIn("child task/revision", result[0]["reason"])

    def test_trusted_pre_execution_cancel_prevents_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json"); candidate = issue()
            candidate["comments"].append({"author": "owner", "created_at": "2026-01-01T00:00:02Z",
                "body": "/codex-cancel task=GH-1 host=host-a"})
            calls = []
            result = process_once(MockGitHubAPI([candidate]), config(Path(tmp) / "state.json"), store,
                executor=lambda task: calls.append(task))
            self.assertEqual(result[0]["state"], "Cancelled")
            self.assertEqual(calls, [])
            self.assertEqual(store.load()["tasks"]["GH-1"]["cancellation_actor"], "owner")
            self.assertEqual(store.load()["tasks"]["GH-1"]["human_gate"], "CANCELLED")

    def test_untrusted_cancel_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "state.json"); candidate = issue()
            candidate["comments"].append({"author": "intruder", "created_at": "2026-01-01T00:00:02Z",
                "body": "/codex-cancel task=GH-1 host=host-a"})
            result = process_once(MockGitHubAPI([candidate]), config(Path(tmp) / "state.json"), store,
                executor=lambda task: completed_outcome())
            self.assertEqual(result[0]["state"], "Completed")

    def test_claim_revalidation_rejects_last_moment_edit(self):
        class ChangedAPI(MockGitHubAPI):
            def get_task(self, number):
                latest = dict(super().get_task(number)); latest["body"] = latest["body"].replace("Update docs", "Changed late")
                return latest
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]; store=StateStore(Path(tmp)/"state.json")
            result=process_once(ChangedAPI([issue()]),config(Path(tmp)/"state.json"),store,executor=lambda task:calls.append(task))
            self.assertEqual(result[0]["state"],"Rejected"); self.assertEqual(calls,[])
            self.assertEqual(store.load()["tasks"]["GH-1"]["state"],"Blocked")

    def test_queued_restart_adopts_existing_progress_comment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"state.json"; store=StateStore(path); candidate=issue()
            candidate["comments"].append({"id":777,"author":"receiver","created_at":"2026-01-01T00:00:02Z","body":"<!-- codex-handoff-progress -->\n{}"})
            data=store.load(); data["tasks"]["GH-1"]={"state":"Queued","digest":task_digest(parse_task(BODY)),"issue_number":1,
                "approval_actor":"owner","approval_nonce":"nonce-123456","revision":1,"updated_at":"2026-01-01T00:00:02+00:00"}; store.save(data)
            api=MockGitHubAPI([candidate]); result=process_once(api,config(path),store,executor=lambda task:completed_outcome())
            self.assertEqual(result[0]["state"],"Completed"); self.assertEqual(api.calls[0][0],777)

    def test_child_lineage_requires_parent_and_next_revision(self):
        state={"tasks":{"PARENT":{"revision":1,"state":"Completed"}}}
        child=parse_task(BODY.replace("GH-1","CHILD")+"## Parent Task ID\nPARENT\n## Revision\n2\n")
        validate_lineage(child,state)
        with self.assertRaisesRegex(SafetyError,"not found"):
            validate_lineage({**child,"Parent Task ID":"MISSING"},state)
        with self.assertRaisesRegex(SafetyError,"revision"):
            validate_lineage({**child,"Revision":3},state)

    def test_github_lists_are_paginated_and_pull_requests_are_excluded(self):
        class FakeAPI(GitHubAPI):
            def __init__(self):
                super().__init__("O/R", "not-a-real-token"); self.paths = []
            def _request(self, method, path, payload=None):
                self.paths.append(path)
                if "issues?" in path and path.endswith("page=1"):
                    return [{"number": index, "body": BODY, "user": {"login": "owner"},
                        "created_at": "2026-01-01T00:00:00Z", **({"pull_request": {}} if index == 1 else {})}
                        for index in range(1, 101)]
                if "issues?" in path and path.endswith("page=2"):
                    return [{"number": 101, "body": BODY, "user": {"login": "owner"},
                        "created_at": "2026-01-01T00:00:00Z"}]
                return []
        api = FakeAPI(); tasks = api.list_tasks()
        self.assertEqual(len(tasks), 100)
        self.assertNotIn(1, [task["number"] for task in tasks])
        self.assertIn(101, [task["number"] for task in tasks])
        self.assertTrue(any("page=2" in path for path in api.paths))

if __name__ == "__main__": unittest.main()
