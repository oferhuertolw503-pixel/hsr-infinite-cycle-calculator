"""Cycle repair planner and critical-parameter tests (Phase 3, §8)."""

from pathlib import Path

import numpy as np

from src.analyzer.optimizer import (
    CycleRepairPlanner,
    critical_parameter,
    minimal_edge_boost,
)
from src.data_loader.matrix_loader import load_example_json, load_family
from src.matrix.family import MatrixFamily
from src.matrix.transfer_matrix import TransferMatrix

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"


def _four_node():
    data = load_example_json(EXAMPLES / "four_node_model_N5.json")
    return TransferMatrix(data["matrix"], node_names=data["nodes"])


def _audit_demo():
    data = load_example_json(EXAMPLES / "audit_workflow_demo.json")
    return TransferMatrix(data["matrix"], node_names=data["nodes"])


def test_minimal_boosts_reach_target_exactly():
    plan = CycleRepairPlanner(_four_node()).plan(target_rho=1.0)
    assert plan["needed"] is True
    assert plan["candidates"]
    for row in plan["candidates"]:
        # rho is monotone in a single entry: bisection brackets 1.
        assert np.isclose(row["achieved_rho"], 1.0, atol=1e-6)
        assert row["new_value"] > row["value"]


def test_best_repair_on_most_fragile_self_loop():
    # First-order: the needed boost is (1 - rho) / (u_i v_j a_ij).  The
    # cheapest single intervention lands on the H_U self-loop (the most
    # fragile edge, section 4/8), not necessarily on the highest-elasticity
    # edge (C -> H_U) once nonlinearity is accounted for.
    plan = CycleRepairPlanner(_four_node()).plan(target_rho=1.0)
    best = plan["best"]
    assert (best["from"], best["to"]) == ("H_U", "H_U")
    assert best["kind"] == "boost"
    # The bisection result agrees with the elasticity estimate.
    assert np.isclose(best["added"], best["first_order_added"], rtol=0.15)


def test_no_repair_needed_when_already_growth():
    plan = CycleRepairPlanner(_audit_demo()).plan(target_rho=1.0)
    assert plan["needed"] is False
    assert plan["best"] is None
    assert "无需修复" in plan["note"]


def test_nilpotent_chain_requires_added_edge():
    # Acyclic chain: boosting existing edges keeps rho = 0 (theorem 1
    # in the extreme); only new edges work.  The cheapest is a 1.0
    # self-loop; closing the cycle a->b->c->a needs x = 4 because
    # rho = (0.5 * 0.5 * x)^(1/3) = 1.
    chain = TransferMatrix([[0, 0.5, 0], [0, 0, 0.5], [0, 0, 0]],
                           node_names=["a", "b", "c"])
    assert minimal_edge_boost(chain.A, 0, 1, target_rho=1.0) is None
    plan = CycleRepairPlanner(chain).plan(target_rho=1.0)
    assert plan["needed"] is True
    assert all(row["kind"] == "add" for row in plan["candidates"])
    best = plan["best"]
    assert best["kind"] == "add"
    assert np.isclose(best["added"], 1.0, atol=1e-4)
    assert np.isclose(best["achieved_rho"], 1.0, atol=1e-6)
    by_edge = {(row["from"], row["to"]): row for row in plan["candidates"]}
    back = by_edge[("c", "a")]
    assert np.isclose(back["added"], 4.0, atol=1e-4)
    assert np.isclose(back["achieved_rho"], 1.0, atol=1e-6)


def test_critical_parameter_of_seven_node_family():
    family = load_family(EXAMPLES / "seven_node_family.json")
    result = critical_parameter(family)
    assert result["status"] == "already_at_or_above"
    assert result["critical_key"] == "2"
    assert result["sub_critical_key"] is None


def test_critical_parameter_locates_crossing():
    family = MatrixFamily(
        name="synthetic",
        nodes=["a"],
        matrices_by_key={"2": [[0.5]], "3": [[0.9]], "4": [[1.2]]},
    )
    result = critical_parameter(family)
    assert result["status"] == "reached"
    assert result["critical_key"] == "4"
    assert result["sub_critical_key"] == "3"
    assert np.isclose(result["critical_rho"], 1.2)
    assert "目标数进入系统" in result["note"]


def test_critical_parameter_all_decay_warns_against_extrapolation():
    family = MatrixFamily(
        name="synthetic",
        nodes=["a"],
        matrices_by_key={"2": [[0.5]], "3": [[0.9]]},
    )
    result = critical_parameter(family)
    assert result["status"] == "all_decay"
    assert result["critical_key"] is None
    assert "外推" in result["note"]
