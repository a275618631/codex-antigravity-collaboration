import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from github_handoff.cli import ReceiverLock, _pid_is_alive, build_issue_url, live_runtime_status, main, run_watch
from github_handoff.core import SafetyError, StateStore


class LifecycleTests(unittest.TestCase):
    def test_windows_pid_liveness_uses_query_helper_not_os_kill(self):
        with mock.patch("github_handoff.cli.os.name", "nt"), \
             mock.patch("github_handoff.cli._windows_pid_is_alive", return_value=True) as query, \
             mock.patch("github_handoff.cli.os.kill") as kill:
            self.assertTrue(_pid_is_alive(1234))
        query.assert_called_once_with(1234)
        kill.assert_not_called()

    def test_unexpected_posix_liveness_error_fails_closed(self):
        with mock.patch("github_handoff.cli.os.name", "posix"), \
             mock.patch("github_handoff.cli.os.kill", side_effect=OSError("unknown")):
            self.assertTrue(_pid_is_alive(1234))

    def test_live_lock_cannot_be_stolen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receiver.lock"
            first = ReceiverLock(path, host="host-a", pid=os.getpid()); first.acquire()
            try:
                with self.assertRaisesRegex(SafetyError, "owns"):
                    ReceiverLock(path, host="host-a", pid=os.getpid()).acquire()
            finally:
                first.release()

    def test_dead_same_host_lock_is_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receiver.lock"
            path.write_text(json.dumps({"pid": 2_147_483_000, "host": "host-a"}), encoding="utf-8")
            lock = ReceiverLock(path, host="host-a", pid=os.getpid()); lock.acquire()
            try:
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["pid"], os.getpid())
            finally:
                lock.release()

    def test_cross_host_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receiver.lock"
            path.write_text(json.dumps({"pid": 2_147_483_000, "host": "other-host"}), encoding="utf-8")
            with self.assertRaisesRegex(SafetyError, "another host"):
                ReceiverLock(path, host="host-a").acquire()

    def test_two_stale_recovery_attempts_have_one_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receiver.lock"
            path.write_text(json.dumps({"pid": 2_147_483_000, "host": "host-a"}), encoding="utf-8")
            barrier = threading.Barrier(2); winners = []; failures = []; locks = []
            def attempt(index):
                lock = ReceiverLock(path, host="host-a", pid=os.getpid()); locks.append(lock); barrier.wait()
                try: lock.acquire(); winners.append(index)
                except SafetyError: failures.append(index)
            threads=[threading.Thread(target=attempt,args=(i,)) for i in range(2)]
            [thread.start() for thread in threads]; [thread.join() for thread in threads]
            self.assertEqual(len(winners),1); self.assertEqual(len(failures),1)
            for lock in locks: lock.release()

    def test_failed_recovery_contender_cannot_remove_owner_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"receiver.lock"; guard=Path(str(path)+".recovery")
            path.write_text(json.dumps({"pid":2_147_483_000,"host":"host-a"}),encoding="utf-8")
            guard.write_text("owner",encoding="utf-8")
            for _ in range(2):
                with self.assertRaisesRegex(SafetyError,"recovery"):
                    ReceiverLock(path,host="host-a").acquire()
                self.assertTrue(guard.exists())

    def test_status_initializes_state_without_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); config_path=root/"config.json"
            config_path.write_text(json.dumps({"state_file":str(root/"state.json")}),encoding="utf-8")
            previous=os.environ.pop("GH_TOKEN",None)
            try:
                with contextlib.redirect_stdout(io.StringIO()): code=main(["--config",str(config_path),"status"])
                self.assertEqual(code,0)
            finally:
                if previous is not None: os.environ["GH_TOKEN"]=previous

    def test_issue_link_encodes_task_without_token(self):
        config = {"inbox_repo": "OWNER/private-inbox", "max_issue_body_chars": 6000}
        url = build_issue_url(config, "## Goal\n修正 docs & tests", "[Codex Task] 測試")
        parsed = urlparse(url); query = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/OWNER/private-inbox/issues/new")
        self.assertEqual(query["title"], ["[Codex Task] 測試"])
        self.assertEqual(query["body"], ["## Goal\n修正 docs & tests"])
        self.assertEqual(query["labels"], ["codex-task"])

    def test_issue_link_rejects_size_and_secret(self):
        with self.assertRaisesRegex(SafetyError, "max_issue_body_chars"):
            build_issue_url({"inbox_repo": "O/R", "max_issue_body_chars": 3}, "four")
        with self.assertRaisesRegex(SafetyError, "secret-like"):
            build_issue_url({"inbox_repo": "O/R"}, "token=github_pat_abcdefghijklmnopqrstuvwxyz1234567890")

    def test_issue_link_cli_does_not_require_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config_path = root / "config.json"; body_path = root / "body.md"
            config_path.write_text(json.dumps({"inbox_repo": "O/R", "state_file": str(root / "state.json")}), encoding="utf-8")
            body_path.write_text("## Goal\nSafe task", encoding="utf-8")
            previous = os.environ.pop("GH_TOKEN", None)
            try:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(["--config", str(config_path), "issue-link", "--body-file", str(body_path)])
                self.assertEqual(code, 0); self.assertIn("https://github.com/O/R/issues/new?", output.getvalue())
            finally:
                if previous is not None: os.environ["GH_TOKEN"] = previous

    def test_live_runtime_status_fails_closed_without_handshake_proof(self):
        status = live_runtime_status({})
        self.assertEqual(status["state"], "LIVE_BLOCKED")
        self.assertFalse(status["ready"])
        self.assertEqual(status["codex"]["authentication"], "unverified")
        self.assertEqual(status["gemini"]["authentication"], "unverified")
        self.assertIn("cli_present", status["antigravity"])
        self.assertEqual(status["antigravity"]["authentication"], "unverified")
        self.assertTrue(status["reasons"])

    def test_watch_backoff_is_bounded_and_resets_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); marker = root / "run"; state = StateStore(root / "state.json")
            outcomes = [RuntimeError("first"), RuntimeError("second"), [], RuntimeError("again")]; sleeps = []

            def processor(*args, **kwargs):
                outcome = outcomes.pop(0)
                if isinstance(outcome, Exception): raise outcome
                return outcome

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_watch(object(), {"poll_interval_seconds": 15, "max_backoff_seconds": 30}, state,
                    marker, None, sleep=sleeps.append, processor=processor, max_cycles=4)
            self.assertEqual(code, 0); self.assertEqual(sleeps, [15.0, 30.0, 15.0]); self.assertFalse(marker.exists())

    def test_watch_stops_when_marker_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); marker = root / "run"; state = StateStore(root / "state.json"); calls = []

            def processor(*args, **kwargs):
                calls.append(True); marker.unlink(); return []

            with contextlib.redirect_stdout(io.StringIO()):
                code = run_watch(object(), {}, state, marker, None,
                    sleep=lambda _: self.fail("sleep not expected"), processor=processor)
            self.assertEqual(code, 0); self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
