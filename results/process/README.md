# Who turns up, and who has help

Built by `scripts/analyze_process.py` from `results/case_details_all/case_details_raw.csv`.

**Sample.** 6,000 orders drawn across *every* application type in proportion to how common each is, so an unweighted rate over the sample is a caseload rate. 3,564 of them (59%) carry the sentence naming who attended the hearing; the rest are excluded rather than scored as a no-show.

## Why this needed its own sample

An earlier version of this figure came from a sample of L1, L2 and L4 orders only. Those are landlord money cases, where the landlord is the applicant and the tenant the respondent in every single one. Reporting "tenants attend 52%" from that sample measured one side of the docket and called it the whole. Split by who actually filed, the question is whether a party is absent because of who they are or because of which side of the case they are on.

## Attendance and representation, by who filed

| Application filed by | Party | Attended | Represented | Represented, of those attending |
|---|---|---:|---:|---:|
| Landlord | Landlord | 88.7% | 70.9% | 79.9% |
| Landlord | Tenant | 51.6% | 7.4% | 14.4% |
| Tenant | Landlord | 82.2% | 51.2% | 62.2% |
| Tenant | Tenant | 71.5% | 24.9% | 34.9% |

## What it says

**The applicant shows up.** In landlord-filed cases the landlord attends 88.7% of hearings and the tenant 51.6%. In tenant-filed cases the tenant attends 71.5% and the landlord 82.2%. So a good part of the attendance gap is structural: whoever brought the application turns up to it, and the respondent is likelier to be absent whichever side they are on.

**Representation does not work like that.** Landlords are represented at 70.9% of the hearings they bring and 51.2% of the ones brought against them. Tenants are represented at 24.9% of the hearings they bring and 7.4% of the ones brought against them. Being the applicant does not close that gap, and it is the finding worth carrying: a tenant is far less likely to have anyone speaking for them regardless of which side of the case they are on.

## Across the whole caseload

| Party | Attended | Represented |
|---|---:|---:|
| Landlord | 87.2% | 67.8% |
| Tenant | 53.8% | 9.7% |

## Method and limits

* **Read from the order text**, specifically the sentence naming who attended the hearing ("the Landlord's Legal Representative, ..., attended the hearing"). A representative is credited to whichever party is named next to them, within a window, so one side's paralegal is not counted for the other.
* **Orders with no such sentence are excluded**, not counted as absences. Ex parte orders largely have no hearing to attend, and are a separate measure kept in `results/parties/decided_without_hearing.csv`.
* **Attendance is not the same as participation.** The order records who was present, not whether they said anything or understood what was happening.
* **This supersedes** the attendance figures in `results/burden/attendance.csv`, which came from a landlord-money-only sample and are left in place only so the correction is traceable.
