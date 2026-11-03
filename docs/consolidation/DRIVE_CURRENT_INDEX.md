# 本地多 Agent 協作系統目前索引

> 2026-10-15 歷史索引；目前進度請以專案 Drive CURRENT 與 2026-10-30 交接文件為準。

這個索引對應 canonical Drive folder `1CZ3N6T8BlvcL2ocybv3Op8oUF7EgTc4s` 與 canonical repository `a275618631/codex-antigravity-collaboration`。GitHub 是工程狀態來源；這個 Drive 索引只保留人可讀的關係、現況與交接資訊。

## 模組

- Core Collaboration：Task / Result Packet、bounded delegation、Shared Skills。
- GitHub Local Handoff：同一系統的 module，不是另一個專案。
- Agent Orchestration：Parent Goal、task graph、state machine、auto resume。
- Agent Adapters：Codex、Antigravity、Future Agent contract。
- Routing：Manual / Deterministic / Capability；System One 僅實驗。
- Safety：`agent-tool-policy-engine` 為外部連結元件，維持獨立 repo。

## 目前限制

現有控制平面通過 mock 驗證；跨 Runtime 真實 E2E、私有 GitHub inbox、self-hosted runner 和 Antigravity runtime 授權仍需獨立驗證。不得把 mock 結果視為 live evidence。

完整明細見同一資料夾內的 `PROJECT_TREE.md`、`SYSTEM_RELATIONSHIPS.yaml` 與 `PROJECT_REGISTRY.yaml`。
