# -*- coding: utf-8 -*-
"""
How much of the rental picture the LTB record actually covers, and who reaches
it.

Three questions, all of which have been put to this analysis as objections and
all of which are answerable from public data:

  1. "How big is this next to the whole tenancy picture?"
     -> cases per year against Ontario's renter households, triangulated three
        ways and set beside the United States filing rate.

  2. "What about the disputes that never reach the Board?"
     -> the reasons recorded at the LTB against the reasons tenants themselves
        report to Statistics Canada. The two do not describe the same
        population, and the gap is the point.

  3. "Is this related to income?"
     -> per-FSA join of dispute rates to census income, rent burden and core
        housing need, with correlation coefficients.

Outputs (results/exposure/):
    exposure_rate.csv      the denominator answer, every route shown
    reason_mismatch.csv    LTB-recorded reasons vs tenant-reported reasons
    fsa_access_income.csv  per-FSA rates, ratios and census characteristics
    correlations.csv       correlation of each rate against each census measure
    README.md
"""
import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_pct

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "results" / "exposure"
CENSUS_PATH = BASE / "data" / "fsa_census_profile.csv"

# --- External reference figures, each with its source -----------------------
# Ontario renter households, 2021 Census. Read from the province-level Census
# Profile (98-401-X2021001, characteristic 1416). Summing the same
# characteristic across Ontario FSAs gives 1,725,025, a 55-household gap that
# is census random rounding, which is the check that both are the same measure.
ONTARIO_RENTER_HOUSEHOLDS = 1_724_970

# Tribunals Ontario 2024-25 Annual Report:
#   "the LTB received a total of 87,993 applications"
#   "Landlords filed 72,836 applications, while tenants filed 8,267 applications
#    through the Tribunals Ontario Portal. Additionally, 387 co-op applications
#    were filed using the Portal."
# https://tribunalsontario.ca/documents/TO/Tribunals_Ontario_2024-2025_Annual_Report.html
#
# Note the two do not reconcile: 72,836 + 8,267 + 387 = 81,490 against a total of
# 87,993, because the per-party figures count Portal filings only. So 72,836 is a
# FLOOR on landlord applications, not the full count, and the exposure rate derived
# from it is correspondingly conservative.
TO_APPLICATIONS_RECEIVED = 87_993
TO_LANDLORD_APPLICATIONS = 72_836  # Portal filings only; a floor
TO_TENANT_APPLICATIONS = 8_267
TO_PORTAL_TOTAL = 81_490

# Eviction Lab (Princeton), Eviction Tracking System, 2024: eviction filings per
# 100 renter households across tracked United States cities.
# https://evictionlab.org/ets-report-2024/
US_FILING_RATE_PCT = 8.0

# CMHC, "Towards Understanding the Magnitude of Evictions in Canada", July 2025,
# using Statistics Canada's Canadian Housing Survey 2021 and 2022: share of all
# renters evicted in the previous 12 months, counting formal and informal.
# https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-research/research-reports/2025/towards-understanding-magnitude-evictions-en.pdf
CMHC_EVICTION_RATE_PCT = 1.0

# Statistics Canada, Canadian Housing Survey 2021, reasons given by renters who
# reported being forced to move by a landlord.
# https://www150.statcan.gc.ca/n1/pub/11-627-m/11-627-m2022046-eng.htm
CHS_REASONS = {
    "Landlord sold the property": 37,
    "Landlord wanted the unit": 26,
    "Conflict with the landlord": 13,
    "Demolition, conversion or repairs": 10,
    "Behind on rent": 8,
}

# Census characteristics correlated against dispute rates.
CENSUS_MEASURES = {
    "median_household_income": "Median household income",
    "pct_tenant_core_housing_need": "% of tenants in core housing need",
    "pct_tenant_shelter_over_30pct": "% of tenants paying 30%+ on shelter",
    "pct_renter": "% of households renting",
    "average_monthly_rent": "Average monthly rent",
    "rent_to_income_ratio": "Annual rent as % of median income",
}

# Below this many renter households an FSA's rate swings wildly on a handful of
# cases, so it is excluded from correlations and rankings (kept in the CSV).
RELIABLE_RENTER_FLOOR = 500

