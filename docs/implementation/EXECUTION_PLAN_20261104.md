# Codex × Antigravity 協作專案｜單一路徑可執行計畫

> **版本**：Planning v2.0｜2026-11-04（Asia/Taipei）  
> **性質**：供本地 Codex 接手的執行計畫；**不是執行結果**。研究證據來自 GitHub／Drive 唯讀核對；本版本另作為規劃文件發布，不表示已操作 Windows 主機、跑專案測試、建立 Runner／Token／Issue 或修改專案程式碼。  
> **專案**：`codex-antigravity-collaboration`（系統 ID：`local-multi-agent-collaboration`）  
> **Repo**：https://github.com/a275618631/codex-antigravity-collaboration  
> **Drive（CURRENT 唯一人類進度入口）**：https://drive.google.com/file/d/1pnrxGpRQnaXTVQh4QRkEmQl0E_R2JJZC/view  
> **基線**：PR #15 Head `b2488912f32ed4fc45bcfac967f185f871d5ca9f`，Base `8b0534d62529da4aa1b982d73c1df8bfca6a5ff6`。2026-11-04 查核 `main` SHA `dc252fa75aa3851eb1adf503e8e01dc156a482cd`。開始執行時必須重新確認。


## 執行入口｜兩階段、一次完成所有可執行工作

> **給本地 Codex 的最短指令**：讀本 Repo 的 `docs/implementation/CODEX_START_HERE_20261104.md`，照 `EXECUTION_MANIFEST_20261104.json` 的任務依賴序列執行，詳細操作與驗收依本文件 W0–W7。不要以歷史聊天或 Drive 舊 CURRENT 取代本 Repo 的測試、程式碼及最新 Git 狀態。所有工作以當次實測紀錄為準。

### 階段 I｜本地工程做到全綠（先完成，不因外部授權停住）

工作包 `W0 → W1 → W2 → W3 → W4-PREP`，並行完成 `W6-DESIGN`；在隔離、可回復的 **B 專案開發 worktree** 內，完成：

1. 固定當前工作區與 Git 基線，保護既有未提交檔案，依 #15 分支執行單元回歸；有差異才修補，不重寫已完成的 B1–B5。
2. 實作 production verifier（test／acceptance／artifact／可信核准），以原始測試產物及受控 worktree 檢驗來源，新增拒絕與偽造測試；不得把 Agent 的字串當事實。
3. 以現有 `AgentAdapter` 介面，完成 Codex / Antigravity 的薄 CLI 封裝、解析、health、timeout、取消、重啟 reconciliation；沒有 CLI 登入仍先完成 mock/fixture 測試。
4. 準備 Private Inbox 的受限 workflow/config 樣板、最小權限檢查與完整正反向測試腳本；**此時不啟用 Runner／憑證／自動觸發**。
5. 保留 T7 失敗的既有原因，產出低權限身分或 VM 隔離的主機驗證方案，**不修改主機 ACL**。
6. 輸出 `LOCAL_READY` 或附具體 FAIL 的 `LOCAL_BLOCKED`，**不能直接跳成 live verified**。除新出現的真正安全例外，不在每一包做一般性詢問。

### 階段 II｜一次性的人工前置 → 受控 Live UAT → 可審核 PR

先將全部外部設定集中在「一次性人工前置清單」，由使用者在官方 UI／本機安全操作完成且只回報**非機密**狀態：CLI 登入、私有收件匣、專屬 Runner、最低權限、拋棄式測試 Repo 寫入範圍；**未取得授權不得替使用者做這些動作**。

設定就緒後，依 `W4-LIVE → W5(E0…E6) → W7` 連續執行：dry-run、手動 workflow_dispatch、拋棄式 Issue、真正兩個 Runtime 交接、驗收/回寫/去重/恢復、重跑回歸、更新 PR 準備材料，將證據輸出為可審查報告。

**停線規則**：遇到外部憑證／Runner／特定主機隔離未備妥，僅將相依的 live 步驟標 `BLOCKED_EXTERNAL`，其餘已核准工作繼續；若未知副作用／越界寫入／洩密疑慮，該寫入路徑立即 `SAFETY_STOP`。若不符合 `MVP-L` 全部條件，絕不能宣稱完成整套自動接力。完整狀態需可機器判讀。

### 四個禁止偷渡的捷徑

- `Private Repo` 不等於 OS sandbox；工作樹內安全檢查不等於 T7 kernel isolation。
- 既有 93 項測試紀錄不等於這次 93 項測試重跑結果，也不等於真實跨 Runtime PASS。
- `workflow_dispatch` 不是 `issue_comment.created`；本輪預設仍是人工觸發。改成事件自動觸發須另外做 workflow/approval threat review。
- 「Plan 一次核准」只涵蓋 digest 綁定的固定 task graph。超 scope／新增 discovered work／敏感權限仍須按原合約走 Human Gate，不得暗中修改。

## 0. 最重要的決策與執行指令

**本輪目標**：在**使用者監督、單一拋棄式 Repo／工作區、無跨 Repo 寫入、無無人值守執行**的前提下，把已有 B1–B5 控制平面接上 production-grade verifier、可驗證的 Codex／Antigravity 薄 Adapter、可追溯的 Private Inbox／Runner 手動觸發路徑，完成 Parent Goal → Lead → Worker → Lead → Integration → AC 的真實受控 E2E；整理成可審核的 PR。**若外部權限尚未備妥，依序完成所有本地可交付工作，並將 live gate 明確標為 BLOCKED，不虛報完成。**

**不要重寫 B1–B5**。PR #15 已實作並記錄 2026-11-02 `93 passed`（此為 Repo/PR 紀錄，非本次重新執行）；優先針對缺口增加 production verifier／adapter／真實整合。不要把 `PR #15` 的 93 與 Drive 舊資料的 `115 passed / 4 failed / 1 skipped` 相加或互相取代。

**本輪定義兩個不同完成線**：

- **MVP-L（受控 Live）PASS**：單一拋棄式 Repo，人工啟動／可觀測，完成完整跨 Runtime Parent Goal E2E、可信 verifier、GitHub Issue 回寫與 fail-closed 負向案例；不包含無人值守與跨 Repo 寫入。未取得必要登入或私有 Inbox 授權時維持 `MVP-L=BLOCKED`，本地里程碑可先完成。
- **UAT-U（無人值守／跨 Repo 寫入）**：**不是本輪基本完成條件**；獨立依賴 T7 真正 OS 強制隔離、Runner 執行身分及 host policy，未通過一律 `UNATTENDED_WRITE=DISABLED`。本輪可以設計與測試隔離 PoC，但**不得自行修改主機 ACL／Security Policy**。

**完整工程執行總順序**：`W0 現況與分支鎖定 → W1 B1–B5 回歸／差異 → W2 production verifiers → W3 CLI Adapters → W4 私有 Inbox/Runner 準備 → W5 分級 live E2E → W6 T7 獨立決策／實測（需另行核准） → W7 文件、狀態對齊、PR 可審核收尾`。其中 W1–W3 與 W4 的設定檔／測試部分不必等待外部權限。

**切勿自動執行**：push、merge、production deploy、任何 production 資料變更、變更 ACL／IAM、帳號登入／憑證建立或輸出、對外發訊、在主機安裝/啟動 background service、跨 Repo 寫入、刪除或清理使用者資料。這些要另行具名核准。計畫獲准執行本地程式碼也**不代表**獲准做以上行為。

## 1. 範圍判定（必要／條件式／未來）

