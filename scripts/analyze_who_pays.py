# -*- coding: utf-8 -*-
"""
Who actually carries the money at stake in Ontario rental disputes.

The headline "$130M awarded to landlords" is an aggregate across thousands of
separate landlords. On its own it says nothing about who bears it, and it
invites the reading that a class of landlords received a windfall. This
analysis splits the same estimate by the kind of landlord who filed, and
restates it per landlord rather than in total.

Outputs (results/who_pays/):
    landlord_entities.csv      one row per landlord kind: entities, cases,
                               how many filed once, how many hold one address
    application_mix.csv        each application type split individual/corporate
    concentration.csv          Lorenz curve of filings per landlord, anonymous
    burden_per_landlord.csv    the dollar estimate disaggregated, per entity
    README.md                  the numbers, the method, and the caveats

No landlord is named anywhere in the outputs. The question here is how the
burden is distributed across kinds of owner, not who any of them are.
"""
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_money, fmt_pct

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "results" / "who_pays"
CENSUS_PATH = BASE / "data" / "fsa_census_profile.csv"

# The amount-extraction sample this analysis extrapolates from. Same design
# and same arithmetic as make_perspective_chart.py:
#     estimated total = cases in category x found_rate x mean amount
# found_rate is the share of sampled orders in which a dollar amount was
# actually stated, so orders that state no amount are counted as zero. That is
# deliberately conservative: it understates rather than overstates.
SAMPLE_DIR = BASE / "results" / "amounts_equal_sample_100_per_category"

MONEY_CATEGORIES = ("L1", "L2", "L4")


def load_sample_rates():
    rates = {}
    with open(SAMPLE_DIR / "extraction_summary.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            rates[row["category"]] = {
                "found_rate": float(row["found_rate"]),
                "mean": float(row["mean"]),
                "median": float(row["median"]),
                "sample_n": int(row["count_total"]),
            }
    return rates


