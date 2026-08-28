# The parties: recurrence, process, and gender

Built by `scripts/analyze_parties.py`.

## How often the same tenant recurs

Every person named as a tenant in a landlord-filed case (37,408 distinct names), counted by how many cases they appear in:

| Cases against them | Tenants | Share of tenants | Share of cases |
|---|---:|---:|---:|
| 1 | 33,665 | 89.99% | 81.0% |
| 2 | 3,420 | 9.14% | 16.5% |
| 3 | 270 | 0.72% | 1.9% |
| 4 | 42 | 0.11% | 0.4% |
| 5+ | 11 | 0.03% | 0.1% |

**10.0% of tenants account for 19% of cases.** Of those repeat tenants:

* **73.2%** recur at the *same address* - one tenancy generating more than one case, typically a non-payment application followed by an application to enforce the payment plan that settled it.
* **26.8%** (1,004 people) appear at a *different address* - moved, and it happened again.

### What repeat tenants are taken to the Board for

| Code | Meaning | Repeat tenants | One-time tenants | Ratio |
|---|---|---:|---:|---:|
| L1 | Non-payment of rent | 46.9% | 70.8% | 0.66x |
| L2 | End tenancy (other reasons) | 20.0% | 15.2% | 1.32x |
| L4 | Breached a settlement or order | 29.8% | 8.7% | 3.44x |
| L3 | Tenant gave notice but stayed | 1.9% | 2.6% | 0.71x |
| L9 | Collect rent during tenancy | 0.9% | 1.3% | 0.68x |
| A2 | Application about a mobile home site | 0.4% | 0.6% | 0.62x |
| L5 | Above-guideline rent increase | 0.0% | 0.4% | 0.07x |

The clearest difference is **L4, breaching a settlement or order**: 29.8% of repeat-tenant cases against 8.7% of one-time-tenant cases, a **3.44x** difference. The one-time group is overwhelmingly a straightforward payment problem; the recurring group is disproportionately people who agreed to terms and did not keep them.

### What this does and does not show

This is a **148-day window**, which is too short to detect someone who moves once a year. The 'different address' figure above is therefore a floor on recurrence across tenancies, not a measurement of it. It is also an over-count in the other direction: matching is on name text, so two different people who share a common name are merged. Both errors are real and they push in opposite directions.

A longer window would settle it. Ontario publishes one rolling current-year file, so the only way to get one is to keep snapshotting this export - which `scripts/fetch_ltb_orders.py` already does.

## Decided without a hearing

An ex parte order is made without the other side present.

| | Orders | Ex parte | Share |
|---|---:|---:|---:|
| all landlord-filed orders | 34,422 | 6,345 | 18.4% |
| all tenant-filed orders | 6,043 | 126 | 2.1% |
| L4 - Breached a settlement or order | 5,158 | 3,189 | 61.8% |
| L1 - Non-payment of rent | 21,023 | 2,447 | 11.6% |
| L3 - Tenant gave notice but stayed | 808 | 660 | 81.7% |
| T2 - Tenant rights | 2,863 | 96 | 3.4% |
| L2 - End tenancy (other reasons) | 5,271 | 34 | 0.6% |
| T6 - Maintenance | 1,113 | 19 | 1.7% |
| T1 - Rent rebate or money owed to tenant | 1,360 | 8 | 0.6% |
| L10 - Collect money from a former tenant | 949 | 7 | 0.7% |
| L9 - Collect rent during tenancy | 390 | 6 | 1.5% |
| T5 - Bad-faith notice to terminate | 551 | 3 | 0.5% |
| C1 - Co-op non-payment | 222 | 2 | 0.9% |
| A2 - Application about a mobile home site | 270 | 1 | 0.4% |
| L5 - Above-guideline rent increase | 551 | 0 | 0.0% |

The concentration in L4 and L3 is procedurally expected rather than sinister: both are applications to enforce something already agreed or already noticed, and the Act allows them to proceed without a fresh hearing. The figure worth carrying forward is the difference between the two sides, which is large.

## Household size

Named adults per landlord-filed case. Children are not named, so this is a count of adults on the file, not of people at risk of losing the home.

