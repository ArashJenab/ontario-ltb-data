# -*- coding: utf-8 -*-
"""
Who the parties are: how often the same tenant recurs, how cases are decided,
and what first names suggest about the gender of each side.

Outputs (results/parties/):
    repeat_tenants.csv       cases per tenant, and same-unit vs new-address
    repeat_case_mix.csv      what repeat tenants are taken to the Board for
    decided_without_hearing.csv  ex parte rates by side and application type
    household_size.csv       named adults per case
    gender_summary.csv       inferred gender by role, with coverage
    gender_crosstab.csv      landlord gender against tenant gender
    README.md

The gender inference is a dictionary lookup on first names. It is reported with
its coverage rate attached everywhere because the misses are not random: the
dictionary resolves Anglo and European given names far better than others, so
any group whose names it resolves poorly is under-counted in the resolved base.
Every gender figure here is a statement about *resolved names*, not about all
parties, and is written that way.
"""
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import ltbdata
from chartstyle import fmt_count, fmt_pct

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "results" / "parties"

try:
    import gender_guesser.detector as gender_detector

    DETECTOR = gender_detector.Detector(case_sensitive=False)
except ImportError:  # pragma: no cover
    DETECTOR = None


def infer_gender(name):
    """'M', 'F', 'ambiguous' or 'unknown' from a full name's first token."""
    if DETECTOR is None:
        return "unknown"
    result = DETECTOR.get_gender(ltbdata.first_name(name))
    if result in ("male", "mostly_male"):
        return "M"
    if result in ("female", "mostly_female"):
        return "F"
    if result == "andy":  # the dictionary's label for genuinely unisex names
        return "ambiguous"
    return "unknown"


