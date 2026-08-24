# mac-health

極簡、唯讀、低風險的 macOS 系統健康診斷、根因分析 (RCA)、安全優化規劃與 Before/After 效果驗證工具，專為 AI Agent 設計。

---

## 1. 核心定位與解決問題

- **精準 APFS 空間計算**：直接解析 APFS Container 實際可用空間（`/System/Volumes/Data`），不再誤報唯讀系統卷軸的 5% 容量。
- **客觀 Memory Pressure 語意**：區分 Apple 原生 raw 指標與 derived 狀態判斷，明確指出「高 Swap 不代表此刻必有瓶頸」。
- **防禦性安全優化計畫 (Optimization Plan)**：自動產出包含 P1/P2、預期效益、安全等級與風險的建議清單，並明確標記「不建議處理」的正常系統背景工作（如 Spotlight indexing）。
- **Before / After 閉環驗證 (`compare.py`)**：以客觀指標前後對比，判定 `IMPROVED` / `NO_CHANGE` / `REGRESSED` / `INCONCLUSIVE`。
- **外部工具適配 (`MoleAdapter`)**：唯讀探測與 Dry-run 支援，未安裝時優雅降級不報錯。
- **集中審查閘門 (Approval Gate)**：多項系統建議操作集中一次徵詢，避免反覆中斷。

---

## 2. 專案架構

```text
mac-health/
├── SKILL.md                    # AI Agent 技能指引（RCA 決策流程、安全等級、日常 UX、報告範本）
├── diagnose.py                 # 主程式進入點（輸出 Schema 1.1 JSON 報告）
├── compare.py                  # Before / After 診斷快照比對工具
├── mac_health/                 # 核心模組
│   ├── __init__.py
│   ├── collectors.py           # 原生指令收集器（APFS plist、vm_stat、ps、iostat 取樣等）
│   ├── parsers.py              # 純函式解析器（完全解耦、零外部副作用）
│   ├── optimizer.py            # 安全優化分析器（產生 Optimization Plan）
│   ├── comparator.py           # 快照比對引擎（計算指標變化與判定 Verdict）
│   └── mole_adapter.py         # Mole 外部工具唯讀與 Dry-run 適配器
├── README.md                   # 完整專案說明與操作手冊
├── docs/
│   ├── SAFETY.md               # 操作安全模型與等級規範 (READ_ONLY ~ PROHIBITED)
│   └── FUTURE_WORK.md          # 未來演進規劃
└── tests/
    ├── test_diagnose.py        # 單元測試 (Case A ~ F, Parsers, Optimizer, Mole, Comparator)
    ├── test_live_workloads.py  # 真實受控系統負載測試 (Live CPU, Memory, Disk I/O, Before/After)
    └── fixtures/               # 測試用原始輸出資料
```

---

## 3. 使用方式

### 1. 執行系統健康診斷
```bash
# 輸出格式化 JSON 診斷報告（包含 Optimization Plan）
python3 diagnose.py

# 輸出緊湊單行 JSON
python3 diagnose.py --compact

# 輸出至指定檔案
python3 diagnose.py -o before.json
```

### 2. 執行 Before / After 改善驗收對比
```bash
python3 compare.py before.json after.json
```

### 3. 執行全套測試 (包含 Live Workloads)
```bash
python3 -m unittest discover -s tests -v
```

---

## 4. JSON Schema 1.1 範例

```json
{
  "schema_version": "1.1",
  "timestamp": "2026-08-23T17:44:00.123456+08:00",
  "host": {
    "model": "MacBookPro18,3",
    "chip": "Apple M1 Pro",
    "macos_version": "26.5.2",
    "memory_bytes": 17179869184,
    "cpu_cores": 8
  },
  "cpu": {
    "load_average": [2.15, 2.50, 2.65],
    "usage_percent": 24.5,
    "top_processes": []
  },
  "memory": {
    "pressure": {
      "state": "warning",
      "source": "derived",
      "free_percent": 32.0
    },
    "swap_used_bytes": 22390442557,
    "swap_total_bytes": 23622320128,
    "compressed_bytes": 7391019008,
    "top_processes": []
  },
  "disk": {
    "mount": "/System/Volumes/Data",
    "total_bytes": 994662584320,
    "used_bytes": 719503933440,
    "free_bytes": 275158650880,
    "used_percent": 72.3,
    "source": "diskutil APFSContainer",
    "source_type": "apfs_container",
    "io": {
      "status": "observed_low",
      "raw_available": true,
      "sample_duration_seconds": 1,
      "sample_count": 2,
      "max_tps": 180.0,
      "max_mb_per_sec": 5.2
    }
  },
  "thermal": {
    "status": "normal"
  },
  "battery": {
    "available": true,
    "condition": "Good",
    "cycle_count": 101,
    "charging": false,
    "state_of_charge": 80,
    "max_capacity_percent": 87
  },
  "spotlight": {
    "indexing_enabled": true,
    "likely_active": false,
    "related_processes": []
  },
  "background": {
    "login_items_count": null,
    "launch_agents_count": 12,
    "launch_daemons_count": 9,
    "brew_services": []
  },
  "optimization_plan": {
    "status": "attention",
    "bottlenecks": [
      {
        "category": "memory",
        "severity": "warning",
        "detail": "Memory Pressure 處於 Warning 狀態 (Free: 32.0%)，Swap 佔用 20.8 GB。"
      }
    ],
    "actions": [
      {
        "id": "opt-mem-29585",
        "priority": "P2",
        "category": "memory",
        "target": "com.apple.WebKit.WebContent (PID: 29585)",
        "action_type": "user_app_recommendation",
        "reason": "佔用 480.6 MB RAM，在記憶體警告狀態下建議關閉未使用分頁或重啟應用程式。",
        "expected_benefit": "釋放約 480.6 MB 記憶體。",
        "risk": "low",
        "safety_level": "WORK_INTERRUPTING",
        "requires_approval": true,
        "reversible": true
      }
    ],
    "not_recommended": [
      {
        "target": "Spotlight (mds / mdworker)",
        "reason": "Spotlight 索引為系統正常維護工作，嚴禁手動強制終止。"
      }
    ]
  },
  "warnings": [],
  "errors": []
}
```

---

## 5. 安全保證

- **零破壞性操作**：所有 collector、optimizer、compare 與 mole adapter 均為 100% 唯讀或 Dry-run。
- **零外部依賴**：100% 使用 Python 3 標準庫與 macOS 原生指令。
- **無 sudo / 提權需求**：一般使用者權限即可完整運作。
