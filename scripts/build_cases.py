"""Build the shipped data files: scenarios.json + demo_case.json.

Run from the repository root:  python scripts/build_cases.py
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canary_meter.generate import demo_document
from canary_meter.models import FORMATS, STAGES
from canary_meter.pipeline import (
    CHUNK_WIDTH,
    MAIL_MAX_CHARS,
    SUMMARY_KEEP,
)


def main():
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )
    os.makedirs(data_dir, exist_ok=True)
    scenarios = {
        "n_documents": 48,
        "base_seed": 20261121,
        "canaries_per_document": len(FORMATS),
        "formats": list(FORMATS),
        "stages": list(STAGES),
        "chunk_width": CHUNK_WIDTH,
        "summary_keep": SUMMARY_KEEP,
        "mail_max_chars": MAIL_MAX_CHARS,
    }
    with io.open(os.path.join(data_dir, "scenarios.json"), "w",
                 encoding="utf-8") as fh:
        json.dump(scenarios, fh, indent=2, sort_keys=True)
    doc = demo_document()
    demo = {
        "doc_id": doc.doc_id,
        "seed": doc.seed,
        "sentences": doc.sentences,
        "canaries": [
            {
                "canary_id": c.canary_id,
                "format": c.format,
                "secret": c.secret,
                "planted_form": c.planted_form,
                "rendered": c.rendered,
                "rendering": c.rendering,
                "sentence_index": c.sentence_index,
            }
            for c in doc.canaries
        ],
    }
    with io.open(os.path.join(data_dir, "demo_case.json"), "w",
                 encoding="utf-8") as fh:
        json.dump(demo, fh, indent=2, sort_keys=True)
    print("Wrote data/scenarios.json and data/demo_case.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
