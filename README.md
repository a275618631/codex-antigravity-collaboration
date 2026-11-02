# Codex × Antigravity｜讓兩個 AI 開發環境有條理地協作

Codex 和 Antigravity 都能協助寫程式，但當兩套工具一起處理同一個專案，真正需要解決的是：**誰負責哪件事、可以修改哪些檔案、完成後要怎麼交接與驗收？**

我以這兩個開發環境建立一套輕量協作方式：共用 Task／Result 契約、限制跨平台委派次數，透過 Git 分支與 worktree 分開修改，並實作本地 MCP Bridge 傳送訊息。重點是保留工具本身的能力，不另外建一套龐大的多 Agent 管理框架。

[繁體中文技術說明](README.zh-TW.md) · [架構展示網站](https://a275618631.github.io/codex-antigravity-collaboration/)

## 核心設計

- **任務格式統一**：工作目標、讀寫範圍、驗收條件和結果使用同一套 Task／Result 格式。
- **依能力分工**：Codex 與 Antigravity 各自使用原生工具，只把需要的工作交給對方。
- **委派有限次數**：限制跨 Runtime 反覆轉交，避免 Agent 之間無止盡地互相呼叫。
- **協作時不互相覆寫**：以 branch、worktree 和 PR 分離修改，再交由人員檢查。
- **本地 MCP Bridge**：使用 JSONL mailbox 與跨平台檔案鎖，在 Windows 與其他系統交換訊息。
- **必要的人工核准**：高風險寫入由明確的審核流程決定，不把 Prompt 當作系統權限。

## 一次工作怎麼進行

```text
提出需求與驗收條件
          ↓
指定合適的 Agent Runtime
          ↓
在限定的工作區執行、測試
          ↓
回傳修改結果與驗證紀錄
          ↓
人工審查 Git diff / PR
```

## 做過哪些驗證

- 已實作 Task／Result 契約、有限委派與本地橋接程式。
- Windows 本地 Bridge 曾通過雙程序與相關自動化測試；2026-10-20 有一次受限的跨 Runtime 唯讀交接通過紀錄。
- 2026-10-22 的跨 Runtime 重測逾時；桌面端完整即時雙向交接尚未列為穩定可用功能。跨專案無人值守寫入也還不具備作業系統層級的完整隔離。

以上差異可在[測試證據](LIVE_HANDOFF_EVIDENCE_20261020.md)與[技術說明](README.zh-TW.md)核對。

## 從程式與文件開始

- [本地 MCP Bridge](local_bridge/README.md)：訊息格式、啟動方式與本地測試。
- [GitHub → 本地 Codex 接單工具](github_handoff/README_GITHUB_HANDOFF_20260929.md)：Issue 讀取、核准與本機執行。
- [架構設計](docs/ARCHITECTURE.md)：角色分工、邊界與協作方式。
- [本機操作手冊](GitHub本地Codex自動交接_使用手冊_20260929.md)：從 Issue 到工作結果的流程。

MIT License。
