"""Load transfer-matrix examples from JSON files.

Two formats are supported:

  * single matrix:  {"nodes": [...], "matrix": [[...]], "documented_rho": ...}
  * N-parameterized family (theory section 5.2):
    {"nodes": [...], "parameter": "N",
     "matrices_by_N": {"2": [...], "3": [...], ...},
     "rho_target_by_N": {...}}
"""

import json
from pathlib import Path

import numpy as np

from ..matrix.family import MatrixFamily
from ..matrix.transfer_matrix import TransferMatrix


def load_example_json(path):
    """Load a raw example JSON file as a dict."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_transfer_matrix(path):
    """Build a TransferMatrix from a single-matrix example file."""
    data = load_example_json(path)
    return TransferMatrix(data["matrix"], node_names=data.get("nodes"))


def load_family(path):
    """Build a MatrixFamily from a parameterized example file."""
    data = load_example_json(path)
    if "matrices_by_N" not in data:
        raise ValueError(f"{path} is not a parameterized family example")
    matrices = {
        key: np.asarray(matrix, dtype=float)
        for key, matrix in data["matrices_by_N"].items()
    }
    return MatrixFamily(
        name=data.get("name", Path(path).stem),
        nodes=data.get("nodes"),
        matrices_by_key=matrices,
        parameter_name=data.get("parameter", "N"),
        rho_targets=data.get("rho_target_by_N"),
        notes=data.get("notes"),
    )
