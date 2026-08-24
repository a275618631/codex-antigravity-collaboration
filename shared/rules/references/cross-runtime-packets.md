# Cross-Runtime Communication Packets Specification

當且僅當發生跨 Runtime 委派 (Cross-Runtime Delegation) 時，依本規範格式進行通訊。

## 1. Task Packet (任務封包)

```yaml
task_packet:
  task_id: "<UUID or timestamped string>"
  initiator: "Antigravity | Codex"
  target: "Codex | Antigravity"
  hop_count: 1  # 必須 <= 1
  collaboration_mode: "Vertical | Debate | Review | Implementation"
  objective: "<清楚具體的任務目標>"
  context:
    sources_of_truth: ["<檔案路徑或 URL>"]
    background: "<必要背景資訊>"
  lane: "fast | standard | deep"
  scope:
    read_scope: ["<允許讀取之路徑清單>"]
    write_scope: ["<允許寫入之路徑清單，唯讀任務為空>"]
  constraints:
    - "<不可更動之檔案或邊界>"
    - "<禁止行為 (例如禁止 force push、禁止外流 secret)>"
  validation_criteria:
    - "<驗證通過標準，如測試指令、Lint、回讀檢查>"
  expected_output_format: "Result Packet"
```

## 2. Result Packet (結果封包)

```yaml
result_packet:
  task_id: "<對應之 task_id>"
  responder: "Codex | Antigravity"
  status: "SUCCESS | PARTIAL | FAILED | BLOCKED"
  summary: "<結論性成果摘要>"
  changes:
    modified_files: ["<修改檔案路徑>"]
    created_files: ["<新增檔案路徑>"]
    deleted_files: ["<刪除檔案路徑>"]
  evidence:
    - "<具體執行紀錄、指令輸出或回讀證明>"
  validation_results:
    tests_run: ["<執行的測試名稱或指令>"]
    passed: true | false
    details: "<測試輸出與狀態>"
  risks_and_limitations:
    - "<已知限制或潛在風險>"
  remaining_work:
    - "<尚未完成或待後續跟進之事項>"
  recommendation: "<下一步建議行動>"
```

## 3. Read-Only Debate Contract (唯讀辯論協議)

針對重大架構或技術選型，雙方 Reviewer 進行最多 **2 輪** 唯讀交叉評估：
- 格式包含：`主張 (Claim)`、`證據 (Evidence)`、`風險 (Risk)`、`建議 (Recommendation)`。
- 辯論期間**嚴禁修改任何正式檔案**。
- 辯論結束後由主控者裁決，並指定單一 Implementer 執行。
