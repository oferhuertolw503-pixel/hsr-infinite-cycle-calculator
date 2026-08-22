"""Command-line argument parsing and command dispatch."""

import argparse
import sys

from .cli_handlers import (
    run_family,
    run_library,
    run_report,
    run_search,
    run_single,
    run_team,
)


def build_parser():
    """Build the public command-line parser."""
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
    return parser


def run_cli(argv=None):
    """Parse arguments and dispatch to one analysis handler."""
    args = build_parser().parse_args(
        argv if argv is not None else sys.argv[1:]
    )

    if args.family:
        return run_family(args.example)
    if args.library:
        return run_library(args.example)
    if args.report:
        return run_report(args.example)
    if args.team:
        return run_team(args.example)
    if args.search:
        return run_search(args.example, team_size=args.team_size,
                          max_rounds=args.max_rounds)
    return run_single(args.example, audit=args.audit,
                      sensitivity=args.sensitivity, repair=args.repair)


if __name__ == "__main__":
    run_cli()
