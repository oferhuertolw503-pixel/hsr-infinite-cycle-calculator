"""Versioned matrix library (theory document section 7, step 8).

Different game versions, modes, blessings and enemy kits correspond to
DIFFERENT transfer matrices; a single matrix must never be extrapolated
into a universal conclusion.  A MatrixLibrary binds each matrix to its
game context and compares the linear conclusions across contexts:

  * regime consensus -- do all variants agree?  If not, the conclusion
    is context-bound and extrapolation is forbidden (step 8);
  * node groups -- variants modelled at different granularity (event
    lists) can only be compared qualitatively (step 1).
"""

from __future__ import annotations

from .transfer_matrix import TransferMatrix

_CONTEXT_KEYS = ("version", "mode", "blessing", "enemy")


class MatrixVariant:
    """One transfer matrix bound to a game version/mode/blessing/enemy context."""

    def __init__(self, name, matrix, nodes=None, version=None, mode=None,
                 blessing=None, enemy=None, provenance=None,
                 documented_rho=None, notes=None, tol=1e-9):
        self.name = name
        self.model = TransferMatrix(matrix, node_names=nodes, tol=tol)
        self.version = version
        self.mode = mode
        self.blessing = blessing
        self.enemy = enemy
        self.provenance = provenance
        self.documented_rho = (
            float(documented_rho) if documented_rho is not None else None
        )
        self.notes = notes

    @property
    def context(self):
        """Non-None context tags (version / mode / blessing / enemy)."""
        return {
            key: getattr(self, key)
            for key in _CONTEXT_KEYS
            if getattr(self, key) is not None
        }

    def summary(self, rho_tol=1e-9):
        """One comparison row: context tags plus the linear conclusion."""
        result = self.model.classify(rho_tol)
        row = {
            "name": self.name,
            "n_nodes": self.model.n,
            "rho": result["rho"],
            "regime": result["regime"],
            "irreducible": result["irreducible"],
            "provenance": self.provenance,
        }
        row.update(self.context)
        if self.documented_rho is not None:
            row["matches_documented"] = bool(
                abs(result["rho"] - self.documented_rho) <= 1e-5
            )
        return row


class MatrixLibrary:
    """A registry of context-tagged transfer matrices (section 7, step 8)."""

    def __init__(self, name, variants, notes=None):
        self.name = name
        self.variants = list(variants)
        names = [v.name for v in self.variants]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate variant names: {names}")
        self.notes = notes

    def filter(self, **context):
        """Sub-library of variants whose tags match all given filters."""
        for key in context:
            if key not in _CONTEXT_KEYS:
                raise ValueError(
                    f"unknown context tag {key!r}; expected one of "
                    f"{_CONTEXT_KEYS}"
                )
        selected = [
            variant for variant in self.variants
            if all(getattr(variant, key) == value
                   for key, value in context.items())
        ]
        return MatrixLibrary(
            f"{self.name} [filtered]", selected, notes=self.notes
        )

    def node_groups(self):
        """Variant names grouped by their event-node list (step 1)."""
        groups = {}
        for variant in self.variants:
            key = tuple(variant.model.node_names)
            groups.setdefault(key, []).append(variant.name)
        return groups

    def compare(self, rho_tol=1e-9):
        """Cross-context comparison with extrapolation diagnostics."""
        rows = [variant.summary(rho_tol) for variant in self.variants]
        regimes = sorted({row["regime"] for row in rows})
        node_groups = self.node_groups()

        warnings = []
        if not rows:
            warnings.append("库内没有变体(可能过滤器无匹配),无可对比结论。")
        if len(regimes) > 1:
            warnings.append(
                "不同版本/模式/敌方机制下的 regime 不一致"
                f"({'+'.join(regimes)}):结论是上下文绑定的,"
                "任何一张矩阵都不可外推为通用结论(§7 步骤 8)。"
            )
        if len(node_groups) > 1:
            warnings.append(
                f"库内有 {len(node_groups)} 种事件粒度"
                "(不同节点列表):跨粒度只能定性对比,"
                "rho 数值不可直接排名(§7 步骤 1)。"
            )
        undocumented = [
            row["name"] for row in rows if row["provenance"] is None
        ]
        if undocumented:
            warnings.append(
                "以下变体未登记 provenance(实测/重构/演示),"
                f"对比结论须先核对来源:{', '.join(undocumented)}。"
            )

        return {
            "library": self.name,
            "rows": rows,
            "regimes": regimes,
            "consensus": len(regimes) == 1,
            "rho_range": (min(r["rho"] for r in rows),
                          max(r["rho"] for r in rows)) if rows else None,
            "node_groups": node_groups,
            "warnings": warnings,
            "note": (
                "§7 步骤 8:不同版本、模式、祝福和敌方机制对应不同 A;"
                "本库把每张矩阵与其上下文绑定后再对比。"
                "regime 一致也不构成实战永动的充分条件(§5)。"
            ),
        }
