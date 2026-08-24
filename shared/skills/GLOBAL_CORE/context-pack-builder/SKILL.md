---
name: context-pack-builder
description: 當需要把長對話、專案歷史、研究資料或零散筆記濃縮成可交接給 Codex、其他 AI Agent 或人類接手的 Context Pack 時使用。
---

# 上下文包建立器

## Trigger

使用者要求「整理上下文」、「交接給 Codex」、「做 context pack」、「把長對話濃縮」時啟用。

## Input Schema

必填：
- `raw_context`

選填：
- `target_agent`
- `project_goal`
- `constraints`

## Workflow

1. 擷取使用者背景、專案背景與目前目標。
2. 彙整已做決策、目前狀態與下一步。
3. 保留限制、禁止事項與重要假設。
4. 移除聊天雜訊、重複討論與暫時性內容。
5. 列出開放問題與需要人工確認的事項。

## Output Schema

輸出：
- `project`
- `user_profile`
- `goals`
- `decisions`
- `constraints`
- `current_state`
- `next_steps`
- `open_questions`

## Validation

- 不新增來源沒有支持的假設。
- 必須保留明確限制與禁止事項。
- 下一個 Agent 應能不重讀全文就接手。

## KPI

- 目標省時：90%。
- 目標正確率：90%。
- 成功指標：接手者可直接繼續工作，少量追問即可。
