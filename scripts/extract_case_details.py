# -*- coding: utf-8 -*-
"""
Read a large sample of landlord-side order PDFs and pull out the fields the
open-data export does not carry: the monthly rent, the hearing date, who
attended, and who was represented.

Why this exists separately from extract_amounts.py: that script answers "how
much money", one category at a time, serially, with a polite sleep between
documents. It works and is not changed here. This one answers "how much money
*relative to the rent on that unit*", which is the question that distinguishes
a loss a corporate owner absorbs from one an individual owner cannot, and it
needs a sample large enough to carry a confidence interval. It reuses this
module's download and text extraction so both scripts agree on what a PDF says.

The rent is recoverable because non-payment orders state the daily rate and
show their work:

    "the daily rent/compensation is $75.13. This amount is calculated as
     follows: $2,285.11 x 12, divided by 365 days."

so the monthly rent is the figure before "x 12". Roughly 40% of landlord
orders state it in that form; a further set state "lawful rent is $X" or
"Rent was $X per month".

Usage:
    python scripts/extract_case_details.py --n 5000
    python scripts/extract_case_details.py --n 200 --workers 2     # a quick pass
"""
import argparse
import csv
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import extract_amounts as ea

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "results" / "case_details"
DATA_PATH = BASE / "data" / "ltb_open_data_export.json"

# The default frame: the landlord money categories, where an amount and a rent
# are both plausibly stated. Proportional allocation within these three makes an
# unweighted mean over the sample a population mean *for landlord money cases*,
# which is the question the burden figures answer.
MONEY_CATEGORIES = ("L1", "L2", "L4")

# --categories all widens the frame to every application type, weighted by how
# common each is across the whole caseload. Needed for any question about
# process rather than money: attendance and representation cannot be read off a
# landlord-money-only sample, because in a tenant-filed case the tenant is the
# applicant and the roles invert. Sampling only L1/L2/L4 and reporting
# "tenants attend 52%" would be measuring one side of the docket and calling it
# the whole.
ALL_CATEGORIES = (
    "L1", "L2", "L4", "T2", "T1", "T6", "L10", "L3", "L5", "T5", "L9", "A2",
    "T3", "L8", "A1", "C1", "C2", "C4", "T7", "T4",
)

SEED = 20260827

# --- Field patterns ---------------------------------------------------------
# Monthly rent, most reliable form first.
RENT_PATTERNS = [
    re.compile(r"\$\s?([\d, ]+\.\d{2})\s*(?:x|X|×)\s*12\s*,?\s*divided\s*by\s*365", re.I),
    re.compile(r"lawful\s+rent\s+is\s+\$\s?([\d, ]+\.?\d{0,2})", re.I),
    re.compile(r"(?:monthly\s+)?rent\s+(?:is|was)\s+\$\s?([\d, ]+\.?\d{0,2})\s*(?:per\s+month|monthly|a\s+month)", re.I),
    re.compile(r"rent\s+of\s+\$\s?([\d, ]+\.?\d{0,2})\s*per\s+month", re.I),
]

HEARING_DATE_RE = re.compile(
    r"heard\s+(?:by\s+[\w\- ]+\s+)?on\s+([A-Z][a-z]+\s+\d{1,2},?\s+20\d\d)", re.I
)
ATTENDANCE_RE = re.compile(r"([^.]{0,260}?attended the hearing)", re.I)
NO_ATTEND_RE = re.compile(
    r"(did not attend|was not present|were not present|no one (?:appeared|attended)"
    r"|did not appear)",
    re.I,
)
REP_RE = re.compile(r"(legal\s+representative|representative|paralegal|counsel|agent)", re.I)

print_lock = threading.Lock()


