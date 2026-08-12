# Ontario's Landlord and Tenant Board, By the Numbers

*An open-data analysis — August 2026*

**In one sentence:** Ontario's own public records show landlords filing more than five times as often as tenants and being awarded at least 26 times as much money, dispute activity is heavily concentrated in specific neighbourhoods once population is accounted for, and no public agency currently shows any of this to the people it affects.

This analysis uses only two public sources — the LTB's own open-data order export (40,844 records) and Statistics Canada's 2021 Census — and nothing else. All figures, code, and underlying data are public: **[github.com/ArashJenab/ontario-ltb-data](https://github.com/ArashJenab/ontario-ltb-data)**.

## Finding 1: Landlords are awarded far more than tenants

Sampling completed LTB orders and reading the dollar amount each one actually states, landlords were awarded an estimated **$130 million** against tenants — non-payment of rent, breach of a settlement, and other landlord-filed evictions — versus an estimated **$4.9 million** awarded to tenants, across rent rebates, maintenance remedies, and tenant-rights compensation combined.

| Sampling design | Landlord-side awards | Tenant-side awards | Ratio |
|---|---:|---:|---:|
| 100 orders / category (balanced) | $130M | $4.9M | **26 : 1** |
| 10 orders / category (pilot) | $81M | $2.2M | 37 : 1 |
| Budget split by category size | $151M | $2.0M | 74 : 1 |

Three independent sampling designs put the ratio anywhere from 26 to 1 up to 74 to 1. None came close to parity, and the true figure — a full accounting would require reading all 40,844 orders rather than a sample — is unlikely to be smaller than the most conservative estimate here.

## Finding 2: Landlords file over 5 times as often — no estimation required

Independent of any dollar figure, this is a direct count of the complete public dataset, not a sample: of all 40,844 applications on record, **34,422 (84%) were filed by landlords** against tenants, versus **6,043 (15%) filed by tenants** against landlords. Landlords bring cases to the Board 5.7 times more often than tenants do.

## Finding 3: Dispute activity is concentrated in specific areas — but not the ones raw counts suggest

Normalizing filings against each area's population (rather than raw counts, which just track population density) surfaces a very different map. The highest-activity postal areas — Hamilton's L8N, London's N6B, parts of Etobicoke, Sudbury, and Ottawa — see roughly **7 times the provincial median rate** of LTB activity per resident, and there is an **8-fold gap** between the most- and least-active areas once tiny-population outliers are excluded.

Raw counts alone point somewhere else entirely: Toronto's M3N has the single highest number of applications in the province, but drops to 11th place once its (large) population is factored in. Whether an area looks "high-activity" depends entirely on whether the analysis accounts for population — and to date, nothing public does.

## How this was built

Application-filing counts and geographic figures (Findings 2 and 3) are exact counts of the full public dataset — no estimation involved. Dollar figures (Finding 1) required downloading and reading a sample of order PDFs individually, since the open-data export lists case metadata but not the amounts each order states; reading all 40,844 documents was outside this pass's scope, so those numbers are estimates, not a census, and should be read as order-of-magnitude rather than precise. An interactive, population-normalized map of dispute activity by postal area — built from the same two public sources — accompanies this report.

## Why this matters

Nothing in this analysis required data the government doesn't already hold. The LTB already publishes its order records; Statistics Canada already publishes population by area. Putting the two together — enough to build the map and the figures above — took a few days' work with public tools. No public agency currently does this, so residents, journalists, and elected officials assessing whether the Board is working as intended have no way to see it for themselves.

Two things follow. First, a public dashboard along these lines would cost a fraction of many other provincial data initiatives and would let anyone check these numbers directly rather than take a private analysis's word for it. Second, once the disparity is visible, it raises a legitimate question for legislative attention: is a 26-to-1-or-worse gap between landlord- and tenant-side outcomes explained by the underlying merits of the cases the Board hears, or does it point to something structural worth examining?

---
*Prepared from the Landlord and Tenant Board open-data export and Statistics Canada table 98-10-0019-01 (2021 Census, population by forward sortation area). Methodology, raw data, and the full sampling comparison are available alongside this report.*
