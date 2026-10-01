# What Ontario's rental disputes cost, and who pays

*An open-data analysis. Generated 2026-10-01 by `scripts/build_site.py`.*

**Window.** The Landlord and Tenant Board publishes one rolling current-year file. This analysis covers **2026-01-02 to 2026-06-30**, 180 days, holding 49,269 orders across 44,743 distinct cases. Not a full year and not all time. No earlier period is published anywhere, so no trend can be measured yet. Annual figures below are that window multiplied by 2.028.

**How current.** Retrieved from the province's open-data catalogue on **2026-10-01**. The newest order in the file was then 93 days old. That gap is the Board's: it adds orders to the catalogue in batches, about three months after they issue (on 2026-08-13 the newest order was dated 2026-05-29).

**Source.** Every count is taken directly from the Board's own LTB Order Catalogue on data.ontario.ca, through its public API. The catalogue does not carry amounts, rents, attendance or outcomes, so those are read from 8,125 of the order documents it links to. Rates use the 2021 Census.

**In one sentence:** the Board handles a normal-sized caseload by international standards, but the weight of it falls on people who own a single rental unit and on tenants who never reach the Board at all, and the public record is not shaped like the problem it gets used to describe.

## 1. The scale is ordinary

About **4.22% of Ontario's 1,724,970 renter households**, roughly 1 in 24, have a landlord case filed against them each year. Three independent routes agree: this export annualised, this export counting distinct rental units, and the Board's own published intake for 2024-25.

For comparison, the United States filing rate is about 8.0% of renter households (Eviction Lab, 2024), and only about 1.0% of Canadian renters are actually evicted in a year (CMHC, 2025). **An application is not an eviction**: most non-payment cases end with the tenant paying and staying. Quoting the filing rate as an eviction rate is wrong in either direction.

## 2. Who actually carries the cost

| | Individual owners | Corporate or institutional |
|---|---:|---:|
| Landlords | 10,873 | 5,121 |
| Share of cases | 37.6% | 62.4% |
| Filed exactly once | **84.3%** | 60.4% |
| Own a single address | **90.5%** | 61.8% |
| Share of the money at stake | 33.6% | 66.4% |
| Mean owed each | $5,325 | $21,205 |

Across a year a corporate owner is owed roughly 4.0 times more in total, because it brings many cases. That is the aggregate view and it is modelled from category averages.

Reading 2,542 orders individually gives the per-case answer the model cannot, and it does not point the way the aggregate implies. **An individual owner's case is larger than a corporate one, not smaller:**

| Median case | Individual owners | Corporate or institutional |
|---|---:|---:|
| Months of rent owed | **4.06** | 3.13 |
| Amount owed | **$7,212** | $5,062 |
| Share of that unit's annual rent | **33.8%** | 26.1% |
| Rent on the unit | $1,950 | $1,640 |
| Orders measured | 953 | 1,589 |

The mean amounts are $9,790 and $6,629, with 95% intervals that do not overlap, so this is a real difference rather than sampling noise. Individual owners do rent costlier units, but the months figure controls for that and the gap survives it. For 90.5% of these owners the unit in question is all they have.

The application mix says the same thing from another angle. **77.5% of applications to collect from a tenant who has already left** are brought by individuals: the cases least likely ever to be recovered. The reverse also holds and belongs in the record, because an analysis that only reports one direction is not evidence: above-guideline rent increases are **79.4% corporate**.

## 3. The record is not a picture of eviction

Non-payment is **63.7%** of the Board's landlord cases but only **8%** of the evictions tenants report to Statistics Canada. The reasons tenants most often give, that the landlord sold the property (37%) or wanted the unit (26%), usually end with the tenant leaving on a notice and produce no order at all.

This cuts both ways. The Board's file understates how often tenants lose housing, **and** it is not evidence about the frequency of the no-fault evictions it barely contains.

## 4. Recurrence, and process

**88% of tenants appear in exactly one case.** The 12% who recur account for 21.7% of cases and are taken to the Board for breaching a settlement at **3.67 times** the rate of one-time tenants (28.7% of their cases against 7.8%). Most recur at the same address rather than moving on.

**18.5% of landlord-filed orders are made without a hearing, against 2.1% of tenant-filed ones.** Much of that gap is procedurally expected, since an application to enforce something already agreed may proceed without a fresh hearing, but the size of it is a fact about the system worth knowing.

Where a hearing did happen, orders name who attended. Split by who brought the application, because in a landlord-filed case the tenant is the respondent by construction:

| Filed by | Party | Attended | Represented |
|---|---|---:|---:|
| Landlord | Landlord | 89.1% | 71.7% |
| Landlord | Tenant | 51.3% | 7.7% |
| Tenant | Landlord | 83.3% | 50.9% |
| Tenant | Tenant | 70.5% | 23.6% |

**Part of the attendance gap is structural**: the applicant turns up to their own case. Tenants attend 70.5% of the hearings they bring against 51.3% of those brought against them.

**Representation does not behave that way.** Even bringing their own case, tenants have someone acting for them 23.6% of the time, against 50.9% for landlords who are only responding to it. This cuts against the landlord side of the ledger and is reported for that reason: whoever bears the financial loss, the party facing loss of housing is far less likely to have anyone speaking for them, on either side of the case.

## 5. What was tested and not found

- **Area income does not explain where landlords file.** Rank correlation -0.128 across 395 postal areas, about 2% of the variation between them. Rental disputes are not concentrated in poor postal codes in any strong sense, in either direction.
- **No gendered pairing between the sides.** Male and female landlords face essentially the same gender mix of tenants, though individual landlords who file do skew about two to one male.
- **The serial-tenant claim is not supported at this timescale.** About 3.1% of tenants appear at more than one address in 180 days, and the apparent top of that list turns out to be legal clinics named in the tenant field. What the data does support is narrower: the settlement-breach difference above.

## Why this matters

None of this required data the province does not already hold. The Board publishes its orders; Statistics Canada publishes the census. Three gaps stand out, and all three are cheap to close:

1. **Only a rolling current-year file is published**, so no trend can be measured. Nobody, inside or outside government, can presently say whether this is improving or deteriorating.
2. **Amounts are not in the export**, so every dollar figure here required downloading and reading order PDFs one at a time. The Board already holds these figures.
3. **There is no outcome field**, so whether an application ended in eviction, payment, settlement or dismissal cannot be answered from public data at all.

A public dashboard covering those three would cost a fraction of most provincial data initiatives, and would let landlords, tenants, journalists and members of the Legislature check these numbers directly rather than take a private analysis's word for them.

---

*Every figure above traces to a named public source; see `sources.html` for which, and for how far each can be pushed. Application counts, party classification, geography and process rates are exact counts of the complete export. Dollar figures are estimates from a sample of order PDFs and are presented as such. No landlord, tenant or address is named anywhere in this analysis.*

*This is an independent analysis developed using data published by the Government of Ontario. It is not an official publication of, and is not affiliated with or endorsed by, the Government of Ontario or the Landlord and Tenant Board.*
