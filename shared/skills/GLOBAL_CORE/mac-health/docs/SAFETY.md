# mac-health 安全模型與守則 (Safety Model)

## 核心設計理念

mac-health 的第一核心準則是 **安全性與無侵入性**。
診斷與優化規劃工具本身絕不具備自動清理、刪除、終止進程或修改系統設定的能力。

---

## 操作分級 (Safety Levels)

### 1. READ_ONLY (唯讀查詢) — 自動允許
- 執行 `diagnose.py`、`compare.py`
- 執行 macOS 原生只讀查詢指令：`diskutil info -plist`, `sysctl`, `vm_stat`, `memory_pressure -Q`, `df`, `ps`, `iostat`, `pmset`, `system_profiler`, `mdutil -s`
- 執行 `MoleAdapter.analyze()` 與 `MoleAdapter.dry_run_clean()`
- 產出結構化 JSON 與優化計畫

### 2. REVERSIBLE_LOW_RISK (低風險可逆操作) — 需集中徵詢核准
- 重新啟動 Finder 或 Dock (`killall Finder`, `killall Dock`)

### 3. WORK_INTERRUPTING (中度影響操作) — 必須明確列出並取得核准
- 關閉使用者指定之單一應用程式或分頁
- 停止 Docker Desktop 或虛擬機 (VM)
- 停止特定 Homebrew 服務 (`brew services stop <service>`)
- 停用登入項目 (Login Items) 或 LaunchAgents

### 4. DESTRUCTIVE (破壞性操作) — 必須嚴格執行 Dry-Run 審查
- 流程要求：`分析目標 -> 執行 Dry-run -> 呈現完整刪除路徑與釋放容量 -> 集中審查確認 -> 實際執行`
- 未列於審查清單內的檔案一律不得更動。

### 5. PROHIBITED (絕對禁止行為) — 永遠不執行
1. 執行包含萬用字元或未知路徑的 `sudo rm` 或 `rm -rf`
2. 關閉系統完整保護機制 (System Integrity Protection, SIP) 或 Gatekeeper
3. 修改或掛載 Sealed System Volume (SSV) 與驗證根目錄
4. 刪除或更動 `/System`, `/usr/bin`, `/sbin` 等 macOS 原生二進位程式
5. 未經驗證強制 `kill -9` 系統級核心 Daemon（如 `WindowServer`, `launchd`, `kernel_task`, `mds`）
6. 清除系統安全金鑰庫 (Keychain) 或重設安全性權限
7. 執行來源不明的「一鍵加速」、「清理記憶體」終端機黑魔法腳本
