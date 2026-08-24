# Codex同步設定-使用說明_20260611

## 目的

讓不同電腦使用 Codex 時，採用相同的規則、設定、skills、workflows、execution profiles 與同步流程。

本同步方案只處理 Codex 通用設定，不同步專案產物、影片、程式碼成果、`.env`、OAuth / Notion / Google / GitHub 登入狀態、tokens、credentials、auth.json、plugin cache、OS 工作排程器、macOS launchd、本機路徑、沙盒權限、信任專案狀態、session DB、暫存或 cache。

## 主要同步來源

GitHub private repo：

```text
https://github.com/a275618631/codex-settings-sync.git
```

Google Drive 與 Notion 作為說明文件、設定備份與災難復原用途；實際版本控管與跨電腦同步一律以 GitHub `master` 為準，Drive 不參與日常覆蓋。

Google Doc 備份：

```text
https://docs.google.com/document/d/1rdXVSarRQQeOYZPCfd0lRkRfFfC90IKQ0aLSl1c6MV4
```

## 20260611 更新與封存紀錄

- <span style="color:red">修正：舊版「每日自動 pull」已過時；新電腦或其他電腦從遠端更新時，必須手動選擇來源電腦與分類。</span>
- <span style="color:red">修正：舊版「整包複製 `要同步的Codex設定/`」已改為 `backups/<電腦名稱>/<分類>/` 分類備份與手動拉取。</span>
- <span style="color:red">修正：舊版寫入工作排程器 / launchd 的做法不再納入同步；OS 排程器屬本機狀態，不備份。</span>
- 舊流程對比：~~每日自動 pull~~ -> 手動執行 `手動拉取分類設定.ps1` 或 `.sh`，並明確指定分類。
- 舊結構對比：~~`要同步的Codex設定/.codex/skills/` 作為主要同步位置~~ -> `backups/<電腦名稱>/skills/` 作為遠端分類備份主結構。

## GitHub 備份結構

新的遠端備份結構以電腦名稱分開，並在每台電腦底下再分分類：

```text
backups/
  <電腦名稱>/
    agents-root/AGENTS.md
    agents-codex/AGENTS.md
    agents/                  # 自訂 agent 設定
    config/config.toml
    execution-profiles/
      sol-auto.config.toml
      luna-manual.config.toml
    skills/
    workflows/
    workflow-definitions/
    sync-tools-and-docs/
    metadata/export-info.txt
```

`要同步的Codex設定/` 是舊版相容同步包，保留作為人工閱讀與過渡用途；分電腦、分分類拉取以 `backups/` 為主。

## 可分開同步的分類

- `agents-root`：`AGENTS.md`
- `agents-codex`：`.codex/AGENTS.md`
- `agents`：`.codex/agents/` 自訂 agent 設定
- `config`：非機密 `config.toml`
- `execution-profiles`：可攜的 `sol-auto.config.toml` 與 `luna-manual.config.toml`
- `skills`：自訂 skills，排除 `.system`
- `workflows`：工作流與可重複 SOP
- `workflow-definitions`：Codex 工作流定義與交付流程
- `sync-tools-and-docs`：同步腳本與說明文件

## 本機匯出與 GitHub 備份

修改 Codex 設定檔、skills、workflows 或 execution profiles 後，先匯出到本機同步 repo：

```powershell
.\同步工具\自動備份並推送.ps1
```

不加參數時只匯出。使用者主動要求上傳時，才由 Luna 在非受保護功能分支執行：

```powershell
.\同步工具\自動備份並推送.ps1 -Branch <功能分支> -ConfirmPush
```

腳本不執行 rebase 或 Merge，也拒絕直接推送 `main`／`master`。分類匯出入口是：

```powershell
.\同步工具\匯出目前設定到同步包.ps1
```

## 手動拉取

新電腦或其他電腦從 GitHub 更新時，固定使用 `master`；腳本會自動選擇最新來源電腦與全部可攜分類：

```powershell
git switch master
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category all
```

常用範例：

```powershell
# 只拉 AGENTS.md
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category agents-root

# 只拉自訂 skills，並與本機內容取聯集
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category skills -Union

# 只拉 workflow
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category workflows -Union

# 套用 Sol Auto／Luna execution profiles
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category execution-profiles

# 拉全部分類
.\同步工具\手動拉取分類設定.ps1 -Pull -Branch master -Category all
```

## 聯集規則

分電腦備份的目的，是允許不同電腦上傳不同版本。拉取時有兩種模式：

- 不加 `-Union`：用來源電腦的分類覆蓋目標分類。
- 加 `-Union`：目錄取聯集；同名文字檔則保留本機內容，並把遠端檔案中本機沒有的文字行附加到檔尾。

這裡的聯集不是只看檔名。skills、workflows 會合併檔案集合；同名文字檔會合併內容。若遇到非文字檔且內容衝突，腳本會保留遠端副本為 `*.remote-conflict.*`。

## 不同步清單

- `.env`
- OAuth / Notion / Google / GitHub 登入狀態
- tokens、credentials、auth.json
- 本機 plugin cache 狀態
- OS 工作排程器 / macOS launchd
- 本機路徑、沙盒權限、信任專案狀態
- session DB、暫存、cache
- Codex 內建 `.system` skills
- 外掛 cache 或 marketplace cache
- 影片
- 專案產出程式碼
- 任務輸出資料

## 已測試項目

- GitHub private repo 已建立並推送成功。
- GitHub repo visibility 已確認為 `PRIVATE`。
- 分類匯出腳本測試成功。
- 手動來源列表測試成功。
- 手動分類套用至暫存資料夾測試成功，未修改真實 `.codex`。
- `execution-profiles` 可還原至暫存 Codex home，且檔案雜湊與來源一致。
- `config.toml` 清洗後未包含本機路徑、sandbox、trust 狀態或 token。
- Google Drive connector 可讀取既有文件。

## 已知限制

- Google Drive 目前可用工具未暴露重新命名、移動到封存資料夾或刪除檔案的 Drive metadata 操作。
- 因上述限制，Drive 端可以更新文件正文，但檔名加上 `20260611`、移入「封存」或刪除過時文件需透過 Google Drive UI 或具備 metadata 寫入能力的工具完成。
