# Data

Source data and derived datasets. Everything in [`results/`](../results/) is built from what's here.

## Files

| File | What it is |
|---|---|
| `ltb_open_data_export.json` | The LTB's own open-data export — 40,844 order records. Source of truth for every finding in this repo. |
| `fsa_population.csv` | `fsa`, `population` — 1,646 FSAs, all of Canada, 2021 Census. |
| `fsa_applications_normalized.csv` | [`results/applications_by_area/fsa_application_counts.csv`](../results/applications_by_area/) joined with `fsa_population.csv`, plus `total_applications_per_10k`, `landlord_filed_per_10k`, `tenant_filed_per_10k` — applications per 10,000 residents, sorted descending. |
| `ontario_fsa_simplified.geojson` | Ontario FSA boundary polygons (520 of them), simplified from StatCan's full cartographic detail (94MB → 3.5MB, ~400m tolerance) so they're usable as inline SVG. |
| `fsa_map_payload.json` | `ontario_fsa_simplified.geojson` polygons projected to SVG path coordinates + `fsa_applications_normalized.csv` stats joined in per FSA, plus a `focusView` bounding box (see below) — the exact payload embedded in [`../map.html`](../map.html). |
| `csd_population.csv` | `csduid`, `name`, `population` — 564 Ontario municipalities (Census Subdivisions), 2021 Census. |
| `csd_applications_normalized.csv` | FSA-level application counts rolled up to municipality by **area-weighted overlap** (not the FSA join above — see `results/applications_by_city/README.md` for why centroid-based assignment doesn't work here), joined with `csd_population.csv`, plus the same three `*_per_10k` columns and an `fsa_count` column (how many FSAs, possibly fractional, contributed). |
| `ontario_csd_simplified.geojson` | Ontario municipality boundary polygons (577 of them), simplified the same way as the FSA polygons (94MB → 3.6MB). |
| `csd_map_payload.json` | The municipality-level counterpart to `fsa_map_payload.json` — embedded in [`../city-map.html`](../city-map.html). |
| `raw_statcan_98100019/` | The untouched StatsCan FSA-population-table download (zip + extracted CSV + metadata), kept for provenance. |
| `raw_statcan_98100002/` | Same, for the municipality-population table. This one covers all of Canada at multiple geographic levels in a single file — `scripts/fetch_csd_population.py` filters it down to Ontario CSD-level rows. |

**`focusView`**: the map's default zoomed-in viewport, computed as the 2nd–98th percentile of application-*weighted* FSA centroids — most of Ontario's land area has close to zero LTB activity, so a plain bounding box of "any FSA with data" still spans the whole province. Weighting by volume instead crops to where the data actually is.

## The interactive map

Built from `fsa_map_payload.json`, lives at [`../map.html`](../map.html) (self-contained, works offline). Toggle between raw counts and per-10,000 rates, and between total/landlord-filed/tenant-filed; scroll to zoom, drag to pan, hover for the full breakdown, live top-10 ranking. Colored by **quantile rank** (equal-count bins), not a linear scale — the underlying distribution is heavily right-skewed enough that linear coloring left almost everything the same pale shade.

Regenerate with:
```bash
python scripts/fetch_fsa_boundaries.py     # Ontario FSA polygons from StatCan ArcGIS REST (~94MB raw, not kept in repo)
python scripts/simplify_fsa_boundaries.py  # -> ontario_fsa_simplified.geojson
python scripts/build_fsa_map_data.py       # -> fsa_map_payload.json (joins in the stats + focusView)
python scripts/build_fsa_map_html.py       # -> scripts/_build/fsa_dispute_map.html (copy to ../map.html)
```

## The city-level map

Same idea, rolled up to municipality (Toronto, Hamilton, Windsor, etc.) instead of postal FSA — lives at [`../city-map.html`](../city-map.html), cross-linked with the FSA map. Detail on the FSA→municipality join method (area-weighted overlap, and why a simpler centroid-based approach broke badly in rural areas) is in [`results/applications_by_city/README.md`](../results/applications_by_city/).

Regenerate with:
```bash
python scripts/fetch_csd_population.py     # -> csd_population.csv (from raw_statcan_98100002/)
python scripts/fetch_csd_boundaries.py     # Ontario municipality polygons (~95MB raw, not kept in repo)
python scripts/simplify_csd_boundaries.py  # -> ontario_csd_simplified.geojson
python scripts/join_fsa_to_csd.py          # -> csd_applications_normalized.csv
python scripts/build_csd_map_data.py       # -> csd_map_payload.json
python scripts/build_csd_map_html.py       # -> scripts/_build/csd_dispute_map.html (copy to ../city-map.html)
```

## Source

**Population**: Statistics Canada, table 98-10-0019-01, *"Population and dwelling counts: Canada and forward sortation areas"*, 2021 Census (released 2023-03-29).
[www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810001901](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810001901) · downloaded from the [CSV export](https://www150.statcan.gc.ca/n1/tbl/csv/98100019-eng.zip).

**FSA boundaries**: Statistics Canada 2021 Census Cartographic Boundary Files, queried via the [ArcGIS REST feature service](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/14) (layer 14 = FSA, WGS84 output).

**Municipality population**: Statistics Canada, table 98-10-0002-01, *"Population and dwelling counts: Canada and census subdivisions (municipalities)"*, 2021 Census. [www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810000201](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810000201) · downloaded from the [CSV export](https://www150.statcan.gc.ca/n1/tbl/csv/98100002-eng.zip). This table covers all of Canada at multiple geographic levels (country/province/division/subdivision) in one file — `scripts/fetch_csd_population.py` filters to CSD-level, Ontario only, using the `DGUID` field (a CSD-level row's DGUID ends in the 7-digit CSDUID, e.g. Toronto = `3520005`).

**Municipality boundaries**: same Cartographic Boundary Files service, [layer 9 = CSD](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/9).

**Application data**: Ontario Landlord and Tenant Board open-data export. See [`DATA_SOURCES.md`](../DATA_SOURCES.md) at the repo root for full licensing terms on both sources.

## How it was built

```bash
python scripts/normalize_fsa_by_population.py
```
Reads the StatsCan CSV, drops the national "Canada" total row, keeps the 3-character FSA rows, left-joins onto `fsa_application_counts.csv` on `fsa`. See the map sections above for the boundary-fetch → simplify → map-build chains (FSA and municipality).

**A bug worth knowing about if you touch `fetch_fsa_boundaries.py` or `fetch_csd_boundaries.py`**: Esri's "rings" geometry format doesn't nest holes inside their exterior ring the way GeoJSON does — a single Esri feature can contain several genuinely disjoint parts (e.g. a municipality with river islands), distinguished only by ring winding order, not nesting. An earlier version of both scripts dumped every ring into one GeoJSON `Polygon` (treating rings 2+ as holes of ring 1), which silently produced a degenerate near-empty shape for any feature with more than one true exterior ring — Windsor (which has ~20 ring parts) came out as a single point instead of a city. Both scripts now correctly reconstruct `Polygon`/`MultiPolygon` geometry from ring winding order (`esri_rings_to_geojson()`).

## Caveats

- 12 of the 524 FSAs present in the application data have no population match (likely retired/reassigned or non-residential FSAs) — all very low-volume (max 17 applications). They're in `fsa_applications_normalized.csv` with population/rate columns blank rather than silently dropped.
- Per-10k rates get noisy for low-population FSAs — a handful of applications in a small-population FSA can produce a misleadingly high rate. The normalize script's printed "top 15" filters to population ≥ 1,000 for this reason; the saved CSV itself keeps every row unfiltered.
- This is 2021 Census population (all residents), not renter/rental-unit counts specifically — an FSA with a high owner-occupied share will show a lower per-10k rate than its actual rental-market activity, since the denominator includes non-renters too.
- Every order in the source export was **issued** between 2026-01-02 and 2026-05-29 — a 5-month window (the underlying application may have been *filed* years earlier; LTB file numbers encode filing year, e.g. `-22`, but this dataset's date field is order-issuance date). Population is a single 2021 snapshot, so there's a uniform ~5-year gap between the two — worth keeping in mind for fast-growing FSAs, though it doesn't vary record-to-record the way a multi-year order-date span would.
- Boundary polygons are simplified to ~400m tolerance for file size — fine for a province-scale choropleth, not for precise area lookups.
- 11 Ontario FSAs on the boundary map never appear in the LTB export at all (genuinely zero applications, not missing data) and render grey/no-data in per-10k mode specifically, because population figures are only attached to FSAs that showed up in the application data in the first place — raw-count mode correctly shows these as 0 rather than grey.
- The map colors by quantile rank, not raw value — bin edges shift depending on which toggle is selected, so read the legend each time rather than assuming a color means the same rate across two different views.
- Municipality-level data (`csd_*`) has its own, more involved caveats around the FSA→municipality join method and a higher population reliability floor (10,000 vs. 1,000) — see [`results/applications_by_city/README.md`](../results/applications_by_city/).
