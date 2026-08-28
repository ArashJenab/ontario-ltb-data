# -*- coding: utf-8 -*-
"""
Read what each order actually decided, from the PDFs already on disk.

The site has been saying that whether an application ended in eviction,
payment, settlement or dismissal "cannot be answered from public data at all".
That is true of the open-data export, which carries only case metadata. It is
not true of the orders themselves, which are public, linked from that export,
and already downloaded for the amount and attendance work. This closes that
gap before the cached PDFs are deleted.

No downloading: this reads only what is already in pdfs/, and skips anything
missing. It re-uses the sample membership from the existing extractions, so
the proportional weighting of those samples carries over and the resulting
rates are caseload rates rather than rates over whatever happened to be
cached.

Outcome taxonomy, ordered most specific first, because a single order can
contain several of these phrases:

  dismissed             the application was dismissed
  terminated_voidable   tenancy terminated BUT the tenant may pay to stay
  terminated            tenancy terminated, or the tenant must move out
  money_only            an order to pay, with no termination
  remedy_ordered        a non-monetary obligation placed on the landlord
                        (repairs, compliance). This is what a tenant winning
                        usually looks like, and without it half the tenant-filed
                        orders fall into "other" and the dismissal rate reads
                        as though nothing else happened.
  other                 none of the above matched

Two flags are recorded independently of the outcome, because they cut across
it: whether the order was made on consent (the parties settled and asked the
Board to record it) and whether enforcement by the Sheriff is referenced.
"""
import argparse
import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parent.parent
PDF_DIR = BASE / "pdfs"

SAMPLES = {
    "all": BASE / "results" / "case_details_all" / "case_details_raw.csv",
    "money": BASE / "results" / "case_details" / "case_details_raw.csv",
}

DISMISSED = re.compile(
    r"application (?:is|was) dismissed|applications? (?:is|are) dismissed"
    r"|application is hereby dismissed", re.I)
VOIDABLE = re.compile(
    r"may void this order|void this order and continue the tenancy"
    r"|is terminated unless the Tenant voids", re.I)
TERMINATED = re.compile(
    r"tenancy (?:between[^.]{0,90})?is terminated"
    r"|must move out of the rental unit"
    r"|the tenancy is terminated", re.I)
MONEY = re.compile(r"shall pay to the (?:Landlord|Tenant)", re.I)
# An obligation placed on the landlord: pay, repair, comply, return a deposit.
# Written without a backslash escape on purpose. An earlier version of this
# line was generated through a shell heredoc that turned  into a literal
# backspace character, so the pattern silently matched nothing and every
# tenant-side remedy fell into "other".
REMEDY = re.compile(r"[Tt]he Landlord shall ", re.I)
CONSENT = re.compile(r"ordered on consent|order on consent|on consent that", re.I)
SHERIFF = re.compile(r"Court Enforcement Office \(Sheriff\)", re.I)
WITHDRAWN = re.compile(r"application (?:is|was) withdrawn|request to withdraw", re.I)


def classify(text):
    """(outcome, on_consent, sheriff_referenced)."""
    voidable = bool(VOIDABLE.search(text))
    terminated = bool(TERMINATED.search(text))
    if WITHDRAWN.search(text) and not terminated:
        outcome = "withdrawn"
    elif DISMISSED.search(text) and not terminated:
        outcome = "dismissed"
    elif terminated and voidable:
        outcome = "terminated_voidable"
    elif terminated:
        outcome = "terminated"
    elif MONEY.search(text):
        outcome = "money_only"
    elif REMEDY.search(text):
        outcome = "remedy_ordered"
    else:
        outcome = "other"
    return outcome, bool(CONSENT.search(text)), bool(SHERIFF.search(text))


def read_pdf(file_number):
    path = PDF_DIR / f"{file_number}.pdf"
    if not path.exists():
        return None
    try:
        with fitz.open(path) as doc:
            return " ".join("".join(page.get_text() for page in doc).split())
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", choices=sorted(SAMPLES) + ["both"], default="both")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    targets = SAMPLES if args.sample == "both" else {args.sample: SAMPLES[args.sample]}

    for name, path in targets.items():
        if not path.exists():
            print(f"skipping {name}: {path} not found")
            continue
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
        out_path = path.parent / "outcomes.csv"
        results = []
        missing = 0

        def work(row):
            text = read_pdf(row["file_number"])
            if not text or len(text) < 300:
                return None
            outcome, consent, sheriff = classify(text)
            return {
                "file_number": row["file_number"],
                "category": row["category"],
                "filed_by": {"L": "landlord", "T": "tenant", "C": "co-op"}.get(
                    (row["category"] or " ")[0], "unknown"),
                "doc_type": row.get("doc_type", ""),
                "outcome": outcome,
                "on_consent": consent,
                "sheriff_referenced": sheriff,
            }

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for i, result in enumerate(pool.map(work, rows), 1):
                if result is None:
                    missing += 1
                else:
                    results.append(result)
                if i % 500 == 0:
                    print(f"\r  {name}: {i}/{len(rows)}", end="", file=sys.stderr)
        print(file=sys.stderr)

        if results:
            with open(out_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(results[0]))
                writer.writeheader()
                writer.writerows(results)
        print(f"{name}: classified {len(results):,} of {len(rows):,} "
              f"({missing:,} PDFs not cached) -> {out_path}")


if __name__ == "__main__":
    main()
