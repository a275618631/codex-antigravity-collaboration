# Antigravity × Codex Shared Collaboration Protocol (v3)

## 1. 宗旨與核心跨平台不變量 (Cross-Runtime Invariants)

本協定為 **Antigravity** 與 **Codex** 雙 Runtime 協作之核心規範，作為所有跨平台工作之唯一共通標準 (Shared Canonical Source)。

### 10 大核心不變量
1. **原生能力優先 (Native Capabilities First)**：各 Runtime 優先使用本機原生 Subagents、Worktrees、Skills、Permissions 與排程機制，不額外建立非必要的調度層或 Broker。
2. **共享核心，薄適配層 (Shared Core, Thin Adapters)**：共用核心 Rules 與 16 項 Global Core Skills，各平台僅維護薄適配層 (Thin Adapters)。
3. **有限委派與防遞迴 (Bounded Delegation / One-Hop)**：跨平台委派嚴格限制為最多一跳 (1-Hop)，杜絕遞迴調用風暴（例如：A ➔ B 合規；A ➔ B ➔ A 嚴禁）。
4. **單一寫入者 (One Active Writer Per Write-Set)**：支援多方唯讀分析與審查，但同一目標檔案集 (write-set) 同一時間僅允許單一 active writer 進行修改。
5. **嚴格安全與無 Secret 傳遞 (No Secret Transfer)**：禁止在 Prompt、封包、日誌或程式碼中傳遞任何 API Key、Token、Password、Cookie、OAuth Secret、SSH Key 或 `.env`。
6. **低干預與安全自動化 (Minimal Human Overhead)**：安全可回復操作全自動連續執行，不可逆高風險破壞性行為（刪除、覆寫、強制 Push）保留單一確認閘門。
7. **預設單一主力模型 (Default Single Strong Agent)**：一般任務預設由當前主力 Agent 直接執行，不進行無謂的角色包裝或前置委派。
8. **條件式並行 (Parallel Only Clean Workstreams)**：僅在任務可拆為無寫入衝突之獨立工作流時啟用並行 Subagents（預設最多 2 concurrent workers）。
9. **高門禁審查 (High-Risk Review Only)**：僅在涉及安全、權限、認證、資料庫遷移、公共 API 變更或使用者明確要求時調度 Reviewer。
10. **結構化跨平台交付 (Structured Cross-Runtime Contract)**：跨 Runtime 委派時遵循結構化通訊協定，一般單 Agent 任務無需載入封包規格。

---

## 2. 漸進式細節引用 (Progressive Disclosure)

- **執行期能力與調度指南**：請參閱 `references/runtime-routing.md`。
- **跨平台任務與結果封包規格**：請參閱 `references/cross-runtime-packets.md`。
