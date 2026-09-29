import datetime as dt
import json
from pathlib import Path
import tempfile
import threading
import unittest

from github_handoff.core import (MockGitHubAPI, SafetyError, StateStore, build_codex_command,
    parse_task, process_once, reconcile, redact, run_codex, task_digest, verify_approval)

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

class ContractTests(unittest.TestCase):
    def test_parse_and_digest_stable(self): self.assertEqual(task_digest(parse_task(BODY)), task_digest(parse_task(BODY)))
    def test_missing_field_rejected(self):
        with self.assertRaises(SafetyError): parse_task("## Task ID\nx")
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
        altered = BODY.replace("- src\n## Forbidden", "- ../private\n## Forbidden")
        with self.assertRaises(SafetyError): verify_approval(issue(altered), parse_task(altered), config("x"), {"used_nonces":[]})
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
    def test_complete_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); api=MockGitHubAPI([issue()]); executor=lambda task:{"status":"Completed","tests":"PASS"}
            self.assertEqual(process_once(api, config(Path(tmp)/"state.json"), store, executor=executor)[0]["state"], "Completed")
            self.assertEqual(process_once(api, config(Path(tmp)/"state.json"), store, executor=executor), [])
    def test_restart_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); data=store.load(); data["tasks"]["x"]={"state":"Running","updated_at":"2020-01-01T00:00:00+00:00"}; store.save(data)
            self.assertEqual(reconcile(store, 1), 1); self.assertEqual(store.load()["tasks"]["x"]["state"], "Blocked")
    def test_safe_command(self):
        command=build_codex_command(Path("worktree"),Path("schema"),Path("out")); self.assertIn("workspace-write", command); self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
    def test_unsafe_model_rejected(self):
        with self.assertRaisesRegex(SafetyError, "model"): build_codex_command(Path("w"),Path("s"),Path("o"),"model; command")
    def test_redaction(self): self.assertNotIn("ghp_", redact("token=ghp_abcdefghijklmnopqrstuvwxyz"))
    def test_cancel_runner(self):
        event=threading.Event(); event.set(); result=run_codex(["git","hash-object","--stdin"], "x", 5, event); self.assertEqual(result["status"], "Cancelled")
    def test_executor_exception_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=StateStore(Path(tmp)/"state.json"); api=MockGitHubAPI([issue()])
            result=process_once(api, config(Path(tmp)/"state.json"), store, executor=lambda task: (_ for _ in ()).throw(RuntimeError("boom")))
            self.assertEqual(result[0]["state"], "Blocked"); self.assertEqual(store.load()["tasks"]["GH-1"]["state"], "Blocked")

if __name__ == "__main__": unittest.main()
