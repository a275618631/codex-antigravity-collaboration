"""mac_health.parsers

純函式解析器集合，將 macOS 原生 CLI 與 plist/JSON 輸出轉換為標準化資料型別。
不執行任何 I/O 或 subprocess。
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def parse_vm_stat(raw_text: str) -> Dict[str, Any]:
    """解析 vm_stat 命令輸出。"""
    result: Dict[str, Any] = {
        "page_size_bytes": 4096,
        "free_bytes": 0,
        "active_bytes": 0,
        "inactive_bytes": 0,
        "speculative_bytes": 0,
        "wired_bytes": 0,
        "compressed_bytes": 0,
        "purgeable_bytes": 0,
    }
    if not raw_text:
        return result

    page_size = 4096
    ps_match = re.search(r"page size of (\d+) bytes", raw_text, re.IGNORECASE)
    if ps_match:
        page_size = int(ps_match.group(1))
    result["page_size_bytes"] = page_size

    key_mapping = {
        "Pages free": "free_bytes",
        "Pages active": "active_bytes",
        "Pages inactive": "inactive_bytes",
        "Pages speculative": "speculative_bytes",
        "Pages wired down": "wired_bytes",
        "Pages occupied by compressor": "compressed_bytes",
        "Pages stored in compressor": "compressed_bytes",
        "Pages purgeable": "purgeable_bytes",
    }

    for line in raw_text.splitlines():
        if ":" not in line:
            continue
        parts = line.split(":", 1)
        k = parts[0].strip().strip('"')
        val_str = parts[1].strip().rstrip(".")
        if not val_str.isdigit():
            continue
        pages = int(val_str)
        if k in key_mapping:
            result[key_mapping[k]] = pages * page_size

    return result


def parse_swapusage(raw_text: str) -> Dict[str, Optional[int]]:
    """解析 sysctl vm.swapusage 輸出。"""
    res: Dict[str, Optional[int]] = {
        "total_bytes": None,
        "used_bytes": None,
        "free_bytes": None,
    }
    if not raw_text:
        return res

    def _to_bytes(num_str: str, unit: str) -> int:
        val = float(num_str)
        u = unit.upper()
        if u == "K":
            return int(val * 1024)
        elif u == "M":
            return int(val * 1024 * 1024)
        elif u == "G":
            return int(val * 1024 * 1024 * 1024)
        elif u == "B":
            return int(val)
        return int(val)

    pattern = re.compile(
        r"total\s*=\s*([\d\.]+)([KMGBkmgb])\s+used\s*=\s*([\d\.]+)([KMGBkmgb])\s+free\s*=\s*([\d\.]+)([KMGBkmgb])"
    )
    match = pattern.search(raw_text)
    if match:
        t_val, t_unit, u_val, u_unit, f_val, f_unit = match.groups()
        res["total_bytes"] = _to_bytes(t_val, t_unit)
        res["used_bytes"] = _to_bytes(u_val, u_unit)
        res["free_bytes"] = _to_bytes(f_val, f_unit)
    return res


def parse_memory_pressure(raw_text: str) -> Dict[str, Any]:
    """解析 memory_pressure -Q 輸出並轉換為結構化狀態。

    輸出範例：
    The system has 17179869184 (1048576 pages with a page size of 16384).
    System-wide memory free percentage: 33%

    狀態定義（derived heuristic）：
    >= 50% -> normal
    20% - 49% -> warning
    < 20% -> critical
    """
    res: Dict[str, Any] = {
        "state": "unknown",
        "source": "derived",
        "free_percent": None,
    }
    if not raw_text:
        return res

    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", raw_text)
    if match:
        pct = float(match.group(1))
        res["free_percent"] = pct
        if pct >= 50:
            res["state"] = "normal"
        elif pct >= 20:
            res["state"] = "warning"
        else:
            res["state"] = "critical"
        return res

    lower = raw_text.lower()
    if "pressure: normal" in lower or "normal" in lower:
        res["state"] = "normal"
    elif "pressure: warn" in lower or "warning" in lower:
        res["state"] = "warning"
    elif "pressure: critical" in lower or "critical" in lower:
        res["state"] = "critical"

    return res


def parse_df_output(raw_text: str) -> Dict[str, Any]:
    """解析 df 輸出（支援 /System/Volumes/Data 或 /）。"""
    res: Dict[str, Any] = {
        "mount": "/",
        "total_bytes": 0,
        "used_bytes": 0,
        "free_bytes": 0,
        "used_percent": 0.0,
        "source": "df",
        "source_type": "posix_vfs",
    }
    if not raw_text:
        return res

    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return res

    # 優先尋找 /System/Volumes/Data 行，否則取最後一行
    target_line = lines[-1]
    for l in lines[1:]:
        if "/System/Volumes/Data" in l:
            target_line = l
            break

    tokens = target_line.split()
    if len(tokens) >= 6:
        try:
            total_1k = int(tokens[1])
            used_1k = int(tokens[2])
            avail_1k = int(tokens[3])
            pct_str = tokens[4].rstrip("%")
            mount = tokens[-1]

            res["mount"] = mount
            res["total_bytes"] = total_1k * 1024
            res["used_bytes"] = used_1k * 1024
            res["free_bytes"] = avail_1k * 1024
            res["used_percent"] = float(pct_str)
            res["source"] = f"df {mount}"
        except (ValueError, IndexError):
            pass
    return res


def parse_diskutil_plist(pl_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """從 diskutil info -plist /System/Volumes/Data 解析 APFS Container 空間。"""
    if not pl_data:
        return None

    try:
        container_size = pl_data.get("APFSContainerSize") or pl_data.get("TotalSize")
        container_free = pl_data.get("APFSContainerFree")

        if container_size is not None and container_free is not None:
            total = int(container_size)
            free = int(container_free)
            used = max(0, total - free)
            used_pct = round((used / total) * 100.0, 1) if total > 0 else 0.0

            return {
                "mount": pl_data.get("MountPoint", "/System/Volumes/Data"),
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "used_percent": used_pct,
                "source": "diskutil APFSContainer",
                "source_type": "apfs_container",
                "volume_group_id": pl_data.get("APFSVolumeGroupID"),
            }
    except Exception:
        pass
    return None


def parse_ps_processes(raw_text: str, max_items: int = 10) -> List[Dict[str, Any]]:
    """解析 ps -A -o pid,ppid,%cpu,%mem,rss,command 輸出。"""
    processes: List[Dict[str, Any]] = []
    if not raw_text:
        return processes

    lines = raw_text.strip().splitlines()
    if not lines:
        return processes

    data_lines = lines[1:]

    for line in data_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = line_clean.split(None, 5)
        if len(parts) < 6:
            continue

        try:
            pid = int(parts[0])
            ppid = int(parts[1])
            cpu_pct = float(parts[2])
            mem_pct = float(parts[3])
            rss_kb = int(parts[4])
            command = parts[5]

            raw_name = command.split()[0] if command else "unknown"
            name = raw_name.split("/")[-1]

            processes.append(
                {
                    "pid": pid,
                    "ppid": ppid,
                    "name": name,
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem_pct,
                    "rss_bytes": rss_kb * 1024,
                    "command": command,
                }
            )
        except (ValueError, IndexError):
            continue

        if len(processes) >= max_items:
            break

    return processes


def parse_top_cpu_line(raw_text: str) -> Optional[float]:
    """解析 top 中的 CPU usage 總佔比。"""
    if not raw_text:
        return None
    match = re.search(r"([\d\.]+)%\s*idle", raw_text)
    if match:
        try:
            idle = float(match.group(1))
            return round(max(0.0, min(100.0, 100.0 - idle)), 2)
        except ValueError:
            pass
    return None


def parse_iostat(raw_text: str) -> Dict[str, Any]:
    """解析 iostat -c 2 -w 1 -d 輸出。"""
    res: Dict[str, Any] = {
        "status": "unknown",
        "raw_available": False,
        "sample_duration_seconds": 1,
        "sample_count": 2,
        "max_tps": 0.0,
        "max_mb_per_sec": 0.0,
    }
    if not raw_text:
        return res

    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return res

    res["raw_available"] = True
    data_lines = []
    for line in lines:
        tokens = line.split()
        if tokens and all(re.match(r"^[\d\.]+$", t) for t in tokens):
            data_lines.append(tokens)

    if not data_lines:
        return res

    latest_sample = data_lines[-1]
    max_tps = 0.0
    max_mb = 0.0
    idx = 0
    while idx + 2 < len(latest_sample):
        try:
            tps = float(latest_sample[idx + 1])
            mb = float(latest_sample[idx + 2])
            if tps > max_tps:
                max_tps = tps
            if mb > max_mb:
                max_mb = mb
        except ValueError:
            pass
        idx += 3

    res["max_tps"] = max_tps
    res["max_mb_per_sec"] = max_mb

    if max_tps > 2000 or max_mb > 100.0:
        res["status"] = "observed_busy"
    else:
        res["status"] = "observed_low"

    return res


def parse_pmset_therm(raw_text: str) -> Dict[str, str]:
    """解析 pmset -g therm 輸出。"""
    res = {"status": "unknown"}
    if not raw_text:
        res["status"] = "unavailable"
        return res

    lower = raw_text.lower()
    if "no thermal warning" in lower or "cpu_speed_limit = 100" in lower:
        res["status"] = "normal"
    elif "warning" in lower or "threat" in lower:
        res["status"] = "warning"
    elif "critical" in lower or "emergency" in lower:
        res["status"] = "critical"
    elif "not supported" in lower or "error" in lower:
        res["status"] = "unavailable"
    else:
        res["status"] = "normal"
    return res


def parse_power_json(raw_json: str) -> Dict[str, Any]:
    """解析 system_profiler SPPowerDataType -json 輸出。"""
    res: Dict[str, Any] = {
        "available": False,
        "condition": None,
        "cycle_count": None,
        "charging": None,
        "state_of_charge": None,
        "max_capacity_percent": None,
    }
    if not raw_json:
        return res

    try:
        data = json.loads(raw_json)
        power_items = data.get("SPPowerDataType", [])
        for item in power_items:
            charge_info = item.get("sppower_battery_charge_info", {})
            health_info = item.get("sppower_battery_health_info", {})
            if health_info or charge_info:
                res["available"] = True
                if "sppower_battery_cycle_count" in health_info:
                    try:
                        res["cycle_count"] = int(health_info["sppower_battery_cycle_count"])
                    except (ValueError, TypeError):
                        pass
                if "sppower_battery_health" in health_info:
                    res["condition"] = str(health_info["sppower_battery_health"])
                if "sppower_battery_health_maximum_capacity" in health_info:
                    cap_str = str(health_info["sppower_battery_health_maximum_capacity"]).rstrip("%")
                    try:
                        res["max_capacity_percent"] = int(cap_str)
                    except ValueError:
                        pass
                if "sppower_battery_is_charging" in charge_info:
                    val = charge_info["sppower_battery_is_charging"]
                    res["charging"] = val.upper() == "TRUE" if isinstance(val, str) else bool(val)
                if "sppower_battery_state_of_charge" in charge_info:
                    try:
                        res["state_of_charge"] = int(charge_info["sppower_battery_state_of_charge"])
                    except (ValueError, TypeError):
                        pass
                break
    except Exception:
        pass

    return res


def parse_spotlight_mdutil(raw_text: str) -> Optional[bool]:
    """解析 mdutil -s / 輸出。"""
    if not raw_text:
        return None
    lower = raw_text.lower()
    if "indexing enabled" in lower:
        return True
    elif "indexing disabled" in lower:
        return False
    return None


def parse_brew_services(raw_text: str) -> List[Dict[str, str]]:
    """解析 brew services list 表格輸出。"""
    services: List[Dict[str, str]] = []
    if not raw_text:
        return services

    lines = raw_text.strip().splitlines()
    if not lines or "Name" not in lines[0]:
        return services

    for line in lines[1:]:
        tokens = line.split()
        if len(tokens) >= 2:
            services.append(
                {
                    "name": tokens[0],
                    "status": tokens[1],
                    "user": tokens[2] if len(tokens) > 2 else "",
                }
            )
    return services
