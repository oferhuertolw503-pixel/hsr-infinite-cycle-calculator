from pathlib import Path

import pytest

from src import cli


ROOT = Path(__file__).resolve().parent.parent


def test_default_command_runs_matrix_analysis(capsys):
    example = ROOT / "examples" / "theory_document" / "four_node_model_N5.json"

    result = cli.run_cli([str(example)])

    assert result["regime"] == "decay"
    assert "谱半径" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("flag", "handler_name"),
    [
        ("--family", "run_family"),
        ("--library", "run_library"),
        ("--report", "run_report"),
        ("--team", "run_team"),
    ],
)
def test_mode_flag_dispatches_to_its_handler(monkeypatch, flag, handler_name):
    calls = []
    monkeypatch.setattr(
        cli,
        handler_name,
        lambda path: calls.append(path) or handler_name,
    )

    result = cli.run_cli(["example.json", flag])

    assert result == handler_name
    assert calls == ["example.json"]


def test_search_options_are_forwarded(monkeypatch):
    calls = []

    def fake_search(path, team_size=None, max_rounds=None):
        calls.append((path, team_size, max_rounds))
        return "search"

    monkeypatch.setattr(cli, "run_search", fake_search)

    result = cli.run_cli([
        "team.json", "--search", "--team-size", "2", "--max-rounds", "50"
    ])

    assert result == "search"
    assert calls == [("team.json", 2, 50)]


def test_default_options_are_forwarded(monkeypatch):
    calls = []

    def fake_single(path, audit=False, sensitivity=False, repair=False):
        calls.append((path, audit, sensitivity, repair))
        return "single"

    monkeypatch.setattr(cli, "run_single", fake_single)

    result = cli.run_cli([
        "matrix.json", "--audit", "--sensitivity", "--repair"
    ])

    assert result == "single"
    assert calls == [("matrix.json", True, True, True)]