| 分類 | 元件或能力 | 本輪判斷與依據 |
|---|---|---|
| 必要 | B1–B5 regression、Parent/Task digest、scope、Result v2、去重／重啟／Human Gate | PR #15 已有實作，先重驗與針對缺口修補，禁止從零重做 |
| 必要 | Production `evidence_verifier`、`artifact_verifier`、可信核准來源 | `control_plane/orchestrator.py` 明確提供 callbacks，未配置會 fail-closed；沒有它們無法達成真實 PASS |
| 必要 | Codex/Antigravity 真實 CLI Adapter 與分級 E2E | 現有 `PassiveAdapter` 健康狀態是 unavailable；歷史 nonce 不是完整 Goal chain |
| 必要 | 私有 Inbox 的可重現手動觸發與 Result 回寫 | GitHub Issues 是選定 ledger；目前 `.github/workflow-templates/local-codex-handoff.yml` 只是**範本**，且僅 `workflow_dispatch` |
| 必要 | 全套負向測試／redaction／中斷和恢復／PR review | 防止錯誤 PASS、越界寫入及不安全重派 |
| 條件式 | 真實 Private Inbox repo、Runner、process-scoped token、Antigravity 登入 | 真正跑 live 前的使用者安全設定；Codex 只能準備檔案、檢查狀態，不得代取憑證 |
| 條件式 | 單一拋棄式 Repo 的受控寫入 E2E | 只在明確核准與隔離測試資料的狀態下執行；未通過不得標 Live PASS |
| 獨立安全 gate | T7 OS 強制隔離 | 對**無人值守及跨 Repo 寫入**必要；不以應用層 scope 檢查、私有 Repo 或 Git worktree 取代 |
| 未來 | Desktop MCP mailbox | GitHub Issue 不是其依賴；若日後要 Desktop MCP UX 再獨立驗收 |
| 未來 | Privacy local/cloud routing、local-model lane、multi-host | README 明載 Planned／Experimental／Exploratory；不阻擋單主機 MVP |
| 未來 | Broker／自製排程／Dashboard／DB／System One | 違反最小化架構；只有現有 GitHub/CLI 無法滿足明確量化需求才重啟評估 |

### 實務上的「一次核准」邊界

一般子工作在**核准的 repo/base/write-set／Task Graph**內可自動接續；**新增 discovered task 目前仍須可信核准且會 re-digest**（PR #15 程式即如此）。因此不能聲稱「任何新增工作都零人介入」。可先執行不增大範圍的既有任務；若新增任務造成 `PENDING_REVIEW`，只有它和相關依賴停下。這是設計上的 Human Gate，不應被規避。

## 2. 現況與可信度對照（2026-11-04 唯讀）

**證據標籤**：`V1=官方／專案文件聲明`；`V2=讀到實際 GitHub code、PR metadata、commit 或設計明確的測試內容`；`V3=實際在目標 host Clone/Install/Run/Test`。本次最高 V2，**沒有新的 V3**。

| 項目 | 本次狀態 | 查核依據／日期 | 證據 |
|---|---|---|---|
| Stable identity | Confirmed | `PROJECT.yaml` 指定 repo 與 Drive Folder ID `1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s` | V2 |
| B1–B5 | Implemented but unmerged | PR #15，Head `b2488912...`，2026-11-02 記錄 `93 passed`；**本次未執行** | V2 code + V1 test claim |
| PR #15 | Open / Draft / unmerged | 2026-11-04 GitHub PR readback；Base 是 PR #10 的分支，**不是 main** | V2 |
| PR #10 | Open / unmerged | Head `8b0534d...`；是 #15 的依賴 | V2 |
| PR #8 | Open / Draft | GitHub Local Handoff 老分支；須防止與 #15 複製重疊程式 | V2 |
| PR #12 | Open / unmerged | 狀態／SOT 變更須檢查是否與 #15 文件衝突 | V2 |
| PR #13 | **Merged** | 2026-11-02 已合併；10/30 Drive 當時說 Open 已過期 | V2 |
| `main` | SHA 已不同於舊交接 | 2026-11-04 `dc252fa75aa3851eb1adf503e8e01dc156a482cd` | V2 |
| Production evidence/artifact verifier | Unconfigured | `ControlPlane(..., evidence_verifier=None, artifact_verifier=None)`，均 fail-closed | V2 |
| Codex/Antigravity active Adapter | Unverified / Partial | `PassiveAdapter` 的 `submit()` 直接丟出例外；外部 runtime transport 尚未接好 | V2 |
| 真實 Antigravity 受限 nonce | Historical bounded CLI PASS | 2026-10-22、10-28 Log；非本次重測，也非 Parent 全流程 | V1/V2 紀錄，非新 V3 |
| Private Inbox/Runner | Unconfigured | Drive CURRENT、PR #15 均標未配置；範本限手動 dispatch | V1/V2 |
| T7 OS write isolation | **FAIL（歷史實測）** | 2026-10-20 Windows ACL 套用後，主機策略重設 Modify，受限身分仍可寫 sibling repo；當次已回復 | V2 檢閱紀錄；非當下 V3 |
| Drive CURRENT 舊測試 | CONFLICT / UNVERIFIED | `115/4/1` 無可對應的 checkout/原始 logs；2026-10-30 文件含互相矛盾的 E2E 標記 | V1，不能升格 |
| 主機當前狀態 | UNVERIFIED | 無法讀取使用者 Windows 工作目錄、登入或 Runner service | 無 |

**關鍵矛盾處理**：Drive 10/30 CURRENT 的「部分 live E2E PASS」、「未提交的 115/4/1」均保留為歷史宣稱；最新 PR #15 的工程基線採用該 Head，並清楚區分 mock、CLI nonce、完整 GitHub Inbox E2E、完整 Parent E2E、OS 隔離。先完成 `W0` 當日 host 檢查，才可更新「今天實際狀態」。GitHub `main` 由 API 顯示 `protected=false`，**這不代表使用者授權 merge**；仍一律 Human Gate，另核對是否有 ruleset。

## 3. 依賴有序工作包（Codex 的實作指示）

### W0｜基線固定、保護已有資料、判斷實際差異

- **Owner**：Codex；不需額外帳號。**前置**：開啟指定本機目錄；尚未獲准寫入前唯讀。
- **入口**：`C:\Users\Y6T2\Documents\New project\codex-antigravity-integration-20261030`（交接提供的 11/04 路徑；**不能假設**與舊 T7 測試的 `Documents\Tech Review\...` 是同一目錄）。
- **步驟**：讀 `AGENTS.md` → `README.md` → `README.zh-TW.md` → `PROJECT.yaml` → `docs/DEVELOPMENT_ALIGNMENT_20261030.md`；執行唯讀 `git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git remote -v`、`git log -1`；比對 #15/#10/#8/#12/#13，確認 main 進度與目前工作樹是否乾淨。不得清理 portable worktree 或任何未提交使用者檔案。
- **DoD**：固定 `repo/branch/base/head/dirty paths/PR dependencies`，產出一次性的本輪 `evidence/baseline-YYYYMMDD/` 本地證據；若 Host 與來源不一致，以 `CONFLICT` 列差異，先在**獨立可回復工作區**處理，不覆蓋。
- **失敗／回復**：缺本機目錄或未提交工作無法界定時，只做唯讀盤點並停止該路徑的寫入；其他離線設計／測試準備仍可進行。

### W1｜B1–B5 回歸與 PR 依賴核對（不重寫）

- **Owner**：Codex。**前置**：W0 基線可辨識。**涉及**：`control_plane/orchestrator.py`、`control_plane/result.schema.json`、`github_handoff/result.schema.json`、`tests/test_control_plane.py`、`tests/test_github_handoff*.py`。
- **步驟**：先跑來源已有的 `python -m unittest discover -s tests -v`；執行 `git diff --check`（來源中已有紀錄，非本次實測）；比較 93 cases 是否可重現。分別確認：B1 approval digest/write-set、B2 v1 不得自證 PASS、B3 原子 ingest/同 ID 不同 digest 拒絕、B4 Parent integration/evidence gate、B5 crash reconciliation。讀 PR #15 P1/P2 修補，不得重導入被修掉的缺陷。
- **DoD**：可重現且記錄 `Python version / OS / HEAD / pass/fail/skip / raw test log`；任何失敗都分類 `regression / environment / stale report`；不能拿 Drive 舊 115/4/1 充當現況。若 93 無法重現，保留原輸出與 `UNVERIFIED`。
- **失敗／回復**：測試不通則在獨立 worktree 修復最小差異；禁止無證據大規模重構。若 PR #10 或其他 PR 已改，重新檢查依賴且不得直接自動 rebase/force-push。

