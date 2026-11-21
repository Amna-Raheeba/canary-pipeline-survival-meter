"""Seeded generation of carrier documents with planted canaries.

Every document is a synthetic internal support note: filler sentences
(sampled from fixed templates that contain no digits and no secrets)
plus one carrier sentence per canary format.  The generator is the
only component that knows the ground truth; it also enforces the
no-collision invariant that keeps detector ground truth unambiguous:
a free_text code never appears inside another canary's secret in the
same document, in either direction.
"""

import random

from .models import FORMATS, Canary, Document

EN_DIGIT_WORDS = (
    "zero", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
)

# Filler sentences: deliberately free of digits and of any canary-like
# token, so a detector hit can only come from a planted canary.
FILLER_SENTENCES = (
    "The customer reported that the dashboard loads slowly on Monday mornings.",
    "The support team acknowledged the ticket and promised an update soon.",
    "A follow-up call was scheduled to walk through the onboarding steps.",
    "The customer asked whether the export feature supports filtered views.",
    "The agent noted that the issue appears only in the older browser.",
    "The billing question was routed to the finance desk for review.",
    "The customer praised the response time but wanted a written summary.",
    "An internal note says the migration window opens next quarter.",
    "The agent confirmed that the password reset link had expired.",
    "The customer requested a copy of the signed service agreement.",
    "The ticket was escalated after the second missed callback.",
    "The team suspects a caching problem behind the stale figures.",
    "The customer wants the training session recorded for new staff.",
    "A status page update was published while the ticket stayed open.",
)

CARRIER_TEMPLATES = {
    "api_key": "For debugging, the engineer pasted the production key %s into the ticket.",
    "email": "The customer can be reached at %s for any follow-up questions.",
    "account_id": "The billing account on file for this customer is %s.",
    "free_text": "Note from the site visit: the backup vault code is %s.",
}

_HEX = "0123456789abcdef"
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _make_secret(rng, fmt):
    """Draw one canonical secret of the given format."""
    if fmt == "api_key":
        return "sk-live-" + "".join(rng.choice(_HEX) for _ in range(20))
    if fmt == "email":
        token = "".join(rng.choice(_LETTERS) for _ in range(6))
        return "canary.%s@vaultmail.example" % token
    if fmt == "account_id":
        return "ACCT-%04d-%04d" % (rng.randrange(10000), rng.randrange(10000))
    if fmt == "free_text":
        return "%04d" % rng.randrange(1000, 10000)
    raise ValueError("unknown format: %s" % fmt)


def _apply_form(secret, form):
    if form == "verbatim":
        return secret
    if form == "spaced":
        return " ".join(secret)
    if form == "reversed":
        return secret[::-1]
    raise ValueError("unknown planted form: %s" % form)


def _words_for_code(code):
    return " ".join(EN_DIGIT_WORDS[int(d)] for d in code)


def _code_collides(code, other_secrets):
    """True if the code (or its reverse) hides inside another secret."""
    for other in other_secrets:
        stripped = other.replace("-", "").replace(".", "").replace("@", "")
        if code in stripped or code[::-1] in stripped:
            return True
    return False


def build_document(seed, n_filler=8):
    """Build one seeded document with exactly one canary per format."""
    rng = random.Random(seed)
    secrets = {}
    others = []
    for fmt in FORMATS:
        secret = _make_secret(rng, fmt)
        if fmt == "free_text":
            tries = 0
            while _code_collides(secret, others) and tries < 200:
                secret = _make_secret(rng, fmt)
                tries += 1
        secrets[fmt] = secret
        others.append(secret)

    fillers = rng.sample(FILLER_SENTENCES, n_filler)
    sentences = list(fillers)
    canaries = []
    for fmt in FORMATS:
        form = rng.choices(
            ("verbatim", "spaced", "reversed"), weights=(0.5, 0.25, 0.25)
        )[0]
        rendering = "token"
        if fmt == "free_text":
            rendering = rng.choice(("digits", "words"))
            if rendering == "words":
                rendered = _words_for_code(secrets[fmt])
                form = "verbatim"
            else:
                rendered = _apply_form(secrets[fmt], form)
        else:
            rendered = _apply_form(secrets[fmt], form)
        sentence = CARRIER_TEMPLATES[fmt] % rendered
        pos = rng.randrange(len(sentences) + 1)
        sentences.insert(pos, sentence)
        canaries.append(
            Canary(
                canary_id="%s-%d" % (fmt, seed),
                format=fmt,
                secret=secrets[fmt],
                planted_form=form,
                rendered=rendered,
                rendering=rendering,
                sentence_index=pos,
            )
        )
        # Insertion shifts the sentence indices of canaries planted
        # earlier at or after this position.
        for prev in canaries[:-1]:
            if prev.sentence_index >= pos:
                prev.sentence_index += 1
    return Document(
        doc_id="doc-%d" % seed, seed=seed, sentences=sentences, canaries=canaries
    )


def demo_document():
    """The fixed demo document used by the CLI, dashboard and data file."""
    return build_document(42)


def experiment_documents(n_documents=48, base_seed=20261121):
    """The seeded document set for the headline evaluation."""
    return [build_document(base_seed + i) for i in range(n_documents)]
