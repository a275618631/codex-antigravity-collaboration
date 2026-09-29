from __future__ import annotations
import argparse, json, os
from pathlib import Path
import shutil, sys
from .core import GitHubAPI, StateStore, execute_task, process_once, reconcile, redact

def load_config(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
def doctor(config: dict) -> dict:
    return {"python": sys.version.split()[0], "codex": shutil.which("codex"), "git": shutil.which("git"), "token_configured": bool(os.environ.get(config.get("token_env", "GH_TOKEN"))), "host_id": config.get("host_id"), "allowed_repos": sorted(config.get("allowed_repos", {}))}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="github-handoff"); parser.add_argument("--config", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "status", "once", "dry-run", "start", "stop"): sub.add_parser(name)
    args = parser.parse_args(argv); config = load_config(args.config); state = StateStore(Path(config["state_file"]).expanduser())
    if args.command == "doctor": print(json.dumps(doctor(config), indent=2)); return 0
    if args.command == "status": reconcile(state, int(config.get("stale_seconds", 3600))); print(json.dumps(state.load(), indent=2)); return 0
    marker = Path(config.get("run_marker", str(Path(config["state_file"]).with_suffix(".run")))).expanduser()
    if args.command == "stop": marker.unlink(missing_ok=True); print("receiver stop requested"); return 0
    if args.command == "start": marker.parent.mkdir(parents=True, exist_ok=True); marker.write_text(str(os.getpid()), encoding="ascii"); print("local run marker created; no service was installed"); return 0
    token = os.environ.get(config.get("token_env", "GH_TOKEN"), "")
    if not token: print("GitHub token is not configured", file=sys.stderr); return 2
    api = GitHubAPI(config["inbox_repo"], token, config.get("api_base", "https://api.github.com"))
    execute = None if args.command == "dry-run" else lambda task: execute_task(task, config)
    lock = Path(config["state_file"]).expanduser().with_suffix(".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600); os.close(descriptor)
    except FileExistsError:
        print("another receiver invocation owns the local write lock", file=sys.stderr); return 3
    try:
        print(redact(json.dumps(process_once(api, config, state, dry_run=args.command == "dry-run", executor=execute), ensure_ascii=False, indent=2)))
    finally:
        lock.unlink(missing_ok=True)
    return 0

if __name__ == "__main__": raise SystemExit(main())
