# Who carries the money at stake

Built by `scripts/analyze_who_pays.py`. No landlord is named in any output here; the question is how the burden splits across kinds of owner.

## What a landlord looks like at the LTB

Of 13,808 distinct landlords bringing 31,463 cases in the export window:

| | Individual owners | Corporate / institutional |
|---|---:|---:|
| Landlords | 9,291 | 4,517 |
| Share of cases | 37.7% | 62.3% |
| Filed exactly once | 85.8% | 61.3% |
| Hold a single address | 91.1% | 63.0% |
| Mean cases each | 1.28 | 4.34 |

For 85.8% of individual owners this is a single event at their only property. For the corporate side it is a recurring process. That difference is what the aggregate dollar figure hides.

## The dollar estimate, disaggregated

Estimated total at stake across L1, L2 and L4: **$123.5M**.

| | Individual owners | Corporate / institutional |
|---|---:|---:|
| Share of the money | 33.4% | 66.6% |
| Median per landlord | $5,226 | $5,226 |
| Mean per landlord | $5,193 | $20,133 |
| 90th percentile | $6,088 | $29,511 |

At Ontario's household-weighted average rent of $1,407/month (2021 census), the median individual owner's $5,226 is **3.7 months of rent**, or **30.9% of that unit's annual gross revenue** before mortgage, tax or repairs. The same median for a corporate owner is one line item among many.

## Concentration

Gini coefficient of filings per landlord: **0.529** (0 would mean every landlord files equally often).

| Top N landlords | Share of landlords | Share of cases |
|---:|---:|---:|
| 1 | 0.01% | 3.4% |
| 10 | 0.07% | 14.1% |
| 25 | 0.18% | 19.8% |
| 50 | 0.36% | 24.8% |
| 100 | 0.72% | 30.3% |
| 250 | 1.81% | 38.1% |
| 500 | 3.62% | 44.8% |
| 1000 | 7.24% | 51.6% |
| 2500 | 18.11% | 62.2% |
| 5000 | 36.21% | 72.0% |

10,738 landlords (77.8%) filed exactly one case.

## Application mix by kind of owner

| Code | Meaning | Cases | Individual | Corporate |
|---|---|---:|---:|---:|
| L1 | Non-payment of rent | 19,951 | 33.2% | 66.8% |
| L2 | End tenancy, other reasons | 4,879 | 52.0% | 48.0% |
| L4 | Breached a settlement or order | 3,877 | 29.9% | 70.1% |
| L10 | Collect money from a former tenant | 867 | 77.0% | 23.0% |
| L3 | Tenant gave notice, did not leave | 742 | 69.4% | 30.6% |
| L5 | Above-guideline rent increase | 528 | 22.5% | 77.5% |
| L9 | Collect rent, tenancy continuing | 374 | 35.3% | 64.7% |
| A2 | Application about a mobile home site | 192 | 31.2% | 68.8% |

Read both directions. Individual owners dominate the categories about recovering money from someone who has already gone (L10) and about a tenant who gave notice and stayed (L3). Corporate owners dominate above-guideline rent increases (L5).

## Method and limits

**Classification.** A landlord is treated as corporate or institutional if the name contains a company/organisation token or a six-or-more digit run (a numbered Ontario company). This is inclusive of public and non-profit providers: the distinction drawn is 'an organisation with staff and a process' versus 'a person who owns a unit', not for-profit versus not. Individual owners who file under a numbered company are counted as corporate, so the individual-owner share here is a floor, not a ceiling.

**Name matching.** Spelling and suffix variants are collapsed to one key (case, punctuation, Inc/Ltd/LP, and anything after 'c/o'). Genuinely distinct landlords who share a canonical name are merged, and one landlord using two unrelated spellings is still counted twice. Concentration figures are therefore approximate at the margin.

**Dollar figures are estimates, not a census.** They extrapolate a sample of order PDFs: `cases x found_rate x mean amount`, per category. Orders stating no amount count as zero, which understates rather than overstates. Sample sizes and found rates used here:

| Category | Sample n | Found rate | Mean amount |
|---|---:|---:|---:|
| L1 | 100 | 0.74 | $7,062 |
| L2 | 100 | 0.37 | $2,330 |
| L4 | 100 | 0.73 | $5,305 |

**Window.** The export covers a single period, not all time. See the top of `data/README.md` for the exact date range; every rate here is over that window unless it says annualised.
