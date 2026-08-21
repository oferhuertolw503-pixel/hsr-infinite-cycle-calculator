"""Full audit workflow demo: theory document section 7 end-to-end."""

import json
from pathlib import Path

import numpy as np

from src.analyzer.audit import CycleAudit
from src.data_loader.matrix_loader import load_example_json, load_transfer_matrix
from src.matrix.transfer_matrix import TransferMatrix

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "theory_document" / "audit_workflow_demo.json"


def _audit_demo():
    data = load_example_json(EXAMPLE)
    return CycleAudit(
        data["matrix"],
        node_names=data.get("nodes"),
        edge_meta=data.get("edge_meta"),
        sequence=data.get("sequence"),
        enemy_av0=data.get("enemy_av0"),
        perturbations=data.get("perturbations"),
        mode_note=data.get("mode_note"),
    )


def test_audit_demo_runs_all_eight_steps():
    report = _audit_demo().run()
    assert report["all_done"]
    assert set(report["steps"]) == {
        "granularity", "units", "edge_table", "spectral_radius",
        "perron", "timing", "perturbation", "version",
    }


def test_audit_demo_edge_meta_parsed_from_json_string_keys():
    report = _audit_demo().run()
    edges = report["steps"]["edge_table"]["edges"]
    tu_edges = [e for e in edges if e["from"] == "T_U"]
    assert any(e["depends_on_N"] for e in tu_edges)
    assert report["steps"]["edge_table"]["fully_documented"]


def test_audit_demo_base_regime_is_growth():
    data = load_example_json(EXAMPLE)
    model = TransferMatrix(data["matrix"], node_names=data.get("nodes"))
    result = model.classify()
    assert result["regime"] == "growth"
    assert np.isclose(result["rho"], 1.00522, atol=2e-5)


def test_audit_demo_perturbations_flip_and_hold_regime():
    report = _audit_demo().run()["steps"]["perturbation"]
    by_label = {row["label"]: row for row in report["cases"]}

    # target count up (N=5): stays robustly in growth
    n5 = by_label["target_count_N5"]
    assert n5["regime"] == "growth"
    assert np.isclose(n5["rho"], 1.04432, atol=2e-5)

    # a single missed kill (T_U self-energy gone) flips to decay
    missed = by_label["missed_kill_TU_self"]
    assert missed["regime"] == "decay"
    assert missed["regime_flipped"]
    assert missed["delta_rho"] < 0

    # a half heal on C -> H_U also flips to decay
    healed = by_label["half_heal_C_to_HU"]
    assert healed["regime"] == "decay"
    assert healed["regime_flipped"]

    assert len(report["flips"]) == 2


def test_audit_demo_timing_step_stable():
    report = _audit_demo().run()
    timing = report["steps"]["timing"]
    assert timing["stable"] is True
