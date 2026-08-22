from src.v1 import verify


def test_v1_verifies_all_four_case_images():
    result = verify()

    assert result["version"] == "v1"
    assert result["all_verified"]
    assert [row["image"] for row in result["rows"]] == [
        "case_4node_decay.png",
        "case_4node_kill.png",
        "case_matrix_definition.png",
        "case_7node_matrix.png",
    ]
    assert all(row["verified"] for row in result["rows"])


def test_v1_exposes_seven_node_source_inconsistency():
    result = verify()
    seven_table = result["rows"][-1]

    assert seven_table["checks"]["reported_rhos"]
    assert seven_table["checks"]["calibrated_cell"]
    assert seven_table["checks"]["source_inconsistency_exposed"]