### W2｜Production evidence／artifact／approval verifiers（本輪最重要）

- **Owner**：Codex；使用者只需事先核准**可用的可信證據根與環境**，不是提供憑證值。**前置**：W1；不依賴 Runner 已上線。
- **既有介面**：`ControlPlane(state_file, policy=..., repo_root=..., evidence_verifier=..., approval_verifier=..., artifact_verifier=...)`；`_verify_evidence()` 接收 `kind,name,evidence_ref,goal_id,repo,base_sha,approved_plan_digest,task_id,task_digest,attempt_id,result`；`_verify_artifacts()` 接收 `repo_root,base_sha,write_scope,reported_changed_paths,result` 等。此為已在 source 讀到的 callback **Boolean API**，不是憑空設計的服務端點。
- **實作**：新增最小 verifier 模組（**建議位置** `control_plane/verifiers.py`，最終依既有風格決定），並新增不依賴任何正式 token 的 fixture tests（**建議** `tests/test_production_verifiers.py`）。每筆 evidence-ref 僅能指向受控 evidence root／可信 GitHub run/artifact/commit 來源，驗證 owner、kind、digest、attempt、完成狀態、hash、時間／版本／大小上限，拒絕 `..`、絕對路徑、UNC、symlink/junction、替換後檔案與未知 schema。任何 callback 出錯/失聯/資料不完整 → False；**不得接受 Agent 自稱的 PASS 或自己寫的「測試成功」字串**。
- **驗證類型**：① unit/integration test 只信任實際 subprocess 結束碼、原始 framework report 與受控 runner 紀錄；② acceptance criteria 必須對應明確 criterion_id、相同 plan+attempt、真正驗證器產生的證據；③ write artifact 以可信 `git status/diff` 與 path resolve 比對**實際**追蹤及未追蹤檔案，不能只信 result 的 `artifacts_changed`，也檢查 base SHA、write-set 與無越界路徑；④ integration 的 evidence 必須由同一 integration attempt 回寫；⑤ GitHub delivery/writeback 必須以實際 API 成功與讀回／idempotency 證據為準。
- **建議結果紀錄（新建，非現有 API）**：`{verifier_id, version, kind, evidence_ref, trusted_source, repo, base_sha, goal_id, task_id, attempt_id, plan_digest, checked_at, PASS|FAIL|UNVERIFIED, reason, sha256}`，寫入 restricted local evidence root；adapter 只收 callback `True/False`。若需要通用檔案型態或 GitHub provenance API，先以 fixtures 定介面，實際 CLI 版本／權限檢查後再填值（TBD）。
- **DoD**：正向可檢驗、篡改/偽造/缺失/錯 attempt/錯 SHA/redirected path/未知來源等一律拒絕。包含 `artifact_verifier=None` 的 write fail-closed、`evidence_verifier=None` 的 AC 不完成、`approval_verifier=None` 的 discovered work 不放行。
- **失敗／回復**：整個驗證器以 feature gate 預設關閉，不能把 mock verifier 設成 production。驗證失敗保持 BLOCKED，保留原證據供人工審查；不得用 `acceptance_passed=true` 強制通過。

### W3｜CLI 薄 Adapter 與可靠性測試

- **Owner**：Codex。**前置**：W2 contract 及 W0 的本機 CLI 健康檢查；無登入可先寫 mock-backed adapter tests。
- **既有合約**：`control_plane/orchestrator.py` 中 `AgentAdapter` 六方法：`health/capabilities/submit/status/cancel/collect_result`；`PassiveAdapter` 尚不能提交任務。
- **實作**：在 `control_plane/` 或現有 `integrations/` 下建立**薄、可替換**的 Codex／Antigravity adapter。禁止建新的 server、queue、DB。用 argv array＋受限工作目錄＋stdin，無 shell 拼接；exec process 不承接 Receiver token；記錄 process ID/external ID、deadline、exit code、可信 stdout/JSON、stderr 去敏、cancellation ack、不確定狀態。Non-interactive prompt 不可使用會跳過所有工具權限的參數。
- **已核對官方 Antigravity 介面**：`agy -p`、`--output-format json|stream-json`、`--print-timeout`、`--json-schema`、stdin streaming；CLI 憑證需由**使用者在相應主機**完成正式登入，並在本機驗證版本。文檔：https://antigravity.google/docs/cli/headless/ 。Codex CLI 依既有 README 與官方 noninteractive 文件實作；當日先用 `--help`/版本輸出核對可用旗標，不假設舊版完全相容。
- **分級驗證**：先唯讀 nonce，再唯讀小任務；再在使用者核准的拋棄式 repo 進行單 Repo 寫入；最後做 Lead→Worker→Lead。每級要求 runtime 身分、request+result ID、exit/status、耗時、證據鏈；任何 auth failure、truncated JSON、timeout、未知 side effect 都不得成功。
- **DoD**：六方法行為與負向 cases 重現，回傳 v2 Result Packet，所有身份由可信 transport bind；cancel 只有外部確認 terminal 才能完成，unknown 進 `NEEDS_RECONCILIATION`。
- **失敗／回復**：失敗時禁自動重派未知執行；不刪原產物。模型/CLI 未登入時只有 Adapter live 停止，W1/W2 本地工作不阻塞。

### W4｜Private Inbox／Actions／Runner：準備與安全啟用

- **Owner**：Codex 準備配置／測試碼；**使用者**完成 GitHub UI／Host 安全設定。**前置**：W2、W3 基礎完成；設定私有 Inbox 與 token 的動作必須獨立核准。
- **已存在檔案**：`github_handoff/config.example.json`、`github_handoff/core.py`、`github_handoff/cli.py`、`github_handoff/result.schema.json`、`RUNBOOK_GITHUB_HANDOFF_20260929.md`、`SECURITY_GITHUB_HANDOFF_20260929.md`、`.github/workflow-templates/local-codex-handoff.yml`。**注意範本不是 `.github/workflows/` 已啟用工作流。**
- **可信觸發選型**：MVP 優先使用**私人 Inbox 上已核准者手動 `workflow_dispatch`**。目前範本僅手動觸發，絕不宣稱 Issue comment 自動觸發已實作；若要改為 `issue_comment.created`，須另外設計 actor、workflow trust、防惡意 payload／任意 runner code 執行的審查 Gate，**不屬本輪預設**。
- **步驟（Codex）**：從範本準備**只在專用 private inbox**使用的 workflow、`GH_HANDOFF_CONFIG` 指向本機受限 config 的 runner environment 變數、限定 runner labels `self-hosted/windows/codex-handoff`、細限 `permissions: contents: read; issues: read`；receiver 所需的 Issues 回寫權限由**獨立最小權限認證**提供，不能誤以為 workflow 的 `issues: read` 可寫回。若實際部署需要 workflow `issues: write`，須審查是否必要，不要預設擴權。強制限定 actor/approver/repo/host/read-write scope、Issue body hash、approval nonce、事件時間晚於最後編輯、已用 nonce 拒絕重用；`issue-link`、`doctor`、`dry-run`、`once` 驗證按次執行。
- **人工設定**：參照第 4 節一次性清單；Runner 僅綁 private inbox，使用專屬非管理者執行身分。不可將私有 repo 視為 sandbox；不讓任意公開 PR 或未驗證 Issue 文字成為執行指令。Runner 未有 OS 寫入隔離前，只能**人工監督的受限 dry-run/readonly/synthetic E2E**，不可開放背景任意寫入。
- **DoD**：Runner 真實 online、private inbox/指定環境/labels 匹配、doctor 顯示每項細部狀態、dry-run 無執行副作用、人工核准後可執行 synthetic single Issue 並可正確寫回/讀回；token 不在 Issue、輸出、Git、Drive 或模型 prompt。
- **失敗／回復**：Runner 改 offline／停用 workflow；撤銷獨立 PAT/憑證（使用者操作）；保留原始 issue/audit；只刪測試專用資產且需使用者另行確認。

