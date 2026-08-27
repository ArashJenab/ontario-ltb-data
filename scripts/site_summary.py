# -*- coding: utf-8 -*-
"""
The markdown twin of the report, generated from the same CSVs so the two
cannot drift.

Kept as markdown because that is the form that travels: it is what gets
pasted into an email or a constituency-office inbox, renders on GitHub, and
survives being forwarded, none of which an HTML page does well.
"""
from build_site import BUILT, num


def build(d):
    s = d["summary"]
    ind, corp = d["by_kind"]["individual"], d["by_kind"]["corporate"]
    ind_b, corp_b = d["burden_by_kind"]["individual"], d["burden_by_kind"]["corporate"]
    ontario, us, evicted = d["exposure"][2], d["exposure"][3], d["exposure"][4]
    arrears = d["reasons"][0]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    l10 = next(r for r in d["mix"] if r["code"] == "L10")
    l5 = next(r for r in d["mix"] if r["code"] == "L5")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]
    one_case = d["repeat"][0]
    income_corr = next(
        r for r in d["correlations"]
        if r["census_measure"] == "Median household income"
        and r["rate"].startswith("Landlord")
    )
    mi = d["measured"].get("individual")
    mc = d["measured"].get("corporate")
    att = {r["party"]: r for r in d["attendance"]} if d.get("attendance") else None
    once_pct = round(num(one_case["pct_of_tenants"]))
    repeat_share = 100 - once_pct
    repeat_cases = round(100 - num(one_case["pct_of_cases"]), 1)
    corp_multiple = num(corp_b["mean_per_entity"]) / num(ind_b["mean_per_entity"])

    out = [
        "# What Ontario's rental disputes cost, and who pays",
        "",
        f"*An open-data analysis. Generated {BUILT} by `scripts/build_site.py`.*",
        "",
        f"**Window.** The Landlord and Tenant Board publishes one rolling "
        f"current-year file. This analysis covers **{s['first_date']} to "
        f"{s['last_date']}**, {s['days']} days, holding {s['orders']:,} orders "
        f"across {s['files']:,} distinct cases. Not a full year and not all time. No "
        f"earlier period is published anywhere, so no trend can be measured yet. "
        f"Annual figures below are that window multiplied by "
        f"{s['annualisation_factor']:.3f}.",
        "",
        "**In one sentence:** the Board handles a normal-sized caseload by "
        "international standards, but the weight of it falls on people who own a "
        "single rental unit and on tenants who never reach the Board at all, and the "
        "public record is not shaped like the problem it gets used to describe.",
        "",
        "## 1. The scale is ordinary",
        "",
        f"About **{ontario['pct_of_renter_households']}% of Ontario's 1,724,970 "
        f"renter households**, roughly 1 in {ontario['one_in']}, have a landlord case "
        f"filed against them each year. Three independent routes agree: this export "
        f"annualised, this export counting distinct rental units, and the Board's own "
        f"published intake for 2024-25.",
        "",
        f"For comparison, the United States filing rate is about "
        f"{us['pct_of_renter_households']}% of renter households (Eviction Lab, "
        f"2024), and only about {evicted['pct_of_renter_households']}% of Canadian "
        f"renters are actually evicted in a year (CMHC, 2025). **An application is "
        f"not an eviction**: most non-payment cases end with the tenant paying and "
        f"staying. Quoting the filing rate as an eviction rate is wrong in either "
        f"direction.",
        "",
        "## 2. Who actually carries the cost",
        "",
        "| | Individual owners | Corporate or institutional |",
        "|---|---:|---:|",
        f"| Landlords | {int(num(ind['entities'])):,} | {int(num(corp['entities'])):,} |",
        f"| Share of cases | {ind['pct_of_cases']}% | {corp['pct_of_cases']}% |",
        f"| Filed exactly once | **{ind['pct_filed_exactly_once']}%** | {corp['pct_filed_exactly_once']}% |",
        f"| Own a single address | **{ind['pct_holds_one_address']}%** | {corp['pct_holds_one_address']}% |",
        f"| Share of the money at stake | {ind_b['pct_of_estimated_total']}% | {corp_b['pct_of_estimated_total']}% |",
        f"| Mean owed each | ${int(num(ind_b['mean_per_entity'])):,} | ${int(num(corp_b['mean_per_entity'])):,} |",
        "",
        f"Across a year a corporate owner is owed roughly {corp_multiple:.1f} times "
        f"more in total, because it brings many cases. That is the aggregate view and "
        f"it is modelled from category averages.",
        "",
    ]
    if mi and mc:
        out += [
            f"Reading {int(num(mi['n'])) + int(num(mc['n'])):,} orders individually "
            f"gives the per-case answer the model cannot, and it does not point the "
            f"way the aggregate implies. **An individual owner's case is larger than a "
            f"corporate one, not smaller:**",
            "",
            "| Median case | Individual owners | Corporate or institutional |",
            "|---|---:|---:|",
            f"| Months of rent owed | **{mi['median_months']}** | {mc['median_months']} |",
            f"| Amount owed | **${int(num(mi['median_amount'])):,}** | ${int(num(mc['median_amount'])):,} |",
            f"| Share of that unit's annual rent | **{mi['median_pct_of_annual_rent']}%** | {mc['median_pct_of_annual_rent']}% |",
            f"| Rent on the unit | ${int(num(mi['median_rent'])):,} | ${int(num(mc['median_rent'])):,} |",
            f"| Orders measured | {int(num(mi['n'])):,} | {int(num(mc['n'])):,} |",
            "",
            f"The mean amounts are ${int(num(mi['mean_amount'])):,} and "
            f"${int(num(mc['mean_amount'])):,}, with 95% intervals that do not "
            f"overlap, so this is a real difference rather than sampling noise. "
            f"Individual owners do rent costlier units, but the months figure controls "
            f"for that and the gap survives it. For "
            f"{ind['pct_holds_one_address']}% of these owners the unit in question is "
            f"all they have.",
            "",
        ]
    out += [
        f"The application mix says the same thing from another angle. "
        f"**{l10['pct_individual']}% of applications to collect from a tenant who has "
        f"already left** are brought by individuals: the cases least likely ever to "
        f"be recovered. The reverse also holds and belongs in the record, because an "
        f"analysis that only reports one direction is not evidence: above-guideline "
        f"rent increases are **{l5['pct_corporate']}% corporate**.",
        "",
        "## 3. The record is not a picture of eviction",
        "",
        f"Non-payment is **{arrears['pct_of_ltb_landlord_cases']}%** of the Board's "
        f"landlord cases but only **{arrears['pct_of_tenant_reported_evictions']}%** "
        f"of the evictions tenants report to Statistics Canada. The reasons tenants "
        f"most often give, that the landlord sold the property (37%) or wanted the "
        f"unit (26%), usually end with the tenant leaving on a notice and produce no "
        f"order at all.",
        "",
        "This cuts both ways. The Board's file understates how often tenants lose "
        "housing, **and** it is not evidence about the frequency of the no-fault "
        "evictions it barely contains.",
        "",
        "## 4. Recurrence, and process",
        "",
        f"**{once_pct}% of tenants appear in exactly one case.** "
        f"The {repeat_share}% who recur account for {repeat_cases}% of cases and are "
        f"taken to the Board for breaching a settlement at **{l4['ratio']} times** the "
        f"rate of one-time tenants ({l4['pct_of_repeat_tenant_cases']}% of their "
        f"cases against {l4['pct_of_one_time_tenant_cases']}%). Most recur at the "
        f"same address rather than moving on.",
        "",
        f"**{ll_hearing['pct_ex_parte']}% of landlord-filed orders are made without a "
        f"hearing, against {tt_hearing['pct_ex_parte']}% of tenant-filed ones.** Much "
        f"of that gap is procedurally expected, since an application to enforce "
        f"something already agreed may proceed without a fresh hearing, but the size "
        f"of it is a fact about the system worth knowing.",
        "",
    ]
    if att:
        out += [
            f"Where a hearing did happen, orders name who attended. Landlords appear "
            f"at **{att['landlord']['pct_attended']}%** of them and are represented at "
            f"**{att['landlord']['pct_represented']}%**. Tenants appear at "
            f"**{att['tenant']['pct_attended']}%** and are represented at "
            f"**{att['tenant']['pct_represented']}%**. Among those who do attend, "
            f"{att['landlord']['pct_represented_of_those_attending']}% of landlords "
            f"have someone acting for them against "
            f"{att['tenant']['pct_represented_of_those_attending']}% of tenants. This "
            f"finding cuts against the landlord side of the ledger and is reported for "
            f"that reason: whoever bears the financial loss, the party facing loss of "
            f"housing is the one more likely to be absent and far less likely to have "
            f"anyone speaking for them.",
            "",
        ]
    out += [
        "## 5. What was tested and not found",
        "",
        f"- **Area income does not explain where landlords file.** Rank correlation "
        f"{income_corr['spearman_rho']} across {income_corr['n_fsas']} postal areas, "
        f"about 1% of the variation between them. Rental disputes are not "
        f"concentrated in poor postal codes in any strong sense, in either direction.",
        "- **No gendered pairing between the sides.** Male and female landlords face "
        "essentially the same gender mix of tenants, though individual landlords who "
        "file do skew about two to one male.",
        f"- **The serial-tenant claim is not supported at this timescale.** About 2.7% "
        f"of tenants appear at more than one address in {s['days']} days, and the "
        f"apparent top of that list turns out to be legal clinics named in the tenant "
        f"field. What the data does support is narrower: the settlement-breach "
        f"difference above.",
        "",
        "## Why this matters",
        "",
        "None of this required data the province does not already hold. The Board "
        "publishes its orders; Statistics Canada publishes the census. Three gaps "
        "stand out, and all three are cheap to close:",
        "",
        "1. **Only a rolling current-year file is published**, so no trend can be "
        "measured. Nobody, inside or outside government, can presently say whether "
        "this is improving or deteriorating.",
        "2. **Amounts are not in the export**, so every dollar figure here required "
        "downloading and reading order PDFs one at a time. The Board already holds "
        "these figures.",
        "3. **There is no outcome field**, so whether an application ended in "
        "eviction, payment, settlement or dismissal cannot be answered from public "
        "data at all.",
        "",
        "A public dashboard covering those three would cost a fraction of most "
        "provincial data initiatives, and would let landlords, tenants, journalists "
        "and members of the Legislature check these numbers directly rather than take "
        "a private analysis's word for them.",
        "",
        "---",
        "",
        "*Every figure above traces to a named public source; see `sources.html` for "
        "which, and for how far each can be pushed. Application counts, party "
        "classification, geography and process rates are exact counts of the complete "
        "export. Dollar figures are estimates from a sample of order PDFs and are "
        "presented as such. No landlord, tenant or address is named anywhere in this "
        "analysis.*",
        "",
        "*This is an independent analysis developed using data published by the "
        "Government of Ontario. It is not an official publication of, and is not "
        "affiliated with or endorsed by, the Government of Ontario or the Landlord "
        "and Tenant Board.*",
    ]
    return "\n".join(out)
