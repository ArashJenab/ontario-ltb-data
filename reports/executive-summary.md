# What Ontario's rental disputes cost, and who pays

*An open-data analysis. Generated 2026-08-27 by `scripts/build_site.py`.*

**Window.** The Landlord and Tenant Board publishes one rolling current-year file. This analysis covers **2026-01-02 to 2026-05-29**, 148 days, holding 40,844 orders across 37,401 distinct cases. Not a full year and not all time. No earlier period is published anywhere, so no trend can be measured yet. Annual figures below are that window multiplied by 2.466.

**In one sentence:** the Board handles a normal-sized caseload by international standards, but the weight of it falls on people who own a single rental unit and on tenants who never reach the Board at all, and the public record is not shaped like the problem it gets used to describe.

## 1. The scale is ordinary

About **4.22% of Ontario's 1,724,970 renter households**, roughly 1 in 24, have a landlord case filed against them each year. Three independent routes agree: this export annualised, this export counting distinct rental units, and the Board's own published intake for 2024-25.

For comparison, the United States filing rate is about 8.0% of renter households (Eviction Lab, 2024), and only about 1.0% of Canadian renters are actually evicted in a year (CMHC, 2025). **An application is not an eviction**: most non-payment cases end with the tenant paying and staying. Quoting the filing rate as an eviction rate is wrong in either direction.

## 2. Who actually carries the cost

| | Individual owners | Corporate or institutional |
|---|---:|---:|
| Landlords | 9,291 | 4,517 |
| Share of cases | 37.7% | 62.3% |
| Filed exactly once | **85.8%** | 61.3% |
| Own a single address | **91.1%** | 63.0% |
| Share of the money at stake | 33.4% | 66.6% |
| Mean owed each | $5,193 | $20,133 |

The median case is about the same size on both sides, roughly $5,226. What differs is what it means: **3.7 months of rent, or 30.9% of that unit's annual gross revenue** before mortgage, tax or repairs. For 91.1% of individual owners, that unit is all they have. A corporate owner is owed roughly 3.9 times more on average because it brings more cases, not larger ones.

The application mix says the same thing from another angle. **77.0% of applications to collect from a tenant who has already left** are brought by individuals: the cases least likely ever to be recovered. The reverse also holds and belongs in the record, because an analysis that only reports one direction is not evidence: above-guideline rent increases are **77.5% corporate**.

## 3. The record is not a picture of eviction

Non-payment is **63.4%** of the Board's landlord cases but only **8%** of the evictions tenants report to Statistics Canada. The reasons tenants most often give, that the landlord sold the property (37%) or wanted the unit (26%), usually end with the tenant leaving on a notice and produce no order at all.

This cuts both ways. The Board's file understates how often tenants lose housing, **and** it is not evidence about the frequency of the no-fault evictions it barely contains.

## 4. Recurrence, and process

**90% of tenants appear in exactly one case.** The 10% who recur account for 19.0% of cases and are taken to the Board for breaching a settlement at **3.44 times** the rate of one-time tenants (29.8% of their cases against 8.7%). Most recur at the same address rather than moving on.

**18.4% of landlord-filed orders are made without a hearing, against 2.1% of tenant-filed ones.** Much of that gap is procedurally expected, since an application to enforce something already agreed may proceed without a fresh hearing, but the size of it is a fact about the system worth knowing.

## 5. What was tested and not found

- **Area income does not explain where landlords file.** Rank correlation -0.119 across 371 postal areas, about 1% of the variation between them. Rental disputes are not concentrated in poor postal codes in any strong sense, in either direction.
- **No gendered pairing between the sides.** Male and female landlords face essentially the same gender mix of tenants, though individual landlords who file do skew about two to one male.
- **The serial-tenant claim is not supported at this timescale.** About 2.7% of tenants appear at more than one address in 148 days, and the apparent top of that list turns out to be legal clinics named in the tenant field. What the data does support is narrower: the settlement-breach difference above.

## Why this matters

None of this required data the province does not already hold. The Board publishes its orders; Statistics Canada publishes the census. Three gaps stand out, and all three are cheap to close:

1. **Only a rolling current-year file is published**, so no trend can be measured. Nobody, inside or outside government, can presently say whether this is improving or deteriorating.
2. **Amounts are not in the export**, so every dollar figure here required downloading and reading order PDFs one at a time. The Board already holds these figures.
3. **There is no outcome field**, so whether an application ended in eviction, payment, settlement or dismissal cannot be answered from public data at all.

A public dashboard covering those three would cost a fraction of most provincial data initiatives, and would let landlords, tenants, journalists and members of the Legislature check these numbers directly rather than take a private analysis's word for them.

---

*Every figure above traces to a named public source; see `sources.html` for which, and for how far each can be pushed. Application counts, party classification, geography and process rates are exact counts of the complete export. Dollar figures are estimates from a sample of order PDFs and are presented as such. No landlord, tenant or address is named anywhere in this analysis.*

*This is an independent analysis developed using data published by the Government of Ontario. It is not an official publication of, and is not affiliated with or endorsed by, the Government of Ontario or the Landlord and Tenant Board.*
