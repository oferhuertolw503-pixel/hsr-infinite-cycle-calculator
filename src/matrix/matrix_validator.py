"""Validation utilities for resource transfer matrices."""

import numpy as np


def is_non_negative(matrix):
    A = np.asarray(matrix, dtype=float)
    return bool(np.all(A >= 0))


def is_square(matrix):
    A = np.asarray(matrix)
    return len(A.shape) == 2 and A.shape[0] == A.shape[1]


def validate_matrix(matrix):
    return {
        "square": is_square(matrix),
        "non_negative": is_non_negative(matrix),
    }
