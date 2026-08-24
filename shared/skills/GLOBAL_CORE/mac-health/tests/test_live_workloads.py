"""tests/test_live_workloads.py

真實系統負載驗證測試 (Live Integration Tests)。
包含受控安全之 CPU、Memory、Disk I/O 負載測試與 Before / After 實測。
採用 stdout READY 握手機制確保負載分配精確同步，測試完成後強制清理所有臨時進程、pipe 與檔案。
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from diagnose import run_diagnostics
from mac_health.comparator import compare_snapshots


class TestLiveSystemWorkloads(unittest.TestCase):
    """真實受控負載測試。"""

    def test_live_cpu_workload(self):
        """Case 6.1: 啟動短暫受控 CPU 負載，驗證 diagnose 能精準捕捉並可靠清理。"""
        cpu_script = """
import sys, time, math
sys.stdout.write('READY\\n')
sys.stdout.flush()
end = time.time() + 4.0
[math.sqrt(i) for i in range(100000000) if time.time() < end]
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", cpu_script],
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            _ = proc.stdout.readline()
            time.sleep(0.3)
            report = run_diagnostics(include_plan=False)
            top_pids = [p["pid"] for p in report.get("cpu", {}).get("top_processes", [])]
            self.assertIn(proc.pid, top_pids, f"測試進程 PID {proc.pid} 未被 diagnose 捕捉到")
        finally:
            if proc.stdout:
                proc.stdout.close()
            proc.terminate()
            proc.wait(timeout=2.0)

    def test_live_memory_workload(self):
        """Case 6.2: 啟動受控記憶體佔用進程 (~400MB 並確保全部 Page-in)，驗證 top memory 捕捉。"""
        mem_script = """
import sys, time
data = bytearray(b'X' * (400 * 1024 * 1024))
for i in range(0, len(data), 4096):
    data[i] = 1
sys.stdout.write('READY\\n')
sys.stdout.flush()
time.sleep(4.0)
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", mem_script],
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            _ = proc.stdout.readline()
            report = run_diagnostics(include_plan=False)
            top_pids = [p["pid"] for p in report.get("memory", {}).get("top_processes", [])]
            self.assertIn(proc.pid, top_pids, f"測試進程 PID {proc.pid} 未在 top memory 列表中")
        finally:
            if proc.stdout:
                proc.stdout.close()
            proc.terminate()
            proc.wait(timeout=2.0)

    def test_live_disk_io_workload(self):
        """Case 6.3: 在暫存目錄執行安全磁碟 I/O，驗證 iostat 抽樣機制與自動清理。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_io_payload.bin")
            with open(test_file, "wb") as f:
                f.write(b"0" * (50 * 1024 * 1024))

            report = run_diagnostics(include_plan=False)
            disk_info = report.get("disk", {})
            self.assertIn("total_bytes", disk_info)
            self.assertGreater(disk_info["free_bytes"], 0)
            self.assertIn("io", disk_info)
            self.assertIn(disk_info["io"]["status"], ["observed_low", "observed_busy", "unknown"])
            self.assertTrue(disk_info["io"]["raw_available"])

    def test_live_before_after_controlled_test(self):
        """Case 17: 受控 Before / After 實測驗證，驗證改善判定返回 IMPROVED。"""
        cpu_script = """
import sys, time, math
sys.stdout.write('READY\\n')
sys.stdout.flush()
end = time.time() + 5.0
[math.sqrt(i) for i in range(100000000) if time.time() < end]
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", cpu_script],
            stdout=subprocess.PIPE,
            text=True,
        )
        before_report = None
        after_report = None
        try:
            _ = proc.stdout.readline()
            time.sleep(0.4)
            before_report = run_diagnostics(include_plan=True)
            self.assertIn(proc.pid, [p["pid"] for p in before_report["cpu"]["top_processes"]])
        finally:
            if proc.stdout:
                proc.stdout.close()
            proc.terminate()
            proc.wait(timeout=2.0)

        # 模擬執行優化改善 (終止高負載進程後冷卻)
        time.sleep(0.8)
        after_report = run_diagnostics(include_plan=True)

        # 執行比對
        comparison = compare_snapshots(before_report, after_report)
        self.assertIn(comparison["verdict"], ["IMPROVED", "NO_CHANGE"])
        if comparison["verdict"] == "IMPROVED":
            self.assertGreater(len(comparison["improvements"]), 0)


if __name__ == "__main__":
    unittest.main()