### W5｜真實受控 E2E 分級驗收（Critical Path）

- **Owner**：Codex 主導；使用者核准 private inbox／synthetic E2E；外部 Antigravity 登入由使用者完成。**前置**：W2/W3 PASS、W4 的必要權限備妥。
- **E0 preflight**：記 `Windows/CLI/Git/Python` 版本、登入狀態（只記成功/失敗，不讀 credential）、Repo/base SHA/worktree clean、deadline、單 writer、evidence root 安全權限。
- **E1 read-only nonce**：獨立暫存工作目錄；核對 nonce、exit=0、CLI 結果結構與去敏 log；timeout 一律不算 PASS。
- **E2 read-only task**：Lead 發真正小任務給另一 Runtime，回傳 v2 packet；證據來自 runtime 實際結果，不能是測試夾具。
- **E3 disposable single-repo write**：只有在明確人工核准與隔離 disposable 路徑後，測新增一個指定檔案；repo write-set 外一律拒絕；無 permission bypass，工作樹、diff、hash 均核對。此為**受監督**寫入，不代表 T7。
- **E4 Lead→Worker→Lead**：Codex Lead 執行 A、Antigravity Worker 執行 B、Codex 自動接收 Result Packet 並在同一批准範圍繼續 C；禁止使用者手動複製結果。
- **E5 Parent Goal**：建立 Parent/required tasks/integration criterion，完成後必須有 evidence verifier PASS、artifact verifier PASS、integration same-attempt PASS、所有 required tasks、Parent AC PASS、無 unresolved，並完成 GitHub Issue 狀態回寫與 readback。重送相同 delivery no-op；不同 digest 拒絕。
- **E6 failure series**：驗證 timeout/cancel、restart、malformed packet、missing verifier、misbound attempt、scope escape、approval stale／nonce reuse、redaction。任何未知副作用 → reconciliation，不盲目重派。
- **DoD**：E0–E6 各有 timestamp、versions、repo/commit SHA、goal/task/attempt/delivery/digests、測試狀態、脫敏 log、GitHub Issue/run URL、reject reasons。只有**完整 E0–E6 與 Parent 真實終態**才能標 `MVP-L=PASS`。
- **失敗／回復**：以最小單次嘗試重跑具體失敗案例；未知寫入、身分錯誤、scope 違反立即停寫，保留現場由人審查。

### W6｜T7 OS 隔離：獨立必備條件（本輪不自動變更 ACL）

- **Owner**：Codex 提供唯讀盤點、方案與測試；主機安全設定由使用者／管理者核准與執行。**前置**：W0 真正主機路徑／runtime 身分確認；不要複用 10/20 舊路徑當成現在有效。
- **已有失敗資訊**：`WINDOWS_ACL_IMPACT_MIN_CHANGE_PLAN_20261020.md` 記載 10/20 試改父層 ACL，主機策略重施 `CodexSandboxUsers Modify`，受限 `codexsandboxoffline` 仍成功寫入 sibling repo；且完整 ACL `/restore` 有 Windows 1300 限制。**不推薦直接重試相同 icacls 腳本**。
- **方案比較**：A. 改相同父層 DACL（最少設備，但已知會被 host policy 覆蓋，**不推薦**）；B. 獨立 Windows 低權限 OS identity＋僅掛載單一 disposable repo 的 ACL 隔離（先查 host policy 相容，**最低變更候選**）；C. 隔離 VM／容器與只有必要工作目錄的 host mount（隔離較明確、維護較多，若 B 無法生效則優先）。無論 B/C，**都須原生 OS 拒絕證據**，不可拿 prompt、scope preflight、Git diff 或 private repo 代替。
- **測試矩陣**：ALLOW 對核准 worktree 的唯一暫存檔可寫；DENY sibling repo、其它 user files、`..`、絕對路徑、drive letter、UNC、junction、symlink／reparse point、子程序繼承權限、path case 變化；用真實受限身份呼叫原生檔案寫入，要求 `ERROR_ACCESS_DENIED (0x5)`／相符原生拒絕；確認無殘留、Git 乾淨，並保留 ACL before/after、whoami/groups、hash、回復演練。
- **DoD**：只在「寫入核准路徑 ALLOW + 全部越界 DENY + 變更持久性 + 可回復 + 受限身份一致」都 PASS 後，才提案解鎖 `UNATTENDED_WRITE`；是否開啟仍需獨立人工作業授權。
- **失敗／回復**：重施廣泛 Modify、意外可寫、OS 權限來源不明或 rollback 不可用，立即 `T7=FAIL`，停止相關程序並依事先驗證的備份回復；不得靠無法成功的 `/restore` 宣稱已復原。

### W7｜完整驗收、PR 整理與唯一進度對齊

- **Owner**：Codex 準備內容；使用者審核 Push／PR 更新／Drive 更新／Merge。**前置**：W1–W5 有已驗證結果或明確 Blocked，W6 有獨立狀態。
- **步驟**：重跑適當測試、`git diff --check`、敏感字串與 scope audit；確認 PR #10 仍未合併、#15 Base 不是 main、新版 main 已包含 #13。提出**最小安全整合順序／PR base 調整方案**，不偷偷 force push、rebase、cherry-pick、merge。將 PR #15 描述改為 `Implemented` / `Unit-mock verified` / `CLI bounded` / `Live inbox verified` / `Parent E2E verified` / `T7`，附 commit、run URL、log hash、可重現測試、風險與 rollback。到**PR 已備妥可審核**止。
- **Drive CURRENT 唯一更新方案**（**取得使用者明確核准後才寫**）：保留原檔 ID，更新最後查核時間、Repo/PR/HEAD、分層證據矩陣、今日 pass/fail/blocked、T7、下一個 Human Gate、來源 URL／commit；舊 `115/4/1` 放到 historical/conflict 不可覆寫成新 PASS。不要另開第二份 CURRENT/backlog/SOT。
- **DoD**：所有聲稱均可追到來源與執行時版本；PR 可審核但**不自動合併**。若外部 gate 不能通過，交付範圍明確的 `Local packages complete / Live blocked`，不說整套已完成。
- **失敗／回復**：PR 衝突保留 diff 與人工決策；Drive 未授權維持原樣並在交付報告列出建議修改欄位。

## 4. 一次性人工前置清單（不需要回傳任何秘密）

> 這是**後續要實際執行 W4/W5 時**使用者需做的操作，不是本次規劃已完成項目。只需回報「已完成／尚未」以及非敏感的 repo、runner 名稱、狀態或 URL；**絕對不要貼 token、cookie、認證碼或設定檔私密內容**。

