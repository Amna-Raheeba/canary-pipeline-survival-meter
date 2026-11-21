"""Tests for the command line interface."""

import io
import json
import os

from canary_meter.cli import main, run_demo, run_evaluate


def test_run_demo(capsys):
    assert run_demo() == 0
    out = capsys.readouterr().out
    assert "Canary survival audit" in out


def test_main_demo(capsys):
    assert main(["demo"]) == 0
    assert "Redactor log" in capsys.readouterr().out


def test_run_evaluate_writes_files(tmp_path):
    out_dir = str(tmp_path / "results")
    assert run_evaluate(out_dir) == 0
    for name in ("evaluation.json", "evaluation.csv",
                 "evaluation_summary.md", "HEADLINE.md"):
        assert os.path.exists(os.path.join(out_dir, name))
    with io.open(os.path.join(out_dir, "evaluation.json"),
                 encoding="utf-8") as fh:
        results = json.load(fh)
    assert results["aggregate"]["n_canaries"] == 192


def test_main_evaluate(tmp_path, capsys):
    out_dir = str(tmp_path / "r")
    assert main(["evaluate", "--out", out_dir]) == 0
    assert "Overall leak rate" in capsys.readouterr().out
