# -*- coding: utf-8 -*-
"""
What a rental dispute actually costs, measured rather than modelled.

The dollar figures elsewhere in this repository extrapolate a sample mean to a
population. That answers "how much in total" but not "how much relative to what
this landlord takes in", which is the question that separates a loss a
portfolio owner absorbs from one an individual owner cannot. This script uses
the rent stated inside each order to answer the second question directly.

Reads results/case_details/case_details_raw.csv (produced by
extract_case_details.py) and writes results/burden/:

    months_owed.csv        arrears expressed in months of that unit's own rent
    months_distribution.csv how many orders fall in each band
    by_landlord_kind.csv   the same, split individual vs corporate
    attendance.csv         who turned up and who had a representative
    README.md

Every mean here carries a bootstrap confidence interval, because the whole
point of the larger sample was to stop quoting point estimates from a few
dozen documents.
"""
import csv
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_money, fmt_pct

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "results" / "case_details" / "case_details_raw.csv"
OUT_DIR = BASE / "results" / "burden"

BOOTSTRAP_ROUNDS = 2000
SEED = 20260827

# Bands for "how many months of rent had gone unpaid by the time an order
# issued". The first is the one that matters most for the tenant side and the
# last for the landlord side.
BANDS = [
    (0, 1, "Under 1 month"),
    (1, 2, "1 to 2 months"),
    (2, 3, "2 to 3 months"),
    (3, 6, "3 to 6 months"),
    (6, 12, "6 to 12 months"),
    (12, float("inf"), "Over 12 months"),
]


def bootstrap_ci(values, statistic=statistics.mean, rounds=BOOTSTRAP_ROUNDS, alpha=0.05):
    """Percentile bootstrap interval. Returns (point, low, high)."""
    if len(values) < 5:
        return (statistic(values) if values else None, None, None)
    rng = random.Random(SEED)
    n = len(values)
    draws = []
    for _ in range(rounds):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        draws.append(statistic(sample))
    draws.sort()
    lo = draws[int(alpha / 2 * rounds)]
    hi = draws[int((1 - alpha / 2) * rounds)]
    return (statistic(values), lo, hi)


def load_landlord_kinds():
    """file number -> individual/corporate, from the export."""
    kinds = {}
    for case in ltbdata.load_orders(unique_files=True):
        if case["landlord_kind"]:
            kinds[case["file_number"]] = case["landlord_kind"]
    return kinds


