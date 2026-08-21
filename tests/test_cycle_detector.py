"""Cycle break classification tests (theory section 8).

The detector consumes the result dicts of TimedBattleEngine and
SpeedBattleEngine and answers "断轴究竟是资源问题还是时序问题".
"""

import pytest

from src.analyzer.cycle_detector import CycleDetector
from src.simulation.timed_engine import TimedBattleEngine, TimedEvent


def _detector():
    return CycleDetector()


def test_sustained_run():
    engine = TimedBattleEngine(
        [TimedEvent(name="e", energy_cost=1.0, energy_gain=1.0)],
        enemy_av0=100.0,
    )
    result = _detector().analyze(engine.run({"energy": 1.0}))
    assert result["stable"] is True
    assert result["break_class"] == "sustained"
    assert result["loops_completed"] == 100
    assert result["enemy_interjected"] is False


def test_energy_shortage_is_resource_problem():
    engine = TimedBattleEngine(
        [TimedEvent(name="ult", energy_cost=5.0, energy_gain=0.0)],
        enemy_av0=100.0,
    )
    result = _detector().analyze(engine.run({"energy": 3.0}))
    assert result["stable"] is False
    assert result["break_class"] == "resource"
    assert result["break_reason"].startswith("energy_shortage_at_")
    assert "资源问题" in result["note"]


def test_enemy_interjection_is_timing_problem():
    engine = TimedBattleEngine(
        [TimedEvent(name="act", av_cost=60.0)], enemy_av0=100.0
    )
    result = _detector().analyze(engine.run({}))
    assert result["stable"] is False
    assert result["break_class"] == "timing"
    assert result["enemy_interjected"] is True
    assert "时序问题" in result["note"]


def test_failed_condition_is_condition_problem():
    engine = TimedBattleEngine(
        [TimedEvent(name="ult", energy_cost=0.0,
                    condition=lambda state: False)],
        enemy_av0=100.0,
    )
    result = _detector().analyze(engine.run({}))
    assert result["break_class"] == "condition"
    assert "触发问题" in result["note"]


def test_speed_engine_result_shapes():
    detector = _detector()
    stuck = detector.analyze({
        "cycles_completed": 3, "break_reason": "no_executable_action",
        "enemy_actions": 0,
    })
    assert stuck["break_class"] == "resource"
    assert stuck["loops_completed"] == 3

    enemy = detector.analyze({
        "cycles_completed": 7, "break_reason": "enemy_interjection",
        "enemy_actions": 1,
    })
    assert enemy["break_class"] == "timing"
    assert enemy["enemy_interjected"] is True


def test_unknown_reason_classified_and_noted():
    result = _detector().analyze({"cycles_completed": 2,
                                  "break_reason": "something_new"})
    assert result["break_class"] == "unknown"
    assert result["note"]


def test_rejects_non_dict_input():
    with pytest.raises(TypeError):
        _detector().analyze(["not", "a", "result"])
