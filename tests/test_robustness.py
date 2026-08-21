import numpy as np

from src.analyzer.robustness import RobustnessReport, drop_edge, scale_edge


def _himeko_like_matrix():
    # mildly growing 2-node loop with an extra kill-energy edge
    return np.array([[0.0, 1.0], [1.2, 0.3]])


def test_drop_edge_removes_entry():
    matrix = np.array([[0.0, 1.0], [1.2, 0.3]])
    dropped = drop_edge(matrix, 1, 0)
    assert dropped[1, 0] == 0.0
    assert dropped[0, 1] == 1.0


def test_scale_edge_halves_entry():
    matrix = np.array([[0.0, 1.0], [1.2, 0.3]])
    scaled = scale_edge(matrix, 0, 1, 0.5)
    assert scaled[0, 1] == 0.5


def test_robustness_report_flags_regime_flips():
    report = RobustnessReport(
        _himeko_like_matrix(),
        node_names=["basic", "kill"],
    )
    report.add("missed_kill", drop_edge(_himeko_like_matrix(), 1, 0))
    report.add("half_heal", scale_edge(_himeko_like_matrix(), 1, 1, 0.5))
    result = report.run()
    assert result["base"]["regime"] in ("growth", "decay", "critical")
    for row in result["cases"]:
        assert "delta_rho" in row
        assert row["regime_flipped"] in (True, False)
    # dropping the only feed edge must push rho down (weaker loop)
    missed = next(r for r in result["cases"] if r["label"] == "missed_kill")
    assert missed["delta_rho"] < 0


def test_robustness_report_works_without_perturbations():
    report = RobustnessReport([[0.5]])
    result = report.run()
    assert result["cases"] == []
    assert result["flips"] == []
