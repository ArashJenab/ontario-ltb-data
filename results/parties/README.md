# The parties: recurrence, process, and gender

Built by `scripts/analyze_parties.py`.

## How often the same tenant recurs

Every person named as a tenant in a landlord-filed case (44,156 distinct names), counted by how many cases they appear in:

| Cases against them | Tenants | Share of tenants | Share of cases |
|---|---:|---:|---:|
| 1 | 39,041 | 88.42% | 78.3% |
| 2 | 4,622 | 10.47% | 18.5% |
| 3 | 407 | 0.92% | 2.4% |
| 4 | 67 | 0.15% | 0.5% |
| 5+ | 19 | 0.04% | 0.2% |

**11.6% of tenants account for 22% of cases.** Of those repeat tenants:

* **73.0%** recur at the *same address* - one tenancy generating more than one case, typically a non-payment application followed by an application to enforce the payment plan that settled it.
* **27.0%** (1,380 people) appear at a *different address* - moved, and it happened again.

### What repeat tenants are taken to the Board for

| Code | Meaning | Repeat tenants | One-time tenants | Ratio |
|---|---|---:|---:|---:|
| L1 | Non-payment of rent | 48.8% | 71.3% | 0.68x |
| L2 | End tenancy (other reasons) | 19.3% | 15.3% | 1.27x |
| L4 | Breached a settlement or order | 28.7% | 7.8% | 3.67x |
| L3 | Tenant gave notice but stayed | 1.8% | 2.8% | 0.64x |
| L9 | Collect rent during tenancy | 0.8% | 1.4% | 0.55x |
| A2 | Application about a mobile home site | 0.4% | 0.6% | 0.69x |
| L5 | Above-guideline rent increase | 0.1% | 0.4% | 0.14x |

The clearest difference is **L4, breaching a settlement or order**: 28.7% of repeat-tenant cases against 7.8% of one-time-tenant cases, a **3.67x** difference. The one-time group is overwhelmingly a straightforward payment problem; the recurring group is disproportionately people who agreed to terms and did not keep them.

### What this does and does not show

This is a **180-day window**, which is too short to detect someone who moves once a year. The 'different address' figure above is therefore a floor on recurrence across tenancies, not a measurement of it. It is also an over-count in the other direction: matching is on name text, so two different people who share a common name are merged. Both errors are real and they push in opposite directions.

A longer window would settle it. Ontario publishes one rolling current-year file, so the only way to get one is to keep snapshotting this export - which `scripts/fetch_ltb_orders.py` already does.

## Decided without a hearing

An ex parte order is made without the other side present.

| | Orders | Ex parte | Share |
|---|---:|---:|---:|
| all landlord-filed orders | 41,576 | 7,707 | 18.5% |
| all tenant-filed orders | 7,242 | 155 | 2.1% |
| L4 - Breached a settlement or order | 6,256 | 3,858 | 61.7% |
| L1 - Non-payment of rent | 25,379 | 2,934 | 11.6% |
| L3 - Tenant gave notice but stayed | 1,035 | 853 | 82.4% |
| T2 - Tenant rights | 3,385 | 119 | 3.5% |
| L2 - End tenancy (other reasons) | 6,389 | 46 | 0.7% |
| T6 - Maintenance | 1,314 | 22 | 1.7% |
| T1 - Rent rebate or money owed to tenant | 1,682 | 11 | 0.7% |
| L9 - Collect rent during tenancy | 483 | 7 | 1.4% |
| L10 - Collect money from a former tenant | 1,065 | 7 | 0.7% |
| T5 - Bad-faith notice to terminate | 672 | 3 | 0.4% |
| C1 - Co-op non-payment | 252 | 2 | 0.8% |
| A2 - Application about a mobile home site | 302 | 1 | 0.3% |
| L5 - Above-guideline rent increase | 656 | 0 | 0.0% |

The concentration in L4 and L3 is procedurally expected rather than sinister: both are applications to enforce something already agreed or already noticed, and the Act allows them to proceed without a fresh hearing. The figure worth carrying forward is the difference between the two sides, which is large.

## Household size

Named adults per landlord-filed case. Children are not named, so this is a count of adults on the file, not of people at risk of losing the home.

