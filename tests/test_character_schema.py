"""Character schema v2 validation and data-table tests."""

import json
from pathlib import Path

import pytest

from src.data_loader.character_loader import (
    CharacterDataError,
    available_characters,
    load_character,
    load_character_validated,
    validate_character,
)
from src.simulation.speed_engine import unit_from_character_data

DATA = Path(__file__).resolve().parent.parent / "data" / "characters"


def test_all_shipped_character_files_validate():
    files = available_characters(DATA)
    assert len(files) >= 4
    for path in files:
        data = load_character_validated(path)
        assert data.get("name") or data.get("id")


def test_valid_v2_character_passes():
    data = {
        "id": "x", "name": "X", "speed": 100, "max_energy": 130,
        "skills": [
            {"name": "basic_attack", "type": "basic", "energy_gain": 20,
             "skill_points": 1, "priority": 1},
            {"name": "ultimate", "type": "ultimate", "energy_cost": 130},
        ],
        "light_cone": {"name": "lc", "superimposition": 1,
                       "effects": [{"kind": "initial_energy", "value": 20}]},
        "eidolons": [{"rank": 2, "effects": [{"kind": "speed_delta",
                                              "value": 2}]}],
    }
    assert validate_character(data)["valid"]


def test_validation_reports_each_issue():
    data = {
        "speed": -5,
        "skills": [
            {"name": "a", "type": "weird", "priority": "high"},
            {"name": "a"},                                   # duplicate
            {"name": "b", "energy_cost": 120, "energy_gain": 5},
        ],
        "light_cone": {"effects": [{"kind": "unknown_kind", "value": 1}]},
        "eidolons": [{"rank": 9, "effects": []}],
    }
    report = validate_character(data)
    assert not report["valid"]
    joined = "; ".join(report["issues"])
    assert "name" in joined                     # missing identity
    assert "positive" in joined                 # speed
    assert "weird" in joined                    # skill type
    assert "duplicate" in joined
    assert "energy_gain" in joined              # cost+gain conflict
    assert "unknown_kind" in joined
    assert "1..6" in joined                     # eidolon rank


def test_load_character_validated_raises():
    bad = DATA.parent / "_bad_character.json"
    bad.write_text(json.dumps({"id": "bad", "speed": 0}), encoding="utf-8")
    try:
        with pytest.raises(CharacterDataError, match="speed"):
            load_character_validated(bad)
    finally:
        bad.unlink()


def test_legacy_events_format_still_loads():
    legacy = {
        "name": "legacy",
        "speed": 100,
        "events": [
            {"name": "attack", "energy": 20},
            {"name": "ultimate", "energy_cost": 120},
        ],
    }
    assert validate_character(legacy)["valid"]
    unit = unit_from_character_data(legacy)
    assert unit.ult_cost == 120.0
    assert [a.name for a in unit.actions] == ["attack"]


def test_light_cone_and_eidolon_effects_apply():
    data = load_character(DATA / "himeko.json")
    unit = unit_from_character_data(data)
    # light cone: energy_regen_percent on basic/skill/talent gains
    basic = [a for a in unit.actions if a.name == "basic_attack"][0]
    assert basic.energy_gain == pytest.approx(20.0 * 1.05)

    march = load_character(DATA / "march7th_hunt.json")
    unit = unit_from_character_data(march)
    assert unit.speed == pytest.approx(102.0 + 4.0)  # E1 speed_delta


def test_grant_action_effect_adds_inserted_action():
    data = {
        "id": "x", "name": "X", "speed": 100,
        "skills": [{"name": "basic_attack", "type": "basic",
                    "energy_gain": 20, "skill_points": 1}],
        "light_cone": {"name": "lc", "effects": [{
            "kind": "grant_action",
            "action": {"name": "lc_follow_up", "energy_gain": 5,
                       "inserted": True},
        }]},
    }
    assert validate_character(data)["valid"]
    unit = unit_from_character_data(data)
    names = {a.name: a for a in unit.actions}
    assert names["lc_follow_up"].inserted is True
    assert names["lc_follow_up"].energy_gain == 5.0


def test_max_energy_sets_threshold():
    data = load_character(DATA / "luocha.json")
    unit = unit_from_character_data(data)
    assert unit.energy_cap == 90.0
    assert unit.ult_cost == 90.0