1. **一次確認本輪授權**：同意本地 Codex 只在指定 B 專案獨立 branch/worktree 修改與測試；是否同意建立合成資料的 disposable repo、測試 Issue/Comment，以及日後由你按下 Push／PR 更新，逐項清楚區分。未授權的對外寫入不執行。
2. **Antigravity／Codex CLI 登入**：在目標 Windows 主機內以官方流程登入、核對當日 `agy`／`codex` 的版本與權限；回報 `auth ok/not ok` 即可。Runner 不得把個人登入資料暴露給 model。
3. **Private operational inbox**：在 GitHub UI 建立一個專用**Private** repo，禁止讓 public PR 執行 workflow；決定 Inbox 名稱與實際只允許的 actor/approver、目標測試 repo，回報 repo URL。**建立 repo 是對外資源變更，須先核准。**
4. **Self-hosted runner**：在上述 private repo 的 `Settings → Actions → Runners` 註冊**專用** Windows Runner；限定 private repo、非系統管理員的帳號／工作目錄和 `codex-handoff` label；回報 runner 顯示 `Idle/Online`、label 與綁定 repo。註冊 token 依 UI 處理，不貼聊天。官方：https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners 。**不要把自動啟動 service 預設視為已核准。**
5. **最小權限與外部 config**：在受限本機權限下建立 `github_handoff/config.example.json` 的外部 copy；只在安全的程序環境注入獨立最低權限 token，設 `allowed_task_actors`、`allowed_approvers`、`allowed_repos`、host/worktree/scope，及 private runner environment 的 `GH_HANDOFF_CONFIG` **檔案路徑**。回報「已配置」與無機密的允許範圍摘要即可。Github workflow 的 `GITHUB_TOKEN` 和 receiver token 權限要個別核對。
6. **T7／寫入 gate 分開決策**：若只做**人工監督的 single-repo synthetic E2E**，明確授權它的測試範圍與停止條件即可；若未來要無人值守／跨 Repo 寫入，需另行核准專用 OS identity/VM 或 ACL 改動與 rollback。不要默認啟用。
7. **PR／Drive 更新**：完成後再由你確認是否可 Push、更新 PR #15、更新**原 Drive CURRENT**；protected/main 的 Merge 永遠最後單獨核准。

## 5. 最終 E2E 驗收矩陣（不得把 Mock 等同 Live）

| ID | 類型 | 驗收動作／條件 | PASS 規則 | 證據與失敗分級 |
|---|---|---|---|---|
| T01 | unit/mock | B1 plan 未核准、digest 改變 | `next_task()` 不啟動、Human Gate | `tests/test_control_plane.py` raw log；LOCAL |
| T02 | unit/mock | 空 write-set 宣稱 write、policy 缺失／DENY | 拒絕且無檔案變動 | LOCAL |
| T03 | unit/mock | v1/legacy 自稱 PASS | 轉換成 UNVERIFIED、Parent 不完成 | schema fixtures；LOCAL |
| T04 | unit/mock | v2 身分/attempt/delivery/plan digest 不匹配 | 無副作用，拒絕 ingest | LOCAL |
| T05 | unit/mock | 同 delivery+digest 重送 | 不重做、不重寫、不重送 | LOCAL |
| T06 | unit/mock | 相同 delivery ID、不同 digest | 拒絕，狀態不壞 | LOCAL |
| T07 | unit/mock | 新工作一筆合格一筆非法、環狀依賴 | 全批不入庫 | LOCAL |
| T08 | unit/mock | 新工作需 plan revision/approval | `PENDING_REVIEW`，可信核准重算 digest | LOCAL |
| T09 | unit/mock | verified tests/AC 缺失或冒造 | Parent 不 COMPLETED | LOCAL+Verifier |
| T10 | unit/mock | 多 writer 寫同一路徑 | 互斥排程/序列化 | LOCAL |
| T11 | unit/mock | cancel 未收到 runtime terminal ack | `CANCEL_REQUESTED` 或 `NEEDS_RECONCILIATION` | LOCAL |
| T12 | unit/mock | crash：submit 前/後、collect 前/後、重啟 | 重建一致狀態，不盲目重跑未知 side effect | LOCAL |
| T13 | verifier | 測試 report/evidence 被替換、錯 attempt/base | verifier=False、完成 gate 保持關閉 | VERIFIED ARTIFACT |
| T14 | verifier | `artifact_verifier=None` 且回報寫入成功 | Fail closed | VERIFIED ARTIFACT |
| T15 | verifier | git 真實 diff 含超 write-set、junction/symlink | 拒絕 | VERIFIED ARTIFACT |
| T16 | GitHub real | Private Inbox actor／edit time／approval digest／nonce | 完全符合才 `Queued`；未核准只 Pending | GITHUB LIVE run/Issue |
| T17 | GitHub real | `doctor` → `dry-run` → 手動 `workflow_dispatch` → `once` | 正確單次派工與去敏進度回寫／readback | GITHUB LIVE |
| T18 | GitHub real | 重送、取消、惡意 Issue、偽造 label／actor | 不重跑、不擴權、不顯示 secret | GITHUB LIVE |
| T19 | Runtime real | Antigravity CLI 唯讀 nonce | 真 CLI、正確 nonce／status/exit、無檔案變動 | BOUNDED CLI ONLY |
| T20 | Runtime real | read-only Task Packet → v2 Result | 真實 Adapter/身份/可核證 log | RUNTIME LIVE READ |
| T21 | Runtime real | 單 Repo disposable write | 受控確切檔案、實際 diff、verifier PASS | RUNTIME LIVE WRITE，不解除 T7 |
| T22 | Runtime real | Codex A → Antigravity B → Codex C | 無人工複製，Lead 真正 resume | RUNTIME LIVE E2E |
| T23 | Runtime real | integration 完成且 Parent AC 同 attempt VERIFIED_PASS | Parent 才 COMPLETED 且 Issue 成功回寫 | PARENT LIVE E2E |
| T24 | OS kernel | 受限身分越界寫 sibling repo／UNC／junction 等 | 原生 ACCESS_DENIED，核准範圍允許，持久且可回復 | T7 OS；獨立 gate |
| T25 | 文件/PR | source/date/SHA/測試結論對齊 | PR 可審核；Drive 只在獲准後更新 | REVIEW READY |

**Evidence 目錄（建議；非現有路徑）**：`evidence/<run-id>/manifest.json`、`preflight.json`、`test-report.txt`、`result-v2.json`、`verifier-audit.json`、`git-diff-summary.json`、`github-writeback.json`、`reconciliation.json`、`t7-os-probe.json`；敏感 log 存受限本機，不把原始 secret、完整 user home path 或 personal data 上傳 repo/Issue。公開 Repo 僅提供去敏摘要與 hash。

**狀態嚴格分層**：`UNIT_MOCK_PASS`、`BOUNDED_CLI_PASS`、`PRIVATE_INBOX_LIVE_PASS`、`CROSS_RUNTIME_PARENT_E2E_PASS`、`T7_OS_PASS`；每個狀態需有實際 run_id + commit + timestamp，不可推論升級。

## 6. 缺口、選項與預設決策

| 問題 | 建議（本輪預設） | 替代與影響 |
|---|---|---|
| PR #15 Base 是未合併 PR #10 | **先驗證 PR 依賴，整合順序留到可審 PR 時交人判定** | 直接改 Base 到 main 可能帶入遺失或衝突，禁止未檢查自動 rebase |
| GitHub 事件觸發不在現有範本 | **手動 `workflow_dispatch` 為 MVP-L** | 追加 `issue_comment` 自動事件需獨立 workflow-security review；不默默放進這輪 |
| Production verifier 哪個來源可信 | **主機受限 process 的原始測試輸出 + git 實際 diff + verified run/commit provenance** | 只憑 model Result Packet = 無法保證；不得採用 |
| Antigravity CLI 工具權限版本差異 | **現場 health/--help/官方文件核對，再作最小薄 adapter** | 不假定實際登入或 flag 仍與歷史紀錄一致 |
| T7 ACL 修復方案 | **先查 host security policy，再評估獨立受限身分；失敗用 VM 只掛單一 repo** | 重跑 10/20 父層 `icacls` 已知無法持久成立 |
| Writeback 與 Parent COMPLETE 原子性 | **把 GitHub 回寫 readback 納入 Final DoD，不用單一 local state 宣稱已交付** | 若沒有跨系統交易，失敗時應進 REPORTING/NEEDS_RECONCILIATION，而非假 COMPLETED；需要先核對現有狀態機能否表示，不能直接杜撰已支援 |
| `main` branch protection / ruleset | **無論 GitHub 技術上 protected 與否，使用者核准仍必要** | API branch `protected=false` 不能證明無 ruleset，也不能代替業務授權 |
| Drive 舊報告互斥 | **舊版 archive/historical、當輪附完整 SHA/run_id** | 不可修改歷史文字冒充當日重新跑過 |

