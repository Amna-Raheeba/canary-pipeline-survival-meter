"""Tests for the report builders."""

from canary_meter.evaluate import run_evaluation
from canary_meter.generate import demo_document
from canary_meter.pipeline import run_pipeline
from canary_meter.report import document_report, evaluation_summary, headline


def test_document_report_contents():
    doc = demo_document()
    run = run_pipeline(doc)
    text = document_report(doc, run)
    assert "Canary survival audit" in text
    assert "Redactor log" in text
    assert "Leaked into the mailed output" in text
    for c in doc.canaries:
        assert c.canary_id in text


def test_evaluation_summary_contents():
    results = run_evaluation(n_documents=4)
    text = evaluation_summary(results)
    assert "Stage x format survival" in text
    assert "Redactor honesty" in text
    assert "false-claim" in text
    for fmt in ("api_key", "email", "account_id", "free_text"):
        assert fmt in text


def test_headline_contents():
    results = run_evaluation(n_documents=4)
    text = headline(results)
    assert "Headline results" in text
    assert "Overall leak rate" in text
    agg = results["aggregate"]
    expected = "%.1f%%" % (100.0 * agg["overall_leak_rate"])
    assert expected in text
