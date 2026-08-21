"""Command-line entry point for the cycle analyzer.

Examples:

    python main.py examples/himeko_nova_cycle_demo.json
    python main.py examples/theory_document/four_node_model_N5.json
    python main.py examples/theory_document/seven_node_family.json --family
    python main.py examples/theory_document/four_node_kill_energy.json --audit
    python main.py examples/theory_document/version_matrix_library.json --library
    python main.py examples/theory_document/audit_workflow_demo.json --report

The wording of the conclusions follows the theory document section 6: a
spectral radius above 1 is reported as a growth direction of the linear
approximation, never as a proof of a practical infinite loop.
"""

import argparse
import json
import sys

from .analyzer.audit import CycleAudit
from .analyzer.bottleneck import BottleneckAnalyzer
from .analyzer.cycle_detector import CycleDetector
from .analyzer.optimizer import CycleRepairPlanner, critical_parameter
from .analyzer.report import Report
from .analyzer.team_search import TeamSearch
from .data_loader.character_loader import load_character_validated
from .data_loader.matrix_loader import (
    load_example_json,
    load_family,
    load_matrix_library,
    load_transfer_matrix,
)
from .matrix.transfer_matrix import TransferMatrix
from .simulation.priority import PriorityEditor, apply_priority_overrides
from .simulation.speed_engine import SpeedBattleEngine, unit_from_character_data
from .simulation.timed_engine import TimedBattleEngine, TimedEvent


def _print_perron(model):
    freqs = model.perron_frequencies()
    print("\nPerron 相对频率(§4):")
    print(f"  主导特征值: {freqs['eigenvalue']:.6g}"
          f"  实根: {freqs['real']}  非负: {freqs['positive']}")
    for row in freqs["table"]:
        flag = "  <-- 最小份额,优先核对" if row.get("flagged_as_scarce") else ""
        print(f"  {row['node']:>10s}  {row['frequency']:.6f}{flag}")


def _print_sensitivity(model, top=5):
    analysis = BottleneckAnalyzer(model).analyze()
    print("\n瓶颈与敏感性分析(§4/§8):")
    if analysis["analytic"]:
        print(f"  解析梯度 d_rho/d_a_ij = u_i*v_j 可用"
              f"  (与数值差分最大相对误差 {analysis['max_relative_error']:.2e})")
    else:
        print("  解析梯度不可用,排序退化为数值差分")
    scarce = analysis["scarce_node"]
    if scarce:
        print(f"  最小份额节点: {scarce['node']} (frequency="
              f"{scarce['frequency']:.6f})  <-- 最先断粮候选(§4)")
    print(f"  决定性资源边 Top{top} (边际敏感度 |d rho/d a_ij|):")
    for row in analysis["decisive_edges"][:top]:
        print(f"    {row['from']:>10s} -> {row['to']:<10s} a_ij={row['value']:.4f}"
              f"  d_rho={row['d_rho']:+.6f}")
    print(f"  脆弱边 Top{top} (整边移除后 rho 跌幅,对应'一次未击杀'):")
    for row in analysis["fragile_edges"][:top]:
        flag = "" if row["load_bearing"] else "  (非承重)"
        print(f"    {row['from']:>10s} -> {row['to']:<10s} a_ij={row['value']:.4f}"
              f"  移除后 rho={row['drop_rho']:.6g} (delta {row['drop_delta']:+.4f}){flag}")
    if analysis["dormant_edges"]:
        print(f"  潜在新边 Top3 (新增一条转移边的边际收益):")
        for row in analysis["dormant_edges"][:3]:
            print(f"    {row['from']:>10s} -> {row['to']:<10s} d_rho={row['d_rho']:+.6f}")
    return analysis


def _print_repair(model, target_rho=1.0, top=5):
    plan = CycleRepairPlanner(model).plan(target_rho=target_rho)
    print(f"\n循环修复规划(自动寻找循环组合,目标 rho>={target_rho}):")
    if not plan["needed"]:
        print(f"  rho(A)={plan['rho']:.6g} 已达/超过目标,无需修复。")
        return plan
    if plan["best"] is None:
        print("  任何单边干预在界限内都无法达到目标谱半径;")
        print("  须改循环结构(加边/换节点)或提高目标数。")
        return plan
    print(f"  基矩阵 rho={plan['rho']:.6g},按干预量排序的最小修复:")
    for row in plan["candidates"][:top]:
        kind = f"系数 x{row['multiplier']:.4f}" if row["kind"] == "boost" else "新增边"
        print(f"    {row['from']:>10s} -> {row['to']:<10s} {kind}"
              f"  a_ij: {row['value']:.4f} -> {row['new_value']:.4f}"
              f"  (增加 {row['added']:.4f},rho -> {row['achieved_rho']:.6g})")
    print("  * " + plan["note"])
    return plan


