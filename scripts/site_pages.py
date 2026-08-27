# -*- coding: utf-8 -*-
"""
The sources page and the print one-pager.

The sources page exists because the commonest way this analysis gets dismissed
is "where did that number come from" - so every figure on the site is traced
here to a named source, its licence, and the window it covers.
"""
import svgchart as sv
from build_site import BUILT, SERIES, num, table, tile

# Every external source, in the order a reader would want them.
SOURCES = [
    {
        "name": "LTB Order Catalogue",
        "publisher": "Ontario Landlord and Tenant Board, via data.ontario.ca",
        "url": "https://data.ontario.ca/dataset/ltb-order-catalogue",
        "licence": "Open Government Licence, Ontario",
        "licence_url": "https://www.ontario.ca/page/open-government-licence-ontario",
        "window": "One rolling current-year file. The copy analysed here covers "
                  "2026-01-02 to 2026-05-29.",
        "supplies": "Every case count, application type, party name, address and "
                    "order date. The dollar amounts are read from the order PDFs "
                    "this file links to.",
        "note": "No earlier period is published. The repository snapshots every "
                "fetch so a historical series accumulates from here.",
    },
    {
        "name": "Census Profile 2021, Forward Sortation Areas (98-401-X2021013)",
        "publisher": "Statistics Canada",
        "url": "https://www150.statcan.gc.ca/n1/en/catalogue/98-401-X2021013",
        "licence": "Statistics Canada Open Licence",
        "licence_url": "https://www.statcan.gc.ca/en/reference/licence",
        "window": "2021 Census; income refers to calendar year 2020.",
        "supplies": "Renter-household counts (the denominator for every rate), "
                    "median household income, average and median rent, share of "
                    "tenants in core housing need, and share paying 30%+ of income "
                    "on shelter, for all 521 Ontario postal areas.",
        "note": "Renter households summed across Ontario FSAs come to 1,725,025 "
                "against a province-level 1,724,970, a 55-household gap that is "
                "census random rounding, and the check that both are the same "
                "measure.",
    },
    {
        "name": "Census population by FSA (98-10-0019-01) and by municipality (98-10-0002-01)",
        "publisher": "Statistics Canada",
        "url": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810001901",
        "licence": "Statistics Canada Open Licence",
        "licence_url": "https://www.statcan.gc.ca/en/reference/licence",
        "window": "2021 Census.",
        "supplies": "Population denominators for the per-resident view on the maps, "
                    "kept for continuity alongside the renter-household rate.",
        "note": "A per-resident rate largely measures how many renters an area has. "
                "The renter-household rate is the defensible one and is what the "
                "report uses.",
    },
    {
        "name": "Cartographic Boundary Files, 2021",
        "publisher": "Statistics Canada",
        "url": "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm",
        "licence": "Statistics Canada Open Licence",
        "licence_url": "https://www.statcan.gc.ca/en/reference/licence",
        "window": "2021 Census geography.",
        "supplies": "The postal-area and municipality polygons the maps are drawn on.",
        "note": "",
    },
    {
        "name": "Tribunals Ontario Annual Report 2024-25",
        "publisher": "Tribunals Ontario",
        "url": "https://tribunalsontario.ca/documents/TO/Tribunals_Ontario_2024-2025_Annual_Report.html",
        "licence": "Government of Ontario, published report",
        "licence_url": "",
        "window": "Fiscal year April 2024 to March 2025.",
        "supplies": "The Board's own intake: 87,993 applications received, of which "
                    "72,836 were filed by landlords. Used as an independent check on "
                    "this analysis's annualised figures.",
        "note": "Two caveats. It is a different fiscal year from the order export, "
                "which is why the two are reported as separate routes to the same "
                "quantity rather than averaged. And the per-party figures count "
                "Tribunals Ontario Portal filings only (72,836 + 8,267 + 387 = "
                "81,490, against a stated total of 87,993), so the landlord figure "
                "is a floor and the rate derived from it is conservative.",
    },
    {
        "name": "Canadian Housing Survey 2021: Evictions in Canada",
        "publisher": "Statistics Canada",
        "url": "https://www150.statcan.gc.ca/n1/pub/11-627-m/11-627-m2022046-eng.htm",
        "licence": "Statistics Canada Open Licence",
        "licence_url": "https://www.statcan.gc.ca/en/reference/licence",
        "window": "2021 survey cycle, national.",
        "supplies": "The reasons renters give for being forced to move: sale of the "
                    "property 37%, landlord's own use 26%, conflict 13%, "
                    "demolition or repairs 10%, behind on rent 8%.",
        "note": "National, not Ontario-only. Used to compare the <i>shape</i> of "
                "recorded reasons against reported ones, not to produce an Ontario "
                "count.",
    },
    {
        "name": "Towards Understanding the Magnitude of Evictions in Canada",
        "publisher": "Canada Mortgage and Housing Corporation, July 2025",
        "url": "https://assets.cmhc-schl.gc.ca/sites/cmhc/professional/housing-markets-data-and-research/housing-research/research-reports/2025/towards-understanding-magnitude-evictions-en.pdf",
        "licence": "CMHC research publication",
        "licence_url": "",
        "window": "Canadian Housing Survey 2021 and 2022 reference years.",
        "supplies": "That about 1.0% of Canadian renters are evicted in a year "
                    "counting both formal and informal evictions. This is the figure that "
                    "separates 'a case was filed' from 'someone lost their home'.",
        "note": "CMHC notes the survey excludes people living in shelters and "
                "institutions, so it undercounts.",
    },
    {
        "name": "Eviction Tracking System, 2024",
        "publisher": "The Eviction Lab, Princeton University",
        "url": "https://evictionlab.org/ets-report-2024/",
        "licence": "Eviction Lab terms of use",
        "licence_url": "",
        "window": "Calendar 2024, tracked United States cities.",
        "supplies": "The international benchmark: about 8 eviction filings per 100 "
                    "renter households.",
        "note": "United States court procedure differs from Ontario's, so this is a "
                "rough scale comparison, not a like-for-like rate.",
    },
]

