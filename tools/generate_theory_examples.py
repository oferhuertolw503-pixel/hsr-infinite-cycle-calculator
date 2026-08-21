"""Regenerate the theory-document example matrices.

The theory document (section 6) records spectral radii for three model
families but not the raw matrices.  These generators construct
demonstrative matrices whose rho matches the documented values so the
tooling can reproduce the section-6 numbers:

  * four_node_model_N5.json     rho = 0.88353   (first parameter set, N=5)
  * four_node_kill_energy.json  rho = 1.02442   (adjusted + kill energy)
  * seven_node_family.json      rho(N=2..5) = 1.00522 .. 1.04432

The matrix ENTRIES are demonstrative values, not the entries from the
original screenshots.  Run from the repository root:

    python tools/generate_theory_examples.py
"""

import json
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent / "examples" / "theory_document"

# -- documented values (theory document section 6) ------------------------
RHO_N5 = 0.88353          # first parameter set, N=5
RHO_KILL_ENERGY = 1.02442  # adjusted transfers + kill energy
RHO_SEVEN_N2 = 1.00522     # seven-node model, N=2
RHO_SEVEN_N5 = 1.04432     # seven-node model, N=5
PERRON_FOUR = np.array([0.304637, 0.832597, 0.202899, 0.415706])

SEVEN_NODES = ["H", "H_U", "C", "M", "C_U", "T", "T_U"]


def spectral_radius(matrix):
    return float(np.max(np.abs(np.linalg.eigvals(matrix))))


def rank_one_matrix(rho, vector):
    """A = rho * outer(v, v) / dot(v, v): irreducible rank-1 matrix whose
    Perron root is rho and whose Perron vector is v."""
    v = np.asarray(vector, dtype=float)
    return rho * np.outer(v, v) / float(np.dot(v, v))


def build_base_seven(rng_seed=20260810):
    """Strongly connected 7x7 base matrix with rho exactly RHO_SEVEN_N2."""
    rng = np.random.default_rng(rng_seed)
    base = rng.uniform(0.02, 0.45, size=(7, 7))
    for i in range(7):  # Hamiltonian cycle keeps the digraph strongly connected
        base[i, (i + 1) % 7] = max(base[i, (i + 1) % 7], 0.06)
    return (RHO_SEVEN_N2 / spectral_radius(base)) * base


def find_edge_scale(base, edge_matrix, target, lo=0.0, hi=2048.0, iters=80):
    """Binary search m so rho(base + m * edge) == target.

    Perron root is monotone in the entries, and edge has a self-loop, so
    rho(base + m*edge) -> infinity as m -> infinity: bisection converges.
    """
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        rho = spectral_radius(base + mid * edge_matrix)
        if rho < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def round_matrix(matrix, decimals=8):
    return [[round(float(x), decimals) for x in row] for row in matrix]


def build_seven_family():
    """N enters the T_U-related transfers (theory 5.2): more targets -> more
    军功 (M) and more self energy for 缇宝大招.  N=2 matches the documented
    base; N=3,4 use linearly interpolated targets between the documented
    endpoints; N=5 matches the documented endpoint."""
    base = build_base_seven()
    s = np.zeros((7, 7))
    s[6, 3] = 1.0   # T_U -> M   (军功)
    s[6, 6] = 1.0   # T_U -> T_U (self energy)
    targets = {
        "2": RHO_SEVEN_N2,
        "3": RHO_SEVEN_N2 + (RHO_SEVEN_N5 - RHO_SEVEN_N2) / 3.0,
        "4": RHO_SEVEN_N2 + 2.0 * (RHO_SEVEN_N5 - RHO_SEVEN_N2) / 3.0,
        "5": RHO_SEVEN_N5,
    }
    matrices = {"2": base}
    scales = {"2": 0.0}
    for key, target in targets.items():
        if key == "2":
            continue
        m = find_edge_scale(base, s, target)
        matrices[key] = base + m * s
        scales[key] = m
    return matrices, targets, scales


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # -- four-node model, N=5 ------------------------------------------------
    a_n5 = rank_one_matrix(RHO_N5, PERRON_FOUR)
    four_n5 = {
        "name": "四节点简化模型 (第一组参数, N=5)",
        "source": "theory_document",
        "section": "4, 6",
        "nodes": ["A", "B", "C", "D"],
        "matrix": round_matrix(a_n5),
        "documented_rho": RHO_N5,
        "documented_perron": [float(x) for x in PERRON_FOUR],
        "tolerance": 1e-5,
        "notes": (
            "演示矩阵,谱半径与文档 §6 一致(0.88353 < 1 => 线性衰减)。"
            "Perron 向量与文档 §4 的 alpha 成比例。条目为重构值,非截图原值。"
        ),
    }
    (OUT_DIR / "four_node_model_N5.json").write_text(
        json.dumps(four_n5, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # -- four-node model with kill energy --------------------------------------
    a_kill = rank_one_matrix(RHO_KILL_ENERGY, PERRON_FOUR)
    four_kill = {
        "name": "四节点简化模型 (调整转移并加入击杀回能)",
        "source": "theory_document",
        "section": "6",
        "nodes": ["A", "B", "C", "D"],
        "matrix": round_matrix(a_kill),
        "documented_rho": RHO_KILL_ENERGY,
        "tolerance": 1e-5,
        "notes": (
            "演示矩阵,谱半径与文档 §6 一致(1.02442 > 1 => 线性增长方向,"
            "仍需验证击杀持续、目标数保持、上限与行动顺序)。"
            "条目为重构值,非截图原值。"
        ),
    }
    (OUT_DIR / "four_node_kill_energy.json").write_text(
        json.dumps(four_kill, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # -- seven-node family -------------------------------------------------------
    matrices, targets, scales = build_seven_family()
    seven = {
        "name": "七节点模型 (H, H_U, C, M, C_U, T, T_U)",
        "source": "theory_document",
        "section": "2.1, 5.2, 6",
        "nodes": SEVEN_NODES,
        "parameter": "N",
        "matrices_by_N": {
            key: round_matrix(mat) for key, mat in sorted(matrices.items())
        },
        "rho_target_by_N": {key: float(t) for key, t in targets.items()},
        "transfer_scale_by_N": {key: float(s) for key, s in scales.items()},
        "tolerance": 2e-5,
        "notes": (
            "N 进入缇宝大招相关转移(T_U->M 军功、T_U 自充能),体现 §5.2"
            " 'A 随目标数 N 改变'。N=2 与 N=5 的谱半径为文档 §6 记录值,"
            "N=3、4 为端点间线性插值的演示值。条目为重构值,非截图原值。"
        ),
    }
    (OUT_DIR / "seven_node_family.json").write_text(
        json.dumps(seven, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("wrote:", sorted(str(p) for p in OUT_DIR.glob("*.json")))


if __name__ == "__main__":
    main()
