from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import time
from typing import Any, Callable
from urllib.parse import urlencode

from .core import GitHubAPI, SafetyError, StateStore, execute_task, process_once, reconcile, redact, utcnow


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _windows_process_count(image_name: str) -> int | None:
    """Return a best-effort process count without treating it as auth proof."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32FirstW.restype = wintypes.BOOL
        kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32NextW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        invalid_handle = ctypes.c_void_p(-1).value
        if snapshot in (-1, invalid_handle):
            return None
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                return None
            target = image_name.casefold()
            count = 0
            while True:
                if entry.szExeFile.casefold() == target:
                    count += 1
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
            return count
        finally:
            kernel32.CloseHandle(snapshot)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def live_runtime_status(config: dict[str, Any]) -> dict[str, Any]:
    """Describe local runtime evidence while failing closed on live handoff."""
    codex_cli = shutil.which("codex")
    gemini_cli = shutil.which("gemini")
    antigravity_cli = shutil.which("agy") or shutil.which("antigravity")
    antigravity_config = Path(config.get("antigravity_mcp_config", str(Path.home() / ".gemini" / "config" / "mcp_config.json"))).expanduser()
    antigravity_processes = _windows_process_count("Antigravity.exe")
    return {
        "state": "LIVE_BLOCKED",
        "ready": False,
        "codex": {
            "cli_present": bool(codex_cli),
            "cli_path": codex_cli,
            "authentication": "unverified",
        },
        "gemini": {
            "cli_present": bool(gemini_cli),
            "cli_path": gemini_cli,
            "authentication": "unverified",
        },
        "antigravity": {
            "cli_present": bool(antigravity_cli),
            "cli_path": antigravity_cli,
            "desktop_processes": antigravity_processes,
            "mcp_config_present": antigravity_config.is_file(),
            "authentication": "unverified",
        },
        "reasons": [
            "authenticated Codex ↔ Antigravity desktop handshake evidence is unavailable",
            "process/config presence is not sufficient proof for a Live handoff",
            "T7 OS-level cross-project write isolation is FAIL; unattended cross-project writes are prohibited",
        ],
    }


def doctor(config: dict[str, Any]) -> dict[str, Any]:
    return {"python": sys.version.split()[0], "codex": shutil.which("codex"), "git": shutil.which("git"),
        "token_configured": bool(os.environ.get(config.get("token_env", "GH_TOKEN"))),
        "host_id": config.get("host_id"), "allowed_repos": sorted(config.get("allowed_repos", {})),
        "live_handoff": live_runtime_status(config)}


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_is_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Lack of query permission is not proof that the owner has exited.
        return True
    except OSError:
        # Lock recovery must fail closed when process state is ambiguous.
        return True
    return True


def _windows_pid_is_alive(pid: int) -> bool:
    """Query process state without sending a signal or terminating the target."""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        # PROCESS_QUERY_LIMITED_INFORMATION is sufficient and avoids broad access.
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            # ERROR_INVALID_PARAMETER means the PID does not exist. For all
            # other errors (including access denied), conservatively retain lock.
            return ctypes.get_last_error() != 87
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    except (AttributeError, OSError, TypeError, ValueError):
        # An unavailable or failing query must never cause a live lock to be stolen.
        return True


class ReceiverLock:
    """Crash-recoverable single-writer lock scoped to one configured host."""

    def __init__(self, path: Path, host: str | None = None, pid: int | None = None):
        self.path = path
        self.host = host or socket.gethostname()
        self.pid = pid or os.getpid()
        self.owner = {"pid": self.pid, "host": self.host, "created_at": utcnow()}
        self.recovery_guard = self.path.with_name(self.path.name + ".recovery")
        self.held = False

    def _create(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(self.owner, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        self.held = True

    def acquire(self) -> None:
        if self.recovery_guard.exists():
            raise SafetyError("receiver lock recovery is already in progress")
        try:
            self._create()
            return
        except FileExistsError:
            pass
        try:
            existing = json.loads(self.path.read_text(encoding="utf-8"))
            existing_host = existing.get("host")
            existing_pid = int(existing.get("pid", 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise SafetyError("receiver lock exists but ownership cannot be verified") from exc
        if existing_host != self.host:
            raise SafetyError("receiver lock belongs to another host")
        if _pid_is_alive(existing_pid):
            raise SafetyError("another receiver invocation owns the local write lock")
        guard_descriptor = None
        guard_owned = False
        try:
            guard_descriptor = os.open(self.recovery_guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            guard_owned = True
            os.close(guard_descriptor); guard_descriptor = None
            current = json.loads(self.path.read_text(encoding="utf-8"))
            if current != existing or _pid_is_alive(int(current.get("pid", 0))):
                raise SafetyError("receiver lock changed during stale-lock recovery")
            self.path.unlink()
            self._create()
        except (FileExistsError, FileNotFoundError, json.JSONDecodeError) as exc:
            raise SafetyError("receiver lock changed during stale-lock recovery") from exc
        finally:
            if guard_descriptor is not None: os.close(guard_descriptor)
            if guard_owned: self.recovery_guard.unlink(missing_ok=True)

    def release(self) -> None:
        if not self.held:
            return
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.held = False
            return
        if current.get("pid") == self.pid and current.get("host") == self.host:
            self.path.unlink(missing_ok=True)
        self.held = False

    def __enter__(self) -> "ReceiverLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


def build_issue_url(config: dict[str, Any], body: str, title: str = "[Codex Task] ") -> str:
    maximum = int(config.get("max_issue_body_chars", 6000))
    if len(body) > maximum:
        raise SafetyError(f"task body exceeds max_issue_body_chars ({maximum})")
    if redact(body) != body or redact(title) != title:
        raise SafetyError("task body or title contains a secret-like value or private absolute path")
    repo = config.get("inbox_repo", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise SafetyError("inbox_repo must use OWNER/repository format")
    query = urlencode({"title": title, "body": body, "labels": "codex-task"})
    return f"https://github.com/{repo}/issues/new?{query}"


def run_watch(api: Any, config: dict[str, Any], state: StateStore, marker: Path,
              executor: Callable[[dict[str, Any]], dict[str, Any]] | None, *,
              sleep: Callable[[float], None] = time.sleep,
              processor: Callable[..., list[dict[str, Any]]] = process_once,
              max_cycles: int | None = None) -> int:
    poll = max(15.0, float(config.get("poll_interval_seconds", 30)))
    maximum = max(poll, float(config.get("max_backoff_seconds", 300)))
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"pid": os.getpid(), "host": socket.gethostname(), "started_at": utcnow()}), encoding="utf-8")
    failures = 0
    cycles = 0
    try:
        while marker.exists():
            delay = poll
            try:
                result = processor(api, config, state, executor=executor)
                print(redact(json.dumps(result, ensure_ascii=False, indent=2)))
                failures = 0
            except Exception as exc:
                failures += 1
                delay = min(maximum, poll * (2 ** (failures - 1)))
                print("receiver poll failed: " + redact(str(exc)), file=sys.stderr)
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            if marker.exists():
                sleep(delay)
    finally:
        marker.unlink(missing_ok=True)
    return 0


def _marker_path(config: dict[str, Any]) -> Path:
    return Path(config.get("run_marker", str(Path(config["state_file"]).with_suffix(".run")))).expanduser()


def _lock_path(config: dict[str, Any]) -> Path:
    return Path(config["state_file"]).expanduser().with_suffix(".lock")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="github-handoff")
    parser.add_argument("--config", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "status", "once", "dry-run", "start", "stop", "watch"):
        sub.add_parser(name)
    link_parser = sub.add_parser("issue-link")
    link_parser.add_argument("--body-file", type=Path, required=True)
    link_parser.add_argument("--title", default="[Codex Task] ")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command == "doctor":
        print(json.dumps(doctor(config), indent=2)); return 0
    if args.command == "status":
        state = StateStore(Path(config["state_file"]).expanduser())
        reconcile(state, int(config.get("stale_seconds", 3600)))
        print(json.dumps(state.load(), indent=2)); return 0
    marker = _marker_path(config)
    if args.command == "stop":
        marker.unlink(missing_ok=True); print("receiver stop requested"); return 0
    if args.command == "start":
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"requested_at": utcnow()}), encoding="utf-8")
        print("local run marker created; run 'watch' in the foreground; no service was installed"); return 0
    if args.command == "issue-link":
        try:
            print(build_issue_url(config, args.body_file.read_text(encoding="utf-8"), args.title)); return 0
        except (OSError, SafetyError) as exc:
            print(redact(str(exc)), file=sys.stderr); return 4

    state = StateStore(Path(config["state_file"]).expanduser())

    token = os.environ.get(config.get("token_env", "GH_TOKEN"), "")
    if not token:
        print("GitHub token is not configured", file=sys.stderr); return 2
    api = GitHubAPI(config["inbox_repo"], token, config.get("api_base", "https://api.github.com"))
    execute = None if args.command == "dry-run" else lambda task: execute_task(task, config)
    try:
        with ReceiverLock(_lock_path(config), host=str(config.get("host_id") or socket.gethostname())):
            if args.command == "watch":
                try:
                    return run_watch(api, config, state, marker, execute)
                except KeyboardInterrupt:
                    marker.unlink(missing_ok=True); print("receiver stopped"); return 130
            result = process_once(api, config, state, dry_run=args.command == "dry-run", executor=execute)
            print(redact(json.dumps(result, ensure_ascii=False, indent=2))); return 0
    except SafetyError as exc:
        print(redact(str(exc)), file=sys.stderr); return 3


if __name__ == "__main__":
    raise SystemExit(main())