def parse_money(raw):
    try:
        return float(raw.replace(",", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def extract_rent(text):
    """(monthly_rent, which_pattern_matched) or (None, None)."""
    for i, pattern in enumerate(RENT_PATTERNS):
        match = pattern.search(text)
        if match:
            value = parse_money(match.group(1))
            # A "monthly rent" outside this band is a misparse (a total, a
            # deposit, or a daily rate), not a rent.
            if value and 200 <= value <= 20000:
                return value, f"pattern_{i + 1}"
    return None, None


def extract_attendance(text):
    """Who attended, and whether either side had a representative.

    The attendance sentence names whoever was there, e.g. "the Landlord's
    Legal Representative, Faith McGregor, attended the hearing". Absence of a
    party from that sentence is treated as absence from the hearing only when
    the sentence itself was found, so a missing sentence stays unknown rather
    than being scored as a no-show.
    """
    result = {
        "hearing_sentence_found": False,
        "landlord_attended": None,
        "tenant_attended": None,
        "landlord_represented": None,
        "tenant_represented": None,
        "explicit_non_attendance": bool(NO_ATTEND_RE.search(text)),
    }
    match = ATTENDANCE_RE.search(text)
    if not match:
        return result

    sentence = match.group(1)
    result["hearing_sentence_found"] = True
    lowered = sentence.lower()

    # Split the sentence at the landlord/tenant mentions so a representative
    # named next to one party is not credited to the other.
    landlord_span = [m.start() for m in re.finditer(r"landlord", lowered)]
    tenant_span = [m.start() for m in re.finditer(r"tenant", lowered)]
    result["landlord_attended"] = bool(landlord_span)
    result["tenant_attended"] = bool(tenant_span)

    for party, positions in (("landlord", landlord_span), ("tenant", tenant_span)):
        represented = False
        for position in positions:
            window = lowered[position:position + 80]
            if REP_RE.search(window):
                represented = True
                break
        result[f"{party}_represented"] = represented if positions else None
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5000,
                        help="total documents to sample across L1/L2/L4")
    parser.add_argument("--workers", type=int, default=4,
                        help="concurrent downloads (kept low deliberately)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds each worker waits after a fresh download")
    parser.add_argument("--categories", choices=["money", "all"], default="money",
                        help="'money': L1/L2/L4 only, for the burden figures. "
                             "'all': every application type, weighted by how common "
                             "each is, for questions about process.")
    parser.add_argument("--outdir", default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    default_dir = "case_details" if args.categories == "money" else "case_details_all"
    out_dir = BASE / "results" / (args.outdir or default_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ea.PDF_DIR.mkdir(exist_ok=True)
    random.seed(SEED)

    with open(DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    fields = data["fields"]
    index = {f["id"]: i for i, f in enumerate(fields)}
    file_field = ea.load_field_name(fields, ea.FILE_NUMBER_FIELD_PREFIX)
    apps_field = ea.load_field_name(fields, ea.APPLICATIONS_FIELD_PREFIX)
    doc_field = ea.load_field_name(fields, ea.DOC_TYPE_FIELD_PREFIX)
    date_field = ea.load_field_name(fields, ea.ORDER_DATE_FIELD_PREFIX)
    url_field = ea.load_field_name(fields, ea.URL_FIELD_PREFIX)
    address_field = ea.load_address_field(fields)

    categories = MONEY_CATEGORIES if args.categories == "money" else ALL_CATEGORIES
    pools = {c: [] for c in categories}
    for record in data["records"]:
        code = record[index[apps_field]]
        if code in pools:
            pools[code].append(record)

    # Proportional allocation: the sample should mirror the real category mix
    # so an unweighted mean over it is already a population mean.
    population = {c: len(pools[c]) for c in categories if pools[c]}
    total_population = sum(population.values())
    allocation = {
        c: min(len(pools[c]), round(args.n * population[c] / total_population))
        for c in population
    }
    # Largest-remainder would be tidier, but rounding drift of a few documents
    # across twenty categories does not move any figure derived from this.
    print(f"Pool sizes: {population}")
    print(f"Sampling {sum(allocation.values())} documents: {allocation}")

    sample = []
    for code in allocation:
        for record in random.sample(pools[code], allocation[code]):
            sample.append((code, record))
    random.shuffle(sample)

    total = len(sample)
    counter = {"done": 0, "rent": 0, "amount": 0, "hearing": 0}
    rows = []
    rows_lock = threading.Lock()

    def process(item):
        code, record = item
        file_number = record[index[file_field]]
        url = ea.extract_url(record[index[url_field]])
        row = {
            "file_number": file_number,
            "category": code,
            "doc_type": record[index[doc_field]],
            "order_date": record[index[date_field]],
            "fsa": ea.extract_fsa(record[index[address_field]]),
            "primary_amount": None,
            "amount_type": None,
            "monthly_rent": None,
            "rent_pattern": None,
            "months_of_rent_owed": None,
            "hearing_date": None,
            "hearing_sentence_found": False,
            "landlord_attended": None,
            "tenant_attended": None,
            "landlord_represented": None,
            "tenant_represented": None,
            "explicit_non_attendance": None,
            "extraction_method": None,
            "notes": None,
        }

        if not url:
            row["notes"] = "no download URL"
            return row

        pdf_path = ea.PDF_DIR / f"{file_number}.pdf"
        ok, status = ea.download_pdf(url, pdf_path)
        if status == "downloaded":
            time.sleep(args.delay)
        if not ok:
            row["notes"] = f"download failed: {status}"
            return row

        text, method = ea.extract_text(pdf_path)
        row["extraction_method"] = method
        if method not in ("text", "ocr"):
            row["notes"] = method
            return row

        flat = " ".join(text.split())

        primary, amount_type, note, _fees, _ctx, _all = ea.pick_primary(text, code)
        row["primary_amount"] = primary
        row["amount_type"] = amount_type
        row["notes"] = note

        rent, pattern = extract_rent(flat)
        row["monthly_rent"] = rent
        row["rent_pattern"] = pattern
        if rent and primary:
            row["months_of_rent_owed"] = round(primary / rent, 2)

        hearing = HEARING_DATE_RE.search(flat)
        row["hearing_date"] = hearing.group(1) if hearing else None
        row.update(extract_attendance(flat))
        return row

    def worker(item):
        try:
            row = process(item)
        except Exception as exc:  # keep one bad PDF from killing the run
            code, record = item
            row = {
                "file_number": record[index[file_field]],
                "category": code,
                "notes": f"error: {type(exc).__name__}: {exc}",
            }
        with rows_lock:
            rows.append(row)
            counter["done"] += 1
            counter["rent"] += 1 if row.get("monthly_rent") else 0
            counter["amount"] += 1 if row.get("primary_amount") else 0
            counter["hearing"] += 1 if row.get("hearing_sentence_found") else 0
            if counter["done"] % 25 == 0 or counter["done"] == total:
                with print_lock:
                    print(
                        f"\r[{counter['done']}/{total}] "
                        f"amount {counter['amount']} · rent {counter['rent']} · "
                        f"hearing {counter['hearing']}",
                        end="",
                        file=sys.stderr,
                        flush=True,
                    )
        return row

    started = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(worker, sample))
    print(file=sys.stderr)

    rows.sort(key=lambda r: (r.get("category") or "", r.get("file_number") or ""))
    raw_path = out_dir / "case_details_raw.csv"
    keys = list({k: None for row in rows for k in row})
    with open(raw_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - started
    print(f"\nDone in {elapsed / 60:.1f} min. {len(rows)} rows -> {raw_path}")
    print(f"  amount found : {counter['amount']} ({100 * counter['amount'] / total:.0f}%)")
    print(f"  rent found   : {counter['rent']} ({100 * counter['rent'] / total:.0f}%)")
    print(f"  hearing line : {counter['hearing']} ({100 * counter['hearing'] / total:.0f}%)")
    print("\nNext: python scripts/analyze_burden.py")


if __name__ == "__main__":
    main()
