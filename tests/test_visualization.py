"""Visualization smoke tests: figures must be produced without error.

(tmp_path points at the system temp dir, which the file sandbox denies;
we write into the workspace instead and clean up afterwards.)
"""

import shutil
from pathlib import Path

from src.data_loader.matrix_loader import load_family, load_transfer_matrix
from src.matrix.transfer_matrix import TransferMatrix
from src.matrix.visualization import plot_digraph, plot_family_rho, plot_heatmap

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"
FIG_DIR = Path(__file__).resolve().parent / ".tmp_figures"


def _setup_fig_dir():
    FIG_DIR.mkdir(exist_ok=True)
    return FIG_DIR


def _teardown_fig_dir():
    shutil.rmtree(FIG_DIR, ignore_errors=True)


def test_plot_heatmap():
    _setup_fig_dir()
    try:
        model = load_transfer_matrix(EXAMPLES / "four_node_model_N5.json")
        out = FIG_DIR / "heatmap.png"
        plot_heatmap(model, out)
        assert out.exists() and out.stat().st_size > 0
    finally:
        _teardown_fig_dir()


def test_plot_digraph():
    _setup_fig_dir()
    try:
        model = TransferMatrix([[0.0, 1.0], [1.2, 0.3]],
                               node_names=["basic", "kill"])
        out = FIG_DIR / "digraph.png"
        plot_digraph(model, out)
        assert out.exists() and out.stat().st_size > 0
    finally:
        _teardown_fig_dir()


def test_plot_family_rho():
    _setup_fig_dir()
    try:
        family = load_family(EXAMPLES / "seven_node_family.json")
        out = FIG_DIR / "family_rho.png"
        plot_family_rho(family, out)
        assert out.exists() and out.stat().st_size > 0
    finally:
        _teardown_fig_dir()
