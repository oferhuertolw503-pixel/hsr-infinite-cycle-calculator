"""Resource transfer matrix engine.

Row-vector convention (theory document section 2.2):

    x_{t+1} = x_t A          x_{t+n} = x_t A^n

Entry A[i, j] is the average number of type-j events produced by one
type-i event.  The long-term trend is governed by the spectral radius
rho(A) (section 3): rho < 1 means decay, rho = 1 is the critical
non-decaying case, and rho > 1 only yields a growth direction -- it is
NOT by itself a proof of a practical infinite loop.
"""

from __future__ import annotations

import math

import numpy as np

from .irreducibility import (
    condensation_summary,
    is_irreducible,
    strongly_connected_components,
)
from .matrix_validator import validate_matrix


class MatrixValidationError(ValueError):
    """Raised when a transfer matrix violates the model assumptions."""


class TransferMatrix:
    """Non-negative resource transfer matrix with spectral analysis."""

    def __init__(self, matrix, node_names=None, tol=1e-9):
        self.A = np.asarray(matrix, dtype=float)
        self.tol = float(tol)
        report = validate_matrix(self.A)
        if not report["valid"]:
            raise MatrixValidationError("; ".join(report["issues"]))

        n = self.A.shape[0]
        if node_names is not None:
            if len(node_names) != n:
                raise MatrixValidationError(
                    f"got {len(node_names)} node names for a {n}x{n} matrix"
                )
            self.node_names = list(node_names)
        else:
            self.node_names = [f"x{i}" for i in range(n)]

    # -- basic properties -------------------------------------------------
    @property
    def shape(self):
        return self.A.shape

    @property
    def n(self):
        return self.A.shape[0]

    # -- spectral analysis ------------------------------------------------
    def eigenvalues(self):
        return np.linalg.eigvals(self.A)

    def spectral_radius(self):
        """rho(A) = max |lambda| over all eigenvalues."""
        return float(np.max(np.abs(self.eigenvalues())))

    def is_irreducible(self):
        """Irreducibility of the digraph with edge i->j iff A[i,j] > tol."""
        return is_irreducible(self.A, eps=self.tol)

    def components(self):
        """Strongly connected components of the matrix digraph."""
        return strongly_connected_components(self.A, eps=self.tol)

    def component_summary(self):
        return condensation_summary(self.A, self.node_names, eps=self.tol)

    # -- Perron pair ------------------------------------------------------
    def dominant_pair(self):
        """Dominant eigenvalue and eigenvector, normalized to sum to 1.

        Returns (value, vector, info) where info carries:
          - real:     whether the dominant eigenvalue is real
          - positive: whether the normalized vector is non-negative
          - mode:     "sum" (sum-1 normalization, section 4 frequencies)
                      or "max" (fallback when the sum vanishes)

        For an irreducible non-negative matrix the dominant eigenvalue is
        the Perron root: real, simple, with a strictly positive vector
        (theorems 2 and 3).  A complex dominant root means the dominant
        mode rotates (e.g. periodic reducible chains) and no real Perron
        direction exists.
        """
        values, vectors = np.linalg.eig(self.A)
        idx = int(np.argmax(np.abs(values)))
        value = values[idx]
        vec = vectors[:, idx]

        real = bool(abs(value.imag) <= self.tol * max(1.0, abs(value)))
        if real:
            value = float(np.real(value))
            vec = np.real(vec)

        # Flip the vector sign so the entry with the largest magnitude is
        # positive.  The eigenvalue must NOT change: A(-v) = lambda * (-v).
        k = int(np.argmax(np.abs(vec)))
        if vec[k] < 0:
            vec = -vec

        # Normalize: sum to 1 gives relative event frequencies (section 4).
        # A complex dominant vector only gets a max-modulus normalization,
        # because its components are not real resource shares.
        if real:
            total = float(np.sum(vec))
            mode = "sum"
            if abs(total) > self.tol * max(1.0, float(np.max(np.abs(vec)))):
                vec = vec / total
            else:
                peak = float(np.max(np.abs(vec)))
                mode = "max"
                if peak > self.tol:
                    vec = vec / peak
        else:
            peak = float(np.max(np.abs(vec)))
            mode = "max"
            if peak > self.tol:
                vec = vec / peak

        positive = bool(np.all(np.real(vec) >= -self.tol)) if real else False
        return value, vec, {
            "real": real,
            "positive": positive,
            "mode": mode,
        }

    def perron_frequencies(self):
        """Relative event frequencies from the dominant vector (section 4).

        Returns a list of dicts sorted by frequency, with the smallest
        share flagged as the node to double-check first.  This is a
        diagnostic, not a rotation prescription.
        """
        value, vec, info = self.dominant_pair()
        table = [
            {
                "node": name,
                "index": i,
                "frequency": float(np.real(vec[i])),
            }
            for i, name in enumerate(self.node_names)
        ]
        table.sort(key=lambda row: row["frequency"], reverse=True)
        if table:
            table[-1]["flagged_as_scarce"] = True
        return {
            "eigenvalue": value,
            "real": info["real"],
            "positive": info["positive"],
            "note": (
                "Perron 向量给出主导模式中各事件的相对频率;"
                "最小份额节点需优先核对产出与回流,不是配速结论。"
            ),
            "table": table,
        }

    # -- regime classification (theorems 1-3) ----------------------------
    def classify(self, rho_tol=1e-9):
        """Classify the linear regime of the transfer matrix.

        Wording follows the theory document: a growth direction is never
        reported as a practical infinite loop.
        """
        rho = self.spectral_radius()
        value, vec, info = self.dominant_pair()
        irreducible = self.is_irreducible()
        caveats = []

        if rho < 1 - rho_tol:
            regime = "decay"
            conclusion = (
                f"rho(A)={rho:.6g} < 1: A^n -> 0,任何有限非负初始资源在纯线性模型下"
                "必然衰减,无法维持无限次正资源循环(定理 1)。初始资源再多也只能延后断轴。"
            )
        elif abs(rho - 1) <= rho_tol:
            regime = "critical"
            if irreducible and info["real"] and info["positive"]:
                conclusion = (
                    f"rho(A)={rho:.6g} ~= 1 且 A 不可约:存在 Perron 向量 v>0 使 "
                    "Av=v,给出理论守恒方向(定理 2)。仍须验证上限、阈值、时序与敌方行动。"
                )
            else:
                conclusion = (
                    f"rho(A)={rho:.6g} ~= 1(数值容差内):临界情形。"
                )
                if not irreducible:
                    conclusion += (
                        "但 A 可约,Perron-Frobenius 严格正性不适用,"
                        "须按强连通分量逐块检查。"
                    )
                if not info["real"]:
                    conclusion += "主导特征值为复根,长期模式含周期性振荡。"
                conclusion += "仍须验证上限、阈值、时序与敌方行动。"
        else:
            regime = "growth"
            doubling = self.growth_doubling_time()
            conclusion = (
                f"rho(A)={rho:.6g} > 1:在线性、无上限、条件恒成立的近似下,"
                f"沿 Perron 方向资源约每 {doubling:.3g} 轮翻倍(定理 3)。"
                "这只能推出存在增长方向,不能单独推出实战无限循环。"
            )
        if not irreducible:
            caveats.append(
                "A 不可约性不成立,严格正 Perron 向量的定理前提缺失;"
                "衰减/增长结论需分强连通分量讨论。"
            )
        if not info["real"]:
            caveats.append(
                "主导特征值为复根,长期资源模式含周期性振荡,谱半径判定不受影响。"
            )
        caveats.append(
            "线性结论是必要条件而非充分条件:上限、阈值、时序与敌方行动须由"
            "离散模拟逐项验证。"
        )

        return {
            "rho": rho,
            "regime": regime,
            "irreducible": irreducible,
            "dominant_real": info["real"],
            "dominant_positive": info["positive"],
            "eigenvalue": value,
            "conclusion": conclusion,
            "caveats": caveats,
        }

    # -- time scales ------------------------------------------------------
    def growth_doubling_time(self):
        """Rounds for the dominant mode to double: ln(2)/ln(rho), rho>1."""
        rho = self.spectral_radius()
        if rho <= 1:
            raise ValueError("doubling time is defined only for rho > 1")
        return math.log(2.0) / math.log(rho)

    def vector_decay_horizon(self, x0, epsilon=1e-6, max_steps=10**6):
        """Smallest t with max(|x0 A^t|) < epsilon (row-vector convention)."""
        x = np.asarray(x0, dtype=float).reshape(-1)
        if x.shape[0] != self.n:
            raise ValueError(f"x0 must have {self.n} entries")
        scale = float(np.max(np.abs(x))) or 1.0
        if scale <= epsilon:
            return 0
        for t in range(1, max_steps + 1):
            x = x @ self.A
            if float(np.max(np.abs(x))) < epsilon * scale:
                return t
        return None

    def matrix_decay_horizon(self, epsilon=1e-6, max_steps=10**6):
        """Smallest t with ||A^t||_inf < epsilon; None if not reached.

        Uses repeated squaring plus binary search on the matrix powers.
        """
        rho = self.spectral_radius()
        if rho >= 1 - self.tol:
            raise ValueError("decay horizon is defined only for rho < 1")

        power = np.array(self.A, copy=True)
        n = 1
        while np.max(np.abs(power)) >= epsilon and n < max_steps:
            power = power @ power
            n *= 2
        if np.max(np.abs(power)) >= epsilon:
            return None
        lo, hi = n // 2, n
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if np.max(np.abs(np.linalg.matrix_power(self.A, mid))) < epsilon:
                hi = mid
            else:
                lo = mid
        return hi

    # -- trajectories -----------------------------------------------------
    def iterate(self, x0, steps):
        """Return trajectory rows x_0, ..., x_steps under x_{t+1} = x_t A."""
        x = np.asarray(x0, dtype=float).reshape(-1)
        if x.shape[0] != self.n:
            raise ValueError(f"x0 must have {self.n} entries")
        if steps < 0:
            raise ValueError("steps must be non-negative")
        trajectory = np.empty((steps + 1, self.n))
        trajectory[0] = x
        for t in range(1, steps + 1):
            x = x @ self.A
            trajectory[t] = x
        return trajectory

    # -- edge sensitivity -------------------------------------------------
    def edge_sensitivity(self, delta=1e-4):
        """Finite-difference sensitivity of rho(A) to each entry a_ij.

        Answers "which resource edge decides success or failure" (theory
        document section 8): positive entries use central differences,
        zero entries use one-sided differences (marginal effect of
        adding that edge).
        """
        rho0 = self.spectral_radius()
        rows = []
        for i in range(self.n):
            for j in range(self.n):
                if self.A[i, j] > 0:
                    ap = self.A.copy()
                    ap[i, j] += delta
                    am = self.A.copy()
                    am[i, j] -= delta
                    if am[i, j] < 0:
                        am[i, j] = 0.0
                    grad = (TransferMatrix(ap).spectral_radius()
                            - TransferMatrix(am).spectral_radius())
                    grad /= ap[i, j] - am[i, j]
                else:
                    ap = self.A.copy()
                    ap[i, j] += delta
                    grad = (TransferMatrix(ap).spectral_radius() - rho0) / delta
                rows.append({
                    "i": i,
                    "j": j,
                    "from": self.node_names[i],
                    "to": self.node_names[j],
                    "value": float(self.A[i, j]),
                    "d_rho": float(grad),
                })
        rows.sort(key=lambda r: abs(r["d_rho"]), reverse=True)
        return rows
