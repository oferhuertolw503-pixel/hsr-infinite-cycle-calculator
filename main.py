"""HSR Infinite Cycle Calculator - command line entry.

Usage:
    python main.py examples/himeko_nova_cycle_demo.json
    python main.py examples/theory_document/four_node_model_N5.json
    python main.py examples/theory_document/seven_node_family.json --family
"""

from src.cli import run_cli

if __name__ == "__main__":
    run_cli()
