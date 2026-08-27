# -*- coding: utf-8 -*-
"""
The sources page and the print one-pager.

The sources page exists because the commonest way this analysis gets dismissed
is "where did that number come from" - so every figure on the site is traced
here to a named source, its licence, and the window it covers.
"""
from build_site import BUILT, num, table, tile

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
                    "72,836 filed by landlords. Used as an independent check on this "
                    "analysis's annualised figures.",
        "note": "A different year from the order export, which is why the two are "
                "reported as separate routes to the same quantity rather than "
                "combined.",
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
      f'rate of {us["pct_of_renter_households"]}%. But {one_case["pct_of_tenants"]}% '
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
      f'{round(100 - num(one_case["pct_of_tenants"]), 1)}% of tenants who appear more '
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


def build_index(d):
    """The front door. Generated from the same data as everything else, so the
    headline figures on it cannot drift from the report they link to."""
    s = d["summary"]
    ind = d["by_kind"]["individual"]
    ind_b = d["burden_by_kind"]["individual"]
    ontario = d["exposure"][2]
    arrears = d["reasons"][0]
    l4 = next(r for r in d["repeat_mix"] if r["code"] == "L4")
    ll_hearing, tt_hearing = d["hearing"][0], d["hearing"][1]

    p = []
    a = p.append
    a('<div class="eyebrow">Open data &middot; Ontario</div>')
    a("<h1>What Ontario's rental disputes actually cost, and who pays</h1>")
    a('<p class="dek">A ledger of Ontario\'s Landlord and Tenant Board, built only '
      'from two public sources: the Board\'s own order export and Statistics Canada\'s '
      'census. No private or scraped data. It reports what the record shows in both '
      'directions, including the things it does not show.</p>')
    a(f'<div class="window"><b>{s["files"]:,} cases</b> over {s["days"]} days '
      f'({s["first_date"]} to {s["last_date"]}). Not a full year and not all time: '
      'Ontario publishes one rolling current-year file. Annualised figures say so '
      'where they appear.</div>')
    a('<div class="nav">'
      '<a class="primary" href="report.html">Read the full report</a>'
      '<a href="onepager.html">One-page briefing</a>'
      '<a href="map.html">Interactive map</a>'
      '<a href="sources.html">Sources</a></div>')

    a('<div class="tiles">')
    a(tile(f'1 in {ontario["one_in"]}',
           "renter households have a landlord case filed against them each year, "
           "about half the United States rate", "a"))
    a(tile(f'{ind["pct_filed_exactly_once"]}%',
           f'of individual landlords filed exactly once, and '
           f'{ind["pct_holds_one_address"]}% own a single address', "c"))
    a(tile(f'{arrears["pct_of_ltb_landlord_cases"]}% vs {arrears["pct_of_tenant_reported_evictions"]}%',
           "of cases are about unpaid rent, in the Board's file versus in the "
           "evictions tenants actually report", "b"))
    a(tile(f'{l4["ratio"]}x',
           "the rate at which repeat tenants are taken to the Board for breaching a "
           "settlement, against one-time tenants", "a"))
    a("</div>")

    a('<div class="preview-grid">')
    for href, image, alt, caption in (
        ("map.html", "docs/map-preview.png",
         "Ontario rental dispute map by postal area",
         "All 520 postal areas"),
        ("city-map.html", "docs/city-map-preview.png",
         "Ontario rental dispute map by municipality",
         "The same data, by city name"),
    ):
        a(f'<a class="preview-link" href="{href}">'
          f'<img src="{image}" alt="{alt}" loading="lazy">'
          f'<div class="preview-caption"><span>{caption}</span>'
          f'<span>Open map</span></div></a>')
    a("</div>")

    a("<h2>What it found</h2>")
    a("<figure>")
    a(f'<p><b>The scale is ordinary; the distribution is not.</b> About '
      f'{ontario["pct_of_renter_households"]}% of renter households a year, against '
      'about 8% in tracked United States cities. But nine in ten tenants appear '
      'exactly once, and most landlords do too.</p>')
    a(f'<p><b>"Landlords" is not one group.</b> '
      f'{int(num(ind["entities"])):,} individual owners bring '
      f'{ind["pct_of_cases"]}% of cases. The median one is owed '
      f'${int(num(ind_b["median_per_entity"])):,}, which is '
      f'{ind_b["median_as_months_of_rent"]} months of rent or '
      f'{ind_b["median_as_pct_of_annual_rent"]}% of that unit\'s annual gross '
      'revenue. The same sum is a line item to a portfolio owner.</p>')
    a('<p><b>The record is not a picture of eviction.</b> The reasons tenants most '
      'often give for losing a home mostly produce no order at all, so the Board\'s '
      'file understates how often it happens <i>and</i> is not evidence about the '
      'no-fault evictions it barely contains.</p>')
    a(f'<p><b>The two sides do not get the same process.</b> '
      f'{ll_hearing["pct_ex_parte"]}% of landlord-filed orders are made without a '
      f'hearing, against {tt_hearing["pct_ex_parte"]}% of tenant-filed ones.</p>')
    a('<p><b>Some things were tested and not found.</b> Area income barely predicts '
      'where landlords file. There is no gendered pairing between the sides. The '
      'serial-tenant claim is not supported at this timescale, though a real '
      'difference in settlement-breaching is.</p>')
    a("</figure>")

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
         "520 areas, rates per renter household, zoomable and offline-capable"),
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
