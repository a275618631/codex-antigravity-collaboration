---
name: task-router
description: 任務模糊、同時有兩個以上合理執行路徑、需要判斷是否啟用 skill，或需要把使用者需求分流成最小執行路徑時使用。特別適用於「幫我規劃怎麼做」、「這要用哪個 skill」、「先判斷流程」；已有明確專用 skill 的單一路徑任務不使用。
---

# 任務路由器

## 核心原則

只做分流與最小路徑選擇，不替專用 skill 執行完整任務。目標是降低誤觸發、少讀不必要內容、減少來回修改。

## 流程

1. 先判斷任務類型：程式碼、文件、研究、資料、視覺化、同步、提示詞移植、skill 優化、一般問答。
2. 檢查是否有明確禁止事項、敏感資料、不可逆動作或需要最新查證。
3. 若任務只需一個 skill，指定該 skill。
4. 若任務跨多步，最多先選 1-3 個 skill，依順序使用。
5. 若資訊不足，提出 1-3 個精準問題；若可合理假設，列出假設後繼續。
6. 若已有明確專用 skill 且路徑沒有歧義，直接交給專用 skill，不再由本 Skill 介入。

## 輸出格式

```text
建議路由：
- 主要 skill：...
- 輔助 skill：...
- 不使用的 skill：...（原因）

執行順序：
1. ...
2. ...
3. ...

需要確認：...
```

## 判斷表

| 任務 | 優先 skill |
|---|---|
| 複雜流程、比較、架構圖 | visual-response |
| 新增或修改 skill | skill-evaluator |
| 完成前收尾格式 | output-contract |
| 規則移植到其他 AI | prompt-portability |
| Codex 設定、skills、同步文件 | codex-settings-sync |
| 研究、文章、多來源比較 | research-synthesizer 或 web-research-citation |
| 程式碼修改 | code-generation-agent |
| PR / diff 審查 | pr-review-agent |