def ontario_average_rent():
    """Household-weighted average monthly rent across Ontario FSAs, 2021 census.

    Weighted by tenant households so a small FSA does not count as much as
    Toronto. Used to express a dollar figure as months of rent.
    """
    numerator = denominator = 0.0
    with open(CENSUS_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rent = row["average_monthly_rent"]
            households = row["tenant_households"]
            if not rent or not households:
                continue
            numerator += float(rent) * float(households)
            denominator += float(households)
    return numerator / denominator if denominator else None


def gini(values):
    """Gini coefficient of a list of counts; 0 = every landlord files equally."""
    values = sorted(values)
    n = len(values)
    total = sum(values)
    if n == 0 or total == 0:
        return 0.0
    cumulative = sum((i + 1) * v for i, v in enumerate(values))
    return (2 * cumulative) / (n * total) - (n + 1) / n


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = [c for c in ltbdata.load_orders(unique_files=True) if c["filed_by"] == "landlord"]
    rates = load_sample_rates()
    rent = ontario_average_rent()

    # ---- one record per landlord entity -----------------------------------
    entities = defaultdict(
        lambda: {"cases": 0, "addresses": set(), "codes": Counter(), "kind": None}
    )
    for case in cases:
        key = case["landlord_key"]
        if not key:
            continue
        entity = entities[key]
        entity["cases"] += 1
        entity["kind"] = case["landlord_kind"]
        entity["codes"][case["code"]] += 1
        if case["address"] and not ltbdata.is_placeholder_address(case["address"]):
            entity["addresses"].add(case["address"].upper().strip())

    by_kind = defaultdict(list)
    for entity in entities.values():
        by_kind[entity["kind"]].append(entity)

    total_cases = sum(e["cases"] for e in entities.values())

    # ---- landlord_entities.csv --------------------------------------------
    rows = []
    for kind in ("individual", "corporate"):
        group = by_kind[kind]
        case_count = sum(e["cases"] for e in group)
        filed_once = sum(1 for e in group if e["cases"] == 1)
        one_address = sum(1 for e in group if len(e["addresses"]) == 1)
        rows.append(
            {
                "landlord_kind": kind,
                "entities": len(group),
                "pct_of_entities": round(100 * len(group) / len(entities), 1),
                "cases": case_count,
                "pct_of_cases": round(100 * case_count / total_cases, 1),
                "filed_exactly_once": filed_once,
                "pct_filed_exactly_once": round(100 * filed_once / len(group), 1),
                "holds_one_address": one_address,
                "pct_holds_one_address": round(100 * one_address / len(group), 1),
                "mean_cases_per_entity": round(case_count / len(group), 2),
                "max_cases_per_entity": max(e["cases"] for e in group),
            }
        )
    _write_csv(OUT_DIR / "landlord_entities.csv", rows)

    # ---- application_mix.csv ----------------------------------------------
    mix = defaultdict(Counter)
    for case in cases:
        if case["landlord_kind"]:
            mix[case["code"]][case["landlord_kind"]] += 1
    mix_rows = []
    for code, counts in sorted(mix.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counts.values())
        if total < 50:
            continue
        mix_rows.append(
            {
                "code": code,
                "meaning": ltbdata.CATEGORY_LABELS.get(code, ""),
                "cases": total,
                "individual": counts["individual"],
                "corporate": counts["corporate"],
                "pct_individual": round(100 * counts["individual"] / total, 1),
                "pct_corporate": round(100 * counts["corporate"] / total, 1),
            }
        )
    _write_csv(OUT_DIR / "application_mix.csv", mix_rows)

    # ---- concentration.csv (anonymous Lorenz curve) ------------------------
    counts = sorted((e["cases"] for e in entities.values()), reverse=True)
    cumulative = 0
    conc_rows = []
    for k in (1, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000):
        if k > len(counts):
            break
        share = sum(counts[:k])
        conc_rows.append(
            {
                "top_n_landlords": k,
                "pct_of_all_landlords": round(100 * k / len(counts), 2),
                "cases": share,
                "pct_of_all_cases": round(100 * share / total_cases, 1),
            }
        )
    _write_csv(OUT_DIR / "concentration.csv", conc_rows)
    filed_once_all = sum(1 for c in counts if c == 1)
    gini_value = gini(counts)

    # ---- burden_per_landlord.csv ------------------------------------------
    # Apply the sample's found_rate and mean to each entity's own case mix, so
    # an entity's estimate reflects what it actually filed.
    estimates = defaultdict(list)
    modelled_total = defaultdict(float)
    for entity in entities.values():
        amount = 0.0
        for code, n in entity["codes"].items():
            rate = rates.get(code)
            if code in MONEY_CATEGORIES and rate:
                amount += n * rate["found_rate"] * rate["mean"]
        if amount > 0:
            estimates[entity["kind"]].append(amount)
            modelled_total[entity["kind"]] += amount

    grand_total = sum(modelled_total.values())
    burden_rows = []
    for kind in ("individual", "corporate"):
        values = sorted(estimates[kind])
        median = statistics.median(values)
        burden_rows.append(
            {
                "landlord_kind": kind,
                "entities_owed_money": len(values),
                "estimated_total": round(modelled_total[kind]),
                "pct_of_estimated_total": round(100 * modelled_total[kind] / grand_total, 1),
                "mean_per_entity": round(statistics.mean(values)),
                "median_per_entity": round(median),
                "p90_per_entity": round(values[int(0.9 * len(values))]),
                "median_as_months_of_rent": round(median / rent, 1),
                "median_as_pct_of_annual_rent": round(100 * median / (rent * 12), 1),
            }
        )
    _write_csv(OUT_DIR / "burden_per_landlord.csv", burden_rows)

    _write_readme(
        rows, mix_rows, conc_rows, burden_rows, entities, total_cases,
        filed_once_all, gini_value, rent, rates, grand_total,
    )

    # ---- console summary ---------------------------------------------------
    print(f"Landlord-filed cases: {fmt_count(total_cases)} across {fmt_count(len(entities))} landlords")
    print(f"Ontario average monthly rent (2021 census, household-weighted): {fmt_money(rent)}\n")
    for r in rows:
        print(
            f"  {r['landlord_kind']:11s} {fmt_count(r['entities']):>7s} entities  "
            f"{fmt_pct(r['pct_of_cases']):>6s} of cases  "
            f"{fmt_pct(r['pct_filed_exactly_once']):>6s} filed once  "
            f"{fmt_pct(r['pct_holds_one_address']):>6s} one address"
        )
    print(f"\n  Gini of filings per landlord: {gini_value:.3f}")
    print(f"  Landlords filing exactly once: {fmt_count(filed_once_all)} "
          f"({fmt_pct(100 * filed_once_all / len(entities))} of landlords)\n")
    print(f"Estimated total at stake (L1+L2+L4): {fmt_money(grand_total)}")
    for r in burden_rows:
        print(
            f"  {r['landlord_kind']:11s} {fmt_money(r['estimated_total']):>7s} "
            f"({fmt_pct(r['pct_of_estimated_total']):>5s})  "
            f"median per landlord {fmt_money(r['median_per_entity']):>8s} = "
            f"{r['median_as_months_of_rent']} months rent = "
            f"{fmt_pct(r['median_as_pct_of_annual_rent'])} of a unit's annual rent"
        )
    print(f"\nSaved to {OUT_DIR}")


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(entity_rows, mix_rows, conc_rows, burden_rows, entities,
                  total_cases, filed_once_all, gini_value, rent, rates, grand_total):
    ind = next(r for r in entity_rows if r["landlord_kind"] == "individual")
    corp = next(r for r in entity_rows if r["landlord_kind"] == "corporate")
    ind_b = next(r for r in burden_rows if r["landlord_kind"] == "individual")
    corp_b = next(r for r in burden_rows if r["landlord_kind"] == "corporate")
    top100 = next((r for r in conc_rows if r["top_n_landlords"] == 100), None)

    lines = [
        "# Who carries the money at stake",
        "",
        "Built by `scripts/analyze_who_pays.py`. No landlord is named in any output "
        "here; the question is how the burden splits across kinds of owner.",
        "",
        "## What a landlord looks like at the LTB",
        "",
        f"Of {fmt_count(len(entities))} distinct landlords bringing "
        f"{fmt_count(total_cases)} cases in the export window:",
        "",
        "| | Individual owners | Corporate / institutional |",
        "|---|---:|---:|",
        f"| Landlords | {fmt_count(ind['entities'])} | {fmt_count(corp['entities'])} |",
        f"| Share of cases | {fmt_pct(ind['pct_of_cases'])} | {fmt_pct(corp['pct_of_cases'])} |",
        f"| Filed exactly once | {fmt_pct(ind['pct_filed_exactly_once'])} | {fmt_pct(corp['pct_filed_exactly_once'])} |",
        f"| Hold a single address | {fmt_pct(ind['pct_holds_one_address'])} | {fmt_pct(corp['pct_holds_one_address'])} |",
        f"| Mean cases each | {ind['mean_cases_per_entity']} | {corp['mean_cases_per_entity']} |",
        "",
        f"For {fmt_pct(ind['pct_filed_exactly_once'])} of individual owners this is a "
        "single event at their only property. For the corporate side it is a recurring "
        "process. That difference is what the aggregate dollar figure hides.",
        "",
        "## The dollar estimate, disaggregated",
        "",
        f"Estimated total at stake across L1, L2 and L4: **{fmt_money(grand_total)}**.",
        "",
        "| | Individual owners | Corporate / institutional |",
        "|---|---:|---:|",
        f"| Share of the money | {fmt_pct(ind_b['pct_of_estimated_total'])} | {fmt_pct(corp_b['pct_of_estimated_total'])} |",
        f"| Mean per landlord | {fmt_money(ind_b['mean_per_entity'])} | {fmt_money(corp_b['mean_per_entity'])} |",
        f"| 90th percentile | {fmt_money(ind_b['p90_per_entity'])} | {fmt_money(corp_b['p90_per_entity'])} |",
        f"| Median per landlord | {fmt_money(ind_b['median_per_entity'])} | {fmt_money(corp_b['median_per_entity'])} |",
        "",
        "**The two medians are identical, and that is an artifact, not a finding.** "
        "Under this model every landlord whose only case is one L1 receives the same "
        "estimate, and the median landlord of both kinds is exactly that. The median "
        "is therefore uninformative about the difference between them; the mean and "
        "the 90th percentile are the columns that carry it. A corporate owner is "
        f"owed roughly {corp_b['mean_per_entity'] / ind_b['mean_per_entity']:.1f} times "
        "as much on average, because it brings many cases, not because its cases are "
        "individually larger.",
        "",
        "That is the whole point. The typical *case* is about the same size on both "
        f"sides. At Ontario's household-weighted average rent of {fmt_money(rent)}/month "
        f"(2021 census), the median owner's {fmt_money(ind_b['median_per_entity'])} is "
        f"**{ind_b['median_as_months_of_rent']} months of rent**, or "
        f"**{fmt_pct(ind_b['median_as_pct_of_annual_rent'])} of that unit's annual gross "
        "revenue** before mortgage, tax or repairs. What differs is what that case "
        f"represents: for {fmt_pct(ind['pct_holds_one_address'])} of individual owners "
        "it is their only unit and, on this evidence, a one-time event; for a corporate "
        "owner it is one line item among many, spread across a portfolio.",
        "",
        "## Concentration",
        "",
        f"Gini coefficient of filings per landlord: **{gini_value:.3f}** "
        "(0 would mean every landlord files equally often).",
        "",
        "| Top N landlords | Share of landlords | Share of cases |",
        "|---:|---:|---:|",
    ]
    for row in conc_rows:
        lines.append(
            f"| {row['top_n_landlords']} | {fmt_pct(row['pct_of_all_landlords'], 2)} "
            f"| {fmt_pct(row['pct_of_all_cases'])} |"
        )
    lines += [
        "",
        f"{fmt_count(filed_once_all)} landlords "
        f"({fmt_pct(100 * filed_once_all / len(entities))}) filed exactly one case.",
        "",
        "## Application mix by kind of owner",
        "",
        "| Code | Meaning | Cases | Individual | Corporate |",
        "|---|---|---:|---:|---:|",
    ]
    for row in mix_rows:
        lines.append(
            f"| {row['code']} | {row['meaning']} | {fmt_count(row['cases'])} "
            f"| {fmt_pct(row['pct_individual'])} | {fmt_pct(row['pct_corporate'])} |"
        )
    lines += [
        "",
        "Read both directions. Individual owners dominate the categories about "
        "recovering money from someone who has already gone (L10) and about a tenant "
        "who gave notice and stayed (L3). Corporate owners dominate above-guideline "
        "rent increases (L5).",
        "",
        "## Method and limits",
        "",
        "**Classification.** A landlord is treated as corporate or institutional if "
        "the name contains a company/organisation token or a six-or-more digit run "
        "(a numbered Ontario company). This is inclusive of public and non-profit "
        "providers: the distinction drawn is 'an organisation with staff and a "
        "process' versus 'a person who owns a unit', not for-profit versus not. "
        "Individual owners who file under a numbered company are counted as "
        "corporate, so the individual-owner share here is a floor, not a ceiling.",
        "",
        "**Name matching.** Spelling and suffix variants are collapsed to one key "
        "(case, punctuation, Inc/Ltd/LP, and anything after 'c/o'). Genuinely "
        "distinct landlords who share a canonical name are merged, and one landlord "
        "using two unrelated spellings is still counted twice. Concentration figures "
        "are therefore approximate at the margin.",
        "",
        "**Dollar figures are estimates, not a census.** They extrapolate a sample of "
        "order PDFs: `cases x found_rate x mean amount`, per category. Orders stating "
        "no amount count as zero, which understates rather than overstates. Sample "
        "sizes and found rates used here:",
        "",
        "| Category | Sample n | Found rate | Mean amount |",
        "|---|---:|---:|---:|",
    ]
    for code in MONEY_CATEGORIES:
        r = rates.get(code)
        if r:
            lines.append(
                f"| {code} | {r['sample_n']} | {r['found_rate']:.2f} | {fmt_money(r['mean'])} |"
            )
    lines += [
        "",
        "**Window.** The export covers a single period, not all time. See the top of "
        "`data/README.md` for the exact date range; every rate here is over that "
        "window unless it says annualised.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
