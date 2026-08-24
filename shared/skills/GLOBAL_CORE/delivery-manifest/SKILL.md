---
name: delivery-manifest
description: "每次產生、修改、上傳或寄送檔案後，產生統一的交付物索引 (Delivery Manifest)，並嚴格控管 Google Drive 上傳路徑。"
---

# Delivery Manifest (交付物索引與平台分流)

確保所有產出的檔案、上傳操作，都能有清晰、可驗證的軌跡，並嚴格遵循 Antigravity 與 Codex 的儲存分流原則。

## 1. 檔名與 Google Drive 路徑分流

為了避免 Antigravity 覆寫 Codex 的產出，所有外部寫入必須嚴格遵守以下路徑分流：

| 平台 | 目標路徑與帳號 | 規則限制 |
|---|---|---|
| **Codex** | `Google Drive/CODEX/<project folder>/` | 僅供 Codex 參考，Antigravity 不得寫入 |
| **Antigravity Drive** | `https://drive.google.com/drive/folders/1aaYM0LH7nZc8nGVeGJWWvGuZQEb4zQ2G` | **必須放在此特定資料夾底下**。若同類任務無之前的資料夾，則新創。命名要能說明任務並且加上新增日期。 |
| **Antigravity GitHub** | `https://github.com/a275618631` | 您的專屬 GitHub 擁有者 (Owner) 帳號 |

**檔名統一規範**：必須包含以下元素：
- 專案或功能名稱 (繁體中文)
- 用途 (繁體中文)
- 日期 (`YYYY-MM-DD`)
- 範例：`Antigravity架構草案_2026-08-07.md`

## 2. 交付物索引 (Delivery Manifest)

只要任務中產生了新檔案、修改了檔案、上傳 Drive 或寄送 Email，回覆結論前**固定加入「交付物索引」表格**。

> [!TIP]
> **Minimal 免檢疫例外**：若任務判定為 `Minimal` 車道 (本機 + 極簡單 + 低風險)，**強制豁免**產出此 7 欄位報表，改以一句話精簡回報完成狀態與耗時即可，以維持最高 CP 值。

| 欄位 | 要求 |
|---|---|
| **檔名** | 實際檔名 |
| **用途** | 一句話說明用途 |
| **本機完整路徑** | 絕對路徑；若無本機檔案則寫「不適用」 |
| **遠端 URL** | 只使用**實際回讀**的 Drive/GitHub URL |
| **存放位置** | Drive 完整路徑/parent ID 或 repository/branch |
| **狀態** | 已建立、已更新、尚未保存、未驗證或失敗 |
| **驗證** | 內容、格式、遠端存在性、權限等實際結果 |

> [!IMPORTANT]
> 寫入 Drive 後，必須以實際 metadata、parent 與 URL 回讀驗證。若儲存位置錯誤或回讀失敗，不得報告為「已完成」。
