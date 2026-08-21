"""Timed, ordered battle execution (theory document sections 5.3, 5.4).

The matrix model records how many resources events produce, but not the
order in which they can be used:

  * section 5.3 -- Executable(e_k) iff x_k >= cost(e_k) and
    condition(e_k, s_k); an energy gain that happens AFTER an ultimate
    cannot pay for that ultimate;
  * section 5.4 -- the enemy clock q_t must stay positive at every key
    node, and the loop must close before q_t hits zero; inserted actions
    (100% advance, extra turns, events that do not push the normal action
    bar) do not advance q_t, so it may stay high -- but that still
    depends on strict priority and trigger order.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TimedEvent:
    """One event in the ordered sequence sigma."""

    name: str
    energy_cost: float = 0.0
    energy_gain: float = 0.0
    sp_cost: float = 0.0
    sp_gain: float = 0.0
    av_cost: float = 0.0          # normal turns advance the enemy clock by this
    no_advance: bool = False      # extra-turn / 100% advance: does not advance it
    condition: callable = None    # optional predicate(state) -> bool

    def __post_init__(self):
        if self.condition is None:
            self.condition = lambda state: True


class TimedBattleEngine:
    """Execute a fixed event sequence against the enemy clock.

    Resource caps are NOT enforced here (that is the CappedTransferSystem
    concern); this engine checks executability and timing only.
    """

    def __init__(self, sequence, enemy_av0, max_loops=100):
        self.sequence = list(sequence)
        self.enemy_av0 = float(enemy_av0)
        self.max_loops = int(max_loops)

    def run(self, x0):
        """x0: dict-like with 'energy' and 'skill_points' keys."""
        state = {
            "energy": float(x0.get("energy", 0.0)),
            "skill_points": float(x0.get("skill_points", 0.0)),
        }
        q = self.enemy_av0
        history = []
        reason = None
        loops_done = 0

        for loops_done in range(1, self.max_loops + 1):
            broken = False
            for event in self.sequence:
                if q <= 0:
                    reason = "enemy_interjection"
                    broken = True
                    break
                if state["energy"] + 1e-9 < event.energy_cost:
                    reason = f"energy_shortage_at_{event.name}"
                    broken = True
                    break
                if state["skill_points"] + 1e-9 < event.sp_cost:
                    reason = f"skill_point_shortage_at_{event.name}"
                    broken = True
                    break
                if not event.condition(state):
                    reason = f"condition_failed_at_{event.name}"
                    broken = True
                    break

                state["energy"] += event.energy_gain - event.energy_cost
                state["skill_points"] += event.sp_gain - event.sp_cost
                if not event.no_advance:
                    q -= event.av_cost
                    if q <= 0:
                        # the loop must close before the enemy clock runs out
                        reason = "enemy_interjection"
                        broken = True
                        history.append({
                            "loop": loops_done,
                            "event": event.name,
                            "energy": state["energy"],
                            "skill_points": state["skill_points"],
                            "q": q,
                        })
                        break
                history.append({
                    "loop": loops_done,
                    "event": event.name,
                    "energy": state["energy"],
                    "skill_points": state["skill_points"],
                    "q": q,
                })
            if broken:
                break

        return {
            "stable": reason is None,
            "loops_completed": loops_done if reason is None else loops_done - 1,
            "break_reason": reason,
            "enemy_av": q,
            "final_state": state,
            "history": history,
        }
