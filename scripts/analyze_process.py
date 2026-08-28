# -*- coding: utf-8 -*-
"""
Who turns up to a hearing, and who has someone acting for them.

Reads results/case_details_all/, a sample drawn proportionally across every
application type rather than only the landlord money categories. That
distinction is the whole point of this file. An earlier version of this
analysis computed attendance from an L1/L2/L4-only sample and reported
"tenants attend 52%" as a fact about hearings. It was not: in every order in
that sample the landlord is the applicant and the tenant the respondent, so it
measured one side of the docket and called it the whole.

Split by who actually brought the application, the question becomes answerable:
is a party absent because of who they are, or because of which side of a given
case they are on?

Outputs (results/process/):
    attendance_by_filer.csv   each party's attendance and representation,
                              split by whether a landlord or a tenant filed
    attendance_overall.csv    the same across the whole caseload
    README.md
"""
import csv
from collections import defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_pct

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "results" / "case_details_all" / "case_details_raw.csv"
OUT_DIR = BASE / "results" / "process"


def filer_of(code):
    """'landlord', 'tenant' or 'co-op' from an application code."""
    return ltbdata.FILED_BY.get((code or " ")[0], "unknown")


def summarise(rows, party):
    """Attendance and representation for one party across a set of orders."""
    heard = [r for r in rows if r["hearing_sentence_found"] == "True"]
    if not heard:
        return None
    attended = sum(1 for r in heard if r[f"{party}_attended"] == "True")
    represented = sum(1 for r in heard if r[f"{party}_represented"] == "True")
    return {
        "party": party,
        "orders_naming_attendance": len(heard),
        "attended": attended,
        "pct_attended": round(100 * attended / len(heard), 1),
        "represented": represented,
        "pct_represented": round(100 * represented / len(heard), 1),
        "pct_represented_of_attending": (
            round(100 * represented / attended, 1) if attended else ""
        ),
    }


def main():
    if not IN_PATH.exists():
        raise SystemExit(
            f"{IN_PATH} not found. Run:\n"
            "  python scripts/extract_case_details.py --n 6000 --categories all"
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(open(IN_PATH, encoding="utf-8-sig")))
    for row in rows:
        row["filer"] = filer_of(row.get("category"))

    by_filer = defaultdict(list)
    for row in rows:
        by_filer[row["filer"]].append(row)

    filer_rows = []
    for filer in ("landlord", "tenant"):
        subset = by_filer.get(filer, [])
        heard = [r for r in subset if r["hearing_sentence_found"] == "True"]
        if len(heard) < 30:
            continue
        for party in ("landlord", "tenant"):
            summary = summarise(subset, party)
            if summary:
                filer_rows.append(
                    {
                        "filed_by": filer,
                        "orders_in_sample": len(subset),
                        **summary,
                    }
                )
    _write(OUT_DIR / "attendance_by_filer.csv", filer_rows)

    overall_rows = [
        {"scope": "all application types", **summarise(rows, party)}
        for party in ("landlord", "tenant")
        if summarise(rows, party)
    ]
    _write(OUT_DIR / "attendance_overall.csv", overall_rows)

    _write_readme(rows, filer_rows, overall_rows)

    print(f"Sample: {len(rows):,} orders across every application type")
    heard_total = sum(1 for r in rows if r["hearing_sentence_found"] == "True")
    print(f"  naming who attended: {heard_total:,} ({100 * heard_total / len(rows):.0f}%)\n")
    print("ATTENDANCE BY WHO FILED")
    for filer in ("landlord", "tenant"):
        subset = [r for r in filer_rows if r["filed_by"] == filer]
        if not subset:
            continue
        print(f"  {filer}-filed applications "
              f"(n={subset[0]['orders_naming_attendance']:,} naming attendance)")
        for row in subset:
            print(f"     {row['party']:9s} attended {row['pct_attended']:>5}%   "
                  f"represented {row['pct_represented']:>5}%   "
                  f"of those attending {row['pct_represented_of_attending']:>5}%")
    print("\nWHOLE CASELOAD")
    for row in overall_rows:
        print(f"  {row['party']:9s} attended {row['pct_attended']:>5}%   "
              f"represented {row['pct_represented']:>5}%")
    print(f"\nSaved to {OUT_DIR}")