| Named adults | Cases | Share |
|---:|---:|---:|
| 1 | 24,134 | 66.8% |
| 2 | 10,420 | 28.8% |
| 3 | 1,169 | 3.2% |
| 4 | 322 | 0.9% |
| 5 | 84 | 0.2% |

## Gender

Inferred from first names against a name-gender dictionary. **Every figure below describes resolved names only**, and the coverage column says how much of each group that is.

| Role | Men | Women | Men per woman | Coverage |
|---|---:|---:|---:|---:|
| Individual landlords who filed | 6,024 | 2,984 | 2.02 | 64.8% |
| Tenants named in landlord-filed cases | 19,865 | 19,044 | 1.04 | 77.5% |
| Tenants who filed their own case | 3,229 | 3,504 | 0.92 | 76.6% |

Individual landlords who bring cases are **2.02 men per woman**. Tenants named in those cases are **1.04** - effectively even. Tenants who bring their own case are **0.92**.

### Landlord gender against tenant gender

| | Tenant M | Tenant F |
|---|---:|---:|
| Landlord M | 33.9% | 33.2% |
| Landlord F | 17.5% | 15.4% |

Based on 10,259 pairs where both sides resolved.

### Gender by what the case is about

The aggregate hides the only part of this that is interesting. Split by application type (rows with at least 100 resolved tenant names):

| Code | Meaning | Filed by | Individual landlord, M:F | Tenants, M:F | Tenants who are women |
|---|---|---|---:|---:|---:|
| L1 | Non-payment of rent | landlord | 2.17 | 1.03 | 49.1% |
| L2 | End tenancy (other reasons) | landlord | 1.8 | 1.07 | 48.4% |
| L4 | Breached a settlement or order | landlord | 2.1 | 1.01 | 49.6% |
| T2 | Tenant rights | tenant | 1.89 | 0.9 | 52.6% |
| T1 | Rent rebate or money owed to tenant | tenant | 1.95 | 1.03 | 49.3% |
| T6 | Maintenance | tenant | 1.65 | 0.84 | 54.2% |
| L3 | Tenant gave notice but stayed | landlord | 2.24 | 1.18 | 46.0% |
| T5 | Bad-faith notice to terminate | tenant | 1.98 | 0.9 | 52.7% |
| L9 | Collect rent during tenancy | landlord | thin | 1.14 | 46.7% |
| A2 | Application about a mobile home site |  | thin | 1.36 | 42.4% |
| L5 | Above-guideline rent increase | landlord | 1.28 | 0.9 | 52.6% |
| A1 | Whether the Act applies |  | thin | 1.22 | 45.1% |

Two patterns, pointing in different directions:

* **Individual landlords skew about two men to one woman in every category.** It barely varies by what the case is about, which suggests it is a fact about who owns rental property rather than about how anyone behaves.
* **Tenants are taken to the Board at parity, but bring their own cases more often when they are women.** Tenants named in the three large landlord applications run 1.01 to 1.07 men per woman, essentially even. Tenant-filed applications run the other way: maintenance 0.84 (54.2% women), bad-faith notice to terminate 0.9, tenant rights 0.9.

### Gender by recurrence and by household

| Group | Men per woman | Resolved names |
|---|---:|---:|
| Tenants with one case | 1.03 | 29,969 |
| Tenants with more than one case | 1.1 | 4,089 |
| Tenancies with one named adult | 1.02 | 19,213 |
| Tenancies with two named adults | 1.05 | 16,018 |

Both are null results and are reported as such. Tenants who come back more than once are not meaningfully more male than those who appear once (1.09 against 1.03), and a one-adult tenancy is not more male than a two-adult one (1.01 against 1.05). Whatever explains recurrence, it is not this.

### Why this is reported with a coverage column

The dictionary resolves 64.8% of individual landlord first names and 77.5% of tenant first names. **The misses are not random.** It resolves Anglo and European given names far better than others, so communities whose names it does not carry are under-represented in the resolved base. If the gender balance among unresolved names differs from the resolved ones, every ratio above shifts.

The direction of the landlord finding is robust to plausible assumptions about the missing third - it would take an extreme skew among unresolved names to bring 2 men per woman down to parity - but the precise ratio should not be quoted to more than one decimal place, and no figure here should be read as a statement about any named community.
