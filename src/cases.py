"""The four validation cases transcribed from docs/screenshots."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .calculator import calculate


ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "docs" / "screenshots"


def four_node_matrix(target_count: int, kill_energy: bool) -> list[list[float]]:
    """H/H_U/T/T_U matrix; kill energy changes H_U from 3/5 to 3/4."""
    n = target_count
    h_ultimate = 3 / 4 if kill_energy else 3 / 5
    return [
        [0, 1 / 4, 0, 1 / 4],
        [h_ultimate, h_ultimate, 0, 0],
        [0, 0, 0, 1 / 2],
        [(4.5 * n + 5) / 97.5, 6 * n / 97.5, 30 / 97.5, 5 / 97.5],
    ]


def seven_node_matrix(target_count: int, calibrated: bool) -> list[list[float]]:
    """H/H_U/C/M/C_U/T/T_U matrix from the seven-node screenshots."""
    n = target_count
    t_to_c_ultimate = 1 / 2 if calibrated else 1 / 4
    return [
        [0, 1 / 4, 0, 0, 1 / 4, 0, 1 / 4],
        [3 / 5, 3 / 5, 0, 1 / 5, 0, 0, 0],
        [0, 0, 0, 0, 1 / 2, 0, 1 / 4],
        [3 / 6, 3 / 6, 0.5 / 6, 0, 2 / 6, 0, 0],
        [3 / 20, 4 / 20, 5 / 20, 0, 0, 0, 0],
        [0, 0, 0, 0, t_to_c_ultimate, 0, 1 / 2],
        [
            (4.5 * n + 5) / 97.5,
            6 * n / 97.5,
            0,
            0,
            1.5 * n / 97.5,
            30 / 97.5,
            5 / 97.5,
        ],
    ]


def _rho_matches(matrix, expected, tolerance=1e-5) -> bool:
    return bool(np.isclose(calculate(matrix)["rho"], expected, atol=tolerance))


def verify_cases() -> list[dict]:
    """Run one transparent numerical check for each source screenshot."""
    decay = four_node_matrix(5, kill_energy=False)
    kill = four_node_matrix(5, kill_energy=True)
    kill_vector = calculate(kill)["dominant_vector"]
    expected_vector = np.array([0.304637, 0.832597, 0.202899, 0.415706])
    expected_vector /= expected_vector.sum()

    displayed = seven_node_matrix(5, calibrated=False)
    reported_rhos = {2: 1.00522, 3: 1.01872, 4: 1.03174, 5: 1.04432}

    cases = [
        {
            "image": "case_4node_decay.png",
            "passed": _rho_matches(decay, 0.88353),
            "detail": "四节点无击杀回能：rho(N=5)=0.88353",
        },
        {
            "image": "case_4node_kill.png",
            "passed": _rho_matches(kill, 1.02442)
            and bool(np.allclose(kill_vector, expected_vector, rtol=1e-3)),
            "detail": "四节点击杀回能：rho(N=5)=1.02442，特征向量一致",
        },
        {
            "image": "case_matrix_definition.png",
            "passed": bool(np.isclose(displayed[5][4], 1 / 4))
            and _rho_matches(displayed, 1.0408690555),
            "detail": "七节点逐格转录：T→C_U=1/4",
        },
        {
            "image": "case_7node_matrix.png",
            "passed": all(
                _rho_matches(seven_node_matrix(n, calibrated=True), rho)
                for n, rho in reported_rhos.items()
            )
            and not _rho_matches(displayed, reported_rhos[5]),
            "detail": "结果表需 T→C_U=1/2；与图示 1/4 不一致",
        },
    ]

    for case in cases:
        case["passed"] = case["passed"] and (SCREENSHOTS / case["image"]).is_file()
    return cases


def print_verification(results: list[dict]) -> None:
    print("四图验证")
    print("=" * 60)
    for item in results:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"[{status}] {item['image']}")
        print(f"       {item['detail']}")
    print("=" * 60)
    print("结论：", "全部通过" if all(item["passed"] for item in results) else "验证失败")
