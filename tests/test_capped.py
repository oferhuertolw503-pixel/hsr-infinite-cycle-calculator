import numpy as np
import pytest

from src.matrix.capped import CappedTransferSystem
from src.matrix.transfer_matrix import MatrixValidationError


def test_capped_converges_where_linear_grows():
    # rho(A) = 2 > 1, but the cap clips growth at 1.0 (theory section 5.1)
    system = CappedTransferSystem([[2.0]], caps=[1.0])
    trajectory = system.iterate([0.25], steps=10)
    assert trajectory[-1][0] == 1.0
    result = system.run_until_cycle([0.25])
    assert result["status"] == "fixed_point"
    assert result["x"][0] == 1.0
    assert result["saturated"] == 1.0


def test_capped_fixed_point_with_exogenous_input():
    # x* = min(1, 0.5 x* + 0.4) -> x* = 0.8 (below cap)
    system = CappedTransferSystem([[0.5]], caps=[1.0])
    result = system.run_until_cycle([0.0], b=[0.4])
    assert result["status"] == "fixed_point"
    assert np.isclose(result["x"][0], 0.8)


def test_capped_detects_two_cycle():
    # alternating clipping produces a 2-cycle
    system = CappedTransferSystem([[0.0, 1.0], [1.0, 0.0]], caps=[1.0, 1.0])
    result = system.run_until_cycle([0.0, 1.0])
    assert result["status"] in ("2_cycle", "fixed_point")


def test_capped_linear_comparison():
    system = CappedTransferSystem([[2.0]], caps=[1.0])
    comparison = system.linear_comparison([0.25], steps=8)
    assert comparison["rho"] > 1
    assert comparison["capped_total"] < comparison["linear_total"]
    assert "封顶" in comparison["note"]


def test_capped_saturation_rate():
    system = CappedTransferSystem([[2.0]], caps=[1.0])
    trajectory = system.iterate([0.25], steps=6)
    rates = system.saturation_rate(trajectory)
    assert 0.0 < rates[0] < 1.0  # late steps saturate, early ones do not


def test_capped_rejects_nonpositive_caps():
    with pytest.raises(MatrixValidationError):
        CappedTransferSystem([[1.0]], caps=[0.0])
    with pytest.raises(MatrixValidationError):
        CappedTransferSystem([[1.0]], caps=[-1.0])


def test_capped_rejects_cap_count_mismatch():
    with pytest.raises(MatrixValidationError):
        CappedTransferSystem([[1.0, 0.0], [0.0, 1.0]], caps=[1.0])
