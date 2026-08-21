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
from ..matrix.library import MatrixLibrary, MatrixVariant
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


def _resolve_source(source, library_path):
    """Resolve a variant's source path against the library file, then CWD."""
    candidate = Path(library_path).parent / source
    if candidate.exists():
        return candidate
    return Path(source)


def _variant_matrix_from_source(entry, library_path):
    """Extract (matrix, nodes, documented_rho) from a referenced example.

    Three reference modes, all regen-safe (the referenced files are the
    single source of truth for the matrices):

      source: ...                      -> the file's own matrix
      source + family_key: "5"         -> matrices_by_N[key] of a family
      source + perturbation: "label"   -> that perturbation's matrix
    """
    source_data = load_example_json(_resolve_source(entry["source"], library_path))
    family_key = entry.get("family_key")
    perturbation_label = entry.get("perturbation")

    if family_key is not None:
        if "matrices_by_N" not in source_data:
            raise ValueError(
                f"{entry['source']} has no matrices_by_N for family_key"
            )
        matrix = source_data["matrices_by_N"][str(family_key)]
        documented = (source_data.get("rho_target_by_N") or {}).get(
            str(family_key)
        )
    elif perturbation_label is not None:
        matches = [
            p["matrix"] for p in source_data.get("perturbations", [])
            if p.get("label") == perturbation_label
        ]
        if not matches:
            raise ValueError(
                f"{entry['source']} has no perturbation "
                f"{perturbation_label!r}"
            )
        matrix = matches[0]
        documented = None
    else:
        if "matrix" not in source_data:
            raise ValueError(
                f"{entry['source']} is neither a single-matrix example, "
                "a family (needs family_key) nor an audit demo "
                "(needs perturbation)"
            )
        matrix = source_data["matrix"]
        documented = source_data.get("documented_rho")
    return matrix, source_data.get("nodes"), documented


def load_matrix_library(path):
    """Build a MatrixLibrary from a version/mode/blessing/enemy registry.

    Library JSON format:

        {"name": ..., "notes": ...,
         "variants": [
            {"name": ..., "matrix": [[...]], "nodes": [...],
             "version": ..., "mode": ..., "blessing": ..., "enemy": ...,
             "provenance": ..., "documented_rho": ..., "notes": ...},
            {"name": ..., "source": "examples/theory_document/....json",
             "family_key": "5" | "perturbation": "label", ...overrides}
         ]}
    """
    data = load_example_json(path)
    if "variants" not in data:
        raise ValueError(f"{path} is not a matrix library (no 'variants')")
    if not data["variants"]:
        raise ValueError(f"{path} declares no variants")

    variants = []
    for entry in data["variants"]:
        if "matrix" in entry:
            matrix = entry["matrix"]
            nodes = entry.get("nodes")
            documented = entry.get("documented_rho")
        elif "source" in entry:
            matrix, nodes, documented = _variant_matrix_from_source(
                entry, path
            )
        else:
            raise ValueError(
                f"variant {entry.get('name', '?')!r} needs either an "
                "inline 'matrix' or a 'source' reference"
            )
        source = entry.get("source")
        if entry.get("name"):
            name = entry["name"]
        elif source:
            name = Path(source).stem
        else:
            name = entry["name"]
        variants.append(MatrixVariant(
            name=name,
            matrix=matrix,
            nodes=nodes,
            version=entry.get("version"),
            mode=entry.get("mode"),
            blessing=entry.get("blessing"),
            enemy=entry.get("enemy"),
            provenance=entry.get("provenance"),
            documented_rho=entry.get("documented_rho", documented),
            notes=entry.get("notes"),
        ))
    return MatrixLibrary(
        name=data.get("name", Path(path).stem),
        variants=variants,
        notes=data.get("notes"),
    )
