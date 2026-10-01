# Who carries the money at stake

Built by `scripts/analyze_who_pays.py`. No landlord is named in any output here; the question is how the burden splits across kinds of owner.

## What a landlord looks like at the LTB

Of 15,994 distinct landlords bringing 37,682 cases in the export window:

| | Individual owners | Corporate / institutional |
|---|---:|---:|
| Landlords | 10,873 | 5,121 |
| Share of cases | 37.6% | 62.4% |
| Filed exactly once | 84.3% | 60.4% |
| Hold a single address | 90.5% | 61.8% |
| Mean cases each | 1.3 | 4.59 |

For 84.3% of individual owners this is a single event at their only property. For the corporate side it is a recurring process. That difference is what the aggregate dollar figure hides.

## The dollar estimate, disaggregated

Estimated total at stake across L1, L2 and L4: **$148.1M**.

| | Individual owners | Corporate / institutional |
|---|---:|---:|
| Share of the money | 33.6% | 66.4% |
| Mean per landlord | $5,325 | $21,205 |
| 90th percentile | $9,099 | $30,003 |
| Median per landlord | $5,226 | $5,226 |

> **Superseded in part.** `results/burden/` reads the rent and amount out of individual orders instead of applying a category average, and finds that an individual owner's median case is *larger* than a corporate one ($7,229 against $5,108, after 4.04 months against 3.14). The model below cannot see that difference by construction, because it gives every landlord in a category the same per-case average. Prefer the measured figures for anything per-case; the model remains the basis for province-wide totals.

**The two medians are identical, and that is an artifact, not a finding.** Under this model every landlord whose only case is one L1 receives the same estimate, and the median landlord of both kinds is exactly that. The median is therefore uninformative about the difference between them; the mean and the 90th percentile are the columns that carry it. A corporate owner is owed roughly 4.0 times as much on average, because it brings many cases, not because its cases are individually larger.

The model gives every landlord in a category the same per-case average, so the only thing it can vary between kinds of owner is how many cases each brings. Do not read a per-case conclusion out of it. What it does support: at Ontario's household-weighted average rent of $1,407/month (2021 census), a case of this typical size is **3.7 months of rent**, or **30.9% of a unit's annual gross revenue** before mortgage, tax or repairs, and that 90.5% of individual owners have no second property to spread it across while a corporate owner does.

## Concentration

Gini coefficient of filings per landlord: **0.541** (0 would mean every landlord files equally often).

| Top N landlords | Share of landlords | Share of cases |
|---:|---:|---:|
| 1 | 0.01% | 3.2% |
| 10 | 0.06% | 13.9% |
| 25 | 0.16% | 19.4% |
| 50 | 0.31% | 24.4% |
| 100 | 0.63% | 29.8% |
| 250 | 1.56% | 37.6% |
| 500 | 3.13% | 44.3% |
| 1000 | 6.25% | 51.2% |
| 2500 | 15.63% | 60.9% |
| 5000 | 31.26% | 70.8% |

12,253 landlords (76.6%) filed exactly one case.

## Application mix by kind of owner

| Code | Meaning | Cases | Individual | Corporate |
|---|---|---:|---:|---:|
| L1 | Non-payment of rent | 23,988 | 33.4% | 66.6% |
| L2 | End tenancy (other reasons) | 5,877 | 51.2% | 48.8% |
| L4 | Breached a settlement or order | 4,554 | 30.3% | 69.7% |
| L10 | Collect money from a former tenant | 965 | 77.5% | 22.5% |
| L3 | Tenant gave notice but stayed | 936 | 69.1% | 30.9% |
| L5 | Above-guideline rent increase | 630 | 20.6% | 79.4% |
| L9 | Collect rent during tenancy | 460 | 32.0% | 68.0% |
| A2 | Application about a mobile home site | 210 | 31.9% | 68.1% |
| A1 | Whether the Act applies | 55 | 81.8% | 18.2% |

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
