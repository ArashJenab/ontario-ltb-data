# What a dispute costs, measured from the orders themselves

Built by `scripts/analyze_burden.py` from `results/case_details/case_details_raw.csv`.

Orders state the rent inside the daily-rate calculation ("$2,285.11 x 12, divided by 365 days"), which makes it possible to express what a landlord is owed in months of that unit's own rent rather than in dollars. That is the comparison that means the same thing to a landlord with one unit and one with a thousand.

## Months of rent owed when the order issued

| Scope | Orders | Median | Mean | 95% interval |
|---|---:|---:|---:|---|
| All landlord money cases | 2,105 | 3.45 | 4.44 | 4.27 to 4.62 |
| L1 - Non-payment of rent | 1,627 | 3.7 | 4.66 | 4.49 to 4.85 |
| L2 - End tenancy (other reasons) | 80 | 1.09 | 2.2 | 1.64 to 2.84 |
| L4 - Breached a settlement or order | 398 | 2.73 | 3.97 | 3.57 to 4.39 |

The median landlord money case reaches an order with **3.45 months of rent** outstanding, on a unit renting at a median of $1,731/month.

## How that is distributed

| Months owed | Orders | Share |
|---|---:|---:|
| Under 1 month | 167 | 7.9% |
| 1 to 2 months | 337 | 16.0% |
| 2 to 3 months | 358 | 17.0% |
| 3 to 6 months | 754 | 35.8% |
| 6 to 12 months | 385 | 18.3% |
| Over 12 months | 104 | 4.9% |

**7.9% of orders are for less than a single month's rent**, and **4.9% are for more than a year's.** Both tails matter and they matter to different people: the short one is a tenancy ending over an amount smaller than one rent cheque, the long one is a landlord who has gone a year without income from the unit.

## Individual against corporate owners

| | Orders | Median months | Mean amount | 95% interval |
|---|---:|---:|---:|---|
| Individual | 780 | 4.04 | $9,935 | $9,296 to $10,604 |
| Corporate | 1,325 | 3.14 | $6,714 | $6,359 to $7,052 |

Per case the two are close, which is the finding. The difference between the two kinds of landlord is not the size of an individual loss but how many of them each carries and what share of income each represents.

## Who turned up, and who had help

| Party | Attended | Had a representative |
|---|---:|---:|
| Landlord | 90.3% | 73.6% |
| Tenant | 52.2% | 7.6% |

Read from orders that name who attended the hearing. An order that does not carry that sentence is excluded rather than scored as a no-show, so these are rates among orders that say, not among all orders.

## Method and limits

* **Sample.** 5,000 orders drawn across L1, L2 and L4 in proportion to how common each is, so an unweighted mean over the sample is already a population mean. Seeded, so the draw is reproducible.
* **Coverage.** A rent figure is recoverable from about 44% of sampled orders and both a rent and an amount from 2,105. Orders that state neither are excluded, and there is no guarantee they resemble those that do.
* **Intervals** are percentile bootstrap, 2,000 resamples. They express sampling error only. They say nothing about whether the extraction read each order correctly.
* **Ratios above 60 months** are dropped as parse failures rather than believed.
* **An amount ordered is not an amount collected.** Nothing in the public record says whether any of this was ever paid.