FIGURE_PROVENANCE = [
    ("1 in 24 renter households per year",
     "This export, annualised; cross-checked against Tribunals Ontario intake",
     "Exact count of cases, divided by a census denominator. The annualisation "
     "assumes the rest of the year resembles the 148 days observed."),
    ("63.4% of Board cases are about unpaid rent",
     "This export", "Exact count. No estimation."),
    ("8% of evictions tenants report are about unpaid rent",
     "Canadian Housing Survey 2021", "Survey estimate, national."),
    ("9,291 individual landlords, 85.8% filed once",
     "This export",
     "Exact count, but the individual/corporate split is a name-based "
     "classification, not a legal one. Individual owners filing through a "
     "numbered company are counted as corporate, so the individual share is a "
     "floor."),
    ("$123.5M at stake; $5,226 median per landlord",
     "Sample of order PDFs, extrapolated",
     "Estimate, not a census. cases x found-rate x mean amount, per category. "
     "Orders stating no amount count as zero."),
    ("31% of a unit's annual rent",
     "The above, divided by census average rent",
     "Combines an estimate with a 2021 rent figure. Directionally solid, not "
     "precise."),
    ("Breach of settlement 3.4x more common among repeat tenants",
     "This export", "Exact count within the window. Name matching merges people "
     "who share a name."),
    ("18.4% of landlord orders made without a hearing",
     "This export", "Exact count of the document-type field."),
    ("Rank correlation -0.119 between filing rate and area income",
     "This export joined to the 2021 Census",
     "Area-level association. Says nothing about any individual household."),
    ("2.0 men per woman among individual landlords",
     "First-name dictionary lookup",
     "Weak instrument. Resolves 65% of landlord names, and the misses are not "
     "random across communities."),
]


