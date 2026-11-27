---
name: codex-settings-sync
description: 管理、備份、匯出、同步、還原與檢查 Codex 專屬設定（Thin AGENTS.md、default.rules、config.toml、execution profiles）與同步工具。支援「同步設定」「更新 Codex 設定」「套用到另一台 Mac」「完成後同步」等語意。
---

# Codex 設定同步

## 1. 權威歸屬 (Canonical Ownership)

- **Shared Artifacts 權威庫**：`a275618631/codex-antigravity-collaboration`（擁有 Shared Protocol、13 項 Global Core Skills 與 Canonical Registry）。
- **Codex-specific Artifacts 權威庫**：`a275618631/codex-settings-sync`（擁有 Codex Thin Adapter、Codex 權限規則 `default.rules`、可攜設定與同步工具）。
- **Antigravity-specific Artifacts 權威庫**：`a275618631/antigravity-config`（擁有 Antigravity Thin Adapter 與專屬外掛設定）。

## 2. 核心同步規則

1. 修改 Codex 設定、使用者技能或同步工具前，先於本地執行含時間戳快照的既有備份；全部修改完成並通過靜態檢查後再執行一次最終匯出。
2. GitHub canonical repository 是日常來源；Google Drive 僅作備份與災難復原，不得在日常套用時混合覆蓋。
3. 不同步內建 `.system` skills、plugin cache、credentials、tokens、OAuth/auth state、OS schedulers、local paths、session DBs、temp files。專案進度與交接不是設定同步項目；跨裝置接續沿用既有 Project Current/README/SSOT 或 context-pack-builder，不放進設定包。
4. 對每個 manifest artifact，先確認 owner 的最新 Canonical commit/hash，再與兩端最近共同採用的基準、local checkout（包含 dirty diff）及本機平台 Installed target 比較；文字換行正規化為 LF 後比 hash，回報 `MATCH`、`DRIFT`、`MISSING` 或 `UNVERIFIED`。
5. 共同基準須能由既有 Git 歷史、上次共同採用的 Manifest/commit 或同步紀錄確認；無法確認時標示 `UNVERIFIED`，不得自動覆寫。最新 Canonical 優先於較舊的 local/Installed 副本，絕不以舊本機內容覆蓋較新的 Canonical；local-only 修改須保留並逐檔審查/合併。**Canonical 13 項 `GLOBAL_CORE` Skills 與 Thin Adapter 嚴禁使用舊式逐行文字聯集（`--union`）混合新舊規則**，應採完整 Canonical 檔案替換並保留同步前去敏備份。
6. 保留 Windows/Mac 與 Codex/Antigravity 的平台/Runtime 專屬設定；跨 Runtime 只同步 Manifest 明確標記為 shared/portable 的項目，不把某平台 adapter 複製到另一 Runtime。使用既有 exporter/備份能力；若該平台無法執行 exporter，以原生檔案操作備份明確列出的目標檔。只有取得授權後才同步；完成後回讀並驗證每個實際寫入檔案的內容/hash。

## 3. 平台與跨 Runtime 載入驗收要求

1. **前置就緒與跨倉順序**：所有相依 PR 合併且各 owner 預設分支 LF Hash 與 `CANONICAL_MANIFEST.json` 回讀一致前，不執行正式裝置同步；共用工具決策與可攜工具規則依循既有 `portable-ai-agent-environment` 納管入口。
2. **Codex 本機驗收**：同步 `$HOME/.agents/` 與 `~/.codex/AGENTS.md` 後，於該裝置 `$CODEX_HOME/config.toml` **依實際與 `~/.agents/skills/` 重名的項目重新產生 `[[skills.config]] enabled = false`**（嚴禁跨機複製 Windows 絕對路徑，不刪舊檔、不修改 `.system`），並重開 Session 或執行 `codex debug prompt-input` 驗證模型可見目錄確實消除重複且無誤停用必要技能。
3. **Antigravity 本機驗收**：核對實際 CLI 版本與 Global Loader 路徑（`~/.gemini/config/GEMINI.md` 與 `~/.gemini/config/skills/`），同步後必須將 13 項 `GLOBAL_CORE` Skills 與其 `references/` **投影覆寫至 `~/.gemini/config/skills/`**（不可僅存於 `~/.agents/skills/`），重開 Session 確認 `<RULE[user_global]>` 與全部共用技能真正進入模型可見清單、維持原生 Lazy Loading，並依各裝置授權獨立核對 `config.json`（Sandbox / EAGER / 白名單）。
4. **跨裝置一句話接續**：當使用者於任一電腦下達「依照最新正式 Canonical Manifest，同步並驗證本機 Codex／Antigravity 設定。」時，按上述四向比對、授權備份、投影與載入驗收程序執行；無法存取之遠端電腦標示 `UNVERIFIED` 並附直接執行入口。