# Windows ACL 影響範圍與最小變更方案（2026-10-20）

## 0. 執行摘要

本文件是唯讀盤點與待核准方案。本次盤點沒有修改 ACL、Windows 安全性政策、portable worktree、任何其他 Repo 或檔案權限。

目前 T7 FAIL 的直接證據：

- 目前執行身分：51398-3779\codexsandboxoffline。
- 該身分屬於 51398-3779\CodexSandboxUsers。
- C:\Users\Y6T2\Documents\Tech Review 父層有一條對 CodexSandboxUsers 的明確 Modify, Synchronize Allow ACE，並設定 ContainerInherit, ObjectInherit。
- B Repo 的同一條 Modify 規則目前是 inherited。
- 盤點到的 24 個父層直接子目錄均承接 CodexSandboxUsers: Modify, Synchronize。

建議方向：

1. 先在目標樹外備份完整 DACL。
2. 移除父層對 CodexSandboxUsers 的可繼承 Modify。
3. 父層只保留讓受限 Runtime 定位目錄的唯讀／走訪權限。
4. 僅對 B Repo 明確授予 CodexSandboxUsers 的 Modify；其他同層專案維持唯讀。
5. 用同一受限身分執行原生寫入嘗試，要求相鄰 Repo 回傳 Windows ERROR_ACCESS_DENIED (0x5)。

以上步驟尚未執行，必須由使用者確認並由具備主機權限的人員操作。

## 1. 目前環境與盤點證據

### 1.1 B Repo 狀態

| 項目 | 值 |
|---|---|
| Repo | C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration |
| Branch | codex/docs-entry-20261019 |
| HEAD | 2538a1e |
| 工作樹 | 既有未提交變更與 LIVE_HANDOFF_EVIDENCE_20261020.md 保留；本次新增本方案文件 |

### 1.2 受限身分

唯讀命令 whoami 回報：

~~~text
51398-3779\codexsandboxoffline
~~~

唯讀命令 whoami /groups 顯示：

~~~text
51398-3779\CodexSandboxUsers  Alias  S-1-5-21-1782533309-825769221-2843094921-1008
~~~

### 1.3 父層 ACL

目標父層：

~~~text
C:\Users\Y6T2\Documents\Tech Review
~~~

關鍵 ACL：

| Identity | Rights | Type | Inherited | Inheritance |
|---|---|---|---:|---|
| 51398-3779\CodexSandboxUsers | Modify, Synchronize | Allow | No | ContainerInherit, ObjectInherit |
| 51398-3779\CodexSandboxUsers | Modify, Synchronize | Allow | Yes（父層既有繼承規則） | ContainerInherit, ObjectInherit |
| NT AUTHORITY\SYSTEM | FullControl | Allow | Yes | ContainerInherit, ObjectInherit |
| BUILTIN\Administrators | FullControl | Allow | Yes | ContainerInherit, ObjectInherit |
| 51398-3779\Y6T2 | FullControl | Allow | Yes | ContainerInherit, ObjectInherit |

父層 AreAccessRulesProtected=False，表示 ACL 仍允許繼承。完整 SDDL 與每條 ACE 應在正式變更前以備份命令保存。

### 1.4 B Repo ACL

目標：

~~~text
C:\Users\Y6T2\Documents\Tech Review\codex-antigravity-collaboration
~~~

CodexSandboxUsers: Modify, Synchronize 目前為 inherited，且 B Repo AreAccessRulesProtected=False。這證明 B Repo 的寫入權限目前由父層廣泛規則提供，而非 B Repo 專屬的最小授權。

### 1.5 影響範圍

以下 24 個父層直接子目錄均承接 CodexSandboxUsers: Modify, Synchronize；其下的繼承子目錄與檔案也可能受影響：

~~~text
_bridge_repair_20261008
_codex_luna_snapshots
_codex_security_snapshots
_codex_sync_luna_snapshots
_github_handoff_e2e_20260929
_local_interop_portable_20261008
_ppt-master-benchmark-20260811
_ppt-master-final-export-20260811
_ppt-master-handoff-20260811
_ppt-master-handoff-verify-20260811
_ppt-master-install
_ppt-master-preflight-20260811
_rca_staging
.agents
.git
.tools
.venv-systemone
codex-antigravity-collaboration
codex-settings-sync-cross-platform-fix
factory-knowledge-grounded-rag-review-20261007
github_handoff
MCP_SETUP_BACKUP_20261015
project-isolation-audit_20261015
R4_testdata
~~~

