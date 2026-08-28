# -*- coding: utf-8 -*-
"""
What actually happens to an application.

This is the question the rest of the site had been calling unanswerable. It is
unanswerable from the open-data export, which carries case metadata and no
disposition. It is answerable from the orders, and this reads them.

Two findings drive out of it, and they point in opposite directions, which is
why both are reported:

  * A landlord application ending in "terminated" mostly does not end the
    tenancy. Roughly half of terminations are voidable: the order says the
    tenancy ends UNLESS the tenant pays a stated sum by a stated date. Anyone
    citing filings, or even terminations, as a count of evictions is wrong.
  * A tenant bringing their own application is dismissed far more often than a
    landlord bringing one.

Reads results/case_details_all/outcomes.csv, which is drawn proportionally
across every application type, so these are caseload rates.

Outputs (results/outcomes/):
    outcome_by_side.csv     disposition split by who filed
    outcome_by_category.csv the same for the largest application types
    README.md
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_pct

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "results" / "case_details_all" / "outcomes.csv"
OUT_DIR = BASE / "results" / "outcomes"

# Display order and plain wording. The key is what the extractor emits.
LABELS = [
    ("terminated_voidable", "Terminated, but the tenant can pay to stay"),
    ("terminated", "Terminated"),
    ("money_only", "Ordered to pay, tenancy continues"),
    ("remedy_ordered", "Landlord ordered to do something"),
    ("dismissed", "Dismissed"),
    ("withdrawn", "Withdrawn"),
    ("other", "Not classified"),
]


def rows_for(rows, predicate):
    subset = [r for r in rows if predicate(r)]
    counts = Counter(r["outcome"] for r in subset)
    total = len(subset)
    return subset, counts, total


def main():
    if not IN_PATH.exists():
        raise SystemExit(
            f"{IN_PATH} not found. Run:\n"
            "  python scripts/extract_case_details.py --n 6000 --categories all\n"
            "  python scripts/extract_outcomes.py"
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(IN_PATH, encoding="utf-8-sig")))

    side_rows = []
    for side in ("landlord", "tenant"):
        subset, counts, total = rows_for(rows, lambda r, s=side: r["filed_by"] == s)
        if total < 50:
            continue
        record = {"filed_by": side, "orders": total}
        for key, label in LABELS:
            record[key] = round(100 * counts[key] / total, 1)
        record["on_consent"] = round(
            100 * sum(1 for r in subset if r["on_consent"] == "True") / total, 1)
        record["any_termination"] = round(
            100 * (counts["terminated"] + counts["terminated_voidable"]) / total, 1)
        record["voidable_share_of_terminations"] = (
            round(100 * counts["terminated_voidable"]
                  / (counts["terminated"] + counts["terminated_voidable"]), 1)
            if counts["terminated"] + counts["terminated_voidable"] else ""
        )
        side_rows.append(record)
    _write(OUT_DIR / "outcome_by_side.csv", side_rows)

    category_rows = []
    by_category = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
    for code, subset in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        if len(subset) < 100:
            continue
        counts = Counter(r["outcome"] for r in subset)
        total = len(subset)
        record = {
            "code": code,
            "meaning": ltbdata.CATEGORY_LABELS.get(code, ""),
            "filed_by": ltbdata.FILED_BY.get(code[0], ""),
            "orders": total,
        }
        for key, label in LABELS:
            record[key] = round(100 * counts[key] / total, 1)
        record["any_termination"] = round(
            100 * (counts["terminated"] + counts["terminated_voidable"]) / total, 1)
        category_rows.append(record)
    _write(OUT_DIR / "outcome_by_category.csv", category_rows)

    _write_readme(rows, side_rows, category_rows)

    landlord = next(r for r in side_rows if r["filed_by"] == "landlord")
    tenant = next(r for r in side_rows if r["filed_by"] == "tenant")
    print(f"Sample: {len(rows):,} orders read, drawn across every application type\n")
    print("DISPOSITION, by who filed")
    for record in side_rows:
        print(f"  {record['filed_by']}-filed (n={record['orders']:,})")
        for key, label in LABELS:
            if record[key]:
                print(f"     {label:44s} {record[key]:>5}%")
        print(f"     {'made on consent':44s} {record['on_consent']:>5}%")
    print()
    print(f"Landlord applications ending in any termination: "
          f"{landlord['any_termination']}%, of which "
          f"{landlord['voidable_share_of_terminations']}% are voidable")
    print(f"Dismissal rate: landlord-filed {landlord['dismissed']}%, "
          f"tenant-filed {tenant['dismissed']}%")
    print(f"\nSaved to {OUT_DIR}")


def _write(path, rows):
    if not rows:
        return
    keys = list({k: None for row in rows for k in row})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(rows, side_rows, category_rows):
    landlord = next(r for r in side_rows if r["filed_by"] == "landlord")
    tenant = next(r for r in side_rows if r["filed_by"] == "tenant")
    unclassified = round(
        100 * sum(1 for r in rows if r["outcome"] == "other") / len(rows), 1)

    lines = [
        "# What actually happens to an application",
        "",
        "Built by `scripts/analyze_outcomes.py` from "
        "`results/case_details_all/outcomes.csv`.",
        "",
        f"**Sample.** {len(rows):,} orders, drawn proportionally across every "
        "application type and read individually. The disposition is not in the "
        "open-data export; it is in the orders, which are public and linked from "
        "that export.",
        "",
        "## Disposition, by who filed",
        "",
        "| | Landlord-filed | Tenant-filed |",
        "|---|---:|---:|",
        f"| Orders read | {landlord['orders']:,} | {tenant['orders']:,} |",
    ] + [
        f"| {label} | {landlord[key]}% | {tenant[key]}% |"
        for key, label in LABELS
    ] + [
        f"| Made on consent | {landlord['on_consent']}% | {tenant['on_consent']}% |",
        "",
        "## The two things this settles",
        "",
        f"**A termination order mostly does not end a tenancy.** "
        f"{landlord['any_termination']}% of landlord applications end in a "
        f"termination of some kind, but "
        f"**{landlord['voidable_share_of_terminations']}% of those are voidable**: "
        "the order says the tenancy ends unless the tenant pays a stated sum by a "
        "stated date. Netting that out, roughly a quarter of landlord applications "
        "produce an unconditional termination. Anyone citing filings, or even "
        "terminations, as a count of evictions is overstating it, and this is the "
        "measurement that shows by how much.",
        "",
        f"**Tenants lose the cases they bring far more often than landlords lose "
        f"theirs.** {tenant['dismissed']}% of tenant-filed applications are "
        f"dismissed against {landlord['dismissed']}% of landlord-filed ones, a "
        f"{tenant['dismissed'] / landlord['dismissed']:.1f}-fold difference. A "
        f"further {tenant['remedy_ordered']}% end with the landlord ordered to do "
        f"something and {tenant['money_only']}% with a payment, so a tenant who "
        "brings a case is more likely to leave with nothing than with anything.",
        "",
        "This file is the reason the phrase 'an application is not an eviction' "
        "appears throughout this repository with a number attached rather than as an "
        "assertion.",
        "",
        "## By application type",
        "",
        "| Code | Meaning | Filed by | Orders | Any termination | Dismissed |",
        "|---|---|---|---:|---:|---:|",
    ] + [
        f"| {r['code']} | {r['meaning']} | {r['filed_by']} | {r['orders']:,} "
        f"| {r['any_termination']}% | {r['dismissed']}% |"
        for r in category_rows
    ] + [
        "",
        "## Method and limits",
        "",
        "* **Classified from the order text** by matching the operative language "
        "(\"the tenancy ... is terminated\", \"may void this order\", \"the "
        "application is dismissed\"), most specific first, because one order can "
        "contain several of those phrases.",
        f"* **{unclassified}% of orders are left unclassified** rather than forced "
        "into a bucket. That share is a real limit on everything above: the rates "
        "are shares of all orders read, so an unclassified order counts against "
        "every category rather than being quietly dropped.",
        "* **An order is not an enforcement.** Whether a termination was ever acted "
        "on, and whether money ordered was ever collected, is not in the record at "
        "all.",
        "* **Review and amended orders** appear as their own rows. An application "
        "reviewed and re-decided contributes twice, once per document.",
        "* **The PDFs this was read from are not kept in the repository.** They are "
        "re-downloadable from the URLs in the export by "
        "`scripts/extract_case_details.py`, and `scripts/extract_outcomes.py` "
        "re-reads whatever is cached locally.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
