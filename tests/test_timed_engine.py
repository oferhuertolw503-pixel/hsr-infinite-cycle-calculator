"""Timed, ordered execution: theory document sections 5.3 and 5.4."""

from src.simulation.timed_engine import TimedBattleEngine, TimedEvent


def _sequence_ultimate_before_energy():
    # an ultimate that costs 120 energy is placed BEFORE the event that
    # grants 30 energy: the gain cannot pay for the earlier cost (5.3)
    return [
        TimedEvent("ultimate", energy_cost=120.0, av_cost=10.0),
        TimedEvent("basic", energy_gain=30.0, sp_gain=1.0, av_cost=10.0),
    ]


def _sequence_energy_before_ultimate():
    # same events in the other order; the ultimate is affordable and the
    # enemy clock decides the break
    return [
        TimedEvent("basic", energy_gain=30.0, sp_gain=1.0, av_cost=10.0),
        TimedEvent("ultimate", energy_cost=20.0, av_cost=10.0),
    ]


def test_energy_gain_after_cost_cannot_pay_it():
    engine = TimedBattleEngine(_sequence_ultimate_before_energy(), enemy_av0=1000.0)
    result = engine.run({"energy": 0.0, "skill_points": 0.0})
    assert not result["stable"]
    assert result["break_reason"].startswith("energy_shortage_at_ultimate")
    assert result["loops_completed"] == 0


def test_ordering_swap_keeps_loop_running_until_enemy():
    engine = TimedBattleEngine(_sequence_energy_before_ultimate(), enemy_av0=25.0)
    result = engine.run({"energy": 0.0, "skill_points": 0.0})
    # with the ultimate affordable, energy accumulates; the enemy clock
    # decides the break (section 5.4)
    assert result["break_reason"] == "enemy_interjection"
    assert result["enemy_av"] <= 0
    assert not result["stable"]
    assert result["final_state"]["energy"] >= 0


def test_inserted_actions_do_not_advance_enemy_clock():
    # theory 5.4: extra-turn / 100%-advance events do not push the normal
    # action bar, so q_t lasts longer
    normal = TimedBattleEngine(
        [TimedEvent("basic", energy_gain=10.0, av_cost=10.0),
         TimedEvent("extra", energy_gain=0.0, av_cost=10.0)],
        enemy_av0=30.0,
        max_loops=20,
    )
    inserted = TimedBattleEngine(
        [TimedEvent("basic", energy_gain=10.0, av_cost=10.0),
         TimedEvent("extra", energy_gain=0.0, av_cost=0.0, no_advance=True)],
        enemy_av0=30.0,
        max_loops=20,
    )
    normal_result = normal.run({"energy": 0.0, "skill_points": 0.0})
    inserted_result = inserted.run({"energy": 0.0, "skill_points": 0.0})
    assert normal_result["break_reason"] == "enemy_interjection"
    assert inserted_result["loops_completed"] > normal_result["loops_completed"]


def test_condition_gate_blocks_event():
    def only_when_energized(state):
        return state["energy"] >= 100.0

    sequence = [
        TimedEvent("skill", energy_gain=10.0, av_cost=5.0),
        TimedEvent("ultimate", energy_cost=0.0, av_cost=5.0,
                   condition=only_when_energized),
    ]
    engine = TimedBattleEngine(sequence, enemy_av0=1000.0)
    result = engine.run({"energy": 0.0, "skill_points": 0.0})
    assert result["break_reason"].startswith("condition_failed_at_ultimate")


def test_history_records_enemy_clock():
    engine = TimedBattleEngine(
        [TimedEvent("basic", energy_gain=10.0, av_cost=4.0)],
        enemy_av0=10.0,
        max_loops=3,
    )
    result = engine.run({"energy": 0.0, "skill_points": 0.0})
    # 10 - 4*3 = -2 after the third event -> enemy interjects
    assert result["break_reason"] == "enemy_interjection"
    assert result["enemy_av"] <= 0
    assert len(result["history"]) == 3