這是高影響範圍：不能直接對父層執行遞迴移除或重設 ACL，否則可能改變多個專案、快照、虛擬環境與既有協作資料的權限。

## 2. 變更前必做的備份（待核准，不是本次執行內容）

備份位置必須在目標樹外，避免備份檔被納入 ACL 遞迴操作。以下命令只應由核准的主機管理員執行：

~~~powershell
$parent = 'C:\Users\Y6T2\Documents\Tech Review'
$backup = 'C:\Users\Y6T2\Documents\Tech Review_ACL_BACKUP_20261020'

# 本方案階段不執行
New-Item -ItemType Directory -Force -Path $backup | Out-Null

# 保存目標樹的 DACL；/save 不會修改目標 ACL
icacls $parent /save (Join-Path $backup 'tech-review-dacl.acl') /t /c

# 保存父層與 B Repo 的可讀 SDDL 快照
(Get-Acl -LiteralPath $parent).Sddl |
  Set-Content -LiteralPath (Join-Path $backup 'parent.sddl.txt') -Encoding UTF8
(Get-Acl -LiteralPath (Join-Path $parent 'codex-antigravity-collaboration')).Sddl |
  Set-Content -LiteralPath (Join-Path $backup 'b-repo.sddl.txt') -Encoding UTF8

# 保存受限執行身分，供驗收證據比對
whoami /user | Set-Content -LiteralPath (Join-Path $backup 'whoami-user.txt')
whoami /groups | Set-Content -LiteralPath (Join-Path $backup 'whoami-groups.txt')
Get-FileHash -Algorithm SHA256 (Join-Path $backup 'tech-review-dacl.acl')
~~~

備份驗收要求：

- tech-review-dacl.acl 存在且可讀。
- 備份檔 hash 已記錄。
- parent.sddl.txt、b-repo.sddl.txt 與受限身分紀錄存在。
- 備份位置不在 C:\Users\Y6T2\Documents\Tech Review 之下。

## 3. 建議的最小變更

### 3.1 變更原則

- 只處理 51398-3779\CodexSandboxUsers 這個已確認的主體。
- 不刪除、不重設其他未知 SID 的 ACE；未知 SID 需由管理員先完成身分對照與有效權限分析。
- 不移動、不複製、不重建任何 Repo 或 portable worktree。
- 不改變檔案擁有者、SYSTEM、Administrators 或使用者本人 FullControl。
- 先停止 Codex、Antigravity、MCP Bridge 與可能使用目標目錄的程序，避免變更期間產生寫入競態。

### 3.2 候選命令（僅供核准後執行）

以下是最小候選方案，不是本輪已執行的命令：

~~~powershell
$parent = 'C:\Users\Y6T2\Documents\Tech Review'
$repo = Join-Path $parent 'codex-antigravity-collaboration'
$sid = '*S-1-5-21-1782533309-825769221-2843094921-1008'

# 1. 在 Tech Review 父層停止上游 ACL 繼承並保留既有其他 ACE 的副本。
#    目前父層同時有明確與 inherited 的 CodexSandboxUsers Modify；
#    只移除明確 ACE 會讓上游的 Modify 繼續生效。
icacls $parent /inheritance:d

# 2. 從父層移除該主體的 Modify ACE。
icacls $parent /remove:g $sid

# 3. 父層只給受限 Runtime 走訪／讀取權，並讓此權限可傳給同層子目錄。
icacls $parent /grant:r ("{0}:(OI)(CI)(RX)" -f $sid)

# 4. 僅對 B Repo 建立明確可繼承 Modify ACE。
icacls $repo /grant:r ("{0}:(OI)(CI)(M)" -f $sid)
~~~

這個方案只有在其他群組／SID 不會透過有效權限再次授予該受限身分 Modify 的前置檢查通過後才可執行。若有效權限分析發現其他 ACE 仍讓 codexsandboxoffline 可寫，應停止，不得自行擴大刪除範圍。

### 3.3 預期結果

| 位置 | CodexSandboxUsers 預期權限 |
|---|---|
| Tech Review 父層 | Read/Execute，可走訪，不可建立／修改／刪除 |
| B Repo 根目錄及其子項 | 明確 Modify，供核准的 B 工作流程使用 |
| 其他同層 Repo／快照／工具目錄 | 僅承接父層唯讀，不可寫入 |

