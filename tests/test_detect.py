"""Tests for the oracle, audit and grep detectors."""

from canary_meter.detect import audit_detect, grep_detect, oracle_detect
from canary_meter.generate import FILLER_SENTENCES, build_document, demo_document
from canary_meter.models import Canary
from canary_meter.pipeline import CHUNK_MARKER, stage_mail, stage_translate


def _canary(secret, fmt="api_key", form="verbatim", rendering="token"):
    return Canary(canary_id="t", format=fmt, secret=secret,
                  planted_form=form, rendered=secret, rendering=rendering,
                  sentence_index=0)


def test_oracle_finds_every_demo_canary_at_planting():
    doc = demo_document()
    for c in doc.canaries:
        assert oracle_detect(c, doc.text)
        assert audit_detect(c, doc.text)


def test_oracle_and_audit_find_spaced_and_reversed():
    secret = "sk-live-0123456789abcdef0123"
    c = _canary(secret)
    assert oracle_detect(c, "x %s y" % " ".join(secret))
    assert audit_detect(c, "x %s y" % " ".join(secret))
    assert oracle_detect(c, "x %s y" % secret[::-1])
    assert audit_detect(c, "x %s y" % secret[::-1])
    assert not grep_detect(c, "x %s y" % " ".join(secret))
    assert not grep_detect(c, "x %s y" % secret[::-1])


def test_detectors_find_chunk_split_secret():
    secret = "ACCT-1234-5678"
    c = _canary(secret, fmt="account_id")
    text = "pre %s\n%s\n%s post" % (secret[:7], CHUNK_MARKER, secret[7:])
    assert oracle_detect(c, text)
    assert audit_detect(c, text)
    assert not grep_detect(c, text)


def test_detectors_find_base64_mail_output():
    secret = "canary.abcdef@vaultmail.example"
    c = _canary(secret, fmt="email")
    out = stage_mail("The customer can be reached at %s for follow-up." % secret)
    assert oracle_detect(c, out)
    assert audit_detect(c, out)
    assert not grep_detect(c, out)


def _word_form_canary():
    for seed in range(200):
        doc = build_document(seed)
        for c in doc.canaries:
            if c.format == "free_text" and c.rendering == "words":
                return doc, c
    raise AssertionError("no word-form canary found in 200 seeds")


def test_word_form_fact_recovery_across_translation():
    doc, c = _word_form_canary()
    sentence = doc.sentences[c.sentence_index]
    assert oracle_detect(c, sentence)
    assert audit_detect(c, sentence)
    translated = stage_translate(sentence)
    # The oracle reads the pipeline's own digit words back; the
    # audit detector does not invert the translator and loses it.
    assert oracle_detect(c, translated)
    assert not audit_detect(c, translated)
    assert not grep_detect(c, sentence)


def test_grep_finds_only_verbatim():
    secret = "ACCT-1234-5678"
    c = _canary(secret, fmt="account_id")
    assert grep_detect(c, "the account is %s." % secret)
    assert not grep_detect(c, "the account is %s." % secret.lower().replace("a", "a"))


def test_no_false_positives_on_filler():
    filler = " ".join(FILLER_SENTENCES)
    doc = demo_document()
    for c in doc.canaries:
        assert not oracle_detect(c, filler)
        assert not audit_detect(c, filler)
        assert not grep_detect(c, filler)


def test_oracle_misses_redacted_secret():
    secret = "sk-live-0123456789abcdef0123"
    c = _canary(secret)
    assert not oracle_detect(c, "the key is [REDACTED] now")
    assert not audit_detect(c, "the key is [REDACTED] now")
