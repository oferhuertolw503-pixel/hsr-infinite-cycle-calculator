"""Capped transfer system (theory document section 5.1).

Battles cap energy, skill points, stacks, and summon-attack counts.  The
piecewise-non-linear update

    x_{t+1} = min(c, x_t A + b_t)

clips the linear update component-wise at the caps c, with b_t an
exogenous input vector (kill energy, enemy refresh, environment
blessings, ...).

Two consequences spelled out in the theory document:

  * rho(A) > 1 does NOT imply unbounded growth once caps apply: the
    capped system can converge to a fixed point even though the linear
    model grows;
  * when a critical node saturates, the subsequent trigger counts change,
    so the original linear matrix stops being the right model -- the
    system must be rewritten as piecewise non-linear.
"""

from __future__ import annotations

import numpy as np

from .transfer_matrix import MatrixValidationError, TransferMatrix


class CappedTransferSystem:
    """x_{t+1} = min(c, x_t A + b_t) with per-component caps and inputs."""

    def __init__(self, matrix, caps, node_names=None, tol=1e-9):
        self.model = TransferMatrix(matrix, node_names=node_names, tol=tol)
        caps = np.asarray(caps, dtype=float).reshape(-1)
        if caps.shape[0] != self.model.n:
            raise MatrixValidationError(
                f"got {caps.shape[0]} caps for a {self.model.n}x{self.model.n} matrix"
            )
        if not np.all(np.isfinite(caps)) or np.any(caps <= 0):
            raise MatrixValidationError("caps must be finite and strictly positive")
        self.caps = caps
        self.node_names = self.model.node_names

    @property
    def n(self):
        return self.model.n

    def step(self, x, b=None):
        """One capped update from x; b is an optional exogenous input vector."""
        x = np.asarray(x, dtype=float).reshape(-1)
        if x.shape[0] != self.n:
            raise ValueError(f"x must have {self.n} entries")
        if b is None:
            b = np.zeros(self.n)
        b = np.asarray(b, dtype=float).reshape(-1)
        if b.shape[0] != self.n:
            raise ValueError(f"b must have {self.n} entries")
        return np.minimum(self.caps, x @ self.model.A + b)

    def iterate(self, x0, steps, b=None):
        """Return trajectory rows x_0, ..., x_steps under the capped update."""
        if steps < 0:
            raise ValueError("steps must be non-negative")
        trajectory = np.empty((steps + 1, self.n))
        x = np.asarray(x0, dtype=float).reshape(-1)
        if x.shape[0] != self.n:
            raise ValueError(f"x0 must have {self.n} entries")
        trajectory[0] = x
        for t in range(1, steps + 1):
            x = self.step(x, b)
            trajectory[t] = x
        return trajectory

    def run_until_cycle(self, x0, b=None, max_steps=100000, tol=1e-9):
        """Iterate until a fixed point, a 2-cycle, or max_steps.

        Returns a dict with status "fixed_point" / "2_cycle" /
        "no_convergence", the number of steps, the final state, and the
        saturation share of the final state.
        """
        x = np.asarray(x0, dtype=float).reshape(-1)
        if x.shape[0] != self.n:
            raise ValueError(f"x0 must have {self.n} entries")
        prev = None
        for t in range(max_steps):
            xn = self.step(x, b)
            if np.allclose(xn, x, rtol=tol, atol=tol):
                return {
                    "status": "fixed_point",
                    "steps": t,
                    "x": xn,
                    "saturated": float(np.mean(xn >= self.caps - tol)),
                }
            if prev is not None and np.allclose(xn, prev, rtol=tol, atol=tol):
                return {
                    "status": "2_cycle",
                    "steps": t,
                    "x": x,
                    "next": xn,
                    "saturated": float(np.mean(xn >= self.caps - tol)),
                }
            prev, x = x, xn
        return {
            "status": "no_convergence",
            "steps": max_steps,
            "x": x,
            "saturated": float(np.mean(x >= self.caps - tol)),
        }

    def saturation_rate(self, trajectory):
        """Per-node fraction of trajectory steps at the cap."""
        trajectory = np.asarray(trajectory, dtype=float)
        if trajectory.ndim != 2 or trajectory.shape[1] != self.n:
            raise ValueError("trajectory must have shape (steps+1, n)")
        return np.mean(trajectory >= self.caps - 1e-9, axis=0)

    def linear_comparison(self, x0, steps, b=None):
        """Compare the capped and the pure-linear trajectories.

        Demonstrates section 5.1: with rho(A) > 1 the linear model grows
        while the capped model may converge.
        """
        linear = self.model.iterate(x0, steps)
        capped = self.iterate(x0, steps, b)
        return {
            "rho": self.model.spectral_radius(),
            "linear_final": linear[-1],
            "capped_final": capped[-1],
            "linear_total": float(np.sum(linear)),
            "capped_total": float(np.sum(capped)),
            "capped_at_cap": float(np.mean(capped[-1] >= self.caps - 1e-9)),
            "note": (
                "线性模型无上限,rho>1 时沿 Perron 方向增长;封顶系统按分量截断,"
                "饱和节点会改变后续触发数量,原矩阵不再适用(§5.1)。"
            ),
        }
