"""Notebook 2 (runnable .py): reduced evaluation experiment.

Runs the headline evaluation on a reduced document set (12 documents
instead of 48, so CI stays fast) and prints the stage x format
survival matrix, detector recovery and the redactor's false-claim
rate.  The shipped results/ come from the full 48-document run via
`python -m canary_meter evaluate`.
Run:  python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canary_meter.evaluate import run_evaluation
from canary_meter.models import FORMATS, SNAPSHOTS


def main():
    results = run_evaluation(n_documents=12)
    agg = results["aggregate"]
    print("Survival matrix (oracle):")
    print("  %-10s %s" % ("stage", "  ".join("%-10s" % f for f in FORMATS)))
    for snap in SNAPSHOTS:
        print("  %-10s %s" % (
            snap,
            "  ".join("%.3f     " % agg["survival"][snap][f] for f in FORMATS),
        ))
    print("Recovery at mail: audit %.3f, grep %.3f"
          % (agg["recovery"]["mail"]["audit"], agg["recovery"]["mail"]["grep"]))
    print("Redactor false-claim rate: %.3f" % agg["redactor_false_claim_rate"])
    print("Overall leak rate: %.3f" % agg["overall_leak_rate"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
