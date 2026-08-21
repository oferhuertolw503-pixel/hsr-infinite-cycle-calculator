import numpy as np
import pytest

from src.matrix.irreducibility import is_irreducible
from src.matrix.perron import perron_analysis, perron_vector
from src.matrix.transfer_matrix import MatrixValidationError, TransferMatrix


# -- spectral radius -----------------------------------------------------
def test_spectral_radius():
    model = TransferMatrix([[0, 1], [0.5, 0]])
    assert np.isclose(model.spectral_radius(), np.sqrt(0.5))


def test_spectral_radius_permutation_cycle():
    # 3-cycle: eigenvalues are the cube roots of unity, rho = 1
    model = TransferMatrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
    assert np.isclose(model.spectral_radius(), 1.0)


# -- validation ----------------------------------------------------------
def test_rejects_non_square():
    with pytest.raises(MatrixValidationError):
        TransferMatrix([[1, 2]])


def test_rejects_negative_entries():
    with pytest.raises(MatrixValidationError):
        TransferMatrix([[0, -1], [1, 0]])


def test_rejects_nan():
    with pytest.raises(MatrixValidationError):
        TransferMatrix([[0, float("nan")], [1, 0]])


def test_rejects_node_name_count_mismatch():
    with pytest.raises(MatrixValidationError):
        TransferMatrix([[1]], node_names=["a", "b"])


# -- irreducibility ------------------------------------------------------
def test_irreducible_two_cycle():
    assert is_irreducible(np.array([[0, 1], [1, 0]]))


def test_reducible_diagonal():
    assert not is_irreducible(np.array([[1, 0], [0, 1]]))


def test_reducible_chain():
    assert not is_irreducible(np.array([[0, 1], [0, 0]]))


# -- perron vector -------------------------------------------------------
def test_dominant_pair_eigenvalue_sign_stable_under_vector_flip(monkeypatch):
    # A(-v) = lambda * (-v): sign-flipping the returned eigenvector must not
    # flip the reported eigenvalue (regression: both used to be negated).
    A = np.array([[1.0, 0.0], [0.0, 2.0]])

    def fake_eig(matrix):
        # dominant eigenvalue 2 with a negative-peaked eigenvector (0, -1)
        return np.array([1.0, 2.0]), np.array([[1.0, 0.0], [0.0, -1.0]])

    monkeypatch.setattr(np.linalg, "eig", fake_eig)
    model = TransferMatrix(A)
    value, vec, info = model.dominant_pair()
    assert value == 2.0
    assert np.allclose(A @ vec, value * vec)
    assert info["positive"]


def test_perron_vector_normalized():
    value, vector = perron_vector([[1, 0], [0, 2]])
    assert value == 2
    assert np.isclose(np.sum(vector), 1)


def test_perron_vector_of_stochastic_matrix():
    value, vector = perron_vector([[0.5, 0.5], [0.5, 0.5]])
    assert np.isclose(value, 1.0)
    assert np.allclose(vector, [0.5, 0.5])


def test_perron_analysis_flags_reducible():
    info = perron_analysis([[1, 0], [0, 2]])
    assert not info["irreducible"]
    assert info["positive"]


# -- classification ------------------------------------------------------
def test_classify_decay():
    model = TransferMatrix([[0, 0.5], [0.5, 0]])
    result = model.classify()
    assert result["regime"] == "decay"
    assert result["rho"] < 1
    assert "衰减" in result["conclusion"]


def test_classify_critical_irreducible():
    model = TransferMatrix([[0.5, 0.5], [0.5, 0.5]])
    result = model.classify()
    assert result["regime"] == "critical"
    assert result["irreducible"]
    assert result["dominant_positive"]


def test_classify_growth():
    model = TransferMatrix([[0, 1.5], [1.5, 0]])
    result = model.classify()
    assert result["regime"] == "growth"
    assert result["rho"] > 1
    # growth must not be presented as a practical infinite loop
    assert "不能单独推出实战无限循环" in result["conclusion"]
    assert any("上限" in c for c in result["caveats"])


def test_classify_complex_dominant():
    model = TransferMatrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
    result = model.classify()
    assert result["regime"] == "critical"
    assert not result["dominant_real"]
    assert result["irreducible"]


# -- time scales ---------------------------------------------------------
def test_vector_decay_horizon():
    model = TransferMatrix([[0.5, 0], [0, 0.5]])
    assert model.vector_decay_horizon([1, 1], epsilon=1e-6) == 20


def test_growth_doubling_time():
    model = TransferMatrix([[2]])
    assert np.isclose(model.growth_doubling_time(), 1.0)


def test_matrix_decay_horizon():
    model = TransferMatrix([[0.5]])
    assert model.matrix_decay_horizon(epsilon=1e-6) == 20


def test_decay_horizon_undefined_for_growth():
    model = TransferMatrix([[1.5]])
    with pytest.raises(ValueError):
        model.matrix_decay_horizon()


# -- iteration -----------------------------------------------------------
def test_iterate_row_convention():
    model = TransferMatrix([[0, 1], [1, 0]])
    trajectory = model.iterate([1, 0], steps=3)
    assert np.allclose(trajectory[0], [1, 0])
    assert np.allclose(trajectory[1], [0, 1])
    assert np.allclose(trajectory[2], [1, 0])
    assert np.allclose(trajectory[3], [0, 1])


# -- edge sensitivity ----------------------------------------------------
def test_edge_sensitivity_positive_for_growth_edge():
    model = TransferMatrix([[0, 1.5], [1.5, 0]])
    sensitivity = model.edge_sensitivity()
    assert all(row["d_rho"] > 0 for row in sensitivity)


def test_edge_sensitivity_sorted():
    model = TransferMatrix([[0, 1.5], [0.1, 0]])
    sensitivity = model.edge_sensitivity()
    magnitudes = [abs(row["d_rho"]) for row in sensitivity]
    assert magnitudes == sorted(magnitudes, reverse=True)
