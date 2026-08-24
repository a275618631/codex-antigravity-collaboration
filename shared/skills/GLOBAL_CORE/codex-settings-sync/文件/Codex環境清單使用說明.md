# Codex 環境清單與跨電腦重建

本功能補足原有同步策略沒有處理的環境差異：MCP、外部服務、CLI 工具、自訂 skills，以及登入／授權的人工重建步驟。

## 安全邊界

- GitHub `master` 是可攜 Codex 設定的唯一日常來源。
- `config.toml` 匯出仍排除全部 `[mcp_servers.*]`；環境清單不會重新合併進 `config.toml`。
- 不同步 API Key、Token、Cookie、OAuth 憑證、密碼、`.env` 值、Credential Manager、瀏覽器 Session、plugin cache、OS 排程器、session DB 或本機絕對路徑。
- 登入狀態只作盤點參考；目標電腦必須重新登入與驗證。

## 來源電腦匯出

```powershell
.\同步工具\匯出-Codex環境清單.ps1
.\同步工具\測試-Codex環境清單.ps1
```

輸出位於 `環境清單/current/`：

- `codex-environment-manifest.json`：供 Schema、比較腳本與自動檢查使用。
- `codex-environment-manifest.yaml`：供人工閱讀。
- `codex-restore-checklist.md`：逐項安裝、設定、登入與驗證清單。
- `codex-environment-validation.md`：本次盤點的安全界線與驗證記錄。

## 目標電腦比較

先在目標電腦匯出自己的清單，再比較來源與目標：

```powershell
.\同步工具\匯出-Codex環境清單.ps1
.\同步工具\比較-Codex環境清單.ps1 `
  -ReferenceManifest "..\來源電腦\codex-environment-manifest.json" `
  -TargetManifest ".\環境清單\current\codex-environment-manifest.json"
```

比較結果會區分缺少工具、缺少 MCP 設定、需要登入、版本差異、連線驗證失敗、僅單方存在與已完成。版本不會一律要求完全相同；無法判定相容性時保留 `unknown` 或人工確認。

## 套用全部可攜設定

另一台電腦第一次使用時，先登入 GitHub、clone 私有同步 repo，再執行：

```powershell
git switch master
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category all
```

這會套用可攜的 agents、config、execution profiles、skills、workflows、workflow definitions 與同步文件。它不會自動安裝 CLI／MCP、不會建立登入狀態，也不會複製秘密；完成後依環境清單的重建清單逐項處理。

因此，「套用全部 Codex 最新設定」可以讓兩台電腦的可攜 Codex 規則與同步工具一致，但不能保證 MCP 執行檔、外部工具版本、插件安裝、登入狀態或作業系統設定完全相同。

## 失敗處理

若輸出疑似包含秘密，立即停止提交／上傳，只保留檔案位置與欄位，不在終端輸出內容；不要刪除原始 `config.toml`。所有安裝、登入與 OAuth 都必須在目標電腦由本人操作。
