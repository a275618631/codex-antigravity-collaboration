#!/usr/bin/env python3
"""mac-health diagnose.py

極簡、唯讀、低風險的 macOS 系統健康狀態結構化診斷工具。
輸出合規之 JSON 格式，供 AI Agent 進行根因分析 (RCA) 與安全優化規劃。
"""

import argparse
import datetime
import json
import sys
from typing import Any, Dict

from mac_health.collectors import (
    collect_background_info,
    collect_battery_info,
    collect_cpu_info,
    collect_disk_info,
    collect_host_info,
    collect_memory_info,
    collect_spotlight_info,
    collect_thermal_info,
)
from mac_health.optimizer import generate_optimization_plan


def run_diagnostics(include_plan: bool = True) -> Dict[str, Any]:
    """執行全套唯讀系統健康診斷並彙整為標準化字典。"""
    all_warnings = []
    all_errors = []

    # 1. Host
    host_info, w_host, e_host = collect_host_info()
    all_warnings.extend(w_host)
    all_errors.extend(e_host)

    # 2. CPU
    cpu_info, w_cpu, e_cpu = collect_cpu_info()
    all_warnings.extend(w_cpu)
    all_errors.extend(e_cpu)

    # 3. Memory
    mem_info, w_mem, e_mem = collect_memory_info()
    all_warnings.extend(w_mem)
    all_errors.extend(e_mem)

    # 4. Disk
    disk_info, w_disk, e_disk = collect_disk_info()
    all_warnings.extend(w_disk)
    all_errors.extend(e_disk)

    # 5. Thermal
    thermal_info, w_therm, e_therm = collect_thermal_info()
    all_warnings.extend(w_therm)
    all_errors.extend(e_therm)

    # 6. Battery
    batt_info, w_batt, e_batt = collect_battery_info()
    all_warnings.extend(w_batt)
    all_errors.extend(e_batt)

    # 7. Spotlight
    all_procs = cpu_info.get("top_processes", []) + mem_info.get("top_processes", [])
    spotlight_info, w_spot, e_spot = collect_spotlight_info(all_procs)
    all_warnings.extend(w_spot)
    all_errors.extend(e_spot)

    # 8. Background
    bg_info, w_bg, e_bg = collect_background_info()
    all_warnings.extend(w_bg)
    all_errors.extend(e_bg)

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()

    report: Dict[str, Any] = {
        "schema_version": "1.1",
        "timestamp": now.isoformat(),
        "host": host_info,
        "cpu": cpu_info,
        "memory": mem_info,
        "disk": disk_info,
        "thermal": thermal_info,
        "battery": batt_info,
        "spotlight": spotlight_info,
        "background": bg_info,
        "warnings": all_warnings,
        "errors": all_errors,
    }

    if include_plan:
        report["optimization_plan"] = generate_optimization_plan(report)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="極簡、唯讀的 macOS 系統健康診斷工具 (輸出 JSON)"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="輸出緊湊單行 JSON (預設為格式化 pretty JSON)",
    )
    parser.add_argument(
        "--no-plan",
        action="store_true",
        help="不包含建議優化計畫 (僅輸出原始硬體指標)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="將結果寫入指定檔案路徑，而非 stdout",
    )

    args = parser.parse_args()

    report = run_diagnostics(include_plan=not args.no_plan)

    indent = None if args.compact else 2
    json_str = json.dumps(report, indent=indent, ensure_ascii=False)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_str)
                f.write("\n")
        except OSError as e:
            sys.stderr.write(f"Failed to write output to {args.output}: {e}\n")
            sys.exit(1)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
