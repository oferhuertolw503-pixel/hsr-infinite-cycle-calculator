"""Theory-document examples: reproduced spectral radii (section 6)."""

from pathlib import Path

import numpy as np
import pytest

from src.data_loader.matrix_loader import load_family, load_transfer_matrix

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"


def test_four_node_model_n5_matches_documented_rho():
    data = load_transfer_matrix(EXAMPLES / "four_node_model_N5.json")
    # section 6: rho = 0.88353 -> linear decay (theorem 1)
    assert np.isclose(data.spectral_radius(), 0.88353, atol=1e-5)
    assert data.classify()["regime"] == "decay"


def test_four_node_kill_energy_matches_documented_rho():
    data = load_transfer_matrix(EXAMPLES / "four_node_kill_energy.json")
    # section 6: adjusted + kill energy -> rho = 1.02442 > 1 (growth direction)
    assert np.isclose(data.spectral_radius(), 1.02442, atol=1e-5)
    result = data.classify()
    assert result["regime"] == "growth"
    # growth must not be presented as a practical infinite loop
    assert "不能单独推出实战无限循环" in result["conclusion"]


def test_four_node_perron_vector_matches_documented_alpha():
    import json
    data = json.loads((EXAMPLES / "four_node_model_N5.json").read_text(encoding="utf-8"))
    model = load_transfer_matrix(EXAMPLES / "four_node_model_N5.json")
    _, vec, info = model.dominant_pair()
    assert info["positive"]
    documented = np.array(data["documented_perron"])
    # the returned vector is sum-1 normalized; the documented alpha is the
    # raw Perron vector, so compare ratios (proportionality)
    documented = documented / documented[np.argmax(np.abs(documented))]
    vec = vec / vec[np.argmax(np.abs(vec))]
    assert np.allclose(vec, documented, rtol=1e-3)


def test_seven_node_family_matches_documented_rhos():
    family = load_family(EXAMPLES / "seven_node_family.json")
    rows = family.analyze()
    by_key = {row["key"]: row for row in rows}
    # documented endpoints: N=2 -> 1.00522, N=5 -> 1.04432 (section 6)
    assert np.isclose(by_key["2"]["rho"], 1.00522, atol=2e-5)
    assert np.isclose(by_key["5"]["rho"], 1.04432, atol=2e-5)
    # every family member must hit its documented target
    for row in rows:
        assert row["matches_target"], row
        assert row["regime"] == "growth"
        assert row["irreducible"]


def test_seven_node_family_rho_increases_with_N():
    family = load_family(EXAMPLES / "seven_node_family.json")
    sweep = family.regime_sweep()
    assert sweep["monotone_increasing"]
    radii = list(family.spectral_radii().values())
    assert radii == sorted(radii)


def test_seven_node_family_parameter_enters_matrix():
    # theory section 5.2: A changes with N; N=2 must differ from N=5
    family = load_family(EXAMPLES / "seven_node_family.json")
    assert not np.allclose(family.models["2"].A, family.models["5"].A)


def test_loader_rejects_non_family_file():
    with pytest.raises(ValueError):
        load_family(EXAMPLES / "four_node_model_N5.json")
