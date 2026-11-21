"""Headline-drift guard.

Re-runs the full seeded evaluation and compares the aggregate
headline numbers against the shipped results/evaluation.json.
Exits non-zero if any headline value moved by more than the
tolerance -- i.e. if the code no longer reproduces the published
results.

Run from the repository root:  python scripts/reproduce_results.py
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canary_meter.evaluate import run_evaluation
from canary_meter.models import FORMATS, SNAPSHOTS

TOLERANCE = 0.02


def headline_values(results):
    agg = results["aggregate"]
    values = {
        "overall_leak_rate": agg["overall_leak_rate"],
        "redactor_false_claim_rate": agg["redactor_false_claim_rate"],
    }
    for snap in SNAPSHOTS:
        for fmt in FORMATS:
            values["survival_%s_%s" % (snap, fmt)] = agg["survival"][snap][fmt]
        for name in ("audit", "grep"):
            values["recovery_%s_%s" % (snap, name)] = agg["recovery"][snap][name]
    for fmt in FORMATS:
        entry = agg["redactor"][fmt]
        values["redactor_kill_%s" % fmt] = entry["kill_rate"]
        if entry["false_claim_rate"] is not None:
            values["false_claim_%s" % fmt] = entry["false_claim_rate"]
    return values


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shipped_path = os.path.join(root, "results", "evaluation.json")
    with io.open(shipped_path, encoding="utf-8") as fh:
        shipped = json.load(fh)
    fresh = run_evaluation()
    expected = headline_values(shipped)
    actual = headline_values(fresh)
    failures = []
    for key in sorted(expected):
        if key not in actual:
            failures.append("%s missing from fresh run" % key)
        elif abs(expected[key] - actual[key]) > TOLERANCE:
            failures.append(
                "%s: shipped %.4f vs fresh %.4f"
                % (key, expected[key], actual[key])
            )
    if failures:
        print("HEADLINE DRIFT DETECTED:")
        for line in failures:
            print("  " + line)
        return 1
    print("OK: %d headline values reproduce within %.2f"
          % (len(expected), TOLERANCE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
