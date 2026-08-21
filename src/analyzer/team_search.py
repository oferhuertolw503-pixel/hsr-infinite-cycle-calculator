"""Team search over the speed battle engine (simulator layer).

The matrix layer answers where a loop can exist; this module searches
the discrete layer for rotations that actually sustain it:

  * rosters -- combinations of the character pool at a given team size;
  * rotations -- per unit, every ordering of its standard actions
    (priority = rank), plus the SP-negative-disabled variant of each
    ordering (skill-point saver rotations);
  * ranking -- by cycle stability: sustained runs first, then completed
    cycles, then the section-8 break class (a loop that dies by its own
    resources ranks below one closed by enemy interjection), then
    ultimate count.

Every candidate runs through SpeedBattleEngine with the same enemy
speed and round budget, so the ranking is comparable within one search.
Results stay bound to their premises (section 7 step 8): a different
enemy speed, data table or budget can reorder everything.
"""

from __future__ import annotations

import itertools
import json

from ..simulation.priority import apply_priority_overrides
from ..simulation.speed_engine import SpeedBattleEngine, unit_from_character_data
from .cycle_detector import CycleDetector

_BREAK_RANK = {
    "sustained": 0,
    "timing": 1,     # the loop closed as far as it could; the enemy acted
    "condition": 2,
    "resource": 3,   # the loop died by its own resources
    "unknown": 4,
}


def rotation_variants(character_data):
    """Priority-override maps covering the unit's standard-action space.

    One variant per ordering of the standard actions (priority = rank,
    all enabled), plus -- when the unit has SP-negative actions -- the
    same orderings with those actions disabled (SP-saver rotations).
    Variants that would disable every action are skipped.  The data
    table's own priorities are NOT included as a variant: the search
    reorders them anyway, and callers can evaluate the table order
    separately via the engine.
    """
    unit = unit_from_character_data(character_data)
    names = [action.name for action in unit.actions if not action.inserted]
    sp_negative = {
        action.name for action in unit.actions
        if not action.inserted and action.sp_cost > 1e-9
    }
    variants = {}
    for order in itertools.permutations(names):
        overrides = {
            name: {"priority": rank, "enabled": True}
            for rank, name in enumerate(order)
        }
        variants[json.dumps(overrides, sort_keys=True)] = overrides
        if sp_negative:
            saver = {
                name: (
                    {"priority": rank, "enabled": False}
                    if name in sp_negative
                    else {"priority": rank, "enabled": True}
                )
                for rank, name in enumerate(order)
            }
            if any(entry["enabled"] for entry in saver.values()):
                variants[json.dumps(saver, sort_keys=True)] = saver
    return list(variants.values())


class TeamSearch:
    """Enumerate and rank team rotations through the speed engine."""

    def __init__(self, character_pool, enemy_speed, team_size=None,
                 max_rounds=200, sp_cap=5.0, initial_energy=0.0,
                 initial_sp=3.0):
        self.character_pool = list(character_pool)
        if not self.character_pool:
            raise ValueError("the character pool is empty")
        names = [data.get("name", data.get("id")) for data in self.character_pool]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate character names in pool: {names}")
        self.team_size = int(team_size if team_size is not None
                             else len(self.character_pool))
        if not 1 <= self.team_size <= len(self.character_pool):
            raise ValueError(
                f"team_size must be between 1 and {len(self.character_pool)}"
            )
        self.enemy_speed = float(enemy_speed)
        self.max_rounds = int(max_rounds)
        self.sp_cap = float(sp_cap)
        self.initial_energy = float(initial_energy)
        self.initial_sp = float(initial_sp)

    # -- search space -----------------------------------------------------
    def rosters(self):
        """Character-data combinations at the team size, pool order."""
        for combo in itertools.combinations(self.character_pool,
                                            self.team_size):
            yield list(combo)

    def candidates(self):
        """Yield (roster, overrides) for every roster x rotation."""
        for roster in self.rosters():
            variant_lists = [rotation_variants(data) for data in roster]
            for combination in itertools.product(*variant_lists):
                overrides = {}
                for data, variant in zip(roster, combination):
                    overrides[data.get("name", data.get("id"))] = variant
                yield roster, overrides

    # -- evaluation ---------------------------------------------------------
    def evaluate(self, roster, overrides):
        """Run one roster + override map; return a ranked result row."""
        units = [
            unit_from_character_data(data) for data in roster
        ]
        apply_priority_overrides(units, overrides)
        engine = SpeedBattleEngine(
            units, enemy_speed=self.enemy_speed,
            max_rounds=self.max_rounds, sp_cap=self.sp_cap,
        )
        result = engine.run(
            initial_energy=self.initial_energy, initial_sp=self.initial_sp,
        )
        cycle = CycleDetector().analyze(result)
        ults = sum(result["ult_count"].values())
        return {
            "roster": [unit.name for unit in units],
            "overrides": overrides,
            "stable": cycle["stable"],
            "cycles_completed": result["cycles_completed"],
            "rounds": result["rounds"],
            "enemy_actions": result["enemy_actions"],
            "break_class": cycle["break_class"],
            "break_reason": result["break_reason"],
            "ult_count": dict(result["ult_count"]),
            "total_ults": ults,
        }

    @staticmethod
    def rank_key(row):
        """Stability ordering: sustained, then cycles, then break class,
        then ultimate count.  Used as a descending sort key."""
        return (
            1 if row["stable"] else 0,
            row["cycles_completed"],
            -_BREAK_RANK.get(row["break_class"], 4),
            row["total_ults"],
        )

    def search(self, limit=None, top=None):
        """Evaluate the whole candidate space and rank it."""
        rows = []
        searched = 0
        for roster, overrides in self.candidates():
            rows.append(self.evaluate(roster, overrides))
            searched += 1
        rows.sort(key=self.rank_key, reverse=True)
        if limit is not None:
            rows = rows[:limit]
        return {
            "searched": searched,
            "rows": rows if top is None else rows[:top],
            "best": rows[0] if rows else None,
            "note": (
                "排序依据:是否持续 > 完成循环数 > §8 断轴类别"
                "(时序/资源)> 终结技次数。结论绑定于本次搜索的敌方速度、"
                "轮数预算与数据表(§7 步骤 8);数据为演示量级时,排序"
                "只对模型内部有效,不构成游戏配队结论(§5)。"
            ),
        }