def build_sources(d):
    s = d["summary"]
    p = []
    a = p.append
    a('<div class="eyebrow">Provenance</div>')
    a("<h1>Every source, and which number came from where</h1>")
    a('<p class="dek">This analysis uses only published data. Nothing here is '
      'scraped, private, or purchased. This page exists so any figure on the site '
      'can be traced to a named source, its licence, and the period it covers.</p>')
    a('<div class="nav no-print"><a href="report.html">Back to the report</a>'
      '<a href="index.html">Home</a></div>')

    a("<h2>The sources</h2>")
    for src in SOURCES:
        a("<figure>")
        a(f'<h3 style="margin-top:0">{src["name"]}</h3>')
        a(f'<p style="margin:6px 0 0;color:var(--ink-muted);font-size:14px">'
          f'{src["publisher"]}</p>')
        rows = [
            ["Link", f'<a href="{src["url"]}">{src["url"][:74]}&hellip;</a>'],
            ["Licence",
             f'<a href="{src["licence_url"]}">{src["licence"]}</a>'
             if src["licence_url"] else src["licence"]],
            ["Period", src["window"]],
            ["Supplies", src["supplies"]],
        ]
        if src["note"]:
            rows.append(["Caveat", src["note"]])
        a(table(["", ""], rows, numeric_from=99))
        a("</figure>")

    a("<h2>Figure by figure</h2>")
    a("<p>What each headline number rests on, and how far it can be pushed.</p>")
    a("<figure>")
    a(table(["Figure", "Source", "How solid"],
            [[f, s_, h] for f, s_, h in FIGURE_PROVENANCE], numeric_from=99))
    a("</figure>")

    a("<h2>The two kinds of number on this site</h2>")
    a('<div class="finding"><b>Exact counts.</b> Case volumes, application types, '
      'party classifications, geography and ex parte rates are counted from the '
      'complete public export. No sampling, no modelling. They are exact for the '
      f'window {s["first_date"]} to {s["last_date"]} and are labelled as annualised '
      'wherever they are projected to a year.</div>')
    a('<div class="finding"><b>Estimates.</b> Every dollar figure. The export lists '
      'case metadata but not the amount each order states, so amounts come from '
      'downloading and reading order PDFs individually. Those are samples with a '
      'stated method, and they are presented as ranges or with their sample size '
      'attached. They should be read as order-of-magnitude.</div>')

    a("<h2>Known limits</h2>")
    a("<figure>")
    a(table(["Limit", "What it means for the numbers"],
            [["A 148-day window",
              "Not a full year and not all time. Seasonality cannot be separated "
              "from trend, and nothing here shows whether things are getting better "
              "or worse."],
             ["Orders are not cases",
              f'{s["orders"]:,} orders cover {s["files"]:,} distinct cases, because '
              "review and amended orders repeat a file. Counts on this site are of "
              "cases unless stated."],
             ["An application is not an eviction",
              "Most non-payment cases end with the tenant paying and staying. "
              "Filing rates and eviction rates are different quantities and are "
              "labelled separately."],
             ["Name-based classification",
              "Whether a landlord is 'corporate' and whether a party is a person are "
              "inferred from name text, not from a registry."],
             ["Name matching merges and splits",
              "Two landlords sharing a canonical name are merged; one landlord using "
              "two spellings is double-counted. Concentration figures are "
              "approximate at the margin."],
             ["Area-level correlation",
              "Associations between an area's case rate and its census profile say "
              "nothing about any individual household or landlord in it."],
             ["Gender inference",
              "A dictionary lookup on first names that resolves some naming "
              "traditions far better than others. Always reported with its coverage."]],
            numeric_from=99))
    a("</figure>")
    return "\n".join(p)


