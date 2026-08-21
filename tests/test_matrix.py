import numpy as np

from src.matrix.transfer_matrix import TransferMatrix
from src.matrix.perron import perron_vector


def test_spectral_radius():
    model = TransferMatrix([[0, 1], [0.5, 0]])
    assert np.isclose(model.spectral_radius(), np.sqrt(0.5))


def test_perron_vector():
    value, vector = perron_vector([[1, 0], [0, 2]])
    assert value == 2
    assert np.isclose(np.sum(vector), 1)