| Named adults | Cases | Share |
|---:|---:|---:|
| 1 | 20,132 | 66.9% |
| 2 | 8,650 | 28.7% |
| 3 | 994 | 3.3% |
| 4 | 258 | 0.9% |
| 5 | 74 | 0.2% |

## Gender

Inferred from first names against a name-gender dictionary. **Every figure below describes resolved names only**, and the coverage column says how much of each group that is.

| Role | Men | Women | Men per woman | Coverage |
|---|---:|---:|---:|---:|
| Individual landlords who filed | 5,025 | 2,515 | 2.0 | 64.8% |
| Tenants named in landlord-filed cases | 16,529 | 15,905 | 1.04 | 77.6% |
| Tenants who filed their own case | 2,697 | 2,955 | 0.91 | 76.9% |

Individual landlords who bring cases are **2.0 men per woman**. Tenants named in those cases are **1.04** - effectively even. Tenants who bring their own case are **0.91**.

### Landlord gender against tenant gender

| | Tenant M | Tenant F |
|---|---:|---:|
| Landlord M | 33.8% | 33.4% |
| Landlord F | 17.7% | 15.2% |

Based on 8,611 pairs where both sides resolved.

### Gender by what the case is about

The aggregate hides the only part of this that is interesting. Split by application type (rows with at least 100 resolved tenant names):

| Code | Meaning | Filed by | Individual landlord, M:F | Tenants, M:F | Tenants who are women |
|---|---|---|---:|---:|---:|
| L1 | Non-payment of rent | landlord | 2.15 | 1.03 | 49.2% |
| L2 | End tenancy (other reasons) | landlord | 1.83 | 1.06 | 48.6% |
| L4 | Breached a settlement or order | landlord | 2.06 | 1.02 | 49.5% |
| T2 | Tenant rights | tenant | 1.91 | 0.9 | 52.7% |
| T1 | Rent rebate or money owed to tenant | tenant | 1.97 | 0.99 | 50.1% |
| T6 | Maintenance | tenant | 1.58 | 0.85 | 53.9% |
| L3 | Tenant gave notice but stayed | landlord | 2.19 | 1.17 | 46.2% |
| T5 | Bad-faith notice to terminate | tenant | 1.9 | 0.88 | 53.1% |
| L9 | Collect rent during tenancy | landlord | thin | 1.12 | 47.2% |
| A2 | Application about a mobile home site |  | thin | 1.28 | 43.8% |
| L5 | Above-guideline rent increase | landlord | thin | 0.91 | 52.5% |

Two patterns, pointing in different directions:

* **Individual landlords skew about two men to one woman in every category.** It barely varies by what the case is about, which suggests it is a fact about who owns rental property rather than about how anyone behaves.
* **Tenants are taken to the Board at parity, but bring their own cases more often when they are women.** Tenants named in landlord applications run 1.02 to 1.06 men per woman, essentially even. Tenant-filed applications run the other way: maintenance 0.85 (53.9% women), bad-faith notice to terminate 0.88, tenant rights 0.90.

### Gender by recurrence and by household

| Group | Men per woman | Resolved names |
|---|---:|---:|
| Tenants with one case | 1.03 | 25,875 |
| Tenants with more than one case | 1.09 | 3,002 |
| Tenancies with one named adult | 1.01 | 16,005 |
| Tenancies with two named adults | 1.05 | 13,296 |

Both are null results and are reported as such. Tenants who come back more than once are not meaningfully more male than those who appear once (1.09 against 1.03), and a one-adult tenancy is not more male than a two-adult one (1.01 against 1.05). Whatever explains recurrence, it is not this.

### Why this is reported with a coverage column

The dictionary resolves 64.8% of individual landlord first names and 77.6% of tenant first names. **The misses are not random.** It resolves Anglo and European given names far better than others, so communities whose names it does not carry are under-represented in the resolved base. If the gender balance among unresolved names differs from the resolved ones, every ratio above shifts.

The direction of the landlord finding is robust to plausible assumptions about the missing third - it would take an extreme skew among unresolved names to bring 2 men per woman down to parity - but the precise ratio should not be quoted to more than one decimal place, and no figure here should be read as a statement about any named community.
