"""Tests for the headline-drift guard in scripts/reproduce_results.py."""

import importlib.util
import os

from canary_meter.evaluate import run_evaluation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_guard():
    path = os.path.join(ROOT, "scripts", "reproduce_results.py")
    spec = importlib.util.spec_from_file_location("reproduce_results", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_headline_values_cover_matrix_and_honesty():
    guard = _load_guard()
    values = guard.headline_values(run_evaluation(n_documents=2))
    assert values["overall_leak_rate"] >= 0.0
    assert "survival_mail_free_text" in values
    assert "recovery_mail_audit" in values
    assert "false_claim_api_key" in values
    assert "redactor_kill_free_text" in values


def test_guard_reproduces_shipped_results():
    guard = _load_guard()
    assert guard.main() == 0
