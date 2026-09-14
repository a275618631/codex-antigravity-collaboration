---
name: save-to-notion
description: 將 Codex 對話、回答、決策、工作流程與可重用知識整理到使用者的 Notion 知識 Hub；僅在使用者明確要求保存、歸檔或更新到 Notion 時觸發，一般報告不自動寫入。
---

# Save To Notion

將可重用的結論、流程、決策、版本變更與下一步整理成結構化 Notion 內容，不保存原始聊天流水帳。

## 寫入門檻與驗證

- 只有使用者明確指定 Notion 作為目的地，或明確要求保存／歸檔到 Notion，才執行實際寫入；否則只提供可貼上的草稿。
- 寫入前先用 Notion `fetch("self")` 驗證目前帳號與 Workspace，再重新讀取目標 Data Source schema；不得沿用快取欄位、舊 URL 或舊 schema。
- 帳號、Workspace、目標頁面或 Data Source 不一致時停止寫入並回報，不自動切換、建立或搬移資料庫。
- 建立前搜尋相同主題，決定更新既有頁面或建立新頁面；歷史頁面不自動搬移、複製或刪除。

## 最小工作流程

1. 讀取現行工作區標準與目標 schema，確認內容分類與目的地。
2. 只保存已確認事實、結論、指令、路徑、決策、假設、警告與下一步；省略閒聊、重複脈絡與工具雜訊。
3. 依現行欄位建立或精準更新一個頁面／資料庫項目，必要時追加版本紀錄與關聯。
4. 完成時回報目的地、建立／更新狀態、版本變更與待人工確認事項。

Notion 工具不可用時，讀取 [notion-templates.md](references/notion-templates.md) 產生可直接貼上的歸檔稿，並明確說明尚未寫入。

## 路由參考

目前帳號、Workspace、Hub、Data Source 與資料庫分類的可變設定見 [workspace-routing.md](references/workspace-routing.md)；每次寫入前仍須以 live account/schema 驗證為準。
