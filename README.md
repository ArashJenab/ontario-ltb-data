# Ontario LTB Data

What Ontario's own public records show about who wins at the Landlord and Tenant Board, and where disputes concentrate — built entirely from open data: the LTB's own order export and Statistics Canada's census.

**[→ Open the interactive map](https://arashjenab.github.io/ontario-ltb-data/map.html)** (or [by city](https://arashjenab.github.io/ontario-ltb-data/city-map.html)) · **[→ Read the 2-page summary](reports/executive-summary.md)**

![Map preview](docs/map-preview.png)

## The headline numbers

- **Landlords file 5.7× more often than tenants** — 34,422 landlord-filed applications vs. 6,043 tenant-filed, out of 40,844 total. This is an exact count of the full public dataset, not an estimate.
- **Landlords are awarded an estimated 26–74× more money than tenants** — roughly $130M in landlord-side awards (non-payment of rent, breach of settlement, other evictions) vs. $4.9M in tenant-side awards (rebates, maintenance remedies, compensation), depending on sampling design. The gap isn't only volume: landlords also average ~3.7× more *per case* ($4,249 vs. $1,143) than tenants do. See [`reports/executive-summary.md`](reports/executive-summary.md) and [`results/landlord_vs_tenant_overview/`](results/landlord_vs_tenant_overview/) for the range and methodology.
- **Dispute activity is geographically concentrated** — once normalized by population, the highest-activity areas (Hamilton, London, parts of Etobicoke, Sudbury, Ottawa) run ~7× the provincial median rate. Raw volume alone points somewhere else entirely: Toronto has the single highest case count in the province but drops well down the list once population is accounted for. Available both [by postal FSA](map.html) and [by municipality](city-map.html).

## What's here

| | |
|---|---|
| **[`map.html`](map.html)** / **[`city-map.html`](city-map.html)** | Interactive, zoomable choropleths — by postal FSA (520 areas) or by municipality (Toronto, Hamilton, etc.) — toggle raw counts vs. per-10,000-resident rates, and total vs. landlord-filed vs. tenant-filed. Self-contained, work offline. |
| **[`reports/executive-summary.md`](reports/executive-summary.md)** / **[`report.html`](report.html)** | 2-page summary of all findings, written for a general/policy audience. |
| **[`data/`](data/)** | Source data (the LTB export, the StatsCan population tables) and every derived dataset, each documented in its own README. |
| **[`results/`](results/)** | Every chart and CSV behind the findings above, organized one folder per analysis, each with the exact numbers, the command that built it, and its caveats. |
| **[`scripts/`](scripts/)** | The full pipeline, in Python — reproducible end to end from the source files in `data/`. |

## Reproduce it yourself

```bash
pip install pandas matplotlib pymupdf pytesseract pillow requests shapely numpy
# Tesseract-OCR must also be installed separately (system package, not pip) — only
# needed for the ~1% of order PDFs that are scanned images rather than native text.

python scripts/make_chart.py                                    # application volume by category
python scripts/postal_analysis.py                                # raw application counts by FSA
python scripts/normalize_fsa_by_population.py                    # + population-normalized rates
python scripts/extract_amounts.py --n 100 \
  --outdir results/amounts_equal_sample_100_per_category         # dollar-amount extraction (downloads PDFs)
python scripts/make_perspective_chart.py --n 100 \
  --outdir amounts_equal_sample_100_per_category                 # landlord vs. tenant $ chart
python scripts/fetch_fsa_boundaries.py                           # Ontario FSA polygons (~94MB, not kept in repo)
python scripts/simplify_fsa_boundaries.py
python scripts/build_fsa_map_data.py
python scripts/build_fsa_map_html.py                             # -> the FSA-level interactive map

python scripts/fetch_csd_population.py                           # municipality population (from data/raw_statcan_98100002)
python scripts/fetch_csd_boundaries.py                           # Ontario municipality polygons (~95MB, not kept in repo)
python scripts/simplify_csd_boundaries.py
python scripts/join_fsa_to_csd.py                                # rolls FSA-level counts up to municipality, by area-weighted overlap
python scripts/build_csd_map_data.py
python scripts/build_csd_map_html.py                             # -> the city-level interactive map

python scripts/make_overview_chart.py                            # the landlord-vs-tenant "big picture" donut chart
```

Full detail, exact flags, and what each output means: every folder under `results/` and `data/` has its own README. `scripts/extract_amounts.py --help` and `--allocation proportional` cover the two sampling designs used for the dollar-amount estimates.

**Not included in this repo**: the ~600 downloaded order PDFs used for the dollar-amount extraction (would be several GB; `scripts/extract_amounts.py` re-downloads and caches them locally into a git-ignored `pdfs/` folder on demand) and the raw ~95MB pre-simplification FSA and municipality boundary files (`fetch_fsa_boundaries.py` / `fetch_csd_boundaries.py` re-fetch them if you need a different simplification tolerance).

## Data sources & licensing

Built from two public sources — no private or scraped data:

- **Ontario Landlord and Tenant Board**, open-data order export (40,844 records)
- **Statistics Canada**, table 98-10-0019-01 (population by postal FSA) and table 98-10-0002-01 (population by municipality), 2021 Census, plus the corresponding Cartographic Boundary Files

See [`DATA_SOURCES.md`](DATA_SOURCES.md) for full attribution and license terms for both. The code in this repository is [MIT-licensed](LICENSE); the underlying government data remains subject to its own open-government license terms, not this repo's license.

## A note on the estimates

Application-count and geographic figures are exact counts of the full public dataset — no sampling involved. Dollar-amount figures required downloading and reading a sample of order PDFs individually (the open-data export lists case metadata but not the amount each order states), so those numbers are **estimates**, not a census, and are presented with the sampling method and margin discussion alongside them throughout. Nothing here should be read as more precise than it actually is — see [`reports/executive-summary.md`](reports/executive-summary.md) and the relevant `results/` folders for exactly how each number was produced.
