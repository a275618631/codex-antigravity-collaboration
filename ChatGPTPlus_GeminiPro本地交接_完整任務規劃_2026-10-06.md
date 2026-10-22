# ChatGPT Plus／Gemini AI Pro 本地交接完整任務規劃（2026-10-06）

## 1. 任務結論

本案只支援個人版 **ChatGPT Plus** 與 **Google AI Pro 的 Gemini**，入口限網頁版與手機 App。兩者負責討論、產生標準任務卡及閱讀 Result Packet；GitHub Private Issue 是唯一任務、核准與狀態帳本；Windows 本機 Receiver 負責驗證、執行及回寫。

目前官方能力不足以讓這兩個個人方案在台灣從原對話直接完成可靠的外部寫入及結果主動回灌，因此正式流程定義為「一次人工確認開單＋本機自動執行與回報」。不使用瀏覽器 DOM 自動化，不依賴 Business／Enterprise／Cloud Work，也不把 Drive 當第二個 Queue。

## 2. 目標流程

```text
ChatGPT Plus／Gemini AI Pro 討論
  → 產生標準 Task Brief
  → 使用者點預填 GitHub Issue 連結並確認建立
  → 授權者核對 digest／nonce／host 後核准
  → Windows Receiver 安全輪詢並接單
  → Codex 在獨立 worktree 執行與驗證
  → Receiver 更新單一進度留言及 Result Packet
  → 使用者把 Issue URL／Result Packet 帶回原對話續談
  → 新變更建立 child Issue 並重新核准
```

## 3. 不變量

- 沿用既有 Receiver，不重寫核心。
- GitHub Issue 是唯一 execution ledger；Drive／repo 只保存文件、程式與工作紀錄。
- 一個 Issue／Task ID 只執行一次；後續修改使用新的 child Issue、revision 與 nonce。
- Issue 內容永遠視為不可信資料，不可直接成為 shell command。
- Repo、branch、read/write scope、actor、approver、host 均須 allowlist。
- approval 必須綁定最新內容 digest；編輯後舊核准立即失效。
- Token 只從程序環境讀取，不寫入設定、Issue、日誌、測試 fixture 或工作報告。
- 單一主機、單一 active writer、獨立 worktree；不自動 merge。
- macOS 在實機驗證前保持 `NOT VERIFIED`。

## 4. 工作分解與相依性

### P0｜基線與文件落盤

狀態：`COMPLETE`

- 保存本規劃、工作日誌及驗收清單。
- 核對目前分支、遠端、既有測試、PR 與工作樹狀態。
- 修正過期文件中的 Windows E2E／Push／Draft PR 狀態。

驗收：文件可在 repo 直接回讀，且未包含 Token、本機使用者名稱或私密絕對路徑。

### P1｜對話入口薄適配

狀態：`COMPLETE (LOCAL)`

- 建立 ChatGPT Plus／Gemini AI Pro 共用 Task Brief 範本。
- 增加非敏感來源 metadata：`Origin Surface`、`Client`、`Parent Task ID`、`Revision`；禁止保存 conversation URL、cookie、session ID 或整段聊天。
- 提供預填 GitHub Issue URL 產生器；不持有 GitHub Token、不直接替使用者送出。
- 針對手機輸出短版 Result Packet，方便貼回原對話續談。

相依：P0。

驗收：兩種入口產生相同 canonical task body；URL 參數正確編碼；超長內容安全拒絕；既有 Issue 格式仍相容。

### P2｜Receiver 可持續執行與進度回報

狀態：`COMPLETE (LOCAL)`

- 新增安全的前景輪詢命令，以 marker 控制啟停，含間隔與 backoff。
- 每個 Issue 只維護一則 progress comment，依序反映 Queued、Running、Validating、Reporting、Terminal。
- 啟動時執行 stale-state reconciliation；local lock 防止雙重 Receiver。
- 不自動安裝或啟用常駐服務；Windows 排程只提供可審閱安裝說明或腳本。

相依：P0。

驗收：重複 poll 不重複修改；progress comment 不增生；停止 marker 後可控結束；API 暫時錯誤有上限 backoff。

### P3｜後續討論、取消與復原

