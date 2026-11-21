"""Tests for the core data model and constants."""

from canary_meter.models import (
    FORMATS,
    PLANTED_FORMS,
    REDACTOR_CLAIMED_FORMATS,
    SNAPSHOTS,
    STAGES,
    Canary,
    Document,
    PipelineRun,
)


def test_formats_are_the_four_graded_formats():
    assert FORMATS == ("api_key", "email", "account_id", "free_text")


def test_snapshots_are_planted_plus_stages():
    assert SNAPSHOTS == ("planted",) + STAGES
    assert len(STAGES) == 6


def test_redactor_does_not_claim_free_text():
    assert "free_text" not in REDACTOR_CLAIMED_FORMATS
    for fmt in ("api_key", "email", "account_id"):
        assert fmt in REDACTOR_CLAIMED_FORMATS


def test_planted_forms():
    assert set(PLANTED_FORMS) == {"verbatim", "spaced", "reversed"}


def test_document_text_joins_sentences():
    doc = Document(doc_id="d", seed=1, sentences=["One.", "Two."])
    assert doc.text == "One. Two."


def test_canary_fields():
    c = Canary(canary_id="x", format="api_key", secret="s",
               planted_form="verbatim", rendered="s", rendering="token",
               sentence_index=0)
    assert c.format in FORMATS
    assert c.planted_form in PLANTED_FORMS


def test_pipeline_run_defaults():
    run = PipelineRun(doc_id="d")
    assert run.snapshots == {}
    assert run.redact_log == {}
