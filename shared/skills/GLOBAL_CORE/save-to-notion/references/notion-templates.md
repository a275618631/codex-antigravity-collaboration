# Save To Notion 模板

以下模板用於使用者的 Notion Hub：

`https://app.notion.com/p/440e62ad3eb382c4977201bf8ba9b217`

## 目前實際儲存目的地

- Notion 帳號：`a275618631@gmail.com`
- Workspace：`Dan Wu's Notion`
- 入口頁：`工作控制中心`
- 主要資料庫：`長期知識庫`
- Data Source：`collection://d26e62ad-3eb3-8226-a4b8-07e35af67f7f`

工作區架構總綱：

`https://app.notion.com/p/3a6e62ad3eb3811fb01ccc6b41c34d5d`

新內容應依類型優先放入既有專用資料庫：Product Knowledge、Projects、Tasks、Docs & Sharing、Engineering Specs 或 User Manual；只有治理規則、跨平台同步、工作標準或無專用資料庫的內容才放入 `長期知識庫`。`Docs & Sharing` 暫時合併簡報、文件與素材索引，避免重複建立資料庫。

舊版四資料庫模板僅供歷史參考，不再作為預設建立目標。工作控制中心的實際入口與私人區以 Notion 現況為準。

所有新的 Notion 歸檔、工作報告與知識頁，預設指向上述 Data Source。建立或更新前必須重新讀取 schema；不要使用舊快取欄位或舊 Hub URL。舊有四資料庫模板以下僅作歷史參考，除非使用者另行指定，不建立新的資料庫。

## Hub 版面

將下列內容貼到 Hub 頁面：

```md
# Codex 知識 Hub

## 資料庫

- Codex 問題收件箱
- Codex 知識庫
- Codex 決策紀錄
- Codex 版本進展

## 運作規則

- 不保存完整流水帳，只保存可復用的結論、步驟、決策與待辦。
- 新主題建立新頁；既有主題更新原頁並新增版本紀錄。
- 重要選擇同步寫入決策紀錄。
- 每次更新需包含版本、變更摘要、變更原因、目前狀態。
- Notion 工具不可用時，先輸出可貼上的歸檔稿。
```

## 資料庫 1：Codex 問題收件箱

用途：追蹤每個應沉澱為知識、決策、任務或版本更新的問題。

欄位：

| 欄位 | 類型 | 選項 / 備註 |
| --- | --- | --- |
| 問題 | Title | 原始問題或整理後的問題 |
| 類型 | Select | 設定, 教學, 決策, 任務, FAQ, 流程, 專案 |
| 狀態 | Select | Inbox, 整理中, 已歸檔, 需確認, 放棄 |
| 主題 | Multi-select | Codex, Notion, Skills, 專案管理, 自動化, 資料整理 |
| 優先級 | Select | High, Medium, Low |
| 來源 | Select | Codex 對話, 手動輸入, 文件, 其他 |
| 提問日期 | Date | 提問日期 |
| 關聯知識 | Relation | Codex 知識庫 |
| 關聯決策 | Relation | Codex 決策紀錄 |
| 關聯版本 | Relation | Codex 版本進展 |
| 待確認事項 | Text | 需要人工確認或阻塞事項 |

頁面模板：

```md
## 原始問題

## 問題摘要

## 處理結果

## 分類理由

## 需要歸檔到

## 待確認事項
```

## 資料庫 2：Codex 知識庫

用途：保存穩定、可重用的知識、教學、FAQ、設定規則與流程文件。

欄位：

| 欄位 | 類型 | 選項 / 備註 |
| --- | --- | --- |
| 標題 | Title | 知識頁標題 |
| 類型 | Select | How-To, Concept, Reference, FAQ, Workflow, Setup |
| 分類 | Select | Codex, Notion, Project, Automation, Skills, Data, General |
| 標籤 | Multi-select | 彈性標籤 |
| 狀態 | Select | Draft, Active, Needs Review, Deprecated |
| 目前版本 | Text | v0.1、v1.0 等 |
| 最後檢視 | Date | 檢視日期 |
| 關聯問題 | Relation | Codex 問題收件箱 |
| 關聯決策 | Relation | Codex 決策紀錄 |
| 關聯版本 | Relation | Codex 版本進展 |

頁面模板：

```md
## 摘要

## 適用情境

## 最終結論

## 操作步驟

## 重要路徑與連結

## 注意事項

## 相關決策

## 版本紀錄

## 待確認事項
```

## 資料庫 3：Codex 決策紀錄

用途：記錄重要操作選擇以及做出該選擇的原因。

欄位：

| 欄位 | 類型 | 選項 / 備註 |
| --- | --- | --- |
| 決策 | Title | 決策內容 |
| 日期 | Date | Decision date |
| 狀態 | Select | Proposed, Accepted, Superseded, Deprecated |
| 領域 | Select | Codex, Notion, Project, Automation, Data, Skills |
| 影響 | Select | High, Medium, Low |
| 決策者 | People/Text | 使用者或團隊 |
| 關聯知識 | Relation | Codex 知識庫 |
| 關聯版本 | Relation | Codex 版本進展 |

頁面模板：

```md
## 背景

## 決策

## 理由

## 考慮過的替代方案

## 影響與後果

## 執行方式

## 何時需要重新檢視
```

## 資料庫 4：Codex 版本進展

用途：追蹤工作流程、知識頁、規則與決策的動態變更。

欄位：

| 欄位 | 類型 | 選項 / 備註 |
| --- | --- | --- |
| 版本項目 | Title | 版本紀錄標題 |
| 關聯頁面 | Relation | Codex 知識庫 |
| 關聯決策 | Relation | Codex 決策紀錄 |
| 版本 | Text | v0.1、v0.2、v1.0 |
| 變更類型 | Select | 新增, 修正, 廢棄, 合併, 拆分 |
| 日期 | Date | Change date |
| 狀態 | Select | Draft, Active, Superseded |
| 變更摘要 | Text | 簡短摘要 |
| 變更原因 | Text | 變更原因 |

頁面模板：

```md
## 版本

## 變更摘要

## 變更原因

## 變更前

## 變更後

## 影響範圍

## 待確認事項
```

## 歸檔稿格式

Notion 工具不可用時，輸出下列格式：

```md
目的地資料庫：
建立或更新：
建議標題：
分類：
狀態：
版本：

## 摘要

## 最終結論

## 操作步驟 / 工作流程

## 決策與理由

## 版本變更

## 相關連結 / 路徑

## 待確認事項
```