狀態：`COMPLETE (LOCAL)`

- child Issue 必須帶 `Parent Issue` 與遞增 `Revision`，且仍需新 digest／nonce。
- 執行前 Issue 已關閉或含有效取消指令時不得接單。
- 執行中取消維持本機中斷與重啟對帳；若實作遠端取消監看，必須有明確 actor allowlist 與測試。
- Failed／Blocked／Cancelled 保留 state、evidence 路徑及 worktree，不自動刪除。

相依：P1、P2。

驗收：未核准、內容變更、nonce 重用、Task ID 重用、取消與 stale recovery 全部有自動測試。

### P4｜文件、平台驗收與交付

狀態：`COMPLETE (LOCAL) / LIMITED CLI PROBE PASS / EXTERNAL E2E NOT VERIFIED`

- 更新使用手冊、Runbook、Security、Final Report、README、計畫與驗收清單；PR #9 已於 2026-10-22 依使用者明確核准合併。
- Windows 執行完整單元／整合測試；不使用真實 Token 的測試均自動完成。
- 真實 GitHub E2E 只在既有專用 Private 測試 repo、短期 fine-grained Token 及使用者明確執行下進行。
- 2026-10-22 限定唯讀 Antigravity CLI nonce probe：`PASS`；直接桌面 MCP mailbox 路徑與桌面 GUI 單獨可用性尚未重新驗證。
- ChatGPT Plus Web/Mobile、Gemini AI Pro Web/Mobile 與 macOS 實機流程仍為 `NOT VERIFIED`。
- T7 OS 級跨專案寫入隔離仍為 `FAIL`；不得執行無人值守或跨 Repo 寫入。主機 ACL 修正需管理員／使用者人工操作。
- PR #10 僅更新上述新證據與狀態，保持開啟待審；不得自動合併。

相依：P1–P3。

驗收：完整測試綠燈、`git diff --check` 通過、敏感資料掃描通過、文件狀態與實際證據一致。

## 5. Worker 分配

| Workstream | 負責角色 | Write-set | 交付與驗收 |
|---|---|---|---|
| Gap audit | Explorer（唯讀） | 無 | 檔案級缺口、相依性、驗收命令 |
| Receiver core hardening | Luna worker A | `github_handoff/core.py`、schemas、Issue template、core tests | 契約、安全與去重測試 |
| Receiver lifecycle | Luna worker B | `github_handoff/cli.py`、config、必要 scripts／lifecycle tests | foreground watch、lock、backoff、stop |
| 文件與工作日誌整合 | Parent Sol | 根目錄正式文件 | 狀態、證據、操作手冊與 manifest |
| 安全／回歸驗收 | Parent Sol；高風險時獨立 reviewer | 唯讀 | 測試、secret scan、diff audit |

同一 write-set 同時只允許一個 writer；worker 不得修改 shared rules、global skills、Bridge 或其他專案。

## 6. 完成定義

- ChatGPT Plus／Gemini AI Pro 都能產生同格式 Task Brief 與一鍵預填 Issue。
- Receiver 能以前景輪詢模式持續運作，單一留言呈現進度，並保持去重與核准安全。
- Result Packet 可帶回原對話繼續討論；後續工作透過 child Issue 安全重派。
- 所有非真實 GitHub 寫入測試自動通過；59 項 Windows 單元／整合測試與限定 CLI nonce probe 已 PASS。直接桌面 MCP mailbox、真實 GitHub E2E 與 T7 OS 隔離仍未通過或未驗證，必須分別標示，不可互相代替。
- 計畫、工作日誌、操作文件、驗收結果與交付物索引均保存在本 repo。
- 不宣稱「完全原生對話內自動化」；不啟用常駐服務、不自動 merge。

## 7. 官方能力依據

- ChatGPT GPT 建立與編輯限制：<https://help.openai.com/en/articles/8554397-creating-and-editing-gpts>
- ChatGPT Developer Mode／MCP：<https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt>
- Gemini Web 地區支援：<https://support.google.com/gemini/answer/13575153>
- Gemini Custom Apps／MCP：<https://support.google.com/gemini/answer/17209137>
- GitHub REST API 最佳實務：<https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api>
