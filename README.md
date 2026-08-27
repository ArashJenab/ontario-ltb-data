# Ontario LTB Data

What Ontario's own public records show about its rental disputes: how many there are, who brings them, what they cost, and who carries the cost. Built entirely from open data: the Landlord and Tenant Board's order export and Statistics Canada's census.

**[→ Read the report](https://arashjenab.github.io/ontario-ltb-data/report.html)** · **[→ One-page briefing](https://arashjenab.github.io/ontario-ltb-data/onepager.html)** · **[→ Interactive map](https://arashjenab.github.io/ontario-ltb-data/map.html)** ([by city](https://arashjenab.github.io/ontario-ltb-data/city-map.html)) · **[→ Sources](https://arashjenab.github.io/ontario-ltb-data/sources.html)**

![Map preview](docs/map-preview.png)

## Read this first

The LTB publishes **one rolling current-year file**. The copy analysed here covers **2026-01-02 to 2026-05-29**: 148 days, not a full year and not all time. It holds 40,844 orders across 37,401 distinct cases, because review and amended orders repeat a case. Annual figures in this repository are that window annualised, and say so wherever they appear.

No earlier period is published anywhere, so no trend can be measured yet. `scripts/fetch_ltb_orders.py` snapshots every fetch into `data/snapshots/`, which is the only way a historical series will ever exist.

## What it found

**The scale is ordinary; the distribution is not.** About **1 in 24** Ontario renter households has a landlord case filed against it each year. Three independent routes agree: this export annualised, this export counting distinct units, and the Board's own published intake for 2024-25. That is roughly half the United States filing rate of ~8%. Meanwhile only about 1% of renters are actually evicted in a year, because an application is not an eviction.

**"Landlords" is not one group, and the aggregate hides it.** 9,291 individual owners bring 37.7% of cases; **85.8% of them file exactly once and 91.1% own a single address**. For them this is a one-time event at their only property. The 4,517 corporate and institutional owners bring 62.3%, at 4.3 cases each. The estimated $123.5M at stake splits 33% / 67%, but the median case is the same size on both sides: about **$5,226, which is 3.7 months of rent, or 31% of that unit's annual gross revenue** before mortgage, tax or repairs. A corporate owner is owed ~3.9x more on average because it brings more cases, not larger ones.

**The record is not a picture of eviction.** Non-payment is **63.4%** of the Board's landlord cases but only **8%** of the evictions tenants report to Statistics Canada. The reasons tenants most often give, that the landlord sold (37%) or wanted the unit (26%), usually end with the tenant leaving on a notice and leave no record. This cuts both ways: the file understates how often tenants lose housing, *and* it is not evidence about the frequency of the no-fault evictions it barely contains.

**A small group of tenants does behave differently.** 90% of tenants appear in exactly one case. The 10% who recur account for 19% of cases, and are taken to the Board for **breaching a settlement at 3.4x the rate** of one-time tenants. Most recur at the same address rather than moving on.

**The two sides do not get the same process.** **18.4%** of landlord-filed orders are made without a hearing, against **2.1%** of tenant-filed ones.

**Some things were tested and not found.** Area income barely predicts where landlords file (rank correlation −0.119, about 1% of the variation). There is no gendered pairing between the sides. The serial-tenant claim is not supported at this timescale, and the apparent top of that list turns out to be legal clinics named in the tenant field.

## What's here

| | |
|---|---|
| **[`report.html`](report.html)** | The main artifact. Nine sections, eleven charts, sources beside each number. |
| **[`onepager.html`](onepager.html)** | Print-ready one-page briefing. |
| **[`sources.html`](sources.html)** | Every source, its licence, its period, and which figure came from where. |
| **[`map.html`](map.html)** / **[`city-map.html`](city-map.html)** | Interactive choropleths by postal FSA (520 areas) or municipality. Self-contained, work offline. |
| **[`results/`](results/)** | One folder per analysis, each with its CSVs, its exact numbers, the command that built it, and its caveats. |
| **[`data/`](data/)** | Source data and every derived dataset, each documented. |
| **[`scripts/`](scripts/)** | The full pipeline in Python, reproducible end to end. |

## Reproduce it

```bash
pip install pandas matplotlib pymupdf pytesseract pillow requests shapely numpy \
            gender-guesser playwright
# Tesseract-OCR is a separate system package, needed only for the ~1% of order
# PDFs that are scanned images rather than native text.

# --- data ---------------------------------------------------------------
python scripts/fetch_ltb_orders.py            # the LTB export (also snapshots it)
python scripts/fetch_fsa_census_profile.py    # census profile by FSA: renter
                                              # households, income, rent, core need

# --- analysis -----------------------------------------------------------
python scripts/analyze_who_pays.py            # individual vs corporate, concentration,
                                              # the dollar estimate disaggregated
python scripts/analyze_exposure.py            # denominators, the reason mismatch,
                                              # income correlations by area
python scripts/analyze_parties.py             # repeat tenants, ex parte, gender

python scripts/extract_case_details.py --n 5000   # reads order PDFs: rent, hearing,
                                                  # attendance, representation
python scripts/analyze_burden.py                  # months of rent owed, with intervals

# --- the site -----------------------------------------------------------
python scripts/build_site.py                  # report, sources, one-pager, index
python scripts/check_pages.py                 # renders all four, light and dark,
                                              # desktop and phone, fails on overflow
```

The maps have their own pipeline (boundary fetch, simplification, join, build) unchanged from the previous version; see the commands in `scripts/` and the notes in `results/applications_by_area/`.

`scripts/ltbdata.py` is the shared loader: it defines once what counts as a corporate landlord, how a name cell splits into people, and the difference between an order and a case. Every analysis imports it.

**Not in this repository**: the order PDFs (`extract_*.py` re-download and cache them into a git-ignored `pdfs/`), the ~95MB raw boundary files, and the ~68MB raw census profile download. All are regenerated on demand.

## The two kinds of number here

**Exact counts.** Case volumes, application types, party classification, geography and ex parte rates are counted from the complete public export. No sampling. Exact for the window stated above.

**Estimates.** Every dollar figure. The export lists case metadata but not the amount each order states, so amounts come from downloading and reading order PDFs. Those are samples with a stated method, presented with their sample size and, in `results/burden/`, bootstrap confidence intervals. They are order-of-magnitude, not precise.

## Data sources & licensing

- **Ontario Landlord and Tenant Board**, order catalogue (Open Government Licence, Ontario)
- **Statistics Canada** (Statistics Canada Open Licence): Census Profile by FSA (98-401-X2021013), population by FSA (98-10-0019-01) and by municipality (98-10-0002-01), 2021 Cartographic Boundary Files
- **Tribunals Ontario** 2024-25 Annual Report, for the independent intake check
- **Statistics Canada** Canadian Housing Survey 2021 and **CMHC** (2025), for what tenants report and how many are actually evicted
- **The Eviction Lab**, Princeton University, for the international comparison

Full attribution, periods and caveats: [`sources.html`](sources.html) and [`DATA_SOURCES.md`](DATA_SOURCES.md). Code is [MIT-licensed](LICENSE); the underlying government data keeps its own terms.

## A note on what this is not

No landlord, tenant or address is named anywhere in these outputs. Where concentration or recurrence is reported it is as a distribution, not a list. Findings are reported in whichever direction they came out, including the ones that do not support the argument a reader might have arrived with.

This is an independent analysis developed using data published by the Government of Ontario. It is not an official publication of, and is not affiliated with or endorsed by, the Government of Ontario or the Landlord and Tenant Board.
