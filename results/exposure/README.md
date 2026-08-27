# Exposure: how much of the picture the LTB record covers

Built by `scripts/analyze_exposure.py`.

**Window.** This export covers 2026-01-02 to 2026-05-29 - 148 days, not a full year and not all time. Annual figures below are that window multiplied by 2.466. Ontario publishes one rolling current-year file, so no earlier period is available to compare against.

## 1. How big is this next to the whole tenancy picture?

Ontario has **1,724,970 renter households** (2021 Census). Three independent routes to the annual number of landlord-filed cases:

| Route | Cases/year | Share of renter households | |
|---|---:|---:|---|
| This export, landlord-filed cases, annualised | 77,602 | 4.5% | 1 in 22 |
| This export, distinct rental units, annualised | 70,275 | 4.07% | 1 in 25 |
| Tribunals Ontario, landlord applications received 2024-25 | 72,836 | 4.22% | 1 in 24 |

The three agree, which matters: the middle route is this dataset counting distinct units, and the third is the Board's own published intake for a different year. **Roughly 1 in 24 Ontario renter households has a case filed against it each year.**

Two comparisons that keep the number honest:

* The United States rate is **8.0%** of renter households (Eviction Lab, 2024) - about twice Ontario's. Ontario is a normal-sized eviction system by international standards. The findings elsewhere in this repository are about what it does, not about it being unusually large.
* Only about **1.0%** of Canadian renters are actually evicted in a year (CMHC, 2025, counting formal and informal). An application is not an eviction: most non-payment cases end with the tenant paying and staying. Anyone quoting the filing rate as an eviction rate is wrong, in either direction.

## 2. What about the disputes that never reach the Board?

The LTB record and tenants' own accounts describe different populations:

| Reason | Share of LTB landlord cases | Share of evictions tenants report |
|---|---:|---:|
| Behind on rent | **63.4%** | **8%** |
| Every other reason | 36.6% | 92% |

Non-payment dominates the Board because a landlord needs an order to recover money. The reasons tenants most often give for an eviction - the landlord sold (37%), wanted the unit (26%), or was renovating (10%) - mostly end with the tenant leaving on a notice, generating no order and no record. The Board's file is a biased sample of evictions, not a census of them, and it is biased toward the money cases in both directions.

This cuts against a simple reading either way: it means the LTB record understates how often tenants lose housing, *and* it means the LTB record is not evidence about the frequency of the no-fault evictions it barely contains.

*Caveat:* L2 bundles landlord's-own-use, demolition/renovation and conduct-based applications into one code, so the LTB side cannot be split further without reading the orders themselves.

## 3. Is any of this related to income?

Across 371 FSAs with enough renter households to give a stable rate, Spearman rank correlations:

| Rate | Census measure | FSAs | Pearson r | Spearman rho |
|---|---|---:|---:|---:|
| Landlord cases per 1,000 renter households | Median household income | 371 | -0.052 | -0.119 |
| Landlord cases per 1,000 renter households | % of tenants in core housing need | 371 | +0.292 | +0.258 |
| Landlord cases per 1,000 renter households | % of tenants paying 30%+ on shelter | 371 | -0.080 | -0.086 |
| Landlord cases per 1,000 renter households | % of households renting | 371 | -0.029 | -0.011 |
| Landlord cases per 1,000 renter households | Average monthly rent | 371 | -0.089 | -0.137 |
| Landlord cases per 1,000 renter households | Annual rent as % of median income | 371 | -0.062 | -0.006 |
| Tenant cases per landlord case (who can use the Board) | Median household income | 371 | +0.294 | +0.292 |
| Tenant cases per landlord case (who can use the Board) | % of tenants in core housing need | 371 | -0.205 | -0.206 |
| Tenant cases per landlord case (who can use the Board) | % of tenants paying 30%+ on shelter | 371 | +0.258 | +0.259 |
| Tenant cases per landlord case (who can use the Board) | % of households renting | 371 | -0.206 | -0.276 |
| Tenant cases per landlord case (who can use the Board) | Average monthly rent | 371 | +0.344 | +0.304 |
| Tenant cases per landlord case (who can use the Board) | Annual rent as % of median income | 371 | +0.134 | +0.024 |

**Read these as weak.** The strongest association here is average monthly rent against tenant cases per landlord case (who can use the Board), at rho = +0.304 - which accounts for about 9% of the variation between areas. Two conclusions follow, and the second is the one people get wrong:

1. **How often landlords file is close to unrelated to how rich an area is** (rho = -0.119, about 1% of the variation). Rental disputes are not concentrated in poor postal codes in any strong sense. A claim in either direction that they are is not supported here.
2. **Whether tenants themselves use the Board is modestly related to income** - higher-income, higher-rent areas produce more tenant-filed cases per landlord-filed case. Real, consistent across three separate census measures, and still small.

### Who can actually use the Board

Tenant-filed cases per landlord-filed case, by area. A low ratio means tenants in that area appear at the Board almost only as respondents. Only FSAs with at least 100 landlord cases are named: below that a single filing moves the ratio enough to invent a ranking.

| | FSA | Landlord cases | Tenant cases | Ratio |
|---|---|---:|---:|---:|
| lowest | M3N | 356 | 9 | 0.025 |
| lowest | L4T | 199 | 6 | 0.030 |
| lowest | M3L | 127 | 5 | 0.039 |
| lowest | M9M | 154 | 6 | 0.039 |
| lowest | L6T | 239 | 11 | 0.046 |
| **median** | | | | **0.142** |
| highest | K1L | 107 | 30 | 0.280 |
| highest | M2N | 122 | 35 | 0.287 |
| highest | M5R | 113 | 35 | 0.310 |
| highest | N2L | 151 | 69 | 0.457 |
| highest | M5V | 156 | 97 | 0.622 |

Between the 10th and 90th percentile of these 101 areas the ratio runs 0.064 to 0.225, a **4-fold** spread. That percentile range is quoted rather than the extremes because the single lowest area has almost no tenant filings at all and dividing by it produces an arbitrarily large multiple.

## Method and limits

* **Denominator.** Renter households, not residents. An area that is 80% renters will show more rental disputes per resident than one that is 20% renters without anything else differing, so a per-resident rate mostly measures tenure mix. Population-normalised versions of the maps are kept for continuity but the renter-household rate is the defensible one.
* **Cases, not orders.** Counts here are unique file numbers. The raw export has more rows than cases because review and amended orders repeat a file.
* **Correlation is not cause.** These are area-level associations. An association at the area level does not license a claim about any individual household or landlord in that area.
* **Small areas excluded.** FSAs under 500 renter households or 20 landlord cases are kept in the CSV but left out of correlations and rankings, where a handful of cases would swing the rate.