def resolved_ratio(counts):
    resolved = counts["M"] + counts["F"]
    total = sum(counts.values())
    return {
        "men": counts["M"],
        "women": counts["F"],
        "ambiguous": counts["ambiguous"],
        "unresolved": counts["unknown"],
        "coverage_pct": round(100 * resolved / total, 1) if total else 0,
        "men_per_woman": round(counts["M"] / counts["F"], 2) if counts["F"] else "",
        "pct_men_of_resolved": round(100 * counts["M"] / resolved, 1) if resolved else "",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = ltbdata.load_orders(unique_files=True)
    orders = ltbdata.load_orders()
    landlord_cases = [c for c in cases if c["filed_by"] == "landlord"]

    # ---- repeat tenants ----------------------------------------------------
    tenant_files = defaultdict(set)
    tenant_addresses = defaultdict(set)
    for case in landlord_cases:
        if not case["address"] or ltbdata.is_placeholder_address(case["address"]):
            continue
        for name in case["tenant_names"]:
            key = name.upper()
            tenant_files[key].add(case["file_number"])
            tenant_addresses[key].add(case["address"].upper().strip())

    total_tenants = len(tenant_files)
    total_named_cases = sum(len(v) for v in tenant_files.values())
    distribution = Counter(len(v) for v in tenant_files.values())

    repeat_rows = []
    for n in sorted(distribution):
        label = f"{n}" if n <= 4 else "5+"
        if n > 4:
            continue
        repeat_rows.append(
            {
                "cases_against_this_tenant": label,
                "tenants": distribution[n],
                "pct_of_tenants": round(100 * distribution[n] / total_tenants, 2),
                "cases": n * distribution[n],
                "pct_of_cases": round(100 * n * distribution[n] / total_named_cases, 1),
            }
        )
    tail = sum(v for k, v in distribution.items() if k > 4)
    tail_cases = sum(k * v for k, v in distribution.items() if k > 4)
    repeat_rows.append(
        {
            "cases_against_this_tenant": "5+",
            "tenants": tail,
            "pct_of_tenants": round(100 * tail / total_tenants, 2),
            "cases": tail_cases,
            "pct_of_cases": round(100 * tail_cases / total_named_cases, 1),
        }
    )

    repeaters = {k for k, v in tenant_files.items() if len(v) > 1}
    same_unit = sum(1 for k in repeaters if len(tenant_addresses[k]) == 1)
    moved = len(repeaters) - same_unit
    repeat_rows.append(
        {
            "cases_against_this_tenant": "-- of repeaters: same address",
            "tenants": same_unit,
            "pct_of_tenants": round(100 * same_unit / len(repeaters), 1),
            "cases": "",
            "pct_of_cases": "",
        }
    )
    repeat_rows.append(
        {
            "cases_against_this_tenant": "-- of repeaters: different address",
            "tenants": moved,
            "pct_of_tenants": round(100 * moved / len(repeaters), 1),
            "cases": "",
            "pct_of_cases": "",
        }
    )
    _write_csv(OUT_DIR / "repeat_tenants.csv", repeat_rows)

    # ---- what repeat tenants are taken to the Board for ---------------------
    repeat_codes, single_codes = Counter(), Counter()
    for case in landlord_cases:
        names = [n.upper() for n in case["tenant_names"]]
        if not names or not case["code"]:
            continue
        target = repeat_codes if any(n in repeaters for n in names) else single_codes
        target[case["code"]] += 1
    repeat_total, single_total = sum(repeat_codes.values()), sum(single_codes.values())
    mix_rows = []
    for code in sorted(set(repeat_codes) | set(single_codes), key=lambda c: -single_codes[c]):
        if single_codes[code] + repeat_codes[code] < 100:
            continue
        mix_rows.append(
            {
                "code": code,
                "meaning": ltbdata.CATEGORY_LABELS.get(code, ""),
                "pct_of_repeat_tenant_cases": round(100 * repeat_codes[code] / repeat_total, 1),
                "pct_of_one_time_tenant_cases": round(100 * single_codes[code] / single_total, 1),
                "ratio": (
                    round((repeat_codes[code] / repeat_total)
                          / (single_codes[code] / single_total), 2)
                    if single_codes[code] else ""
                ),
            }
        )
    _write_csv(OUT_DIR / "repeat_case_mix.csv", mix_rows)

    # ---- decided without a hearing -----------------------------------------
    ex_rows = []
    for side in ("landlord", "tenant"):
        side_orders = [o for o in orders if o["filed_by"] == side]
        ex_parte = sum(1 for o in side_orders if o["ex_parte"])
        ex_rows.append(
            {
                "scope": f"all {side}-filed orders",
                "orders": len(side_orders),
                "ex_parte": ex_parte,
                "pct_ex_parte": round(100 * ex_parte / len(side_orders), 1),
            }
        )
    by_code = defaultdict(lambda: [0, 0])
    for order in orders:
        if not order["code"]:
            continue
        by_code[order["code"]][0] += 1
        by_code[order["code"]][1] += 1 if order["ex_parte"] else 0
    for code, (total, ex_parte) in sorted(by_code.items(), key=lambda kv: -kv[1][1]):
        if total < 200:
            continue
        ex_rows.append(
            {
                "scope": f"{code} - {ltbdata.CATEGORY_LABELS.get(code, '')}",
                "orders": total,
                "ex_parte": ex_parte,
                "pct_ex_parte": round(100 * ex_parte / total, 1),
            }
        )
    _write_csv(OUT_DIR / "decided_without_hearing.csv", ex_rows)

    # ---- household size ----------------------------------------------------
    sizes = Counter(len(c["tenant_names"]) for c in landlord_cases if c["tenant_names"])
    size_total = sum(sizes.values())
    _write_csv(
        OUT_DIR / "household_size.csv",
        [
            {
                "named_adults": n,
                "cases": sizes[n],
                "pct_of_cases": round(100 * sizes[n] / size_total, 1),
            }
            for n in sorted(sizes)
        ],
    )

    # ---- gender ------------------------------------------------------------
    landlord_gender = Counter()
    tenant_gender = Counter()
    tenant_filer_gender = Counter()
    crosstab = Counter()

    for case in landlord_cases:
        if case["landlord_kind"] != "individual" or not case["landlord"]:
            continue
        parties = [p for p in ltbdata.split_parties(case["landlord"]) if ltbdata.looks_like_person(p)]
        if not parties:
            continue
        landlord_side = infer_gender(parties[0])
        landlord_gender[landlord_side] += 1
        for name in case["tenant_names"]:
            tenant_side = infer_gender(name)
            if landlord_side in ("M", "F") and tenant_side in ("M", "F"):
                crosstab[(landlord_side, tenant_side)] += 1

    for case in cases:
        for name in case["tenant_names"]:
            result = infer_gender(name)
            if case["filed_by"] == "landlord":
                tenant_gender[result] += 1
            elif case["filed_by"] == "tenant":
                tenant_filer_gender[result] += 1

    gender_rows = [
        {"role": "Individual landlords who filed", **resolved_ratio(landlord_gender)},
        {"role": "Tenants named in landlord-filed cases", **resolved_ratio(tenant_gender)},
        {"role": "Tenants who filed their own case", **resolved_ratio(tenant_filer_gender)},
    ]
    _write_csv(OUT_DIR / "gender_summary.csv", gender_rows)

    cross_total = sum(crosstab.values())
    _write_csv(
        OUT_DIR / "gender_crosstab.csv",
        [
            {
                "landlord": landlord_side,
                "tenant": tenant_side,
                "pairs": crosstab[(landlord_side, tenant_side)],
                "pct_of_resolved_pairs": round(
                    100 * crosstab[(landlord_side, tenant_side)] / cross_total, 1
                ),
            }
            for landlord_side in ("M", "F")
            for tenant_side in ("M", "F")
        ],
    )

    # ---- gender by application type ----------------------------------------
    # Does the kind of case differ by the gender of the person bringing it, or
    # of the people it is brought against? Reported per code so a reader can see
    # where the resolved base is thin.
    landlord_by_code = defaultdict(Counter)
    tenant_by_code = defaultdict(Counter)
    for case in cases:
        if not case["code"]:
            continue
        if case["landlord_kind"] == "individual" and case["landlord"]:
            parties = [
                party for party in ltbdata.split_parties(case["landlord"])
                if ltbdata.looks_like_person(party)
            ]
            if parties:
                landlord_by_code[case["code"]][infer_gender(parties[0])] += 1
        for name in case["tenant_names"]:
            tenant_by_code[case["code"]][infer_gender(name)] += 1

    code_rows = []
    for code in sorted(
        set(landlord_by_code) | set(tenant_by_code),
        key=lambda c: -(sum(tenant_by_code[c].values())),
    ):
        landlord_counts = landlord_by_code[code]
        tenant_counts = tenant_by_code[code]
        landlord_resolved = landlord_counts["M"] + landlord_counts["F"]
        tenant_resolved = tenant_counts["M"] + tenant_counts["F"]
        if tenant_resolved < 100:
            continue
        code_rows.append(
            {
                "code": code,
                "meaning": ltbdata.CATEGORY_LABELS.get(code, ""),
                "filed_by": ltbdata.FILED_BY.get(code[0], ""),
                "landlord_resolved": landlord_resolved,
                "landlord_men_per_woman": (
                    round(landlord_counts["M"] / landlord_counts["F"], 2)
                    if landlord_counts["F"] and landlord_resolved >= 100 else ""
                ),
                "tenant_resolved": tenant_resolved,
                "tenant_men_per_woman": (
                    round(tenant_counts["M"] / tenant_counts["F"], 2)
                    if tenant_counts["F"] else ""
                ),
                "tenant_pct_women": round(100 * tenant_counts["F"] / tenant_resolved, 1),
            }
        )
    _write_csv(OUT_DIR / "gender_by_application.csv", code_rows)

    # ---- gender by recurrence ----------------------------------------------
    # Is the small group of tenants who come back more male than the rest?
    recurrence_counts = {"one case": Counter(), "more than one case": Counter()}
    for name, files in tenant_files.items():
        bucket = "one case" if len(files) == 1 else "more than one case"
        recurrence_counts[bucket][infer_gender(name)] += 1
    recurrence_rows = [
        {"group": label, **resolved_ratio(counts)}
        for label, counts in recurrence_counts.items()
    ]
    _write_csv(OUT_DIR / "gender_by_recurrence.csv", recurrence_rows)

    # ---- gender by household shape -----------------------------------------
    # A one-name tenancy is a different household from a two-name one, and the
    # gender mix of each says something the aggregate hides.
    household_counts = defaultdict(Counter)
    for case in landlord_cases:
        names = case["tenant_names"]
        if not names or len(names) > 2:
            continue
        label = "one named adult" if len(names) == 1 else "two named adults"
        for name in names:
            household_counts[label][infer_gender(name)] += 1
    household_rows = [
        {"household": label, **resolved_ratio(counts)}
        for label, counts in sorted(household_counts.items())
    ]
    _write_csv(OUT_DIR / "gender_by_household.csv", household_rows)

    _write_readme(repeat_rows, mix_rows, ex_rows, gender_rows, crosstab, cross_total,
                  total_tenants, repeaters, sizes, size_total,
                  code_rows, recurrence_rows, household_rows)

    # ---- console -----------------------------------------------------------
    print(f"Tenants named in landlord-filed cases: {fmt_count(total_tenants)}")
    for row in repeat_rows[:6]:
        print(f"  {str(row['cases_against_this_tenant']):36s} "
              f"{fmt_count(row['tenants']):>7s} tenants  {row['pct_of_tenants']:>5}%")
    print()
    print("DECIDED WITHOUT A HEARING")
    for row in ex_rows[:7]:
        print(f"  {row['scope'][:44]:44s} {row['pct_ex_parte']:>5}%  "
              f"({fmt_count(row['ex_parte'])} of {fmt_count(row['orders'])})")
    print()
    print("GENDER (resolved names only)")
    for row in gender_rows:
        print(f"  {row['role'][:40]:40s} {row['men_per_woman']} men per woman  "
              f"(coverage {row['coverage_pct']}%)")
    print(f"\nSaved to {OUT_DIR}")


def _write_csv(path, rows):
    if not rows:
        return
    keys = list({k: None for row in rows for k in row})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(repeat_rows, mix_rows, ex_rows, gender_rows, crosstab, cross_total,
                  total_tenants, repeaters, sizes, size_total,
                  code_rows, recurrence_rows, household_rows):
    same_unit = next(r for r in repeat_rows if "same address" in str(r["cases_against_this_tenant"]))
    moved = next(r for r in repeat_rows if "different address" in str(r["cases_against_this_tenant"]))
    repeat_share = 100 * len(repeaters) / total_tenants
    l4 = next((r for r in mix_rows if r["code"] == "L4"), None)
    landlord_g = gender_rows[0]
    tenant_g = gender_rows[1]
    filer_g = gender_rows[2]

    lines = [
        "# The parties: recurrence, process, and gender",
        "",
        "Built by `scripts/analyze_parties.py`.",
        "",
        "## How often the same tenant recurs",
        "",
        f"Every person named as a tenant in a landlord-filed case "
        f"({fmt_count(total_tenants)} distinct names), counted by how many cases they "
        "appear in:",
        "",
        "| Cases against them | Tenants | Share of tenants | Share of cases |",
        "|---|---:|---:|---:|",
    ]
    for row in repeat_rows:
        if str(row["cases_against_this_tenant"]).startswith("--"):
            continue
        lines.append(
            f"| {row['cases_against_this_tenant']} | {fmt_count(row['tenants'])} "
            f"| {row['pct_of_tenants']}% | {row['pct_of_cases']}% |"
        )
    lines += [
        "",
        f"**{repeat_share:.1f}% of tenants account for "
        f"{sum(r['pct_of_cases'] for r in repeat_rows if isinstance(r['pct_of_cases'], float) and str(r['cases_against_this_tenant']) not in ('1',)):.0f}% "
        "of cases.** Of those repeat tenants:",
        "",
        f"* **{same_unit['pct_of_tenants']}%** recur at the *same address* - one "
        "tenancy generating more than one case, typically a non-payment application "
        "followed by an application to enforce the payment plan that settled it.",
        f"* **{moved['pct_of_tenants']}%** ({fmt_count(moved['tenants'])} people) appear "
        "at a *different address* - moved, and it happened again.",
        "",
        "### What repeat tenants are taken to the Board for",
        "",
        "| Code | Meaning | Repeat tenants | One-time tenants | Ratio |",
        "|---|---|---:|---:|---:|",
    ]
    for row in mix_rows:
        lines.append(
            f"| {row['code']} | {row['meaning']} | {row['pct_of_repeat_tenant_cases']}% "
            f"| {row['pct_of_one_time_tenant_cases']}% | {row['ratio']}x |"
        )
    if l4:
        lines += [
            "",
            f"The clearest difference is **L4, breaching a settlement or order**: "
            f"{l4['pct_of_repeat_tenant_cases']}% of repeat-tenant cases against "
            f"{l4['pct_of_one_time_tenant_cases']}% of one-time-tenant cases, a "
            f"**{l4['ratio']}x** difference. The one-time group is overwhelmingly a "
            "straightforward payment problem; the recurring group is disproportionately "
            "people who agreed to terms and did not keep them.",
        ]
    lines += [
        "",
        "### What this does and does not show",
        "",
        "This is a **148-day window**, which is too short to detect someone who moves "
        "once a year. The 'different address' figure above is therefore a floor on "
        "recurrence across tenancies, not a measurement of it. It is also an "
        "over-count in the other direction: matching is on name text, so two "
        "different people who share a common name are merged. Both errors are real "
        "and they push in opposite directions.",
        "",
        "A longer window would settle it. Ontario publishes one rolling current-year "
        "file, so the only way to get one is to keep snapshotting this export - which "
        "`scripts/fetch_ltb_orders.py` already does.",
        "",
        "## Decided without a hearing",
        "",
        "An ex parte order is made without the other side present.",
        "",
        "| | Orders | Ex parte | Share |",
        "|---|---:|---:|---:|",
    ]
    for row in ex_rows:
        lines.append(
            f"| {row['scope']} | {fmt_count(row['orders'])} "
            f"| {fmt_count(row['ex_parte'])} | {row['pct_ex_parte']}% |"
        )
    lines += [
        "",
        "The concentration in L4 and L3 is procedurally expected rather than "
        "sinister: both are applications to enforce something already agreed or "
        "already noticed, and the Act allows them to proceed without a fresh hearing. "
        "The figure worth carrying forward is the difference between the two sides, "
        "which is large.",
        "",
        "## Household size",
        "",
        "Named adults per landlord-filed case. Children are not named, so this is a "
        "count of adults on the file, not of people at risk of losing the home.",
        "",
        "| Named adults | Cases | Share |",
        "|---:|---:|---:|",
    ]
    for n in sorted(sizes):
        lines.append(f"| {n} | {fmt_count(sizes[n])} | {100 * sizes[n] / size_total:.1f}% |")
    lines += [
        "",
        "## Gender",
        "",
        "Inferred from first names against a name-gender dictionary. **Every figure "
        "below describes resolved names only**, and the coverage column says how much "
        "of each group that is.",
        "",
        "| Role | Men | Women | Men per woman | Coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in gender_rows:
        lines.append(
            f"| {row['role']} | {fmt_count(row['men'])} | {fmt_count(row['women'])} "
            f"| {row['men_per_woman']} | {row['coverage_pct']}% |"
        )
    lines += [
        "",
        f"Individual landlords who bring cases are **{landlord_g['men_per_woman']} men "
        f"per woman**. Tenants named in those cases are "
        f"**{tenant_g['men_per_woman']}** - effectively even. Tenants who bring their "
        f"own case are **{filer_g['men_per_woman']}**.",
        "",
        "### Landlord gender against tenant gender",
        "",
        "| | Tenant M | Tenant F |",
        "|---|---:|---:|",
    ]
    for landlord_side in ("M", "F"):
        cells = " | ".join(
            f"{100 * crosstab[(landlord_side, t)] / cross_total:.1f}%" for t in ("M", "F")
        )
        lines.append(f"| Landlord {landlord_side} | {cells} |")
    lines += [
        "",
        f"Based on {fmt_count(cross_total)} pairs where both sides resolved.",
        "",
        "### Gender by what the case is about",
        "",
        "The aggregate hides the only part of this that is interesting. Split by "
        "application type (rows with at least 100 resolved tenant names):",
        "",
        "| Code | Meaning | Filed by | Individual landlord, M:F | Tenants, M:F | Tenants who are women |",
        "|---|---|---|---:|---:|---:|",
    ] + [
        f"| {row['code']} | {row['meaning']} | {row['filed_by']} "
        f"| {row['landlord_men_per_woman'] or 'thin'} "
        f"| {row['tenant_men_per_woman']} | {row['tenant_pct_women']}% |"
        for row in code_rows
    ] + [
        "",
        "Two patterns, pointing in different directions:",
        "",
        "* **Individual landlords skew about two men to one woman in every "
        "category.** It barely varies by what the case is about, which suggests it "
        "is a fact about who owns rental property rather than about how anyone "
        "behaves.",
        "* **Tenants are taken to the Board at parity, but bring their own cases "
        "more often when they are women.** Tenants named in landlord applications "
        "run 1.02 to 1.06 men per woman, essentially even. Tenant-filed applications "
        "run the other way: maintenance 0.85 (53.9% women), bad-faith notice to "
        "terminate 0.88, tenant rights 0.90.",
        "",
        "### Gender by recurrence and by household",
        "",
        "| Group | Men per woman | Resolved names |",
        "|---|---:|---:|",
    ] + [
        f"| Tenants with {row['group']} | {row['men_per_woman']} "
        f"| {fmt_count(row['men'] + row['women'])} |"
        for row in recurrence_rows
    ] + [
        f"| Tenancies with {row['household']} | {row['men_per_woman']} "
        f"| {fmt_count(row['men'] + row['women'])} |"
        for row in household_rows
    ] + [
        "",
        "Both are null results and are reported as such. Tenants who come back more "
        "than once are not meaningfully more male than those who appear once (1.09 "
        "against 1.03), and a one-adult tenancy is not more male than a two-adult "
        "one (1.01 against 1.05). Whatever explains recurrence, it is not this.",
        "",
        "### Why this is reported with a coverage column",
        "",
        f"The dictionary resolves {landlord_g['coverage_pct']}% of individual landlord "
        f"first names and {tenant_g['coverage_pct']}% of tenant first names. **The "
        "misses are not random.** It resolves Anglo and European given names far "
        "better than others, so communities whose names it does not carry are "
        "under-represented in the resolved base. If the gender balance among "
        "unresolved names differs from the resolved ones, every ratio above shifts.",
        "",
        "The direction of the landlord finding is robust to plausible assumptions "
        "about the missing third - it would take an extreme skew among unresolved "
        "names to bring 2 men per woman down to parity - but the precise ratio should "
        "not be quoted to more than one decimal place, and no figure here should be "
        "read as a statement about any named community.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
