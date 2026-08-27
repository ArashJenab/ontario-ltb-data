# -*- coding: utf-8 -*-
"""
Shared loading and party-classification layer for the LTB order export.

Every v2 analysis imports from here rather than re-deriving the same regexes,
so that "what counts as a corporate landlord" or "how a tenant name cell is
split into people" is defined exactly once and any change propagates.

The export is a CKAN datastore dump: a `fields` list plus a `records` list of
positional rows. Field names carry the French half after a slash and one of
them contains a double slash, so they are matched by prefix rather than by
literal equality.

Known data shapes this module handles, all verified against the Aug 2026
export (40,844 orders, 2026-01-02 to 2026-05-29):

  * 3,443 orders are second or later documents on the same file (Review /
    Amended orders), so orders != cases. Use `unique_files=True` when the
    question is "how many disputes", not "how many documents".
  * 572 rows carry the literal placeholder address "MULTIPLE RENTAL
    UNITS/PLUSIEURS UNITES DE LOCATION" instead of a street address. These
    are building-wide applications (typically L5 above-guideline increases)
    and must not be treated as one address.
  * A handful of tenant-name cells list every tenant in a building (up to
    several hundred names) for the same reason. `split_parties` returns them
    all; callers doing per-household statistics should drop cells above
    MAX_HOUSEHOLD_NAMES.
  * The tenant-name field sometimes carries a legal clinic or agency
    (Parkdale Community Legal Services, CMHA) acting as representative rather
    than a person. `looks_like_person` filters those.
"""
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXPORT_PATH = BASE / "data" / "ltb_open_data_export.json"

# A tenant-name cell listing more names than this is a building-wide
# application, not a household.
MAX_HOUSEHOLD_NAMES = 5

PLACEHOLDER_ADDRESS = "MULTIPLE RENTAL UNITS"

FIELD_PREFIXES = {
    "id": "_id",
    "file_number": "File Number",
    "application": "Applications/",
    "application_type": "Application Type",
    "complex_address": "Complex Address",
    "landlord": "Landlord Name",
    "landlord_agent": "Landlord Agent Name",
    "tenant": "Tenant Name",
    "former_tenant": "Former Tenant Name",
    "subtenant": "Sub-Tenant Name",
    "occupant": "Occupant Names",
    "coop_member": "Co-op Member Name",
    "coop": "Co-op Name",
    "document_type": "Document Type",
    "order_date": "Order Date",
    "document_id": "Document ID",
    "url": "ContentDownload URL",
}

# What each application code means, in plain words. Used for chart labels so
# no chart ever ships a bare "L4" that a journalist has to look up.
CATEGORY_LABELS = {
    "L1": "Non-payment of rent",
    "L2": "End tenancy (other reasons)",
    "L3": "Tenant gave notice but stayed",
    "L4": "Breached a settlement or order",
    "L5": "Above-guideline rent increase",
    "L8": "Illegal act or misrepresentation",
    "L9": "Collect rent during tenancy",
    "L10": "Collect money from a former tenant",
    "T1": "Rent rebate or money owed to tenant",
    "T2": "Tenant rights",
    "T3": "Rent reduction",
    "T5": "Bad-faith notice to terminate",
    "T6": "Maintenance",
    "T7": "Rent increase above the guideline",
    "A1": "Whether the Act applies",
    "A2": "Application about a mobile home site",
    "C1": "Co-op non-payment",
    "C2": "Co-op other",
    "C4": "Co-op breached a settlement",
}

FILED_BY = {"L": "landlord", "T": "tenant", "C": "co-op"}

# ---------------------------------------------------------------------------
# Party classification
# ---------------------------------------------------------------------------

