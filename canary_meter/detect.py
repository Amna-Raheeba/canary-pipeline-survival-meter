"""Canary detectors: the oracle, the audit detector and the grep baseline.

Ground truth is *recoverability*: a canary survives a stage if its
secret core can be recovered from that stage's output by an oracle
that knows every transformation the pipeline can apply (verbatim,
spaced, reversed, chunk-split, base64, and digit words in English or
in the pipeline's own translation).  The audit detector is the
instrument this project ships: it recovers the spaced, reversed,
chunk-split and base64 forms and reads English digit words, but it
does *not* invert the translator -- so it honestly undercounts
survival after the translate stage.  The baseline is a verbatim grep
for the canonical secret, which is what most leakage checks amount
to in practice.
"""

import base64
import binascii
import re

from .generate import EN_DIGIT_WORDS
from .pipeline import CHUNK_MARKER, DICTIONARY

ES_DIGIT_WORDS = tuple(DICTIONARY[w] for w in EN_DIGIT_WORDS)

_B64_LINE = re.compile(r"^[A-Za-z0-9+/=]{20,}$")


def _strip(text):
    """Remove chunk markers and all whitespace (undoes spacing/splits)."""
    return "".join(text.replace(CHUNK_MARKER, "").split())


def _b64_views(text):
    """Decode blocks of consecutive base64-looking lines (MIME wraps).

    Ordinary prose lines contain spaces and never qualify, so this
    only fires on genuinely base64-armoured content.
    """
    views = []
    block = []

    def _flush():
        if not block:
            return
        blob = "".join(block)
        blob += "=" * (-len(blob) % 4)
        try:
            decoded = base64.b64decode(blob, validate=False)
        except (binascii.Error, ValueError):
            return
        try:
            views.append(decoded.decode("utf-8"))
        except UnicodeDecodeError:
            return

    for line in text.splitlines():
        if _B64_LINE.match(line.strip()):
            block.append(line.strip())
        else:
            _flush()
            block = []
    _flush()
    return views


def _replace_digit_words(text, digit_words):
    """Replace digit words with digits (no stripping).

    Chunk separators are removed first: a chunk boundary can fall
    inside a digit word without destroying the fact, and removing
    the separator restores the original word.
    """
    out = text.replace("\n" + CHUNK_MARKER + "\n", "").replace(CHUNK_MARKER, "")
    for digit, word in enumerate(digit_words):
        out = re.sub(r"\b%s\b" % word, str(digit), out)
    return out


def _digit_normalise(text, digit_words):
    """Replace digit words with digits, then strip whitespace."""
    return "".join(_replace_digit_words(text, digit_words).split())


def _found(secret, views):
    for view in views:
        if secret in view or secret[::-1] in view:
            return True
    return False


def _base_views(text):
    """Raw text, its decodings, and the stripped form of each."""
    raw = [text] + _b64_views(text)
    views = []
    for item in raw:
        views.append(item)
        views.append(_strip(item))
    return views


def oracle_detect(canary, text):
    """Ground truth: recoverable under the full inverse set."""
    views = _base_views(text)
    for item in [text] + _b64_views(text):
        views.append(_digit_normalise(item, EN_DIGIT_WORDS))
        views.append(_digit_normalise(item, ES_DIGIT_WORDS))
        # Composed view: a chunk boundary can split one digit word
        # so it escapes translation while its neighbours translate;
        # the fact is then mixed-language and only a mapping that
        # reads both languages recovers it.  Both replacements run
        # before stripping, so word boundaries survive.
        views.append(
            "".join(
                _replace_digit_words(
                    _replace_digit_words(item, ES_DIGIT_WORDS),
                    EN_DIGIT_WORDS,
                ).split()
            )
        )
    return _found(canary.secret, views)


def audit_detect(canary, text):
    """The shipped audit detector: no translator inversion."""
    views = _base_views(text)
    for item in [text] + _b64_views(text):
        views.append(_digit_normalise(item, EN_DIGIT_WORDS))
    return _found(canary.secret, views)


def grep_detect(canary, text):
    """Baseline: verbatim substring search for the canonical secret."""
    return canary.secret in text


DETECTORS = {
    "oracle": oracle_detect,
    "audit": audit_detect,
    "grep": grep_detect,
}
