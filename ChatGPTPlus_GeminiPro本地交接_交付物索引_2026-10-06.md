# ChatGPT Plus／Gemini AI Pro 本地交接交付物索引（2026-10-06）

共同存放資訊：

- 本機根目錄：`C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration`
- Repository／branch：`a275618631/codex-antigravity-collaboration`／`codex/github-local-handoff-mvp-20260929`
- Existing Draft PR：<https://github.com/a275618631/codex-antigravity-collaboration/pull/8>
- 本輪尚未 push，因此以下遠端 URL 均標記為「PR #8 尚未包含本輪變更」。
- Google Drive parent ID／雲端 URL：本工作階段無法回讀，標記為未驗證；本機檔案已實際回讀。

| 檔名 | 用途 | 本機完整路徑 | 遠端 URL | 存放位置 | 狀態 | 驗證 |
|---|---|---|---|---|---|---|
| `.github/ISSUE_TEMPLATE/codex-local-task.yml` | Issue Form metadata | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\.github\ISSUE_TEMPLATE\codex-local-task.yml` | PR #8 尚未包含本輪變更 | repo／branch 如上 | 本機已更新 | 50 tests／diff check PASS |
| `github_handoff/core.py` | Receiver 核心與安全控制 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\core.py` | 同上 | repo／branch如上 | 本機已更新 | 50 tests／compileall／independent review PASS |
| `github_handoff/cli.py` | watch、lock、issue-link CLI | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\cli.py` | 同上 | repo／branch如上 | 本機已更新 | lifecycle tests PASS |
| `github_handoff/config.example.json` | 新輪詢設定範例 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\config.example.json` | 同上 | repo／branch如上 | 本機已更新 | JSON parse PASS |
| `github_handoff/task.schema.json` | Task metadata schema | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\task.schema.json` | 同上 | repo／branch如上 | 本機已更新 | JSON parse PASS |
| `github_handoff/result.schema.json` | Result transport state schema | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\result.schema.json` | 同上 | repo／branch如上 | 本機已更新 | JSON parse／schema tests PASS |
| `tests/test_github_handoff.py` | 核心與安全回歸測試 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\tests\test_github_handoff.py` | 同上 | repo／branch如上 | 本機已更新 | PASS |
| `tests/test_github_handoff_cli.py` | Lifecycle／URL 測試 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\tests\test_github_handoff_cli.py` | 同上 | repo／branch如上 | 本機已建立 | PASS |
| `scripts/run-github-handoff-watch-windows.ps1` | Windows 安全前景 watch | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\scripts\run-github-handoff-watch-windows.ps1` | 同上 | repo／branch如上 | 本機已建立 | PowerShell parser PASS |
| `github_handoff/README_GITHUB_HANDOFF_20260929.md` | CLI 技術入口 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\github_handoff\README_GITHUB_HANDOFF_20260929.md` | 同上 | repo／branch如上 | 本機已更新 | 內容回讀／diff check PASS |
| `GitHub本地Codex自動交接_使用手冊_20260929.md` | 既有使用手冊校正 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\GitHub本地Codex自動交接_使用手冊_20260929.md` | 同上 | repo／branch如上 | 本機已更新 | 內容回讀／diff check PASS |
| `RUNBOOK_GITHUB_HANDOFF_20260929.md` | 維運與復原 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\RUNBOOK_GITHUB_HANDOFF_20260929.md` | 同上 | repo／branch如上 | 本機已更新 | 內容回讀／diff check PASS |
| `SECURITY_GITHUB_HANDOFF_20260929.md` | 安全與殘餘風險 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\SECURITY_GITHUB_HANDOFF_20260929.md` | 同上 | repo／branch如上 | 本機已更新 | 內容回讀／secret scan PASS |
| `FINAL_REPORT_GITHUB_HANDOFF_20260929.md` | 歷史狀態與本輪 addendum | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\FINAL_REPORT_GITHUB_HANDOFF_20260929.md` | 同上 | repo／branch如上 | 本機已更新 | 事實校正／diff check PASS |
| `README.md` | 英文文件索引 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\README.md` | 同上 | repo／branch如上 | 本機已更新 | 連結相對路徑檢查 |
| `README.zh-TW.md` | 中文文件索引 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\README.zh-TW.md` | 同上 | repo／branch如上 | 本機已更新 | 連結相對路徑檢查 |
| `ChatGPTPlus_GeminiPro本地交接_完整任務規劃_2026-10-06.md` | 完整 backlog／分工 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_GeminiPro本地交接_完整任務規劃_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |
| `ChatGPTPlus_GeminiPro本地交接_工作日誌_2026-10-06.md` | 決策、worker、驗證日誌 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_GeminiPro本地交接_工作日誌_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |
| `ChatGPTPlus_GeminiPro本地交接_驗收清單_2026-10-06.md` | 驗收矩陣 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_GeminiPro本地交接_驗收清單_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |
| `ChatGPTPlus_本地交接提示模板_2026-10-06.md` | ChatGPT Plus Task Brief／續談 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_本地交接提示模板_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀／secret scan PASS |
| `GeminiGoogleAIPro_本地交接提示模板_2026-10-06.md` | Gemini Task Brief／續談 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\GeminiGoogleAIPro_本地交接提示模板_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀／secret scan PASS |
| `ChatApp本地交接_操作手冊_2026-10-06.md` | ADHD 友善操作手冊 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatApp本地交接_操作手冊_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |
| `ChatGPTPlus_GeminiPro本地交接_工作完成報告_2026-10-06.md` | 本輪正式工作報告 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_GeminiPro本地交接_工作完成報告_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |
| `ChatGPTPlus_GeminiPro本地交接_交付物索引_2026-10-06.md` | 本索引 | `C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration\ChatGPTPlus_GeminiPro本地交接_交付物索引_2026-10-06.md` | 同上 | repo／branch如上 | 本機已建立 | 內容回讀 PASS |

