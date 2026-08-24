---
name: artifact-storage-policy
description: 管理 Codex 交付物的專案識別、Google Drive／GitHub 路由、檔名、儲存位置與回讀驗證；凡工作報告、外部保存、交付成果或新 repository 選擇涉及遠端儲存時使用。
---

# 交付物儲存政策

## 目的

先確認專案、目的地與既有位置，再建立或寫入外部交付物。此 Skill 是工作報告、Project Delivery Orchestrator、Google Drive 保存與 GitHub repository 選擇的共同政策；不負責搬移歷史檔案，也不取代平台專用工具。

## 觸發條件

- 產出或保存工作報告、設定改版、稽核結果或其他正式成果。
- 使用者要求保存到 Google Drive、GitHub，或同時保存到兩者。
- 需要選擇新 repository、專案資料夾或交付目錄。
- 需要判斷是否沿用既有專案、分支或版本。

## Input Schema

```yaml
storage_request:
  task: ""
  project_key: ""
  aliases: []
  destinations: [google_drive|github]
  artifacts: [{purpose: "", filename: ""}]
  date: "YYYY-MM-DD"
  user_authorized_write: false
```

## Resolution Workflow

1. 搜尋既有專案名稱、別名、近期交付物、Drive 資料夾與 GitHub repository；不得只依任務標題猜測。
2. 確認 Google Drive 的 `CODEX` 根資料夾 ID、專案資料夾 ID、完整路徑與寫入權限；Drive 根目錄或 `My Drive` 根目錄不是合格目的地。
3. 確認 GitHub owner、repository、目前分支與既有相關 repository；同一專案優先沿用既有 repository，不因日期或單一任務建立新 repo。
4. 判斷關係：`new`、`continuation`、`branch` 或 `related`。若無法判斷，標記 `needs_review`，不得自行建立新位置。
5. 檔名使用繁體中文，至少包含專案／功能、用途與建立日期；避免只用 `report.md`、`final.docx`、`output.txt`。
6. 寫入後必須讀回 metadata／內容，核對實際 parent、完整路徑、檔名、URL、MIME／大小與 repository／分支。
7. 發現錯放、重複、檔名不合規或無法回讀時，狀態為 `needs_repair` 或 `failed`，不得報告為完成。移動、重新命名、覆蓋、刪除或權限變更需另有明確授權。

## Output Schema

```yaml
routing:
  task: ""
  date: ""
  lane: fast|slow
  workflow: project-delivery-orchestrator
  skills_invoked: []
  agents_invoked: []
storage:
  project_key: ""
  relationship: new|continuation|branch|related|needs_review
  platform: google_drive|github|both
  drive:
    expected_root: CODEX
    expected_project_folder: ""
    expected_parent_id: ""
    actual_parent_id: ""
    actual_path: ""
    root_leak_detected: false
    reused_existing_project_folder: false
    duplicate_project_folders_found: []
    top_folder_date_before: ""
    top_folder_date_after: ""
    placement_verified: false
  github:
    expected_repo: ""
    actual_repo: ""
    reused_existing_repo: false
    new_repo_reason: ""
    duplicate_or_related_repos_found: []
    placement_verified: false
artifacts:
  - purpose: ""
    expected_filename: ""
    actual_filename: ""
    local_path: ""
    url: ""
    storage_path: ""
    parent_id: ""
    repository: ""
    branch: ""
    status: created|updated|not_saved|needs_repair|failed
    verification: ""
    created_at: ""
    filename_language: zh-TW
    project_in_filename: false
    purpose_in_filename: false
    creation_date_in_filename: false
    naming_verified: false
validations:
  routing_ledger: pass|fail|not_applicable
  content: pass|fail|not_run
  format: pass|fail|not_run
  remote_exists: pass|fail|not_run
  permission: pass|fail|not_run
  storage_location: pass|fail|not_run
  project_reuse: pass|fail|not_run
  filename_policy: pass|fail|not_run
  top_folder_date: pass|fail|not_run
unresolved: []
```

## 交付物索引與摘要錨點

- 每次產出、修改、上傳或寄送檔案，都要建立可直接放入最終回覆與工作報告的「交付物索引」；每個檔案一列，不得只列來源或工具名稱。
- 索引至少包含：檔名、用途、本機完整絕對路徑、實際 URL、Drive 完整路徑／parent ID 或 GitHub repository／branch、狀態與驗證結果。
- 本機不存在、尚未保存或無法驗證的欄位必須明確標示 `不適用`、`尚未保存` 或 `未驗證`；不得推測路徑、組合未回讀的 URL 或把來源資料當成交付物。
- 長任務、上下文壓縮或交接摘要時，優先保留這份索引與未完成項目。若平台摘要 UI 只顯示來源，主要回覆仍必須保留完整索引。

## Date and historical-file rules

- 新交付物的檔名使用實際建立日期。
- 同一專案的既有頂層資料夾應沿用；若需要更新頂層日期，先提供舊名／新名／影響範圍並取得明確核准。
- 本 Skill 不自動搬移、重新命名、刪除或覆蓋歷史檔案；錯放項目只列為候選清單，另案處理。
- 新資料夾只有在已確認 `CODEX` 根、專案不存在、關係為 `new` 且使用者授權寫入時才能建立。

## Fail-closed conditions

任何一項無法確認時停止遠端寫入：`CODEX` 根、專案識別、目標 parent、repository、沿用／新建關係、寫入權限、寫入後 metadata／URL／內容回讀。

## Audit fields

每次交付至少保留：實際使用的 Skill／Workflow／Agent、Drive 完整路徑與 parent ID、GitHub owner/repository/branch、每個 artifact 的檔名與 URL、四層驗證結果、未解決項目。
