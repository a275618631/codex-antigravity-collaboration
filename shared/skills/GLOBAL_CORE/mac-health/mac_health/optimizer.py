"""mac_health.optimizer

安全優化分析器 (RCA / Recommendation Calibration)。
嚴格區分 Confirmed Bottleneck、Likely Contributor、Attention 與 Normal。
避免過度下結論，不把排行高直接當問題，禁止直接建議 kill WebKit PID。
"""

from typing import Any, Dict, List


def generate_optimization_plan(report: Dict[str, Any]) -> Dict[str, Any]:
    """根據診斷報告生成校準後之優化計畫與排除清單。"""
    confirmed_bottlenecks: List[Dict[str, Any]] = []
    likely_contributors: List[Dict[str, Any]] = []
    attention_items: List[Dict[str, Any]] = []
    normal_items: List[Dict[str, Any]] = []
    notable_processes: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    not_recommended: List[Dict[str, Any]] = []

    cpu = report.get("cpu", {})
    mem = report.get("memory", {})
    disk = report.get("disk", {})
    therm = report.get("thermal", {})
    spotlight = report.get("spotlight", {})
    host = report.get("host", {})
    cores = host.get("cpu_cores", 8) or 8

    # 1. 記憶體分析 (Memory Calibration)
    pressure = mem.get("pressure", {})
    pressure_state = pressure.get("state", "unknown")
    free_pct = pressure.get("free_percent")
    swap_used = mem.get("swap_used_bytes", 0) or 0
    top_mem_procs = mem.get("top_processes", [])
    swap_gb = round(swap_used / (1024**3), 1)

    # 檢視前段記憶體進程
    for p in top_mem_procs[:3]:
        rss_mb = round(p.get("rss_bytes", 0) / (1024**2), 1)
        pname = p.get("name", "")
        # 若單一進程在 300MB ~ 1200MB 之間，屬現代瀏覽器/IDE 之正常多工作分頁常見範圍，列為 Notable
        if rss_mb >= 300.0:
            notable_processes.append({
                "pid": p.get("pid"),
                "name": pname,
                "rss_mb": rss_mb,
                "assessment": "Notable process (within typical footprint for active browser/IDE workload, not confirmed abnormal)"
            })

    if pressure_state == "critical":
        confirmed_bottlenecks.append({
            "category": "memory",
            "type": "CONFIRMED BOTTLENECK",
            "detail": f"Memory Pressure 處於 Critical 狀態 (Free: {free_pct}%)，系統面臨嚴重記憶體換頁壓力。"
        })
        # 若有單一佔用 > 1.5GB 的非系統進程，列為建議檢視對象
        if top_mem_procs and round(top_mem_procs[0].get("rss_bytes", 0) / (1024**2), 1) > 1500.0:
            top_p = top_mem_procs[0]
            actions.append({
                "id": "opt-mem-critical",
                "priority": "P1",
                "category": "memory",
                "target": f"{top_p.get('name')} 相關應用程式",
                "action_type": "app_level_review",
                "reason": f"進程佔用達 {round(top_p.get('rss_bytes', 0)/(1024**2), 1)} MB RAM，在 Critical 記憶體壓力下為主要資源消耗來源。",
                "expected_benefit": f"可能釋放約 {round(top_p.get('rss_bytes', 0)/(1024**2), 1)} MB process RSS，可能有助於降低 Memory Pressure。",
                "risk": "low",
                "safety_level": "WORK_INTERRUPTING",
                "requires_approval": True,
                "reversible": True
            })
    elif pressure_state == "warning":
        # 判斷是否有真正失控的進程 (> 2.0 GB)
        runaway_procs = [p for p in top_mem_procs if round(p.get("rss_bytes", 0) / (1024**2), 1) > 2000.0]
        if runaway_procs:
            likely_contributors.append({
                "category": "memory",
                "type": "LIKELY CONTRIBUTOR",
                "detail": f"Memory Pressure 處於 Warning 狀態 (Free: {free_pct}%)，且存在單一巨量記憶體進程 ({runaway_procs[0].get('name')}: {round(runaway_procs[0].get('rss_bytes', 0)/(1024**2), 1)} MB)。"
            })
        else:
            attention_items.append({
                "category": "memory",
                "type": "ATTENTION",
                "detail": f"Memory: 歷史 Swap 累計較高 ({swap_gb} GB)，當前 derived pressure 位於 warning 邊界 (Free: {free_pct}%)。無單一異常失控進程。"
            })
    else:
        # Normal 狀態
        if swap_used > 5 * (1024**3):
            attention_items.append({
                "category": "memory",
                "type": "ATTENTION",
                "detail": f"Memory: 歷史 Swap 累計 {swap_gb} GB (可能為過去負載累積)，但當前即時 Memory Pressure 處於 Normal 正常狀態，無當前記憶體瓶頸。"
            })
        else:
            normal_items.append("Memory (Pressure 正常，Swap 處於低水位)")

        not_recommended.append({
            "target": "手動釋放記憶體 / 清空快取 (Purge RAM)",
            "reason": "目前無 active memory pressure。macOS 自動管理記憶體快取屬正常架構行為，不需亦不建議手動清空。"
        })

    # 2. CPU 分析 (CPU Calibration)
    usage_pct = cpu.get("usage_percent")
    load_avg = cpu.get("load_average", [0, 0, 0])
    top_cpu_procs = cpu.get("top_processes", [])

    if usage_pct is not None and usage_pct > 85.0:
        if top_cpu_procs and top_cpu_procs[0].get("cpu_percent", 0) > 50.0:
            top_c = top_cpu_procs[0]
            confirmed_bottlenecks.append({
                "category": "cpu",
                "type": "CONFIRMED BOTTLENECK",
                "detail": f"CPU 使用率持續高達 {usage_pct}%，主要由 {top_c.get('name')} (PID: {top_c.get('pid')}, {top_c.get('cpu_percent')}%) 佔用。"
            })
            actions.append({
                "id": f"opt-cpu-{top_c.get('pid')}",
                "priority": "P1",
                "category": "cpu",
                "target": f"{top_c.get('name')} 應用程式",
                "action_type": "app_level_review",
                "reason": f"進程持續消耗 {top_c.get('cpu_percent')}% CPU。",
                "expected_benefit": f"可能降低約 {top_c.get('cpu_percent')}% CPU 負載，可能有助於改善系統反應速度與溫度。",
                "risk": "low",
                "safety_level": "WORK_INTERRUPTING",
                "requires_approval": True,
                "reversible": True
            })
        else:
            likely_contributors.append({
                "category": "cpu",
                "type": "LIKELY CONTRIBUTOR",
                "detail": f"CPU 使用率較高 ({usage_pct}%)，由多個進程分散佔用。"
            })
    else:
        normal_items.append(f"CPU (即時使用率 {usage_pct if usage_pct is not None else 'N/A'}%，負載正常)")

    # 3. 磁碟容量分析
    free_gb = round(disk.get("free_bytes", 0) / (1024**3), 1)
    used_pct = disk.get("used_percent", 0.0)
    if free_gb < 15.0 or used_pct > 95.0:
        confirmed_bottlenecks.append({
            "category": "disk",
            "type": "CONFIRMED BOTTLENECK",
            "detail": f"主要 SSD 可用空間即將耗盡 (剩餘 {free_gb} GB, 使用率 {used_pct}%)。"
        })
        actions.append({
            "id": "opt-disk-critical",
            "priority": "P1",
            "category": "disk",
            "target": "快取與暫存檔案唯讀掃描 (Dry-run)",
            "action_type": "cache_cleanup_dryrun",
            "reason": "磁碟剩餘空間極低，需評估可安全釋放的暫存空間。",
            "expected_benefit": "找出可安全釋放的暫存檔案路徑。",
            "risk": "low",
            "safety_level": "READ_ONLY",
            "requires_approval": False,
            "reversible": True
        })
    elif free_gb < 35.0:
        attention_items.append({
            "category": "disk",
            "type": "ATTENTION",
            "detail": f"SSD 剩餘空間低於 35 GB (目前剩餘 {free_gb} GB, 使用率 {used_pct}%)。"
        })
    else:
        normal_items.append(f"Disk capacity (剩餘 {free_gb} GB, 使用率 {used_pct}%, 空間充足)")

    # 4. 磁碟 I/O 觀測
    io_status = disk.get("io", {}).get("status", "unknown")
    if io_status == "observed_busy":
        attention_items.append({
            "category": "disk_io",
            "type": "ATTENTION",
            "detail": "Disk I/O: 1秒抽樣中觀測到短暫較高讀寫活動 (屬瞬間觀測，不代表長期阻塞)。"
        })
    else:
        normal_items.append("Disk I/O observation (抽樣讀寫平穩)")

    # 5. 溫控分析
    therm_status = therm.get("status", "unknown")
    if therm_status in ["warning", "critical"]:
        confirmed_bottlenecks.append({
            "category": "thermal",
            "type": "CONFIRMED BOTTLENECK",
            "detail": f"系統報告溫控降頻狀態: {therm_status}。"
        })
    else:
        normal_items.append("Thermal (溫度正常，無熱降頻)")

    # 6. Spotlight 索引保護
    if spotlight.get("likely_active"):
        attention_items.append({
            "category": "spotlight",
            "type": "ATTENTION",
            "detail": "Spotlight 目前正在建立或更新索引 (系統正常維護工作)。"
        })
        not_recommended.append({
            "target": "Spotlight (mds / mdworker)",
            "reason": "Spotlight 正在進行正常背景索引，請等待其自然完成，嚴禁強制終止進程。"
        })
    else:
        normal_items.append("Spotlight (索引待機正常)")

    # 7. 重啟建議評估 (Troubleshooting / Reset step)
    troubleshooting_notes = []
    if swap_gb > 15.0:
        troubleshooting_notes.append({
            "topic": "重新啟動 Mac (可選排查步驟)",
            "guidance": "如果目前仍有明顯卡頓，可在工作告一段落後正常重新啟動，作為低風險排查步驟；重啟會重置目前程序與 Swap 狀態，但不能保證根本問題消失。"
        })

    # 判定整體狀態與是否需要立即修改
    has_confirmed = len(confirmed_bottlenecks) > 0
    has_likely = len(likely_contributors) > 0
    has_attention = len(attention_items) > 0

    if has_confirmed:
        overall_status = "problem"
        immediate_optimization_required = True
    elif has_likely:
        overall_status = "attention"
        immediate_optimization_required = True
    elif has_attention:
        overall_status = "attention"
        immediate_optimization_required = False
    else:
        overall_status = "healthy"
        immediate_optimization_required = False

    return {
        "status": overall_status,
        "immediate_optimization_required": immediate_optimization_required,
        "confirmed_bottlenecks": confirmed_bottlenecks,
        "likely_contributors": likely_contributors,
        "attention_items": attention_items,
        "normal_items": normal_items,
        "notable_processes": notable_processes,
        "actions": actions,
        "not_recommended": not_recommended,
        "troubleshooting_notes": troubleshooting_notes,
    }
