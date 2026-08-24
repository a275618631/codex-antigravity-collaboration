---
name: save-to-notion
description: 將 Codex 對話、回答、決策、工作流程與可重用知識整理到使用者的 Notion 知識 Hub。當使用者明確說「save to notion」，或要求保存、歸檔、整理、分類、版本化、更新到 Notion 時使用；若只是要求產出一般報告或文件，除非另有指定，不要觸發 Notion 實際寫入。
---

# Save To Notion

## 目的

將有價值的 Codex 對話整理成結構化 Notion 知識，而不是保存原始聊天流水帳。優先保存可重用的結論、流程、決策、版本變更與下一步行動。

使用者的主要 Notion Hub：

`https://app.notion.com/p/440e62ad3eb382c4977201bf8ba9b217`

目前首頁名稱：`工作控制中心`

工作區整理標準：

`https://app.notion.com/p/3a6e62ad3eb3811fb01ccc6b41c34d5d`

目前固定儲存帳號與目的地：

- 帳號：`a275618631@gmail.com`
- Workspace：`Dan Wu's Notion`
- 入口頁：`工作控制中心`
- 主要資料庫／Data Source：`長期知識庫`
- Data Source ID：`collection://d26e62ad-3eb3-8226-a4b8-07e35af67f7f`

目前資料庫路由（建立或更新前仍須重新 fetch schema）：

- 可重用知識、治理規則、跨平台同步與沒有專用庫的內容：`長期知識庫` — `collection://d26e62ad-3eb3-8226-a4b8-07e35af67f7f`
- 產品知識、SOP、FAQ、產品決策：`Product Knowledge｜知識庫` — `collection://20f5cdd8-1317-4347-b851-75ad0dc44371`
- 專案：`Projects` — `collection://71ce62ad-3eb3-838a-a8c1-87c91fc0cda8`
- 任務與待辦：`Tasks` — `collection://02ce62ad-3eb3-830d-9305-07366d140e4f`
- 簡報、會議、對外文件與素材索引：`Docs & Sharing｜文件與分享` — `collection://f3a829a4-b8b8-44b6-b6ab-4c8cbe65e264`
- 技術規格、架構、API、ADR、測試與發布：`Engineering Specs｜技術規格` — `collection://0bceb53e-3ab3-44e2-89d5-30515dca9bbe`
- 快速開始、功能教學、FAQ、疑難排解與公開手冊：`User Manual｜使用者手冊` — `collection://a7d50f3a-03f2-4d81-9c45-aa6d01eca2f4`

`Docs & Sharing` 目前合併簡報、文件與素材索引；除非試行後確認需要，避免再建立重複的 Presentations 或 Assets 資料庫。

使用者的短觸發指令：

`save to notion`

## 目的地驗證

- 實際寫入前先用 Notion `fetch("self")` 確認目前帳號是 `a275618631@gmail.com`。
- 再讀取目前 Data Source schema；不得沿用快取欄位名稱或舊 Hub URL。
- 若登入帳號、Workspace 或 Data Source 不一致，停止寫入並回報，不自動切換或建立另一個資料庫。
- 既有歷史頁面不自動搬移、複製或刪除；只有使用者明確要求時才規劃遷移。

## 寫入門檻

- 只有使用者明確指定 Notion 作為目的地，或明確要求保存／歸檔到 Notion，才執行實際寫入。
- 一般報告、文件或工作成果若未指定 Notion，交由對應的報告／文件 skill 處理；需要時只提供可貼上的草稿，不自行寫入。
- 即使使用者要求保存，也要先確認目的地頁面或資料庫，避免把一次性工作結果誤存成長期知識。

## 工作流程

1. 先讀取工作區標準與既有目的地：
   - 先 fetch `工作控制中心` 與 7/23 工作區架構總綱。
   - 先搜尋相同主題，再決定更新既有頁面或建立新頁面。
   - 每次只處理一個資料庫、一種文件或一個專案。

2. 分類並選擇目的地：
   - 產品知識、SOP、FAQ：`Product Knowledge`。
   - 專案、任務、排程與進度：`Projects`／`Tasks`。
   - 簡報大綱、會議、對外文件與素材：`Docs & Sharing`。
   - 技術設計、API、ADR、測試與發布：`Engineering Specs`。
   - 操作教學、快速開始與公開手冊：`User Manual`。
   - 治理規則、跨平台同步、工作標準、版本彙總或無法歸類內容：`長期知識庫`。

3. 判斷建立或更新：
   - 只有真正的新主題才建立新頁面。
   - 若新對話是修改、延伸、修正或取代既有知識，更新原主題頁面。
   - 只要結論、流程、規則、資料夾結構或操作約定改變，就新增版本紀錄。

4. 只保存可長期使用的內容：
   - 保存最終回答、已確認事實、指令、路徑、決策、假設與下一步。
   - 省略閒聊、失敗的探索分支、重複脈絡與工具雜訊，除非它們對稽核有必要。
   - 保留警告、明確禁止事項與需要人工確認的要求。

5. Notion 工具可用時：
   - 先確認 `a275618631@gmail.com` 與 `Dan Wu's Notion`，再開始任何寫入。
   - 讀取目前工作區標準與目標 Data Source schema；不得沿用快取欄位。
   - 建立新頁前先搜尋或讀取既有頁面，避免重複。
   - 建立資料庫頁面前先讀取目前 Data Source schema，使用現行欄位與選項。
   - 更新既有內容前先 fetch，再用精準替換方式更新。
   - 關聯相關的收件箱項目、知識頁、決策與版本紀錄。

6. Notion 工具不可用時：
   - 不要假裝已經存入 Notion。
   - 使用 `references/notion-templates.md` 產生可直接貼到 Notion 的歸檔稿。
   - 說明歸檔稿應放入哪個資料庫，以及應關聯哪些頁面。

## 必須回報

完成歸檔任務時，回報：

- 目的地資料庫或頁面。
- 實際建立、更新，或僅提供可貼上的歸檔稿。
- 版本變更，如果有。
- 尚待處理事項或需要人工確認的內容。

## 參考資料

當使用者需要資料庫 schema、可貼上的頁面模板或 Notion Hub 設定方式時，讀取 `references/notion-templates.md`。
