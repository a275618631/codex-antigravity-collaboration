"""tests/test_diagnose.py

單元測試與純函式解析器驗證 (涵蓋 Case A ~ Case F、MoleAdapter、Optimizer 校準測試 Case 1 ~ Case 6、Comparator 及 Schema 驗證)。
使用 Python 標準庫 unittest 實作。
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from diagnose import run_diagnostics
from mac_health.comparator import compare_snapshots
from mac_health.mole_adapter import MoleAdapter
from mac_health.optimizer import generate_optimization_plan
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


def load_fixture(name: str) -> str:
    path = os.path.join(PROJECT_ROOT, "tests", "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestMacHealthParsers(unittest.TestCase):
    """測試純函式解析器。"""

    def test_case_a_idle_parsers(self):
        """Case A: 正常待機資料解析，不誤報異常。"""
        pres = parse_memory_pressure(load_fixture("memory_pressure.txt"))
        self.assertEqual(pres["state"], "normal")
        self.assertEqual(pres["source"], "derived")
        self.assertEqual(pres["free_percent"], 65.0)

        therm = parse_pmset_therm(load_fixture("pmset_therm.txt"))
        self.assertEqual(therm["status"], "normal")

        power = parse_power_json(load_fixture("power.json"))
        self.assertTrue(power["available"])
        self.assertEqual(power["condition"], "Good")
        self.assertEqual(power["cycle_count"], 98)
        self.assertEqual(power["max_capacity_percent"], 90)

    def test_case_b_cpu_processes(self):
        """Case B: CPU 進程提取與排序。"""
        raw_ps = load_fixture("ps_cpu.txt")
        procs = parse_ps_processes(raw_ps, max_items=10)
        self.assertGreaterEqual(len(procs), 3)
        self.assertEqual(procs[0]["name"], "Google")
        self.assertAlmostEqual(procs[0]["cpu_percent"], 95.5)

        cpu_usage = parse_top_cpu_line("CPU usage: 15.2% user, 5.0% sys, 79.8% idle")
        self.assertAlmostEqual(cpu_usage, 20.2)

    def test_case_c_memory_and_swap(self):
        """Case C: 記憶體與 Swap 解析。"""
        swap = parse_swapusage(load_fixture("swapusage.txt"))
        self.assertIsNotNone(swap["used_bytes"])
        self.assertGreater(swap["used_bytes"], 10 * 1024 * 1024 * 1024)

        vm = parse_vm_stat(load_fixture("vm_stat.txt"))
        self.assertEqual(vm["page_size_bytes"], 16384)
        self.assertGreater(vm["compressed_bytes"], 0)

        pres_crit = parse_memory_pressure("System-wide memory free percentage: 15%")
        self.assertEqual(pres_crit["state"], "critical")

        pres_warn = parse_memory_pressure("System-wide memory free percentage: 35%")
        self.assertEqual(pres_warn["state"], "warning")

    def test_case_d_disk_and_io(self):
        """Case D: 磁碟空間與 I/O 解析。"""
        df_res = parse_df_output(load_fixture("df.txt"))
        self.assertEqual(df_res["mount"], "/")
        self.assertGreater(df_res["total_bytes"], 0)
        self.assertGreater(df_res["free_bytes"], 0)
        self.assertEqual(df_res["used_percent"], 5.0)

        plist_mock = {
            "APFSContainerSize": 1000000000000,
            "APFSContainerFree": 300000000000,
            "MountPoint": "/System/Volumes/Data",
        }
        apfs_res = parse_diskutil_plist(plist_mock)
        self.assertIsNotNone(apfs_res)
        self.assertEqual(apfs_res["total_bytes"], 1000000000000)
        self.assertEqual(apfs_res["free_bytes"], 300000000000)
        self.assertEqual(apfs_res["used_bytes"], 700000000000)
        self.assertEqual(apfs_res["used_percent"], 70.0)

        io_res = parse_iostat(load_fixture("iostat.txt"))
        self.assertTrue(io_res["raw_available"])
        self.assertEqual(io_res["status"], "observed_busy")
        self.assertGreater(io_res["max_tps"], 3000)

        normal_iostat = "disk0\nKB/t tps MB/s\n10.0 50 0.5\n10.0 60 0.6\n"
        io_normal_res = parse_iostat(normal_iostat)
        self.assertEqual(io_normal_res["status"], "observed_low")

    def test_case_e_spotlight(self):
        """Case E: Spotlight 狀態判定。"""
        self.assertTrue(parse_spotlight_mdutil("/:\n\tIndexing enabled."))
        self.assertFalse(parse_spotlight_mdutil("/:\n\tIndexing disabled."))


class TestOptimizerCalibration(unittest.TestCase):
    """測試優化分析器的 RCA 校準規則 (Case 1 ~ Case 6)。"""

    def test_calib_case_1_high_swap_normal_pressure(self):
        """CASE 1: Swap 很高 (20GB) + current pressure normal (55%) + 無 runaway -> 不得判定 current bottleneck。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 15.0, "load_average": [1.2, 1.3, 1.4]},
            "memory": {
                "pressure": {"state": "normal", "free_percent": 55.0},
                "swap_used_bytes": 20 * (1024**3),
                "top_processes": [{"name": "Finder", "pid": 100, "rss_bytes": 150 * (1024**2)}],
            },
            "disk": {"free_bytes": 250 * (1024**3), "used_percent": 70.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertEqual(len(plan["confirmed_bottlenecks"]), 0, "不得判定為 confirmed bottleneck")
        self.assertFalse(plan["immediate_optimization_required"], "不得強制要求立即修改系統")
        # 應歸類為 Attention / 歷史記憶體證據
        self.assertTrue(any("歷史 Swap" in item["detail"] for item in plan["attention_items"]))

    def test_calib_case_2_webkit_moderate_footprint(self):
        """CASE 2: 單一 WebKit process 500-900 MB -> 不得自動判定為 root cause，不得建議 kill PID。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 20.0, "load_average": [1.5, 1.5, 1.5]},
            "memory": {
                "pressure": {"state": "warning", "free_percent": 35.0},
                "swap_used_bytes": 10 * (1024**3),
                "top_processes": [{"name": "com.apple.WebKit.WebContent", "pid": 82252, "rss_bytes": 700 * (1024**2)}],
            },
            "disk": {"free_bytes": 250 * (1024**3), "used_percent": 70.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertEqual(len(plan["confirmed_bottlenecks"]), 0)
        # WebKit 應被歸類為 Notable process 而非 confirmed bottleneck
        self.assertTrue(any(p["pid"] == 82252 for p in plan["notable_processes"]))
        # 確保沒有任何建議叫使用者直接 kill PID
        for action in plan["actions"]:
            self.assertNotIn("kill", action.get("target", "").lower())

    def test_calib_case_3_no_confirmed_bottleneck(self):
        """CASE 3: Confirmed bottleneck = None -> immediate_optimization_required 為 False。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 10.0, "load_average": [1.0, 1.0, 1.0]},
            "memory": {"pressure": {"state": "normal", "free_percent": 60.0}, "swap_used_bytes": 1 * (1024**3)},
            "disk": {"free_bytes": 300 * (1024**3), "used_percent": 65.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertFalse(plan["immediate_optimization_required"])
        self.assertEqual(len(plan["actions"]), 0)

    def test_calib_case_4_restart_as_troubleshooting_only(self):
        """CASE 4: 歷史 Swap 高時，restart 只能是 troubleshooting_notes 建議，不得宣稱一定改善。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 15.0},
            "memory": {"pressure": {"state": "normal", "free_percent": 50.0}, "swap_used_bytes": 22 * (1024**3)},
            "disk": {"free_bytes": 200 * (1024**3), "used_percent": 70.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertTrue(len(plan["troubleshooting_notes"]) > 0)
        note = plan["troubleshooting_notes"][0]["guidance"]
        self.assertIn("排查步驟", note)
        self.assertIn("不能保證根本問題消失", note)
        self.assertNotIn("徹底恢復流暢度", note)

    def test_calib_case_5_top_ram_process_reasonable_magnitude(self):
        """CASE 5: Top RAM process 排名第一但絕對使用量合理 (350MB) -> Notable != Problem。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 12.0},
            "memory": {
                "pressure": {"state": "normal", "free_percent": 55.0},
                "swap_used_bytes": 2 * (1024**3),
                "top_processes": [{"name": "Arc", "pid": 689, "rss_bytes": 350 * (1024**2)}],
            },
            "disk": {"free_bytes": 200 * (1024**3), "used_percent": 70.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertEqual(len(plan["confirmed_bottlenecks"]), 0)
        self.assertEqual(len(plan["likely_contributors"]), 0)

    def test_calib_case_6_true_severe_memory_workload(self):
        """CASE 6: 真正嚴重記憶體負載 (Critical 壓力且單一進程 > 2GB) -> 判定為 Confirmed bottleneck。"""
        report = {
            "host": {"cpu_cores": 8},
            "cpu": {"usage_percent": 30.0},
            "memory": {
                "pressure": {"state": "critical", "free_percent": 12.0},
                "swap_used_bytes": 25 * (1024**3),
                "top_processes": [{"name": "RunawayApp", "pid": 99999, "rss_bytes": 2500 * (1024**2)}],
            },
            "disk": {"free_bytes": 200 * (1024**3), "used_percent": 70.0},
            "thermal": {"status": "normal"},
            "spotlight": {"likely_active": False},
        }
        plan = generate_optimization_plan(report)
        self.assertEqual(len(plan["confirmed_bottlenecks"]), 1)
        self.assertEqual(plan["confirmed_bottlenecks"][0]["category"], "memory")
        self.assertTrue(plan["immediate_optimization_required"])


class TestMoleAdapterAndComparator(unittest.TestCase):
    """測試 Mole 介面與快照比對器。"""

    def test_mole_adapter_behavior(self):
        mole = MoleAdapter(preferred_binary="non_existent_mo_bin")
        self.assertFalse(mole.is_available())
        self.assertIsNone(mole.get_version())
        self.assertEqual(mole.analyze()["status"], "unavailable")

    def test_compare_improved(self):
        before = {
            "cpu": {"usage_percent": 85.0, "load_average": [8.0, 6.0, 4.0]},
            "memory": {"pressure": {"state": "warning", "free_percent": 25.0}, "swap_used_bytes": 5000000000},
            "disk": {"free_bytes": 100000000000},
        }
        after = {
            "cpu": {"usage_percent": 20.0, "load_average": [2.0, 3.0, 3.5]},
            "memory": {"pressure": {"state": "normal", "free_percent": 55.0}, "swap_used_bytes": 4000000000},
            "disk": {"free_bytes": 102000000000},
        }
        res = compare_snapshots(before, after)
        self.assertEqual(res["verdict"], "IMPROVED")


class TestMacHealthCollectorsAndFaultTolerance(unittest.TestCase):
    """測試收集器容錯機制與即時 JSON Schema。"""

    def test_case_f_partial_failure_tolerance(self):
        with patch("mac_health.collectors.run_cmd") as mock_run, patch("subprocess.run") as mock_sub:
            mock_run.return_value = (127, "", "", "Command not found: simulated")
            mock_sub.side_effect = Exception("Simulated subprocess failure")

            report = run_diagnostics()
            self.assertEqual(report["schema_version"], "1.1")
            self.assertIn("optimization_plan", report)


if __name__ == "__main__":
    unittest.main()
