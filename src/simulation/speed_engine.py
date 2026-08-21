"""Speed-driven discrete battle engine.

Theory document mapping:

  * section 1.1 -- AV = 10000 / speed; inserted actions (follow-up,
    ultimate, extra turns) do not consume the character's normal turn,
    which is exactly how off-turn resource chains can form;
  * section 5.1 -- energy and skill points are capped (piecewise
    non-linear, `min` per component);
  * section 5.2 -- "energy full -> ultimate" is a threshold on the state:
    the executable action set (and hence the effective A) changes with
    the state s_t;
  * section 5.3 -- Executable(e) iff x_k >= cost(e) and condition(e, s_k);
  * section 5.4 -- the enemy clock q_t must stay positive at every key
    node; a loop that cannot close before the enemy acts is broken.

This engine is the discrete-event validation layer for the matrix
conclusions: the matrix says WHERE a loop can exist, this engine checks
whether it can actually close.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .priority import apply_priority_overrides

AV_BASE = 10000.0


@dataclass
class ActionSpec:
    """One executable action of an ally unit.

    `priority` orders the standard-action choice: among executable
    non-inserted actions the smallest priority wins, ties broken by
    declaration order (which is also the default priority, so data
    files that set no priorities keep their written order).
    """

    name: str
    energy_gain: float = 0.0
    energy_cost: float = 0.0
    sp_gain: float = 0.0
    sp_cost: float = 0.0
    inserted: bool = False        # does not consume the standard turn
    priority: float = 0.0
    enabled: bool = True
    condition: callable = None    # predicate(unit, team) -> bool

    def __post_init__(self):
        if self.condition is None:
            self.condition = lambda unit, team: True

    def executable(self, unit, team):
        return (
            self.enabled
            and unit.energy + 1e-9 >= self.energy_cost
            and team["sp"] + 1e-9 >= self.sp_cost
            and self.condition(unit, team)
        )


@dataclass
class BattleUnit:
    """An ally or enemy unit on the action-value clock."""

    name: str
    speed: float
    is_enemy: bool = False
    energy: float = 0.0
    energy_cap: float = 120.0     # threshold: ultimate fires when reached
    ult_cost: float = 120.0       # energy consumed by the ultimate
    actions: list = field(default_factory=list)

    def __post_init__(self):
        if self.speed <= 0:
            raise ValueError(f"speed must be positive, got {self.speed}")

    @property
    def base_av(self):
        return AV_BASE / self.speed

    def add_energy(self, amount):
        # section 5.1: energy is capped
        self.energy = min(self.energy_cap, self.energy + amount)

    def ultimate_ready(self):
        return self.energy + 1e-9 >= self.ult_cost

    def fire_ultimate(self):
        if not self.ultimate_ready():
            return False
        self.energy -= self.ult_cost
        return True


class SpeedBattleEngine:
    """Discrete-event simulator over the action-value clock."""

    def __init__(self, allies, enemy_speed, max_rounds=2000, sp_cap=5.0):
        self.allies = list(allies)
        if not self.allies:
            raise ValueError("at least one ally is required")
        self.enemy_speed = float(enemy_speed)
        if self.enemy_speed <= 0:
            raise ValueError("enemy_speed must be positive")
        self.max_rounds = int(max_rounds)
        self.sp_cap = float(sp_cap)

    def run(self, initial_energy=0.0, initial_sp=3.0):
        """Simulate until the enemy acts too soon or max_rounds.

        Returns a dict with rounds, cycles_completed, enemy_actions,
        break_reason, final state and a history log.
        """
        team = {"sp": min(float(initial_sp), self.sp_cap)}
        for unit in self.allies:
            unit.energy = min(float(initial_energy), unit.energy_cap)

        units = list(self.allies) + [
            BattleUnit(name="enemy", speed=self.enemy_speed, is_enemy=True)
        ]
        av = {unit.name: unit.base_av for unit in units}
        standard_turns = {unit.name: 0 for unit in self.allies}
        history = []
        enemy_actions = 0
        ult_count = {unit.name: 0 for unit in self.allies}
        reason = None
        rounds = 0

        for rounds in range(1, self.max_rounds + 1):
            # -- next actor: smallest action value -------------------------
            actor = min(units, key=lambda u: av[u.name])

            if actor.is_enemy:
                # section 5.4: the enemy clock hits zero -> enemy acts
                enemy_actions += 1
                av["enemy"] += actor.base_av
                history.append({"round": rounds, "event": "<enemy acts>"})
                reason = "enemy_interjection"
                break

            # -- ally standard turn -----------------------------------------
            action = self._choose_standard_action(actor, team)
            if action is None:
                reason = "no_executable_action"
                history.append({"round": rounds, "event": f"<{actor.name} stuck>"})
                break

            self._apply(action, actor, team)
            if not action.inserted:
                standard_turns[actor.name] += 1
                av[actor.name] += actor.base_av

            # -- inserted actions: ultimate threshold (section 5.2) ----------
            fired = 0
            while actor.ultimate_ready() and fired < 10:
                actor.fire_ultimate()
                ult_count[actor.name] += 1
                fired += 1
                history.append({
                    "round": rounds,
                    "event": f"{actor.name} ultimate (inserted)",
                    "energy": actor.energy,
                    "sp": team["sp"],
                })
            # generic inserted actions (follow-ups, extra turns)
            for other in self.allies:
                for inserted in other.actions:
                    if inserted.inserted and inserted.executable(other, team):
                        self._apply(inserted, other, team)
                        history.append({
                            "round": rounds,
                            "event": f"{other.name} {inserted.name} (inserted)",
                            "energy": other.energy,
                            "sp": team["sp"],
                        })

            history.append({
                "round": rounds,
                "event": f"{actor.name} {action.name}",
                "energy": actor.energy,
                "sp": team["sp"],
                "av": {name: av[name] for name in av},
            })

        cycles = min(standard_turns.values()) if standard_turns else 0
        return {
            "rounds": rounds,
            "cycles_completed": cycles,
            "enemy_actions": enemy_actions,
            "break_reason": reason,
            "ult_count": ult_count,
            "final": {
                unit.name: {
                    "energy": unit.energy,
                    "speed": unit.speed,
                    "base_av": unit.base_av,
                }
                for unit in self.allies
            },
            "final_sp": team["sp"],
            "history": history,
        }

    def _choose_standard_action(self, unit, team):
        # executable standard (non-inserted) actions, smallest priority
        # first, ties broken by declaration order
        candidates = [
            (index, action)
            for index, action in enumerate(unit.actions)
            if not action.inserted and action.executable(unit, team)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda pair: (pair[1].priority, pair[0]))[1]

    def _apply(self, action, unit, team):
        unit.add_energy(action.energy_gain)
        unit.energy -= action.energy_cost
        team["sp"] = min(self.sp_cap, max(0.0, team["sp"] + action.sp_gain - action.sp_cost))


def unit_from_character_data(data, speed=None, energy_cap=None,
                             priority_overrides=None):
    """Build a BattleUnit from a character JSON dict (schema v2).

    v2 fields: `skills` (ordered list with priority / inserted / type),
    `max_energy`, `light_cone` and `eidolons` with declarative effects
    (speed_delta, initial_energy, energy_regen_percent, grant_action).
    The legacy `events` dict/list keeps working unchanged.

    `priority_overrides` maps action name -> priority (or
    {"priority": p, "enabled": bool}) and is applied last, so team files
    can edit priorities without touching the character tables.
    """
    skills = data.get("skills")
    if skills is None:
        events = data.get("events", {})
        if isinstance(events, list):
            events = {e["name"]: e for e in events}
        skills = [dict(spec, name=name) for name, spec in events.items()]

    if energy_cap is None:
        energy_cap = float(data.get("max_energy", 120.0))
    speed = float(speed if speed is not None else data.get("speed", 100.0))
    ult_cost = energy_cap
    actions = []
    for index, spec in enumerate(skills):
        cost = float(spec.get("energy_cost", 0.0))
        if cost > 0:
            ult_cost = cost
            continue
        sp = float(spec.get("skill_points", spec.get("sp_change", 0.0)))
        actions.append(ActionSpec(
            name=spec["name"],
            energy_gain=float(spec.get("energy_gain", spec.get("energy", 0.0))),
            sp_gain=max(sp, 0.0),
            sp_cost=max(-sp, 0.0),
            inserted=bool(spec.get("inserted", False)),
            priority=float(spec.get("priority", index)),
        ))

    effects = list((data.get("light_cone") or {}).get("effects") or [])
    for eidolon in data.get("eidolons") or []:
        effects.extend(eidolon.get("effects") or [])

    initial_energy = 0.0
    for effect in effects:
        kind = effect.get("kind")
        value = float(effect.get("value", 0.0))
        if kind == "speed_delta":
            speed = max(1.0, speed + value)
        elif kind == "initial_energy":
            initial_energy += value
        elif kind == "energy_regen_percent":
            targets = effect.get("action_types")
            for action in actions:
                if targets is None or _action_type_of(skills, action.name) in targets:
                    action.energy_gain *= 1.0 + value
        elif kind == "grant_action":
            actions.append(_action_from_effect(effect["action"], len(actions)))
        # unknown kinds are rejected by validate_character at load time

    unit = BattleUnit(
        name=data.get("name", data.get("id", "unit")),
        speed=speed,
        energy_cap=energy_cap,
        ult_cost=ult_cost,
        actions=actions,
    )
    unit.energy = min(initial_energy, energy_cap)
    if priority_overrides:
        apply_priority_overrides([unit], priority_overrides)
    return unit


def _action_type_of(skills, action_name):
    for spec in skills:
        if spec.get("name") == action_name:
            return spec.get("type")
    return None


def _action_from_effect(spec, index):
    sp = float(spec.get("skill_points", spec.get("sp_change", 0.0)))
    return ActionSpec(
        name=spec["name"],
        energy_gain=float(spec.get("energy_gain", 0.0)),
        sp_gain=max(sp, 0.0),
        sp_cost=max(-sp, 0.0),
        inserted=bool(spec.get("inserted", True)),
        priority=float(spec.get("priority", index)),
    )
