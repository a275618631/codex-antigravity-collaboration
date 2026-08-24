---
name: checklist-validator
description: 當需要在寄出、發布、合併、部署、歸檔或交接前，對文件、流程、程式碼變更或分析成果做內容、風險與 readiness 最終檢查時使用；本 Skill 不負責最後回報格式。
---

# 檢查清單驗證器

## Trigger

使用者要求「幫我檢查」、「交付前驗證」、「確認有沒有漏」、「ready check」時啟用。

## Input Schema

必填：
- `artifact`
- `checklist_type`

選填：
- `custom_rules`
- `risk_level`
- `audience`
- `storage_ledger`
- `storage_ledger`

## Workflow

1. 判斷 artifact 類型與交付風險。
2. 選擇對應檢查清單。
3. 每項標記 pass、fail 或 needs review。
4. 列出必修項目。
5. 產生 readiness score 與核准建議。
6. 若涉及外部保存，檢查 routing ledger、CODEX 根／parent、專案沿用、檔名政策、GitHub repository／branch 與寫入後回讀。
6. 若涉及外部保存，檢查 routing ledger、CODEX 根／parent、專案沿用、檔名政策、GitHub repository／branch 與寫入後回讀。

## Output Schema

輸出：
- `checklist`
- `passed`
- `failed`
- `needs_review`
- `required_fixes`
- `readiness_score`
- `approval_needed`

## Validation

- 每個 failure 必須有明確原因。
- 高風險項目需要人工核准。
- 缺資料不可默默通過。
- Drive 交付必須同時通過：`storage_location`、`project_reuse`、`filename_policy`、`remote_exists`；缺任一項即 `needs_review` 或 `fail`。
- GitHub 交付必須確認 owner、repository、branch、實際檔案位置與 commit／遠端存在性；不可用本機路徑代替。
- Drive 交付必須同時通過：`storage_location`、`project_reuse`、`filename_policy`、`remote_exists`；缺任一項即 `needs_review` 或 `fail`。
- GitHub 交付必須確認 owner、repository、branch、實際檔案位置與 commit／遠端存在性；不可用本機路徑代替。
- 本 Skill 負責判斷成果是否可交付；完成後的修改清單、測試結果與待確認事項格式由 `output-contract` 處理。

## KPI

- 目標省時：80-90%。
- 目標正確率：90%。
- 成功指標：交付前漏項明顯降低。