# A landlord name containing any of these, or a 6+ digit run (a numbered
# Ontario company such as "2758214 Ontario Inc"), is treated as corporate or
# institutional rather than an individual owner. Deliberately inclusive of
# public and non-profit providers (community housing, co-ops): the analytical
# distinction being drawn is "an organisation with staff and a process" versus
# "a person who owns a unit", not "for-profit versus not".
CORPORATE_TOKENS = r"""
    INC|INCORPORATED|LTD|LIMITED|CORP|CORPORATION|LP|LLP|GP|COMPANY|PARTNERSHIP
  | HOLDINGS?|PROPERTIES|PROPERTY|MANAGEMENT|REALTY|REAL\ ESTATE|RENTALS?
  | HOUSING|HOMES|APARTMENTS?|RESIDENCES?|RESIDENTIAL|SUITES
  | TRUST|GROUP|ENTERPRISES?|INVESTMENTS?|DEVELOPMENTS?|VENTURES?|CAPITAL
  | ASSOCIATION|COOPERATIVE|CO-OPERATIVE|CO-OP|SOCIETY|FOUNDATION|CHURCH
  | MUNICIPALITY|CITY\ OF|TOWN\ OF|REGIONAL|MINISTRY|AUTHORITY|COMMISSION
  | FUND|REIT|LIVING|COMMUNITIES
"""
CORPORATE_RE = re.compile(r"\b(?:%s)\b" % CORPORATE_TOKENS, re.IGNORECASE | re.VERBOSE)
NUMBERED_CO_RE = re.compile(r"\b\d{6,}\b")

# Tokens that mark a "tenant" cell as an organisation or a placeholder rather
# than a person: legal clinics and agencies appear as representatives, and the
# export uses ". VACANT" / ". Tenant" for unnamed occupants.
NON_PERSON_RE = re.compile(
    r"\b(LEGAL|CLINIC|SERVICES?|ASSOCIATION|SOCIETY|CENTRE|CENTER|COMMUNITY"
    r"|HEALTH|HOUSING|INC|LTD|LLP|CORP|CORPORATION|MINISTRY|OFFICE|AGENCY"
    r"|VACANT|UNKNOWN|OCCUPANT|TENANT|LANDLORD|ESTATE)\b",
    re.IGNORECASE,
)

# Corporate suffixes stripped when building a canonical landlord key, so that
# "CAPREIT Limited Partnership", "CAPREIT LIMITED PARTNERSHIP" and "Capreit LP"
# collapse to one filer. Everything after "c/o" is dropped for the same reason
# (the same owner appears with and without a management company appended).
CANON_STRIP_RE = re.compile(
    r"\b(?:INC|INCORPORATED|LTD|LIMITED|CORP|CORPORATION|LP|LLP|GP|CO|COMPANY"
    r"|PARTNERSHIP|THE)\b",
    re.IGNORECASE,
)
CARE_OF_RE = re.compile(r"\bC/?O\b.*", re.IGNORECASE)

PARTY_SPLIT_RE = re.compile(r"\s+and\s+|\s*[,;&]\s*", re.IGNORECASE)
UNIT_PREFIX_RE = re.compile(
    r"^(?:(?:UNIT|APT|APARTMENT|SUITE|STE|BSMT|BASEMENT|FLOOR|FL|RM|ROOM|#)\s*)?"
    r"[A-Z0-9]{1,7}\s*-\s*",
    re.IGNORECASE,
)
POSTAL_RE = re.compile(r"([A-Za-z]\d[A-Za-z])\s?\d[A-Za-z]\d")


def is_corporate(name):
    """True if a landlord name reads as an organisation rather than a person."""
    if not name:
        return False
    return bool(NUMBERED_CO_RE.search(name) or CORPORATE_RE.search(name))


def is_numbered_company(name):
    return bool(name and NUMBERED_CO_RE.search(name))


def canonical_landlord(name):
    """Collapse spelling/suffix variants of one landlord to a single key."""
    if not name:
        return None
    key = CARE_OF_RE.sub("", name.upper())
    key = re.sub(r"[^A-Z0-9 ]", " ", key)
    key = CANON_STRIP_RE.sub(" ", key)
    key = re.sub(r"\s+", " ", key).strip()
    return key or None


def split_parties(cell):
    """Split a name cell into individual party names."""
    if not cell:
        return []
    return [" ".join(p.split()) for p in PARTY_SPLIT_RE.split(cell) if p.strip()]


def looks_like_person(name):
    """True if a name cell entry plausibly names a human being."""
    if not name or name.startswith("."):
        return False
    if len(name.split()) < 2:
        return False
    return not NON_PERSON_RE.search(name)


def household_names(cell):
    """Person-like names from a tenant cell, or [] for a building-wide list."""
    parts = split_parties(cell)
    if not parts or len(parts) > MAX_HOUSEHOLD_NAMES:
        return []
    return [p for p in parts if looks_like_person(p)]


def first_name(name):
    tokens = [t for t in re.split(r"[\s.]+", name) if t]
    return tokens[0] if tokens else ""


def is_placeholder_address(address):
    return bool(address) and PLACEHOLDER_ADDRESS in address.upper()


