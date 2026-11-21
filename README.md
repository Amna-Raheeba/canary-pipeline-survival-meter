# Canary Pipeline Survival Meter

**Where did the secret survive?** Plant labelled synthetic secrets
at the entrance of an LLM data pipeline, push them through the
stages every real pipeline has — summarise, chunk, redact,
translate, mail — and measure, stage by stage and format by format,
which stage leaks them and which stage falsely claims to have
redacted them.

## 1. What it is

Pipelines that summarise support tickets, chunk documents for
retrieval, "redact" secrets and forward the result rarely get
audited end to end. Each stage is someone else's component, and the
usual leakage check is a verbatim grep at the end — which, measured
below, finds **0.0%** of what actually leaks into the mailed output.

This tool is a defensive measurement instrument for your *own*
pipeline. It plants canary secrets of graded formats at known entry
points, runs them through a chain of deterministic offline pipeline
operators, and scores canary survival per stage with a detector
that recovers spaced, reversed, chunk-split and base64 forms. The
output is a stage × format survival matrix that names the exact
stage that leaks and the exact stage that falsely claims to redact.
Everything is offline, deterministic and seeded. Pure Python
standard library; no API keys, no model downloads, no network. All
secrets and documents are synthetic, generated in-repo — there is
no real credential or personal data anywhere in this project.

## 2. The novel mechanism

**Stage-wise canary survival with redactor-honesty grading.** Three
components:

1. **Graded canaries.** Four formats of increasing prose-ness —
   `api_key` (`sk-live-…` token), `email`, `account_id`
   (`ACCT-####-####`) and `free_text` (a prose fact whose secret is
   a 4-digit vault code, planted as digits or as digit *words*) —
   each planted verbatim, spaced (`s k - l i v e - …`) or reversed,
   the obfuscations that slip past pattern matching in the wild.
2. **An oracle ground truth.** Survival at a stage is
   *recoverability*: an oracle detector that inverts every
   transformation the pipeline can apply (spacing, reversal, chunk
   splits, base64 armour, digit words in English and in the
   pipeline's own translation) decides whether the secret core is
   still recoverable from that stage's output. A second, shipped
   **audit detector** recovers the same obfuscations but does not
   invert the translator — its shortfall against the oracle is
   itself a measured result. The baseline is a **verbatim grep**
   for the canonical secret.
3. **Redactor honesty.** The regex redactor claims to cover the
   three token formats. For each claimed format, the *false-claim
   rate* is the share of canaries entering the redact stage that
   walk out of it still recoverable. `free_text` is honestly not
   claimed — no regex covers a prose fact — and its survival is
   reported separately.

## 3. Prior art and the differentiator

Provider-scale canary studies (Dragos / HD Moore, 2026, ~2M prompts
to live AI services) and prompt-injection exfiltration test guides
target *live third-party services*; canary detectors exist as test
snippets. None measures stage-wise survival through a user's own
transformation chain, and none grades redactor honesty
(claimed-redacted vs actually-surviving) per format. That is the
unit of analysis here: not "did a secret leak?" but "at which stage,
in which format, past which claimed defence?"

## 4. The pipeline under audit

Six deterministic stages, all simulated offline:

| stage | operator | what it does to canaries |
|---|---|---|
| ingest | whitespace cleanup | nothing (control stage) |
| summarise | extractive summariser | drops low-scored sentences, canaries included |
| chunk | fixed-width chunker (110 chars) | splits secrets across chunk boundaries |
| redact | regex redactor | replaces canonical token patterns, logs claims |
| translate | dictionary translator | substitutes known words; tokens pass through, prose mutates |
| mail | template mailer | truncates the body to 420 chars and base64-armours it |

## 5. Measured headline results

48 seeded documents, 192 planted canaries (one per format per
document), full run shipped in `results/`.

**Survival into the mailed output (oracle):** api_key **31.2%**,
email **10.4%**, account_id **18.8%**, free_text **89.6%** — an
overall leak rate of **37.5%** of planted canaries reaching the
recipient.

**Redactor honesty:** the redactor kills only 39.6% of the API keys
that enter it. Its false-claim rate is **60.4%** for api_key,
**45.8%** for account_id and **12.8%** for email — **41.5%** across
the formats it claims to cover. The spaced, reversed and
chunk-split plantings are what walk through: the patterns only see
canonical contiguous tokens. (One emergent exception: the email
pattern is direction-agnostic, so reversed emails *are* caught —
hence email's low false-claim rate.) Free-text facts are never
redacted at all: 100% survive the redact stage, and 89.6% reach the
recipient.

**Detector recovery (share of true survivors found):** the audit
detector recovers 100% of survivors through the redact stage, then
falls to **66.7%** at the mail stage — the translated digit-word
facts it cannot read back. Verbatim grep degrades from 48.4% at
planting (it only ever sees the verbatim half of plantings) to
12.5% after redaction and **0.0%** at the mail stage, where the
output is base64.

**Killing-stage attribution** (of 192 canaries): summarise 9,
chunk 0 (lossless — it hides secrets from pattern matchers without
destroying them), redact 79, translate 24, mail 8, leaked 72. The
translate kills are a collateral-damage finding: spaced canaries
die there because a standalone spaced `a` is a dictionary word and
gets translated like one.

## 6. How to run

```bash
pip install -r requirements.txt
python -m canary_meter demo          # audit the demo document
python -m canary_meter evaluate      # full 48-document evaluation -> results/
python scripts/reproduce_results.py  # headline-drift guard vs shipped results
python notebooks/01_demo_run.py      # demo, notebook form
python notebooks/02_evaluation_experiment.py  # reduced 12-document run
streamlit run app.py                 # dashboard: matrix / explorer / evaluation
pytest                               # 60 tests
```

## 7. Honest limits

- **Synthetic everything.** Documents, secrets, pipeline operators
  and the translator's dictionary are seeded simulations with
  declared parameters. The numbers validate the audit instrument
  and the qualitative stage/format pattern; they are not
  measurements of any production pipeline or model.
- **Ground truth is recoverability under a declared inverse set.**
  The oracle inverts spacing, reversal, chunk splits, base64 and
  digit words in both languages; a transformation outside that set
  (a paraphrasing summariser, a real MT system) would need its own
  inverse. The audit detector's gap is measured against exactly
  this declared oracle.
- **The stages are honest but simple.** A keyword-scored extractive
  summariser is not an LLM summariser; a 60-word dictionary is not
  a translator. Real stages are *less* predictable, which cuts both
  ways: more paraphrase kills, more paraphrase leaks.
- **The mailer's truncation point and the chunk width are declared
  constants** (420 chars, 110 chars); moving them moves the
  mail/chunk rows of the matrix. They are configuration in
  `data/scenarios.json`, not findings.

## 8. Repository layout

```
canary_meter/   generator, pipeline stages, detectors, evaluation, reports, CLI
data/           scenarios.json (experiment config), demo_case.json (demo ground truth)
examples/       run_audit.py + a captured sample report
notebooks/      01 demo run, 02 evaluation experiment (runnable .py)
scripts/        build_cases.py, reproduce_results.py (headline-drift guard)
results/        evaluation.json/.csv, evaluation_summary.md, HEADLINE.md
tests/          60 tests: generator, stages, detectors, evaluation, CLI, dashboard
app.py          Streamlit dashboard (survival matrix / canary explorer / evaluation)
```

## 9. Paper angle

"Where did the secret survive? Stage-wise canary survival as a
leakage audit for LLM data pipelines" — privacy/security
methodology workshops.

## 10. Author and licence

Amna Raheeba. MIT licence (see `LICENSE`).
