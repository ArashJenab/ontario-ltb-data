# Data Sources

This project uses two public datasets. Neither is scraped, purchased, or private — both are published by their respective governments specifically for reuse.

## Ontario Landlord and Tenant Board — LTB Order Catalogue

- **Publisher**: Landlord and Tenant Board (Ontario Ministry of the Attorney General)
- **Dataset**: [LTB Order Catalogue](https://data.ontario.ca/dataset/ltb-order-catalogue), via the Ontario Data Catalogue
- **License**: [Open Government Licence – Ontario](https://www.ontario.ca/page/open-government-licence-ontario)
- **What it contains**: copies of final orders issued by the LTB, published in phases (historical orders from 2021 onward; orders subject to confidentiality orders are excluded)
- **Used here as**: `data/ltb_open_data_export.json` — the export snapshot this analysis is built from (40,844 records)

Under the Open Government Licence – Ontario, you're free to copy, modify, publish, translate, and distribute this information, including commercially, provided you attribute the source and don't imply endorsement by the Ontario government or the LTB. This repository's use complies with those terms; the license applies to the LTB data itself, independent of this repo's own [MIT license](LICENSE) on the analysis code.

## Statistics Canada — 2021 Census, population by Forward Sortation Area

- **Publisher**: Statistics Canada
- **Table**: 98-10-0019-01, *"Population and dwelling counts: Canada and forward sortation areas"* — [statcan.gc.ca](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810001901)
- **Boundaries**: 2021 Census Cartographic Boundary Files (FSA layer), via the [ArcGIS REST feature service](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/14)
- **License**: [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence)
- **Used here as**: `data/fsa_population.csv` (population lookup) and `data/ontario_fsa_simplified.geojson` (boundary polygons, simplified for file size — see `data/README.md`)

Under the Statistics Canada Open Licence, this data may be used, reproduced, and redistributed for any purpose, commercial or non-commercial, provided Statistics Canada is credited as the source. Attribution used throughout this repo: *"Statistics Canada, table 98-10-0019-01, 2021 Census."*

## What this repo adds

Everything in `results/` and `data/*normalized*` / `data/*payload*` is **derived** from the two sources above — joins, per-capita rates, sampled dollar-amount extractions, and the map. These derived outputs are original analysis and are covered by this repository's own [MIT license](LICENSE); they are not official statistics from either source agency, and neither agency has reviewed or endorsed this analysis.

## Reference year and currency of the data

The LTB export used here reflects orders available at the time of download (see `data/README.md` for the exact date range observed in the data). Population figures are the 2021 Census — the single most recent Census available at time of writing. Some drift between the two reference periods is expected and noted where relevant (e.g. `results/applications_by_area/README.md`).
