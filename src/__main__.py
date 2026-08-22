"""Command-line entry point for the calculator and bundled checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .calculator import calculate
from .cases import print_verification, verify_cases


def _calculate_file(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = calculate(data["matrix"])
    print(data.get("name", path.stem))
    print(f"谱半径 rho = {result['rho']:.8f}")
    print(f"判断：{result['regime']}")
    print("主导特征向量：", result["dominant_vector"])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="资源转移矩阵计算器")
    parser.add_argument("file", nargs="?", type=Path, help="包含 matrix 字段的 JSON")
    args = parser.parse_args()

    if args.file is not None:
        return _calculate_file(args.file)

    results = verify_cases()
    print_verification(results)
    return 0 if all(item["passed"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
