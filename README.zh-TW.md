# Codex × Antigravity｜架構設計與實作紀錄

這個專案研究兩套 AI 開發環境如何合作完成工程任務。目標是讓任務可以清楚分工、結果能夠驗證，且不同 Agent 不會在同一個工作區互相覆寫。

與其替 Codex、Antigravity 重寫另一套 Agent Runtime，我選擇用共同契約、本地橋接和 Git 工作流程連接既有能力。

## 技術組成

| 元件 | 負責什麼 |
| --- | --- |
| **Task／Result 契約** | 記錄目標、讀寫範圍、驗收方式、實際輸出與剩餘工作 |
| **能力導向委派** | 將工作送給有相應工具的 Runtime；跨 Runtime 委派有次數限制 |
| **Shared Skills** | 通用的工作方法只維護一套，平台差異交由薄 Adapter 處理 |
| **MCP Bridge** | 以本地 JSONL mailbox 交換任務與狀態；使用 Windows／POSIX 對應的檔案鎖 |
| **Git 工作隔離** | 使用 branch、worktree、diff、PR 與審查處理平行變更 |
| **人工核准** | 工具執行與寫入遵守允許範圍；尚未授權的任務保持待核准 |

## 實作情境

假設一個專案需要修改 API、補測試，並讓另一套 Agent 查看結果：

1. 先寫出 Task，包含修改範圍和成功條件。
2. 指定合適的 Runtime 在獨立工作區處理。
3. 執行完成後，回傳 Result，附上變更、測試與阻礙。
4. 檢查 Git diff 與測試證據，再決定是否合併。

最重要的是**讓結果可接續、讓修改可追溯**；不需要把每一個簡單工作都升級成多 Agent 交互通訊。

## 已完成的實作與測試

- 本地 MCP Bridge、Task／Result 合約與有限委派邏輯已建置。
- 2026-10-20 Windows 本地橋接完成雙程序測試，相關 GitHub handoff 測試曾記錄 **53 項通過**。
- 2026-10-20 的跨 Runtime 受限唯讀交接有成功紀錄；2026-10-22 的再次測試逾時。這兩次結果說明本地協作機制可用，但完整桌面端交互仍需穩定性驗證。
- Git branch／worktree 與人工審查可管理程式修改；尚未完成 T7 的作業系統層級跨專案寫入隔離，因此不將無人值守跨倉寫入當作已驗收功能。

[跨 Runtime 測試證據](LIVE_HANDOFF_EVIDENCE_20261020.md) · [操作手冊](GitHub本地Codex自動交接_使用手冊_20260929.md)

## 核心設計原則

**優先用平台原生能力。** Codex 和 Antigravity 已有自己的工具、平行執行及任務管理能力，不必再複製一套。

**跨 Runtime 合作保持簡單。** 先使用 GitHub 與共同工作格式；需要本地直接交換訊息時再用 MCP Bridge。佇列、心跳與多主機協調應隨實際需求增加。

**保留人工決策位置。** Agent 可以整理、撰寫和測試，但未授權的高風險修改不能自動擴大工作範圍。

**敏感資料先分類。** 在本機研究 Local／Cloud 分流與去識別方法，正式隱私路由 Gateway 尚不是目前可用的產品功能。

## 程式與相關文件

- [本地 MCP Bridge](local_bridge/README.md)
- [GitHub 本地 Codex 接單技術文件](github_handoff/README_GITHUB_HANDOFF_20260929.md)
- [整體架構](docs/ARCHITECTURE.md)
- [隱私設計](docs/PRIVACY_AND_TRUST.md)
- [功能狀態與路線](docs/STATUS_AND_ROADMAP.md)
- [本機知識庫工作台：Trilium 採用與最小整合規劃](docs/LOCAL_KNOWLEDGE_WORKSPACE_PLAN_20261111.md)（規劃與工單；尚未本機部署驗收）

這個作品最適合用來理解如何設計**低耦合的多 Agent 協作機制**，也可以單獨採用其中的任務契約、本地 Bridge 或 Git 交付方式。
