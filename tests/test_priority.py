"""Priority editor tests: engine selection order + edits + overrides."""

import pytest

from src.simulation.priority import (
    PriorityEditor,
    PriorityEditorError,
    apply_priority_overrides,
)
from src.simulation.speed_engine import ActionSpec, BattleUnit, SpeedBattleEngine


def _unit(name="m", speed=100):
    return BattleUnit(name, speed=speed, actions=[
        ActionSpec("basic", energy_gain=20.0, sp_gain=1.0, priority=2),
        ActionSpec("skill", energy_gain=30.0, sp_cost=1.0, priority=0),
        ActionSpec("enhanced", energy_gain=30.0, priority=1),
    ])


def _chosen(unit, sp=3.0):
    engine = SpeedBattleEngine([unit], enemy_speed=10)
    team = {"sp": sp}
    return engine._choose_standard_action(unit, team)


def test_engine_picks_smallest_priority():
    # skill (priority 0) preferred while SP is available
    assert _chosen(_unit()).name == "skill"


def test_priority_overrides_flip_selection():
    unit = _unit()
    apply_priority_overrides([unit], {"m": {"skill": 9, "basic": 0}})
    assert _chosen(unit).name == "basic"


def test_disabled_action_is_not_chosen():
    unit = _unit()
    apply_priority_overrides([unit], {"m": {"skill": {"enabled": False}}})
    assert _chosen(unit).name == "enhanced"


def test_declaration_order_breaks_ties():
    unit = BattleUnit("m", speed=100, actions=[
        ActionSpec("first", energy_gain=1.0),
        ActionSpec("second", energy_gain=2.0),
    ])
    # no explicit priorities: both default to their declaration index
    assert _chosen(unit).name == "first"


def test_editor_set_reorder_and_serialize():
    unit = _unit()
    editor = PriorityEditor([unit])
    editor.reorder("m", ["basic", "enhanced", "skill"])
    order = [a.name for a in sorted(
        (a for a in unit.actions if not a.inserted),
        key=lambda a: a.priority,
    )]
    assert order == ["basic", "enhanced", "skill"]

    editor.disable("m", "enhanced")
    overrides = editor.to_overrides()
    assert overrides["m"]["enhanced"] == {
        "priority": 1.0, "enabled": False,
    }

    fresh = _unit()
    apply_priority_overrides([fresh], overrides)
    disabled = [a for a in fresh.actions if a.name == "enhanced"][0]
    assert disabled.enabled is False
    assert _chosen(fresh).name == "basic"


def test_editor_rejects_unknown_names():
    editor = PriorityEditor([_unit()])
    with pytest.raises(PriorityEditorError, match="unknown unit"):
        editor.set_priority("nobody", "skill", 1)
    with pytest.raises(PriorityEditorError, match="unknown action"):
        editor.set_priority("m", "nonexistent", 1)
    with pytest.raises(PriorityEditorError, match="unknown actions"):
        editor.reorder("m", ["skill", "wrong"])


def test_engine_run_respects_edited_rotation():
    unit = _unit()
    engine = SpeedBattleEngine([unit], enemy_speed=10)
    default = engine.run()
    events = [h["event"] for h in default["history"] if h["event"].endswith("skill")]
    assert events  # skill-first rotation actually fires

    apply_priority_overrides([unit], {"m": {"skill": {"enabled": False}}})
    edited = SpeedBattleEngine([unit], enemy_speed=10).run()
    assert not any(
        h["event"].endswith("skill") for h in edited["history"]
    )
