"""Team search tests (simulator layer: rosters x rotations x ranking)."""

import copy
from pathlib import Path

import pytest

from src.analyzer.team_search import TeamSearch, rotation_variants
from src.data_loader.character_loader import load_character
from src.simulation.speed_engine import unit_from_character_data

DATA = Path(__file__).resolve().parent.parent / "data" / "characters"


def _march():
    return load_character(DATA / "march7th_hunt.json")


def _luocha():
    return load_character(DATA / "luocha.json")


def test_rotation_variants_cover_orderings_and_savers():
    # march7th: 3 standard actions, skill is SP-negative ->
    # 6 orderings + 6 SP-saver variants, all distinct
    variants = rotation_variants(_march())
    assert len(variants) == 12
    import json
    keys = [json.dumps(v, sort_keys=True) for v in variants]
    assert len(set(keys)) == len(keys)
    for variant in variants:
        enabled = [name for name, spec in variant.items()
                   if spec["enabled"]]
        assert enabled                      # never disables everything
        priorities = sorted(spec["priority"] for spec in variant.values())
        assert priorities == list(range(len(variant)))
    savers = [v for v in variants if not v["skill"]["enabled"]]
    assert len(savers) == 6


def test_rotation_variants_without_sp_negative_actions():
    data = {
        "id": "x", "name": "X", "speed": 100,
        "skills": [
            {"name": "basic", "type": "basic", "energy_gain": 20,
             "skill_points": 1},
        ],
    }
    assert rotation_variants(data) == [
        {"basic": {"priority": 0, "enabled": True}}
    ]


def test_rank_key_orders_by_stability():
    rows = [
        {"stable": False, "cycles_completed": 3, "break_class": "resource",
         "total_ults": 5},
        {"stable": True, "cycles_completed": 2, "break_class": "sustained",
         "total_ults": 0},
        {"stable": False, "cycles_completed": 3, "break_class": "timing",
         "total_ults": 1},
        {"stable": False, "cycles_completed": 5, "break_class": "timing",
         "total_ults": 0},
        {"stable": False, "cycles_completed": 3, "break_class": "timing",
         "total_ults": 4},
    ]
    ranked = sorted(rows, key=TeamSearch.rank_key, reverse=True)
    assert ranked[0]["stable"] is True
    # more completed cycles next
    assert ranked[1]["cycles_completed"] == 5
    # same cycles: timing beats resource, then ultimate count
    assert [r["break_class"] for r in ranked[2:]] == ["timing", "timing",
                                                      "resource"]
    assert ranked[2]["total_ults"] == 4
    assert ranked[3]["total_ults"] == 1


def test_search_covers_space_and_sorts_rows():
    search = TeamSearch([_march(), _luocha()], enemy_speed=50,
                        team_size=2, max_rounds=100)
    # march: 12 variants, luocha (basic/skill): 2 + 2 = 4
    result = search.search()
    assert result["searched"] == 12 * 4
    assert len(result["rows"]) == result["searched"]
    keys = [TeamSearch.rank_key(row) for row in result["rows"]]
    assert keys == sorted(keys, reverse=True)
    assert result["best"] == result["rows"][0]
    assert set(result["best"]["roster"]) == {"三月七·巡猎", "罗刹"}
    assert "§7 步骤 8" in result["note"]


def test_evaluate_does_not_mutate_character_data():
    data = _march()
    snapshot = copy.deepcopy(data)
    search = TeamSearch([data], enemy_speed=50, max_rounds=50)
    row = search.evaluate([data], {"三月七·巡猎": {
        "skill": {"priority": 9, "enabled": False},
    }})
    assert data == snapshot                       # pool dict untouched
    fresh = unit_from_character_data(data)
    skill = [a for a in fresh.actions if a.name == "skill"][0]
    assert skill.enabled and skill.priority == 0  # defaults intact
    assert row["roster"] == ["三月七·巡猎"]


def test_search_validation():
    with pytest.raises(ValueError, match="empty"):
        TeamSearch([], enemy_speed=50)
    with pytest.raises(ValueError, match="team_size"):
        TeamSearch([_march()], enemy_speed=50, team_size=2)
    with pytest.raises(ValueError, match="duplicate"):
        TeamSearch([_march(), _march()], enemy_speed=50)