def _print_single(path, audit=False, sensitivity=False, repair=False):
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

    if sensitivity:
        _print_sensitivity(model)

    if repair:
        _print_repair(model)

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
        perturbation = audit_result["steps"]["perturbation"]
        if perturbation.get("cases"):
            print("\n扰动用例结果(§7 步骤 7):")
            base_rho = perturbation["base"]["rho"]
            print(f"  基矩阵 rho={base_rho:.6g} regime={perturbation['base']['regime']}")
            for row in perturbation["cases"]:
                flip = "  <-- regime 翻转!" if row["regime_flipped"] else ""
                print(f"  {row['label']:<24s} rho={row['rho']:.6g} "
                      f"delta={row['delta_rho']:+.4f} regime={row['regime']}{flip}")
        if audit_result["steps"]["timing"].get("stable") is not None:
            timing = audit_result["steps"]["timing"]
            print(f"\n时序模拟(§5.3/§5.4): stable={timing['stable']} "
                  f"loops={timing['loops_completed']} "
                  f"break={timing['break_reason']}")
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
    critical = critical_parameter(family)
    print(f"\n临界参数(§8 目标数从哪里进入系统): {critical['status']}")
    print(f"  {critical['note']}")
    if family.notes:
        print("\n说明:", family.notes)
    return sweep


def _print_library(path):
    library = load_matrix_library(path)
    comparison = library.compare()
    print("=" * 60)
    print("HSR 永动机矩阵分析 (版本/模式矩阵库, §7 步骤 8)")
    print("=" * 60)
    print("库:", comparison["library"])
    rho_range = comparison["rho_range"]
    range_text = (
        f"{rho_range[0]:.6g} .. {rho_range[1]:.6g}" if rho_range else "(空)"
    )
    print(f"变体数: {len(comparison['rows'])}  "
          f"regimes: {comparison['regimes']}  rho 范围: {range_text}")
    print(f"\n{'变体':<24s}  {'版本':<14s}  {'模式':<8s}  {'敌方机制':<24s}  "
          f"{'rho(A)':>10s}  {'regime':>8s}  {'不可约':>6s}")
    for row in comparison["rows"]:
        print(f"{row['name']:<24s}  {str(row.get('version', '-')):<14s}  "
              f"{str(row.get('mode', '-')):<8s}  "
              f"{str(row.get('enemy', '-')):<24s}  "
              f"{row['rho']:10.6g}  {row['regime']:>8s}  "
              f"{str(row['irreducible']):>6s}")
    for node_set, names in comparison["node_groups"].items():
        print(f"\n节点粒度 [{'/'.join(node_set)}]: {', '.join(names)}")
    consensus = ("一致" if comparison["consensus"]
                 else "不一致 --> 结论上下文绑定,禁止外推")
    print(f"\nregime 一致性: {consensus}")
    for warning in comparison["warnings"]:
        print("  * 警告:", warning)
    if library.notes:
        print("\n说明:", library.notes)
    return comparison


def _print_report(path):
    data = load_example_json(path)
    model = TransferMatrix(data["matrix"], node_names=data.get("nodes"))
    timing = None
    if data.get("sequence"):
        sequence = [
            TimedEvent(**item) if isinstance(item, dict) else item
            for item in data["sequence"]
        ]
        timing = TimedBattleEngine(
            sequence, enemy_av0=data.get("enemy_av0") or 100.0
        ).run({"energy": 0.0, "skill_points": 0.0})
    report = Report(model).generate(timing)
    print(report["text"])
    return report


def _print_team(path):
    data = load_example_json(path)
    character_paths = data.get("characters") or data.get("team")
    if not character_paths:
        raise ValueError(f"{path} needs a 'characters' (or legacy 'team') list")
    units = [
        unit_from_character_data(load_character_validated(character_path))
        for character_path in character_paths
    ]
    overrides = data.get("priority_overrides")
    if overrides:
        apply_priority_overrides(units, overrides)

    sim = data.get("simulation", {})
    engine = SpeedBattleEngine(
        units,
        enemy_speed=float(data.get("enemy_speed", 132.0)),
        max_rounds=int(sim.get("turns", sim.get("max_rounds", 1000))),
    )
    result = engine.run(
        initial_energy=float(sim.get("initial_energy", 0.0)),
        initial_sp=float(sim.get("initial_skill_points", 3.0)),
    )
    cycle = CycleDetector().analyze(result)

    print("=" * 60)
    print("HSR 永动机队伍模拟 (SpeedBattleEngine, 游戏侧数据)")
    print("=" * 60)
    print("队伍:", ", ".join(
        f"{u.name}(速度 {u.speed:g})" for u in units))
    print(f"敌方速度: {engine.enemy_speed:g}  上限轮数: {engine.max_rounds}")
    print("\n动作优先级表 (数值越小越先出手):")
    for row in PriorityEditor(units).view():
        status = "启用" if row["enabled"] else "禁用"
        kind = "插入" if row["inserted"] else "通常"
        print(f"  {row['unit']:>10s}  {row['action']:<18s} "
              f"priority={row['priority']:g}  {kind}  {status}")
    print(f"\n模拟结果: rounds={result['rounds']} "
          f"cycles={result['cycles_completed']} "
          f"enemy_actions={result['enemy_actions']} "
          f"break={result['break_reason']}")
    for name, count in result["ult_count"].items():
        print(f"  {name:>10s} 终结技次数: {count}")
    print(f"\n断轴判定(§8): stable={cycle['stable']} "
          f"类别={cycle['break_class']}")
    print(" ", cycle["note"])
    return {"result": result, "cycle": cycle}


