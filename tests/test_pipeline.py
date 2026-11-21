"""Tests for the six pipeline stages."""

import base64

from canary_meter.generate import build_document, demo_document
from canary_meter.models import SNAPSHOTS
from canary_meter.pipeline import (
    CHUNK_MARKER,
    MAIL_MAX_CHARS,
    REDACTION,
    run_pipeline,
    split_sentences,
    stage_chunk,
    stage_ingest,
    stage_mail,
    stage_redact,
    stage_summarise,
    stage_translate,
)

KEY = "sk-live-0123456789abcdef0123"
EMAIL = "canary.abcdef@vaultmail.example"
ACCT = "ACCT-1234-5678"


def test_ingest_collapses_whitespace():
    assert stage_ingest("a   b\n\n c  ") == "a b c"


def test_split_sentences_round_trip():
    text = "One here. Two there. Three everywhere."
    parts = split_sentences(text)
    assert len(parts) == 3
    assert " ".join(parts) == text


def test_summarise_keeps_at_most_five():
    doc = build_document(3)
    out = stage_summarise(doc.text)
    assert len(split_sentences(out)) == 5
    for sentence in split_sentences(out):
        assert sentence in doc.sentences


def test_summarise_keeps_short_text_whole():
    text = "Only one. And two."
    assert stage_summarise(text) == text


def test_chunk_markers_and_reversibility():
    text = "x" * 500
    out = stage_chunk(text, width=100)
    assert CHUNK_MARKER in out
    restored = out.replace("\n" + CHUNK_MARKER + "\n", "")
    assert restored == text


def test_chunk_short_text_unchanged():
    assert stage_chunk("short", width=100) == "short"


def test_redact_replaces_verbatim_tokens():
    text = "key %s mail %s acct %s end" % (KEY, EMAIL, ACCT)
    out, log = stage_redact(text)
    assert KEY not in out and EMAIL not in out and ACCT not in out
    assert out.count(REDACTION) == 3
    assert log["replaced"] == {"api_key": 1, "email": 1, "account_id": 1}
    assert log["total_replaced"] == 3


def test_redact_misses_spaced_key():
    spaced = " ".join(KEY)
    out, log = stage_redact("key %s end" % spaced)
    assert log["replaced"]["api_key"] == 0
    assert spaced in out


def test_redact_catches_reversed_email():
    # The email pattern is direction-agnostic: a reversed address
    # still has an @ with dotted letter runs on both sides.
    out, log = stage_redact("mail %s end" % EMAIL[::-1])
    assert log["replaced"]["email"] == 1


def test_redact_does_not_claim_or_touch_free_text():
    out, log = stage_redact("the backup vault code is 4815.")
    assert "4815" in out
    assert "free_text" not in log["claimed_formats"]


def test_translate_substitutes_dictionary_words():
    out = stage_translate("The customer reported the vault code")
    assert "cliente" in out
    assert "boveda" in out
    assert "codigo" in out


def test_translate_leaves_clean_key_unchanged():
    assert stage_translate(KEY) == KEY


def test_translate_converts_digit_words():
    out = stage_translate("the code is four eight one five")
    assert "cuatro" in out and "ocho" in out
    assert "five" not in out


def test_mail_base64_round_trip_and_truncation():
    body = "y" * (MAIL_MAX_CHARS + 100)
    out = stage_mail(body)
    payload = out.split("\n\n", 1)[1]
    decoded = base64.b64decode("".join(payload.split())).decode("utf-8")
    assert decoded == "y" * MAIL_MAX_CHARS
    assert "Subject: Your support summary" in out


def test_run_pipeline_snapshots_and_log():
    doc = demo_document()
    run = run_pipeline(doc)
    assert list(run.snapshots.keys()) == list(SNAPSHOTS)
    assert run.snapshots["planted"] == doc.text
    assert run.redact_log["total_replaced"] >= 0
    assert set(run.redact_log["claimed_formats"]) == {
        "api_key", "email", "account_id"
    }
