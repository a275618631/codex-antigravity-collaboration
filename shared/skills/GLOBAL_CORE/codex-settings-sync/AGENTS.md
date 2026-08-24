本檔是 Codex 設定同步專案的專案層規則。全域工作習慣放在 Codex home 的 `AGENTS.md`，預設位置通常是 Windows 的 `%USERPROFILE%\.codex\AGENTS.md`、macOS/Linux 的 `~/.codex/AGENTS.md`，或 `$CODEX_HOME` 指定的位置；本檔只放此同步專案專用規則。

## 專案目標

- 維護可在多台電腦手動還原的 Codex 設定同步包。
- 優先同步可移植、可審查、非敏感的設定。
- 避免同步授權、快取、工作階段、資料庫暫存、OS 本機狀態。

## 修改規則

- 若由 Sol Auto 主持本專案任務，Sol 只做評估、計畫、排障、分派與驗收判定；匯出、同步文件、固定範圍檢查比對、同步實測與 GitHub 可回復交付預設交 Luna High。同步腳本的架構或程式碼實作、審查與驗證交 Terra，阻塞時才回 Sol。
- 修改 Codex 設定、使用者技能、工作流程、execution profiles 或同步文件前，先執行一次含時間戳的既有匯出／備份腳本；全部修改與靜態驗證完成後再執行一次最終匯出，中間不重複建立快照。
- 不要修改 `.env`；若任務真的需要，先說明目的、後果，並取得使用者同意。
- 不要自動套用遠端設定到另一台電腦；遠端還原必須手動、分類執行。
- 使用者說「同步設定」或「更新設定」時，預設意思是匯出本機目前設定並檢查差異，不自動 Commit／Push／PR。
- 只有使用者明確要求「上傳 Codex 設定到 GitHub」或同義語意時，才由 Luna 執行 stage、commit、非受保護功能分支 push 與 Draft PR；不得 Merge、force-push 或直接寫入預設／受保護分支。
- 使用者說「更新最新設定」時，預設意思是先 pull GitHub 最新同步 repo，再將遠端設定與本機目前設定比較並取聯集，不直接覆蓋本機新增但尚未上傳的規則。
- 若使用者只說「同步」、「更新」或其他語意不明口令，預設只做安全的本機匯出與差異檢查；只有拉取來源或外部寫入會改變結果時才集中詢問。
- 不要同步內建 `.system` skills、plugin cache、credentials、tokens、OAuth/auth state、OS schedulers、sandbox/trust state、session DBs、temp files 或本機絕對路徑狀態。
- 若要變更工作區、同步根目錄或設定路徑，先說明後續風險：舊 workspace 綁定、trusted project、同步腳本、快取狀態、歷史 session、捷徑與排程可能失效。

## 備份白名單

- `config.toml`
- `AGENTS.md`
- `sol-auto.config.toml` 與 `luna-manual.config.toml`（存於 `execution-profiles/`，還原至 `$CODEX_HOME` 根層）
- 使用者自訂 skills
- 使用者自訂 workflows 或 automations 設定
- 同步工具與同步說明文件

## 備份黑名單

- `auth.json`
- `*.sqlite`
- `*.sqlite-wal`
- `*.sqlite-shm`
- `sessions/`
- `archived_sessions/`
- `logs_*.sqlite`
- `plugins/cache/`
- `cache/`
- `.sandbox*/`
- `.tmp/`
- `tmp/`
- `models_cache.json`
- `rules/default.rules`（含本機核准規則與絕對路徑）

## Git 規則

- 不使用 `git add .`；只 stage 與本次任務直接相關的檔案。
- commit 前先列出修改檔案、測試結果與待確認事項。
- commit message 使用簡短英文 conventional commit。
- 分支名稱預設使用 `codex/` 前綴。
- 永不使用 force push，不直接推送預設或受保護分支，不執行 Merge。