def _print_search(path, team_size=None, max_rounds=None, top=10):
    data = load_example_json(path)
    character_paths = data.get("characters") or data.get("team")
    if not character_paths:
        raise ValueError(f"{path} needs a 'characters' (or legacy 'team') list")
    pool = [load_character_validated(p) for p in character_paths]
    search_config = data.get("search", {})
    team_size = team_size if team_size is not None else search_config.get("team_size")
    if max_rounds is None:
        max_rounds = search_config.get(
            "max_rounds", data.get("simulation", {}).get("turns", 200)
        )
    sim = data.get("simulation", {})

    searcher = TeamSearch(
        pool,
        enemy_speed=float(data.get("enemy_speed", 132.0)),
        team_size=team_size,
        max_rounds=int(max_rounds),
        initial_energy=float(sim.get("initial_energy", 0.0)),
        initial_sp=float(sim.get("initial_skill_points", 3.0)),
    )
    result = searcher.search()

    print("=" * 60)
    print("HSR 永动机队伍搜索 (模拟器层:组合 x 优先级枚举)")
    print("=" * 60)
    print("角色池:", ", ".join(
        d.get("name", d.get("id")) for d in pool))
    print(f"队伍规模: {searcher.team_size}  敌方速度: {searcher.enemy_speed:g}"
          f"  轮数预算: {searcher.max_rounds}")
    print(f"枚举候选: {result['searched']}")

    print(f"\n稳定性排行 Top{min(top, len(result['rows']))} "
          "(持续 > 循环数 > §8 断轴类别 > 终结技数):")
    header = (f"  {'#':>2s}  {'队伍':<30s}  {'循环':>4s}  "
              f"{'断轴':>8s}  {'终结技':>4s}  排轴")
    print(header)
    for rank, row in enumerate(result["rows"][:top], start=1):
        rotation = _format_rotation(row["overrides"])
        print(f"  {rank:>2d}  {'+'.join(row['roster']):<30s}  "
              f"{row['cycles_completed']:>4d}  "
              f"{row['break_class']:>8s}  {row['total_ults']:>4d}  "
              f"{rotation}")

    best = result["best"]
    if best is not None:
        print("\n最优排轴 (可粘贴进队伍文件 priority_overrides):")
        print(json.dumps(best["overrides"], ensure_ascii=False, indent=2))
    print("\n" + result["note"])
    return result


def _format_rotation(overrides):
    """Compact 'unit: a>b(crossed)' rotation summary for the table."""
    parts = []
    for unit, actions in overrides.items():
        enabled = sorted(
            (spec["priority"], name) for name, spec in actions.items()
            if spec.get("enabled", True)
        )
        parts.append(f"{unit}: " + ">".join(name for _, name in enabled))
    return "; ".join(parts)


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
    parser.add_argument("--sensitivity", action="store_true",
                        help="瓶颈与敏感性分析:决定性资源边/脆弱边/潜在新边(§4/§8)")
    parser.add_argument("--repair", action="store_true",
                        help="循环修复规划:达到 rho>=1 的最小单边干预(目标数族请用 --family)")
    parser.add_argument("--library", action="store_true",
                        help="按版本/模式矩阵库对比分析(§7 步骤 8)")
    parser.add_argument("--report", action="store_true",
                        help="输出完整报告:谱半径+Perron+瓶颈敏感性+时序断轴分类")
    parser.add_argument("--team", action="store_true",
                        help="按队伍 JSON 运行速度引擎(角色数据+优先级编辑+断轴分类)")
    parser.add_argument("--search", action="store_true",
                        help="按角色池 JSON 枚举队伍组合与优先级,按稳定性排序给出最优排轴")
    parser.add_argument("--team-size", type=int, default=None,
                        help="--search 的队伍规模(默认:池内全部角色)")
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="--search 的轮数预算(默认:200 或文件内 search.max_rounds)")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.family:
        return _print_family(args.example)
    if args.library:
        return _print_library(args.example)
    if args.report:
        return _print_report(args.example)
    if args.team:
        return _print_team(args.example)
    if args.search:
        return _print_search(args.example, team_size=args.team_size,
                             max_rounds=args.max_rounds)
    return _print_single(args.example, audit=args.audit,
                         sensitivity=args.sensitivity, repair=args.repair)


if __name__ == "__main__":
    run_cli()
