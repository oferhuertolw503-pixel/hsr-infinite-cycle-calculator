"""Beginner-friendly V1 acceptance check for the four case screenshots."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .data_loader.matrix_loader import load_family, load_transfer_matrix


ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "docs" / "screenshots"
EXAMPLES = ROOT / "examples" / "theory_document"


def _image_ok(name):
    path = SCREENSHOTS / name
    return path.is_file() and path.stat().st_size > 100_000


def _four_node_matrix(target_count, ultimate_self_loop):
    n = target_count
    return np.array([
        [0, 1 / 4, 0, 1 / 4],
        [ultimate_self_loop, ultimate_self_loop, 0, 0],
        [0, 0, 0, 1 / 2],
        [(4.5 * n + 5) / 97.5, 6 * n / 97.5, 30 / 97.5, 5 / 97.5],
    ])


def _seven_node_matrix(target_count):
    n = target_count
    return np.array([
        [0, 1 / 4, 0, 0, 1 / 4, 0, 1 / 4],
        [3 / 5, 3 / 5, 0, 1 / 5, 0, 0, 0],
        [0, 0, 0, 0, 1 / 2, 0, 1 / 4],
        [3 / 6, 3 / 6, 0.5 / 6, 0, 2 / 6, 0, 0],
        [3 / 20, 4 / 20, 5 / 20, 0, 0, 0, 0],
        [0, 0, 0, 0, 1 / 4, 0, 1 / 2],
        [(4.5 * n + 5) / 97.5, 6 * n / 97.5, 0, 0,
         1.5 * n / 97.5, 30 / 97.5, 5 / 97.5],
    ])


def verify():
    """Return one explicit verification row per source screenshot."""
    decay = load_transfer_matrix(EXAMPLES / "four_node_model_N5.json")
    kill = load_family(EXAMPLES / "four_node_kill_real_family.json")
    displayed = load_family(EXAMPLES / "seven_node_real_family.json")
    calibrated = load_family(
        EXAMPLES / "seven_node_table_calibrated_family.json"
    )

    decay_checks = {
        "image": _image_ok("case_4node_decay.png"),
        "matrix": np.allclose(decay.A, _four_node_matrix(5, 3 / 5)),
        "rho": np.isclose(decay.spectral_radius(), 0.88353, atol=1e-5),
    }

    kill_model = kill.models["5"]
    _, kill_vector, _ = kill_model.dominant_pair()
    reported_vector = np.array([0.304637, 0.832597, 0.202899, 0.415706])
    kill_vector /= kill_vector.max()
    reported_vector /= reported_vector.max()
    kill_checks = {
        "image": _image_ok("case_4node_kill.png"),
        "matrix": np.allclose(kill_model.A, _four_node_matrix(5, 3 / 4)),
        "rho": np.isclose(kill_model.spectral_radius(), 1.02442, atol=1e-5),
        "perron": np.allclose(kill_vector, reported_vector, rtol=1e-3),
    }

    definition_model = displayed.models["5"]
    definition_checks = {
        "image": _image_ok("case_matrix_definition.png"),
        "matrix": np.allclose(definition_model.A, _seven_node_matrix(5)),
        "displayed_cell": np.isclose(definition_model.A[5, 4], 1 / 4),
    }

    reported_rhos = {
        "2": 1.00522,
        "3": 1.01872,
        "4": 1.03174,
        "5": 1.04432,
    }
    table_checks = {
        "image": _image_ok("case_7node_matrix.png"),
        "reported_rhos": all(
            np.isclose(calibrated.models[key].spectral_radius(), rho, atol=1e-5)
            for key, rho in reported_rhos.items()
        ),
        "calibrated_cell": np.isclose(calibrated.models["5"].A[5, 4], 1 / 2),
        "source_inconsistency_exposed": not np.isclose(
            displayed.models["5"].spectral_radius(),
            reported_rhos["5"],
            atol=1e-5,
        ),
    }

    rows = [
        {
            "image": "case_4node_decay.png",
            "checks": decay_checks,
            "note": "显示矩阵直接复现 rho(N=5)=0.88353。",
        },
        {
            "image": "case_4node_kill.png",
            "checks": kill_checks,
            "note": "显示矩阵直接复现 rho(N=5)=1.02442 与特征向量。",
        },
        {
            "image": "case_matrix_definition.png",
            "checks": definition_checks,
            "note": "七节点矩阵逐格转录，保留图示 T→C_U=1/4。",
        },
        {
            "image": "case_7node_matrix.png",
            "checks": table_checks,
            "note": (
                "图中结果表需 T→C_U=1/2 才能复现；与显示的 1/4 不一致，"
                "V1 将校准版单独保存。"
            ),
        },
    ]
    for row in rows:
        row["verified"] = all(bool(value) for value in row["checks"].values())
    return {
        "version": "v1",
        "rows": rows,
        "all_verified": all(row["verified"] for row in rows),
    }


def main():
    result = verify()
    print("V1 四图验收")
    print("=" * 60)
    for row in result["rows"]:
        status = "PASS" if row["verified"] else "FAIL"
        print(f"[{status}] {row['image']}")
        print(f"       {row['note']}")
    print("=" * 60)
    print("结论:", "V1 验收通过" if result["all_verified"] else "V1 验收失败")
    return result


if __name__ == "__main__":
    main()
