"""Small calculator for non-negative resource-transfer matrices."""

from __future__ import annotations

import numpy as np


def _validated_matrix(matrix) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[0] != array.shape[1]:
        raise ValueError("matrix 必须是非空方阵")
    if not np.all(np.isfinite(array)):
        raise ValueError("matrix 不能包含 NaN 或无穷大")
    if np.any(array < 0):
        raise ValueError("资源转移矩阵不能包含负数")
    return array


def calculate(matrix, tolerance: float = 1e-9) -> dict:
    """Calculate spectral radius, regime and normalized dominant vector."""
    array = _validated_matrix(matrix)
    eigenvalues, eigenvectors = np.linalg.eig(array)
    rho = float(np.max(np.abs(eigenvalues)))

    # 非负矩阵的谱半径本身是实特征值，选择最接近 rho 的特征对。
    index = int(np.argmin(np.abs(eigenvalues - rho)))
    vector = np.real_if_close(eigenvectors[:, index])
    if np.iscomplexobj(vector):
        raise ValueError("未找到实数主导特征向量")
    vector = np.asarray(vector, dtype=float)
    if vector[np.argmax(np.abs(vector))] < 0:
        vector = -vector
    vector[np.abs(vector) < tolerance] = 0.0
    total = float(np.sum(vector))
    if abs(total) > tolerance:
        vector /= total

    if rho < 1 - tolerance:
        regime = "衰减（rho < 1）"
    elif rho > 1 + tolerance:
        regime = "增长方向（rho > 1，不等于实战永动）"
    else:
        regime = "临界（rho ≈ 1）"

    return {
        "rho": rho,
        "regime": regime,
        "dominant_vector": vector.tolist(),
    }
