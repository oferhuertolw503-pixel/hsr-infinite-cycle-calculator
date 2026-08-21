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


# -- real matrices transcribed from the source screenshots (样例/) --------
# Verified against the numbers displayed in the screenshots:
#   * seven-node: eigenvalues N=2..5 = 1.00522/1.01872/1.03174/1.04432
#     (exact to 5 decimals) plus the N=5 eigenvector.  The screenshot
#     DISPLAYS the T -> C_U entry as 1/4, but only 1/2 reproduces all
#     documented values; recorded as 1/2 here.
#   * four-node kill-energy (H/H_U/T/T_U): rho(N=5) = 1.02442 and the
#     eigenvector alpha = (0.304637, 0.832597, 0.202899, 0.415706).
SEVEN_REAL_RHO = {"2": 1.00522, "3": 1.01872, "4": 1.03174, "5": 1.04432}
SEVEN_REAL_EIGVEC_N5 = (0.28, 0.61, 0.19, 0.51, 0.20, 0.27, 0.37)
ALPHA_FOUR = (0.304637, 0.832597, 0.202899, 0.415706)


def seven_node_real(N):
    """Seven-node transfer matrix from the screenshots, N = target count."""
    A = np.zeros((7, 7))
    A[0] = [0, 1 / 4, 0, 0, 1 / 4, 0, 1 / 4]                    # H
    A[1] = [3 / 5, 3 / 5, 0, 1 / 5, 0, 0, 0]                    # H_U
    A[2] = [0, 0, 0, 0, 1 / 2, 0, 1 / 4]                        # C
    A[3] = [3 / 6, 3 / 6, 0.5 / 6, 0, 2 / 6, 0, 0]              # M
    A[4] = [3 / 20, 4 / 20, 5 / 20, 0, 0, 0, 0]                 # C_U
    A[5] = [0, 0, 0, 0, 1 / 2, 0, 1 / 2]                        # T
    A[6] = [(4.5 * N + 5) / 97.5, 6 * N / 97.5, 0, 0,           # T_U
             1.5 * N / 97.5, 30 / 97.5, 5 / 97.5]
    return A


