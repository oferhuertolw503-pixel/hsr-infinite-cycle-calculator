"""Bottleneck localization from the Perron pair (theory sections 4 and 8).

For a non-negative matrix A whose spectral radius rho is a simple real
eigenvalue, let v be the right Perron vector (the relative event
frequencies of section 4) and u the left Perron vector.  With the
scale-invariant normalization u^T v = 1:

    d rho / d a_ij = u_i * v_j        (elasticity formula)

So the product u_i * v_j ranks edges by how much one transfer
coefficient moves the spectral radius -- the matrix-level answer to
"哪条资源边决定成败" (section 8).  The analyzer cross-checks the
analytic gradient against finite differences and falls back to the
numeric ranking when the dominant root is not simple (reducible or
periodic digraphs), where the formula no longer applies.
"""

from __future__ import annotations

import numpy as np

from ..matrix.transfer_matrix import TransferMatrix

_FALLBACK_NOTE = (
    "主导特征值非单实根(可约或周期结构),解析梯度不适用,"
    "排序退化为数值差分。"
)


class BottleneckAnalyzer:
    """Locate decisive edges and scarce nodes from the Perron pair."""

    def __init__(self, model, numeric_delta=1e-4):
        self.model = model
        self.numeric_delta = float(numeric_delta)

    # -- Perron pair -------------------------------------------------------
    def _dominant_gap(self):
        """Relative gap between the two largest eigenvalue moduli."""
        moduli = np.sort(np.abs(self.model.eigenvalues()))[::-1]
        top = float(moduli[0])
        second = float(moduli[1]) if moduli.size > 1 else 0.0
        if top <= self.model.tol:
            return float("inf")
        return (top - second) / top

    def analytic_gradient(self):
        """Edge-wise d rho / d a_ij = u_i v_j / (u^T v), or None.

        Valid only when the dominant eigenvalue is real, simple, and has
        a non-negative left/right Perron pair; otherwise the caller must
        fall back to finite differences.
        """
        value, vec, info = self.model.dominant_pair()
        if not info["real"]:
            return None
        if self._dominant_gap() <= 1e-9:
            return None
        if np.any(vec < -self.model.tol):
            return None

        # Left Perron vector: eigenvector of A^T for the same eigenvalue.
        values_t, vectors_t = np.linalg.eig(self.model.A.T)
        idx = int(np.argmin(np.abs(values_t - value)))
        left = np.real(vectors_t[:, idx])
        k = int(np.argmax(np.abs(left)))
        if left[k] < 0:
            left = -left
        if np.any(left < -self.model.tol):
            return None

        weight = float(left @ vec)
        if weight <= self.model.tol:
            return None
        return np.outer(left, vec) / weight

    # -- report ------------------------------------------------------------
    def analyze(self):
        """Full bottleneck report: decisive edges, dormant edges, nodes."""
        model = self.model
        rho = model.spectral_radius()
        grad = self.analytic_gradient()
        numeric = model.edge_sensitivity(delta=self.numeric_delta)
        numeric_by_edge = {(r["i"], r["j"]): r["d_rho"] for r in numeric}

        edges = []
        max_rel_error = 0.0
        for i in range(model.n):
            for j in range(model.n):
                if model.A[i, j] <= model.tol:
                    continue
                numeric_d = float(numeric_by_edge[(i, j)])
                row = {
                    "i": i,
                    "j": j,
                    "from": model.node_names[i],
                    "to": model.node_names[j],
                    "value": float(model.A[i, j]),
                    "d_rho_numeric": numeric_d,
                }
                if grad is not None:
                    analytic = float(grad[i, j])
                    row["d_rho"] = analytic
                    denom = max(abs(analytic), abs(numeric_d), 1e-12)
                    row["relative_error"] = abs(analytic - numeric_d) / denom
                    max_rel_error = max(max_rel_error, row["relative_error"])
                else:
                    row["d_rho"] = numeric_d
                    row["relative_error"] = None
                edges.append(row)
        # Complete-removal impact: zeroing each edge in turn.  This is a
        # finite perturbation, complementary to the marginal gradient --
        # an edge can have a small local elasticity yet break the loop
        # when removed entirely (one missed kill), as in the audit demo.
        for row in edges:
            dropped = np.array(model.A, copy=True)
            dropped[row["i"], row["j"]] = 0.0
            rho_dropped = TransferMatrix(
                dropped, node_names=model.node_names, tol=model.tol
            ).spectral_radius()
            row["drop_rho"] = rho_dropped
            row["drop_delta"] = rho_dropped - rho
            row["load_bearing"] = rho_dropped < rho - model.tol
        edges.sort(key=lambda r: abs(r["d_rho"]), reverse=True)
        fragile_edges = sorted(edges, key=lambda r: r["drop_delta"])

        # Dormant edges (a_ij = 0): marginal effect of wiring in a new link.
        dormant = [
            {
                "i": r["i"],
                "j": r["j"],
                "from": r["from"],
                "to": r["to"],
                "d_rho": float(r["d_rho"]),
            }
            for r in numeric
            if r["value"] <= model.tol and r["d_rho"] > 0
        ]
        dormant.sort(key=lambda r: r["d_rho"], reverse=True)

        freqs = model.perron_frequencies()
        if grad is not None:
            node_sensitivity = [
                {
                    "node": model.node_names[i],
                    "out_sensitivity": float(grad[i].sum()),
                    "in_sensitivity": float(grad[:, i].sum()),
                }
                for i in range(model.n)
            ]
            node_sensitivity.sort(
                key=lambda r: r["out_sensitivity"], reverse=True
            )
        else:
            node_sensitivity = []

        return {
            "rho": rho,
            "analytic": grad is not None,
            "max_relative_error": max_rel_error if grad is not None else None,
            "frequencies": freqs,
            "scarce_node": freqs["table"][-1] if freqs["table"] else None,
            "decisive_edges": edges,
            "fragile_edges": fragile_edges,
            "dormant_edges": dormant,
            "node_sensitivity": node_sensitivity,
            "note": (
                "u_i*v_j 给出单条资源边对谱半径的边际影响(§8 哪条资源边决定成败);"
                "fragile_edges 按整边移除的 rho 跌幅排序,边际弹性小不代表"
                "整条边可缺(一次未击杀即断轴);"
                "v 的最小份额节点是最先断粮的候选(§4);"
                "dormant_edges 给出新增一条转移边的边际收益。"
                + ("" if grad is not None else _FALLBACK_NOTE)
            ),
        }
