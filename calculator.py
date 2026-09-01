"""行向量资源转移矩阵计算器，内含四个原图复算案例。

统一口径：``x_(t+1) = x_t @ A``，其中 ``A[i][j]`` 表示事件 i 产生事件 j。
"""

import argparse
import json

import numpy as np
from numpy.typing import ArrayLike


TOLERANCE = 1e-9
CASE_TOLERANCE = 1e-5


def calculate(matrix: ArrayLike) -> tuple[float, list[float]]:
    """返回谱半径和归一化左主导特征向量。"""
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[0] != array.shape[1]:
        raise ValueError("矩阵必须是非空方阵")
    if not np.all(np.isfinite(array)):
        raise ValueError("矩阵只能包含有限数")
    if np.any(array < 0):
        raise ValueError("矩阵不能包含负数")

    # p @ A = rho * p 等价于 A.T @ p = rho * p。
    eigenvalues, eigenvectors = np.linalg.eig(array.T)
    radius = float(np.max(np.abs(eigenvalues)))
    index = int(np.argmin(np.abs(eigenvalues - radius)))
    vector = np.real_if_close(eigenvectors[:, index])
    if np.iscomplexobj(vector):
        raise ValueError("未找到实数主导比例")

    vector = np.asarray(vector, dtype=float)
    if vector[np.argmax(np.abs(vector))] < 0:
        vector = -vector
    total = float(np.sum(vector))
    if abs(total) > TOLERANCE:
        vector /= total
    return radius, vector.tolist()


def four_node(targets: int, kill_energy: bool = False) -> list[list[float]]:
    """四节点矩阵，节点顺序为 H/H_U/T/T_U。"""
    ultimate = 3 / 4 if kill_energy else 3 / 5
    return [
        [0, 1 / 4, 0, 1 / 4],
        [ultimate, ultimate, 0, 0],
        [0, 0, 0, 1 / 2],
        [(4.5 * targets + 5) / 97.5, 6 * targets / 97.5, 30 / 97.5, 5 / 97.5],
    ]


def seven_node(targets: int, calibrated: bool = False) -> list[list[float]]:
    """七节点矩阵，节点顺序为 H/H_U/C/M/C_U/T/T_U。"""
    # 原图显示 T→C_U=1/4；结果表需要 1/2。
    t_to_c_ultimate = 1 / 2 if calibrated else 1 / 4
    return [
        [0, 1 / 4, 0, 0, 1 / 4, 0, 1 / 4],
        [3 / 5, 3 / 5, 0, 1 / 5, 0, 0, 0],
        [0, 0, 0, 0, 1 / 2, 0, 1 / 4],
        [3 / 6, 3 / 6, 0.5 / 6, 0, 2 / 6, 0, 0],
        [3 / 20, 4 / 20, 5 / 20, 0, 0, 0, 0],
        [0, 0, 0, 0, t_to_c_ultimate, 0, 1 / 2],
        [
            (4.5 * targets + 5) / 97.5,
            6 * targets / 97.5,
            0,
            0,
            1.5 * targets / 97.5,
            30 / 97.5,
            5 / 97.5,
        ],
    ]


def run_cases() -> bool:
    """复算四张原图；全部通过时返回 True。"""
    close = lambda matrix, expected: (  # noqa: E731 - 保留项目的 lambda 风格
        abs(calculate(matrix)[0] - expected) <= CASE_TOLERANCE
    )
    displayed = seven_node(5)
    reported = {2: 1.00522, 3: 1.01872, 4: 1.03174, 5: 1.04432}
    checks = [
        ("四节点：无击杀回能", close(four_node(5), 0.88353)),
        ("四节点：有击杀回能", close(four_node(5, True), 1.02442)),
        (
            "七节点：显示矩阵",
            displayed[5][4] == 1 / 4 and close(displayed, 1.0408690555),
        ),
        (
            "七节点：结果表",
            all(close(seven_node(n, True), rho) for n, rho in reported.items())
            and not close(displayed, reported[5]),
        ),
    ]
    for name, passed in checks:
        print(f"[{'通过' if passed else '失败'}] {name}")
    return all(passed for _, passed in checks)


def main() -> int:
    parser = argparse.ArgumentParser(description="资源转移矩阵计算器")
    parser.add_argument(
        "matrix",
        nargs="?",
        help='JSON 矩阵，例如 "[[0.5,0.2],[0.1,0.6]]"',
    )
    parser.add_argument("--cases", action="store_true", help="复算四个原图案例")
    args = parser.parse_args()

    if args.cases:
        if args.matrix:
            parser.error("矩阵和 --cases 不能同时使用")
        return 0 if run_cases() else 1
    if not args.matrix:
        parser.print_help()
        return 0

    try:
        radius, vector = calculate(json.loads(args.matrix))
    except (json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))

    if radius < 1 - TOLERANCE:
        state = "衰减"
    elif radius > 1 + TOLERANCE:
        state = "增长"
    else:
        state = "临界"

    print(f"谱半径 = {radius:.8f}")
    print(f"状态 = {state}")
    print(f"主导比例 = {vector}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