## 7. 可連續執行與真正中斷條件

**應連續做完、不需每步再問**：同已核准工作區的 repo 靜態研究、fixture／unit test、verifier/adapter 本地程式碼實作、非機密 mock、read-only probe、失敗診斷、去敏證據整理。由執行者先按 W0→W3→W4 準備，不因人工作業未做就停止全部工作。

**必須立即 Human Gate / STOP**：1) 要求取得、複製或輸出任何憑證；2) 登入／外部權限改動或新建私有 repo/runner；3) 對外 Issue/PR/Drive 寫入及 push；4) 修改 ACL/主機安全策略；5) 單 Repo 寫入 PoC 尚未授權；6) scope/base/plan 變更或新 discovered task 需要重核准；7) 任意跨 Repo/無人值守寫入；8) merge／deploy／刪除資料；9) 可信身份或 OS 實際越界、失敗後無法回復、unknown runtime side effect；10) acceptance 無法由可信證據判斷。

**Human Gate 回報格式**：`阻擋工作包 ID / 原因 / 已完成的可獨立工作 / 需要使用者做的唯一動作 / 操作 UI 入口 / 回覆只含非敏感結果 / 可安全恢復點`。所有外部前置項一次集中提供，避免做到一半才問。

## 8. Codex 接手時可一次貼上的執行任務（安全邊界仍有效）

> 依本文件 W0→W7 按依賴執行。先唯讀確認本機目前 branch、HEAD、dirty worktree、PR #15 依賴與官方 runtime 版本；保護所有未提交資料。B1–B5 已實作，先重驗 93 cases，針對真正缺口完成 production verifiers、可信 artifact provenance、CLI 薄 Adapter、所有負向測試與受監督 single-repo E2E。能本地完成的工作持續做到可驗收，不等外部帳號。遇 runner/Private Inbox/登入/權限/ACL/外部寫入/Push/Merge/Drive 必須停在人工作業 gate，整理一次性前置清單，不要索取任何 secret。請以實際 commit、run_id、去敏 raw log、test summary、issue/run URL 支持每個 PASS。最後只到 PR #15 及相依 PR 可審核的狀態，不合併 main，不建立第二份 CURRENT 或自製 Agent 框架。若 live gate 缺權限，明確交付「本地模組完成、Live blocked」，不可用 mock 冒充。

## 9. 來源、查核日期與保留邊界

**GitHub（2026-11-04 唯讀）**：

- Repo/README：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/README.md
- PR #15：https://github.com/a275618631/codex-antigravity-collaboration/pull/15
- PR #10：https://github.com/a275618631/codex-antigravity-collaboration/pull/10
- PR #8：https://github.com/a275618631/codex-antigravity-collaboration/pull/8
- PR #12：https://github.com/a275618631/codex-antigravity-collaboration/pull/12
- PR #13：https://github.com/a275618631/codex-antigravity-collaboration/pull/13
- Control plane source：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/control_plane/orchestrator.py
- Control plane v2 schema：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/control_plane/result.schema.json
- Workflow template：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/.github/workflow-templates/local-codex-handoff.yml
- GitHub Handoff security：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/SECURITY_GITHUB_HANDOFF_20260929.md
- Windows T7 ACL report：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/WINDOWS_ACL_IMPACT_MIN_CHANGE_PLAN_20261020.md
- Live nonce history：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/LIVE_HANDOFF_EVIDENCE_20261020.md
- Engineering alignment：https://github.com/a275618631/codex-antigravity-collaboration/blob/codex/control-plane-alignment-20261030/docs/DEVELOPMENT_ALIGNMENT_20261030.md

**Drive（2026-11-04 唯讀）**：

- CURRENT（最後修改 2026-10-30）：https://drive.google.com/file/d/1pnrxGpRQnaXTVQh4QRkEmQl0E_R2JJZC/view
- 2026-10-30 設計與交接：https://docs.google.com/document/d/1vMTLbeRmlv2-YXn_4b1M6akg9VY1nG_gLCtDIfCiH2I/edit
- 2026-10-15 LOCAL MASTER TASK（歷史需求）：https://docs.google.com/document/d/1RP4HDLG4gm8LpHypyvkbhBlEuz59TdKmEOdwnQnQs5s/edit
- 2026-10-16 工程交接（歷史）：https://docs.google.com/document/d/16tzzLWNJnMn27A6FxAMSP9zFPixDxXPyMcaqjt0RKcQ/edit

**最新官方工程邊界**：

- Antigravity CLI Headless：https://antigravity.google/docs/cli/headless/
- GitHub 自架 Runner 註冊：https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
- GitHub Actions Secure use：https://docs.github.com/en/actions/reference/security/secure-use
- GitHub workflow 權限：https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

**驗證限制**：以上 GitHub/Drive 源與 PR metadata 為本次實際查閱；93 passed 與 Windows T7 FAIL 是原始文件記錄的歷史實測結果，**本次沒有在使用者 Windows 主機重跑**。任何 README/PR/Drive 未含足夠證據的內容均應在執行當日標 `UNVERIFIED`。本文件建立在 2026-11-04 瞬間快照上，若 branch、PR 或 CLI 版本變更，由 W0 重新確認即可，不需另建一份平行規畫。

---

### 第一版研究交付狀態（已由本 v2 計畫取代）

- **已完成**：唯讀來源核對、MVP 完成線、分級證據、W0–W7 工作包、人工前置清單、25 項驗收矩陣、安全 gate 與 Codex 接手指令。
- **驗證結果**：GitHub PR／程式與 Drive 文件已閱讀；**未跑使用者專案測試／真實 live E2E**。
- **風險／限制**：PR #15 依賴未合併 PR #10；production verifier、private runner、Antigravity live integration、T7 尚有 gate；現在不可稱全部完成。
- **待確認**：使用者是否授權 Codex 後續開始修改本地工作分支；外部 Private Inbox、Runner、登入、寫入／ACL 與 PR／Drive 動作分別由使用者按需核准。


## 10. 精確執行契約（供 Codex 長任務單次接關）

### 10.1 工作目錄與分支策略

Repo 的工作計畫發布在**獨立規劃分支** `plan/codex-antigravity-execution-20261104`，此分支以 PR #15 的 `b2488912f32ed4fc45bcfac967f185f871d5ca9f` 為起點。因此該分支 **包含 #15 未合併的程式碼**。這不是 `main` 的新狀態，不能以它的 HEAD 替代 PR #15 的來源 SHA。

本地執行必須先在使用者指定目錄做唯讀檢查，不可預設相同名稱的另一個 Git checkout 就是目標；若該 checkout 已有未提交變更，請建立新的、經確認路徑的 worktree / clone 作為執行區，原工作樹保留原樣。建議執行分支 `codex/execute-b-mvp-20261104` 應從規劃分支起始 commit 建立，**不是**在 `main` 上重做 #15。不得自動覆蓋已有同名分支。

**精確開工 preflight（唯讀部分可直接做）**：

```powershell
# 使用者需在已確認的 B 專案 Git 工作目錄執行；以下命令不會修改 Repo
pwd
git status --short
git branch --show-current
git rev-parse --show-toplevel
git rev-parse HEAD
git remote -v
git log -1 --format="%H %ci %s"
# 請先檢查所有輸出，不能在 dirty checkout 強制 switch/reset/clean
```

規劃分支在 GitHub 的精確 URL 及本機對應路徑以實際 readback 為準。若規劃文件未被成功讀到，**不要從舊聊天室憑印象寫碼**；可直接使用本文件的離線副本，標示 `PLAN_SOURCE_UNVERIFIED`。

### 10.2 逐檔案責任表（以現有檔案為優先）

