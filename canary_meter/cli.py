"""Command line interface: demo and evaluate."""

import argparse
import csv
import io
import json
import os
import sys

from .evaluate import run_evaluation
from .generate import demo_document
from .models import FORMATS, SNAPSHOTS
from .pipeline import run_pipeline
from .report import document_report, evaluation_summary, headline


def run_demo():
    document = demo_document()
    run = run_pipeline(document)
    sys.stdout.write(document_report(document, run))
    return 0


def run_evaluate(out_dir):
    results = run_evaluation()
    os.makedirs(out_dir, exist_ok=True)
    with io.open(os.path.join(out_dir, "evaluation.json"), "w",
                 encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=True)
    with io.open(os.path.join(out_dir, "evaluation.csv"), "w",
                 encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "seed", "doc_id", "canary_id", "format", "planted_form",
            "rendering", "killing_stage", "leaked",
        ] + ["oracle_%s" % s for s in SNAPSHOTS]
          + ["audit_%s" % s for s in SNAPSHOTS]
          + ["grep_%s" % s for s in SNAPSHOTS])
        for r in results["records"]:
            writer.writerow(
                [r["seed"], r["doc_id"], r["canary_id"], r["format"],
                 r["planted_form"], r["rendering"],
                 r["killing_stage"] or "", int(r["leaked"])]
                + [int(r["stages"][s]["oracle"]) for s in SNAPSHOTS]
                + [int(r["stages"][s]["audit"]) for s in SNAPSHOTS]
                + [int(r["stages"][s]["grep"]) for s in SNAPSHOTS]
            )
    with io.open(os.path.join(out_dir, "evaluation_summary.md"), "w",
                 encoding="utf-8") as fh:
        fh.write(evaluation_summary(results))
    with io.open(os.path.join(out_dir, "HEADLINE.md"), "w",
                 encoding="utf-8") as fh:
        fh.write(headline(results))
    agg = results["aggregate"]
    print("Evaluated %d documents, %d canaries."
          % (results["documents"], agg["n_canaries"]))
    print("Overall leak rate: %.3f" % agg["overall_leak_rate"])
    print("Redactor false-claim rate: %.3f"
          % agg["redactor_false_claim_rate"])
    for fmt in FORMATS:
        print("  %-10s mail survival %.3f" % (fmt, agg["survival"]["mail"][fmt]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="canary_meter")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo")
    ev = sub.add_parser("evaluate")
    ev.add_argument("--out", default="results")
    args = parser.parse_args(argv)
    if args.command == "evaluate":
        return run_evaluate(args.out)
    return run_demo()


if __name__ == "__main__":
    sys.exit(main())
