# Codex × Antigravity 協作架構

> 一份以「平台原生能力優先」為核心的 Agent 協作參考架構；目標是在不新增另一套重型 orchestration framework 的前提下，讓不同 Agent runtime 分工合作。

這個專案目前以 **Codex + Google Antigravity** 為已實作案例，並保留往 **本地模型、隱私分級、跨主機協作** 演進的設計路線。

它**不是**新的 Agent Framework、Scheduler、Message Bus，也不是企業級資安產品。

> **Repo 類型：**這是一份以文件為主的 Reference Architecture + Case Study，整理已運作私人環境中的架構模式、協作契約、狀態與設計決策。它**不是可一鍵安裝的套件**，目前也不提供獨立 runtime。

核心原則只有一句：

> **先用平台原生能力；只有需求真的出現時，才增加協調基礎設施。**

## 為什麼這樣設計

Codex、Antigravity 與本地模型各有不同強項。若把所有能力再包進一個新的大型框架，容易增加重複的 runtime、context、權限設定與維護成本。

因此本架構採：

- **能力導向分工**：依工作類型選 runtime，而不是所有模型都跑一次。
- **有限外部委派**：平台內部可以平行 fan-out；跨平台則限制 hop，避免遞迴爆炸。
- **共用 Skills、薄 Adapter**：可攜方法只維護一份；平台差異才另外適配。
- **漸進式協調**：簡單工作先用 GitHub / Drive；明確 Agent-to-Agent 才升級 MCP / A2A；真的需要 queue / lease / retry 才加入 broker。
- **分散式寫入所有權**：多人可讀、可分析、可 review；衝突 write-set 同一時間只有一個 owner。**目前這是協作政策，不是分散式鎖服務**；Git 類工作依靠 branch/worktree 隔離、optimistic concurrency 與 PR/review/merge gate 處理衝突。
- **隱私導向 routing**：Restricted 資料留本地；可上雲資料只傳最小必要 context。

## 現況

| 能力 | 狀態 |
|---|---|
| Codex ↔ Antigravity Bridge / smoke path | **已實作** |
| Task / Result 協作契約 | **已實作** |
| One-hop / bounded external delegation | **已實作** |
| Read-only、最多兩輪 Debate | **已實作** |
| Codex / Antigravity 原生平行 Agent | **使用平台原生能力** |
| Shared Skills | **部分完成**：canonical source 尚未完全驗證 |
| 本地模型 Bridge | **實驗性** |
| Privacy-aware routing | **規劃中** |
| Multi-host coordination | **探索中** |
| Broker / lease / heartbeat / retry | **探索中，刻意延後** |

公開文件使用保守口徑：**Roadmap 不等於已完成。**

## Agent Topology

一台 PC 或一個平台不是一個 Agent，而是一個可能包含多層 Agent 的 runtime：

```text
Host
└─ Agent Runtime
   ├─ Coordinator
   ├─ Vertical Workers
   ├─ Native Parallel Agents
   └─ External Runtime Delegation
```

因此協作分四種：

1. **Runtime 內平行**：平台原生多 Agent / Subagents。
2. **Runtime 內垂直分工**：Coordinator → 專門 Worker。
3. **跨 Runtime 委派**：Codex ↔ Antigravity。
4. **跨 Host 委派**：未來延伸到不同電腦或本地 GPU 節點。

平台內部可以複雜；跨 Runtime 的委派保持有界。

## 隱私擴展方向

資料依風險分四級：

| 等級 | 預設處理 |
|---|---|
| **Public** | 直接使用 Cloud |
| **Internal** | 本地去識別／最小化後，依政策決定是否上雲 |
| **Sensitive** | 可逆假名化後，依政策決定是否上雲；結果回本地還原 |
| **Restricted** | 只在本地處理 |

這不是「加密後讓 LLM 看密文」。比較精確的概念是：

> **Reversible pseudonymization + local vault**

[Presidio](https://github.com/data-privacy-stack/presidio) 這類成熟專案可作為敏感資訊辨識基礎；本地模型可補充企業特有語意，但不應單獨決定是否允許資料離開本機。

**去敏只能降低暴露，不代表零風險，也不等於企業合規。**

## 協調機制的演進

```text
Stage 1
GitHub / Drive
Shared Workspace

        ↓

Stage 2
MCP / A2A
Explicit Coordination

        ↓

Stage 3
Thin Broker
Queue / State / Lease / Heartbeat / Retry
```

最重要的不是做到 Stage 3，而是：

> **沒有需要，就不要升級。**

## 本專案不打算做什麼

- 不重新實作 Codex / Antigravity 已有的 multi-agent runtime。
- 不為了架構漂亮就新增 Gateway、DB、Vector DB 或 Broker。
- 不允許 Agent 無限制跨平台互相遞迴委派。
- 不宣稱「全自動」、「零風險」或「企業級安全」。
- 不把尚未實作的 Privacy / Multi-host roadmap 寫成現成功能。

## 文件

- [Architecture](docs/ARCHITECTURE.md)
- [Design Principles](docs/DESIGN_PRINCIPLES.md)
- [Privacy and Trust](docs/PRIVACY_AND_TRUST.md)
- [Status and Roadmap](docs/STATUS_AND_ROADMAP.md)
- [References](docs/REFERENCES.md)

## 本機雙向 MCP Bridge（已驗證）

本專案現在包含一個僅限本機使用的 Codex × Antigravity MCP bridge：

- [Bridge 程式與測試](local_bridge/)
- 兩個桌面 runtime 各自以 stdio 啟動 bridge process。
- 兩端透過同一個鎖定的 JSONL mailbox 傳遞 bounded text message。
- bridge 不執行訊息中的指令，也不包含 OAuth、PAT 或其他憑證。
- 這是 pull-based transport；模型需要呼叫 `bridge_receive`，不會自動插入另一個已執行中的回合。

重啟後已完成 Codex → Antigravity → Codex 的實際 smoke test。完整的本機設定與安全邊界請見 [local bridge README](local_bridge/README.md)。

## 定位

這個專案最適合被理解為：

> **Reference architecture + working two-runtime case study**

它的價值不在發明一個新 Agent Framework，而在說明：

> **如何把今天已存在的 Agent runtime、Skills、Bridge 與共享工作區，用較少的額外複雜度組合起來。**

## License

MIT License，詳見 [LICENSE](LICENSE)。
