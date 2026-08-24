"""mac_health.collectors

唯讀系統資訊收集器，封裝 macOS 原生工具呼叫與錯誤防護機制。
嚴格確保安全，不進行任何系統狀態修改。
"""

import os
import plistlib
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from mac_health.parsers import (
    parse_brew_services,
    parse_df_output,
    parse_diskutil_plist,
    parse_iostat,
    parse_memory_pressure,
    parse_pmset_therm,
    parse_power_json,
    parse_ps_processes,
    parse_spotlight_mdutil,
    parse_swapusage,
    parse_top_cpu_line,
    parse_vm_stat,
)


def run_cmd(
    cmd: List[str], timeout: float = 3.0
) -> Tuple[int, str, str, Optional[str]]:
    """安全執行子進程指令。

    回傳: (returncode, stdout, stderr, error_msg)
    """
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr, None
    except FileNotFoundError:
        return 127, "", "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as e:
        return 1, "", "", f"Command failed ({' '.join(cmd)}): {str(e)}"


def collect_host_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集主機基本硬體與作業系統資訊。"""
    warnings: List[str] = []
    errors: List[str] = []
    host_info: Dict[str, Any] = {
        "model": "unknown",
        "chip": "unknown",
        "macos_version": "unknown",
        "memory_bytes": 0,
        "cpu_cores": 0,
    }

    rc, stdout, _, err = run_cmd(["sysctl", "-n", "hw.model", "machdep.cpu.brand_string", "hw.memsize", "hw.ncpu"])
    if err:
        errors.append(err)
    elif rc == 0:
        lines = stdout.strip().splitlines()
        if len(lines) >= 4:
            host_info["model"] = lines[0].strip()
            host_info["chip"] = lines[1].strip()
            try:
                host_info["memory_bytes"] = int(lines[2].strip())
                host_info["cpu_cores"] = int(lines[3].strip())
            except ValueError:
                pass

    rc, stdout, _, err = run_cmd(["sw_vers", "-productVersion"])
    if rc == 0 and stdout.strip():
        host_info["macos_version"] = stdout.strip()
    elif err:
        warnings.append(f"Could not read macos_version: {err}")

    return host_info, warnings, errors


def collect_cpu_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集 CPU 負載、總體使用率與前十大進程。"""
    warnings: List[str] = []
    errors: List[str] = []
    cpu_info: Dict[str, Any] = {
        "load_average": [0.0, 0.0, 0.0],
        "usage_percent": None,
        "top_processes": [],
    }

    try:
        load = os.getloadavg()
        cpu_info["load_average"] = [round(x, 2) for x in load]
    except (OSError, AttributeError) as e:
        warnings.append(f"os.getloadavg failed: {e}")

    rc, stdout, _, _ = run_cmd(["top", "-l", "1", "-n", "0", "-s", "0"], timeout=2.5)
    if rc == 0 and stdout:
        for line in stdout.splitlines()[:15]:
            if "CPU usage" in line:
                cpu_info["usage_percent"] = parse_top_cpu_line(line)
                break

    rc, stdout, _, err = run_cmd(
        ["ps", "-A", "-o", "pid,ppid,%cpu,%mem,rss,command", "-r"],
        timeout=3.0,
    )
    if err:
        errors.append(err)
    elif rc == 0:
        cpu_info["top_processes"] = parse_ps_processes(stdout, max_items=15)

    return cpu_info, warnings, errors