這不是拒絕所有跨專案讀取；它是針對 T7 所需的最小寫入邊界。若需求還包括讀取隔離，必須另行設計 read boundary，不能把本方案誤稱為完整多租戶隔離。

## 4. 回復程序（待核准，不是本次執行內容）

若任何既有 Codex／Bridge／快照流程異常，先停止相關程序，再以完整 DACL 備份回復：

~~~powershell
$parent = 'C:\Users\Y6T2\Documents\Tech Review'
$backup = 'C:\Users\Y6T2\Documents\Tech Review_ACL_BACKUP_20261020'

# /save 產生的路徑以 Tech Review 為第一段，
# 因此 /restore 必須從 Documents 父層執行，而不是從 Tech Review 內執行。
Push-Location (Split-Path $parent -Parent)
try {
    # 先確認 backup hash 與變更前紀錄一致
    icacls . /restore (Join-Path $backup 'tech-review-dacl.acl') /c
}
finally {
    Pop-Location
}

# 回復後唯讀檢查
icacls $parent
icacls (Join-Path $parent 'codex-antigravity-collaboration')
~~~

icacls /save／/restore 主要保存與回復 DACL；擁有者、稽核策略或其他非 DACL 設定若有變更，需使用變更前的獨立紀錄由管理員處理。

## 5. T7 驗收方式（套用變更後才可執行）

### 5.1 前置條件

- 變更前備份已驗收。
- Codex、Antigravity、MCP Bridge 與 B Repo 相關 watcher 已停止。
- 驗收命令在 codexsandboxoffline／CodexSandboxUsers 安全身分下執行，不可用管理員身分代替。
- 不使用 portable worktree；B Repo 現有未提交資料先保留原樣。

### 5.2 ACL 靜態驗收

~~~powershell
$parent = 'C:\Users\Y6T2\Documents\Tech Review'
$repo = Join-Path $parent 'codex-antigravity-collaboration'
$sibling = Join-Path $parent 'github_handoff'

whoami
whoami /groups
icacls $parent
icacls $repo
icacls $sibling
~~~

必須看到：

- 父層對 CodexSandboxUsers 沒有 M／W／F。
- B Repo 有明確可識別的 CodexSandboxUsers:(OI)(CI)(M)。
- 相鄰 github_handoff 沒有該主體的 M／W／F。

### 5.3 原生拒絕／允許驗收

以下測試只應在人工核准套用 ACL 後執行。它會在 B Repo 建立唯一暫存檔並立即清除；對相鄰 Repo 的嘗試若意外成功，會立即刪除該唯一測試檔並判定 FAIL。這不是模擬測試，而是由 Windows 核心回傳結果的 bounded probe。

~~~powershell
$parent = 'C:\Users\Y6T2\Documents\Tech Review'
$repo = Join-Path $parent 'codex-antigravity-collaboration'
$sibling = Join-Path $parent 'github_handoff'
$id = [guid]::NewGuid().ToString('N')
$allowed = Join-Path $repo ('.t7-allow-' + $id + '.tmp')
$denied = Join-Path $sibling ('.t7-deny-' + $id + '.tmp')
$deniedByKernel = $false

try {
    try {
        [System.IO.File]::WriteAllText($denied, 't7-denial-probe')
    }
    catch [System.UnauthorizedAccessException] {
        $deniedByKernel = $true
        Write-Output ('DENY_OK hresult=' + $_.Exception.HResult)
    }

    if (Test-Path -LiteralPath $denied) {
        Remove-Item -LiteralPath $denied -Force -ErrorAction SilentlyContinue
        throw 'T7_FAIL: cross-project write unexpectedly succeeded'
    }
    if (-not $deniedByKernel) {
        throw 'T7_FAIL: no native access-denied result was observed'
    }

    [System.IO.File]::WriteAllText($allowed, 't7-allow-probe')
    if (-not (Test-Path -LiteralPath $allowed)) {
        throw 'T7_FAIL: B Repo allow-write probe did not persist'
    }
    Write-Output 'ALLOW_OK b_repo_write_observed'
}
finally {
    Remove-Item -LiteralPath $allowed -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $denied -Force -ErrorAction SilentlyContinue
}
~~~

T7 PASS 的最低證據：

