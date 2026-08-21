"""Parameterized matrix families (theory document section 5.2).

In real battles the transfer coefficients depend on state: A = A(x_t, N,
s_t) where N is the target count and s_t the character/enemy state.  The
theory document notes that "perpetual motion only in multi-target
environments" is not a build detail -- the matrix entries themselves
change with N.

A MatrixFamily bundles one transfer matrix per parameter value and
analyzes how the spectral radius and regime move with the parameter.
"""

from __future__ import annotations

import numpy as np

from .transfer_matrix import TransferMatrix


def _numeric_sort_key(key):
    try:
        return (0, float(key))
    except (TypeError, ValueError):
        return (1, str(key))


class MatrixFamily:
    """A parameterized family {key: TransferMatrix} of transfer matrices."""

    def __init__(self, name, nodes, matrices_by_key, parameter_name="N",
                 rho_targets=None, notes=None, tol=1e-9):
        self.name = name
        self.parameter_name = parameter_name
        self.rho_targets = dict(rho_targets or {})
        self.notes = notes
        self.models = {
            key: TransferMatrix(matrix, node_names=list(nodes), tol=tol)
            for key, matrix in matrices_by_key.items()
        }

    @property
    def keys(self):
        return sorted(self.models, key=_numeric_sort_key)

    def spectral_radii(self):
        return {key: self.models[key].spectral_radius() for key in self.keys}

    def analyze(self, rho_tol=1e-9):
        """Sweep the parameter: rho, regime, and match to documented targets."""
        rows = []
        for key in self.keys:
            model = self.models[key]
            result = model.classify(rho_tol)
            target = self.rho_targets.get(key)
            rows.append({
                "key": key,
                "rho": result["rho"],
                "regime": result["regime"],
                "irreducible": result["irreducible"],
                "target_rho": float(target) if target is not None else None,
                "matches_target": (
                    bool(abs(result["rho"] - float(target)) <= 1e-5)
                    if target is not None else None
                ),
            })
        return rows

    def regime_sweep(self, rho_tol=1e-9):
        """Summarize how the linear regime moves across the parameter."""
        rows = self.analyze(rho_tol)
        regimes = {row["regime"] for row in rows}
        return {
            "parameter": self.parameter_name,
            "regimes": sorted(regimes),
            "rho_range": (min(r["rho"] for r in rows), max(r["rho"] for r in rows)),
            "monotone_increasing": all(
                rows[i]["rho"] < rows[i + 1]["rho"] for i in range(len(rows) - 1)
            ),
            "rows": rows,
        }

    def model_for(self, key):
        return self.models[key]