| 工作 | 已查到的真實檔案 | 僅在差異確認後可新增的候選檔案 | 目的 |
|---|---|---|---|
| W0/W1 | `AGENTS.md`、`PROJECT.yaml`、`docs/DEVELOPMENT_ALIGNMENT_20261030.md`、`tests/test_control_plane.py` | 本次專用、去敏 evidence 目錄 | 固定真實基線，重跑測試 |
| W2 | `control_plane/orchestrator.py`、`control_plane/result.schema.json` | `control_plane/verifiers.py`、`tests/test_production_verifiers.py` | 不信任 Agent 自述，接可信驗證來源 |
| W3 | `control_plane/orchestrator.py`（`AgentAdapter`、`PassiveAdapter`） | `control_plane/adapters/`、`tests/test_live_adapters.py` | CLI runtime 薄介面；先 fixture 再 live |
| W4 | `github_handoff/core.py`、`github_handoff/cli.py`、`github_handoff/config.example.json`、`.github/workflow-templates/local-codex-handoff.yml` | 受限設定模板、disposable Inbox 工作流、整合測試檔 | GitHub Issue、核准／nonce／回寫；不新增常駐服務 |
| W5 | `github_handoff/`、`control_plane/`、`tests/` | 受控 E2E test harness 和 restricted logs | Parent 端到端真實證據 |
| W6 | `WINDOWS_ACL_IMPACT_MIN_CHANGE_PLAN_20261020.md` | T7 獨立報告與測試 fixture（非直接修改 ACL） | 確認 OS 權限拒絕，獨立安全 gate |
| W7 | `README.md`、`README.zh-TW.md`、PR #15、Drive CURRENT | 去敏 evidence summary、PR checklist | 對齊聲稱與實證，禁止假 PASS |

以上候選路徑**不是目前已存在檔案的聲稱**；Codex 必須先在實際 checkout 檢查來源是否已有實作／替代檔案，選最小 diff。

### 10.3 `W2` verifier 的逐項可信判斷（應可直接實作）

`ControlPlane` 目前僅接受 callable 回傳 `True/False`，因此新增驗證器不需建立 API server。提出「可信 execution evidence record」資料結構，可用本機 JSON 檔案／受限執行者輸出，關聯 `run_id/goal_id/task_id/attempt_id/approved_plan_digest/base_sha/actual_tool_exit/sha256`。

**信任邊界**：證據必須由 runner／test harness／Git 工具在受控工作目錄實際產生；Agent 只可提供候選 `evidence_ref`，不可決定該 ref 的驗證結果。必須驗證 evidence root、檔案 hash、source kind、attempt、nonce/digest、完整性及測試所需欄位；由外部 Repo/Issue 提供的 URL 僅為參照，不是可信 verdict。

| 驗證器 | 輸入必備 | PASS 條件 | 必拒絕 |
|---|---|---|---|
| Test | `name`、`evidence_ref`、受控 process result | 真執行 exit 0、無測試失敗、可核對原始 test log / structured report、run 身分吻合 | 僅報 `PASS` 的模型字串、只給 path、錯誤/截斷 report、exit 非 0、超時 |
| Acceptance | `criterion_id`、attempt、plan_digest、證據 ref | 已核准的 criterion，可信 harness 證據與本次 attempt 綁定 | 孤立截圖、舊 attempt、未列入的 criterion、自報成功 |
| Artifact | 真實 worktree 路徑、repo/base SHA、核准 write set、Git staged/unstaged/untracked | 真實變更與 report 相符、無越界、不可跨 junction/symlink、只在可寫範圍 | Agent 少報的實際變更、路徑跳脫、base 變更、保留未知副作用 |
| Approval | GitHub API 驗證身分、Issue 當下版本、nonce、digest、時間、allowlist | 確認不是 stale approval、已核准者、正確 scope、同一 revision | label 即核准、偽造 actor、重用 nonce、舊 digest、Issue 事後修改 |
| Writeback | 可信 API response、後續 readback、issue revision/posted comment | 真正對同一目標 issue 更新完成，內容去敏且冪等 | 僅本地 print 已完成、API 超時但未知是否已送達而盲重送 |

必要測試資料：`good-report`、`agent-forged-pass`、`tampered-hash`、`stale-attempt`、`wrong-base`、`missing-verifier`、`escape-path`、`untracked-file`、`symlink/junction`、`duplicate-delivery`。對每個拒絕案例要求**沒有完成狀態副作用**。

### 10.4 `W3` adapter 的「一次執行」規範

以 `AgentAdapter.health/capabilities/submit/status/cancel/collect_result` 作唯一對外介面，**不另建第二個 orchestrator**。對 CLI 的呼叫只允許 `argv list`，傳入固定 `cwd`、明確 timeout／kill 行為、STDOUT/STERR 最大長度、去敏及不暴露憑證；結果只採官方 CLI 當次輸出或可信 local process metadata。啟動後立即持久化 external run ID；若 ID 取得前中斷，原生工具無法判斷副作用時 `NEEDS_RECONCILIATION`，不可再派新 attempt。

- `health`：版本與登入可用性分開記錄，不讀出登入 token。
- `submit`：只送 digest 綁定的 task packet，並限制一次跨 runtime hop；預設 read-only。指定 write 必須通過授權與 sandbox／worktree gate。
- `status`：`UNKNOWN` 不能轉成 SUCCESS。碰到 CLI 不提供查詢功能時，設計保守狀態，而不是假造 running/completed。
- `cancel`：收到取消請求 != 子程序已終止；需等待 kernel process 終態或可信 runtime ack，狀態 unknown 則 reconciliation。
- `collect_result`：解析官方格式及嚴格 schema；若 v1，保持 `UNVERIFIED`；v2 由可信 transport 注入 session/attempt 身分再驗證。
- `retry`：只有具備冪等鍵、可確定未產生副作用或已完成對帳的工作可以重試；未知副作用必須停下且保留 evidence。

Antigravity CLI 歷史 headless 文件與本機版本要在 W0 重新確認；無法驗證旗標時，**不得寫成已知可執行命令**。不要用 GUI 操作代替可重現的 CLI 自動接力證據。

### 10.5 `W4` 私有 Inbox 真實操作流程（人與 Agent 分工）

1. **Codex（可先做）**：準備 GitHub private inbox repo 的 Workflow/Runner 設計、Receiver config 樣板（僅允許最小測試 repo）、狀態與回寫證據方案；review `github_handoff/` 真實 CLI 選項。
2. **Human Gate（不可代辦）**：使用者建立/選定專用 Private Inbox，確認不對任意 Issue／PR 自動執行、註冊 Runner 並注入秘密到安全環境、完成兩種 CLI 登入；只回傳非機密 runner 狀態與 repo URL。
3. **Codex（設定後繼續）**：執行 repo 已存在的 `doctor` → unit → `dry-run` → 人工 `workflow_dispatch` → `once`，建立 synthetic Issue；先驗證 Pending，再由 allowlisted approver 在 GitHub 留下現有語法的核准留言（不是只貼 label）。
4. **Codex（live 驗證）**：核對 issue edit-time、actor、digest、nonce、host、scope、worktree；只跑一個批准的任務，回寫結果至原 Issue，再讀回核對。重送同事件不得二次執行；篡改/未授權/舊 nonce 必須拒絕。
5. **復原**：當 Runner/Workflow/憑證或真實 scope 有疑慮，停用該 Workflow、Runner 設 Offline，由使用者撤銷 credential。保留 Issue ID、run ID、hash 等去敏證據；不要默默刪除外部資源。

**已查到的硬邊界**：`.github/workflow-templates/local-codex-handoff.yml` 是模板、`workflow_dispatch` 一種觸發，`issues: read` 不自動包含回寫；Receiver 所需的認證應另核最小權限。不要用開放 `issue_comment.created` 來掩飾手動觸發的缺口。

