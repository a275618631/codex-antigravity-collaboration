# Antigravity × Codex Shared Collaboration Protocol (v3)

## 1. 宗旨與核心原則

本協定為 **Antigravity** 與 **Codex** 雙 Runtime 協作之核心規範，作為所有跨平台工作之唯一共通標準 (Shared Canonical Source)。

### 核心原則
1. **原生能力優先 (Native Capabilities First)**：各 Runtime 優先使用本機原生 Subagents、Worktrees、Skills、Permissions 與排程機制，不額外建立非必要的調度層或 Broker。
2. **漸進複雜度 (Complexity Must Be Earned)**：以 Shared Workspace、CLI Bridge、MCP 協作為主，嚴禁引入不必要之 Message Broker、Redis、Vector DB 等常駐服務。
3. **能力導向路由 (Capability-Aware Routing)**：依 Runtime 特長派工，不對相同任務進行重複無謂派發。
4. **有限委派與防遞迴 (Bounded Delegation / One-Hop)**：跨平台委派嚴格限制為最多一跳 (1-Hop)，杜絕遞迴調用風暴。
5. **共享核心，薄適配層 (Shared Core, Thin Adapters)**：共用核心 Rules 與 Skills，各平台僅維護薄適配層 (Thin Adapters)。
6. **單一寫入者 (One Active Writer Per Write-Set)**：支援多方唯讀分析與審查，但同一目標檔案集 (write-set) 同一時間僅允許單一 active writer。
7. **嚴格安全與低干預 (Safety & Minimal Human Overhead)**：不傳遞 Secret/Token，安全可回復操作全自動執行，高風險破壞性行為保留人工確認閘門。

---

## 2. 雙 Runtime 職責劃分 (Routing Guidelines)

### Antigravity (Primary Coordinator / Host Runtime)
* **角色定位**：主協調者 (Coordinator)、環境安裝與維護者、全域驗證者。
* **主要領域**：
  - Google 生態系整合 (Drive, Gmail, Docs 等)
  - 瀏覽器檢視、除錯與自動化 (優先使用 NeoBrowser / Chrome DevTools)
  - 大量文件閱讀、跨文件檢索與整合分析
  - 龐大 parallel workers / background tasks
  - 全域 MCP 協調
  - 本機環境部署與驗收判定

### Codex (Secondary Runtime / Engineering Specialist)
* **角色定位**：深度工程實作者、Repo 工作者、代碼審查者、第二意見提供者。
* **內部角色 (Codex Roles)**：
  - **Sol**：規劃、架構設計、協調、最終交付判定、審查。
  - **Luna**：快速任務、常規作業、小型修訂、安全交付。
  - **Terra**：深度程式碼實作、架構重構、工程除錯、嚴格測試驗證。
* **主要領域**：
  - 深度 Coding、Refactoring、Bugfix
  - Repository 級別修改與維護
  - 專案 Build、Unit/Integration Tests 執行
  - Git-aware 工程任務
  - 嚴格 Code Review 與架構評估

---

## 3. 委派規範與防遞迴守則 (Bounded Delegation & One-Hop)

### 跨平台一跳限制 (One-Hop Rule)
* **允許路徑**：
  - `Antigravity` → `Codex` (1-Hop)
  - `Codex` → `Antigravity` (1-Hop)
* **嚴禁路徑 (Recursive Delegation Ban)**：
  - `Antigravity` → `Codex` → `Antigravity` (禁止！Codex 收到委派後不得再次委派 Antigravity)
  - `Codex` → `Antigravity` → `Codex` (禁止！)

### 平台內部子代理不計入跨平台 Hop
* `Antigravity` → `Antigravity Subagent` → `Antigravity Reviewer` (合規)
* `Codex (Sol)` → `Codex (Terra)` → `Codex (Sol Review)` (合規)

---

## 4. 協作模式 (Collaboration Modes)

1. **Vertical Delegation (垂直委派)**：
   主控者指派明確邊界的子任務給專門 Runtime，受託者完成後回傳 Result Packet。
2. **Read-only Debate (唯讀技術辯論)**：
   針對重大架構或技術選型，雙方 Reviewer 進行最多 **2 輪** 唯讀交叉評估。
   - 格式包含：`主張 (Claim)`、`證據 (Evidence)`、`風險 (Risk)`、`建議 (Recommendation)`。
   - 辯論期間**嚴禁修改任何正式檔案**。
   - 辯論結束後由主控者裁決，並指定**單一 Implementer** 執行。
3. **One-Writer Implementation (單一寫入實作)**：
   多方可同時讀取與審查，但實作修改期間由指定 Writer 獨佔 write-set，避免編輯衝突。

---

## 5. 通訊封包規格 (Contract Schemas)

### Task Packet (任務封包)
任何跨 Runtime 委派任務必須提供具備以下結構的 Task Packet：
```yaml
task_packet:
  task_id: "<UUID or timestamped string>"
  initiator: "Antigravity | Codex"
  target: "Codex | Antigravity"
  hop_count: 1  # 必須 <= 1
  collaboration_mode: "Vertical | Debate | Review | Implementation"
  objective: "<清楚具體的任務目標>"
  context:
    sources_of_truth: ["<檔案路徑或 URL>"]
    background: "<必要背景資訊>"
  lane: "fast | standard | deep"
  scope:
    read_scope: ["<允許讀取之路徑清單>"]
    write_scope: ["<允許寫入之路徑清單，唯讀任務為空>"]
  constraints:
    - "<不可更動之檔案或邊界>"
    - "<禁止行為 (例如禁止 force push、禁止外流 secret)>"
  validation_criteria:
    - "<驗證通過標準，如測試指令、Lint、回讀檢查>"
  expected_output_format: "Result Packet"
```

### Result Packet (結果封包)
受託 Runtime 完成任務後，必須回傳符合以下結構的 Result Packet：
```yaml
result_packet:
  task_id: "<對應之 task_id>"
  responder: "Codex | Antigravity"
  status: "SUCCESS | PARTIAL | FAILED | BLOCKED"
  summary: "<結論性成果摘要>"
  changes:
    modified_files: ["<修改檔案路徑>"]
    created_files: ["<新增檔案路徑>"]
    deleted_files: ["<刪除檔案路徑>"]
  evidence:
    - "<具體執行紀錄、指令輸出或回讀證明>"
  validation_results:
    tests_run: ["<執行的測試名稱或指令>"]
    passed: true | false
    details: "<測試輸出與狀態>"
  risks_and_limitations:
    - "<已知限制或潛在風險>"
  remaining_work:
    - "<尚未完成或待後續跟進之事項>"
  recommendation: "<下一步建議行動>"
```

---

## 6. 安全與隱私邊界 (Security & Privacy Boundaries)

1. **嚴禁外洩敏感資料**：禁止在 Task Packet、Result Packet、日誌或程式碼中傳遞任何 API Key、Token、Password、Cookie、OAuth Secret、SSH Key 或 `.env`。
2. **路徑正規化**：macOS 環境下一律使用 `$HOME` 或標準路徑，嚴禁複製 Windows 絕對路徑或 Windows 專屬 sandbox 設定。
3. **人工確認閘門**：
   - 刪除重要資料
   - 覆寫且無備份之檔案
   - Git Push (非受保護 feature branch 外)、Merge、Publish、Deploy
   - 涉及系統權限或 Keychain/帳號變更
