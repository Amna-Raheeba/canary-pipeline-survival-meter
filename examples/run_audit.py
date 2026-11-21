"""Example: audit one seeded document end to end.

Run from the repository root:  python examples/run_audit.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canary_meter.generate import build_document
from canary_meter.pipeline import run_pipeline
from canary_meter.report import document_report


def main():
    document = build_document(7)
    run = run_pipeline(document)
    sys.stdout.write(document_report(document, run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
