"""The six deterministic pipeline stages.

Each stage is a pure text-to-text transformation (the redact stage
also returns its log).  The stages are deliberately ordinary: an
extractive summariser, a fixed-width chunker, a regex redactor, a
dictionary translator and a MIME-style template mailer of the kind
sitting inside real LLM data pipelines.  None of them knows anything
about canaries.
"""

import base64
import hashlib
import re

from .models import REDACTOR_CLAIMED_FORMATS, STAGES, PipelineRun

CHUNK_MARKER = "@@CHUNK@@"
CHUNK_WIDTH = 110
SUMMARY_KEEP = 5
MAIL_MAX_CHARS = 420
REDACTION = "[REDACTED]"

_SUMMARY_KEYWORDS = (
    "customer", "billing", "urgent", "reported", "account", "follow",
    "visit", "key", "code", "reached", "issue", "payment", "ticket",
)

# Word-by-word pseudo-translation dictionary (English -> Spanish-like).
# Tokens absent from the dictionary pass through unchanged, which is
# why token-shaped secrets survive translation but prose facts do not:
# their English digit words are in the dictionary.
DICTIONARY = {
    "the": "el", "a": "un", "an": "un", "customer": "cliente",
    "reported": "reporto", "that": "que", "is": "es", "can": "puede",
    "be": "ser", "reached": "alcanzado", "at": "en", "for": "para",
    "any": "cualquier", "follow": "seguimiento", "questions": "preguntas",
    "billing": "facturacion", "account": "cuenta", "on": "en",
    "file": "archivo", "this": "este", "note": "nota", "from": "desde",
    "site": "sitio", "visit": "visita", "backup": "respaldo",
    "vault": "boveda", "code": "codigo", "debugging": "depuracion",
    "engineer": "ingeniero", "pasted": "pegado", "production": "produccion",
    "key": "clave", "into": "dentro", "ticket": "ticket",
    "zero": "cero", "one": "uno", "two": "dos", "three": "tres",
    "four": "cuatro", "five": "cinco", "six": "seis", "seven": "siete",
    "eight": "ocho", "nine": "nueve",
}

_REDACTOR_PATTERNS = (
    ("api_key", re.compile(r"sk-live-[0-9a-f]{20}")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("account_id", re.compile(r"ACCT-\d{4}-\d{4}")),
)

_WORD_RE = re.compile(r"[A-Za-z]+")


def split_sentences(text):
    """Split on sentence boundaries.

    Safe for the generated documents: secrets are always planted
    mid-sentence, so no secret contains the '. ' separator.
    """
    parts = text.split(". ")
    sentences = [p + "." for p in parts[:-1]]
    if parts[-1]:
        sentences.append(parts[-1])
    return [s for s in sentences if s.strip()]


def stage_ingest(text):
    """Whitespace cleanup: collapse runs, strip the ends."""
    return " ".join(text.split())


def _sentence_score(sentence):
    low = sentence.lower()
    hits = sum(1 for kw in _SUMMARY_KEYWORDS if kw in low)
    digest = hashlib.md5(sentence.encode("utf-8")).hexdigest()
    jitter = (int(digest[:4], 16) % 100) / 200.0
    return hits + jitter


def stage_summarise(text, keep=SUMMARY_KEEP):
    """Extractive summariser: keep the `keep` highest-scored sentences."""
    sentences = split_sentences(text)
    if len(sentences) <= keep:
        return text
    ranked = sorted(
        range(len(sentences)), key=lambda i: (-_sentence_score(sentences[i]), i)
    )
    chosen = sorted(ranked[:keep])
    return " ".join(sentences[i] for i in chosen)


def stage_chunk(text, width=CHUNK_WIDTH):
    """Fixed-width character chunker with an explicit separator."""
    if len(text) <= width:
        return text
    pieces = [text[i:i + width] for i in range(0, len(text), width)]
    return ("\n" + CHUNK_MARKER + "\n").join(pieces)


def stage_redact(text):
    """Regex redactor.  Returns (text, log).

    The log records how many matches each pattern replaced and which
    formats the redactor claims to cover, so the audit can grade the
    claim against measured survival.
    """
    replaced = {}
    out = text
    for fmt, pattern in _REDACTOR_PATTERNS:
        out, n = pattern.subn(REDACTION, out)
        replaced[fmt] = n
    log = {
        "replaced": replaced,
        "total_replaced": sum(replaced.values()),
        "claimed_formats": list(REDACTOR_CLAIMED_FORMATS),
    }
    return out, log


def stage_translate(text):
    """Dictionary translator: substitute known words, pass the rest."""

    def _sub(match):
        word = match.group(0)
        return DICTIONARY.get(word.lower(), word)

    return _WORD_RE.sub(_sub, text)


def stage_mail(text, max_chars=MAIL_MAX_CHARS):
    """Template mailer: truncate the body and MIME-base64 it."""
    body = text[:max_chars]
    encoded = base64.b64encode(body.encode("utf-8")).decode("ascii")
    lines = [encoded[i:i + 76] for i in range(0, len(encoded), 76)]
    header = (
        "Subject: Your support summary\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: base64\n"
        "\n"
    )
    return header + "\n".join(lines)


def run_pipeline(document):
    """Push one document through all six stages, snapshotting each."""
    snapshots = {"planted": document.text}
    text = stage_ingest(document.text)
    snapshots["ingest"] = text
    text = stage_summarise(text)
    snapshots["summarise"] = text
    text = stage_chunk(text)
    snapshots["chunk"] = text
    text, redact_log = stage_redact(text)
    snapshots["redact"] = text
    text = stage_translate(text)
    snapshots["translate"] = text
    text = stage_mail(text)
    snapshots["mail"] = text
    assert list(snapshots.keys()) == ["planted"] + list(STAGES)
    return PipelineRun(
        doc_id=document.doc_id, snapshots=snapshots, redact_log=redact_log
    )
