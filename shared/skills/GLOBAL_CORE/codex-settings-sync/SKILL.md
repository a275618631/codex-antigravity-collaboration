---
name: codex-settings-sync
description: 修改、備份、匯出、同步、還原或檢查 Codex 全域設定、AGENTS.md、使用者 skills、workflow 規格、execution profiles 與同步文件時使用。支援「同步設定」「更新 Codex 設定」「套用到另一台 Mac」「完成後同步」等中文、英文與中英混用語意。
---

# Codex 設定同步

## 核心規則

- 修改 Codex 設定、使用者 skills、workflow 規格、execution profiles 或同步文件前，先執行一次含時間戳快照的既有匯出器；全部修改完成並通過靜態檢查後再執行一次最終匯出。中間不重複建立快照。
- GitHub `master` 是日常設定唯一來源；Google Drive 只作備份與災難復原，不得在日常套用時與 GitHub 混合覆蓋。
- 遠端還原必須在使用者明確要求套用時執行；完整套用固定先更新 GitHub `master`，再套用全部可攜分類。
- 「套用／更新 Codex 設定」是從 GitHub 更新另一台電腦的本機設定；不建立、不執行備份腳本，只使用既有同步 repo 與既有套用工具。若目標電腦尚未 clone 同步 repo，先取得 `a275618631/codex-settings-sync`；路徑或覆蓋範圍會改變結果時才詢問。
- 可攜的 execution profiles 僅限 allowlist：`sol-auto.config.toml`、`luna-manual.config.toml`。同步到 `execution-profiles/`，還原至目標電腦的 `$CODEX_HOME` 根層。
- 不同步內建 `.system` skills、plugin cache、credentials、tokens、OAuth/auth state、OS schedulers、local paths、sandbox/trust state、session DBs、temp files。
- 修改 `.env` 前必須說明目的、後果並取得同意。
- 「同步設定」「更新 Codex 設定」「套用 Codex 設定」「更新最新設定」「參考 GitHub 更新」「套用到另一台 Mac」及等價中文、台灣用語、英文與中英混用語意都應觸發本 Skill，不要求使用者說出 Skill 名稱。
- 若目前由 Sol Auto 主持，匯出、同步文件修改、固定範圍檢查／比對、Windows／Mac 還原實測與 GitHub 可回復交付均委派 Luna High；Sol 只制定計畫與判定驗收，不重跑同一組實測。只有同步工具本身涉及架構或程式碼工程判斷時才委派 Terra。

## 同步 repo

優先使用目前工作區中已設定的同步 repo；若使用者未指定，先尋找已 clone 的 `codex-settings-sync`，不要假設另一台電腦使用 Windows 絕對路徑。

## 常用流程

1. 修改前備份：依目前任務的快照政策執行既有匯出器；若使用者已明確表示當日已有快照，不重複建立修改前快照。
2. 做最小必要修改。
3. 以解析器、validator、diff 與敏感資訊指標檢查修改，不為每個小步驟重跑完整匯出。
4. 修改後再次執行同一匯出器，確認同步包、`execution-profiles` 與雜湊。
5. 用暫存 `$CODEX_HOME` 實際執行分類還原，確認全部可攜分類與 `sol-auto.config.toml`、`luna-manual.config.toml` 能跨機器回復。
6. 若使用者明確要求提交或上傳 GitHub，才由 Luna 執行 stage、commit、非受保護功能分支 push 與 Draft PR；不得自動上傳、合併或寫入預設／受保護分支。

另一台 Mac 套用 GitHub 最新設定：

```bash
git switch master
bash "同步工具/手動拉取分類設定.sh" --pull --branch master --category all
```

Windows 使用同等流程：

```powershell
git switch master
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category all
```

腳本會依 GitHub 備份中的最新 `metadata/export-info.txt` 自動選擇來源電腦，並套用 `agents-root`、`agents-codex`、`agents`、`config`、`execution-profiles`、`skills`、`workflows`、`workflow-definitions` 與同步文件。完整套用不使用 Union；若同步 repo 有未提交變更，應先停止並處理，不靜默覆蓋。

## 風險提醒

變更工作區、同步根目錄或設定路徑前，先提醒可能影響：workspace 綁定、trusted project、同步腳本、快取狀態、歷史 session、捷徑、排程與文件中的絕對路徑。

## 完成回報

列出 GitHub branch／commit、修改檔案、可攜分類套用／還原測試結果、未同步項目與原因，以及 Mac 需要執行的分類還原命令。Drive 僅回報備份狀態，不把 Drive 當成日常來源。
