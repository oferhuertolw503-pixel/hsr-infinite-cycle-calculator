"""Report aggregation tests: matrix + bottleneck + cycle in one report."""

from pathlib import Path

from src.analyzer.report import Report
from src.data_loader.matrix_loader import load_example_json
from src.matrix.transfer_matrix import TransferMatrix

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "theory_document"


def _four_node():
    data = load_example_json(EXAMPLES / "four_node_model_N5.json")
    return TransferMatrix(data["matrix"], node_names=data["nodes"])


def test_report_without_timing_flags_unverified_feasibility():
    report = Report(_four_node()).generate()
    assert set(report) >= {
        "matrix", "perron", "bottleneck", "cycle", "caveats", "text"
    }
    assert report["matrix"]["regime"] == "decay"
    assert report["cycle"]["stable"] is None
    assert "时序模拟" in report["cycle"]["note"]
    # The text rendering carries the section-6 wording discipline.
    assert "完整报告" in report["text"]
    assert "未运行离散时序模拟" in report["text"]


def test_report_with_timing_classifies_break():
    report = Report(_four_node()).generate(timing_result={
        "stable": False,
        "loops_completed": 4,
        "break_reason": "enemy_interjection",
        "enemy_actions": 1,
    })
    assert report["cycle"]["break_class"] == "timing"
    assert "断轴类别=timing" in report["text"]
    assert "时序问题" in report["text"]


def test_report_bottleneck_summary_is_trimmed():
    report = Report(_four_node()).generate()
    bottleneck = report["bottleneck"]
    assert bottleneck["analytic"] is True
    assert len(bottleneck["decisive_edges"]) == 5
    assert len(bottleneck["fragile_edges"]) == 5
    assert bottleneck["decisive_edges"][0]["from"] == "H_U"


def test_report_accepts_raw_matrix():
    report = Report([[0.5]]).generate()
    assert report["matrix"]["regime"] == "decay"
