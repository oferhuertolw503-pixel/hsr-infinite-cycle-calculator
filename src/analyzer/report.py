"""One-shot structured report over the current analysis pipeline.

Aggregates the matrix-level conclusions (regime, Perron frequencies,
bottleneck elasticity, fragile edges) with the discrete timing verdict
(CycleDetector) into a single dict, plus a plain-text rendering for the
CLI (`--report`).  Wording follows the theory document: rho > 1 is a
growth direction of the linear approximation, never a practical proof
of infinite cycling.
"""

from __future__ import annotations

from ..matrix.transfer_matrix import TransferMatrix
from .bottleneck import BottleneckAnalyzer
from .cycle_detector import CycleDetector


class Report:
    """Build and render the full report for one transfer matrix."""

    def __init__(self, model, top=5):
        if not isinstance(model, TransferMatrix):
            model = TransferMatrix(model)
        self.model = model
        self.top = int(top)

    def generate(self, timing_result=None):
        classify = self.model.classify()
        report = {
            "matrix": classify,
            "perron": self.model.perron_frequencies(),
            "bottleneck": self._bottleneck_summary(),
            "cycle": (
                CycleDetector().analyze(timing_result)
                if timing_result is not None else {
                    "stable": None,
                    "note": (
                        "未运行离散时序模拟,实战可行性未验证;"
                        "须按 §5.3/§5.4 做时序模拟(§7 步骤 6)。"
                    ),
                }
            ),
            "caveats": classify["caveats"],
        }
        report["text"] = self.render(report)
        return report

    def _bottleneck_summary(self):
        analysis = BottleneckAnalyzer(self.model).analyze()
        return {
            "rho": analysis["rho"],
            "analytic": analysis["analytic"],
            "max_relative_error": analysis["max_relative_error"],
            "scarce_node": analysis["scarce_node"],
            "decisive_edges": analysis["decisive_edges"][:self.top],
            "fragile_edges": analysis["fragile_edges"][:self.top],
            "dormant_edges": analysis["dormant_edges"][:3],
        }

    def render(self, report):
        """Plain-text rendering (used by the CLI --report flag)."""
        lines = []
        classify = report["matrix"]
        lines.append("=" * 60)
        lines.append("HSR 永动机完整报告")
        lines.append("=" * 60)
        lines.append(f"事件节点: {', '.join(self.model.node_names)}")
        lines.append(f"谱半径 rho(A) = {classify['rho']:.6g}"
                     f"  regime: {classify['regime']}"
                     f"  不可约: {classify['irreducible']}")
        lines.append(f"结论: {classify['conclusion']}")

        perron = report["perron"]
        lines.append("")
        lines.append("Perron 相对频率(§4):")
        for row in perron["table"]:
            flag = "  <-- 最小份额" if row.get("flagged_as_scarce") else ""
            lines.append(f"  {row['node']:>10s}  {row['frequency']:.6f}{flag}")

        bottleneck = report["bottleneck"]
        lines.append("")
        analytic = ("解析梯度可用" if bottleneck["analytic"]
                    else "解析梯度不可用(数值差分)")
        lines.append(f"决定性资源边 Top{self.top} ({analytic}):")
        for row in bottleneck["decisive_edges"]:
            lines.append(f"  {row['from']:>10s} -> {row['to']:<10s}"
                         f" a_ij={row['value']:.4f}  d_rho={row['d_rho']:+.6f}")
        lines.append(f"脆弱边 Top{self.top} (整边移除,对应'一次未击杀'):")
        for row in bottleneck["fragile_edges"]:
            lines.append(f"  {row['from']:>10s} -> {row['to']:<10s}"
                         f" a_ij={row['value']:.4f}"
                         f"  移除后 rho={row['drop_rho']:.6g}")

        cycle = report["cycle"]
        lines.append("")
        if cycle.get("stable") is None:
            lines.append(f"时序验证: {cycle['note']}")
        else:
            lines.append(
                f"时序验证: stable={cycle['stable']}"
                f"  loops={cycle['loops_completed']}"
                f"  断轴类别={cycle['break_class']}"
            )
            lines.append(f"  {cycle['note']}")

        lines.append("")
        lines.append("注意事项:")
        for caveat in report["caveats"]:
            lines.append(f"  * {caveat}")
        return "\n".join(lines)