def main():
    if not IN_PATH.exists():
        raise SystemExit(
            f"{IN_PATH} not found. Run scripts/extract_case_details.py first."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kinds = load_landlord_kinds()

    rows = []
    with open(IN_PATH, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            try:
                row["amount"] = float(row["primary_amount"]) if row["primary_amount"] else None
                row["rent"] = float(row["monthly_rent"]) if row["monthly_rent"] else None
                row["months"] = (
                    float(row["months_of_rent_owed"]) if row["months_of_rent_owed"] else None
                )
            except ValueError:
                continue
            row["kind"] = kinds.get(row["file_number"])
            rows.append(row)

    with_months = [r for r in rows if r["months"] and 0 < r["months"] < 60]
    total = len(rows)
    print(f"Sample: {fmt_count(total)} orders read")
    print(f"  amount stated : {fmt_count(sum(1 for r in rows if r['amount']))} "
          f"({fmt_pct(100 * sum(1 for r in rows if r['amount']) / total)})")
    print(f"  rent stated   : {fmt_count(sum(1 for r in rows if r['rent']))} "
          f"({fmt_pct(100 * sum(1 for r in rows if r['rent']) / total)})")
    print(f"  both, usable  : {fmt_count(len(with_months))}\n")

    # ---- months owed, overall and by category ------------------------------
    out_rows = []
    for label, subset in [("All landlord money cases", with_months)] + [
        (f"{code} - {ltbdata.CATEGORY_LABELS.get(code, '')}",
         [r for r in with_months if r["category"] == code])
        for code in ("L1", "L2", "L4")
    ]:
        if len(subset) < 5:
            continue
        months = [r["months"] for r in subset]
        amounts = [r["amount"] for r in subset]
        rents = [r["rent"] for r in subset]
        mean_m, lo_m, hi_m = bootstrap_ci(months)
        mean_a, lo_a, hi_a = bootstrap_ci(amounts)
        out_rows.append({
            "scope": label,
            "n": len(subset),
            "median_months": round(statistics.median(months), 2),
            "mean_months": round(mean_m, 2),
            "mean_months_ci_low": round(lo_m, 2),
            "mean_months_ci_high": round(hi_m, 2),
            "median_amount": round(statistics.median(amounts)),
            "mean_amount": round(mean_a),
            "mean_amount_ci_low": round(lo_a),
            "mean_amount_ci_high": round(hi_a),
            "median_monthly_rent": round(statistics.median(rents)),
        })
    _write(OUT_DIR / "months_owed.csv", out_rows)

    # ---- distribution across bands -----------------------------------------
    band_rows = []
    months_all = [r["months"] for r in with_months]
    for low, high, label in BANDS:
        n = sum(1 for m in months_all if low <= m < high)
        band_rows.append({
            "band": label,
            "orders": n,
            "pct_of_orders": round(100 * n / len(months_all), 1),
        })
    _write(OUT_DIR / "months_distribution.csv", band_rows)

    # ---- by landlord kind ---------------------------------------------------
    kind_rows = []
    for kind in ("individual", "corporate"):
        subset = [r for r in with_months if r["kind"] == kind]
        if len(subset) < 5:
            continue
        months = [r["months"] for r in subset]
        amounts = [r["amount"] for r in subset]
        mean_m, lo_m, hi_m = bootstrap_ci(months)
        mean_a, lo_a, hi_a = bootstrap_ci(amounts)
        kind_rows.append({
            "landlord_kind": kind,
            "n": len(subset),
            "median_months": round(statistics.median(months), 2),
            "mean_months": round(mean_m, 2),
            "mean_months_ci_low": round(lo_m, 2),
            "mean_months_ci_high": round(hi_m, 2),
            "median_amount": round(statistics.median(amounts)),
            "mean_amount": round(mean_a),
            "mean_amount_ci_low": round(lo_a),
            "mean_amount_ci_high": round(hi_a),
            "median_rent": round(statistics.median([r["rent"] for r in subset])),
            "median_pct_of_annual_rent": round(
                100 * statistics.median(months) / 12, 1
            ),
        })
    _write(OUT_DIR / "by_landlord_kind.csv", kind_rows)

    # ---- attendance and representation ---------------------------------------
    heard = [r for r in rows if r["hearing_sentence_found"] == "True"]
    att_rows = []
    if heard:
        for party in ("landlord", "tenant"):
            attended = sum(1 for r in heard if r[f"{party}_attended"] == "True")
            represented = sum(1 for r in heard if r[f"{party}_represented"] == "True")
            att_rows.append({
                "party": party,
                "orders_with_a_hearing_line": len(heard),
                "attended": attended,
                "pct_attended": round(100 * attended / len(heard), 1),
                "had_a_representative": represented,
                "pct_represented": round(100 * represented / len(heard), 1),
                "pct_represented_of_those_attending": (
                    round(100 * represented / attended, 1) if attended else ""
                ),
            })
    _write(OUT_DIR / "attendance.csv", att_rows)

    _write_readme(out_rows, band_rows, kind_rows, att_rows, rows, with_months)

    # ---- console -------------------------------------------------------------
    print("MONTHS OF RENT OWED WHEN THE ORDER ISSUED")
    for r in out_rows:
        print(f"  {r['scope'][:40]:40s} n={r['n']:5d}  median {r['median_months']:5.2f}  "
              f"mean {r['mean_months']:5.2f} [{r['mean_months_ci_low']:.2f}, "
              f"{r['mean_months_ci_high']:.2f}]")
    print("\nDISTRIBUTION")
    for r in band_rows:
        print(f"  {r['band']:16s} {fmt_count(r['orders']):>6s}  {r['pct_of_orders']:>5}%")
    if kind_rows:
        print("\nBY LANDLORD KIND")
        for r in kind_rows:
            print(f"  {r['landlord_kind']:11s} n={r['n']:5d}  median {r['median_months']:.2f} months  "
                  f"mean amount {fmt_money(r['mean_amount'])} "
                  f"[{fmt_money(r['mean_amount_ci_low'])}, {fmt_money(r['mean_amount_ci_high'])}]")
    if att_rows:
        print("\nATTENDANCE (orders naming who attended)")
        for r in att_rows:
            print(f"  {r['party']:9s} attended {r['pct_attended']:>5}%   "
                  f"had a representative {r['pct_represented']:>5}%")
    print(f"\nSaved to {OUT_DIR}")


def _write(path, rows):
    if not rows:
        return
    keys = list({k: None for row in rows for k in row})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(out_rows, band_rows, kind_rows, att_rows, rows, with_months):
    overall = out_rows[0]
    under_one = next(r for r in band_rows if r["band"] == "Under 1 month")
    over_twelve = next(r for r in band_rows if r["band"] == "Over 12 months")

    lines = [
        "# What a dispute costs, measured from the orders themselves",
        "",
        "Built by `scripts/analyze_burden.py` from "
        "`results/case_details/case_details_raw.csv`.",
        "",
        "Orders state the rent inside the daily-rate calculation "
        '("$2,285.11 x 12, divided by 365 days"), which makes it possible to '
        "express what a landlord is owed in months of that unit's own rent rather "
        "than in dollars. That is the comparison that means the same thing to a "
        "landlord with one unit and one with a thousand.",
        "",
        "## Months of rent owed when the order issued",
        "",
        "| Scope | Orders | Median | Mean | 95% interval |",
        "|---|---:|---:|---:|---|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['scope']} | {r['n']:,} | {r['median_months']} | {r['mean_months']} "
            f"| {r['mean_months_ci_low']} to {r['mean_months_ci_high']} |"
        )
    lines += [
        "",
        f"The median landlord money case reaches an order with "
        f"**{overall['median_months']} months of rent** outstanding, on a unit "
        f"renting at a median of ${overall['median_monthly_rent']:,}/month.",
        "",
        "## How that is distributed",
        "",
        "| Months owed | Orders | Share |",
        "|---|---:|---:|",
    ]
    for r in band_rows:
        lines.append(f"| {r['band']} | {r['orders']:,} | {r['pct_of_orders']}% |")
    lines += [
        "",
        f"**{under_one['pct_of_orders']}% of orders are for less than a single "
        f"month's rent**, and **{over_twelve['pct_of_orders']}% are for more than a "
        "year's.** Both tails matter and they matter to different people: the short "
        "one is a tenancy ending over an amount smaller than one rent cheque, the "
        "long one is a landlord who has gone a year without income from the unit.",
        "",
    ]
    if kind_rows:
        lines += [
            "## Individual against corporate owners",
            "",
            "| | Orders | Median months | Mean amount | 95% interval |",
            "|---|---:|---:|---:|---|",
        ]
        for r in kind_rows:
            lines.append(
                f"| {r['landlord_kind'].title()} | {r['n']:,} | {r['median_months']} "
                f"| ${r['mean_amount']:,} | ${r['mean_amount_ci_low']:,} to "
                f"${r['mean_amount_ci_high']:,} |"
            )
        lines += [
            "",
            "Per case the two are close, which is the finding. The difference between "
            "the two kinds of landlord is not the size of an individual loss but how "
            "many of them each carries and what share of income each represents.",
            "",
        ]
    if att_rows:
        lines += [
            "## Who turned up, and who had help",
            "",
            "| Party | Attended | Had a representative |",
            "|---|---:|---:|",
        ]
        for r in att_rows:
            lines.append(
                f"| {r['party'].title()} | {r['pct_attended']}% | {r['pct_represented']}% |"
            )
        lines += [
            "",
            "Read from orders that name who attended the hearing. An order that does "
            "not carry that sentence is excluded rather than scored as a no-show, so "
            "these are rates among orders that say, not among all orders.",
            "",
        ]
    lines += [
        "## Method and limits",
        "",
        f"* **Sample.** {len(rows):,} orders drawn across L1, L2 and L4 in proportion "
        "to how common each is, so an unweighted mean over the sample is already a "
        "population mean. Seeded, so the draw is reproducible.",
        f"* **Coverage.** A rent figure is recoverable from about "
        f"{100 * sum(1 for r in rows if r['rent']) / len(rows):.0f}% of sampled orders "
        f"and both a rent and an amount from {len(with_months):,}. Orders that state "
        "neither are excluded, and there is no guarantee they resemble those that do.",
        "* **Intervals** are percentile bootstrap, 2,000 resamples. They express "
        "sampling error only. They say nothing about whether the extraction read each "
        "order correctly.",
        "* **Ratios above 60 months** are dropped as parse failures rather than "
        "believed.",
        "* **An amount ordered is not an amount collected.** Nothing in the public "
        "record says whether any of this was ever paid.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