def build_onepager(d):
    s = d["summary"]
    ind = d["by_kind"]["individual"]
    corp = d["by_kind"]["corporate"]
    ind_b = d["burden_by_kind"]["individual"]
    corp_b = d["burden_by_kind"]["corporate"]
    ontario = d["exposure"][2]
    us = d["exposure"][3]
    arrears = d["reasons"][0]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]
    one_case = d["repeat"][0]

    p = []
    a = p.append
    a('<div class="eyebrow">Briefing note &middot; Ontario rental disputes</div>')
    a("<h1>What Ontario's rental disputes cost, and who pays</h1>")
    a(f'<p class="dek">Built entirely from the Landlord and Tenant Board\'s own '
      f'published order data ({s["files"]:,} cases, {s["first_date"]} to '
      f'{s["last_date"]}) and the 2021 Census. Independent analysis; not affiliated '
      'with the Government of Ontario or the Board.</p>')
    a('<div class="nav no-print"><a href="report.html">Full report</a>'
      '<a href="sources.html">Sources</a>'
      '<a href="javascript:window.print()">Print this page</a></div>')

    a('<div class="tiles">')
    a(tile(f'1 in {ontario["one_in"]}', "renter households have a case filed against them each year", "a"))
    a(tile(f'{ind["pct_filed_exactly_once"]}%', "of individual landlords filed exactly once", "c"))
    a(tile(f'{ind_b["median_as_pct_of_annual_rent"]}%', "of a unit's annual rent is owed by the time an order lands", "a"))
    a(tile(f'{ll_hearing["pct_ex_parte"]}% / {tt_hearing["pct_ex_parte"]}%', "of landlord / tenant orders are made without a hearing", "b"))
    a("</div>")

    a("<h2>Five things the public record shows</h2>")
    a("<figure>")
    a(f'<p><b>1. The scale is ordinary; the distribution is not.</b> About '
      f'{ontario["pct_of_renter_households"]}% of Ontario renter households have a '
      f'landlord case filed against them each year, roughly half the United States '
      f'rate of {us["pct_of_renter_households"]}%. But {round(num(one_case["pct_of_tenants"]))}% '
      'of tenants appear exactly once, and most landlords do too. This is a system '
      'that touches a lot of people once, not a small group repeatedly.</p>')
    a(f'<p><b>2. Individual landlords are not small versions of corporate ones.</b> '
      f'{int(num(ind["entities"])):,} individual owners bring {ind["pct_of_cases"]}% '
      f'of cases; {ind["pct_filed_exactly_once"]}% file exactly once and '
      f'{ind["pct_holds_one_address"]}% own a single address. The median amount owed, '
      f'${int(num(ind_b["median_per_entity"])):,}, is '
      f'{ind_b["median_as_months_of_rent"]} months of rent, or '
      f'{ind_b["median_as_pct_of_annual_rent"]}% of that unit\'s annual gross revenue '
      'before mortgage, tax or repairs. For a portfolio owner the same sum is one '
      'line item.</p>')
    a(f'<p><b>3. The Board\'s file is not a picture of eviction.</b> '
      f'{arrears["pct_of_ltb_landlord_cases"]}% of landlord cases are about unpaid '
      f'rent, against {arrears["pct_of_tenant_reported_evictions"]}% of the evictions '
      'tenants report to Statistics Canada. The reasons tenants most often give, that '
      'the landlord sold or wanted the unit, mostly end without an order and leave no '
      'record at all.</p>')
    a(f'<p><b>4. A small recurring group behaves differently.</b> The '
      f'{100 - round(num(one_case["pct_of_tenants"]))}% of tenants who appear more '
      f'than once are taken to the Board for breaching a settlement at '
      f'{l4["ratio"]} times the rate of one-time tenants '
      f'({l4["pct_of_repeat_tenant_cases"]}% against '
      f'{l4["pct_of_one_time_tenant_cases"]}%). Most of them recur at the same '
      'address rather than moving on.</p>')
    a(f'<p><b>5. The two sides do not get the same process.</b> '
      f'{ll_hearing["pct_ex_parte"]}% of landlord-filed orders are made without a '
      f'hearing, against {tt_hearing["pct_ex_parte"]}% of tenant-filed ones. Much of '
      'that gap is procedurally expected, but the size of it is a fact about the '
      'system worth knowing.</p>')
    a("</figure>")

    a("<h2>What is not in the data, and could be</h2>")
    a("<figure>")
    a("<p>None of this required information the province does not already hold. The "
      "Board publishes its orders; Statistics Canada publishes the census. Putting "
      "them together took a few days with public tools. Three gaps stand out, and "
      "all three are cheap to close:</p>")
    a(table(["Gap", "Why it matters"],
            [["Only a rolling current-year file is published",
              "No trend can be measured. Nobody, inside or outside government, can "
              "presently say whether the situation is improving or deteriorating."],
             ["Amounts are not in the export",
              "Every dollar figure on this site required downloading and reading "
              "order PDFs one at a time. The Board holds these figures already."],
             ["No outcome field",
              "Whether an application ended in eviction, payment, settlement or "
              "dismissal is not published, so 'how often does filing end a tenancy' "
              "cannot be answered from public data at all."]],
            numeric_from=99))
    a("</figure>")
    a('<div class="finding">A public dashboard covering these three gaps would cost '
      'a small fraction of most provincial data initiatives, and would let landlords, '
      'tenants, journalists and members of the Legislature check these numbers '
      'directly instead of taking a private analysis\'s word for them.</div>')
    return "\n".join(p)


