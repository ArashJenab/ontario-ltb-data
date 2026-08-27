# -*- coding: utf-8 -*-
"""
Build the site pages from the analysis outputs.

Every figure on every page is read out of results/*/ at build time rather than
typed into the HTML, so a page can never drift from the analysis that produced
it. Re-run the analyses, re-run this, and the pages are correct by
construction.

Produces:
    report.html     the main artifact: all findings, all charts, sources inline
    sources.html    every source, its licence, its window, and which figure
                    came from where
    onepager.html   a print-ready single page for a constituency office
"""
import csv
import datetime
from pathlib import Path

import ltbdata
import svgchart as sv
from svgchart import esc

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"

BUILT = datetime.date.today().isoformat()

SERIES = {
    "individual": "--series-1",
    "corporate": "--series-3",
    "landlord": "--series-1",
    "tenant": "--series-2",
    "record": "--series-1",
    "reported": "--series-2",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def read(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def num(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load():
    d = {
        "entities": read(RESULTS / "who_pays" / "landlord_entities.csv"),
        "mix": read(RESULTS / "who_pays" / "application_mix.csv"),
        "concentration": read(RESULTS / "who_pays" / "concentration.csv"),
        "burden": read(RESULTS / "who_pays" / "burden_per_landlord.csv"),
        "exposure": read(RESULTS / "exposure" / "exposure_rate.csv"),
        "reasons": read(RESULTS / "exposure" / "reason_mismatch.csv"),
        "correlations": read(RESULTS / "exposure" / "correlations.csv"),
        "fsa": read(RESULTS / "exposure" / "fsa_access_income.csv"),
        "repeat": read(RESULTS / "parties" / "repeat_tenants.csv"),
        "repeat_mix": read(RESULTS / "parties" / "repeat_case_mix.csv"),
        "hearing": read(RESULTS / "parties" / "decided_without_hearing.csv"),
        "gender": read(RESULTS / "parties" / "gender_summary.csv"),
        "household": read(RESULTS / "parties" / "household_size.csv"),
    }
    # The burden analysis depends on a long PDF extraction run, so the site
    # must build with or without it. Sections keyed off these appear only once
    # results/burden/ exists.
    burden_dir = RESULTS / "burden"
    for key, filename in (
        ("burden_months", "months_owed.csv"),
        ("burden_bands", "months_distribution.csv"),
        ("burden_kinds", "by_landlord_kind.csv"),
        ("attendance", "attendance.csv"),
    ):
        path = burden_dir / filename
        d[key] = read(path) if path.exists() else None

    d["by_kind"] = {r["landlord_kind"]: r for r in d["entities"]}
    d["burden_by_kind"] = {r["landlord_kind"]: r for r in d["burden"]}
    summary = ltbdata.summarise(ltbdata.load_orders(unique_files=True))
    d["summary"] = summary
    return d


# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------

THEME_CSS = """
:root {
  --bg:#eef1f5; --surface:#ffffff; --surface-2:#f7f8fb;
  --ink:#1a2130; --ink-muted:#5c6675; --ink-faint:#8b93a1;
  --border:#dde1e8; --border-strong:#c7cdd7; --grid:#e4e8ee;
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a;
  --warn-bg:#fff6e8; --warn-border:#f0c98a; --warn-ink:#7a4e10;
  --shadow:0 1px 2px rgba(20,24,32,.06), 0 8px 24px rgba(20,24,32,.06);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#0f1319; --surface:#171c25; --surface-2:#12161d;
    --ink:#e8ecf3; --ink-muted:#9aa4b4; --ink-faint:#6b7484;
    --border:#262d3a; --border-strong:#333c4c; --grid:#262d3a;
    --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
    --warn-bg:#241d10; --warn-border:#5c4a20; --warn-ink:#e9c98d;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"] {
  --bg:#0f1319; --surface:#171c25; --surface-2:#12161d;
  --ink:#e8ecf3; --ink-muted:#9aa4b4; --ink-faint:#6b7484;
  --border:#262d3a; --border-strong:#333c4c; --grid:#262d3a;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70;
  --warn-bg:#241d10; --warn-border:#5c4a20; --warn-ink:#e9c98d;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
}
* { box-sizing:border-box; }
html,body { margin:0; padding:0; background:var(--bg); color:var(--ink); }
body {
  font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased; line-height:1.6;
  display:flex; justify-content:center;
  padding:clamp(20px,5vw,64px) clamp(16px,4vw,40px);
}
.page { width:100%; max-width:860px; }
.eyebrow { font-size:12px; font-weight:700; letter-spacing:.09em;
           text-transform:uppercase; color:var(--ink-faint); }
h1 { margin:10px 0 0; font-size:clamp(28px,4.6vw,42px); font-weight:700;
     letter-spacing:-.015em; line-height:1.12; text-wrap:balance; }
h2 { margin:56px 0 6px; font-size:clamp(20px,2.6vw,25px); font-weight:700;
     letter-spacing:-.01em; line-height:1.25; text-wrap:balance; }
h3 { margin:34px 0 4px; font-size:17px; font-weight:700; }
.dek { margin:16px 0 0; font-size:17.5px; color:var(--ink-muted); }
p { margin:14px 0; }
a { color:var(--series-1); }
.lede { margin-top:26px; padding:20px 22px; background:var(--surface);
        border:1px solid var(--border); border-left:3px solid var(--series-1);
        border-radius:10px; font-size:16.5px; box-shadow:var(--shadow); }
.window { margin:22px 0 0; padding:14px 18px; background:var(--warn-bg);
          border:1px solid var(--warn-border); border-radius:10px;
          font-size:14px; color:var(--warn-ink); }
.window b { color:var(--warn-ink); }
.tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:30px 0 0; }
@media (max-width:820px){ .tiles{ grid-template-columns:repeat(2,1fr);} }
@media (max-width:420px){ .tiles{ grid-template-columns:1fr;} }
.tile { background:var(--surface); border:1px solid var(--border);
        border-radius:12px; padding:16px 16px 18px; box-shadow:var(--shadow); }
.tile .n { font-size:27px; font-weight:800; letter-spacing:-.02em;
           font-variant-numeric:tabular-nums; line-height:1.1; }
.tile .t { margin-top:7px; font-size:13px; line-height:1.45; color:var(--ink-muted); }
.n.a { color:var(--series-1); } .n.b { color:var(--series-2); } .n.c { color:var(--series-3); }
figure { margin:26px 0 0; padding:20px 22px 16px; background:var(--surface);
         border:1px solid var(--border); border-radius:12px; box-shadow:var(--shadow); }
figcaption { margin-top:12px; padding-top:12px; border-top:1px solid var(--border);
             font-size:13px; color:var(--ink-muted); }
figcaption b { color:var(--ink); }
details { margin-top:10px; font-size:13px; }
summary { cursor:pointer; color:var(--ink-muted); font-weight:600; }
table { border-collapse:collapse; width:100%; margin:12px 0 0; font-size:13.5px; }
th,td { text-align:left; padding:7px 10px; border-bottom:1px solid var(--border); }
th { font-size:12px; text-transform:uppercase; letter-spacing:.04em;
     color:var(--ink-faint); font-weight:700; }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
.scroll { overflow-x:auto; }
.src { font-size:12.5px; color:var(--ink-faint); margin-top:10px; }
.src a { color:var(--ink-muted); }
footer { margin-top:60px; padding-top:22px; border-top:1px solid var(--border);
         font-size:12.5px; line-height:1.7; color:var(--ink-faint); }
footer a { color:var(--ink-muted); }
.nav { display:flex; flex-wrap:wrap; gap:12px; margin-top:24px; }
.nav a { display:inline-block; padding:11px 18px; border-radius:9px;
         font-weight:700; font-size:14.5px; text-decoration:none;
         background:var(--surface); color:var(--ink);
         border:1px solid var(--border-strong); }
.nav a.primary { background:var(--ink); color:var(--bg); border-color:var(--ink); }
.finding { margin-top:18px; padding:16px 18px; background:var(--surface-2);
           border:1px solid var(--border); border-radius:10px; font-size:15px; }
.finding b { color:var(--ink); }
.ledger { margin-top:22px; background:var(--surface); border:1px solid var(--border);
          border-radius:12px; box-shadow:var(--shadow); overflow:hidden; }
.ledger h4 { margin:0; padding:16px 20px 12px; font-size:15px; font-weight:700;
             border-bottom:1px solid var(--border); }
.ledger dl { margin:0; padding:6px 20px 16px; }
.ledger .row { display:flex; justify-content:space-between; align-items:baseline;
               gap:18px; padding:11px 0; border-bottom:1px solid var(--border); }
.ledger .row:last-child { border-bottom:0; }
.ledger dt { font-size:14px; color:var(--ink-muted); margin:0; }
.ledger dd { margin:0; font-size:17px; font-weight:800; letter-spacing:-.01em;
             font-variant-numeric:tabular-nums; white-space:nowrap; }
.ledger .row.total dd { color:var(--series-1); font-size:20px; }
.ledger .foot { padding:12px 20px 16px; font-size:12.5px; color:var(--ink-faint);
                border-top:1px solid var(--border); background:var(--surface-2); }
"""

PRINT_CSS = """
@media print {
  body { background:#fff; color:#000; padding:0; display:block; }
  .page { max-width:none; }
  .no-print { display:none !important; }
  figure, .tile, .lede, .window, .finding {
    box-shadow:none; border:1px solid #ccc; break-inside:avoid; }
  h2 { break-after:avoid; }
  a { color:#000; text-decoration:none; }
}
"""

DISCLAIMER = (
    "This is an independent analysis developed using data published by the "
    "Government of Ontario. It is not an official publication of, and is not "
    "affiliated with or endorsed by, the Government of Ontario or the Landlord "
    "and Tenant Board."
)


def shell(title, description, body, extra_css=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<style>{THEME_CSS}{sv.CHART_CSS}{PRINT_CSS}{extra_css}</style>
</head>
<body>
<div class="page">
{body}
</div>
</body>
</html>
"""


def table(headers, rows, numeric_from=1):
    def cls(i):
        return ' class="n"' if i >= numeric_from else ""

    head = "".join(f"<th{cls(i)}>{esc(h)}</th>" for i, h in enumerate(headers))
    body = []
    for row in rows:
        cells = "".join(f"<td{cls(i)}>{c}</td>" for i, c in enumerate(row))
        body.append(f"<tr>{cells}</tr>")
    return (
        f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def data_table(headers, rows, label="Show the numbers", numeric_from=1):
    return (
        f"<details><summary>{esc(label)}</summary>"
        f"{table(headers, rows, numeric_from)}</details>"
    )


def tile(number, text, tone="a"):
    return (
        f'<div class="tile"><div class="n {tone}">{number}</div>'
        f'<div class="t">{text}</div></div>'
    )


def source_note(text):
    return f'<p class="src">{text}</p>'


def footer(extra=""):
    return f"""<footer>
{extra}
Built from the <a href="https://data.ontario.ca/dataset/ltb-order-catalogue">Ontario
LTB Order Catalogue</a> (Open Government Licence, Ontario) and the 2021 Census
(Statistics Canada Open Licence). Full provenance for every figure:
<a href="sources.html">sources</a>. Code is <a href="LICENSE">MIT-licensed</a>; the
underlying government data keeps its own licence terms. Figures here are derived from
public data and are not official statistics of either agency.
<p style="margin:10px 0 0">{DISCLAIMER}</p>
<p style="margin:10px 0 0">Page built {BUILT}.</p>
</footer>"""


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main():
    import site_pages
    import site_report

    d = load()

    pages = [
        (
            "report.html",
            "Ontario rental disputes: what they cost and who pays",
            "A ledger of Ontario's Landlord and Tenant Board built from the Board's "
            "own order export and the 2021 Census, reporting findings in both "
            "directions.",
            site_report.build(d),
        ),
        (
            "sources.html",
            "Sources and provenance | Ontario LTB Data",
            "Every source behind the Ontario LTB analysis, its licence, the period "
            "it covers, and which figure came from where.",
            site_pages.build_sources(d),
        ),
        (
            "onepager.html",
            "Briefing note | Ontario rental disputes",
            "A one-page, print-ready summary of what Ontario's public rental "
            "dispute records show.",
            site_pages.build_onepager(d),
            "",
        ),
        (
            "index.html",
            "Ontario LTB Data",
            "What Ontario's own public records show about its rental disputes: "
            "who files, what it costs, and who pays. Built entirely from open data.",
            site_pages.build_index(d),
            site_pages.INDEX_CSS,
        ),
    ]

    for entry in pages:
        filename, title, description, body = entry[:4]
        extra_css = entry[4] if len(entry) > 4 else ""
        html = shell(title, description, body + footer(), extra_css)
        (BASE / filename).write_text(html, encoding="utf-8")
        print(f"  wrote {filename:16s} {len(html) / 1024:6.1f} KB")

    print(f"\nBuilt from window {d['summary']['first_date']} to "
          f"{d['summary']['last_date']} ({d['summary']['days']} days)")


if __name__ == "__main__":
    main()
