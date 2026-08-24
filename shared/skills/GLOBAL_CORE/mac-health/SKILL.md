---
name: mac-health
description: macOS 系統健康診斷、客觀根因分析 (RCA)、安全優化計畫與 Before/After 效果驗證技能。當使用者反映 Mac 卡頓、變慢、發熱、記憶體不足、空間耗盡、要求優化或驗證改善效果時使用。
---

# mac-health 技能指引 (Agent Skill Guide)

本技能規範 AI Agent 如何使用 `diagnose.py`、`optimizer.py`、`compare.py` 進行嚴謹、客觀、不誇大結論的 macOS 系統健康診斷與改善閉環。

---

## 1. 核心分析與判斷準則 (RCA Calibration Principles)

1. **嚴格分級分類**：
   - `CONFIRMED BOTTLENECK`：必須有明確、充分且不可辯駁的實質證據（例如：Critical 記憶體壓力且 Free < 20%、CPU 持續 > 85% 且特定進程獨佔、SSD 可用空間 < 15GB）。
   - `LIKELY CONTRIBUTOR`：指標處於 Warning 且有單一巨量進程（> 2GB RAM / > 50% CPU）。
   - `ATTENTION`：歷史 Swap 較高、短暫 I/O 觀測較忙、或 Memory Free 位於 30%~40% 邊界但無失控進程。
   - `NORMAL`：指標處於安全區間。
   - `UNKNOWN`：無法確定或無足夠權限取得之數據。
2. **Top Process 語意修正 (Notable != Problem)**：
   - 單一 WebKit / 瀏覽器進程使用 500MB ~ 1.2GB RAM 屬於現代多工作瀏覽器分頁之常見正常負載，標記為 `Notable process`，**嚴禁直接判定為卡頓主因或問題進程**。
   - **嚴禁直接建議終止 WebKit raw PID**（例如禁止 `kill PID 82252`）。建議優先順序：1. 使用者自行檢視分頁並關閉不需要的分頁；2. 瀏覽器若持續卡頓建議正常重啟瀏覽器；3. 只有確認失控且獲明確核准才進行進程終止。
3. **Swap 歷史語意**：
   - 歷史累積 Swap 高（如 20 GB）但當前即時 Memory Pressure 處於 Normal/穩態時，僅為 `Historical memory pressure evidence` 或 `ATTENTION`，**不得直接宣稱為「當前已確認瓶頸」**。
4. **重新啟動 Mac 語意修正**：
   - 重開機分類為 `Low-cost troubleshooting / reset step`。
   - **禁止宣稱「徹底恢復流暢度」、「恢復出廠狀態」或「一定能改善」**。
   - 建議措辭：「如果目前仍有明顯卡頓，可在工作告一段落後正常重新啟動，作為低風險排查步驟；重啟會重置目前程序與 Swap 狀態，但不能保證根本問題消失。」
5. **預期效益措辭嚴謹**：
   - 優先使用「可能降低 Memory Pressure」、「可能釋放約 X MB process RSS」、「可能有助於改善反應速度」，禁止無證據承諾百分比或系統一定變快。
6. **保守 Optimization Gate**：
   - 若 `Confirmed bottleneck = None`，預設回覆 **「目前不需要立即修改系統。」**，不為了交差而硬生產生優化動作。

---

## 2. Agent 標準輸出順序

未找到 Confirmed Bottleneck 時，必須優先明確宣告無確認瓶頸，接著條列各項指標：

```text
Mac Health 診斷與分析報告
────────────────────────

Confirmed bottleneck:
None (目前沒有已確認的效能瓶頸)

Likely contributor:
None

Attention:
• Memory: 歷史 Swap 累計較高 (X GB)，當前 derived pressure 位於 warning 邊界 (Free: Y%)。無單一失控進程。

Normal:
• CPU (即時使用率 X%，負載正常)
• Disk capacity (剩餘 X GB, 空間充足)
• Disk I/O observation (抽樣讀寫平穩)
• Thermal (溫度正常，無熱降頻)
• Spotlight (索引待機正常)

Notable processes:
• com.apple.WebKit.WebContent (PID: X, 650 MB) — 屬於現代多工作網頁常見佔用，未確認異常。

Recommendation:
目前不需要立即修改系統。
若實際仍感到卡頓，可先檢視並關閉確定不需要的瀏覽器分頁；若卡頓持續，可於工作告一段落後正常重新啟動 Mac 作為低風險排查步驟。
```

---

## 3. 安全操作分級 (Safety Levels)

| 等級 | 動作類型 | 規範 |
| :--- | :--- | :--- |
| **READ_ONLY** | 執行 `diagnose.py`、查詢 CPU/RAM/Disk、Mole status/analyze | **自動允許**，無需額外確認 |
| **REVERSIBLE_LOW_RISK** | 重新啟動 Finder 或 Dock (`killall Finder`, `killall Dock`) | **需集中徵詢確認** |
| **WORK_INTERRUPTING** | 關閉特定應用程式、重新啟動 Mac、停止 Docker / VM 服務 | **必須向使用者明確列出目標清單並取得核准** |
| **DESTRUCTIVE** | 磁碟清理、快取刪除 (Mole clean) | **必須先跑 Dry-run，展示目標與大小，取得授權後執行** |
| **PROHIBITED** | 關閉 SIP / Gatekeeper、`sudo rm`、刪除 Keychain、手動 kill 系統核心 Daemon | **永久禁止！** |
