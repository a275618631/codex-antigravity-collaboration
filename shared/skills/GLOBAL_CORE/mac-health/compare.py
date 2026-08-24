#!/usr/bin/env python3
"""compare.py

mac-health Before / After 診斷快照比對工具。
讀取兩份 JSON 診斷檔並輸出客觀改善判定 (IMPROVED / NO_CHANGE / REGRESSED / INCONCLUSIVE)。
"""

import argparse
import json
import sys
from mac_health.comparator import compare_snapshots


def main() -> None:
    parser = argparse.ArgumentParser(
        description="mac-health Before / After 診斷快照比對工具"
    )
    parser.add_argument("before", type=str, help="改善前診斷報告 JSON 路徑")
    parser.add_argument("after", type=str, help="改善後診斷報告 JSON 路徑")
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式輸出比對結果 (預設為人類可讀格式)",
    )

    args = parser.parse_args()

    try:
        with open(args.before, "r", encoding="utf-8") as f:
            before_data = json.load(f)
        with open(args.after, "r", encoding="utf-8") as f:
            after_data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"讀取報告檔案失敗: {e}\n")
        sys.exit(1)

    result = compare_snapshots(before_data, after_data)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n==========================================")
        print(f"  mac-health Before / After 比對結論: {result['verdict']}")
        print("==========================================")
        if result["improvements"]:
            print("\n[改善項目 (+)]:")
            for item in result["improvements"]:
                print(f"  ✓ {item}")
        if result["regressions"]:
            print("\n[退步/負載增加項目 (-)]:")
            for item in result["regressions"]:
                print(f"  ✗ {item}")
        if not result["improvements"] and not result["regressions"]:
            print("\n[無明顯變化] 關鍵效能指標均處於正常波動範圍內。")
        print("\n詳細指標變化:")
        for k, v in result["metrics_diff"].items():
            print(f"  - {k}: {v}")
        print()


if __name__ == "__main__":
    main()
