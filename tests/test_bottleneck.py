"""Bottleneck analyzer tests (theory sections 4 and 8).

Covers the analytic elasticity d rho/d a_ij = u_i v_j / (u^T v), its
cross-check against finite differences, the fragile-edge (complete
removal) ranking, and the numeric fallback for periodic digraphs.
"""

from pathlib import Path

import numpy as np

from src.analyzer.bottleneck import BottleneckAnalyzer
from src.data_loader.matrix_loader import load_example_json
from src.matrix.transfer_matrix import TransferMatrix

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"


def _four_node():
    data = load_example_json(EXAMPLES / "four_node_model_N5.json")
    return TransferMatrix(data["matrix"], node_names=data["nodes"])


def _audit_demo():
    data = load_example_json(EXAMPLES / "audit_workflow_demo.json")
    return TransferMatrix(data["matrix"], node_names=data["nodes"])


def test_elasticity_matches_finite_differences():
    analysis = BottleneckAnalyzer(_four_node()).analyze()
    assert analysis["analytic"] is True
    # The rank-1 reconstruction is smooth: central differences should
    # agree with the Karlin formula to high accuracy.
    assert analysis["max_relative_error"] < 1e-6


def test_decisive_edge_maximizes_perron_product():
    # The four-node example is symmetric, so u = v and the elasticity
    # u_i v_j / (u^T v) = v_i v_j / (v^T v) is maximal on (B, B)
    # because B carries the largest Perron frequency.
    analysis = BottleneckAnalyzer(_four_node()).analyze()
    top = analysis["decisive_edges"][0]
    assert (top["from"], top["to"]) == ("B", "B")
    elasticities = [row["d_rho"] for row in analysis["decisive_edges"]]
    assert top["d_rho"] == max(elasticities)


def test_scarce_node_is_smallest_perron_frequency():
    analysis = BottleneckAnalyzer(_four_node()).analyze()
    scarce = analysis["scarce_node"]
    assert scarce["node"] == "C"
    # Documented Perron vector (0.304637, 0.832597, 0.202899, 0.415706)
    # normalized to sum 1 gives C the smallest share ~0.1156.
    assert np.isclose(scarce["frequency"], 0.115557, atol=1e-4)


def test_fragile_edges_report_removal_impact():
    analysis = BottleneckAnalyzer(_four_node()).analyze()
    rho = analysis["rho"]
    for row in analysis["fragile_edges"][:3]:
        assert row["load_bearing"] is True
        assert row["drop_rho"] < rho
        assert np.isclose(row["drop_delta"], row["drop_rho"] - rho)
    # The strongest edge is also the most fragile one here.
    fragile_top = analysis["fragile_edges"][0]
    assert (fragile_top["from"], fragile_top["to"]) == ("B", "B")


def test_audit_demo_missed_kill_edge_is_load_bearing():
    # Zeroing T_U's self-energy edge is the audit demo's "missed kill"
    # perturbation: it flips the regime to decay, so the edge must be
    # flagged load-bearing with drop_rho < 1 even though its *marginal*
    # elasticity is small -- local and total sensitivity differ (§4).
    analysis = BottleneckAnalyzer(_audit_demo()).analyze()
    edges = {
        (row["from"], row["to"]): row for row in analysis["decisive_edges"]
    }
    tu_self = edges[("T_U", "T_U")]
    assert tu_self["load_bearing"] is True
    assert tu_self["drop_rho"] < 1.0
    ch_hu = edges[("C", "H_U")]
    assert ch_hu["load_bearing"] is True
    assert ch_hu["drop_rho"] < 1.0
    # ... while many edges with larger local elasticity exist.
    assert tu_self["d_rho"] < analysis["decisive_edges"][0]["d_rho"]


def test_periodic_digraph_falls_back_to_numeric():
    model = TransferMatrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]],
                           node_names=["a", "b", "c"])
    analysis = BottleneckAnalyzer(model).analyze()
    assert analysis["analytic"] is False
    assert np.isclose(analysis["rho"], 1.0)
    # The numeric ranking is still produced and ordered.
    grads = [abs(row["d_rho"]) for row in analysis["decisive_edges"]]
    assert grads == sorted(grads, reverse=True)
    assert "退化为数值差分" in analysis["note"]


def test_dormant_edges_listed_for_dense_matrix():
    # A sparse matrix has zero edges; their one-sided gradients show the
    # marginal benefit of wiring in a new link.
    model = TransferMatrix([[0.5, 0, 0.2], [0, 0.3, 0], [0, 0.4, 0]],
                           node_names=["a", "b", "c"])
    analysis = BottleneckAnalyzer(model).analyze()
    assert analysis["dormant_edges"]
    grads = [row["d_rho"] for row in analysis["dormant_edges"]]
    assert grads == sorted(grads, reverse=True)
    assert all(g > 0 for g in grads)
