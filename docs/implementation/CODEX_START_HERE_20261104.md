# Codex Start Here｜本地多 Agent 協作專案完整執行入口

> 計畫版本：`2026-11-04-v2`。**這是工作規劃，不是已執行證明。**
> 來源：`EXECUTION_PLAN_20261104.md`（完整操作）、`EXECUTION_MANIFEST_20261104.json`（依賴索引）、原 Repo `AGENTS.md`／`PROJECT.yaml`／最新程式與 PR。

## 你的唯一任務

在不重寫現有 B1–B5 的前提下，完成 `W0 → W1 → W2 → W3`，同步完成 `W4_PREP` 與 `W6_DESIGN`，再一次收集外部必要的人工操作，設定備妥後連續完成 `W4_LIVE → W5(E0–E6) → W7`，直到實際符合 `MVP-L=PASS` 或有可核證的外部封鎖。絕不能把 Code/Mock/Readonly CLI/Test PASS 當成整體 E2E PASS。

## 開工第一步（不得跳過）

1. 進入**使用者實際指定**的 B 專案 Windows 工作目錄。只做 `pwd`、`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git remote -v`，核對 `AGENTS.md`、`PROJECT.yaml`、PR #15、#10、`main`。
2. 工作樹有使用者資料或 dirty changes 時，保護原狀，選隔離 worktree；不可執行 `reset --hard`、`clean -fd`、覆寫、搬檔或自動 cherry-pick。規劃分支含 PR #15 程式碼，**不是 main**。若本地沒有 planning branch，可在確認來源後唯讀 fetch，再評估建立新的本地執行 worktree。
3. 從 `EXECUTION_MANIFEST_20261104.json` 解析各工作包的依賴序。`status=NOT_RUN` 全部是真實初值；先重跑 `python -m unittest discover -s tests -v` 取得本機真證據。
4. 缺 CLI 認證、Private Inbox／Runner／secret 時**先做 Stage I 所有可完成工作**，不要中途逐項詢問。最後集中成一個 `USER_ACTION_PACKET`，只列官方入口、動作、風險、回報非機密的狀態。

## 寫入與授權邊界

本任務的 GitHub 分支只承載工作計畫；未經使用者另外核准，不得自動登入帳號、建立 token、註冊 Runner、修改 ACL/IAM、發公開訊息、Push、開/更新 PR、合併 main、刪使用者檔案、部署上線、啟用無人值守或跨 Repo 寫入。即使 `main` 目前未強制 branch protection，使用者的 merge Human Gate 依然有效。

## 每包最小結果

`work_id / actual_git_head / tested_at_utc / source_command / exit_code / pass_fail_counts / evidence_path / verified_evidence_level / next_ready / blocked_dependency / rollback`；原始敏感 log 留本機 restricted evidence root。每一階段結尾更新當次執行摘要，不要覆寫規劃文件當成 runtime 狀態。

## 安全停止

只有越權／疑似洩密／未知副作用／不可驗證寫入／無法保護既有使用者資料時，才把該寫入路徑停成 `SAFETY_STOP`。外部設定沒好標 `BLOCKED_EXTERNAL`，繼續其他工作。新增 scope／discovered work 進可信 Human Gate，不得繞過。

## 工作已完成時的最終判定

- `LOCAL_READY`：Stage I 所有已核准本地工作 + 負向測試通過。
- `MVP-L=PASS`：可信 verifier、私人 Inbox 真實回寫、Codex Lead→Antigravity Worker→Codex Lead→Integration→Parent Goal 全部真正通過；附 E0–E6 log。
- `T7_OS=PASS`：獨立受限 Windows OS 身分／隔離下，真正 kernel DENY sibling/user paths；**不因 MVP-L PASS 自動升級**。
- `PR=REVIEW_READY`：程式、完整證據、去敏紀錄及 Git 整合策略可由使用者審核；沒有 merge。

### 唯一下一步的格式

```text
PLAN_VERSION: 2026-11-04-v2
WORK_BRANCH: <actual branch/sha>
LAST_COMPLETED: <work-id, evidence>
NEXT_READY: <work-id, exact file/command>
LOCAL_READY: PASS | FAIL | NOT_RUN
MVP_L: PASS | BLOCKED_EXTERNAL | FAIL | NOT_RUN
T7_OS: PASS | FAIL | NOT_RUN
UNATTENDED_WRITE: DISABLED
HUMAN_ACTION_PACKET: <one consolidated list or NONE>
PR_STATE: REVIEW_READY | BLOCKED | NOT_STARTED
```

**不可聲稱背景自動執行。** 本文件目的是讓 Codex 接手當次連續工作、停在真正的人類或安全 Gate，不是允許長期無人監督自主擴權。
