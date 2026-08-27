# -*- coding: utf-8 -*-
"""
The report page: every finding, every chart, sources next to the numbers.

Imported by build_site.py, which owns the data loading and the page chrome.
Kept separate only because one file holding both the shell and nine sections
of prose becomes unnavigable.
"""
import svgchart as sv
from build_site import SERIES, data_table, num, source_note, tile


def build(d):
    s = d["summary"]
    ind, corp = d["by_kind"]["individual"], d["by_kind"]["corporate"]
    ind_b, corp_b = d["burden_by_kind"]["individual"], d["burden_by_kind"]["corporate"]
    ontario = d["exposure"][2]
    us = d["exposure"][3]
    evicted = d["exposure"][4]
    arrears, other = d["reasons"][0], d["reasons"][1]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]
    one_case = d["repeat"][0]
    same_addr = next(r for r in d["repeat"] if "same address" in r["cases_against_this_tenant"])
    diff_addr = next(r for r in d["repeat"] if "different address" in r["cases_against_this_tenant"])
    # A share derived from a count of ~37,000 does not carry two decimals;
    # quoting 89.99% implies a precision the underlying name matching does
    # not have. Rounded for prose; the CSV keeps the raw value.
    once_pct = round(num(one_case["pct_of_tenants"]))
    repeat_share = 100 - once_pct
    repeat_cases = round(100 - num(one_case["pct_of_cases"]), 1)

    stable = [
        r for r in d["fsa"]
        if num(r["landlord_filed"], 0) >= 100 and r["tenant_per_landlord_ratio"] != ""
    ]
    stable.sort(key=lambda r: num(r["tenant_per_landlord_ratio"]))
    ratios = [num(r["tenant_per_landlord_ratio"]) for r in stable]
    p10, p90 = ratios[int(0.10 * len(ratios))], ratios[int(0.90 * len(ratios))]
    income_corr = next(
        r for r in d["correlations"]
        if r["census_measure"] == "Median household income" and r["rate"].startswith("Landlord")
    )
    access_corr = next(
        r for r in d["correlations"]
        if r["census_measure"] == "Median household income" and r["rate"].startswith("Tenant")
    )

    p = []
    a = p.append

    # ---- header ------------------------------------------------------------
    a('<div class="eyebrow">Open data &middot; Ontario</div>')
    a("<h1>What Ontario's rental disputes actually cost, and who pays</h1>")
    a('<p class="dek">A ledger of Ontario\'s Landlord and Tenant Board built only '
      'from public records: the Board\'s own order export and the 2021 Census. It '
      'counts what the record contains, says plainly what it leaves out, and reports '
      'the findings that cut in both directions.</p>')
    a(f'<div class="window"><b>Read this first.</b> This export covers '
      f'<b>{s["first_date"]} to {s["last_date"]}</b>: {s["days"]} days, not a full '
      f'year and not all time. It holds {s["orders"]:,} orders across {s["files"]:,} '
      f'distinct cases, because review and amended orders repeat a case. Annual '
      f'figures are that window multiplied by {s["annualisation_factor"]:.3f}. '
      'Ontario publishes one rolling current-year file, so no earlier period exists '
      'to compare against.</div>')
    a('<div class="nav no-print">'
      '<a class="primary" href="map.html">Explore the map</a>'
      '<a href="city-map.html">By city</a>'
      '<a href="sources.html">Every source</a>'
      '<a href="onepager.html">One-page summary</a></div>')

    a('<div class="tiles">')
    a(tile(f'1 in {ontario["one_in"]}',
           "Ontario renter households have a landlord case filed against them each year", "a"))
    a(tile(f'{arrears["pct_of_ltb_landlord_cases"]}% vs {arrears["pct_of_tenant_reported_evictions"]}%',
           "of cases are about unpaid rent, in the Board's file versus in what tenants report", "b"))
    a(tile(f'{ind["pct_filed_exactly_once"]}%',
           f'of individual landlords filed exactly once; {ind["pct_holds_one_address"]}% own one address', "c"))
    a(tile(f'{ind_b["median_as_pct_of_annual_rent"]}%',
           "of a unit's annual rent is what the median landlord is owed once an order lands", "a"))
    a("</div>")

    # ---- 1. scale ----------------------------------------------------------
    a("<h2>1. How big is this, next to the whole rental picture?</h2>")
    a("<p>The commonest objection to any analysis of the Board is that its numbers "
      "sound large in isolation. They need a denominator. Ontario has "
      "<b>1,724,970 renter households</b>. Three independent routes to the annual "
      "number of landlord-filed cases agree:</p>")
    short_route = {
        0: "This export, cases, annualised",
        1: "This export, distinct units",
        2: "The Board's own intake, 2024-25",
    }
    rows = [{"label": short_route[i],
             "value": num(r["pct_of_renter_households"]),
             "display": f'{r["pct_of_renter_households"]}%',
             "color": SERIES["landlord"]}
            for i, r in enumerate(d["exposure"][:3])]
    rows += [
        {"label": "United States filing rate, 2024", "value": num(us["pct_of_renter_households"]),
         "display": f'{us["pct_of_renter_households"]}%', "color": SERIES["tenant"]},
        {"label": "Renters actually evicted, Canada", "value": num(evicted["pct_of_renter_households"]),
         "display": f'{evicted["pct_of_renter_households"]}%', "color": SERIES["corporate"]},
    ]
    a("<figure>")
    a(sv.hbar(rows, label_width=250, title="Share of renter households per year",
              chart_label="Cases per year as a share of renter households"))
    a('<figcaption><b>Roughly 1 in 24 renter households a year.</b> The first three '
      "bars are one quantity measured three ways, including the Board's own "
      'published intake for a different year, which is why they can be trusted. Two '
      "comparisons keep it honest: the United States rate is about twice Ontario's, "
      'so this is a normal-sized eviction system by international standards; and only '
      'about 1% of renters are actually evicted in a year, because <b>an application '
      'is not an eviction</b> and most non-payment cases end with the tenant paying '
      'and staying.</figcaption>')
    a(data_table(["Route", "Cases/year", "Share", "1 in"],
                 [[r["route"], r["cases_per_year"] or "not applicable",
                   f'{r["pct_of_renter_households"]}%', r["one_in"]] for r in d["exposure"]]))
    a("</figure>")

    # ---- 2. what the record misses ----------------------------------------
    a("<h2>2. What the record contains, and what it misses</h2>")
    a("<p>The Board's file and tenants' own accounts describe different populations. "
      "Statistics Canada asks renters why they were forced to move; the answers "
      "barely overlap with what the Board hears.</p>")
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
    a('<figcaption><b>The record is close to inverted relative to lived '
      'experience.</b> Non-payment dominates the Board because a landlord needs an '
      'order to recover money. The reasons tenants most often give, that the '
      'landlord sold (37%), wanted the unit (26%), or was renovating (10%), usually '
      'end with the tenant leaving on a notice, producing no order and no record. '
      "This cuts both ways: the Board's file understates how often tenants lose "
      'housing, <b>and</b> it is not evidence about the frequency of the no-fault '
      'evictions it barely contains.</figcaption>')
    a(data_table(["Reason", "Share of Board cases", "Share of evictions tenants report"],
                 [[r["reason"],
                   f'{r["pct_of_ltb_landlord_cases"]}%' if r["pct_of_ltb_landlord_cases"]
                   else "not separately recorded",
                   f'{r["pct_of_tenant_reported_evictions"]}%'] for r in d["reasons"]]))
    a("</figure>")
    a(source_note(
        'Board figures from this export. Tenant-reported figures from Statistics '
        'Canada, <a href="https://www150.statcan.gc.ca/n1/pub/11-627-m/'
        '11-627-m2022046-eng.htm">Canadian Housing Survey 2021</a>. L2 bundles '
        'own-use, renovation and conduct applications into one code, so the Board '
        'side cannot be split further without reading the orders themselves.'))

    # ---- 3. who the landlords are -----------------------------------------
    a("<h2>3. Who is actually bringing these cases</h2>")
    a('<p>"Landlords" is not one group. Separating the people who own a rental unit '
      'from the organisations that own portfolios changes what the aggregate '
      'numbers mean.</p>')
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": "Share of all cases",
          "values": [num(ind["pct_of_cases"]), num(corp["pct_of_cases"])],
          "displays": [f'{ind["pct_of_cases"]}%', f'{corp["pct_of_cases"]}%']},
         {"label": "Filed exactly once",
          "values": [num(ind["pct_filed_exactly_once"]), num(corp["pct_filed_exactly_once"])],
          "displays": [f'{ind["pct_filed_exactly_once"]}%', f'{corp["pct_filed_exactly_once"]}%']},
         {"label": "Hold a single address",
          "values": [num(ind["pct_holds_one_address"]), num(corp["pct_holds_one_address"])],
          "displays": [f'{ind["pct_holds_one_address"]}%', f'{corp["pct_holds_one_address"]}%']}],
        series=[(f'Individual owners ({int(num(ind["entities"])):,})', SERIES["individual"]),
                (f'Corporate or institutional ({int(num(corp["entities"])):,})', SERIES["corporate"])],
        label_width=190, title="Two different kinds of landlord",
        chart_label="Individual versus corporate landlords"))
    a(f'<figcaption>For <b>{ind["pct_filed_exactly_once"]}% of individual owners this '
      f'is a single event at their only property</b>. For the corporate side it is a '
      f'recurring process: {corp["mean_cases_per_entity"]} cases each on average '
      f'against {ind["mean_cases_per_entity"]} for individuals. That difference is '
      'what an aggregate dollar figure hides.</figcaption>')
    a(data_table(
        ["", "Individual", "Corporate"],
        [["Landlords", f'{int(num(ind["entities"])):,}', f'{int(num(corp["entities"])):,}'],
         ["Share of cases", f'{ind["pct_of_cases"]}%', f'{corp["pct_of_cases"]}%'],
         ["Filed exactly once", f'{ind["pct_filed_exactly_once"]}%', f'{corp["pct_filed_exactly_once"]}%'],
         ["Hold one address", f'{ind["pct_holds_one_address"]}%', f'{corp["pct_holds_one_address"]}%'],
         ["Mean cases each", ind["mean_cases_per_entity"], corp["mean_cases_per_entity"]]]))
    a("</figure>")

    a("<h3>What each kind comes to the Board for</h3>")
    a("<figure>")
    a(sv.split_bar(
        [{"label": f'{r["code"]} · {r["meaning"]}',
          "values": [num(r["pct_individual"]), num(r["pct_corporate"])]}
         for r in d["mix"]],
        series=[("Individual owners", SERIES["individual"]),
                ("Corporate or institutional", SERIES["corporate"])],
        label_width=290, title="Who files which kind of application",
        chart_label="Application type split by kind of landlord"))
    a('<figcaption>Read this in both directions. Individual owners dominate the '
      'categories about recovering money from someone who has already gone (L10, '
      '77%) and about a tenant who gave notice and stayed (L3, 69%). Corporate '
      'owners dominate above-guideline rent increases (L5, 78%). Neither pattern '
      'is flattering to a simple story about either side.</figcaption>')
    a(data_table(["Code", "Meaning", "Cases", "Individual", "Corporate"],
                 [[r["code"], r["meaning"], f'{int(num(r["cases"])):,}',
                   f'{r["pct_individual"]}%', f'{r["pct_corporate"]}%'] for r in d["mix"]],
                 numeric_from=2))
    a("</figure>")

    # ---- 4. the burden -----------------------------------------------------
    a("<h2>4. What it costs, per landlord rather than in total</h2>")
    a(f'<p>The estimated total at stake across non-payment, other-eviction and '
      f'breach-of-settlement cases is <b>${num(ind_b["estimated_total"]) / 1e6 + num(corp_b["estimated_total"]) / 1e6:.0f}M</b>. '
      'On its own that number invites the reading that a class of landlords received '
      'a windfall. It is spread across about 12,000 separate landlords, and what it '
      'means depends entirely on which kind you are.</p>')
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": "Share of the money",
          "values": [num(ind_b["pct_of_estimated_total"]), num(corp_b["pct_of_estimated_total"])],
          "displays": [f'{ind_b["pct_of_estimated_total"]}%', f'{corp_b["pct_of_estimated_total"]}%']},
         {"label": "Mean owed, per landlord",
          "values": [num(ind_b["mean_per_entity"]), num(corp_b["mean_per_entity"])],
          "displays": [f'${int(num(ind_b["mean_per_entity"])):,}',
                       f'${int(num(corp_b["mean_per_entity"])):,}']},
         {"label": "90th percentile",
          "values": [num(ind_b["p90_per_entity"]), num(corp_b["p90_per_entity"])],
          "displays": [f'${int(num(ind_b["p90_per_entity"])):,}',
                       f'${int(num(corp_b["p90_per_entity"])):,}']}],
        series=[("Individual owners", SERIES["individual"]),
                ("Corporate or institutional", SERIES["corporate"])],
        label_width=190, title="The same total, split by kind of landlord",
        chart_label="Money at stake per landlord by kind"))
    a(f'<figcaption>A corporate owner is owed about '
      f'<b>{num(corp_b["mean_per_entity"]) / num(ind_b["mean_per_entity"]):.1f} times '
      f'as much on average</b>, because it brings more cases, not larger ones. The '
      f'typical case is about the same size on both sides: '
      f'<b>${int(num(ind_b["median_per_entity"])):,}</b>, which is '
      f'<b>{ind_b["median_as_months_of_rent"]} months of rent</b> or '
      f'<b>{ind_b["median_as_pct_of_annual_rent"]}% of that unit\'s annual gross '
      f'revenue</b> before mortgage, tax or repairs. For an owner with one unit that '
      'is the whole of it; for a portfolio it is one line item.</figcaption>')
    a("</figure>")
    a(source_note(
        'Dollar figures are estimates, not a census: they extrapolate a sample of '
        'order PDFs as <i>cases x found-rate x mean amount</i>, per category. Orders '
        'stating no amount are counted as zero, which understates rather than '
        'overstates. Method and sample sizes in '
        '<a href="sources.html">sources</a>.'))

    a("<h3>How concentrated the filing is</h3>")
    a("<figure>")
    a(sv.hbar([{"label": f'Top {int(num(r["top_n_landlords"])):,} landlords '
                         f'({r["pct_of_all_landlords"]}% of them)',
                "value": num(r["pct_of_all_cases"]),
                "display": f'{r["pct_of_all_cases"]}%',
                "color": SERIES["landlord"]}
               for r in d["concentration"]],
              label_width=290, max_value=100,
              title="Share of all landlord cases brought by the busiest filers",
              chart_label="Concentration of filings among landlords"))
    a('<figcaption>Filing is concentrated but not extremely so: the busiest 100 '
      'landlords bring about a third of all cases, while most landlords appear once '
      'and never again. No landlord is named anywhere in this analysis; the question '
      'is the shape of the distribution, not who is in it.</figcaption>')
    a("</figure>")

    # ---- 5. repeat parties -------------------------------------------------
    a("<h2>5. How often the same tenant comes back</h2>")
    a("<p>A common claim on the landlord side is that a small group of tenants "
      "cycles through the system. It is testable, and the answer is partly yes and "
      "smaller than the claim.</p>")
    a("<figure>")
    a(sv.hbar([{"label": f'{r["cases_against_this_tenant"]} case'
                         f'{"" if r["cases_against_this_tenant"] == "1" else "s"} '
                         f'against them',
                "value": num(r["pct_of_tenants"]),
                "display": f'{r["pct_of_tenants"]}%',
                "color": SERIES["tenant"]}
               for r in d["repeat"] if not r["cases_against_this_tenant"].startswith("--")],
              label_width=240, title="Tenants by number of cases against them",
              chart_label="Distribution of cases per tenant"))
    a(f'<figcaption><b>{once_pct}% of tenants appear exactly '
      f'once.</b> The {repeat_share}% who recur account for {repeat_cases}% of all '
      f'cases. Of those repeat tenants, <b>{same_addr["pct_of_tenants"]}% recur at '
      f'the same address</b> (one tenancy generating more than one case) and '
      f'{diff_addr["pct_of_tenants"]}% ({int(num(diff_addr["tenants"])):,} people) '
      'appear at a different address.</figcaption>')
    a("</figure>")

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
    a(f'<figcaption><b>The clearest difference is breaching a settlement.</b> That is '
      f'{l4["pct_of_repeat_tenant_cases"]}% of repeat-tenant cases against '
      f'{l4["pct_of_one_time_tenant_cases"]}% of one-time-tenant cases, a '
      f'<b>{l4["ratio"]}-fold</b> difference. The large one-time group is '
      'overwhelmingly a straightforward payment problem; the small recurring group is '
      'disproportionately people who agreed terms and did not keep them.</figcaption>')
    a(data_table(["Code", "Meaning", "Repeat tenants", "One-time tenants", "Ratio"],
                 [[r["code"], r["meaning"], f'{r["pct_of_repeat_tenant_cases"]}%',
                   f'{r["pct_of_one_time_tenant_cases"]}%', f'{r["ratio"]}x']
                  for r in d["repeat_mix"]], numeric_from=2))
    a("</figure>")
    a(f'<div class="finding"><b>What this does not show.</b> {s["days"]} days is too '
      'short a window to detect someone who moves once a year, so the '
      '"different address" figure is a floor on recurrence across tenancies, not a '
      'measurement of it. It is also inflated in the other direction, because '
      'matching is on name text and two different people sharing a common name are '
      'merged. Both errors are real and they push opposite ways. A longer window '
      'would settle it, and the only way to get one is to keep snapshotting this '
      'export, which the repository already does on every fetch.</div>')

    # ---- 6. process --------------------------------------------------------
    a("<h2>6. How many are decided without a hearing</h2>")
    a("<figure>")
    a(sv.hbar([{"label": r["scope"].replace("all ", "").replace(" orders", ""),
                "value": num(r["pct_ex_parte"]),
                "display": f'{r["pct_ex_parte"]}%',
                "color": SERIES["tenant"] if "tenant-filed" in r["scope"] else SERIES["landlord"]}
               for r in d["hearing"]],
              label_width=290, title="Share of orders made without the other side present",
              chart_label="Ex parte order rates"))
    a(f'<figcaption><b>{ll_hearing["pct_ex_parte"]}% of landlord-filed orders are made '
      f'without a hearing, against {tt_hearing["pct_ex_parte"]}% of tenant-filed '
      'ones.</b> The concentration in L4 and L3 is procedurally expected rather than '
      'sinister: both are applications to enforce something already agreed or already '
      'noticed, and the Act allows them to proceed without a fresh hearing. The figure '
      'worth carrying is the gap between the two sides.</figcaption>')
    a(data_table(["Scope", "Orders", "Without a hearing", "Share"],
                 [[r["scope"], f'{int(num(r["orders"])):,}', f'{int(num(r["ex_parte"])):,}',
                   f'{r["pct_ex_parte"]}%'] for r in d["hearing"]]))
    a("</figure>")

    # ---- 7. income and access ---------------------------------------------
    a("<h2>7. Is any of this about income?</h2>")
    a("<p>This gets asserted confidently in both directions. Joining every postal "
      "area's case rate to its census profile settles it, and the answer is mostly "
      "no.</p>")
    a(f'<div class="finding"><b>How often landlords file is close to unrelated to how '
      f'rich an area is</b>: rank correlation {income_corr["spearman_rho"]} '
      f'against median household income across {income_corr["n_fsas"]} postal areas, '
      f'which is about {abs(float(income_corr["spearman_rho"])) ** 2 * 100:.0f}% of the '
      'variation between them. Rental disputes are not concentrated in poor postal '
      'codes in any strong sense, and a claim in either direction that they are is '
      'not supported by this data.</div>')
    a(f'<p>One narrower thing is related to income: whether tenants themselves ever '
      f'use the Board. Tenant-filed cases per landlord-filed case correlate with '
      f'median income at {access_corr["spearman_rho"]}, consistent across three '
      f'separate census measures. Real, and still small at about '
      f'{abs(float(access_corr["spearman_rho"])) ** 2 * 100:.0f}% of the variation.</p>')
    a("<figure>")
    a(sv.scatter(
        [{"x": num(r["median_household_income"]), "y": num(r["tenant_per_landlord_ratio"]),
          "label": r["fsa"]}
         for r in stable if r["median_household_income"]],
        x_label="Median household income in the area",
        y_label="Tenant cases per landlord case",
        title="Where tenants bring their own case",
        highlight={stable[0]["fsa"], stable[-1]["fsa"], stable[-2]["fsa"]},
        chart_label="Tenant filing ratio against area median income"))
    a(f'<figcaption>Each dot is a postal area with at least 100 landlord cases. The '
      f'upward trend is real and weak. Between the 10th and 90th percentile of these '
      f'{len(stable)} areas the ratio runs {p10:.3f} to {p90:.3f}, a '
      f'<b>{p90 / p10:.0f}-fold spread</b>. The percentile range is quoted rather '
      'than the extremes because the lowest area has almost no tenant filings at all '
      'and dividing by it would produce an arbitrarily large multiple.</figcaption>')
    a(data_table(
        ["", "Area", "Landlord cases", "Tenant cases", "Ratio"],
        [["lowest", r["fsa"], r["landlord_filed"], r["tenant_filed"],
          r["tenant_per_landlord_ratio"]] for r in stable[:5]]
        + [["highest", r["fsa"], r["landlord_filed"], r["tenant_filed"],
            r["tenant_per_landlord_ratio"]] for r in stable[-5:]],
        label="Show the most and least active areas"))
    a("</figure>")

    # ---- 8. gender ---------------------------------------------------------
    a("<h2>8. Who the parties are</h2>")
    a("<p>First names carry a signal about gender. It is a weak instrument and is "
      "reported here only alongside how much of each group it actually resolves.</p>")
    a("<figure>")
    a(sv.hbar([{"label": r["role"], "value": num(r["men_per_woman"]),
                "display": f'{r["men_per_woman"]}x',
                "color": SERIES["landlord"] if "landlord" in r["role"].lower() else SERIES["tenant"]}
               for r in d["gender"]],
              label_width=250, title="Gender balance by role, resolved names only",
              chart_label="Inferred gender balance by role"))
    a('<figcaption>Individual landlords who bring cases skew male about two to one. '
      'Tenants named in those cases are even. Tenants who bring their own case are '
      'slightly more often women than men. The landlord-by-tenant crosstab shows no '
      "interaction at all: a landlord's gender does not predict their tenant's."
      '</figcaption>')
    a(data_table(["Role", "Men", "Women", "Men per woman", "Names resolved"],
                 [[r["role"], f'{int(num(r["men"])):,}', f'{int(num(r["women"])):,}',
                   r["men_per_woman"], f'{r["coverage_pct"]}%'] for r in d["gender"]]))
    a("</figure>")
    a('<div class="finding"><b>Why the coverage column is there.</b> The name '
      'dictionary resolves Anglo and European given names far better than others, so '
      'the misses are not random: communities whose names it does not carry are '
      'under-represented in the resolved base. The direction of the landlord finding '
      'survives any plausible assumption about the missing third, but the ratios '
      'should not be read past one decimal place, and none of this is a statement '
      'about any named community.</div>')

    # ---- 9. nulls ----------------------------------------------------------
    a("<h2>9. What was tested and not found</h2>")
    a("<p>Reporting only the things that came out is how an analysis stops being "
      "evidence. These were tested and did not.</p>")
    a("<figure>")
    a(f'<p><b>Area income does not explain where landlords file.</b> Rank correlation '
      f'{income_corr["spearman_rho"]} across {income_corr["n_fsas"]} areas. There is '
      'no strong geography-of-poverty story in the filing rate.</p>')
    a('<p><b>There is no gendered pairing between the sides.</b> Male landlords and '
      'female landlords face essentially the same gender mix of tenants.</p>')
    a(f'<p><b>The serial-tenant claim is not supported at this timescale.</b> Only '
      f'{diff_addr["pct_of_tenants"]}% of repeat tenants, and about 2.7% of all '
      f'tenants, appear at more than one address in {s["days"]} days, and the '
      'apparent top of that list is legal clinics and support agencies named in the '
      'tenant field rather than tenants. A multi-year window is needed for a real '
      'test; what the data does support is the settlement-breach difference in '
      'section 5.</p>')
    a("</figure>")

    return "\n".join(p)
