"""Cycle repair planning and critical-parameter search (Phase 3).

At the matrix level, "自动寻找循环组合" reduces to a well-posed
question: which minimal interventions move a decaying linear model
(rho < 1, theorem 1) up to a target spectral radius?  The planner ranks
single-edge boosts and dormant-edge additions by the size of the
intervention.  For matrix families it reports the smallest parameter
value (target count N) at which the model stops decaying --
"目标数从哪里进入系统" (theory section 8).

Every plan keeps the section-6 wording: reaching rho >= 1 only yields a
growth direction of the linear approximation, never a practical proof
of infinite cycling; caps, thresholds, timing and enemy actions still
need discrete validation (section 5).
"""

from __future__ import annotations

import numpy as np

from ..matrix.family import MatrixFamily
from ..matrix.transfer_matrix import TransferMatrix
from .bottleneck import BottleneckAnalyzer

_CAVEAT = (
    "最小干预只把线性近似推到目标谱半径;实战仍须逐项复核"
    "资源上限、触发阈值、离散时序与敌方行动(§5),"
    "并按 §7 流程做扰动测试。"
)


def _rho_with(A, i, j, k, base):
    """rho(A) after setting a_ij to base*k (existing edge) or k (dormant)."""
    perturbed = np.array(A, copy=True)
    perturbed[i, j] = base * k if base > 0 else k
    return TransferMatrix(perturbed).spectral_radius()


def minimal_edge_boost(matrix, i, j, target_rho=1.0, hi_max=1e6,
                       tol=1e-12):
    """Smallest single-edge intervention on (i, j) reaching rho >= target.

    For an existing edge the intervention is a multiplier k >= 1 on
    a_ij; for a dormant edge (a_ij = 0) it is the added value x > 0.
    rho is monotone non-decreasing in a single entry of a non-negative
    matrix, so doubling plus bisection brackets the crossing exactly.

    Returns a dict with the intervention and the achieved rho, or None
    when the target cannot be reached within `hi_max` (e.g. the edge
    does not feed the dominant strongly connected class).
    """
    A = np.asarray(matrix, dtype=float)
    base = float(A[i, j])
    rho0 = TransferMatrix(A).spectral_radius()
    if rho0 >= target_rho:
        # Nothing to do on this edge; report the trivial intervention.
        return {
            "kind": "boost" if base > 0 else "add",
            "multiplier": 1.0,
            "new_value": base,
            "added": 0.0,
            "achieved_rho": rho0,
            "trivial": True,
        }

    hi = 2.0 if base > 0 else 1.0
    while _rho_with(A, i, j, hi, base) < target_rho:
        hi *= 2.0
        if hi > hi_max:
            return None

    lo = 1.0 if base > 0 else 0.0
    while hi - lo > tol * max(1.0, hi):
        mid = 0.5 * (lo + hi)
        if _rho_with(A, i, j, mid, base) < target_rho:
            lo = mid
        else:
            hi = mid

    new_value = base * hi if base > 0 else hi
    return {
        "kind": "boost" if base > 0 else "add",
        "multiplier": float(hi) if base > 0 else None,
        "new_value": float(new_value),
        "added": float(new_value - base),
        "achieved_rho": _rho_with(A, i, j, hi, base),
        "trivial": False,
    }


class CycleRepairPlanner:
    """Rank minimal single-edge interventions that reach a target rho."""

    def __init__(self, model):
        self.model = model

    def plan(self, target_rho=1.0, limit=None, hi_max=1e6):
        """Rank all edges by the smallest intervention reaching target.

        Each candidate carries a first-order estimate from the analytic
        elasticity (target - rho) / (d rho / d a_ij) for cross-checking
        the bisection result.
        """
        rho0 = self.model.spectral_radius()
        if rho0 >= target_rho:
            return {
                "needed": False,
                "rho": rho0,
                "target_rho": target_rho,
                "candidates": [],
                "best": None,
                "note": (
                    f"rho(A)={rho0:.6g} 已达/超过目标 {target_rho:.6g},"
                    "无需修复;结论仍受 §5 四类约束限制。"
                ),
            }

        grad = BottleneckAnalyzer(self.model).analytic_gradient()
        candidates = []
        for i in range(self.model.n):
            for j in range(self.model.n):
                result = minimal_edge_boost(
                    self.model.A, i, j, target_rho, hi_max=hi_max
                )
                if result is None or result.get("trivial"):
                    continue
                row = {
                    "from": self.model.node_names[i],
                    "to": self.model.node_names[j],
                    "value": float(self.model.A[i, j]),
                    **result,
                }
                if grad is not None and grad[i, j] > self.model.tol:
                    row["first_order_added"] = (
                        (target_rho - rho0) / float(grad[i, j])
                    )
                else:
                    row["first_order_added"] = None
                candidates.append(row)
        candidates.sort(key=lambda c: c["added"])

        if limit is not None:
            candidates = candidates[:limit]
        return {
            "needed": True,
            "rho": rho0,
            "target_rho": target_rho,
            "candidates": candidates,
            "best": candidates[0] if candidates else None,
            "note": _CAVEAT if candidates else (
                "任何单边干预在界限内都无法达到目标谱半径;"
                "须改循环结构(加边/换节点)或提高目标数。"
            ),
        }


def critical_parameter(family, rho_tol=1e-9):
    """Smallest parameter value (e.g. target count N) with rho >= 1.

    This is where the target count enters the system (section 8): below
    the critical value the linear model decays regardless of initial
    resources (theorem 1), above it a growth direction exists.
    """
    sweep = family.regime_sweep(rho_tol)
    rows = sweep["rows"]
    critical = None
    previous = None
    for row in rows:
        if row["rho"] >= 1.0 - rho_tol:
            critical = row
            break
        previous = row

    result = {
        "parameter": sweep["parameter"],
        "monotone_increasing": sweep["monotone_increasing"],
        "rho_range": sweep["rho_range"],
        "critical_key": critical["key"] if critical else None,
        "critical_rho": critical["rho"] if critical else None,
        "sub_critical_key": previous["key"] if previous else None,
        "sub_critical_rho": previous["rho"] if previous else None,
    }
    if critical is None:
        result["status"] = "all_decay"
        result["note"] = (
            f"族内所有{sweep['parameter']}值均 rho<1(定理 1:必然衰减);"
            "更大的参数值属于外推,不可当作结论(§7 步骤 8)。"
        )
    elif previous is None:
        result["status"] = "already_at_or_above"
        result["note"] = (
            f"最小参数值 {sweep['parameter']}={critical['key']} 即有 "
            f"rho={critical['rho']:.6g}>=1,目标数在族内一开始就进入系统(§8)。"
            "仍是线性增长方向,非实战永动充分条件(§5)。"
        )
    else:
        result["status"] = "reached"
        result["note"] = (
            f"{sweep['parameter']}={previous['key']} 时 rho={previous['rho']:.6g}<1,"
            f"升至 {sweep['parameter']}={critical['key']} 时 rho="
            f"{critical['rho']:.6g}>=1:这就是目标数进入系统的位置(§8)。"
            "跨过临界值只说明存在线性增长方向,实战仍须验证(§5)。"
        )
    return result
