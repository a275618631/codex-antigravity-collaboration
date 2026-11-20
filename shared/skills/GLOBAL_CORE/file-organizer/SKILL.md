---
name: file-organizer
description: 當需要依檔名、metadata、內容線索、專案、日期與版本進行檔案分類、重新命名、去重與搬移規劃時使用。
---

# 檔案整理器

## Trigger

使用者要求「整理檔案」、「分類資料夾」、「重新命名」、「找重複檔」時啟用。

## Input Schema

必填：
- `file_list`

選填：
- `file_metadata`
- `folder_rules`
- `project_context`
- `codex_root`
- `existing_project_folders`
- `existing_repositories`

## Workflow

1. 判斷檔案類型、主題、專案、日期、版本與擁有者。
2. 先解析 `project_key`、專案別名、CODEX 根與既有資料夾；不得把 `My Drive` 根目錄或 CODEX 根目錄當成最終目的地。
3. 優先沿用既有專案資料夾／repository；無法判斷時標記人工審查，不建立新位置。
4. 建議繁體中文檔名，包含專案／功能、用途與建立日期。
5. 偵測重複或近似重複檔，保留原始路徑與 parent ID。
6. 低信心檔案、錯放檔案與可能需要改名／搬移的檔案放入人工審查清單。

## Output Schema

輸出：
- `original_file`
- `project_key`
- `relationship`
- `original_parent_id`
- `target_folder`
- `target_parent_id`
- `new_filename`
- `reason`
- `duplicate_status`
- `action_recommendation`
- `confidence`
- `placement_status`

## Validation

- 不得未經明確同意刪除檔案。
- 必須保留原始路徑。
- 必須確認目標完整路徑位於 `Google Drive/CODEX/<project folder>/`；不能只驗證資料夾名稱。
- 搬移或重新命名前必須取得明確同意；本 Skill 只提出建議，不直接清理歷史檔案。
- 模糊檔案需標記審查，不強行分類。