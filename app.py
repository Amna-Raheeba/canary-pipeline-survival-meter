"""Streamlit dashboard for canary-pipeline-survival-meter.

Three tabs:
1. Survival matrix -- the seeded demo document pushed through the
   pipeline live: per-canary survival by stage, plus the aggregate
   stage x format matrix from the shipped evaluation.
2. Canary explorer -- pick one demo canary and inspect its text and
   detector verdicts at every stage.
3. Evaluation -- the shipped aggregate results from
   results/evaluation.json: survival, detector recovery and redactor
   honesty.

Run:  streamlit run app.py
"""

import io
import json
import os

import pandas as pd
import streamlit as st

from canary_meter.detect import audit_detect, grep_detect, oracle_detect
from canary_meter.generate import demo_document
from canary_meter.models import FORMATS, SNAPSHOTS
from canary_meter.pipeline import run_pipeline

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_results():
    path = os.path.join(HERE, "results", "evaluation.json")
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def tab_survival(document, run):
    st.subheader("Demo document: per-canary survival by stage")
    rows = []
    for canary in document.canaries:
        row = {"canary": canary.canary_id, "format": canary.format,
               "form": canary.planted_form}
        for snap in SNAPSHOTS:
            row[snap] = 1 if oracle_detect(canary, run.snapshots[snap]) else 0
        rows.append(row)
    st.dataframe(pd.DataFrame(rows))
    results = _load_results()
    if results is not None:
        st.subheader("Shipped evaluation: stage x format survival")
        agg = results["aggregate"]
        matrix = pd.DataFrame(
            dict((fmt, [agg["survival"][s][fmt] for s in SNAPSHOTS])
                 for fmt in FORMATS),
            index=SNAPSHOTS,
        )
        st.dataframe(matrix)
        st.bar_chart(matrix)


def tab_explorer(document, run):
    st.subheader("Canary explorer")
    labels = ["%s (%s)" % (c.canary_id, c.format) for c in document.canaries]
    choice = st.selectbox("Canary", labels)
    canary = document.canaries[labels.index(choice)]
    st.write("Planted form: %s | rendering: %s | carrier sentence: %d"
             % (canary.planted_form, canary.rendering, canary.sentence_index))
    for snap in SNAPSHOTS:
        text = run.snapshots[snap]
        st.markdown("**%s** -- oracle: %s | audit: %s | grep: %s"
                    % (snap,
                       oracle_detect(canary, text),
                       audit_detect(canary, text),
                       grep_detect(canary, text)))
        st.text(text[:600])


def tab_evaluation():
    st.subheader("Shipped evaluation results")
    results = _load_results()
    if results is None:
        st.warning("results/evaluation.json not found; run "
                   "`python -m canary_meter evaluate` first.")
        return
    agg = results["aggregate"]
    st.write("%d documents, %d canaries. Overall leak rate: %.3f. "
             "Redactor false-claim rate: %.3f."
             % (results["documents"], agg["n_canaries"],
                agg["overall_leak_rate"], agg["redactor_false_claim_rate"]))
    recovery = pd.DataFrame(
        dict((name, [agg["recovery"][s][name] for s in SNAPSHOTS])
             for name in ("audit", "grep")),
        index=SNAPSHOTS,
    )
    st.markdown("**Detector recovery vs ground truth**")
    st.dataframe(recovery)
    st.bar_chart(recovery)
    redactor = pd.DataFrame(
        [dict(format=fmt,
              kill_rate=agg["redactor"][fmt]["kill_rate"],
              false_claim_rate=agg["redactor"][fmt]["false_claim_rate"] or 0.0)
         for fmt in FORMATS]
    )
    st.markdown("**Redactor honesty by format**")
    st.dataframe(redactor)


def main():
    st.title("Canary Pipeline Survival Meter")
    st.write("Where does a planted secret survive your pipeline -- "
             "and which stage falsely claims to have redacted it?")
    document = demo_document()
    run = run_pipeline(document)
    tab1, tab2, tab3 = st.tabs(
        ["Survival matrix", "Canary explorer", "Evaluation"]
    )
    with tab1:
        tab_survival(document, run)
    with tab2:
        tab_explorer(document, run)
    with tab3:
        tab_evaluation()


if __name__ == "__main__":
    main()