# Minimum landlord cases before an FSA enters a correlation.
CORRELATION_CASE_FLOOR = 20

# Minimum landlord cases before an FSA is *named* in a ranking table. A ratio
# built on 20 cases moves by 0.05 on a single filing, so the extremes of a
# low-floor ranking are noise, not geography. At 100 the named areas are stable.
RANKING_CASE_FLOOR = 100


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else None


def spearman(xs, ys):
    """Rank correlation: robust to the long right tail in income and rates."""
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            average = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = average
            i = j + 1
        return out

    return pearson(ranks(xs), ranks(ys))


def load_census():
    census = {}
    with open(CENSUS_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            census[row["fsa"]] = {
                k: (float(v) if v else None) for k, v in row.items() if k != "fsa"
            }
    return census


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    orders = ltbdata.load_orders()
    cases = ltbdata.load_orders(unique_files=True)
    summary = ltbdata.summarise(cases)
    factor = summary["annualisation_factor"]
    census = load_census()

    # ---- 1. exposure rate --------------------------------------------------
    landlord_cases = summary["landlord_filed"]
    tenant_cases = summary["tenant_filed"]
    unique_addresses = len(
        {
            c["address"].upper().strip()
            for c in cases
            if c["filed_by"] == "landlord"
            and c["address"]
            and not ltbdata.is_placeholder_address(c["address"])
        }
    )

    routes = [
        (
            "This export, landlord-filed cases, annualised",
            landlord_cases * factor,
            f"{fmt_count(landlord_cases)} cases over {summary['days']} days x {factor:.3f}",
        ),
        (
            "This export, distinct rental units, annualised",
            unique_addresses * factor,
            "counts each address once, so a unit with two cases counts once",
        ),
        (
            "Tribunals Ontario, landlord applications received 2024-25",
            TO_LANDLORD_APPLICATIONS,
            "the Board's own published intake; Portal filings only, so a floor",
        ),
    ]
    rate_rows = [
        {
            "route": label,
            "cases_per_year": round(value),
            "renter_households": ONTARIO_RENTER_HOUSEHOLDS,
            "pct_of_renter_households": round(100 * value / ONTARIO_RENTER_HOUSEHOLDS, 2),
            "one_in": round(ONTARIO_RENTER_HOUSEHOLDS / value),
            "note": note,
        }
        for label, value, note in routes
    ]
    rate_rows.append(
        {
            "route": "United States, eviction filings 2024 (Eviction Lab)",
            "cases_per_year": "",
            "renter_households": "",
            "pct_of_renter_households": US_FILING_RATE_PCT,
            "one_in": round(100 / US_FILING_RATE_PCT),
            "note": "benchmark: filings per 100 renter households across tracked US cities",
        }
    )
    rate_rows.append(
        {
            "route": "Canada, renters actually evicted (CMHC/CHS, formal + informal)",
            "cases_per_year": "",
            "renter_households": "",
            "pct_of_renter_households": CMHC_EVICTION_RATE_PCT,
            "one_in": round(100 / CMHC_EVICTION_RATE_PCT),
            "note": "an application is not an eviction; most L1 cases end with the tenant paying",
        }
    )
    _write_csv(OUT_DIR / "exposure_rate.csv", rate_rows)

    # ---- 2. reason mismatch ------------------------------------------------
    landlord_codes = Counter(
        c["code"] for c in cases if c["filed_by"] == "landlord" and c["code"]
    )
    landlord_total = sum(landlord_codes.values())
    ltb_arrears_pct = 100 * landlord_codes["L1"] / landlord_total
    reason_rows = [
        {
            "reason": "Behind on rent",
            "pct_of_ltb_landlord_cases": round(ltb_arrears_pct, 1),
            "pct_of_tenant_reported_evictions": CHS_REASONS["Behind on rent"],
            "source_ltb": "L1 share of landlord-filed cases, this export",
            "source_survey": "Canadian Housing Survey 2021",
        },
        {
            "reason": "Every other reason combined",
            "pct_of_ltb_landlord_cases": round(100 - ltb_arrears_pct, 1),
            "pct_of_tenant_reported_evictions": 100 - CHS_REASONS["Behind on rent"],
            "source_ltb": "all non-L1 landlord-filed cases, this export",
            "source_survey": "Canadian Housing Survey 2021",
        },
    ]
    for reason, pct in CHS_REASONS.items():
        if reason == "Behind on rent":
            continue
        reason_rows.append(
            {
                "reason": reason,
                "pct_of_ltb_landlord_cases": "",
                "pct_of_tenant_reported_evictions": pct,
                "source_ltb": "not separately recorded; bundled inside L2",
                "source_survey": "Canadian Housing Survey 2021",
            }
        )
    _write_csv(OUT_DIR / "reason_mismatch.csv", reason_rows)

    # ---- 3. per-FSA access and income --------------------------------------
    by_fsa = defaultdict(Counter)
    for case in cases:
        if case["fsa"]:
            by_fsa[case["fsa"]][case["filed_by"]] += 1

    fsa_rows = []
    for fsa_code, counts in sorted(by_fsa.items()):
        profile = census.get(fsa_code)
        if not profile:
            continue
        renters = profile.get("households_renter")
        landlord_n = counts["landlord"]
        tenant_n = counts["tenant"]
        row = {
            "fsa": fsa_code,
            "landlord_filed": landlord_n,
            "tenant_filed": tenant_n,
            "total_cases": landlord_n + tenant_n + counts["co-op"],
            "renter_households": int(renters) if renters else "",
            "cases_per_1000_renter_households": (
                round(1000 * (landlord_n + tenant_n) / renters, 1) if renters else ""
            ),
            "landlord_cases_per_1000_renter_households": (
                round(1000 * landlord_n / renters, 1) if renters else ""
            ),
            "tenant_per_landlord_ratio": (
                round(tenant_n / landlord_n, 3) if landlord_n else ""
            ),
        }
        for key in CENSUS_MEASURES:
            value = profile.get(key)
            row[key] = value if value is not None else ""
        fsa_rows.append(row)
    _write_csv(OUT_DIR / "fsa_access_income.csv", fsa_rows)

    # ---- 4. correlations ---------------------------------------------------
    reliable = [
        r
        for r in fsa_rows
        if r["renter_households"] not in ("", None)
        and r["renter_households"] >= RELIABLE_RENTER_FLOOR
        and r["landlord_filed"] >= CORRELATION_CASE_FLOOR
    ]
    corr_rows = []
    for rate_key, rate_label in (
        ("landlord_cases_per_1000_renter_households",
         "Landlord cases per 1,000 renter households"),
        ("tenant_per_landlord_ratio",
         "Tenant cases per landlord case (who can use the Board)"),
    ):
        for measure_key, measure_label in CENSUS_MEASURES.items():
            pairs = [
                (r[measure_key], r[rate_key])
                for r in reliable
                if r[measure_key] not in ("", None) and r[rate_key] not in ("", None)
            ]
            if len(pairs) < 20:
                continue
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            corr_rows.append(
                {
                    "rate": rate_label,
                    "census_measure": measure_label,
                    "n_fsas": len(pairs),
                    "pearson_r": round(pearson(xs, ys), 3),
                    "spearman_rho": round(spearman(xs, ys), 3),
                }
            )
    _write_csv(OUT_DIR / "correlations.csv", corr_rows)

    _write_readme(
        summary, rate_rows, reason_rows, corr_rows, reliable,
        landlord_codes, landlord_total,
    )

    # ---- console -----------------------------------------------------------
    print(f"Window: {summary['first_date']} to {summary['last_date']} "
          f"({summary['days']} days, annualisation x{factor:.3f})\n")
    print("EXPOSURE: share of Ontario's 1,724,970 renter households per year")
    for r in rate_rows:
        one_in = f"1 in {r['one_in']}" if r["one_in"] else ""
        print(f"  {r['route'][:58]:58s} {r['pct_of_renter_households']:>6}%  {one_in}")
    print()
    print(f"REASON MISMATCH: 'behind on rent' is {ltb_arrears_pct:.1f}% of LTB landlord "
          f"cases but {CHS_REASONS['Behind on rent']}% of evictions tenants report")
    print()
    print(f"CORRELATIONS across {len(reliable)} FSAs:")
    for r in corr_rows:
        print(f"  {r['rate'][:42]:42s} vs {r['census_measure'][:38]:38s} "
              f"rho={r['spearman_rho']:+.3f}")
    print(f"\nSaved to {OUT_DIR}")


def _write_csv(path, rows):
    if not rows:
        return
    keys = list({k: None for row in rows for k in row})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(summary, rate_rows, reason_rows, corr_rows, reliable,
                  landlord_codes, landlord_total):
    ranked = sorted(
        [
            r
            for r in reliable
            if r["tenant_per_landlord_ratio"] != ""
            and r["landlord_filed"] >= RANKING_CASE_FLOOR
        ],
        key=lambda r: r["tenant_per_landlord_ratio"],
    )
    ratios = [r["tenant_per_landlord_ratio"] for r in ranked]
    median_ratio = statistics.median(ratios)
    p10 = ratios[int(0.10 * len(ratios))]
    p90 = ratios[int(0.90 * len(ratios))]
    strongest = max(corr_rows, key=lambda r: abs(r["spearman_rho"]))
    ltb_arrears_pct = 100 * landlord_codes["L1"] / landlord_total

    lines = [
        "# Exposure: how much of the picture the LTB record covers",
        "",
        "Built by `scripts/analyze_exposure.py`.",
        "",
        f"**Window.** This export covers {summary['first_date']} to "
        f"{summary['last_date']} - {summary['days']} days, not a full year and not all "
        f"time. Annual figures below are that window multiplied by "
        f"{summary['annualisation_factor']:.3f}. Ontario publishes one rolling "
        "current-year file, so no earlier period is available to compare against.",
        "",
        "## 1. How big is this next to the whole tenancy picture?",
        "",
        "Ontario has **1,724,970 renter households** (2021 Census). Three independent "
        "routes to the annual number of landlord-filed cases:",
        "",
        "| Route | Cases/year | Share of renter households | |",
        "|---|---:|---:|---|",
    ]
    for r in rate_rows[:3]:
        lines.append(
            f"| {r['route']} | {fmt_count(r['cases_per_year'])} "
            f"| {r['pct_of_renter_households']}% | 1 in {r['one_in']} |"
        )
    lines += [
        "",
        "The three agree, which matters: the middle route is this dataset counting "
        "distinct units, and the third is the Board's own published intake for a "
        "different year. **Roughly 1 in 24 Ontario renter households has a case filed "
        "against it each year.**",
        "",
        "Two comparisons that keep the number honest:",
        "",
        f"* The United States rate is **{US_FILING_RATE_PCT}%** of renter households "
        "(Eviction Lab, 2024) - about twice Ontario's. Ontario is a normal-sized "
        "eviction system by international standards. The findings elsewhere in this "
        "repository are about what it does, not about it being unusually large.",
        f"* Only about **{CMHC_EVICTION_RATE_PCT}%** of Canadian renters are actually "
        "evicted in a year (CMHC, 2025, counting formal and informal). An application "
        "is not an eviction: most non-payment cases end with the tenant paying and "
        "staying. Anyone quoting the filing rate as an eviction rate is wrong, in "
        "either direction.",
        "",
        "## 2. What about the disputes that never reach the Board?",
        "",
        "The LTB record and tenants' own accounts describe different populations:",
        "",
        "| Reason | Share of LTB landlord cases | Share of evictions tenants report |",
        "|---|---:|---:|",
        f"| Behind on rent | **{ltb_arrears_pct:.1f}%** | **8%** |",
        f"| Every other reason | {100 - ltb_arrears_pct:.1f}% | 92% |",
        "",
        "Non-payment dominates the Board because a landlord needs an order to recover "
        "money. The reasons tenants most often give for an eviction - the landlord "
        "sold (37%), wanted the unit (26%), or was renovating (10%) - mostly end with "
        "the tenant leaving on a notice, generating no order and no record. "
        "The Board's file is a biased sample of evictions, not a census of them, and "
        "it is biased toward the money cases in both directions.",
        "",
        "This cuts against a simple reading either way: it means the LTB record "
        "understates how often tenants lose housing, *and* it means the LTB record is "
        "not evidence about the frequency of the no-fault evictions it barely "
        "contains.",
        "",
        "*Caveat:* L2 bundles landlord's-own-use, demolition/renovation and "
        "conduct-based applications into one code, so the LTB side cannot be split "
        "further without reading the orders themselves.",
        "",
        "## 3. Is any of this related to income?",
        "",
        f"Across {len(reliable)} FSAs with enough renter households to give a stable "
        "rate, Spearman rank correlations:",
        "",
        "| Rate | Census measure | FSAs | Pearson r | Spearman rho |",
        "|---|---|---:|---:|---:|",
    ]
    for r in corr_rows:
        lines.append(
            f"| {r['rate']} | {r['census_measure']} | {r['n_fsas']} "
            f"| {r['pearson_r']:+.3f} | {r['spearman_rho']:+.3f} |"
        )
    lines += [
        "",
        "**Read these as weak.** The strongest association here is "
        f"{strongest['census_measure'].lower()} against "
        f"{strongest['rate'][0].lower()}{strongest['rate'][1:]}, at rho = "
        f"{strongest['spearman_rho']:+.3f} - which accounts for about "
        f"{100 * strongest['spearman_rho'] ** 2:.0f}% of the variation between areas. "
        "Two conclusions follow, and the second is the one people get wrong:",
        "",
        "1. **How often landlords file is close to unrelated to how rich an area is** "
        f"(rho = {next(r['spearman_rho'] for r in corr_rows if r['census_measure'] == 'Median household income' and r['rate'].startswith('Landlord')):+.3f}, "
        "about 1% of the variation). Rental disputes are not concentrated in poor "
        "postal codes in any strong sense. A claim in either direction that they are "
        "is not supported here.",
        "2. **Whether tenants themselves use the Board is modestly related to income** "
        "- higher-income, higher-rent areas produce more tenant-filed cases per "
        "landlord-filed case. Real, consistent across three separate census "
        "measures, and still small.",
        "",
        "### Who can actually use the Board",
        "",
        "Tenant-filed cases per landlord-filed case, by area. A low ratio means "
        "tenants in that area appear at the Board almost only as respondents. Only "
        f"FSAs with at least {RANKING_CASE_FLOOR} landlord cases are named: below "
        "that a single filing moves the ratio enough to invent a ranking.",
        "",
        "| | FSA | Landlord cases | Tenant cases | Ratio |",
        "|---|---|---:|---:|---:|",
    ]
    for r in ranked[:5]:
        lines.append(
            f"| lowest | {r['fsa']} | {r['landlord_filed']} | {r['tenant_filed']} "
            f"| {r['tenant_per_landlord_ratio']:.3f} |"
        )
    lines.append(f"| **median** | | | | **{median_ratio:.3f}** |")
    for r in ranked[-5:]:
        lines.append(
            f"| highest | {r['fsa']} | {r['landlord_filed']} | {r['tenant_filed']} "
            f"| {r['tenant_per_landlord_ratio']:.3f} |"
        )
    lines += [
        "",
        f"Between the 10th and 90th percentile of these {len(ranked)} areas the ratio "
        f"runs {p10:.3f} to {p90:.3f}, a **{p90 / p10:.0f}-fold** spread. That "
        "percentile range is quoted rather than the extremes because the single "
        "lowest area has almost no tenant filings at all and dividing by it produces "
        "an arbitrarily large multiple.",
        "",
        "## Method and limits",
        "",
        "* **Denominator.** Renter households, not residents. An area that is 80% "
        "renters will show more rental disputes per resident than one that is 20% "
        "renters without anything else differing, so a per-resident rate mostly "
        "measures tenure mix. Population-normalised versions of the maps are kept "
        "for continuity but the renter-household rate is the defensible one.",
        "* **Cases, not orders.** Counts here are unique file numbers. The raw export "
        "has more rows than cases because review and amended orders repeat a file.",
        "* **Correlation is not cause.** These are area-level associations. An "
        "association at the area level does not license a claim about any individual "
        "household or landlord in that area.",
        f"* **Small areas excluded.** FSAs under {RELIABLE_RENTER_FLOOR} renter "
        "households or 20 landlord cases are kept in the CSV but left out of "
        "correlations and rankings, where a handful of cases would swing the rate.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
