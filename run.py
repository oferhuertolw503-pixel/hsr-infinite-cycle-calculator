"""HSR Infinite Cycle Calculator entry point (alias of main.py)."""

import sys

from src.cli import run_cli

if __name__ == "__main__":
    run_cli(sys.argv[1:])
