"""Cycle audit: the eight-step modelling and review workflow (theory
document section 7).

    1. 选择粒度   -- list events, not characters (usually 4-8 key events)
    2. 统一量纲   -- every component: count / expected count / energy-equivalent
    3. 逐边填表   -- each non-zero a_ij: mechanism, condition, cap, N-dependence
    4. 计算谱半径 -- rho < 1 excludes linear perpetual motion directly
    5. 求 Perron 特征向量 -- relative frequencies; find the bottleneck node
    6. 做时序模拟 -- ordered execution with real priorities (section 5.3/5.4)
    7. 做扰动测试 -- target count, missed kill, missed heal, enemy interjection
    8. 区分版本与模式 -- different versions/modes/blessings/enemy kits have
       different A; a single matrix must never be extrapolated universally
"""

from __future__ import annotations

from ..matrix.transfer_matrix import TransferMatrix
from ..simulation.timed_engine import TimedBattleEngine, TimedEvent
from .robustness import Perturbation, RobustnessReport


def _coerce_sequence(sequence):
    """Accept either TimedEvent objects or plain dicts (from JSON)."""
    if sequence is None:
        return None
    out = []
    for item in sequence:
        if isinstance(item, dict):
            out.append(TimedEvent(**item))
        else:
            out.append(item)
    return out


def _coerce_perturbations(perturbations):
    """Accept either Perturbation objects or plain dicts (from JSON)."""
    if perturbations is None:
        return None
    out = []
    for item in perturbations:
        if isinstance(item, dict):
            out.append(Perturbation(
                label=item["label"],
                matrix=item["matrix"],
                note=item.get("note", ""),
            ))
        else:
            out.append(item)
    return out


def _coerce_edge_meta(edge_meta):
    """Normalize edge metadata keys to (i, j) tuples.

    Accepts tuple keys (from code) or "i,j" string keys (from JSON files).
    """
    if not edge_meta:
        return {}
    normalized = {}
    for key, value in edge_meta.items():
        if isinstance(key, str):
            i, j = key.split(",")
            key = (int(i), int(j))
        normalized[key] = value
    return normalized


class CycleAudit:
    """Run the eight-step audit against one transfer matrix."""

    def __init__(self, matrix, node_names=None, units=None, edge_meta=None,
                 sequence=None, enemy_av0=None, perturbations=None,
                 mode_note=None, x0=None, tol=1e-9):
        self.model = TransferMatrix(matrix, node_names=node_names, tol=tol)
        n = self.model.n
        self.units = list(units) if units is not None else ["count"] * n
        if len(self.units) != n:
            raise ValueError(f"got {len(self.units)} units for {n} nodes")
        self.edge_meta = _coerce_edge_meta(edge_meta)
        self.sequence = _coerce_sequence(sequence)
        self.enemy_av0 = enemy_av0
        self.perturbations = _coerce_perturbations(perturbations) or []
        self.mode_note = mode_note
        self.x0 = x0 if x0 is not None else {"energy": 0.0, "skill_points": 0.0}

    def run(self, rho_tol=1e-9):
        A = self.model.A
        n = self.model.n
        names = self.model.node_names
        steps = {}

        # 1. granularity ---------------------------------------------------
        steps["granularity"] = {
            "event_count": n,
            "events": names,
            "note": "先列'事件'而非角色名,通常 4-8 个关键事件构成最小模型(§7 步骤 1)。",
        }

        # 2. units ---------------------------------------------------------
        steps["units"] = {
            "units": {name: unit for name, unit in zip(names, self.units)},
            "note": (
                "每个分量须明确是次数、期望次数还是某一基准资源的等价量;"
                "同一模型内必须统一量纲(§7 步骤 2)。"
            ),
        }

        # 3. edge table -----------------------------------------------------
        edges = []
        for i in range(n):
            for j in range(n):
                if A[i, j] > self.model.tol:
                    meta = self.edge_meta.get((i, j), {})
                    edges.append({
                        "from": names[i],
                        "to": names[j],
                        "value": float(A[i, j]),
                        "mechanism": meta.get("mechanism", "?"),
                        "cap": meta.get("cap"),
                        "depends_on_N": meta.get("depends_on_N", False),
                    })
        steps["edge_table"] = {
            "edge_count": len(edges),
            "edges": edges,
            "fully_documented": bool(self.edge_meta),
            "note": (
                "每个非零 a_ij 都应有来源机制、条件、上限与是否依赖敌方数量;"
                "未填写的边需人工补齐(§7 步骤 3)。"
            ),
        }

        # 4. spectral radius ------------------------------------------------
        steps["spectral_radius"] = self.model.classify(rho_tol)

        # 5. Perron frequencies ----------------------------------------------
        steps["perron"] = self.model.perron_frequencies()

        # 6. timing simulation ------------------------------------------------
        if self.sequence:
            engine = TimedBattleEngine(self.sequence, enemy_av0=self.enemy_av0 or 100.0)
            steps["timing"] = engine.run(self.x0)
        else:
            steps["timing"] = {
                "note": (
                    "未提供事件序列 sigma,须补做离散时序模拟:"
                    "按真实优先级逐事件扣资源、给资源、更新状态与行动值(§7 步骤 6)。"
                )
            }

        # 7. perturbation -----------------------------------------------------
        if self.perturbations:
            report = RobustnessReport(
                A, node_names=names, tol=self.model.tol
            )
            for perturbation in self.perturbations:
                report.add(
                    perturbation.label,
                    perturbation.matrix,
                    perturbation.note,
                )
            steps["perturbation"] = report.run(rho_tol)
        else:
            steps["perturbation"] = {
                "note": (
                    "未提供扰动用例,至少应改变目标数、一次未击杀、一次治疗缺失、"
                    "一次敌方插队,观察闭环是否鲁棒(§7 步骤 7)。"
                )
            }

        # 8. version / mode -----------------------------------------------------
        steps["version"] = {
            "note": self.mode_note or (
                "不同版本、模式、祝福和敌方机制对应不同 A;"
                "不可把一张矩阵外推为通用结论(§7 步骤 8)。"
            )
        }

        return {"steps": steps, "all_done": bool(self.sequence and self.perturbations)}
