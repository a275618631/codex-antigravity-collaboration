---
name: codex-settings-sync
description: 管理、備份、匯出、同步、還原與檢查 Codex 專屬設定（Thin AGENTS.md、default.rules、config.toml、execution profiles）與同步工具。支援「同步設定」「更新 Codex 設定」「套用到另一台 Mac」「完成後同步」等語意。
---

# Codex 設定同步

## 1. 權威歸屬 (Canonical Ownership)

- **Shared Artifacts 權威庫**：`a275618631/codex-antigravity-collaboration`（擁有 Shared Protocol、16 項 Global Core Skills 與 Canonical Registry）。
- **Codex-specific Artifacts 權威庫**：`a275618631/codex-settings-sync`（擁有 Codex Thin Adapter、Codex 權限規則 `default.rules`、可攜設定與同步工具）。
- **Antigravity-specific Artifacts 權威庫**：`a275618631/antigravity-config`（擁有 Antigravity Thin Adapter 與專屬外掛設定）。

## 2. 核心同步規則

1. 修改 Codex 設定、使用者技能或同步工具前，先於本地執行含時間戳快照的既有備份；全部修改完成並通過靜態檢查後再執行一次最終匯出。
2. GitHub `migration/*` / `master` 是設定同步的來源庫；Google Drive 僅作備份與災難復原，不得在日常套用時與 GitHub 混合覆蓋。
3. 不同步內建 `.system` skills、plugin cache、credentials、tokens、OAuth/auth state、OS schedulers、local paths、session DBs、temp files。
4. 另一台電腦套用前，先執行本地 vs 遠端 Diff 比對，保留目標電腦專有能力，不進行盲目覆蓋。