def four_node_kill_real(N):
    """Four-node kill-energy matrix (H/H_U/T/T_U) from the screenshots."""
    A = np.zeros((4, 4))
    A[0] = [0, 1 / 4, 0, 1 / 4]                                 # H
    A[1] = [3 / 4, 3 / 4, 0, 0]                                 # H_U
    A[2] = [0, 0, 0, 1 / 2]                                     # T
    A[3] = [(4.5 * N + 5) / 97.5, 6 * N / 97.5, 30 / 97.5, 5 / 97.5]  # T_U
    return A


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

    # -- seven-node REAL matrix family (from the screenshots) --------------
    seven_real = {
        "name": "七节点实测模型 (截图矩阵, N=2..5)",
        "source": "screenshot",
        "section": "2.1, 5.2, 6",
        "provenance": (
            "实测:截图矩阵逐边转录;特征值 N=2..5 与截图表 1.00522/1.01872/"
            "1.03174/1.04432 全部对齐(5 位小数),N=5 特征向量对齐。"
            "注意:截图 T->C_U 显示为 1/4,但只有 1/2 能复现全部截图数值,"
            "此处按 1/2 记录。"
        ),
        "nodes": SEVEN_NODES,
        "parameter": "N",
        "matrices_by_N": {
            str(N): round_matrix(seven_node_real(N)) for N in (2, 3, 4, 5)
        },
        "rho_target_by_N": dict(SEVEN_REAL_RHO),
        "documented_perron_N5": list(SEVEN_REAL_EIGVEC_N5),
        "tolerance": 1e-5,
        "notes": (
            "截图原矩阵(非重构):H/H_U/C/M/C_U/T/T_U 七节点;N 只进入 T_U 行"
            "((4.5N+5)/97.5、6N/97.5、1.5N/97.5),体现 §5.2 目标数进入矩阵条目。"
            "截图来源:样例/屏幕截图 2026-08-22 002415/002429.png。"
        ),
    }
    (OUT_DIR / "seven_node_real_family.json").write_text(
        json.dumps(seven_real, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # -- four-node kill-energy REAL matrix family (from the screenshots) ---
    # The screenshot only documents rho(N=5) = 1.02442 and alpha; the
    # N=2..4 values are computed from the real matrix and expose the
    # critical target count N=4 (0.99683 -> 1.01088), section 8.
    four_kill_real = {
        "name": "四节点击杀回能实测模型 (姬子+缇宝, N=2..5)",
        "source": "screenshot",
        "section": "4, 6",
        "provenance": (
            "实测:截图矩阵逐边转录;rho(N=5)=1.02442 与特征向量 "
            "alpha=(0.304637, 0.832597, 0.202899, 0.415706) 全部对齐。"
        ),
        "nodes": ["H", "H_U", "T", "T_U"],
        "parameter": "N",
        "matrices_by_N": {
            str(N): round_matrix(four_node_kill_real(N)) for N in (2, 3, 4, 5)
        },
        "rho_target_by_N": {"5": RHO_KILL_ENERGY},
        "documented_perron": list(ALPHA_FOUR),
        "tolerance": 1e-5,
        "notes": (
            "截图原矩阵(非重构):N 只进入 T_U 行;截图只记录 N=5 的 1.02442,"
            "N=2..4 为实测矩阵的计算值:N=3 时 0.99683<1 仍衰减,"
            "N=4 时 1.01088 首次越过 1 —— 真实数据的临界目标数(§8)。"
            "截图来源:样例/屏幕截图 2026-08-22 002449.png。"
        ),
    }
    (OUT_DIR / "four_node_kill_real_family.json").write_text(
        json.dumps(four_kill_real, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # -- full audit workflow demo (theory section 7) ----------------------------
    # Base: seven-node model at N=2 (rho ~ 1.00522, barely above critical).
    # The loop is fragile: a missed kill (drop T_U self-energy) or a half
    # heal flips the regime to decay, while raising N to 5 keeps it robust.
    a2 = matrices["2"]
    a5 = matrices["5"]
    missed_kill = a2.copy()
    missed_kill[6, 6] = 0.0            # 缇宝大招自充能缺失 -> 一次未击杀
    half_heal = a2.copy()
    half_heal[2, 1] *= 0.5             # C -> H_U 治疗/回流减半
    audit_demo = {
        "name": "七节点 N=2 复核审计演示 (§7 全流程)",
        "source": "theory_document",
        "section": "6, 7",
        "nodes": SEVEN_NODES,
        "matrix": round_matrix(a2),
        "documented_rho": RHO_SEVEN_N2,
        "tolerance": 2e-5,
        "edge_meta": {
            "6,3": {
                "mechanism": "缇宝大招 -> 军功 M(随目标数 N 缩放)",
                "cap": None,
                "depends_on_N": True,
            },
            "6,6": {
                "mechanism": "缇宝大招自充能(击杀回能)",
                "cap": None,
                "depends_on_N": True,
            },
        },
        "sequence": [
            {"name": "H", "energy_gain": 20.0, "av_cost": 10.0},
            {"name": "C", "energy_gain": 20.0, "av_cost": 10.0},
            {"name": "M", "energy_gain": 15.0, "av_cost": 10.0},
            {"name": "T", "energy_gain": 20.0, "av_cost": 10.0},
            {"name": "T_U", "energy_gain": 5.0, "av_cost": 0.0,
             "no_advance": True},
        ],
        "enemy_av0": 10000.0,
        "perturbations": [
            {
                "label": "target_count_N5",
                "matrix": round_matrix(a5),
                "note": "目标数提升到 5(§5.2):矩阵条目随 N 改变",
            },
            {
                "label": "missed_kill_TU_self",
                "matrix": round_matrix(missed_kill),
                "note": "一次未击杀:缇宝大招自充能缺失",
            },
            {
                "label": "half_heal_C_to_HU",
                "matrix": round_matrix(half_heal),
                "note": "治疗缺失:C -> H_U 回流减半",
            },
        ],
        "mode_note": "该 A 适用于特定版本/模式/敌方配置,不可外推为通用结论。",
        "notes": (
            "§7 全流程审计示例:基矩阵为七节点 N=2(rho≈1.00522,略超临界),"
            "扰动测试显示单边缺失即可翻转 regime(断轴是资源问题);"
            "目标数提升到 N=5 后 rho≈1.04432,闭环更稳健。"
            "条目为重构值,非截图原值。"
        ),
    }
    (OUT_DIR / "audit_workflow_demo.json").write_text(
        json.dumps(audit_demo, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("wrote:", sorted(str(p) for p in OUT_DIR.glob("*.json")))


if __name__ == "__main__":
    main()
