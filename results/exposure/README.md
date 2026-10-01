# Exposure: how much of the picture the LTB record covers

Built by `scripts/analyze_exposure.py`.

**Window.** This export covers 2026-01-02 to 2026-06-30 - 180 days, not a full year and not all time. Annual figures below are that window multiplied by 2.028. Ontario publishes one rolling current-year file, so no earlier period is available to compare against.

## 1. How big is this next to the whole tenancy picture?

Ontario has **1,724,970 renter households** (2021 Census). Three independent routes to the annual number of landlord-filed cases:

| Route | Cases/year | Share of renter households | |
|---|---:|---:|---|
| This export, landlord-filed cases, annualised | 76,417 | 4.43% | 1 in 23 |
| This export, distinct rental units, annualised | 68,310 | 3.96% | 1 in 25 |
| Tribunals Ontario, landlord applications received 2024-25 | 72,836 | 4.22% | 1 in 24 |

The three agree, which matters: the middle route is this dataset counting distinct units, and the third is the Board's own published intake for a different year. **Roughly 1 in 24 Ontario renter households has a case filed against it each year.**

Two comparisons that keep the number honest:

* The United States rate is **8.0%** of renter households (Eviction Lab, 2024) - about twice Ontario's. Ontario is a normal-sized eviction system by international standards. The findings elsewhere in this repository are about what it does, not about it being unusually large.
* Only about **1.0%** of Canadian renters are actually evicted in a year (CMHC, 2025, counting formal and informal). An application is not an eviction: most non-payment cases end with the tenant paying and staying. Anyone quoting the filing rate as an eviction rate is wrong, in either direction.

## 2. What about the disputes that never reach the Board?

The LTB record and tenants' own accounts describe different populations:

| Reason | Share of LTB landlord cases | Share of evictions tenants report |
|---|---:|---:|
| Behind on rent | **63.7%** | **8%** |
| Every other reason | 36.3% | 92% |

Non-payment dominates the Board because a landlord needs an order to recover money. The reasons tenants most often give for an eviction - the landlord sold (37%), wanted the unit (26%), or was renovating (10%) - mostly end with the tenant leaving on a notice, generating no order and no record. The Board's file is a biased sample of evictions, not a census of them, and it is biased toward the money cases in both directions.

This cuts against a simple reading either way: it means the LTB record understates how often tenants lose housing, *and* it means the LTB record is not evidence about the frequency of the no-fault evictions it barely contains.

*Caveat:* L2 bundles landlord's-own-use, demolition/renovation and conduct-based applications into one code, so the LTB side cannot be split further without reading the orders themselves.

## 3. Is any of this related to income?

Across 395 FSAs with enough renter households to give a stable rate, Spearman rank correlations:

| Rate | Census measure | FSAs | Pearson r | Spearman rho |
|---|---|---:|---:|---:|
| Landlord cases per 1,000 renter households | Median household income | 395 | -0.069 | -0.128 |
| Landlord cases per 1,000 renter households | % of tenants in core housing need | 395 | +0.285 | +0.240 |
| Landlord cases per 1,000 renter households | % of tenants paying 30%+ on shelter | 395 | -0.075 | -0.090 |
| Landlord cases per 1,000 renter households | % of households renting | 395 | -0.002 | +0.016 |
| Landlord cases per 1,000 renter households | Average monthly rent | 395 | -0.079 | -0.126 |
| Landlord cases per 1,000 renter households | Annual rent as % of median income | 395 | -0.029 | +0.030 |
| Tenant cases per landlord case (who can use the Board) | Median household income | 395 | +0.293 | +0.305 |
| Tenant cases per landlord case (who can use the Board) | % of tenants in core housing need | 395 | -0.192 | -0.179 |
| Tenant cases per landlord case (who can use the Board) | % of tenants paying 30%+ on shelter | 395 | +0.265 | +0.264 |
| Tenant cases per landlord case (who can use the Board) | % of households renting | 395 | -0.189 | -0.274 |
| Tenant cases per landlord case (who can use the Board) | Average monthly rent | 395 | +0.349 | +0.320 |
| Tenant cases per landlord case (who can use the Board) | Annual rent as % of median income | 395 | +0.139 | +0.028 |

**Read these as weak.** The strongest association here is average monthly rent against tenant cases per landlord case (who can use the Board), at rho = +0.320 - which accounts for about 10% of the variation between areas. Two conclusions follow, and the second is the one people get wrong:

1. **How often landlords file is close to unrelated to how rich an area is** (rho = -0.128, about 1% of the variation). Rental disputes are not concentrated in poor postal codes in any strong sense. A claim in either direction that they are is not supported here.
2. **Whether tenants themselves use the Board is modestly related to income** - higher-income, higher-rent areas produce more tenant-filed cases per landlord-filed case. Real, consistent across three separate census measures, and still small.

### Who can actually use the Board

Tenant-filed cases per landlord-filed case, by area. A low ratio means tenants in that area appear at the Board almost only as respondents. Only FSAs with at least 100 landlord cases are named: below that a single filing moves the ratio enough to invent a ranking.

| | FSA | Landlord cases | Tenant cases | Ratio |
|---|---|---:|---:|---:|
| lowest | N8T | 102 | 3 | 0.029 |
| lowest | M3N | 429 | 13 | 0.030 |
| lowest | L4T | 213 | 7 | 0.033 |
| lowest | M3L | 153 | 5 | 0.033 |
| lowest | M9M | 200 | 8 | 0.040 |
| **median** | | | | **0.149** |
| highest | K0K | 108 | 32 | 0.296 |
| highest | M6J | 105 | 32 | 0.305 |
| highest | M5B | 104 | 33 | 0.317 |
| highest | N2L | 191 | 82 | 0.429 |
| highest | M5V | 173 | 119 | 0.688 |

Between the 10th and 90th percentile of these 130 areas the ratio runs 0.076 to 0.250, a **3-fold** spread. That percentile range is quoted rather than the extremes because the single lowest area has almost no tenant filings at all and dividing by it produces an arbitrarily large multiple.

## Method and limits

* **Denominator.** Renter households, not residents. An area that is 80% renters will show more rental disputes per resident than one that is 20% renters without anything else differing, so a per-resident rate mostly measures tenure mix. Population-normalised versions of the maps are kept for continuity but the renter-household rate is the defensible one.
* **Cases, not orders.** Counts here are unique file numbers. The raw export has more rows than cases because review and amended orders repeat a file.
* **Correlation is not cause.** These are area-level associations. An association at the area level does not license a claim about any individual household or landlord in that area.
* **Small areas excluded.** FSAs under 500 renter households or 20 landlord cases are kept in the CSV but left out of correlations and rankings, where a handful of cases would swing the rate.