def ledger(title, rows, foot=None):
    """A short table of facts set as one figure, for the numbers that only mean
    something next to each other."""
    out = [f'<div class="ledger"><h4>{title}</h4><dl>']
    for entry in rows:
        label, value = entry[0], entry[1]
        emphasis = " total" if len(entry) > 2 and entry[2] else ""
        out.append(
            f'<div class="row{emphasis}"><dt>{label}</dt><dd>{value}</dd></div>'
        )
    out.append("</dl>")
    if foot:
        out.append(f'<div class="foot">{foot}</div>')
    out.append("</div>")
    return "".join(out)


def build_index(d):
    """The front door.

    This carries the findings rather than only linking to them: someone who
    reads this page and nothing else should come away with the size of the
    thing, who carries it, and what the record does not show. Generated from
    the same CSVs as the report, so the two cannot drift apart.
    """
    s = d["summary"]
    ind, corp = d["by_kind"]["individual"], d["by_kind"]["corporate"]
    ind_b, corp_b = d["burden_by_kind"]["individual"], d["burden_by_kind"]["corporate"]
    ontario, us, evicted = d["exposure"][2], d["exposure"][3], d["exposure"][4]
    arrears, other = d["reasons"][0], d["reasons"][1]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]
    l10 = next(r for r in d["mix"] if r["code"] == "L10")
    l3 = next(r for r in d["mix"] if r["code"] == "L3")
    l5 = next(r for r in d["mix"] if r["code"] == "L5")
    l1 = next(r for r in d["mix"] if r["code"] == "L1")
    income_corr = next(
        r for r in d["correlations"]
        if r["census_measure"] == "Median household income" and r["rate"].startswith("Landlord")
    )

    p = []
    a = p.append

    # ---- hero --------------------------------------------------------------
    a('<div class="eyebrow">Open data &middot; Ontario</div>')
    a("<h1>What Ontario's rental disputes actually cost, and who pays</h1>")
    a('<p class="dek">Built only from two public sources: the Landlord and Tenant '
      "Board's own order export and Statistics Canada's census. No private or "
      'scraped data, no named parties, and findings reported in whichever '
      'direction they came out.</p>')
    a(f'<div class="lede">The Board handles a normal-sized caseload by international '
      f'standards. What is not normal is where the weight of it lands. '
      f'<b>{int(num(ind["entities"])):,} people who own a single rental unit</b> '
      f'bring {ind["pct_of_cases"]}% of all landlord cases, and for '
      f'{ind["pct_filed_exactly_once"]}% of them it happens once and never again. By '
      f'the time an order arrives the typical one is owed '
      f'<b>{ind_b["median_as_months_of_rent"]} months of rent on their only '
      f'property</b>. On the other side, the evictions tenants most often actually '
      'experience barely appear in this record at all.</div>')
    a(f'<div class="window"><b>{s["files"]:,} cases</b> over {s["days"]} days '
      f'({s["first_date"]} to {s["last_date"]}). Not a full year and not all time: '
      'Ontario publishes one rolling current-year file, so no trend can be measured '
      'yet. Annualised figures say so where they appear.</div>')
    a('<div class="nav">'
      '<a class="primary" href="report.html">Read the full report</a>'
      '<a href="onepager.html">One-page briefing</a>'
      '<a href="map.html">Interactive map</a>'
      '<a href="sources.html">Sources</a></div>')

    a('<div class="tiles">')
    a(tile(f'{ind_b["median_as_pct_of_annual_rent"]}%',
           "of a unit's annual rent is owed by the time an order lands, on the "
           "typical case", "a"))
    a(tile(f'{ind["pct_holds_one_address"]}%',
           "of individual landlords at the Board own exactly one address", "a"))
    a(tile(f'1 in {ontario["one_in"]}',
           "renter households have a case filed against them each year, about half "
           "the United States rate", "b"))
    a(tile(f'{ll_hearing["pct_ex_parte"]}% / {tt_hearing["pct_ex_parte"]}%',
           "of landlord / tenant orders are made without a hearing", "c"))
    a("</div>")

    # ---- 1. the weight on a single-unit owner ------------------------------
    a("<h2>What this costs someone who owns one unit</h2>")
    a('<p>The aggregate figure, roughly $123M at stake across the province, invites '
      'the reading that a class of landlords received a windfall. It is spread '
      'across about 12,000 separate landlords, and two thirds of them are people, '
      'not companies. Set out per landlord, the same money looks entirely '
      'different.</p>')
    a(ledger(
        "The typical individual owner's case",
        [("Rent owed by the time an order issues",
          f'{ind_b["median_as_months_of_rent"]} months'),
         ("As a sum", f'${int(num(ind_b["median_per_entity"])):,}'),
         ("Share of that unit's annual gross revenue, before mortgage, tax or repairs",
          f'{ind_b["median_as_pct_of_annual_rent"]}%', True),
         ("Share of individual owners who hold any other address",
          f'{100 - num(ind["pct_holds_one_address"]):.1f}%'),
         ("Share who appear at the Board more than once",
          f'{100 - num(ind["pct_filed_exactly_once"]):.1f}%')],
        foot="Median case, individual owners only. The dollar figure is an estimate "
             "from a sample of order PDFs; the ownership figures are exact counts of "
             'the full export. <a href="sources.html">How each was produced</a>.'))
    a("<figure>")
    a(sv.grouped_hbar(
        [{"label": "Share of all cases",
          "values": [num(ind["pct_of_cases"]), num(corp["pct_of_cases"])],
          "displays": [f'{ind["pct_of_cases"]}%', f'{corp["pct_of_cases"]}%']},
         {"label": "Filed exactly once",
          "values": [num(ind["pct_filed_exactly_once"]), num(corp["pct_filed_exactly_once"])],
          "displays": [f'{ind["pct_filed_exactly_once"]}%', f'{corp["pct_filed_exactly_once"]}%']},
         {"label": "Own a single address",
          "values": [num(ind["pct_holds_one_address"]), num(corp["pct_holds_one_address"])],
          "displays": [f'{ind["pct_holds_one_address"]}%', f'{corp["pct_holds_one_address"]}%']}],
        series=[(f'Individual owners ({int(num(ind["entities"])):,})', SERIES["individual"]),
                (f'Corporate or institutional ({int(num(corp["entities"])):,})', SERIES["corporate"])],
        label_width=190, title="Two different kinds of landlord",
        chart_label="Individual versus corporate landlords"))
    a(f'<figcaption>For an organisation this is a recurring process, '
      f'{corp["mean_cases_per_entity"]} cases each on average and spread across a '
      'portfolio. The typical individual owner brings one, at the single address '
      'they have, and is never seen again. <b>The same dollar loss is a line item to '
      'one of them and roughly a third of a year\'s revenue to the '
      'other.</b></figcaption>')
    a("</figure>")

    if d.get("burden_bands"):
        bands = d["burden_bands"]
        months = d["burden_months"][0] if d.get("burden_months") else None
        over_six = sum(
            num(b["pct_of_orders"], 0) for b in bands
            if b["band"] in ("6 to 12 months", "Over 12 months")
        )
        a("<figure>")
        a(sv.hbar([{"label": b["band"], "value": num(b["pct_of_orders"]),
                    "display": f'{b["pct_of_orders"]}%',
                    "color": SERIES["individual"]} for b in bands],
                  label_width=170,
                  title="Rent owed when the order issued, in months of that unit's rent",
                  chart_label="Distribution of months of rent owed"))
        caption = (
            f'Read from the rent each order states, so it is that unit\'s own rent '
            f'rather than a provincial average. <b>{over_six:.0f}% of orders are for '
            f'more than six months of rent</b> on a single unit.'
        )
        if months:
            caption += (
                f' Median {months["median_months"]} months, mean '
                f'{months["mean_months"]} (95% interval {months["mean_months_ci_low"]} '
                f'to {months["mean_months_ci_high"]}), from {int(num(months["n"])):,} '
                'orders read individually.'
            )
        a(f"<figcaption>{caption}</figcaption>")
        a("</figure>")

    a("<figure>")
    a(sv.split_bar(
        [{"label": f'{r["code"]} · {r["meaning"]}',
          "values": [num(r["pct_individual"]), num(r["pct_corporate"])]}
         for r in (l10, l3, l1, l5)],
        series=[("Individual owners", SERIES["individual"]),
                ("Corporate or institutional", SERIES["corporate"])],
        label_width=290, title="Who brings which kind of case",
        chart_label="Application type split by kind of landlord"))
    a(f'<figcaption><b>Individual owners dominate the categories where the money is '
      f'already gone.</b> {l10["pct_individual"]}% of applications to collect from a '
      f'tenant who has already left are brought by individuals, and '
      f'{l3["pct_individual"]}% of those about a tenant who gave notice and stayed. '
      f'The reverse holds too, and belongs here: above-guideline rent increases are '
      f'{l5["pct_corporate"]}% corporate.</figcaption>')
    a("</figure>")

    # ---- 2. how often, and to whom -----------------------------------------
    a("<h2>How often this happens, and to whom</h2>")
    a("<figure>")
    a(sv.hbar(
        [{"label": "Ontario, landlord cases filed",
          "value": num(ontario["pct_of_renter_households"]),
          "display": f'{ontario["pct_of_renter_households"]}%',
          "color": SERIES["landlord"]},
         {"label": "United States, filings 2024",
          "value": num(us["pct_of_renter_households"]),
          "display": f'{us["pct_of_renter_households"]}%',
          "color": SERIES["tenant"]},
         {"label": "Renters actually evicted, Canada",
          "value": num(evicted["pct_of_renter_households"]),
          "display": f'{evicted["pct_of_renter_households"]}%',
          "color": SERIES["corporate"]}],
        label_width=250, title="Share of renter households per year",
        chart_label="Ontario filing rate against international benchmarks"))
    a('<figcaption>Ontario runs at about half the United States filing rate, and the '
      'figure is confirmed three ways including the Board\'s own published intake. '
      '<b>An application is not an eviction</b>: only about 1% of renters are '
      'actually evicted in a year, because most non-payment cases end with the '
      'tenant paying and staying. Anyone quoting the filing rate as an eviction rate '
      'is wrong, in either direction.</figcaption>')
    a("</figure>")

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
      'landlord sold or wanted the unit, usually end with the tenant leaving on a '
      'notice and produce no record at all. So the file understates how often '
      'tenants lose housing <i>and</i> is not evidence about the no-fault evictions '
      'it barely contains.</figcaption>')
    a("</figure>")

    # ---- 3. the map --------------------------------------------------------
    a("<h2>Where it concentrates</h2>")
    a('<a class="preview-link wide" href="map.html">'
      '<img src="docs/map-preview.png" loading="lazy" '
      'alt="Interactive map of Ontario rental dispute rates by postal area">'
      '<div class="preview-caption">'
      '<span>All 520 postal areas, raw counts or per 10,000 residents</span>'
      '<span>Open the map</span></div></a>')
    a('<p class="src">The map currently normalises by <b>population</b>, which is a '
      'weaker denominator than the one used elsewhere on this site: an area that is '
      '80% renters will look busier than one that is 20% renters with nothing else '
      'differing. Per-renter-household rates are in '
      '<code>results/exposure/fsa_access_income.csv</code> and are what section 7 of '
      'the report uses; moving the map onto them is outstanding work. A '
      '<a href="city-map.html">municipality view</a> of the same data is available '
      'for anyone who does not think in postal codes.</p>')

    # ---- 4. nulls ----------------------------------------------------------
    a("<h2>What was tested and not found</h2>")
    a("<p>Reporting only the things that came out is how an analysis stops being "
      "evidence. These were tested and did not.</p>")
    a("<figure>")
    a(f'<p><b>Area income does not explain where landlords file.</b> Rank '
      f'correlation {income_corr["spearman_rho"]} across {income_corr["n_fsas"]} '
      'postal areas, about 1% of the variation between them. Rental disputes are not '
      'concentrated in poor postal codes in any strong sense, in either direction.</p>')
    a('<p><b>There is no gendered pairing between the sides.</b> Male and female '
      'landlords face essentially the same gender mix of tenants, though individual '
      'landlords who file do skew about two to one male.</p>')
    a(f'<p><b>The serial-tenant claim is not supported at this timescale.</b> About '
      f'2.7% of tenants appear at more than one address in {s["days"]} days, and the '
      'apparent top of that list turns out to be legal clinics named in the tenant '
      'field. What the data <i>does</i> support is narrower and real: the 10% of '
      f'tenants who recur are taken to the Board for breaching a settlement at '
      f'{l4["ratio"]} times the rate of one-time tenants.</p>')
    a("</figure>")

    # ---- 5. everything else ------------------------------------------------
    a("<h2>Everything else</h2>")
    a('<div class="file-list">')
    for href, name, desc in (
        ("report.html", "Full report",
         "Nine sections, every chart, sources beside each number"),
        ("onepager.html", "One-page briefing",
         "Print-ready summary for a constituency office"),
        ("sources.html", "Sources and provenance",
         "Every source, its licence, and which figure came from where"),
        ("map.html", "Map by postal area",
         "520 areas, raw counts or per 10,000 residents, zoomable and works offline"),
        ("city-map.html", "Map by municipality",
         "The same data rolled up to recognisable city names"),
        ("https://github.com/ArashJenab/ontario-ltb-data", "Source repository",
         "All data, scripts, and per-analysis methodology notes"),
    ):
        a(f'<a class="file-row" href="{href}"><span class="name">{name}</span>'
          f'<span class="desc">{desc}</span></a>')
    a("</div>")
    return "\n".join(p)


INDEX_CSS = """
.preview-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:30px; }
@media (max-width:700px){ .preview-grid{ grid-template-columns:1fr; } }
.preview-link { display:block; color:inherit; text-decoration:none; border-radius:14px;
                overflow:hidden; border:1px solid var(--border); box-shadow:var(--shadow); }
.preview-link img { display:block; width:100%; height:auto; }
.preview-link.wide { display:block; margin-top:22px; }
.preview-caption { padding:12px 16px; background:var(--surface); font-size:12.5px;
                   color:var(--ink-muted); border-top:1px solid var(--border);
                   display:flex; justify-content:space-between; gap:10px; }
.preview-caption span:last-child { color:var(--ink); font-weight:700; white-space:nowrap; }
.file-list { display:flex; flex-direction:column; gap:10px; margin-top:14px; }
.file-row { display:flex; justify-content:space-between; align-items:baseline; gap:16px;
            padding:14px 18px; background:var(--surface); border:1px solid var(--border);
            border-radius:10px; text-decoration:none; color:var(--ink); }
.file-row:hover { border-color:var(--border-strong); }
.file-row .name { font-weight:700; font-size:14.5px; }
.file-row .desc { font-size:13px; color:var(--ink-muted); text-align:right; }
"""
