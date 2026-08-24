"""mac_health.mole_adapter

Mole 外部工具適配器。
優先使用官方 CLI `mo` (fallback `mole`)，以 machine-readable (--json) 介面與 Dry-run 模式操作。
嚴格禁止自動執行任何破壞性修改。
"""

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class MoleAdapter:
    def __init__(self, preferred_binary: Optional[str] = None, binary_name: Optional[str] = None):
        target = preferred_binary or binary_name
        if target:
            self.binary_path = shutil.which(target)
        else:
            # 官方 CLI binary 為 `mo`，fallback 為 `mole`
            self.binary_path = shutil.which("mo") or shutil.which("mole")

    def is_available(self) -> bool:
        """檢查系統中是否已安裝 Mole (mo)。"""
        return self.binary_path is not None

    def get_version(self) -> Optional[str]:
        """取得 Mole 版本資訊。"""
        if not self.is_available():
            return None
        try:
            res = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def get_status(self) -> Dict[str, Any]:
        """執行 mo status --json 取得系統健康快照。"""
        if not self.is_available():
            return {
                "available": False,
                "status": "unavailable",
                "error": "Mole CLI (mo) not found on system.",
            }
        try:
            res = subprocess.run(
                [self.binary_path, "status", "--json"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout)
                    return {"available": True, "status": "success", "data": data}
                except json.JSONDecodeError:
                    return {"available": True, "status": "success", "raw": res.stdout.strip()}
            return {
                "available": True,
                "status": "failed",
                "returncode": res.returncode,
                "error": res.stderr.strip() or "Empty output",
            }
        except Exception as e:
            return {"available": True, "status": "error", "error": str(e)}

    def analyze(self) -> Dict[str, Any]:
        """執行 mo analyze --json 取得空間佔用深度分析。"""
        if not self.is_available():
            return {
                "available": False,
                "status": "unavailable",
                "error": "Mole CLI (mo) not found on system.",
            }
        try:
            res = subprocess.run(
                [self.binary_path, "analyze", "--json"],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout)
                    return {"available": True, "status": "success", "data": data}
                except json.JSONDecodeError:
                    return {"available": True, "status": "success", "raw": res.stdout.strip()}
            return {
                "available": True,
                "status": "failed",
                "returncode": res.returncode,
                "error": res.stderr.strip() or "Empty output",
            }
        except Exception as e:
            return {"available": True, "status": "error", "error": str(e)}

    def dry_run_clean(self) -> Dict[str, Any]:
        """執行 mo clean --dry-run 取得清理候選清單與估算容量，嚴格不刪除檔案。"""
        if not self.is_available():
            return {
                "available": False,
                "status": "unavailable",
                "error": "Mole CLI (mo) not found on system.",
            }
        try:
            res = subprocess.run(
                [self.binary_path, "clean", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )

            # 檢查 ~/.config/mole/clean-list.txt 是否存在
            clean_list_path = os.path.expanduser("~/.config/mole/clean-list.txt")
            categorized_targets: Dict[str, List[str]] = {
                "cache": [],
                "logs": [],
                "temporary": [],
                "app_leftovers": [],
                "developer_artifacts": [],
                "browser_cache": [],
                "other": [],
            }
            total_items = 0

            if os.path.exists(clean_list_path):
                try:
                    with open(clean_list_path, "r", encoding="utf-8") as f:
                        for line in f:
                            item = line.strip()
                            if not item:
                                continue
                            total_items += 1
                            item_lower = item.lower()
                            if "cache" in item_lower:
                                if any(b in item_lower for b in ("chrome", "safari", "arc", "firefox", "browser")):
                                    categorized_targets["browser_cache"].append(item)
                                else:
                                    categorized_targets["cache"].append(item)
                            elif "log" in item_lower:
                                categorized_targets["logs"].append(item)
                            elif "tmp" in item_lower or "temp" in item_lower:
                                categorized_targets["temporary"].append(item)
                            elif any(d in item_lower for d in ("node_modules", ".cargo", ".gradle", "deriveddata")):
                                categorized_targets["developer_artifacts"].append(item)
                            elif "application support" in item_lower or "leftover" in item_lower:
                                categorized_targets["app_leftovers"].append(item)
                            else:
                                categorized_targets["other"].append(item)
                except Exception:
                    pass

            return {
                "available": True,
                "status": "success" if res.returncode == 0 else "failed",
                "dry_run": True,
                "returncode": res.returncode,
                "raw_output": res.stdout,
                "total_candidate_items": total_items,
                "categorized_targets": categorized_targets,
                "clean_list_file": clean_list_path if os.path.exists(clean_list_path) else None,
                "error": res.stderr if res.returncode != 0 else None,
            }
        except Exception as e:
            return {"available": True, "status": "error", "error": str(e)}

    def dry_run_optimize(self) -> Dict[str, Any]:
        """執行 mo optimize --dry-run 取得系統維護建議。"""
        if not self.is_available():
            return {
                "available": False,
                "status": "unavailable",
                "error": "Mole CLI (mo) not found on system.",
            }
        try:
            res = subprocess.run(
                [self.binary_path, "optimize", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
            return {
                "available": True,
                "status": "success" if res.returncode == 0 else "failed",
                "dry_run": True,
                "returncode": res.returncode,
                "raw_output": res.stdout,
                "error": res.stderr if res.returncode != 0 else None,
            }
        except Exception as e:
            return {"available": True, "status": "error", "error": str(e)}
