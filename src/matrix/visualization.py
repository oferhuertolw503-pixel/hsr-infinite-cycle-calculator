"""Static visualization for transfer matrices (matplotlib, Agg backend).

Three kinds of plots:

  * heatmap of A with rho / regime annotation;
  * circular digraph: nodes on a circle, edges as arrows with width
    proportional to a_ij, node color by Perron frequency;
  * rho vs parameter curve for a MatrixFamily, with the critical line
    rho = 1 drawn (theory sections 3 and 6).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyArrowPatch

from .transfer_matrix import TransferMatrix

# Chinese labels need a CJK font; register the first one found (Windows
# ships Microsoft YaHei / SimHei, macOS PingFang, Linux Noto CJK).
_CJK_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]


def _setup_cjk_font():
    for path in _CJK_FONT_CANDIDATES:
        if Path(path).exists():
            try:
                fm.fontManager.addfont(path)
                name = fm.FontProperties(fname=path).get_name()
                plt.rcParams["font.family"] = [name, "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                return name
            except Exception:
                continue
    return None


_CJK_FONT_NAME = _setup_cjk_font()


def _regime_label(result):
    labels = {"decay": "decay rho<1", "critical": "critical rho=1",
              "growth": "growth rho>1"}
    return labels.get(result["regime"], result["regime"])


def plot_heatmap(model, path, title=None):
    """Heatmap of the transfer matrix with the regime annotation."""
    if not isinstance(model, TransferMatrix):
        model = TransferMatrix(model)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(model.A, cmap="viridis")
    ax.set_xticks(range(model.n))
    ax.set_yticks(range(model.n))
    ax.set_xticklabels(model.node_names, rotation=45, ha="right")
    ax.set_yticklabels(model.node_names)
    for i in range(model.n):
        for j in range(model.n):
            if model.A[i, j] > 0:
                ax.text(j, i, f"{model.A[i, j]:.2f}", ha="center", va="center",
                        color="white" if model.A[i, j] > 0.5 * model.A.max() else "black")
    result = model.classify()
    ax.set_title(title or f"转移矩阵 A  rho={result['rho']:.6g} ({_regime_label(result)})")
    fig.colorbar(im, ax=ax, label="a_ij")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_digraph(model, path, title=None):
    """Circular digraph: edges i -> j with width proportional to a_ij."""
    if not isinstance(model, TransferMatrix):
        model = TransferMatrix(model)
    n = model.n
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pos = {i: (np.cos(a), np.sin(a)) for i, a in enumerate(angles)}

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")

    max_value = float(model.A.max()) or 1.0
    for i in range(n):
        for j in range(n):
            if model.A[i, j] <= model.tol:
                continue
            x0, y0 = pos[i]
            x1, y1 = pos[j]
            arrow = FancyArrowPatch(
                (x0, y0), (x1, y1),
                arrowstyle="->",
                mutation_scale=12 + 10 * model.A[i, j] / max_value,
                linewidth=0.5 + 2.0 * model.A[i, j] / max_value,
                color="tab:blue",
                alpha=0.7,
                connectionstyle="arc3,rad=0.15",
            )
            ax.add_patch(arrow)

    # node colors by Perron frequency
    _, vec, info = model.dominant_pair()
    freqs = np.real(vec) if info["real"] else np.zeros(n)
    colors = plt.cm.plasma((freqs - freqs.min()) / (freqs.max() - freqs.min() + 1e-12))
    for i in range(n):
        x, y = pos[i]
        ax.scatter([x], [y], s=900, color=colors[i], edgecolor="black", zorder=3)
        ax.text(x, y, model.node_names[i], ha="center", va="center", zorder=4,
                fontsize=9, fontweight="bold")

    result = model.classify()
    ax.set_title(title or f"资源转移有向图  rho={result['rho']:.6g} ({_regime_label(result)})")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_family_rho(family, path, title=None):
    """rho vs parameter curve for a MatrixFamily with the rho=1 line."""
    sweep = family.regime_sweep()
    keys = [row["key"] for row in sweep["rows"]]
    rhos = [row["rho"] for row in sweep["rows"]]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(range(len(keys)), rhos, marker="o", color="tab:blue", label="rho(A)")
    ax.axhline(1.0, color="tab:red", linestyle="--", linewidth=1.5, label="rho = 1")
    ax.fill_between(range(len(keys)), 1.0, rhos,
                    where=[r >= 1 for r in rhos], color="tab:green", alpha=0.15)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([f"{family.parameter_name}={k}" for k in keys])
    ax.set_ylabel("谱半径 rho(A)")
    ax.set_title(title or f"{family.name} —— 谱半径随 {family.parameter_name} 变化")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
