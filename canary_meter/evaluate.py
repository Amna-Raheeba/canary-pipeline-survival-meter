"""The headline evaluation.

Runs the seeded document set through the pipeline and measures, per
stage and per canary format: oracle survival (ground truth),
audit-detector and grep recovery against that ground truth, the
redactor's kill rate and false-claim rate, the stage that kills each
canary, and the final leak rate at the mail stage.
"""

from .detect import audit_detect, grep_detect, oracle_detect
from .generate import experiment_documents
from .models import FORMATS, REDACTOR_CLAIMED_FORMATS, SNAPSHOTS, STAGES
from .pipeline import run_pipeline


def _mean(values):
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def evaluate_documents(documents):
    """Evaluate an explicit document list; returns the results dict."""
    records = []
    for doc in documents:
        run = run_pipeline(doc)
        for canary in doc.canaries:
            stages = {}
            for snap in SNAPSHOTS:
                text = run.snapshots[snap]
                stages[snap] = {
                    "oracle": oracle_detect(canary, text),
                    "audit": audit_detect(canary, text),
                    "grep": grep_detect(canary, text),
                }
            killing = None
            for stage in STAGES:
                if not stages[stage]["oracle"]:
                    killing = stage
                    break
            records.append(
                {
                    "doc_id": doc.doc_id,
                    "seed": doc.seed,
                    "canary_id": canary.canary_id,
                    "format": canary.format,
                    "planted_form": canary.planted_form,
                    "rendering": canary.rendering,
                    "stages": stages,
                    "killing_stage": killing,
                    "leaked": stages["mail"]["oracle"],
                }
            )
    return {"documents": len(documents), "records": records,
            "aggregate": _aggregate(records)}


def _aggregate(records):
    survival = {}
    for snap in SNAPSHOTS:
        survival[snap] = {}
        for fmt in FORMATS:
            rows = [r for r in records if r["format"] == fmt]
            survival[snap][fmt] = _mean(
                1.0 if r["stages"][snap]["oracle"] else 0.0 for r in rows
            )
    recovery = {}
    for snap in SNAPSHOTS:
        recovery[snap] = {}
        for name in ("audit", "grep"):
            hits = 0
            total = 0
            for r in records:
                if r["stages"][snap]["oracle"]:
                    total += 1
                    if r["stages"][snap][name]:
                        hits += 1
            recovery[snap][name] = (hits / float(total)) if total else 1.0
    redactor = {}
    for fmt in FORMATS:
        entered = [
            r for r in records
            if r["format"] == fmt and r["stages"]["chunk"]["oracle"]
        ]
        survived = [
            r for r in entered if r["stages"]["redact"]["oracle"]
        ]
        entry = {
            "entered": len(entered),
            "survived": len(survived),
            "kill_rate": (
                1.0 - len(survived) / float(len(entered))
            ) if entered else 0.0,
            "claimed": fmt in REDACTOR_CLAIMED_FORMATS,
            "false_claim_rate": None,
        }
        if entry["claimed"] and entered:
            entry["false_claim_rate"] = len(survived) / float(len(entered))
        redactor[fmt] = entry
    claimed = [redactor[f] for f in REDACTOR_CLAIMED_FORMATS]
    claimed_entered = sum(e["entered"] for e in claimed)
    claimed_survived = sum(e["survived"] for e in claimed)
    killing = {}
    for stage in STAGES:
        killing[stage] = sum(
            1 for r in records if r["killing_stage"] == stage
        )
    killing["leaked"] = sum(1 for r in records if r["leaked"])
    return {
        "n_canaries": len(records),
        "survival": survival,
        "recovery": recovery,
        "redactor": redactor,
        "redactor_false_claim_rate": (
            claimed_survived / float(claimed_entered)
        ) if claimed_entered else 0.0,
        "killing_stages": killing,
        "leak_rate": {
            fmt: survival["mail"][fmt] for fmt in FORMATS
        },
        "overall_leak_rate": _mean(
            1.0 if r["leaked"] else 0.0 for r in records
        ),
    }


def run_evaluation(n_documents=48, base_seed=20261121):
    """Run the full seeded headline evaluation."""
    documents = experiment_documents(n_documents, base_seed)
    results = evaluate_documents(documents)
    results["config"] = {
        "n_documents": n_documents,
        "base_seed": base_seed,
        "canaries_per_document": len(FORMATS),
    }
    return results