### 10.6 `W5` 一個必跑的完整合成場景

測試 Repo 不應含真實專案資料。唯一 Parent Goal（示例名稱 `G-20261104-SYNTH`）具三個依賴任務和一個整合任務：

| 節點 | 所屬 Runtime | 輸入 | 輸出與證據 | 下一步 |
|---|---|---|---|---|
| A `preflight` | Codex Lead | synthetic fixture、核准 digests | 驗證輸入與基線、留下 runner log | 派 B |
| B `worker` | Antigravity Worker | 只允許讀指定 synthetic 資料；若測寫入另行 gate | 真實 CLI Result Packet v2、正確 attempt/delivery | Lead 自動 ingest |
| C `integrate` | Codex Lead | 已核對 B 的 results | 受控單檔產物、hash、可信 diff／tests | 驗證 Parent |
| D `acceptance` | Codex Integration | 同一 plan/attempt 之 evidence | Parent AC verified、Issue status/writeback readback | `COMPLETED` |

**成功的核心不是 B 單次 CLI 返回**，而是 Lead 完全不需使用者複製貼上，自動從 B 的 Result Packet 收斂 unresolved、新工作、重啟及 integration，直到 Parent criteria 都有實證。若遇到發現新工作，應進既有 `PENDING_REVIEW`，**這是正確的 Human Gate 測試結果，不是任務失敗**。

每一級保存 `run_id`、UTC timestamp、host OS、CLI 版本、repo SHA、task/delivery/attempt ids、identity、原始工具 exit、verified result、去敏 evidence hash、Issue/run URL。證據的 PASS 只對該級有效。

### 10.7 `W6` 安全 gate 只能用真實 OS 判定

2026-10-20 同一父層 ACL 方案已實測失敗（主機重新施加 `CodexSandboxUsers Modify`），不能重複執行而忽略先前影響。先確認**現在**使用的 worktree 是否跟舊的 `Documents\Tech Review` 同一路徑、安全 SID、Windows policy；如果不同，原測試不自動移植。

預設只產出 `T7_DESIGN_READY`，不改安全設定。欲解鎖無人值守或跨 Repo，必須先取得一次性主機權限修改核准，使用獨立低權限使用者或 VM/容器專用 mount，驗證根路徑內 ALLOW、其他 sibling/user 目錄及 junction/UNC/子程序 DENY，存完整前後與 rollback log，才可判 `T7_OS_PASS`。沒有通過時維持 `UNATTENDED_WRITE=DISABLED`，不妨礙人工監督的單 Repo UAT。

### 10.8 `W7` 可審核交付與衝突處理

先保留 #15 → #10 的依賴，核對 `main` 是否已包含 #13 與其他更新。完成實作後應交付：

- 可審查的**獨立執行分支**及精確 commit / changed files / diff 範圍；**不得將程式直接合進 main**。
- Verified tests 的原始日誌（本機受限）與去敏摘要、缺陷列表、實際 E0–E6 evidence、`MVP-L`、`T7` 與 `UNATTENDED_WRITE` 狀態。
- PR #15 的安全整合建議：依據最新 Base/Main 判斷是更新既有 PR、由依賴 PR 先處理或另提整合 PR；**未經使用者核准，不做 force push／rebase／merge**。
- Drive 唯一 `CURRENT` 的**更新草稿**：last_verified、repo SHA、PR 狀態、各級 evidence、blockers/human gate、下一個具體行動與原始來源；真正覆寫原 `CURRENT` 需再次得到使用者確認（本任務只授權新增規劃文件）。

**完成的判斷**：可審核 PR 就緒，是工程交付狀態 `REVIEW_READY`；只有 E0–E6 實際通過才可另列 `MVP-L=PASS`。PR 的 merge 不屬自動工作範圍；若缺外部條件，Codex 應盡可能做到 `LOCAL_READY`，報告唯一剩餘的 Human Gate，而不是每走一步停下提問。

## 11. 單回合可持續的 Orchestration／回復協定

`EXECUTION_MANIFEST_20261104.json` 是這份計畫的**執行索引**，不是第二個進度真理源。真正程式狀態以 Git commit/log、正式核准的 GitHub Issue/PR 及 Drive CURRENT 為準；manifest 的 `status` 初值全部 `NOT_RUN`，不得當成當前工程成果。

### 11.1 狀態與依賴

- 狀態：`NOT_RUN` → `RUNNING` → `PASS / FAIL / BLOCKED_EXTERNAL / HUMAN_GATE / SAFETY_STOP / SKIPPED_WITH_REASON`。
- 只有依賴 `PASS` 才可展開對應工作；遇 `BLOCKED_EXTERNAL`，**只停受影響的節點**，可先執行無依賴的工作。
- 每次工作包結束，存本地 evidence manifest（去敏摘要可分享），附 `plan_version`、`base_sha`、`head_sha`、`run_id`、command（可重現者）、exit、測試結果與阻礙，不要直接編輯原規劃檔當成「完成紀錄」。
- 遇到 unknown side-effect，不要直接 retry：先在確保原執行已終止的前提下 readback Git status、runtime status、Issue comment，無法辨識則 `NEEDS_RECONCILIATION` 並僅停相依寫入。
- 各階段結束要產出**唯一下一步**（指向具體 W 子任務與檔案），而不是「待研究」。

### 11.2 不可中途反覆索取的資訊

Codex 在 Stage I 開始前應先從現有 Repo/Drive/本機 source 取得已知設定；對命令選項先讀本機 `--help` 或既有 `github_handoff/` 真實 parser。只有無法自行確定的**主機帳號登入、憑證、Private Repo、Runner 註冊、實際權限調整、外部發佈/merge**才統一形成 User Action Packet，集中一次提出；未獲批准不越權操作。

### 11.3 啟動與結束時要輸出的最小摘要

```text
PLAN_VERSION: 2026-11-04-v2
SOURCE_BRANCH: plan/codex-antigravity-execution-20261104
WORK_BRANCH: <actual branch and HEAD>
STAGE: I or II
LAST_COMPLETED: <work_id + evidence file>
NEXT_READY: <exact work_id + file/command>
LOCAL_READY: PASS / FAIL / NOT_RUN
PRIVATE_INBOX_LIVE: PASS / BLOCKED_EXTERNAL / NOT_RUN
CROSS_RUNTIME_PARENT_E2E: PASS / BLOCKED_EXTERNAL / NOT_RUN
T7_OS: PASS / FAIL / NOT_RUN
UNATTENDED_WRITE: DISABLED unless separately approved + verified
HUMAN_ACTIONS: <consolidated numbered, nonsecret operations or NONE>
PR_STATE: REVIEW_READY / BLOCKED / NOT_STARTED
```

## 12. 交付位置與資料治理

- **Drive（人類閱讀）**：在既有 `2026-10-16_本地多Agent協作系統` Folder ID `1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s` 新增「**本地多Agent協作｜完整工程執行計畫｜20261104**」Google Doc，並保留可離線閱讀的 DOCX／自包含 HTML。**不要建立第二個 CURRENT**；規劃文件只用於決策與驗收，不取代原 CURRENT。
- **GitHub（Agent 接手）**：在獨立 `plan/codex-antigravity-execution-20261104` 分支放 `docs/implementation/EXECUTION_PLAN_20261104.md`、`EXECUTION_MANIFEST_20261104.json`、`CODEX_START_HERE_20261104.md`；本次不修改程式、不合併主分支。
- **權威分工**：程式／測試/提交以 GitHub 為準；正式規劃、驗收與人類進度以 Drive 為準；這些計畫檔是「指引／索引」，不是第二套持續維護的 backlog 或 LTG knowledge store。
- **驗證**：發布後要讀回 GitHub 三檔及 Drive 文件，核對計畫版本與所在 folder。無法直接上傳某個格式時，必須標 `UPLOAD_BLOCKED`，不可聲稱已放入。