def collect_memory_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集記憶體壓力、Swap 使用量、壓縮記憶體與前十大進程。"""
    warnings: List[str] = []
    errors: List[str] = []
    mem_info: Dict[str, Any] = {
        "pressure": {
            "state": "unknown",
            "source": "derived",
            "free_percent": None,
        },
        "swap_used_bytes": 0,
        "swap_total_bytes": 0,
        "compressed_bytes": None,
        "top_processes": [],
    }

    # 1. 記憶體壓力
    rc, stdout, _, err = run_cmd(["memory_pressure", "-Q"], timeout=2.0)
    if err:
        warnings.append(f"memory_pressure probe failed: {err}")
    elif rc == 0:
        mem_info["pressure"] = parse_memory_pressure(stdout)

    # 2. Swap 用量
    rc, stdout, _, err = run_cmd(["sysctl", "vm.swapusage"], timeout=2.0)
    if err:
        errors.append(err)
    elif rc == 0:
        swap = parse_swapusage(stdout)
        if swap["used_bytes"] is not None:
            mem_info["swap_used_bytes"] = swap["used_bytes"]
        if swap["total_bytes"] is not None:
            mem_info["swap_total_bytes"] = swap["total_bytes"]

    # 3. Compressed Memory (vm_stat)
    rc, stdout, _, err = run_cmd(["vm_stat"], timeout=2.0)
    if rc == 0:
        vm = parse_vm_stat(stdout)
        mem_info["compressed_bytes"] = vm["compressed_bytes"]

    # 4. Top Memory 進程 (依記憶體排序)
    rc, stdout, _, err = run_cmd(
        ["ps", "-A", "-o", "pid,ppid,%cpu,%mem,rss,command", "-m"],
        timeout=3.0,
    )
    if err:
        errors.append(err)
    elif rc == 0:
        mem_info["top_processes"] = parse_ps_processes(stdout, max_items=15)

    return mem_info, warnings, errors


def collect_disk_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集主要 SSD / APFS 空間與 I/O 狀態（精確解析 APFS Container）。"""
    warnings: List[str] = []
    errors: List[str] = []
    disk_info: Dict[str, Any] = {
        "mount": "/System/Volumes/Data",
        "total_bytes": 0,
        "free_bytes": 0,
        "used_bytes": 0,
        "used_percent": 0.0,
        "source": "unknown",
        "source_type": "unknown",
        "io": {
            "status": "unknown",
            "raw_available": False,
            "sample_duration_seconds": 1,
            "sample_count": 2,
        },
    }

    # 1. 優先使用 diskutil info -plist 取得 APFS Container 實際可用與總空間
    diskutil_parsed = None
    try:
        proc = subprocess.run(
            ["diskutil", "info", "-plist", "/System/Volumes/Data"],
            capture_output=True,
            timeout=3.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            pl_data = plistlib.loads(proc.stdout)
            diskutil_parsed = parse_diskutil_plist(pl_data)
    except Exception as e:
        warnings.append(f"diskutil plist probe failed: {e}")

    if diskutil_parsed and diskutil_parsed["total_bytes"] > 0:
        disk_info.update(diskutil_parsed)
    else:
        # Fallback: 使用 df -k /System/Volumes/Data /
        rc, stdout, _, err = run_cmd(["df", "-k", "/System/Volumes/Data", "/"], timeout=2.0)
        if err:
            errors.append(err)
        elif rc == 0:
            parsed_df = parse_df_output(stdout)
            disk_info.update(parsed_df)

    # 2. 短時間 I/O 觀測 (取樣 1 秒)
    rc, stdout, _, err = run_cmd(["iostat", "-c", "2", "-w", "1", "-d"], timeout=3.5)
    if err:
        warnings.append(f"iostat probe failed: {err}")
    elif rc == 0:
        disk_info["io"] = parse_iostat(stdout)

    return disk_info, warnings, errors


def collect_thermal_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集溫控與降頻狀態。"""
    warnings: List[str] = []
    errors: List[str] = []
    thermal_info: Dict[str, Any] = {
        "status": "unknown"
    }

    rc, stdout, _, err = run_cmd(["pmset", "-g", "therm"], timeout=2.0)
    if err:
        thermal_info["status"] = "unavailable"
    elif rc == 0:
        thermal_info = parse_pmset_therm(stdout)
    else:
        thermal_info["status"] = "unavailable"

    return thermal_info, warnings, errors


def collect_battery_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集電池狀態 (MacBook)。"""
    warnings: List[str] = []
    errors: List[str] = []
    battery_info: Dict[str, Any] = {
        "available": False,
        "condition": None,
        "cycle_count": None,
        "charging": None,
        "state_of_charge": None,
        "max_capacity_percent": None,
    }

    rc, stdout, _, err = run_cmd(["system_profiler", "SPPowerDataType", "-json"], timeout=4.0)
    if rc == 0 and stdout:
        battery_info = parse_power_json(stdout)
    else:
        rc_batt, stdout_batt, _, _ = run_cmd(["pmset", "-g", "batt"], timeout=2.0)
        if rc_batt == 0 and "InternalBattery" in stdout_batt:
            battery_info["available"] = True
            if "discharging" in stdout_batt:
                battery_info["charging"] = False
            elif "charging" in stdout_batt:
                battery_info["charging"] = True

    return battery_info, warnings, errors


def collect_spotlight_info(
    all_processes: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集 Spotlight 索引狀態與相關進程。"""
    warnings: List[str] = []
    errors: List[str] = []
    spotlight_info: Dict[str, Any] = {
        "indexing_enabled": None,
        "likely_active": False,
        "related_processes": [],
    }

    rc, stdout, _, err = run_cmd(["mdutil", "-s", "/"], timeout=2.0)
    if err:
        warnings.append(f"mdutil check failed: {err}")
    elif rc == 0:
        spotlight_info["indexing_enabled"] = parse_spotlight_mdutil(stdout)

    spotlight_keywords = ("mds", "mdworker", "mds_stores", "mdworker_shared")
    related: List[Dict[str, Any]] = []
    active_cpu_sum = 0.0

    for proc in all_processes:
        pname = proc.get("name", "").lower()
        if any(kw in pname for kw in spotlight_keywords):
            related.append(proc)
            active_cpu_sum += proc.get("cpu_percent", 0.0)

    spotlight_info["related_processes"] = related
    spotlight_info["likely_active"] = active_cpu_sum > 15.0

    return spotlight_info, warnings, errors


def collect_background_info() -> Tuple[Dict[str, Any], List[str], List[str]]:
    """收集開機/登入項目與背景服務摘要。"""
    warnings: List[str] = []
    errors: List[str] = []
    bg_info: Dict[str, Any] = {
        "login_items_count": None,  # 無法無權限 100% 正確獲取時標記為 None (unavailable)
        "launch_agents_count": 0,
        "launch_daemons_count": 0,
        "brew_services": [],
        "notable_items": [],
    }

    user_agents = os.path.expanduser("~/Library/LaunchAgents")
    sys_agents = "/Library/LaunchAgents"
    sys_daemons = "/Library/LaunchDaemons"

    for path, key in [
        (user_agents, "launch_agents_count"),
        (sys_agents, "launch_agents_count"),
        (sys_daemons, "launch_daemons_count"),
    ]:
        if os.path.exists(path) and os.path.isdir(path):
            try:
                files = [f for f in os.listdir(path) if f.endswith(".plist")]
                bg_info[key] += len(files)
            except OSError:
                pass

    rc, stdout, _, _ = run_cmd(["brew", "services", "list"], timeout=3.0)
    if rc == 0 and stdout:
        bg_info["brew_services"] = parse_brew_services(stdout)

    return bg_info, warnings, errors
