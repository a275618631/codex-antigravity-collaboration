# Mac 還原後手動設定清單

這份清單用於在 Mac 上拉取 Codex 設定同步 repo 後，手動確認不能自動跨機套用的本機設定。

## 1. 取得同步 repo

```bash
git clone https://github.com/a275618631/codex-settings-sync.git
cd codex-settings-sync
```

如果 repo 已存在，請先確認沒有未提交變更，再切換到 `master`：

```bash
git status --short
git switch master
```

## 2. 確認 Codex home

Mac 預設 Codex home 通常是：

```text
~/.codex
```

如果有設定 `$CODEX_HOME`，以該環境變數指定的位置為準。

## 3. 從 GitHub 套用全部可攜設定

直接執行完整套用。腳本會從 GitHub `master` 更新同步 repo，並依最新 `export-info.txt` 自動選擇來源電腦：

```bash
./同步工具/手動拉取分類設定.sh --pull --branch master --category all
```

這個完整套用不使用 `--union`，會覆蓋同名可攜設定；不會刪除未列入同步範圍的本機狀態。

若只想更新部分分類，才使用分類參數：

```bash
./同步工具/手動拉取分類設定.sh --pull --branch master --category agents-root --category config --category skills --category workflows
```

`execution-profiles` 是完整設定檔，不使用逐行聯集，若單獨套用可執行：

```bash
./同步工具/手動拉取分類設定.sh --pull --branch master --category execution-profiles
```

若同步 repo 有未提交變更，腳本會停止；請先備份或提交該同步 repo，再重新執行。若不確定，先只做 diff 或備份本機 `~/.codex`。

## 4. 需要 Mac 手動確認的設定

- 登入狀態：重新登入 Codex、GitHub、Google、Notion、Gmail、Slack 等 connector。
- `auth.json`：不要從其他電腦複製。
- Automation：不要直接複製其他電腦的 automation；它可能含本機 task id、workspace id 或本機路徑。Codex 設定預設不建立每日自動上傳；如有需要，只建立提醒或本機匯出 Automation。
- MCP：只套用不含本機路徑的 HTTP MCP；含 Windows runtime 路徑的 stdio MCP 不適用 Mac。
- Context7：若要啟用，先確認 Mac 有可用的 Node.js 與 `npx`。
- Browser / Chrome / Computer Use：依 Mac 系統權限重新授權。
- sandbox / trust：Mac 與 Windows 設定不同，依本機 Codex UI 或官方設定重新確認。
- project paths：不要套用 Windows 絕對路徑；在 Mac 重新 trust 專案資料夾。

## 5. 還原後驗證

```bash
codex --version
```

開啟 Codex 後請確認：

- 全域 `AGENTS.md` 已載入。
- `~/.codex/sol-auto.config.toml` 與 `~/.codex/luna-manual.config.toml` 已存在，且 Luna 預設 reasoning effort 為 `high`。
- 自訂 skills 可被列出或可被 `$skill` 呼叫。
- `openaiDeveloperDocs` MCP 可用。
- `context7` 仍維持停用，直到 Node.js / npx 設定完成。
- GitHub repo 可 pull/push。

## 6. 常用口令

- 「同步設定」或「更新設定」：匯出本機最新設定，不自動上傳。
- 「上傳 Codex 設定到 GitHub」：由 Luna Commit／Push 非受保護功能分支並建立／更新 Draft PR，不 Merge。
- 「套用 Codex 設定」、「更新 Codex 設定」、「更新最新設定」、「參考 GitHub 更新」：從 GitHub `master` 套用全部可攜設定。
- 「同步」或「更新」：若沒有 Codex／設定／GitHub 語意，才詢問方向。
