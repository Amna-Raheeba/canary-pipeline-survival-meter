"""Human-readable reports: demo audit, evaluation summary, headline."""

from .detect import audit_detect, grep_detect, oracle_detect
from .models import FORMATS, SNAPSHOTS


def _pct(x):
    return "%.1f%%" % (100.0 * x)


def document_report(document, run):
    """Audit report for one document's pipeline run."""
    lines = []
    lines.append("Canary survival audit -- %s" % document.doc_id)
    lines.append("")
    lines.append("%-28s %s" % ("canary (format / form)", "  ".join(
        "%-9s" % s for s in SNAPSHOTS)))
    for canary in document.canaries:
        marks = []
        for snap in SNAPSHOTS:
            found = oracle_detect(canary, run.snapshots[snap])
            marks.append("%-9s" % ("SURVIVES" if found else "dead"))
        lines.append(
            "%-28s %s"
            % ("%s (%s / %s)" % (canary.canary_id, canary.format,
                                 canary.planted_form), "  ".join(marks))
        )
    lines.append("")
    log = run.redact_log
    lines.append(
        "Redactor log: replaced %d match(es) %s; claims coverage of %s."
        % (log["total_replaced"], log["replaced"],
           ", ".join(log["claimed_formats"]))
    )
    leaked = [
        c.canary_id for c in document.canaries
        if oracle_detect(c, run.snapshots["mail"])
    ]
    lines.append(
        "Leaked into the mailed output: %s"
        % (", ".join(leaked) if leaked else "none")
    )
    missed = [
        c.canary_id for c in document.canaries
        if oracle_detect(c, run.snapshots["mail"])
        and not audit_detect(c, run.snapshots["mail"])
    ]
    lines.append(
        "Leaked but invisible to the audit detector: %s"
        % (", ".join(missed) if missed else "none")
    )
    grep_missed = [
        c.canary_id for c in document.canaries
        if oracle_detect(c, run.snapshots["mail"])
        and not grep_detect(c, run.snapshots["mail"])
    ]
    lines.append(
        "Leaked but invisible to verbatim grep: %s"
        % (", ".join(grep_missed) if grep_missed else "none")
    )
    return "\n".join(lines) + "\n"


def evaluation_summary(results):
    """Markdown summary of the full evaluation (evaluation_summary.md)."""
    agg = results["aggregate"]
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append(
        "%d documents, %d planted canaries (one per format per document), "
        "seeded and deterministic." % (results["documents"], agg["n_canaries"])
    )
    lines.append("")
    lines.append("## Stage x format survival (oracle ground truth)")
    lines.append("")
    lines.append("| stage | " + " | ".join(FORMATS) + " |")
    lines.append("|" + "---|" * (len(FORMATS) + 1))
    for snap in SNAPSHOTS:
        row = " | ".join(_pct(agg["survival"][snap][f]) for f in FORMATS)
        lines.append("| %s | %s |" % (snap, row))
    lines.append("")
    lines.append("## Detector recovery vs ground truth (share of survivors found)")
    lines.append("")
    lines.append("| stage | audit detector | verbatim grep |")
    lines.append("|---|---|---|")
    for snap in SNAPSHOTS:
        lines.append(
            "| %s | %s | %s |"
            % (snap, _pct(agg["recovery"][snap]["audit"]),
               _pct(agg["recovery"][snap]["grep"]))
        )
    lines.append("")
    lines.append("## Redactor honesty")
    lines.append("")
    lines.append("| format | entered redact | survived | kill rate | claimed | false-claim rate |")
    lines.append("|---|---|---|---|---|---|")
    for fmt in FORMATS:
        e = agg["redactor"][fmt]
        fcr = "-" if e["false_claim_rate"] is None else _pct(e["false_claim_rate"])
        lines.append(
            "| %s | %d | %d | %s | %s | %s |"
            % (fmt, e["entered"], e["survived"], _pct(e["kill_rate"]),
               "yes" if e["claimed"] else "no", fcr)
        )
    lines.append("")
    lines.append(
        "Overall redactor false-claim rate (claimed formats): %s"
        % _pct(agg["redactor_false_claim_rate"])
    )
    lines.append("")
    lines.append("## Killing stage attribution")
    lines.append("")
    for stage, count in agg["killing_stages"].items():
        lines.append("- %s: %d" % (stage, count))
    lines.append("")
    lines.append(
        "Overall leak rate at the mail stage: %s"
        % _pct(agg["overall_leak_rate"])
    )
    return "\n".join(lines) + "\n"


def headline(results):
    """Short headline markdown (HEADLINE.md)."""
    agg = results["aggregate"]
    mail = agg["survival"]["mail"]
    lines = []
    lines.append("# Headline results")
    lines.append("")
    lines.append(
        "Across %d seeded documents (%d planted canaries, 4 formats x "
        "verbatim/spaced/reversed plantings):"
        % (results["documents"], agg["n_canaries"])
    )
    lines.append("")
    for fmt in FORMATS:
        lines.append(
            "- %s survival into the mailed output: %s"
            % (fmt, _pct(mail[fmt]))
        )
    lines.append(
        "- Redactor false-claim rate (formats it claims to cover): %s"
        % _pct(agg["redactor_false_claim_rate"])
    )
    lines.append(
        "- Audit-detector recovery at the mail stage: %s; verbatim grep: %s"
        % (_pct(agg["recovery"]["mail"]["audit"]),
           _pct(agg["recovery"]["mail"]["grep"]))
    )
    lines.append(
        "- Overall leak rate: %s of planted canaries reach the recipient"
        % _pct(agg["overall_leak_rate"])
    )
    lines.append("")
    lines.append(
        "All numbers are measured on synthetic seeded documents; "
        "see README section 7 for limits."
    )
    return "\n".join(lines) + "\n"
