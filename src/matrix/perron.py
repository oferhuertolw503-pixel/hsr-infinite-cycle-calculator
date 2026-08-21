"""Perron-Frobenius analysis for non-negative transfer matrices."""

import numpy as np

from .transfer_matrix import TransferMatrix


def perron_vector(matrix):
    """Return dominant eigenvalue and normalized dominant eigenvector.

    Backward-compatible 2-tuple; the vector is normalized to sum to 1
    when its sum is non-zero (theory document section 4).
    """
    model = TransferMatrix(np.asarray(matrix, dtype=float))
    value, vector, _ = model.dominant_pair()
    return value, vector


def perron_analysis(matrix, node_names=None, rho_tol=1e-9):
    """Rich Perron analysis with irreducibility and positivity flags."""
    model = TransferMatrix(matrix, node_names=node_names, tol=rho_tol)
    value, vector, info = model.dominant_pair()
    rho = model.spectral_radius()

    theorem_note = (
        "Perron-Frobenius 定理要求 A 不可约,才保证谱半径对应一个"
        "严格正特征向量;可约矩阵需按强连通分量逐块分析。"
    )
    return {
        "rho": rho,
        "eigenvalue": value,
        "vector": vector,
        "irreducible": model.is_irreducible(),
        "dominant_real": info["real"],
        "positive": info["positive"],
        "components": model.component_summary(),
        "theorem_note": theorem_note,
    }
