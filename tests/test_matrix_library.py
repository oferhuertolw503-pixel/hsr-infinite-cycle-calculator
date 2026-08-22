"""Matrix library tests (theory section 7, step 8: version data)."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from src.data_loader.matrix_loader import load_matrix_library
from src.matrix.library import MatrixLibrary, MatrixVariant

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"
LIBRARY = EXAMPLES / "version_matrix_library.json"

# pytest's tmp_path points at the system temp dir, which the file sandbox
# denies in some environments; a workspace-relative dir works everywhere.
TMP_DIR = Path(__file__).resolve().parent / ".tmp_library"


@pytest.fixture
def library_file():
    TMP_DIR.mkdir(exist_ok=True)
    yield TMP_DIR
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def _two_variant_library():
    decay = MatrixVariant(
        name="v1", matrix=[[0.5]], nodes=["a"],
        version="1.0", mode="mode-a", enemy="enemy-x",
        provenance="demo",
    )
    growth = MatrixVariant(
        name="v2", matrix=[[1.2]], nodes=["a"],
        version="2.0", mode="mode-a", enemy="enemy-y",
        provenance="demo",
    )
    return MatrixLibrary(name="lib", variants=[decay, growth])


def test_compare_detects_regime_disagreement():
    comparison = _two_variant_library().compare()
    assert comparison["consensus"] is False
    assert comparison["regimes"] == ["decay", "growth"]
    assert any("不可外推" in w for w in comparison["warnings"])
    # Same node list -> a single granularity group.
    assert set(comparison["node_groups"]) == {("a",)}


def test_compare_consensus_when_regimes_agree():
    library = MatrixLibrary(
        name="lib",
        variants=[
            MatrixVariant(name="v1", matrix=[[0.5]], provenance="demo"),
            MatrixVariant(name="v2", matrix=[[0.9]], provenance="demo"),
        ],
    )
    comparison = library.compare()
    assert comparison["consensus"] is True
    assert comparison["warnings"] == []


def test_filter_by_context_tag():
    library = _two_variant_library()
    assert [v.name for v in library.filter(mode="mode-a").variants] == ["v1", "v2"]
    assert [v.name for v in library.filter(version="2.0").variants] == ["v2"]
    assert library.filter(version="9.9").variants == []
    with pytest.raises(ValueError, match="unknown context tag"):
        library.filter(target_count=5)


def test_library_validation():
    with pytest.raises(ValueError, match="duplicate variant names"):
        MatrixLibrary(name="lib", variants=[
            MatrixVariant(name="v", matrix=[[0.5]]),
            MatrixVariant(name="v", matrix=[[0.6]]),
        ])


def test_loader_rejects_empty_library(library_file):
    path = library_file / "lib.json"
    path.write_text(json.dumps({"name": "empty", "variants": []}),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="declares no variants"):
        load_matrix_library(path)


def test_undocumented_variants_are_flagged():
    library = MatrixLibrary(
        name="lib",
        variants=[
            MatrixVariant(name="v1", matrix=[[0.5]], provenance="demo"),
            MatrixVariant(name="v2", matrix=[[1.2]]),
        ],
    )
    comparison = library.compare()
    assert any("provenance" in w for w in comparison["warnings"])


def test_demo_library_loads_all_variants():
    library = load_matrix_library(LIBRARY)
    comparison = library.compare()
    assert len(comparison["rows"]) == 11
    assert comparison["regimes"] == ["decay", "growth"]
    assert comparison["consensus"] is False
    # Three granularities: reconstructed A/B/C/D, seven-node, and the
    # screenshot four-node H/H_U/T/T_U model.
    assert len(comparison["node_groups"]) == 3
    # Most source references keep the documented rho values in sync.
    documented = [r for r in comparison["rows"] if "matches_documented" in r]
    matched = [r for r in documented if r["matches_documented"]]
    assert {round(r["rho"], 5) for r in matched} == {
        0.88353, 1.02442, 1.00522, 1.04432
    }
    # The exact seven-node transcription intentionally exposes the source
    # image's matrix/table inconsistency instead of hiding it.
    mismatched = [r["name"] for r in documented if not r["matches_documented"]]
    assert mismatched == [
        "七节点·截图显示矩阵 (N=2)",
        "七节点·截图显示矩阵 (N=5)",
    ]


def test_demo_library_perturbation_reference_values():
    library = load_matrix_library(LIBRARY)
    by_name = {v.name: v for v in library.variants}
    n5 = by_name["七节点·目标数升至 N=5"]
    assert np.isclose(n5.model.spectral_radius(), 1.04432, atol=2e-5)
    missed = by_name["七节点·击杀不持续 (N=2)"]
    assert np.isclose(missed.model.spectral_radius(), 0.996494, atol=2e-5)
    assert missed.model.classify()["regime"] == "decay"


def test_loader_family_key_reference(library_file):
    path = library_file / "lib.json"
    path.write_text(json.dumps({
        "name": "family ref",
        "variants": [{
            "name": "N=5 via family_key",
            "source": "examples/theory_document/seven_node_family.json",
            "family_key": "5",
        }],
    }), encoding="utf-8")
    library = load_matrix_library(path)
    assert np.isclose(
        library.variants[0].model.spectral_radius(), 1.04432, atol=2e-5
    )


def test_loader_rejects_variant_without_matrix_or_source(library_file):
    path = library_file / "lib.json"
    path.write_text(json.dumps({
        "name": "bad",
        "variants": [{"name": "nothing"}],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="matrix.*source"):
        load_matrix_library(path)


def test_loader_rejects_non_library_file():
    with pytest.raises(ValueError, match="no 'variants'"):
        load_matrix_library(EXAMPLES / "four_node_model_N5.json")
