"""Tests for the headline evaluation."""

from canary_meter.evaluate import evaluate_documents, run_evaluation
from canary_meter.generate import experiment_documents
from canary_meter.models import FORMATS, SNAPSHOTS, STAGES


def _small():
    return run_evaluation(n_documents=6)


def test_structure():
    results = _small()
    assert results["documents"] == 6
    assert len(results["records"]) == 6 * len(FORMATS)
    agg = results["aggregate"]
    for key in ("survival", "recovery", "redactor", "killing_stages",
                "leak_rate", "overall_leak_rate"):
        assert key in agg


def test_planted_survival_is_perfect():
    agg = _small()["aggregate"]
    for fmt in FORMATS:
        assert agg["survival"]["planted"][fmt] == 1.0


def test_survival_is_monotone_non_increasing():
    agg = _small()["aggregate"]
    for fmt in FORMATS:
        series = [agg["survival"][s][fmt] for s in SNAPSHOTS]
        for earlier, later in zip(series, series[1:]):
            assert later <= earlier + 1e-9


def test_audit_recovery_perfect_until_translation():
    agg = _small()["aggregate"]
    for snap in ("planted", "ingest", "summarise", "chunk", "redact"):
        assert agg["recovery"][snap]["audit"] == 1.0
    assert agg["recovery"]["mail"]["grep"] == 0.0


def test_redactor_honesty_fields():
    agg = _small()["aggregate"]
    free = agg["redactor"]["free_text"]
    assert free["claimed"] is False
    assert free["false_claim_rate"] is None
    assert free["kill_rate"] == 0.0
    for fmt in ("api_key", "email", "account_id"):
        entry = agg["redactor"][fmt]
        assert entry["claimed"] is True
        assert 0.0 <= entry["false_claim_rate"] <= 1.0


def test_killing_stage_accounting():
    results = _small()
    agg = results["aggregate"]
    total = sum(agg["killing_stages"][s] for s in STAGES)
    total += agg["killing_stages"]["leaked"]
    assert total == agg["n_canaries"]


def test_leak_rate_matches_mail_survival():
    agg = _small()["aggregate"]
    for fmt in FORMATS:
        assert agg["leak_rate"][fmt] == agg["survival"]["mail"][fmt]


def test_evaluate_documents_matches_run():
    docs = experiment_documents(3)
    results = evaluate_documents(docs)
    assert results["documents"] == 3
    assert results["aggregate"]["n_canaries"] == 3 * len(FORMATS)
