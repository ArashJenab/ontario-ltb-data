# Who turns up, and who has help

Built by `scripts/analyze_process.py` from `results/case_details_all/case_details_raw.csv`.

**Sample.** 7,230 orders drawn across *every* application type in proportion to how common each is, so an unweighted rate over the sample is a caseload rate. 4,237 of them (59%) carry the sentence naming who attended the hearing; the rest are excluded rather than scored as a no-show.

## Why this needed its own sample

An earlier version of this figure came from a sample of L1, L2 and L4 orders only. Those are landlord money cases, where the landlord is the applicant and the tenant the respondent in every single one. Reporting "tenants attend 52%" from that sample measured one side of the docket and called it the whole. Split by who actually filed, the question is whether a party is absent because of who they are or because of which side of the case they are on.

## Attendance and representation, by who filed

| Application filed by | Party | Attended | Represented | Represented, of those attending |
|---|---|---:|---:|---:|
| Landlord | Landlord | 89.1% | 71.7% | 80.5% |
| Landlord | Tenant | 51.3% | 7.7% | 15.0% |
| Tenant | Landlord | 83.3% | 50.9% | 61.0% |
| Tenant | Tenant | 70.5% | 23.6% | 33.5% |

## What it says

**The applicant shows up.** In landlord-filed cases the landlord attends 89.1% of hearings and the tenant 51.3%. In tenant-filed cases the tenant attends 70.5% and the landlord 83.3%. So a good part of the attendance gap is structural: whoever brought the application turns up to it, and the respondent is likelier to be absent whichever side they are on.

**Representation does not work like that.** Landlords are represented at 71.7% of the hearings they bring and 50.9% of the ones brought against them. Tenants are represented at 23.6% of the hearings they bring and 7.7% of the ones brought against them. Being the applicant does not close that gap, and it is the finding worth carrying: a tenant is far less likely to have anyone speaking for them regardless of which side of the case they are on.

## Across the whole caseload

| Party | Attended | Represented |
|---|---:|---:|
| Landlord | 87.6% | 68.3% |
| Tenant | 53.4% | 9.8% |

## Method and limits

* **Read from the order text**, specifically the sentence naming who attended the hearing ("the Landlord's Legal Representative, ..., attended the hearing"). A representative is credited to whichever party is named next to them, within a window, so one side's paralegal is not counted for the other.
* **Orders with no such sentence are excluded**, not counted as absences. Ex parte orders largely have no hearing to attend, and are a separate measure kept in `results/parties/decided_without_hearing.csv`.
* **Attendance is not the same as participation.** The order records who was present, not whether they said anything or understood what was happening.
* **This supersedes** the attendance figures in `results/burden/attendance.csv`, which came from a landlord-money-only sample and are left in place only so the correction is traceable.