def _write(path, rows):
    if not rows:
        return
    keys = list({k: None for row in rows for k in row})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(rows, filer_rows, overall_rows):
    def pick(filer, party):
        return next(
            (r for r in filer_rows if r["filed_by"] == filer and r["party"] == party),
            None,
        )

    ll_ll, ll_tt = pick("landlord", "landlord"), pick("landlord", "tenant")
    tt_ll, tt_tt = pick("tenant", "landlord"), pick("tenant", "tenant")
    overall = {r["party"]: r for r in overall_rows}
    heard_total = sum(1 for r in rows if r["hearing_sentence_found"] == "True")

    lines = [
        "# Who turns up, and who has help",
        "",
        "Built by `scripts/analyze_process.py` from "
        "`results/case_details_all/case_details_raw.csv`.",
        "",
        f"**Sample.** {len(rows):,} orders drawn across *every* application type in "
        "proportion to how common each is, so an unweighted rate over the sample is "
        f"a caseload rate. {heard_total:,} of them "
        f"({100 * heard_total / len(rows):.0f}%) carry the sentence naming who "
        "attended the hearing; the rest are excluded rather than scored as a "
        "no-show.",
        "",
        "## Why this needed its own sample",
        "",
        "An earlier version of this figure came from a sample of L1, L2 and L4 orders "
        "only. Those are landlord money cases, where the landlord is the applicant "
        "and the tenant the respondent in every single one. Reporting "
        '"tenants attend 52%" from that sample measured one side of the docket and '
        "called it the whole. Split by who actually filed, the question is whether a "
        "party is absent because of who they are or because of which side of the case "
        "they are on.",
        "",
        "## Attendance and representation, by who filed",
        "",
        "| Application filed by | Party | Attended | Represented | Represented, of those attending |",
        "|---|---|---:|---:|---:|",
    ]
    for row in filer_rows:
        lines.append(
            f"| {row['filed_by'].title()} | {row['party'].title()} "
            f"| {row['pct_attended']}% | {row['pct_represented']}% "
            f"| {row['pct_represented_of_attending']}% |"
        )
    lines += [
        "",
        "## What it says",
        "",
    ]
    if ll_ll and ll_tt and tt_ll and tt_tt:
        lines += [
            f"**The applicant shows up.** In landlord-filed cases the landlord "
            f"attends {ll_ll['pct_attended']}% of hearings and the tenant "
            f"{ll_tt['pct_attended']}%. In tenant-filed cases the tenant attends "
            f"{tt_tt['pct_attended']}% and the landlord {tt_ll['pct_attended']}%. So "
            "a good part of the attendance gap is structural: whoever brought the "
            "application turns up to it, and the respondent is likelier to be absent "
            "whichever side they are on.",
            "",
            f"**Representation does not work like that.** Landlords are represented "
            f"at {ll_ll['pct_represented']}% of the hearings they bring and "
            f"{tt_ll['pct_represented']}% of the ones brought against them. Tenants "
            f"are represented at {tt_tt['pct_represented']}% of the hearings they "
            f"bring and {ll_tt['pct_represented']}% of the ones brought against them. "
            "Being the applicant does not close that gap, and it is the finding worth "
            "carrying: a tenant is far less likely to have anyone speaking for them "
            "regardless of which side of the case they are on.",
            "",
            "## Across the whole caseload",
            "",
            "| Party | Attended | Represented |",
            "|---|---:|---:|",
        ]
        for party in ("landlord", "tenant"):
            row = overall.get(party)
            if row:
                lines.append(
                    f"| {party.title()} | {row['pct_attended']}% "
                    f"| {row['pct_represented']}% |"
                )
    lines += [
        "",
        "## Method and limits",
        "",
        "* **Read from the order text**, specifically the sentence naming who "
        'attended the hearing ("the Landlord\'s Legal Representative, ..., attended '
        'the hearing"). A representative is credited to whichever party is named '
        "next to them, within a window, so one side's paralegal is not counted for "
        "the other.",
        "* **Orders with no such sentence are excluded**, not counted as absences. "
        "Ex parte orders largely have no hearing to attend, and are a separate "
        "measure kept in `results/parties/decided_without_hearing.csv`.",
        "* **Attendance is not the same as participation.** The order records who "
        "was present, not whether they said anything or understood what was "
        "happening.",
        "* **This supersedes** the attendance figures in "
        "`results/burden/attendance.csv`, which came from a landlord-money-only "
        "sample and are left in place only so the correction is traceable.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
