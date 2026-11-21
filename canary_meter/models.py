"""Core data model for the canary pipeline survival meter.

A *canary* is a synthetic secret planted in a document at a known
position, in a known format and a known planted form.  Because the
planting is done by this package, the ground truth (what was planted,
where, and in which form) is known exactly; the pipeline stages and
detectors never see the canary metadata, only the document text.
"""

from dataclasses import dataclass, field

# The four graded canary formats, from most to least structured.
FORMATS = ("api_key", "email", "account_id", "free_text")

# How a canary's secret core is rendered into the carrier sentence.
# "verbatim" is the canonical string; "spaced" inserts a space
# between every character; "reversed" writes the string backwards.
# These are the obfuscations users (and exfiltrators) actually use to
# slip secrets past naive pattern matching.
PLANTED_FORMS = ("verbatim", "spaced", "reversed")

# The six pipeline transformations, in order.  "planted" is the
# pre-pipeline snapshot, not a stage.
STAGES = ("ingest", "summarise", "chunk", "redact", "translate", "mail")
SNAPSHOTS = ("planted",) + STAGES

# Formats the regex redactor claims to cover.  free_text is honestly
# not claimed: no regex covers a prose fact.  A canary of a claimed
# format that survives the redact stage is a *false claim*.
REDACTOR_CLAIMED_FORMATS = ("api_key", "email", "account_id")


@dataclass
class Canary:
    """One planted synthetic secret."""

    canary_id: str
    format: str
    # Canonical secret core the detectors search for.  For the token
    # formats this is the full token; for free_text it is the 4-digit
    # code, which is the part of the fact that carries the secret.
    secret: str
    planted_form: str
    # The secret as it actually appears in the document text (after
    # the planted-form transform; for word-form free_text, the digit
    # words instead of the digits).
    rendered: str
    # "token" for the structured formats, "digits" or "words" for
    # free_text facts.
    rendering: str
    # Index of the carrier sentence inside the document.
    sentence_index: int


@dataclass
class Document:
    """A synthetic carrier document with planted canaries."""

    doc_id: str
    seed: int
    sentences: list = field(default_factory=list)
    canaries: list = field(default_factory=list)

    @property
    def text(self):
        return " ".join(self.sentences)


@dataclass
class PipelineRun:
    """The result of pushing one document through the pipeline."""

    doc_id: str
    # stage name -> document text after that stage ("planted" = input)
    snapshots: dict = field(default_factory=dict)
    # What the redactor did and claimed, from the redact stage.
    redact_log: dict = field(default_factory=dict)
