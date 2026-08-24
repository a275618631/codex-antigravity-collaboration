目的地資料庫：
Codex 知識庫

建立或更新：
更新既有頁

建議標題：
Codex同步設定-使用說明_20260611

分類：
Codex / Setup / Workflow

狀態：
Active

版本：
v2.0

## 摘要

這份文件整理 Codex 通用設定同步方案。最新版本採用 GitHub private repo 作為主同步源，並以 `backups/<電腦名稱>/<分類>/` 分開保存不同電腦與不同設定分類。

GitHub private repo：

```text
https://github.com/a275618631/codex-settings-sync.git
```

Google Drive 與 Notion 只保存說明文件，作為查閱與交接用途；實際版本控管與跨電腦同步以 GitHub 為準。

Google Drive 文件：

```text
https://docs.google.com/document/d/1rdXVSarRQQeOYZPCfd0lRkRfFfC90IKQ0aLSl1c6MV4
```

## 20260611 更新與封存紀錄

- <span style="color:red">修正：舊版「每日自動 pull」已過時；新電腦或其他電腦從遠端更新時，必須手動選擇來源電腦與分類。</span>
- <span style="color:red">修正：舊版「整包複製 `要同步的Codex設定/`」已改為 `backups/<電腦名稱>/<分類>/` 分類備份與手動拉取。</span>
- <span style="color:red">修正：OS 工作排程器與 macOS launchd 不再納入同步，因為它們屬於本機狀態。</span>
- 舊流程對比：~~每日自動 pull~~ -> 手動執行 `手動拉取分類設定.ps1` 或 `.sh`。

## 最終結論

- GitHub private repo 是 Codex 設定同步主來源。
- 每台電腦可以各自上傳分類備份。
- 新電腦或其他電腦拉取時，不自動套用，必須手動選來源電腦與分類。
- 支援分類：`agents-root`、`agents-codex`、`config`、`skills`、`workflows`、`sync-tools-and-docs`。
- 支援 `-Union` 取聯集；skills/workflows 做目錄聯集，同名文字檔做內容聯集。
- 不同步 `.env`、OAuth、tokens、credentials、auth.json、plugin cache、OS 排程器、本機路徑、沙盒權限、信任專案狀態、session DB、暫存與 cache。

## 操作步驟 / 工作流程

查看可用來源電腦：

```powershell
.\同步工具\手動拉取分類設定.ps1 -Pull -ListSources
```

只拉 AGENTS.md：

```powershell
.\同步工具\手動拉取分類設定.ps1 -Pull -SourceComputer <電腦名稱> -Category agents-root
```

只拉 skills 並與本機內容取聯集：

```powershell
.\同步工具\手動拉取分類設定.ps1 -Pull -SourceComputer <電腦名稱> -Category skills -Union
```

修改設定後備份到遠端：

```powershell
.\同步工具\自動備份並推送.ps1
```

## 版本變更

- v1.0：建立 GitHub private repo 作為 Codex 設定同步主來源，採用單一同步包與每日自動 pull。
- v2.0：改為分電腦、分分類備份；遠端拉取改為手動分類選擇；加入 union 規則；排除本機排程器與本機路徑狀態。

## 待確認事項

- Google Drive 目前可用工具未暴露重新命名、移動到封存資料夾或刪除檔案的 Drive metadata 操作。
- 若要在 Drive UI 中完成封存，請將舊版 Drive 文件移入同資料夾內的「封存」子資料夾，或將目前文件重新命名為 `Codex同步設定-使用說明_20260611`。
