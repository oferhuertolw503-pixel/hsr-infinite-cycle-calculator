"""Eight-step review workflow: theory document section 7."""

import numpy as np

from src.analyzer.audit import CycleAudit
from src.simulation.timed_engine import TimedEvent


def _matrix():
    return np.array([[0.0, 0.9], [0.9, 0.1]])


def test_audit_produces_eight_steps():
    audit = CycleAudit(
        _matrix(),
        node_names=["basic", "ultimate"],
        units=["count", "energy"],
        edge_meta={(0, 1): {"mechanism": "basic generates energy"}},
        sequence=[TimedEvent("basic", energy_gain=10.0, av_cost=5.0)],
        enemy_av0=100.0,
        perturbations=[],
    )
    report = audit.run()
    assert set(report["steps"]) == {
        "granularity", "units", "edge_table", "spectral_radius",
        "perron", "timing", "perturbation", "version",
    }


def test_audit_granularity_is_event_based():
    audit = CycleAudit(_matrix(), node_names=["basic", "ultimate"])
    report = audit.run()
    step = report["steps"]["granularity"]
    assert step["event_count"] == 2
    assert step["events"] == ["basic", "ultimate"]


def test_audit_edge_table_lists_every_nonzero_edge():
    audit = CycleAudit(_matrix(), node_names=["basic", "ultimate"])
    report = audit.run()
    edges = report["steps"]["edge_table"]["edges"]
    assert len(edges) == 3  # (0,1), (1,0), (1,1)
    assert all(edge["value"] > 0 for edge in edges)
    assert not report["steps"]["edge_table"]["fully_documented"]


def test_audit_timing_runs_when_sequence_given():
    audit = CycleAudit(
        _matrix(),
        node_names=["basic", "ultimate"],
        sequence=[TimedEvent("basic", energy_gain=10.0, av_cost=5.0)],
        enemy_av0=1000.0,
    )
    report = audit.run()
    timing = report["steps"]["timing"]
    assert "stable" in timing
    assert timing["stable"] is True


def test_audit_version_note_defaults_to_no_extrapolation():
    audit = CycleAudit(_matrix())
    report = audit.run()
    assert "不可把一张矩阵外推" in report["steps"]["version"]["note"]


def test_audit_accepts_dict_sequence_and_perturbations():
    audit = CycleAudit(
        _matrix(),
        node_names=["basic", "ultimate"],
        sequence=[{"name": "basic", "energy_gain": 10.0, "av_cost": 5.0}],
        enemy_av0=100.0,
        perturbations=[{
            "label": "missed_ultimate",
            "matrix": [[0.0, 0.9], [0.0, 0.1]],
        }],
    )
    report = audit.run()
    perturbation = report["steps"]["perturbation"]
    assert len(perturbation["cases"]) == 1
    assert perturbation["cases"][0]["label"] == "missed_ultimate"
    assert report["all_done"]
