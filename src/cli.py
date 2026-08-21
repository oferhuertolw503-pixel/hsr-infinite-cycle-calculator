"""Command-line entry point for the cycle analyzer.

Examples:

    python main.py examples/himeko_nova_cycle_demo.json
    python main.py examples/theory_document/four_node_model_N5.json
    python main.py examples/theory_document/seven_node_family.json --family
    python main.py examples/theory_document/four_node_kill_energy.json --audit

The wording of the conclusions follows the theory document section 6: a
spectral radius above 1 is reported as a growth direction of the linear
approximation, never as a proof of a practical infinite loop.
"""

import argparse
import sys

from .analyzer.audit import CycleAudit
from .data_loader.matrix_loader import load_example_json, load_family, load_transfer_matrix
from .matrix.transfer_matrix import TransferMatrix


def _print_perron(model):
    freqs = model.perron_frequencies()
    print("\nPerron 相对频率(§4):")
    print(f"  主导特征值: {freqs['eigenvalue']:.6g}"
          f"  实根: {freqs['real']}  非负: {freqs['positive']}")
    for row in freqs["table"]:
        flag = "  <-- 最小份额,优先核对" if row.get("flagged_as_scarce") else ""
        print(f"  {row['node']:>10s}  {row['frequency']:.6f}{flag}")


def _print_single(path, audit=False):
    data = load_example_json(path)
    model = TransferMatrix(data["matrix"], node_names=data.get("nodes"))

    print("=" * 60)
    print("HSR 永动机矩阵分析")
    print("=" * 60)
    print("模型:", data.get("name", path))
    print("事件节点:", ", ".join(model.node_names))

    result = model.classify()
    print(f"\n谱半径 rho(A) = {result['rho']:.6g}  regime: {result['regime']}")
    print("结论:", result["conclusion"])
    for caveat in result["caveats"]:
        print("  * 注意:", caveat)

    documented_rho = data.get("documented_rho")
    if documented_rho is not None:
        match = abs(result["rho"] - float(documented_rho)) <= data.get("tolerance", 1e-5)
        print(f"\n文档对照(§6): 记录值 {documented_rho} -> 一致: {match}")

    _print_perron(model)

    if audit:
        print("\n--- §7 复核流程审计 ---")
        audit_result = CycleAudit(
            data["matrix"],
            node_names=data.get("nodes"),
            edge_meta=data.get("edge_meta"),
            sequence=data.get("sequence"),
            enemy_av0=data.get("enemy_av0"),
            perturbations=data.get("perturbations"),
            mode_note=data.get("mode_note"),
        ).run()
        for key, step in audit_result["steps"].items():
            note = step.get("note") if isinstance(step, dict) else None
            if note:
                print(f"[{key}] {note}")
        print("审计完整性: 全部步骤完成" if audit_result["all_done"] else
              "审计完整性: 部分步骤缺少数据(时序序列/扰动用例),需人工补齐")
    return result


def _print_family(path):
    family = load_family(path)
    sweep = family.regime_sweep()
    print("=" * 60)
    print("HSR 永动机矩阵分析 (参数族)")
    print("=" * 60)
    print("模型:", family.name)
    print(f"参数: {sweep['parameter']}  谱半径范围: "
          f"{sweep['rho_range'][0]:.6g} .. {sweep['rho_range'][1]:.6g}")
    print("单调递增:", sweep["monotone_increasing"], " regimes:", sweep["regimes"])
    print(f"\n{'N':>4s}  {'rho(A)':>10s}  {'regime':>8s}  {'不可约':>6s}  {'对照§6':>8s}")
    for row in sweep["rows"]:
        match = "一致" if row["matches_target"] else ("-" if row["target_rho"] is None else "偏差")
        print(f"{row['key']:>4s}  {row['rho']:10.6g}  {row['regime']:>8s}  "
              f"{str(row['irreducible']):>6s}  {match:>8s}")
    if family.notes:
        print("\n说明:", family.notes)
    return sweep


def run_cli(argv=None):
    parser = argparse.ArgumentParser(
        prog="hsr-infinite-cycle-calculator",
        description="崩铁永动机资源转移矩阵分析与复核",
    )
    parser.add_argument("example", help="示例 JSON 路径")
    parser.add_argument("--family", action="store_true",
                        help="按参数族(N 依赖矩阵)分析")
    parser.add_argument("--audit", action="store_true",
                        help="运行 §7 八步复核流程审计")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.family:
        return _print_family(args.example)
    return _print_single(args.example, audit=args.audit)


if __name__ == "__main__":
    run_cli()
