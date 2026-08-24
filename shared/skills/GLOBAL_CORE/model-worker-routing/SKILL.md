---
name: model-worker-routing
description: Route a task to the existing Ox Alpha worker only when the user explicitly names Ox Alpha; preserve normal Codex behavior for all other tasks.
---

# Model Worker Routing

Use this skill only for an explicit opt-in route. Do not infer delegation from task size, cost, token usage, or coding difficulty.

## Trigger

Trigger only when the current user request explicitly contains Ox Alpha, including these forms:

- `本任務用 Ox Alpha`
- `本任務交給 Ox Alpha`
- `這個任務用 Ox Alpha`
- `這次用 Ox Alpha`
- `請用 Ox Alpha 執行本任務`
- `用 Ox Alpha 做這個任務`
- `本任務用 Ox Alpha 代替 Sol`
- `Use Ox Alpha for this task`
- `Run this task with Ox Alpha`
- `Delegate this task to Ox Alpha`

Do not trigger for generic requests such as「修改這個 Repo」「跑 tests」「省 token」or「用便宜模型」.

## Workflow

1. Preserve the user's task text, but send only the task and constraints to the worker. Do not send the full conversation, parent reasoning, or a pre-scanned repository dump.
2. Determine the current workspace from the active thread/cwd using `pwd` and, when applicable, `git rev-parse --show-toplevel`. If the workspace cannot be determined reliably, stop with a concise workspace-needed message; do not guess.
3. Validate that the workspace exists and is not a credential, system, home-root, or Codex-settings directory. A read-only task may inspect the current workspace; a write or write-test task must use an isolated/disposable workspace when the current workspace is dirty. Never overwrite uncommitted changes.
4. Choose the lowest deterministic permission mode:
   - `read` for analyse, inspect, scan, review, explain, or risk-finding requests.
   - `write` for modify, fix, update, refactor, or add-file requests without a test requirement.
   - `write-test` when the request also asks to run, verify, or pass tests.
   If uncertain, choose the lower mode.
5. Invoke the existing single source of truth exactly once:

   ```text
   python3 /Users/cheyu/.codex/model-routing-mvp/route_task.py \
     --message "<original task containing the explicit Ox Alpha route>" \
     --workspace "<validated workspace>" \
     --workspace-root "<safe parent root>" \
     --permission-mode "<read|write|write-test>"
   ```

   Do not reimplement routing or copy `worker_adapter.py`/`route_task.py` into this skill.
6. While the worker is running, do not perform the same primary task in the parent. Wait for the structured result.
7. On success, perform only targeted review of the result packet, reported diff, changed files, and relevant test output. Use the current parent by default. Invoke the existing `sol-auto` profile only when the user explicitly requests Sol review.
8. On any worker, provider, auth, model, workspace, rate-limit, tool, or context failure, report failure and stop. Never silently fall back to Luna/Sol.

## Result and user-facing behavior

Preserve and surface the worker fields `STATUS`, `SUMMARY`, `FILES_READ`, `FILES_CHANGED`, `COMMANDS_RUN`, `TESTS`, `PASS_FAIL`, `ERRORS`, `KNOWN_ISSUES`, `DIFF_SUMMARY`, `NEEDS_PARENT_REVIEW`, `WORKER_ID`, `MODEL_ROUTE`, `WORKTREE`, and `PROVIDER`.

Do not display credentials or sensitive environment values. If the worker is unavailable, say why at a high level and state that no automatic fallback occurred.

The worker route is `ox-alpha` through the existing registry; the parent model remains whatever is currently active. Do not modify the global default, Desktop binary, model picker, or network layer.
