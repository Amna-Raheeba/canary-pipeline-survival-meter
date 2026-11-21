"""Notebook 1 (runnable .py): the demo document, audited live.

Pushes the fixed demo document through the six pipeline stages and
prints the per-canary survival table, the redactor log and the leak
list.  Run:  python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canary_meter.generate import demo_document
from canary_meter.pipeline import run_pipeline
from canary_meter.report import document_report


def main():
    document = demo_document()
    run = run_pipeline(document)
    sys.stdout.write(document_report(document, run))
    print("Stage outputs (lengths):")
    for name, text in run.snapshots.items():
        print("  %-10s %d chars" % (name, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