1. whoami／群組身分是受限 Runtime，而非 Administrators。
2. 相鄰 Repo 的寫入 API 由 Windows 原生拒絕，HResult 對應 0x80070005／Win32 ERROR_ACCESS_DENIED (0x5)。
3. 相鄰 Repo 沒有留下測試檔。
4. B Repo 的受控暫存寫入成功並已清除。
5. B Repo Git 狀態與變更前一致，沒有污染既有未提交資料。
6. 變更後的 ACL 靜態輸出、測試輸出、備份 hash 與回復紀錄均保存供審查。

若相鄰 Repo 寫入成功，或 B Repo 寫入失敗，必須判定 T7 FAIL 並依第 4 節回復，不得以應用層 guard 或 Bridge PASS 代替 OS 驗收。

## 6. 本次未執行項目與核准點

本次已執行的只有唯讀盤點：Get-Acl、whoami、whoami /groups、同層目錄列舉與 Git 狀態確認。

本次未執行：

- icacls /remove、/grant、/reset、/restore。
- Set-Acl 或任何 Windows Security／DACL 修改。
- 任何跨 Repo 寫入嘗試。
- portable worktree 操作。
- Push、Merge 或其他 Repo 的修改。

第 3 節方案已獲核准並完成一次套用／驗收／回復循環；由於主機策略重新施加 Modify，後續不可再次套用，除非先由主機管理員修正外層安全策略。B Repo 目前維持 LIVE_BLOCKED。

## 7. 本次核准後執行紀錄

本節記錄 2026-10-20 使用者核准後的實際結果。

### 7.1 備份

- 備份位置：`C:\Users\Y6T2\Documents\Tech Review_ACL_BACKUP_20261020`。
- `icacls /save` 成功保存 39,607 個項目；有 1 個檔案未能處理，未位於本次 B Repo／父層 ACL 變更目標。
- 父層與 B Repo 的 SDDL 快照、受限身分快照、完整 DACL 檔與 SHA-256 hash 均保留。
- DACL hash：`A6C91A1794D8F1C96B59EBA849E5185193BA0E60730F1B0749AC34AA90184334`。

### 7.2 套用與主機持久性

在 elevated 程序內，父層曾暫時呈現唯讀、B Repo 呈現明確 Modify；但每次 elevated ACL 命令結束後，Codex sandbox／主機邊界重新把父層與相鄰 Repo 的 `CodexSandboxUsers Modify` 恢復。這表示 Repo 外的主機策略會重新施加廣泛寫入權限，方案無法持久成立。

### 7.3 受限身分原生 T7 probe

最後一次 probe 使用：

~~~text
whoami=51398-3779\codexsandboxoffline
CROSS_WRITE_SUCCEEDED
B_REPO_WRITE_SUCCEEDED
outside_residual=False
allowed_residual=False
git_status_unchanged=True
~~~

結果判定：**T7 FAIL**。受限身分仍能在相鄰 `github_handoff` Repo 建立檔案；檔案已立即清除，B Repo 暫存檔也已清除，Git 狀態未變。elevated 身分 `51398-3779\y6t2` 的寫入結果不列為 T7 證據，因為它不是目標 Runtime 身分。

### 7.4 回復

- 完整 `/restore` 嘗試因 Windows `1300`（caller 未具備備份中部分 SID 所需權限）處理 0 個項目，沒有用它宣稱回復成功。
- 隨後以已確認的 `CodexSandboxUsers` SID 做最小回復：重新啟用父層繼承、恢復父層 Modify、移除 B Repo 額外明確 ACE。
- 回復後唯讀檢查：父層 `AreAccessRulesProtected=False`；父層、B Repo、相鄰 `github_handoff` 均回到 `CodexSandboxUsers Modify` 的原本有效狀態。
- 父層與 B Repo 的 SDDL 目前未能做到 byte-for-byte 完全相同；原本 inherited ACE 在部分套用期間被複製成 explicit ACE，完整 `/restore` 又因 Windows `1300` 權限限制未能執行。這是 ACL metadata 收尾項，不影響本次已驗證的有效寫入結果；若要求完全清除重複 ACE，必須由具備必要安全權限的主機管理員執行備份回復。
- Branch 仍為 `codex/docs-entry-20261019`，HEAD 仍為 `2538a1e`，B Repo 既有未提交內容未被改動。

本次結論維持 `LIVE_BLOCKED`；要讓 T7 變成 PASS，仍需要主機管理員在 Codex sandbox 外層修正會重新施加 Modify 的 Windows 安全策略／ACL，然後重新執行第 5 節驗收。
