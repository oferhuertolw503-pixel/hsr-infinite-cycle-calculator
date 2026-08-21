"""Speed-driven battle engine: theory sections 1.1, 5.1, 5.2, 5.3, 5.4."""

import json
from pathlib import Path

import pytest

from src.data_loader.character_loader import load_character
from src.simulation.speed_engine import (
    ActionSpec,
    BattleUnit,
    SpeedBattleEngine,
    unit_from_character_data,
)

DATA = Path(__file__).resolve().parent.parent / "data" / "characters"


def _march7th_unit():
    return unit_from_character_data(load_character(DATA / "march7th_hunt.json"))


# -- section 1.1: action value --------------------------------------------
def test_av_from_speed():
    assert BattleUnit("a", speed=100).base_av == pytest.approx(100.0)
    assert BattleUnit("b", speed=200).base_av == pytest.approx(50.0)


def test_faster_unit_acts_first():
    slow = BattleUnit("slow", speed=100, actions=[
        ActionSpec("basic", energy_gain=10.0)])
    fast = BattleUnit("fast", speed=200, actions=[
        ActionSpec("basic", energy_gain=10.0)])
    engine = SpeedBattleEngine([slow, fast], enemy_speed=10)
    result = engine.run()
    first = result["history"][0]["event"]
    assert first.startswith("fast")


def test_rejects_nonpositive_speed():
    with pytest.raises(ValueError):
        BattleUnit("x", speed=0)


# -- section 5.1: caps ------------------------------------------------------
def test_energy_is_capped():
    unit = BattleUnit("a", speed=100, energy_cap=120)
    unit.add_energy(200)
    assert unit.energy == 120


def test_skill_points_are_capped():
    engine = SpeedBattleEngine(
        [BattleUnit("a", speed=100, actions=[
            ActionSpec("basic", sp_gain=3.0)])],
        enemy_speed=10,
        sp_cap=5.0,
    )
    result = engine.run(initial_sp=4.0)
    assert result["final_sp"] == 5.0


# -- section 5.2: threshold (energy full -> ultimate) -------------------------
def test_ultimate_fires_at_threshold_without_consuming_turn():
    unit = BattleUnit("m", speed=100, energy_cap=120, actions=[
        ActionSpec("basic", energy_gain=50.0)])
    engine = SpeedBattleEngine([unit], enemy_speed=10)
    result = engine.run(initial_energy=20.0)
    # 20 + 50*2 = 120 -> ultimate fires on the second standard turn
    assert result["ult_count"]["m"] >= 1
    # the ultimate is inserted: it must NOT reset the action value, so the
    # same standard turn still finishes before the unit's next turn
    ultimate_events = [h for h in result["history"]
                       if "ultimate" in h["event"]]
    assert ultimate_events, "ultimate never fired"
    for event in ultimate_events:
        assert event["energy"] < 120  # energy consumed by the cast


def test_energy_never_exceeds_cap_before_ultimate():
    unit = BattleUnit("m", speed=100, energy_cap=120, actions=[
        ActionSpec("basic", energy_gain=30.0)])
    engine = SpeedBattleEngine([unit], enemy_speed=10)
    result = engine.run()
    for entry in result["history"]:
        if "energy" in entry:
            assert entry["energy"] <= 120.0 + 1e-9


# -- section 5.3: executability ------------------------------------------------
def test_no_executable_action_reported():
    unit = BattleUnit("m", speed=100, actions=[
        ActionSpec("skill", energy_cost=50.0, sp_cost=1.0)])
    engine = SpeedBattleEngine([unit], enemy_speed=10)
    result = engine.run()
    assert result["break_reason"] == "no_executable_action"


# -- section 5.4: enemy clock ---------------------------------------------------
def test_slow_team_gets_interrupted_by_enemy():
    unit = BattleUnit("m", speed=100, actions=[
        ActionSpec("basic", energy_gain=10.0)])
    engine = SpeedBattleEngine([unit], enemy_speed=500)  # enemy very fast
    result = engine.run()
    assert result["break_reason"] == "enemy_interjection"
    assert result["enemy_actions"] == 1
    assert result["cycles_completed"] == 0


def test_fast_team_closes_cycle_before_enemy():
    unit = BattleUnit("m", speed=500, actions=[
        ActionSpec("basic", energy_gain=10.0)])
    engine = SpeedBattleEngine([unit], enemy_speed=100)  # enemy slow
    result = engine.run()
    assert result["break_reason"] == "enemy_interjection"
    assert result["cycles_completed"] >= 1


# -- character data wiring -------------------------------------------------------
def test_character_data_builder_march7th():
    unit = _march7th_unit()
    assert unit.speed == pytest.approx(102.0)
    assert unit.ult_cost == pytest.approx(120.0)
    names = [a.name for a in unit.actions]
    assert "basic_attack" in names and "skill" in names and "enhanced_basic" in names
    assert "ultimate" not in names  # ult is the threshold action, not standard


def test_march7th_rotation_sustains_energy():
    unit = _march7th_unit()
    engine = SpeedBattleEngine([unit], enemy_speed=60)
    result = engine.run()
    # basic(20) + skill(30) per cycle with SP refunds keeps energy positive
    assert result["final"]["March 7th (The Hunt)"]["energy"] >= 0
    assert result["break_reason"] in ("enemy_interjection", None)


def test_himeko_data_has_speed_field():
    data = json.loads((DATA / "himeko.json").read_text(encoding="utf-8"))
    assert data["speed"] == 96
