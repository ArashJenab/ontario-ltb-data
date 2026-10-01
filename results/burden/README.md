# What a dispute costs, measured from the orders themselves

Built by `scripts/analyze_burden.py` from `results/case_details/case_details_raw.csv`.

Orders state the rent inside the daily-rate calculation ("$2,285.11 x 12, divided by 365 days"), which makes it possible to express what a landlord is owed in months of that unit's own rent rather than in dollars. That is the comparison that means the same thing to a landlord with one unit and one with a thousand.

## Months of rent owed when the order issued

| Scope | Orders | Median | Mean | 95% interval |
|---|---:|---:|---:|---|
| All landlord money cases | 2,542 | 3.45 | 4.39 | 4.25 to 4.55 |
| L1 - Non-payment of rent | 1,952 | 3.68 | 4.62 | 4.45 to 4.79 |
| L2 - End tenancy (other reasons) | 101 | 1.12 | 2.38 | 1.8 to 3.07 |
| L4 - Breached a settlement or order | 489 | 2.81 | 3.91 | 3.57 to 4.27 |

The median landlord money case reaches an order with **3.45 months of rent** outstanding, on a unit renting at a median of $1,730/month.

## How that is distributed

| Months owed | Orders | Share |
|---|---:|---:|
| Under 1 month | 221 | 8.7% |
| 1 to 2 months | 400 | 15.7% |
| 2 to 3 months | 429 | 16.9% |
| 3 to 6 months | 913 | 35.9% |
| 6 to 12 months | 462 | 18.2% |
| Over 12 months | 117 | 4.6% |

**8.7% of orders are for less than a single month's rent**, and **4.6% are for more than a year's.** Both tails matter and they matter to different people: the short one is a tenancy ending over an amount smaller than one rent cheque, the long one is a landlord who has gone a year without income from the unit.

## Individual against corporate owners

| | Orders | Median months | Mean amount | 95% interval |
|---|---:|---:|---:|---|
| Individual | 953 | 4.06 | $9,790 | $9,233 to $10,371 |
| Corporate | 1,589 | 3.13 | $6,629 | $6,323 to $6,937 |

Per case the two are close, which is the finding. The difference between the two kinds of landlord is not the size of an individual loss but how many of them each carries and what share of income each represents.

## Who turned up, and who had help

| Party | Attended | Had a representative |
|---|---:|---:|
| Landlord | 90.6% | 74.4% |
| Tenant | 52.1% | 8.0% |

Read from orders that name who attended the hearing. An order that does not carry that sentence is excluded rather than scored as a no-show, so these are rates among orders that say, not among all orders.

## Method and limits

* **Sample.** 6,032 orders drawn across L1, L2 and L4 in proportion to how common each is, so an unweighted mean over the sample is already a population mean. Seeded, so the draw is reproducible.
* **Coverage.** A rent figure is recoverable from about 44% of sampled orders and both a rent and an amount from 2,542. Orders that state neither are excluded, and there is no guarantee they resemble those that do.
* **Intervals** are percentile bootstrap, 2,000 resamples. They express sampling error only. They say nothing about whether the extraction read each order correctly.
* **Ratios above 60 months** are dropped as parse failures rather than believed.
* **An amount ordered is not an amount collected.** Nothing in the public record says whether any of this was ever paid.
