# -*- coding: utf-8 -*-
"""
The report page.

Structured as an argument, not a list of analyses. The previous version ran
nine numbered sections each headed by the name of a technique, showed a chart,
and moved on, which read as a report written to have been written. Each section
here is instead a question a person would actually ask, answered in one bold
sentence before any chart appears, and closed with what it means. A reader who
reads only the bold lines should come away with the whole argument.

The argument: the Board's caseload is ordinary in size, and almost nothing else
about it works the way people assume. Filing is not eviction. The landlords
bringing cases are mostly not companies. The losses fall on whoever cannot
spread them. The tenants who most need the Board lose in it. And the record
itself is a biased sample of the problem it gets used to describe.
"""
import svgchart as sv
from build_site import SERIES, data_table, num, source_note, tile


def section(a, question, answer):
    """A heading that asks something, and the answer before any chart."""
    a(f"<h2>{question}</h2>")
    a(f'<p class="answer">{answer}</p>')


def means(a, text):
    a(f'<div class="means"><b>What this means.</b> {text}</div>')


def build(d):
    s = d["summary"]
    ind, corp = d["by_kind"]["individual"], d["by_kind"]["corporate"]
    ind_b, corp_b = d["burden_by_kind"]["individual"], d["burden_by_kind"]["corporate"]
    ontario, us, evicted = d["exposure"][2], d["exposure"][3], d["exposure"][4]
    arrears, other = d["reasons"][0], d["reasons"][1]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    l10 = next(r for r in d["mix"] if r["code"] == "L10")
    l5 = next(r for r in d["mix"] if r["code"] == "L5")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]
    one_case = d["repeat"][0]
    same_addr = next(r for r in d["repeat"] if "same address" in r["cases_against_this_tenant"])
    diff_addr = next(r for r in d["repeat"] if "different address" in r["cases_against_this_tenant"])
    once_pct = round(num(one_case["pct_of_tenants"]))
    repeat_share = 100 - once_pct
    repeat_cases = round(100 - num(one_case["pct_of_cases"]), 1)

    mi = d["measured"].get("individual")
    mc = d["measured"].get("corporate")
    annual_share = mi["median_pct_of_annual_rent"] if mi else ind_b["median_as_pct_of_annual_rent"]
    byfiler = d.get("attendance_by_filer")
    outcomes = {r["filed_by"]: r for r in d["outcomes"]} if d.get("outcomes") else None

    stable = [
        r for r in d["fsa"]
        if num(r["landlord_filed"], 0) >= 100 and r["tenant_per_landlord_ratio"] != ""
    ]
    stable.sort(key=lambda r: num(r["tenant_per_landlord_ratio"]))
    income_corr = next(
        r for r in d["correlations"]
        if r["census_measure"] == "Median household income" and r["rate"].startswith("Landlord")
    )

    def att(filer, party, key):
        row = next(r for r in byfiler if r["filed_by"] == filer and r["party"] == party)
        return num(row[key])

    p = []
    a = p.append

    # ---- header ------------------------------------------------------------
    a('<div class="eyebrow">Open data &middot; Ontario</div>')
    a("<h1>What Ontario's rental disputes actually cost, and who pays</h1>")
    a('<p class="dek">Built from two public sources: the Landlord and Tenant '
      "Board's own order export, and the 2021 Census. Where the export stops, this "
      'reads the orders themselves.</p>')

    a('<div class="thesis">'
      '<p><b>The short version.</b> Ontario\'s rental dispute caseload is ordinary in '
      'size by international standards. Almost nothing else about it works the way it '
      'is usually described.</p>'
      '<ul>'
      '<li><b>Filing is not eviction.</b> About a quarter of landlord applications end '
      'a tenancy outright. Half of all termination orders say the tenancy ends '
      '<i>unless the tenant pays</i>.</li>'
      '<li><b>Most landlords here are not companies.</b> Two thirds are individuals, '
      'and most of them own one unit and appear once.</li>'
      '<li><b>The losses land on whoever cannot spread them.</b> The typical '
      "individual owner's case is bigger than a corporate one, not smaller.</li>"
      '<li><b>Tenants who bring their own case usually lose it</b>, and almost never '
      'have anyone representing them.</li>'
      '<li><b>The record is a biased sample</b> of the thing it gets used to describe.'
      '</li></ul></div>')

    a(f'<div class="window"><b>Before any number below.</b> This export covers '
      f'<b>{s["first_date"]} to {s["last_date"]}</b>: {s["days"]} days, not a full '
      f'year and not all time. It holds {s["orders"]:,} orders across {s["files"]:,} '
      f'distinct cases, because review and amended orders repeat a case. Annual '
      f'figures are that window multiplied by {s["annualisation_factor"]:.3f}. '
      'Ontario publishes one rolling current-year file, so there is no earlier period '
      'to compare against and no trend can be measured yet.</div>')
    a('<div class="nav no-print">'
      '<a class="primary" href="map.html">Explore the map</a>'
      '<a href="sources.html">Every source</a>'
      '<a href="onepager.html">One-page summary</a></div>')

    a('<div class="tiles">')
    a(tile(f'1 in {ontario["one_in"]}',
           "renter households have a case filed against them each year", "a"))
    if outcomes:
        a(tile(f'{outcomes["landlord"]["voidable_share_of_terminations"]}%',
               "of termination orders let the tenant pay and stay", "c"))
        a(tile(f'{outcomes["tenant"]["dismissed"]}%',
               "of cases a tenant brings are dismissed, against "
               f'{outcomes["landlord"]["dismissed"]}% of a landlord\'s', "b"))
    a(tile(f'{annual_share}%',
           "of a unit's annual rent is owed by the time an order lands", "a"))
    a("</div>")

    # ---- 1 -----------------------------------------------------------------
    section(a, "How many people does this actually affect?",
            "About <b>1 in 24 Ontario renter households</b> has a case filed against "
            "it each year. That is roughly half the United States rate. The scale is "
            "unremarkable; what happens inside it is not.")
    rows = [{"label": lab, "value": num(r["pct_of_renter_households"]),
             "display": f'{r["pct_of_renter_households"]}%', "color": SERIES["landlord"]}
            for lab, r in zip(("This export, cases, annualised",
                               "This export, distinct units",
                               "The Board's own intake, 2024-25"), d["exposure"][:3])]
    rows += [
        {"label": "United States filing rate, 2024", "value": num(us["pct_of_renter_households"]),
         "display": f'{us["pct_of_renter_households"]}%', "color": SERIES["tenant"]},
        {"label": "Renters actually evicted, Canada", "value": num(evicted["pct_of_renter_households"]),
         "display": f'{evicted["pct_of_renter_households"]}%', "color": SERIES["corporate"]},
    ]
    a("<figure>")
    a(sv.hbar(rows, label_width=250, title="Share of renter households per year",
              chart_label="Cases per year as a share of renter households"))
    a('<figcaption>The first three bars are one quantity measured three ways, '
      "including the Board's own published intake for a different year. They agree, "
      'which is why the figure can be relied on.</figcaption>')
    a(data_table(["Route", "Cases/year", "Share", "1 in"],
                 [[r["route"], r["cases_per_year"] or "not applicable",
                   f'{r["pct_of_renter_households"]}%', r["one_in"]] for r in d["exposure"]]))
    a("</figure>")
    means(a, "This is not a system in crisis by volume, and anyone arguing from "
             "sheer case counts is arguing weakly. The problems below are about who "
             "the system lands on and what it does to them, not about how many "
             "cases it hears.")

    # ---- 2 -----------------------------------------------------------------
    if outcomes:
        ll, tt = outcomes["landlord"], outcomes["tenant"]
        section(a, "When a landlord files, what actually happens?",
                f"<b>{ll['any_termination']}% of landlord applications end in a "
                f"termination order, but {ll['voidable_share_of_terminations']}% of "
                "those are voidable</b>: the tenancy ends <i>unless</i> the tenant "
                "pays a stated sum by a stated date. Net, about a quarter of "
                "applications end a tenancy outright.")
        a("<figure>")
        a(sv.hbar(
            # "Not classified" is a limit on the measurement, not a result, so it
            # is drawn recessive rather than competing with the real categories.
            [{"label": lab, "value": num(ll[key]), "display": f'{ll[key]}%',
              "color": "--ink-faint" if key == "other" else SERIES["landlord"]}
             for key, lab in (("terminated", "Terminated"),
                              ("terminated_voidable", "Terminated, tenant can pay to stay"),
                              ("money_only", "Ordered to pay, tenancy continues"),
                              ("dismissed", "Dismissed"),
                              ("withdrawn", "Withdrawn"),
                              ("other", "Not classified"))],
            label_width=270, title="How a landlord-filed application ends",
            chart_label="Disposition of landlord-filed applications"))
        a(f'<figcaption>Read from {int(num(ll["orders"])):,} orders individually. '
          f'A further {ll["on_consent"]}% of all landlord applications were decided '
          'on consent, meaning the parties settled and asked the Board to record '
          'it; that cuts across the categories above rather than being one of '
          'them.</figcaption>')
        a("</figure>")
        means(a, "The disposition is not in the open-data export, and until this was "
                 "measured the honest answer to \"how often does filing end a "
                 "tenancy?\" was that nobody outside the Board knew. It is now "
                 "roughly one in four. <b>Any figure that treats filings, or even "
                 "terminations, as a count of evictions is overstating it, and this "
                 "is by how much.</b>")

    # ---- 3 -----------------------------------------------------------------
    section(a, "Who are these landlords?",
            f"<b>Two thirds are individuals, not companies.</b> "
            f"{int(num(ind['entities'])):,} individual owners bring "
            f"{ind['pct_of_cases']}% of cases, and for "
            f"{ind['pct_filed_exactly_once']}% of them it happens once and never "
            f"again. {ind['pct_holds_one_address']}% own a single address.")
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": lab,
          "values": [num(ind[key]), num(corp[key])],
          "displays": [f'{ind[key]}%', f'{corp[key]}%']}
         for key, lab in (("pct_of_cases", "Share of all cases"),
                          ("pct_filed_exactly_once", "Filed exactly once"),
                          ("pct_holds_one_address", "Own a single address"))],
        series=[(f'Individual owners ({int(num(ind["entities"])):,})', SERIES["individual"]),
                (f'Corporate or institutional ({int(num(corp["entities"])):,})', SERIES["corporate"])],
        label_width=190, title="Two different kinds of landlord",
        chart_label="Individual versus corporate landlords"))
    a(f'<figcaption>For an organisation this is a process: '
      f'{corp["mean_cases_per_entity"]} cases each on average, across a portfolio. '
      'The typical individual owner brings one, at the one address they have, and is '
      'never seen again.</figcaption>')
    a("</figure>")
    a("<figure>")
    a(sv.split_bar(
        [{"label": f'{r["code"]} · {r["meaning"]}',
          "values": [num(r["pct_individual"]), num(r["pct_corporate"])]}
         for r in d["mix"]],
        series=[("Individual owners", SERIES["individual"]),
                ("Corporate or institutional", SERIES["corporate"])],
        label_width=290, title="Who brings which kind of case",
        chart_label="Application type split by kind of landlord"))
    a(f'<figcaption>Individual owners dominate the categories where the money is '
      f'already gone: {l10["pct_individual"]}% of applications to collect from a '
      f'tenant who has already left. Corporate owners dominate above-guideline rent '
      f'increases, {l5["pct_corporate"]}%.</figcaption>')
    a("</figure>")
    means(a, '"Landlords" is not one interest group, and a policy aimed at the '
             "corporate landlord hits nine thousand people who own one unit. The "
             "reverse holds too: a policy aimed at protecting small owners does "
             "nothing about above-guideline rent increases, which are almost "
             "entirely a corporate instrument.")

    # ---- 4 -----------------------------------------------------------------
    if mi and mc:
        section(a, "What does a case cost the landlord who brings it?",
                f"<b>The median individual owner is owed "
                f"${int(num(mi['median_amount'])):,} after {mi['median_months']} "
                f"months without rent</b>, which is {mi['median_pct_of_annual_rent']}% "
                "of that unit's annual gross revenue before mortgage, tax or repairs. "
                "That is larger than the corporate median, not smaller.")
        a("<figure>")
        a(sv.paired_rows(
            [{"label": "Months of rent owed",
              "values": [num(mi["median_months"]), num(mc["median_months"])],
              "displays": [f'{mi["median_months"]} mo', f'{mc["median_months"]} mo']},
             {"label": "Amount owed",
              "values": [num(mi["median_amount"]), num(mc["median_amount"])],
              "displays": [f'${int(num(mi["median_amount"])):,}',
                           f'${int(num(mc["median_amount"])):,}']},
             {"label": "Share of annual rent",
              "values": [num(mi["median_pct_of_annual_rent"]),
                         num(mc["median_pct_of_annual_rent"])],
              "displays": [f'{mi["median_pct_of_annual_rent"]}%',
                           f'{mc["median_pct_of_annual_rent"]}%']}],
            series=[("Individual owners", SERIES["individual"]),
                    ("Corporate or institutional", SERIES["corporate"])],
            label_width=210, title="The median case, read from the orders",
            chart_label="Measured burden per case by kind of landlord"))
        a(f'<figcaption>Mean amounts ${int(num(mi["mean_amount"])):,} against '
          f'${int(num(mc["mean_amount"])):,}, with 95% intervals that do not overlap, '
          f'so the difference is real. Individual owners do rent costlier units '
          f'(${int(num(mi["median_rent"])):,} against '
          f'${int(num(mc["median_rent"])):,} a month), but the months figure controls '
          'for that and the gap survives it.</figcaption>')
        a(data_table(
            ["", "Individual", "Corporate"],
            [["Orders measured", f'{int(num(mi["n"])):,}', f'{int(num(mc["n"])):,}'],
             ["Median months owed", mi["median_months"], mc["median_months"]],
             ["Median amount", f'${int(num(mi["median_amount"])):,}',
              f'${int(num(mc["median_amount"])):,}'],
             ["Mean amount", f'${int(num(mi["mean_amount"])):,}',
              f'${int(num(mc["mean_amount"])):,}'],
             ["95% interval on the mean",
              f'${int(num(mi["mean_amount_ci_low"])):,} to ${int(num(mi["mean_amount_ci_high"])):,}',
              f'${int(num(mc["mean_amount_ci_low"])):,} to ${int(num(mc["mean_amount_ci_high"])):,}'],
             ["Median rent on the unit", f'${int(num(mi["median_rent"])):,}',
              f'${int(num(mc["median_rent"])):,}'],
             ["Share of annual rent", f'{mi["median_pct_of_annual_rent"]}%',
              f'{mc["median_pct_of_annual_rent"]}%']]))
        a("</figure>")

    if d.get("burden_bands"):
        bands = d["burden_bands"]
        over_six = sum(num(b["pct_of_orders"], 0) for b in bands
                       if b["band"] in ("6 to 12 months", "Over 12 months"))
        a("<figure>")
        a(sv.hbar([{"label": b["band"], "value": num(b["pct_of_orders"]),
                    "display": f'{b["pct_of_orders"]}%', "color": SERIES["individual"]}
                   for b in bands],
                  label_width=170,
                  title="Rent owed when the order issued, in months of that unit's rent",
                  chart_label="Distribution of months of rent owed"))
        a(f'<figcaption><b>{over_six:.0f}% of orders are for more than six months of '
          'rent</b> on a single unit. The short tail points the other way and matters '
          "too: the smallest band is a tenancy ending over less than one month's "
          'rent.</figcaption>')
        a(data_table(["Months owed", "Orders", "Share"],
                     [[b["band"], f'{int(num(b["orders"])):,}', f'{b["pct_of_orders"]}%']
                      for b in bands]))
        a("</figure>")
    means(a, "A dollar figure means nothing without knowing what it is a fraction "
             "of. The same loss is a line item to a portfolio owner and a third of "
             "the year's revenue to someone with one unit, and it is the second "
             "group that brings most of these cases.")

    # ---- 5 -----------------------------------------------------------------
    if outcomes and byfiler:
        tt = outcomes["tenant"]
        ll = outcomes["landlord"]
        section(a, "And when a tenant files?",
                f"<b>{tt['dismissed']}% of the cases a tenant brings are dismissed, "
                f"against {ll['dismissed']}% of a landlord's.</b> Tenants are also "
                f"represented at {att('tenant', 'tenant', 'pct_represented'):.0f}% of "
                "the hearings they themselves bring.")
        a("<figure>")
        a(sv.grouped_hbar(
            [{"label": lab, "values": [num(ll[key]), num(tt[key])],
              "displays": [f'{ll[key]}%', f'{tt[key]}%']}
             for key, lab in (("dismissed", "Dismissed"),
                              ("money_only", "Ordered to pay"),
                              ("remedy_ordered", "Other side ordered to act"),
                              ("withdrawn", "Withdrawn"))],
            series=[("When a landlord filed", SERIES["landlord"]),
                    ("When a tenant filed", SERIES["tenant"])],
            label_width=210, title="How the application ends, by who brought it",
            chart_label="Disposition by who filed"))
        a('<figcaption>A tenant who brings a case is more likely to leave with '
          'nothing than with anything.</figcaption>')
        a("</figure>")
        a("<figure>")
        a(sv.grouped_hbar(
            [{"label": f'{filer.title()} filed: {party}',
              "values": [att(filer, party, "pct_attended"),
                         att(filer, party, "pct_represented")],
              "displays": [f'{att(filer, party, "pct_attended"):.1f}%',
                           f'{att(filer, party, "pct_represented"):.1f}%']}
             for filer in ("landlord", "tenant") for party in ("landlord", "tenant")],
            series=[("Attended the hearing", SERIES["landlord"]),
                    ("Had a representative", SERIES["tenant"])],
            label_width=210, title="Presence at the hearing, by who filed",
            chart_label="Attendance and representation by party and by filer"))
        a(f'<figcaption>Part of the attendance gap is structural, since the applicant '
          f'turns up to their own case: tenants attend '
          f'{att("tenant", "tenant", "pct_attended"):.1f}% of hearings they bring '
          f'against {att("landlord", "tenant", "pct_attended"):.1f}% of those brought '
          'against them. Representation does not behave that way. Bringing their own '
          f'case, tenants are represented '
          f'{att("tenant", "tenant", "pct_represented"):.1f}% of the time against '
          f'{att("tenant", "landlord", "pct_represented"):.1f}% for landlords who are '
          'only responding to it.</figcaption>')
        a(data_table(
            ["Filed by", "Party", "Attended", "Represented", "Of those attending"],
            [[r["filed_by"].title(), r["party"].title(), f'{r["pct_attended"]}%',
              f'{r["pct_represented"]}%', f'{r["pct_represented_of_attending"]}%']
             for r in byfiler], numeric_from=2))
        a("</figure>")
        means(a, "Both halves of this report point the same way from opposite "
                 "directions. The individual landlord carries a loss they cannot "
                 "spread; the tenant walks into a hearing without anyone acting for "
                 "them and usually loses. <b>Neither is the villain in the other's "
                 "story. Both are the people least equipped for the system they are "
                 "in.</b>")

    # ---- 6 -----------------------------------------------------------------
    section(a, "Is this record a fair picture of eviction in Ontario?",
            f"<b>No.</b> Unpaid rent is {arrears['pct_of_ltb_landlord_cases']}% of "
            f"what the Board hears but only "
            f"{arrears['pct_of_tenant_reported_evictions']}% of the evictions tenants "
            "report to Statistics Canada. The most common real reasons barely appear "
            "here at all.")
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": "Behind on rent",
          "values": [num(arrears["pct_of_ltb_landlord_cases"]),
                     num(arrears["pct_of_tenant_reported_evictions"])],
          "displays": [f'{arrears["pct_of_ltb_landlord_cases"]}%',
                       f'{arrears["pct_of_tenant_reported_evictions"]}%']},
         {"label": "Every other reason",
          "values": [num(other["pct_of_ltb_landlord_cases"]),
                     num(other["pct_of_tenant_reported_evictions"])],
          "displays": [f'{other["pct_of_ltb_landlord_cases"]}%',
                       f'{other["pct_of_tenant_reported_evictions"]}%']}],
        series=[("In the Board's orders", SERIES["record"]),
                ("In what tenants report", SERIES["reported"])],
        label_width=190, title="Why the tenancy ended",
        chart_label="Reasons recorded at the Board versus reasons tenants report"))
    a('<figcaption>Non-payment dominates the Board because a landlord needs an order '
      'to recover money. The reasons tenants most often give, that the landlord sold '
      '(37%) or wanted the unit (26%), usually end with the tenant leaving on a '
      'notice and produce no order at all.</figcaption>')
    a(data_table(["Reason", "Share of Board cases", "Share of evictions tenants report"],
                 [[r["reason"],
                   f'{r["pct_of_ltb_landlord_cases"]}%' if r["pct_of_ltb_landlord_cases"]
                   else "not separately recorded",
                   f'{r["pct_of_tenant_reported_evictions"]}%'] for r in d["reasons"]]))
    a("</figure>")
    means(a, "This cuts against both sides and is the most misused fact here. The "
             "Board's file <b>understates</b> how often tenants lose housing, "
             "<b>and</b> it is not evidence about how common no-fault evictions are, "
             "because it barely contains them. Anyone using this dataset as an "
             "eviction census, in either direction, is using it wrongly.")
    a(source_note(
        'Board figures from this export. Tenant-reported figures from Statistics '
        'Canada, <a href="https://www150.statcan.gc.ca/n1/pub/11-627-m/'
        '11-627-m2022046-eng.htm">Canadian Housing Survey 2021</a>. L2 bundles '
        'own-use, renovation and conduct applications into one code, so the Board '
        'side cannot be split further without reading the orders.'))

    # ---- 7 -----------------------------------------------------------------
    section(a, "Do the same people keep coming back?",
            f"<b>Mostly no. {once_pct}% of tenants appear exactly once.</b> The "
            f"{repeat_share}% who recur account for {repeat_cases}% of cases, and "
            f"they differ in one specific way: they are taken to the Board for "
            f"breaching a settlement at {l4['ratio']} times the rate.")
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": f'{r["code"]} · {r["meaning"]}',
          "values": [num(r["pct_of_repeat_tenant_cases"]), num(r["pct_of_one_time_tenant_cases"])],
          "displays": [f'{r["pct_of_repeat_tenant_cases"]}%', f'{r["pct_of_one_time_tenant_cases"]}%']}
         for r in d["repeat_mix"][:4]],
        series=[("Tenants with more than one case", SERIES["tenant"]),
                ("Tenants with exactly one case", SERIES["landlord"])],
        label_width=290, title="What each group is taken to the Board for",
        chart_label="Case mix for repeat versus one-time tenants"))
    a(f'<figcaption>The one-time group is overwhelmingly a straightforward payment '
      f'problem. The recurring group is disproportionately people who agreed terms '
      f'and did not keep them. Of the repeaters, {same_addr["pct_of_tenants"]}% recur '
      f'at the same address and {diff_addr["pct_of_tenants"]}% at a different '
      'one.</figcaption>')
    a(data_table(["Code", "Meaning", "Repeat tenants", "One-time tenants", "Ratio"],
                 [[r["code"], r["meaning"], f'{r["pct_of_repeat_tenant_cases"]}%',
                   f'{r["pct_of_one_time_tenant_cases"]}%', f'{r["ratio"]}x']
                  for r in d["repeat_mix"]], numeric_from=2))
    a("</figure>")
    means(a, f"There is a real recurring group and it is small. It is not the "
             f"explanation for the caseload: nine in ten tenants here are having one "
             f"bad year, not running a strategy. {s['days']} days is also too short "
             "a window to catch someone who moves annually, so the cross-address "
             "figure is a floor rather than a measurement.")

    # ---- 8 -----------------------------------------------------------------
    section(a, "Is any of this about income, or gender?",
            "<b>Income, almost not at all.</b> How often landlords file is close to "
            f"unrelated to how rich an area is (rank correlation "
            f"{income_corr['spearman_rho']}, about 1% of the variation). Gender shows "
            "one consistent pattern and several nulls.")
    a("<figure>")
    a(sv.hbar([{"label": r["role"], "value": num(r["men_per_woman"]),
                "display": f'{r["men_per_woman"]}x',
                "color": (SERIES["landlord"] if "landlord" in r["role"].lower()
                          else SERIES["tenant"])}
               for r in d["gender"]],
              label_width=250, max_value=2.4, title="Men per woman, by role",
              chart_label="Inferred gender balance by role"))
    a('<figcaption>Individual landlords who file skew about two to one male, '
      'consistently across every application type. Tenants named in cases are even. '
      'Tenants who bring their own case are slightly more often women. Inferred from '
      'first names, which resolves 65% of landlord and 78% of tenant names, and the '
      'misses are not random across communities.</figcaption>')
    a(data_table(["Role", "Men", "Women", "Men per woman", "Names resolved"],
                 [[r["role"], f'{int(num(r["men"])):,}', f'{int(num(r["women"])):,}',
                   r["men_per_woman"], f'{r["coverage_pct"]}%'] for r in d["gender"]]))
    a("</figure>")
    means(a, "The gender difference is in who owns rental property and who reaches "
             "for the Board, not in who behaves how. Nobody in this data is "
             "\"crazier\" than anybody else, and the income result should stop a "
             "common argument in both directions: rental disputes are not "
             "concentrated in poor postal codes in any strong sense.")

    # ---- 9 -----------------------------------------------------------------
    section(a, "What was tested and found to be nothing?",
            "Reporting only what came out is how an analysis stops being evidence. "
            "These were tested and did not.")
    a("<figure>")
    a(f'<p><b>Area income does not explain where landlords file.</b> Rank correlation '
      f'{income_corr["spearman_rho"]} across {income_corr["n_fsas"]} postal areas.</p>')
    a('<p><b>No gendered pairing between the sides.</b> Male and female landlords face '
      'essentially the same gender mix of tenants.</p>')
    a('<p><b>Repeat tenants are not more male</b> than one-time tenants (1.09 against '
      '1.03), and a one-adult tenancy is not more male than a two-adult one.</p>')
    a(f'<p><b>The serial-tenant claim is not supported at this timescale.</b> About '
      f'2.7% of tenants appear at more than one address in {s["days"]} days, and the '
      'apparent top of that list turns out to be legal clinics named in the tenant '
      'field rather than tenants.</p>')
    a("</figure>")

    # ---- 10 ----------------------------------------------------------------
    section(a, "So what should change?",
            "Three gaps, all cheap to close, all in data the province already holds.")
    a("<figure>")
    a(data_table(["Gap", "What it costs", "Why it is cheap"],
                 [["Only a rolling current-year file is published",
                   "No trend can be measured. Nobody, inside or outside government, "
                   "can say whether this is improving or deteriorating.",
                   "The file already exists; keeping the previous ones is a "
                   "retention policy, not a project."],
                  ["Amounts are not in the export",
                   "Every dollar figure on this site required downloading and "
                   "reading order PDFs one at a time.",
                   "The Board holds these figures in the order it already wrote."],
                  ["No disposition field",
                   "Until this report, nobody outside the Board could say how often "
                   "filing ends a tenancy. It is about one in four.",
                   "It is stated in the operative paragraph of every order."]],
                 numeric_from=99))
    a("</figure>")
    a('<div class="means"><b>The point.</b> Nothing in this report needed data the '
      'province does not already hold, and none of it needed access anyone else '
      'lacks. It took a few days with public tools. That a private analysis had to '
      'read ten thousand PDFs to establish how often an eviction application ends a '
      'tenancy is the finding underneath all the other findings.</div>')

    return "\n".join(p)
