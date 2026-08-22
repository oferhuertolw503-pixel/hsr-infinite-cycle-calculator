"""Regenerate documentation figures from the checked-in V1 examples."""

from pathlib import Path

from src.data_loader.matrix_loader import load_family, load_transfer_matrix
from src.matrix.visualization import plot_digraph, plot_family_rho, plot_heatmap


ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples" / "theory_document"
FIGURES = ROOT / "docs" / "figures"


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    four_node = load_transfer_matrix(EXAMPLES / "four_node_model_N5.json")
    seven_node = load_family(EXAMPLES / "seven_node_real_family.json")

    plot_heatmap(four_node, FIGURES / "four_node_heatmap.png")
    plot_digraph(four_node, FIGURES / "four_node_digraph.png")
    plot_family_rho(seven_node, FIGURES / "seven_node_family_rho.png")

    print("wrote:", sorted(str(path) for path in FIGURES.glob("*.png")))


if __name__ == "__main__":
    main()
