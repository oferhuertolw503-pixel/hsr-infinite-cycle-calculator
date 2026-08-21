"""Character data loading and schema validation (game-side data, v2).

Schema v2 (see docs/character_data_schema.md):

    {
      "id": "himeko", "name": "姬子", "path": "Erudition",
      "element": "Fire", "rarity": 5, "speed": 96, "max_energy": 120,
      "skills": [
        {"name": "basic_attack", "type": "basic", "energy_gain": 20,
         "skill_points": 1, "priority": 2},
        {"name": "ultimate", "type": "ultimate", "energy_cost": 120},
        {"name": "follow_up_attack", "type": "talent", "energy_gain": 10,
         "inserted": true, "trigger": "weakness_break"}
      ],
      "light_cone": {"name": "于夜色中", "superimposition": 1,
                     "effects": [{"kind": "energy_regen_percent",
                                  "value": 0.10}]},
      "eidolons": [{"rank": 1, "effects": [{"kind": "speed_delta",
                                            "value": 4}]}],
      "notes": "..."
    }

The legacy `events` format (dict or list) keeps loading unchanged.
Validation only enforces what the simulator consumes: identity, speed,
skill arithmetic and the supported effect kinds.
"""

import json
from pathlib import Path

_SKILL_TYPES = {"basic", "skill", "ultimate", "talent", "technique"}
_EFFECT_KINDS = {
    "speed_delta", "initial_energy", "energy_regen_percent", "grant_action",
}


class CharacterDataError(ValueError):
    """Raised when character data violates the schema."""


def load_character(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_team(paths):
    return [load_character(p) for p in paths]


def _number(value, label, issues):
    try:
        return float(value)
    except (TypeError, ValueError):
        issues.append(f"{label} must be a number, got {value!r}")
        return None


def _check_effect(effect, label, issues):
    kind = effect.get("kind")
    if kind not in _EFFECT_KINDS:
        issues.append(
            f"{label}: unknown effect kind {kind!r}; expected one of "
            f"{sorted(_EFFECT_KINDS)}"
        )
        return
    if kind != "grant_action":
        _number(effect.get("value", 0), f"{label}.value", issues)
    else:
        action = effect.get("action")
        if not isinstance(action, dict) or not action.get("name"):
            issues.append(f"{label}: grant_action needs an 'action' dict "
                          "with a 'name'")


def validate_character(data):
    """Return a validation report dict; raise nothing."""
    issues = []
    if not isinstance(data, dict):
        return {"valid": False, "issues": ["character data must be an object"]}

    if not (data.get("name") or data.get("id")):
        issues.append("needs a 'name' or 'id'")
    speed = _number(data.get("speed", 100), "speed", issues)
    if speed is not None and speed <= 0:
        issues.append(f"speed must be positive, got {speed}")
    if "max_energy" in data:
        energy = _number(data["max_energy"], "max_energy", issues)
        if energy is not None and energy <= 0:
            issues.append(f"max_energy must be positive, got {energy}")

    skills = data.get("skills")
    if skills is None:
        if "events" not in data:
            issues.append("needs either 'skills' (v2) or 'events' (legacy)")
    elif not isinstance(skills, list):
        issues.append("'skills' must be a list")
    else:
        names = set()
        for index, skill in enumerate(skills):
            label = f"skills[{index}]"
            if not isinstance(skill, dict) or not skill.get("name"):
                issues.append(f"{label} needs a 'name'")
                continue
            if skill["name"] in names:
                issues.append(f"duplicate skill name {skill['name']!r}")
            names.add(skill["name"])
            skill_type = skill.get("type")
            if skill_type is not None and skill_type not in _SKILL_TYPES:
                issues.append(
                    f"{label}.type {skill_type!r} not in {sorted(_SKILL_TYPES)}"
                )
            for key in ("energy_gain", "energy_cost", "skill_points",
                        "priority"):
                if key in skill:
                    _number(skill[key], f"{label}.{key}", issues)
            cost = skill.get("energy_cost", 0)
            gain = skill.get("energy_gain", 0)
            if cost and gain:
                issues.append(
                    f"{label}: a skill with energy_cost should not also "
                    "carry energy_gain (ultimate threshold semantics)"
                )

    light_cone = data.get("light_cone")
    if light_cone is not None:
        if not light_cone.get("name"):
            issues.append("light_cone needs a 'name'")
        for index, effect in enumerate(light_cone.get("effects") or []):
            _check_effect(effect, f"light_cone.effects[{index}]", issues)

    eidolons = data.get("eidolons")
    if eidolons is not None:
        if not isinstance(eidolons, list):
            issues.append("'eidolons' must be a list")
        else:
            ranks = [e.get("rank") for e in eidolons]
            if any(not isinstance(rank, int) or rank < 1 or rank > 6
                   for rank in ranks):
                issues.append("eidolon ranks must be integers 1..6")
            for index, eidolon in enumerate(eidolons):
                for jndex, effect in enumerate(eidolon.get("effects") or []):
                    _check_effect(
                        effect, f"eidolons[{index}].effects[{jndex}]", issues
                    )

    return {"valid": not issues, "issues": issues}


def load_character_validated(path):
    """Load a character file and raise CharacterDataError when invalid."""
    data = load_character(path)
    report = validate_character(data)
    if not report["valid"]:
        raise CharacterDataError(
            f"{path}: " + "; ".join(report["issues"])
        )
    return data


def available_characters(directory="data/characters"):
    """List character JSON paths in a data directory."""
    return sorted(Path(directory).glob("*.json"))
