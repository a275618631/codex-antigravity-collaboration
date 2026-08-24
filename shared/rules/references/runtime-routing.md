# Runtime Routing Guidelines & Execution Profiles

## 1. Runtime 特長與分工

### Antigravity (Primary Coordinator / Host Runtime)
- **主要特長**：全域總控、環境安裝與部署、Google 生態系整合 (Drive, Gmail, Docs)、瀏覽器自動化 (Chrome DevTools / NeoBrowser)、大量文件整合檢索。
- **適用工作**：全域驗收、多任務平行調度、跨專案宏觀分析。

### Codex (Secondary Runtime / Engineering Specialist)
- **主要特長**：深度程式碼實作、Repo 重構、單元與整合測試、Build 排障、第二意見審查。
- **適用工作**：專案級別 Coding、Bugfix、複雜工程修改。

---

## 2. Codex Execution Profiles (Sol / Luna / Terra)

- **Sol (Sol Auto)**：規劃、架構決策、調度、最終交付判定、高門禁審查。
- **Luna (Luna Worker)**：快速任務、常規作業、小型修訂、非破壞性交付。
- **Terra (Terra Worker)**：深度程式碼實作、架構重構、工程除錯、嚴格測試驗證。

> **註**：以上為 Codex 專屬之 Execution Profiles。在日常任務中，模型預設以單一強 Agent 直接執行，僅在調用對應 profile 時按需參考。
