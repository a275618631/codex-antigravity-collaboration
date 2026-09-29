# GitHub 本地 Codex 自動交接使用手冊（2026-09-29）

## 目前可用範圍

目前已驗證的正式流程是：

```text
ChatGPT／手機建立 GitHub Issue
→ 授權者核對內容並張貼 digest + nonce 核准
→ Windows 主機以前景 once 模式接單
→ Codex 在獨立 worktree 修改與驗證
→ Receiver 將最小化結果摘要寫回同一個 Issue
```

- Windows 前景 `once`：已通過真實 Private Repo E2E。
- macOS：NOT VERIFIED。
- 常駐背景輪詢：尚未啟用或驗證。
- 自動 Merge：刻意不提供。

## 事前準備

1. 一個專用的 **Private GitHub Inbox Repo**。
2. 一個非敏感測試 Repo；正式 Repo 必須另外加入本機 allowlist。
3. Python 3.11+、Git、已登入的 Codex CLI。
4. 複製 `github_handoff/config.example.json` 到 Git 以外的受限位置。
5. Fine-grained GitHub Token：
   - 只選 Inbox Repo 與需要執行的 Repo。
   - Issues：Read and write。
   - Metadata：Read-only。
   - Token 只注入 Receiver 前景程序，不寫入設定檔、Issue、日誌或聊天。

## 設定 Receiver

設定檔必須固定以下安全邊界：

- `inbox_repo`：唯一 Private Inbox。
- `host_id`：唯一主要執行主機。
- `allowed_task_actors`、`allowed_approvers`：GitHub 帳號白名單。
- `allowed_repos`：Repo、base branch、read/write scope 與本機 clone/worktree 路徑。
- `state_file`：Git 以外的受限本機狀態檔。
- `execution_timeout_seconds`：每項任務最長執行時間。

Issue 不能指定任意本機路徑；本機路徑只能來自上述設定檔。

## 開單

1. 在 Private Inbox 使用 `Codex local task` Issue Template。
2. 填寫 Task ID、目標 Repo、Base Branch、讀寫範圍、禁止行為、驗收條件、Host、Lane 與風險。
3. 路徑一律使用 Repo-relative path。
4. 建立後先不要執行，進入 `Awaiting Approval`。

## 核准

從本機取得 Issue body，計算 digest：

```powershell
Get-Content -Raw .\issue-body.md |
  python -c "from github_handoff.core import parse_task,task_digest; import sys; print(task_digest(parse_task(sys.stdin.read())))"
```

授權者確認最終內容後，在 Issue 張貼：

```text
/codex-approve digest=<64字元SHA-256> nonce=<全新一次性nonce> host=<設定的host_id>
```

下列任一情況都會拒絕執行：

- Issue 作者或核准者不在白名單。
- Host、Repo、Base Branch 或 scope 不符。
- 核准早於最後一次 Issue 編輯。
- digest 不符或 nonce 已使用。

Issue 內容變更後必須重新計算 digest 並使用新 nonce 核准。

## 執行

先檢查環境與權限：

```powershell
python -m github_handoff --config C:\secure\receiver-config.json doctor
python -m github_handoff --config C:\secure\receiver-config.json dry-run
```

確認 `dry-run` 只顯示合格任務後，再執行：

```powershell
python -m github_handoff --config C:\secure\receiver-config.json once
```

`once` 會建立獨立 worktree、以 `workspace-write` 啟動 `codex exec`、收集 JSONL、驗證 Result Packet 及寫入範圍，最後將最小摘要回寫 Issue。

## 查詢、取消與復原

查詢本機狀態：

```powershell
python -m github_handoff --config C:\secure\receiver-config.json status
```

- 執行前取消：關閉 Issue 或移除核准，確保下次 poll 不再領取。
- 前景執行中取消：在執行 Receiver 的終端按一般中斷鍵；重新啟動時會將逾時中的任務對帳為 `Blocked`。
- 失敗後：先檢查受限 evidence 目錄與保留的 worktree；若修改 Issue 內容，必須重新核准。
- Worktree 不會自動刪除，確認不需保留變更後再人工移除精確路徑。

## GitHub Issue 可見資訊

Issue 只應保留：

- Task ID、狀態、最後活動時間。
- 執行結果、耗時、Repo-relative changed files。
- Result Packet 的摘要、測試結果、風險與剩餘工作。

原始 JSONL、stdout、stderr、Token、本機絕對路徑及完整詳細日誌不得寫入 GitHub。

## 每次使用後

1. 確認 Issue 顯示 `Completed`、`Failed`、`Blocked` 或 `Cancelled`。
2. 確認沒有第二次修改同一任務。
3. 掃描 Issue、commit 與 PR 是否含秘密或本機路徑。
4. 不再使用的短期 Token 立即撤銷。
5. PR 只建立為 Draft；人工審查後另行決定是否合併。

## 目前限制

- 只驗證 Windows 前景 `once`；macOS 與 Scheduled Task／LaunchAgent 尚未驗證。
- Read scope 是核准與 prompt 邊界；Codex sandbox 仍可讀取隔離 checkout。敏感檔案不應出現在執行 clone。
- 執行中的遠端取消仍以人工中斷及重啟對帳為主。
- 不提供 Dashboard、通用 Queue、對外 Gateway 或自動 Merge。

## 相關文件

- `github_handoff/README_GITHUB_HANDOFF_20260929.md`：技術入口與 CLI 摘要。
- `RUNBOOK_GITHUB_HANDOFF_20260929.md`：維運與故障處理。
- `SECURITY_GITHUB_HANDOFF_20260929.md`：權限與威脅模型。
- `FINAL_REPORT_GITHUB_HANDOFF_20260929.md`：驗收證據與目前狀態。
- Draft PR：[GitHub PR #8](https://github.com/a275618631/codex-antigravity-collaboration/pull/8)。
