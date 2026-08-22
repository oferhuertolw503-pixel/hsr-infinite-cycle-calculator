import numpy as np
import pytest

from src.__main__ import _calculate_file
from src.calculator import calculate
from src.cases import verify_cases


def test_calculate_spectral_radius_and_regime():
    result = calculate([[0.5, 0.0], [0.0, 0.25]])

    assert np.isclose(result["rho"], 0.5)
    assert result["regime"] == "衰减（rho < 1）"
    assert np.allclose(result["dominant_vector"], [1.0, 0.0])


@pytest.mark.parametrize(
    "matrix, message",
    [
        ([[1, 2, 3], [4, 5, 6]], "非空方阵"),
        ([[1, -1], [0, 1]], "不能包含负数"),
        ([[1, float("nan")], [0, 1]], "NaN"),
    ],
)
def test_reject_invalid_matrix(matrix, message):
    with pytest.raises(ValueError, match=message):
        calculate(matrix)


def test_all_four_screenshot_cases_pass():
    results = verify_cases()

    assert len(results) == 4
    assert all(item["passed"] for item in results)


def test_seven_node_source_discrepancy_is_kept_explicit():
    result = verify_cases()[-1]

    assert result["passed"]
    assert "不一致" in result["detail"]


def test_calculate_json_file(tmp_path, capsys):
    path = tmp_path / "matrix.json"
    path.write_text(
        '{"name": "测试矩阵", "matrix": [[0.5, 0], [0, 0.25]]}',
        encoding="utf-8",
    )

    assert _calculate_file(path) == 0
    output = capsys.readouterr().out
    assert "测试矩阵" in output
    assert "rho = 0.50000000" in output
