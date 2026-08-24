"""mac_health.comparator

Before / After 快照對比器。
根據前後兩份診斷報告的客觀指標計算改善程度並判定 Verdict。
具備進程消長分析、Load Average 衰減滯後容錯與一級指標加權機制。
"""

from typing import Any, Dict


def compare_snapshots(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """比較兩份診斷報告並產出結構化比對與 Verdict。"""
    b_cpu = before.get("cpu", {})
    a_cpu = after.get("cpu", {})
    b_mem = before.get("memory", {})
    a_mem = after.get("memory", {})
    b_disk = before.get("disk", {})
    a_disk = after.get("disk", {})

    metrics_diff: Dict[str, Any] = {}
    primary_improvements = []
    primary_regressions = []
    secondary_improvements = []
    secondary_regressions = []
    diff_cpu = None

    # 1. Top Process 消長分析 (一級指標)
    b_top_cpu = b_cpu.get("top_processes", [])
    a_top_pids = {p.get("pid") for p in a_cpu.get("top_processes", [])}
    if b_top_cpu:
        highest_b = b_top_cpu[0]
        if highest_b.get("cpu_percent", 0) >= 40.0 and highest_b.get("pid") not in a_top_pids:
            primary_improvements.append(
                f"高負載進程已消除：{highest_b.get('name')} (PID: {highest_b.get('pid')}, 原佔用 {highest_b.get('cpu_percent')}%) 已不在活躍高負載清單中"
            )

    # 2. CPU Usage 比較 (一級指標)
    b_usage = b_cpu.get("usage_percent")
    a_usage = a_cpu.get("usage_percent")
    if b_usage is not None and a_usage is not None:
        diff_cpu = round(a_usage - b_usage, 2)
        metrics_diff["cpu_usage_percent"] = {
            "before": b_usage,
            "after": a_usage,
            "delta": diff_cpu,
        }
        if diff_cpu <= -10.0:
            primary_improvements.append(f"CPU 使用率顯著下降了 {abs(diff_cpu)}% (從 {b_usage}% 降至 {a_usage}%)")
        elif diff_cpu >= 25.0 and not primary_improvements:
            primary_regressions.append(f"CPU 使用率上升了 {diff_cpu}% (從 {b_usage}% 升至 {a_usage}%)")

    # 3. CPU Load 比較 (二級滯後指標)
    b_load = b_cpu.get("load_average", [0, 0, 0])
    a_load = a_cpu.get("load_average", [0, 0, 0])
    if b_load and a_load:
        delta_load1 = round(a_load[0] - b_load[0], 2)
        metrics_diff["load_average_1m"] = {
            "before": b_load[0],
            "after": a_load[0],
            "delta": delta_load1,
        }
        if delta_load1 <= -0.8:
            secondary_improvements.append(f"1分鐘系統負載下降了 {abs(delta_load1)}")
        elif delta_load1 >= 2.0:
            if primary_improvements:
                metrics_diff["load_average_lag_note"] = "Load average 存在指數平滑滯後，屬正常過渡現象"
            else:
                secondary_regressions.append(f"1分鐘系統負載上升了 {delta_load1}")

    # 4. Memory Pressure & Free Percent 比較 (一級指標)
    b_pressure = b_mem.get("pressure", {})
    a_pressure = a_mem.get("pressure", {})
    b_state = b_pressure.get("state")
    a_state = a_pressure.get("state")
    b_free = b_pressure.get("free_percent")
    a_free = a_pressure.get("free_percent")

    state_rank = {"normal": 3, "warning": 2, "critical": 1, "unknown": 0}
    if b_state and a_state:
        metrics_diff["memory_pressure_state"] = {"before": b_state, "after": a_state}
        if state_rank.get(a_state, 0) > state_rank.get(b_state, 0):
            primary_improvements.append(f"Memory Pressure 狀態改善：從 {b_state} 轉為 {a_state}")
        elif state_rank.get(a_state, 0) < state_rank.get(b_state, 0):
            primary_regressions.append(f"Memory Pressure 狀態惡化：從 {b_state} 轉為 {a_state}")

    if b_free is not None and a_free is not None:
        delta_free = round(a_free - b_free, 1)
        metrics_diff["memory_free_percent"] = {
            "before": b_free,
            "after": a_free,
            "delta": delta_free,
        }
        if delta_free >= 8.0:
            primary_improvements.append(f"可用記憶體百分比提升了 {delta_free}%")
        elif delta_free <= -12.0:
            primary_regressions.append(f"可用記憶體百分比下降了 {abs(delta_free)}%")

    # 5. Swap 比較
    b_swap = b_mem.get("swap_used_bytes", 0) or 0
    a_swap = a_mem.get("swap_used_bytes", 0) or 0
    delta_swap_mb = round((a_swap - b_swap) / (1024**2), 1)
    metrics_diff["swap_used_mb"] = {
        "before": round(b_swap / (1024**2), 1),
        "after": round(a_swap / (1024**2), 1),
        "delta": delta_swap_mb,
    }
    if delta_swap_mb <= -300:
        secondary_improvements.append(f"Swap 佔用釋放了 {abs(delta_swap_mb)} MB")
    elif delta_swap_mb >= 800:
        secondary_regressions.append(f"Swap 佔用增加了 {delta_swap_mb} MB")

    # 6. Disk Free 比較
    b_disk_free = b_disk.get("free_bytes", 0) or 0
    a_disk_free = a_disk.get("free_bytes", 0) or 0
    delta_disk_mb = round((a_disk_free - b_disk_free) / (1024**2), 1)
    metrics_diff["disk_free_mb"] = {
        "before": round(b_disk_free / (1024**2), 1),
        "after": round(a_disk_free / (1024**2), 1),
        "delta": delta_disk_mb,
    }
    if delta_disk_mb >= 500:
        secondary_improvements.append(f"磁碟可用空間增加了 {delta_disk_mb} MB")
    elif delta_disk_mb <= -1500:
        secondary_regressions.append(f"磁碟可用空間減少了 {abs(delta_disk_mb)} MB")

    all_improvements = primary_improvements + secondary_improvements
    all_regressions = primary_regressions + secondary_regressions

    # 7. 判定 Verdict (加權判定)
    if primary_improvements and not primary_regressions:
        verdict = "IMPROVED"
    elif primary_regressions and not primary_improvements:
        verdict = "REGRESSED"
    elif not primary_improvements and not primary_regressions:
        if secondary_improvements and not secondary_regressions:
            verdict = "IMPROVED"
        elif secondary_regressions and not secondary_improvements:
            verdict = "REGRESSED"
        else:
            verdict = "NO_CHANGE"
    else:
        verdict = "INCONCLUSIVE"

    return {
        "verdict": verdict,
        "summary": f"比對結果判定為：{verdict}",
        "improvements": all_improvements,
        "regressions": all_regressions,
        "metrics_diff": metrics_diff,
    }
