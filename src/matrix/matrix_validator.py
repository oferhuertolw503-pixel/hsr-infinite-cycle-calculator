"""Validation utilities for resource transfer matrices.

A valid transfer matrix must be square, finite, and non-negative
(theory document assumptions A1: a_ij >= 0).
"""

import numpy as np


def is_non_negative(matrix):
    A = np.asarray(matrix, dtype=float)
    return bool(np.all(A >= 0))


def is_square(matrix):
    A = np.asarray(matrix)
    return (
        len(A.shape) == 2
        and A.shape[0] == A.shape[1]
        and A.shape[0] > 0
    )


def is_finite(matrix):
    A = np.asarray(matrix, dtype=float)
    return bool(np.all(np.isfinite(A)))


def validate_matrix(matrix):
    """Return a dict with boolean checks and a human-readable issue list."""
    A = np.asarray(matrix)
    issues = []

    square = is_square(A)
    if not square:
        issues.append(
            f"matrix must be a non-empty square 2-D array, got shape {A.shape}"
        )

    finite = is_finite(A)
    if not finite:
        issues.append("matrix contains NaN or infinite entries")

    non_negative = is_non_negative(A)
    if not non_negative:
        issues.append("matrix entries must be non-negative (assumption A1)")

    return {
        "square": square,
        "non_negative": non_negative,
        "finite": finite,
        "valid": square and finite and non_negative,
        "issues": issues,
    }