def building_key(address):
    """Street address with any unit/suite prefix removed, for building rollups."""
    if not address or is_placeholder_address(address):
        return None
    parts = [p.strip() for p in address.upper().split(",")]
    street = UNIT_PREFIX_RE.sub("", parts[0]).strip()
    if not street:
        return None
    return ", ".join([street] + parts[1:])


def fsa(address):
    if not address:
        return None
    match = POSTAL_RE.search(address)
    return match.group(1).upper() if match else None


def primary_code(application):
    """First code of a multi-code application, e.g. 'L1;L2' -> 'L1'."""
    return (application or "").split(";")[0].strip() or None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


class Order(dict):
    """One row of the export, with derived party attributes attached."""

    __getattr__ = dict.__getitem__


def _resolve_fields(fields):
    names = [f["id"] for f in fields]
    index = {}
    for key, prefix in FIELD_PREFIXES.items():
        for position, name in enumerate(names):
            if name.startswith(prefix):
                index[key] = position
                break
        else:
            raise KeyError(f"No export field starting with {prefix!r}")
    # There are two near-identical rental-address fields (one with a double
    # slash in its French label); prefer whichever is populated per row.
    index["_address_positions"] = [
        p for p, n in enumerate(names) if n.startswith("Rental Unit Address")
    ]
    return index


def load_orders(path=EXPORT_PATH, unique_files=False):
    """Load the export into Order objects with derived fields.

    unique_files=True keeps only the first order per file number, turning the
    document-level export into a case-level one.
    """
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)

    index = _resolve_fields(payload["fields"])
    address_positions = index["_address_positions"]

    orders = []
    seen_files = set()
    for row in payload["records"]:
        file_number = row[index["file_number"]]
        if unique_files:
            if file_number in seen_files:
                continue
            seen_files.add(file_number)

        address = next(
            (row[p] for p in address_positions if row[p]), None
        )
        landlord = row[index["landlord"]]
        application_type = row[index["application_type"]]

        orders.append(
            Order(
                id=row[index["id"]],
                file_number=file_number,
                application=row[index["application"]],
                code=primary_code(row[index["application"]]),
                application_type=application_type,
                filed_by=FILED_BY.get(application_type, "unknown"),
                address=address,
                fsa=fsa(address),
                building=building_key(address),
                landlord=landlord,
                landlord_key=canonical_landlord(landlord),
                landlord_kind=(
                    None
                    if not landlord
                    else "corporate" if is_corporate(landlord) else "individual"
                ),
                landlord_agent=row[index["landlord_agent"]],
                tenant=row[index["tenant"]],
                tenant_names=household_names(row[index["tenant"]]),
                document_type=row[index["document_type"]],
                ex_parte=row[index["document_type"]] == "ExParte Order",
                order_date=row[index["order_date"]],
                document_id=row[index["document_id"]],
                url=row[index["url"]],
            )
        )
    return orders


def date_span(orders):
    """(first, last, days_inclusive) over order dates."""
    from datetime import date

    dates = sorted(o["order_date"] for o in orders if o["order_date"])
    first, last = dates[0], dates[-1]
    days = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    return first, last, days


def annualisation_factor(orders):
    """Multiplier turning a count over the export window into an annual rate."""
    return 365.0 / date_span(orders)[2]


def summarise(orders):
    counts = Counter(o["filed_by"] for o in orders)
    first, last, days = date_span(orders)
    return {
        "orders": len(orders),
        "files": len({o["file_number"] for o in orders}),
        "first_date": first,
        "last_date": last,
        "days": days,
        "annualisation_factor": 365.0 / days,
        "landlord_filed": counts["landlord"],
        "tenant_filed": counts["tenant"],
        "coop_filed": counts["co-op"],
    }


if __name__ == "__main__":
    orders = load_orders()
    cases = load_orders(unique_files=True)
    for label, rows in (("orders", orders), ("cases", cases)):
        s = summarise(rows)
        print(
            f"{label:7s} n={s['orders']:6d}  files={s['files']:6d}  "
            f"{s['first_date']}..{s['last_date']} ({s['days']}d, x{s['annualisation_factor']:.3f})  "
            f"L={s['landlord_filed']} T={s['tenant_filed']} C={s['coop_filed']}"
        )
    kinds = Counter(o["landlord_kind"] for o in cases if o["filed_by"] == "landlord")
    print("landlord cases by owner kind:", dict(kinds))
