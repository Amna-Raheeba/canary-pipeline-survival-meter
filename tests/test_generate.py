"""Tests for the seeded canary/document generator."""

import re

from canary_meter.generate import (
    FILLER_SENTENCES,
    build_document,
    demo_document,
    experiment_documents,
)
from canary_meter.models import FORMATS, PLANTED_FORMS

KEY_RE = re.compile(r"^sk-live-[0-9a-f]{20}$")
EMAIL_RE = re.compile(r"^canary\.[a-z]{6}@vaultmail\.example$")
ACCT_RE = re.compile(r"^ACCT-\d{4}-\d{4}$")
CODE_RE = re.compile(r"^\d{4}$")


def test_build_is_deterministic():
    a = build_document(123)
    b = build_document(123)
    assert a.text == b.text
    assert [c.secret for c in a.canaries] == [c.secret for c in b.canaries]


def test_different_seeds_differ():
    a = build_document(1)
    b = build_document(2)
    assert [c.secret for c in a.canaries] != [c.secret for c in b.canaries]


def test_one_canary_per_format():
    doc = build_document(5)
    assert sorted(c.format for c in doc.canaries) == sorted(FORMATS)


def test_secret_shapes():
    doc = build_document(9)
    by_format = dict((c.format, c) for c in doc.canaries)
    assert KEY_RE.match(by_format["api_key"].secret)
    assert EMAIL_RE.match(by_format["email"].secret)
    assert ACCT_RE.match(by_format["account_id"].secret)
    assert CODE_RE.match(by_format["free_text"].secret)


def test_planted_forms_are_valid():
    for seed in range(20):
        doc = build_document(seed)
        for c in doc.canaries:
            assert c.planted_form in PLANTED_FORMS


def test_verbatim_rendered_equals_secret_for_tokens():
    for seed in range(30):
        doc = build_document(seed)
        for c in doc.canaries:
            if c.format != "free_text" and c.planted_form == "verbatim":
                assert c.rendered == c.secret
            if c.planted_form == "spaced" and c.rendering == "token":
                assert c.rendered == " ".join(c.secret)
            if c.planted_form == "reversed" and c.rendering == "token":
                assert c.rendered == c.secret[::-1]


def test_word_form_free_text_has_no_digits():
    seen = 0
    for seed in range(60):
        doc = build_document(seed)
        for c in doc.canaries:
            if c.format == "free_text" and c.rendering == "words":
                seen += 1
                assert not any(ch.isdigit() for ch in c.rendered)
                assert len(c.rendered.split()) == 4
    assert seen > 0


def test_filler_sentences_contain_no_digits():
    for sentence in FILLER_SENTENCES:
        assert not any(ch.isdigit() for ch in sentence)


def test_sentence_index_points_at_carrier():
    for seed in range(10):
        doc = build_document(seed)
        for c in doc.canaries:
            assert c.rendered in doc.sentences[c.sentence_index]


def test_code_does_not_hide_in_other_secrets():
    for seed in range(40):
        doc = build_document(seed)
        code = [c for c in doc.canaries if c.format == "free_text"][0].secret
        for c in doc.canaries:
            if c.format == "free_text":
                continue
            stripped = c.secret.replace("-", "").replace(".", "").replace("@", "")
            assert code not in stripped
            assert code[::-1] not in stripped


def test_demo_document_seed():
    doc = demo_document()
    assert doc.seed == 42
    assert doc.doc_id == "doc-42"


def test_experiment_documents():
    docs = experiment_documents(5, base_seed=100)
    assert len(docs) == 5
    assert [d.seed for d in docs] == [100, 101, 102, 103, 104]
