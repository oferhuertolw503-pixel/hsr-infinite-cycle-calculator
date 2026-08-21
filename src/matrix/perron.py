"""Perron-Frobenius analysis for non-negative transfer matrices."""

import numpy as np


def perron_vector(matrix):
    """Return dominant eigenvalue and normalized dominant eigenvector."""
    A = np.asarray(matrix, dtype=float)
    values, vectors = np.linalg.eig(A)
    index = np.argmax(np.abs(values))

    value = float(np.real(values[index]))
    vector = np.real(vectors[:, index])

    if np.all(vector < 0):
        vector = -vector

    norm = np.sum(vector)
    if norm != 0:
        vector = vector / norm

    return value, vector
