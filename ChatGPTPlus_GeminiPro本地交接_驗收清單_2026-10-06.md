# ChatGPT Plus／Gemini AI Pro 本地交接驗收清單（2026-10-06）

## A. 範圍與平台

- [x] 只把 ChatGPT Plus Web／Mobile 與 Gemini AI Pro Web／Mobile 列為對話入口。
- [x] 不把 Business、Enterprise、Cloud Work、MCP 或 Custom Apps 當必要依賴。
- [x] 清楚標示一次人工 GitHub 開單確認，不宣稱完全原生自動化。
- [x] macOS 未經實機驗證時保持 `NOT VERIFIED`。

## B. Task Brief 與開單

- [x] ChatGPT／Gemini 使用同一 canonical task body。
- [x] 支援 `Origin Surface`、`Client`、`Parent Task ID`、`Revision` metadata。
- [x] 不保存 conversation URL、cookie、session ID 或整段聊天。
- [x] 預填 URL 正確編碼 title、body、label，且不含 Token 或本機路徑。
- [x] URL／body 過長時 fail closed，提示改用手動貼上。
- [x] 舊格式 Issue 仍可解析與執行。

## C. 核准與安全

- [x] 未授權 actor／approver 拒絕。
- [x] Repo、branch、scope、host 不在 allowlist 時拒絕。
- [x] 核准後內容更改時拒絕。
- [x] nonce 與 Task ID 重複時不再次修改。
- [x] Issue、progress、result、日誌、commit 不洩漏 Token、stdout、stderr 或私密絕對路徑。

## D. Receiver 執行

- [x] 前景輪詢可由 marker 正常啟動與停止。
- [x] 單一 lock 防止同主機雙重 active writer。
- [x] API 暫時錯誤採上限 backoff，不形成緊密重試。
- [x] stale Running／Validating／Reporting 可安全對帳為 Blocked。
- [x] 不自動安裝或啟用常駐服務。

## E. 進度、結果與後續討論

- [x] 每個 Issue 只建立一則 Receiver progress comment。
- [x] progress 至少顯示 Queued、Running、Validating、Reporting、Terminal。
- [x] Result Packet 是最小化摘要，適合貼回手機對話。
- [x] child Issue 可追溯 parent 與 revision，並重新核准。
- [x] Failed／Blocked／Cancelled 保留可復原紀錄，不自動刪除 worktree。

## F. 自動測試與靜態驗證

- [x] 原有 24 項測試無回歸。
- [x] 新增 metadata、URL、loop、progress 去重、取消／復原測試。
- [x] 完整測試套件 PASS（59 PASS／0 FAIL：58 handoff／CLI + 1 two-process bridge）。
- [x] `git diff --check` PASS。
- [x] Secret／本機路徑掃描 PASS。
- [x] 文件列示的狀態、commit、PR 與實際結果一致。

## G. 實機／遠端驗收

- [x] Windows 本機自動測試：PASS（59 項）；新增版本真實 GitHub E2E 未驗證。
- [x] 限定唯讀 Antigravity CLI nonce 接力：PASS（2026-10-22）；直接桌面 MCP mailbox 路徑尚未重新驗證。
- [ ] T7 OS 級跨專案寫入隔離：FAIL；不得啟用無人值守／跨 Repo 寫入，需人工完成主機 ACL 修正與驗收。
- [ ] ChatGPT Plus Web：PASS／FAIL／NOT VERIFIED。
- [ ] ChatGPT Plus Mobile：PASS／FAIL／NOT VERIFIED。
- [ ] Gemini AI Pro Web：PASS／FAIL／NOT VERIFIED。
- [ ] Gemini AI Pro Mobile：PASS／FAIL／NOT VERIFIED。
- [ ] macOS：PASS／FAIL／NOT VERIFIED。
- [x] PR #9 已在 2026-10-22 經使用者明確核准後合併。
- [ ] PR #10（本次狀態與證據文件修訂）已 Push，待審；未授權自動合併。
