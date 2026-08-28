# What actually happens to an application

Built by `scripts/analyze_outcomes.py` from `results/case_details_all/outcomes.csv`.

**Sample.** 5,833 orders, drawn proportionally across every application type and read individually. The disposition is not in the open-data export; it is in the orders, which are public and linked from that export.

## Disposition, by who filed

| | Landlord-filed | Tenant-filed |
|---|---:|---:|
| Orders read | 4,973 | 759 |
| Terminated, but the tenant can pay to stay | 22.6% | 0.0% |
| Terminated | 25.5% | 4.6% |
| Ordered to pay, tenancy continues | 18.9% | 6.1% |
| Landlord ordered to do something | 0.5% | 19.5% |
| Dismissed | 7.1% | 43.9% |
| Withdrawn | 1.4% | 7.8% |
| Not classified | 24.0% | 18.2% |
| Made on consent | 22.6% | 16.1% |

## The two things this settles

**A termination order mostly does not end a tenancy.** 48.1% of landlord applications end in a termination of some kind, but **47.0% of those are voidable**: the order says the tenancy ends unless the tenant pays a stated sum by a stated date. Netting that out, roughly a quarter of landlord applications produce an unconditional termination. Anyone citing filings, or even terminations, as a count of evictions is overstating it, and this is the measurement that shows by how much.

**Tenants lose the cases they bring far more often than landlords lose theirs.** 43.9% of tenant-filed applications are dismissed against 7.1% of landlord-filed ones, a 6.2-fold difference. A further 19.5% end with the landlord ordered to do something and 6.1% with a payment, so a tenant who brings a case is more likely to leave with nothing than with anything.

This file is the reason the phrase 'an application is not an eviction' appears throughout this repository with a number attached rather than as an assertion.

## By application type

| Code | Meaning | Filed by | Orders | Any termination | Dismissed |
|---|---|---|---:|---:|---:|
| L1 | Non-payment of rent | landlord | 2,948 | 49.8% | 4.3% |
| L2 | End tenancy (other reasons) | landlord | 811 | 35.0% | 17.4% |
| L4 | Breached a settlement or order | landlord | 797 | 63.6% | 1.6% |
| T2 | Tenant rights | tenant | 340 | 4.4% | 46.8% |
| T6 | Maintenance | tenant | 167 | 8.4% | 41.3% |
| T1 | Rent rebate or money owed to tenant | tenant | 161 | 3.1% | 41.0% |
| L10 | Collect money from a former tenant | landlord | 146 | 2.1% | 31.5% |
| L3 | Tenant gave notice but stayed | landlord | 124 | 84.7% | 7.3% |

## Method and limits

* **Classified from the order text** by matching the operative language ("the tenancy ... is terminated", "may void this order", "the application is dismissed"), most specific first, because one order can contain several of those phrases.
* **23.8% of orders are left unclassified** rather than forced into a bucket. That share is a real limit on everything above: the rates are shares of all orders read, so an unclassified order counts against every category rather than being quietly dropped.
* **An order is not an enforcement.** Whether a termination was ever acted on, and whether money ordered was ever collected, is not in the record at all.
* **Review and amended orders** appear as their own rows. An application reviewed and re-decided contributes twice, once per document.
* **The PDFs this was read from are not kept in the repository.** They are re-downloadable from the URLs in the export by `scripts/extract_case_details.py`, and `scripts/extract_outcomes.py` re-reads whatever is cached locally.
