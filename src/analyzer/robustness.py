"""Perturbation tests (theory document section 7, step 7).

Change the target count, miss one kill, miss one heal, or let an enemy
interject -- then observe whether the linear regime and the spectral
radius move enough to break the loop.  This answers "which edge decides
success or failure" at the matrix level; enemy interjection additionally
needs the timed simulation (see src.simulation.timed_engine).
"""

from __future__ import annotations

import numpy as np

from ..matrix.transfer_matrix import TransferMatrix


class Perturbation:
    """One perturbed matrix with a human-readable label."""

    def __init__(self, label, matrix, note=""):
        self.label = label
        self.matrix = np.asarray(matrix, dtype=float)
        self.note = note


def drop_edge(matrix, i, j):
    """Missed trigger: remove the edge i -> j entirely (e.g. one missed kill)."""
    out = np.asarray(matrix, dtype=float).copy()
    out[i, j] = 0.0
    return out


def scale_edge(matrix, i, j, factor):
    """Scale one edge by `factor` (e.g. a heal that fires only half the time)."""
    out = np.asarray(matrix, dtype=float).copy()
    out[i, j] *= factor
    return out


class RobustnessReport:
    """Run a set of perturbations against a base matrix and compare regimes."""

    def __init__(self, base_matrix, node_names=None, tol=1e-9):
        self.base = TransferMatrix(base_matrix, node_names=node_names, tol=tol)
        self.node_names = self.base.node_names
        self.tol = tol
        self.cases = []

    def add(self, label, matrix, note=""):
        self.cases.append(Perturbation(label, matrix, note))
        return self

    def run(self, rho_tol=1e-9):
        base_result = self.base.classify(rho_tol)
        rows = []
        for case in self.cases:
            model = TransferMatrix(
                case.matrix, node_names=self.node_names, tol=self.tol
            )
            result = model.classify(rho_tol)
            rows.append({
                "label": case.label,
                "note": case.note,
                "rho": result["rho"],
                "regime": result["regime"],
                "delta_rho": result["rho"] - base_result["rho"],
                "regime_flipped": result["regime"] != base_result["regime"],
            })
        return {
            "base": base_result,
            "cases": rows,
            "flips": [row for row in rows if row["regime_flipped"]],
            "note": (
                "扰动测试改变目标数/一次未击杀/一次治疗缺失/敌方插队,"
                "观察闭环是否仍保持原 regime(§7 步骤 7);"
                "敌方插队须结合时序模拟验证。"
            ),
        }
