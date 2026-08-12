# -*- coding: utf-8 -*-
"""
Sample LTB orders per application category, download the PDFs, extract text
(OCR fallback for scans), and pull out dollar amounts using keyword context.

Per ltb-amount-extraction-brief.md.
"""
import argparse
import io
import json
import random
import re
import time
from pathlib import Path
from statistics import mean, median

import fitz  # PyMuPDF
import pandas as pd
import pytesseract
import requests
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "ltb_open_data_export.json"
PDF_DIR = BASE / "pdfs"

FILE_NUMBER_FIELD_PREFIX = "File Number"
APPLICATIONS_FIELD_PREFIX = "Applications/Requ"
DOC_TYPE_FIELD_PREFIX = "Document Type"
ORDER_DATE_FIELD_PREFIX = "Order Date"
URL_FIELD_PREFIX = "ContentDownload URL"

CATEGORIES = ["L1", "L2", "L4", "T2", "T6", "T1"]
SEED = 42

POSTAL_RE = re.compile(r"([A-Za-z]\d[A-Za-z])\s?\d[A-Za-z]\d")


def extract_fsa(address):
    if not address:
        return None
    m = POSTAL_RE.search(address)
    return m.group(1).upper() if m else None


def load_address_field(fields):
    """Two near-duplicate field ids exist ('Rental Unit Address/...' and the
    mostly-empty double-slash 'Rental Unit Address//...'); pick the populated
    single-slash one specifically rather than a first-match prefix search."""
    candidates = [f["id"] for f in fields if f["id"].startswith("Rental Unit Address/")]
    single_slash = [c for c in candidates if not c.startswith("Rental Unit Address//")]
    return single_slash[0] if single_slash else candidates[0]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10,
                    help="documents to sample per category (equal allocation), or total sample budget with --allocation proportional")
    p.add_argument("--allocation", choices=["equal", "proportional"], default="equal",
                    help="'equal': --n docs from every category. 'proportional': --n total docs, "
                         "split across categories in proportion to each category's population size.")
    p.add_argument("--outdir", default=None, help="results subfolder name (default: n<N> or prop<N>)")
    return p.parse_args()


def allocate_proportional(total_budget, pop_counts):
    """Largest-remainder apportionment of total_budget across CATEGORIES, weighted by pop_counts."""
    total_pop = sum(pop_counts[c] for c in CATEGORIES)
    exact = {c: total_budget * pop_counts[c] / total_pop for c in CATEGORIES}
    floors = {c: int(exact[c]) for c in CATEGORIES}
    remainder = total_budget - sum(floors.values())
    order = sorted(CATEGORIES, key=lambda c: exact[c] - floors[c], reverse=True)
    for c in order[:remainder]:
        floors[c] += 1
    return floors

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# A thousands separator is sometimes a plain space instead of a comma where
# PDF text extraction loses the comma glyph across a line wrap (e.g. a PDF
# rendering "$5,892.49" gets extracted as "$5 892.49") — [ ,] covers both,
# deliberately excluding \n/\t so unrelated adjacent numbers don't get glued.
DOLLAR_RE = re.compile(r"\$\s?\d{1,3}(?:[ ,]\d{3})*(?:\.\d{2})?")
CONTEXT_CHARS = 80

FEE_KEYWORDS = ["filing fee", "application fee", "fee paid", "cost of filing", "n.s.f."]
RATE_KEYWORDS = ["per diem", "per day", "/day", "daily compensation", "each day", "rent/compensation"]
BOILERPLATE_KEYWORDS = [
    "board has authority to award", "independent of any award",
    "regardless of the amount claimed", "monetary jurisdiction",
]
ARREARS_KEYWORDS = [
    "arrears", "rent owing", "amount owing", "shall pay to the landlord",
    "owes the landlord", "total owing", "rent due", "outstanding rent",
]
REMEDY_KEYWORDS = [
    "compensation", "abatement", "rent reduction", "rent decrease",
    "rent shall be reduced", "reduction in rent",
]
REBATE_KEYWORDS = ["rebate"]

_PAY_VERBS = ["pay to the", "pay the", "owes the", "owe the", "owed to the"]
DIRECTION_TO_TENANT_KEYWORDS = [f"{v} tenant" for v in _PAY_VERBS] + [f"{v} tenants" for v in _PAY_VERBS]
DIRECTION_TO_LANDLORD_KEYWORDS = [f"{v} landlord" for v in _PAY_VERBS] + [f"{v} landlords" for v in _PAY_VERBS]


def detect_direction(ctx):
    to_tenant = any(k in ctx for k in DIRECTION_TO_TENANT_KEYWORDS)
    to_landlord = any(k in ctx for k in DIRECTION_TO_LANDLORD_KEYWORDS)
    if to_tenant and not to_landlord:
        return "to_tenant"
    if to_landlord and not to_tenant:
        return "to_landlord"
    return "unknown"


def extract_url(cell):
    if not cell:
        return None
    m = re.search(r'HYPERLINK\("([^"]+)"', cell)
    return m.group(1) if m else None


def load_field_name(fields, must_contain):
    """Resolve the exact field id even if punctuation/apostrophes vary slightly."""
    for f in fields:
        if must_contain in f["id"]:
            return f["id"]
    raise KeyError(must_contain)


def download_pdf(url, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        return True, "cached"
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            return True, "downloaded"
        except Exception as e:
            last_err = str(e)
            time.sleep(1.0)
    return False, last_err


def extract_text(pdf_path: Path):
    """Try native text extraction; fall back to OCR per page if too short."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
    except Exception:
        doc = None

    if len(text.strip()) >= 50:
        if doc is not None:
            doc.close()
        return text, "text"

    # OCR fallback
    ocr_text_parts = []
    try:
        if doc is None:
            doc = fitz.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text_parts.append(pytesseract.image_to_string(img))
        doc.close()
    except Exception as e:
        return text, f"ocr_failed:{e}"

    return "\n".join(ocr_text_parts), "ocr"


def parse_amount(s):
    digits = re.sub(r"[\s$,]", "", s)
    return float(digits)


ORDERED_SECTION_RE = re.compile(r"it is ordered(?:\s+on\s+consent)?\s+that", re.IGNORECASE)
CLAIM_KEYWORDS = ["sought", "requested", "seeks", "claimed", "testified that", "asked for"]


IS_TOTAL_RE = re.compile(r"\bis$", re.IGNORECASE)


def find_dollar_matches(text):
    matches = []
    for m in DOLLAR_RE.finditer(text):
        start, end = m.span()
        ctx_before = text[max(0, start - CONTEXT_CHARS):start]
        ctx_after = text[end:end + CONTEXT_CHARS]
        context = (ctx_before + m.group(0) + ctx_after).lower()
        try:
            value = parse_amount(m.group(0))
        except ValueError:
            continue
        # "...the amount X shall pay Y is $Z" — a dollar figure directly
        # preceded by "is" is almost always the self-declared bottom-line
        # total, as opposed to a line-item in its own breakdown (which is
        # instead introduced by "represents:", a bullet, or "for ...").
        is_stated_total = bool(IS_TOTAL_RE.search(ctx_before.rstrip()))
        matches.append({
            "raw": m.group(0),
            "value": value,
            "context": (ctx_before + ">>>" + m.group(0) + "<<<" + ctx_after).replace("\n", " ").strip(),
            "context_lower": context,
            "is_stated_total": is_stated_total,
        })
    return matches


def classify_matches(matches):
    """Tag each match as fee / rate / boilerplate (all excluded) / stated_total /
    claimed / arrears / remedy / rebate / other."""
    for m in matches:
        ctx = m["context_lower"]
        m["direction"] = detect_direction(ctx)
        if any(k in ctx for k in RATE_KEYWORDS):
            m["tag"] = "rate"
        elif any(k in ctx for k in FEE_KEYWORDS):
            m["tag"] = "fee"
        elif any(k in ctx for k in BOILERPLATE_KEYWORDS):
            # e.g. "the Board has authority to award up to $35,000" — a
            # statutory jurisdiction cap cited in template language, not an
            # amount actually awarded in this order
            m["tag"] = "boilerplate"
        elif m["is_stated_total"]:
            m["tag"] = "stated_total"
        elif any(k in ctx for k in CLAIM_KEYWORDS):
            # amount was requested/testified to, not necessarily awarded
            m["tag"] = "claimed"
        elif any(k in ctx for k in ARREARS_KEYWORDS):
            m["tag"] = "arrears"
        elif any(k in ctx for k in REBATE_KEYWORDS):
            m["tag"] = "rebate"
        elif any(k in ctx for k in REMEDY_KEYWORDS):
            m["tag"] = "remedy"
        else:
            m["tag"] = "other"
    return matches


PRIMARY_TAG_BY_CATEGORY = {
    "L1": "arrears", "L2": "arrears", "L4": "arrears",
    "T1": "rebate", "T2": "remedy", "T6": "remedy",
}

# Some orders combine a tenant application with a companion landlord
# application in one document (e.g. a T2 heard alongside an L1), so a T-code
# order can legitimately state arrears the TENANT owes the LANDLORD — the
# opposite of the remedy a T-code is supposed to represent, and vice versa.
# Guard against picking a same-document amount flowing the wrong way.
EXPECTED_DIRECTION_BY_CATEGORY = {
    "L1": "to_landlord", "L2": "to_landlord", "L4": "to_landlord",
    "T1": "to_tenant", "T2": "to_tenant", "T6": "to_tenant",
}


def _rank_candidates(candidates, category, fee_amounts, scope_note):
    """Given a non-empty, non-fee/rate/boilerplate candidate pool, pick the primary amount."""
    preferred_tag = PRIMARY_TAG_BY_CATEGORY.get(category)

    expected_dir = EXPECTED_DIRECTION_BY_CATEGORY.get(category)
    if expected_dir:
        wrong_dir = "to_landlord" if expected_dir == "to_tenant" else "to_tenant"
        directed = [m for m in candidates if m["direction"] != wrong_dir]
        if not directed:
            worst = max(candidates, key=lambda m: m["value"])
            note = (
                f"{scope_note}; only opposite-direction amount(s) found (money flowing the "
                f"other way, likely a combined hearing) — no correctly-directed amount found; "
                f"largest opposite-direction figure was \\${worst['value']:,.2f}, excluded"
            )
            return None, None, note, fee_amounts, None
        candidates = directed

    awarded = [m for m in candidates if m["tag"] != "claimed"]
    pool = awarded if awarded else candidates
    pool_note = scope_note if awarded else scope_note + "; only requested/testified amounts found, no confirmed award — verify manually"

    # a self-declared "...is $X" total always outranks its own line-item
    # breakdown or any other candidate, regardless of category keyword match
    stated = [m for m in pool if m["tag"] == "stated_total"]
    if stated:
        best = max(stated, key=lambda m: m["value"])
        return best["value"], best["tag"], f"{pool_note}; explicit stated-total phrasing (\"...is \\$X\")", fee_amounts, best["context"]

    strong = [m for m in pool if m["tag"] == preferred_tag]
    if strong:
        best = max(strong, key=lambda m: m["value"])
        return best["value"], best["tag"], f"{pool_note}; matched expected keyword for category", fee_amounts, best["context"]

    if len(pool) == 1:
        best = pool[0]
        return best["value"], best["tag"], f"{pool_note}; single candidate amount, no strong keyword match", fee_amounts, best["context"]

    best = max(pool, key=lambda m: m["value"])
    return best["value"], "ambiguous-max", f"{pool_note}; multiple candidate amounts, took max — manual review advised", fee_amounts, best["context"]


def pick_primary(text, category):
    """
    Restrict the search to the operative 'It is ordered that' section where it
    exists (enforceable amounts), since the reasoning/determinations section
    often cites unrelated testimony or amounts the party merely sought rather
    than was awarded. Fall back to the full document if that section has no
    usable amount.
    """
    full_matches = classify_matches(find_dollar_matches(text))
    fee_amounts = [m["value"] for m in full_matches if m["tag"] == "fee"]
    all_amounts = [m["value"] for m in full_matches]

    op = ORDERED_SECTION_RE.search(text)
    ordered_matches = classify_matches(find_dollar_matches(text[op.start():])) if op else []
    ordered_matches_nonexcluded = [m for m in ordered_matches if m["tag"] not in ("rate", "fee", "boilerplate")]

    if ordered_matches_nonexcluded:
        primary, amount_type, note, _, context = _rank_candidates(
            ordered_matches_nonexcluded, category, fee_amounts, "found in operative 'It is ordered that' section"
        )
        return primary, amount_type, note, fee_amounts, context, all_amounts

    if op is not None and ordered_matches:
        # the operative section exists and had dollar figures, but every one
        # of them was a fee/rate/boilerplate exclusion — that's a real "no
        # lump sum ordered" result (e.g. a per-diem use-compensation order),
        # not a reason to go fish for unrelated testimony amounts in the
        # reasoning section
        note = (
            "operative section found but contained only fee/rate/boilerplate "
            "amounts — likely no lump sum ordered"
        )
        return None, None, note, fee_amounts, None, all_amounts

    # either no operative section was found, or it had zero dollar mentions
    # at all (order may refer back to an amount stated earlier without
    # restating it) — fall back to a full-document search
    full_candidates = [m for m in full_matches if m["tag"] not in ("rate", "fee", "boilerplate")]
    if not full_candidates:
        note = "no dollar amount found" if not full_matches else "only fee/rate/boilerplate amounts found"
        return None, None, note, fee_amounts, None, all_amounts

    primary, amount_type, note, _, context = _rank_candidates(
        full_candidates, category, fee_amounts,
        "no operative section found, or it had no dollar mentions at all; fell back to full-document search"
    )
    return primary, amount_type, note, fee_amounts, context, all_amounts


def main():
    args = parse_args()
    default_outdir = (
        f"amounts_equal_sample_{args.n}_per_category" if args.allocation == "equal"
        else "amounts_proportional_sample"
    )
    outdir = args.outdir or default_outdir
    results_dir = BASE / "results" / outdir
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_csv = results_dir / "extraction_raw.csv"
    summary_csv = results_dir / "extraction_summary.csv"

    random.seed(SEED)
    PDF_DIR.mkdir(exist_ok=True)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    fields = data["fields"]
    FILE_NUMBER_FIELD = load_field_name(fields, FILE_NUMBER_FIELD_PREFIX)
    APPLICATIONS_FIELD = load_field_name(fields, APPLICATIONS_FIELD_PREFIX)
    DOC_TYPE_FIELD = load_field_name(fields, DOC_TYPE_FIELD_PREFIX)
    ORDER_DATE_FIELD = load_field_name(fields, ORDER_DATE_FIELD_PREFIX)
    URL_FIELD = load_field_name(fields, URL_FIELD_PREFIX)
    ADDRESS_FIELD = load_address_field(fields)

    idx = {f["id"]: i for i, f in enumerate(fields)}

    by_cat = {}
    for r in data["records"]:
        code = r[idx[APPLICATIONS_FIELD]]
        if code in CATEGORIES:
            by_cat.setdefault(code, []).append(r)

    pop_counts = {c: len(by_cat.get(c, [])) for c in CATEGORIES}
    print("Pool sizes:", pop_counts)

    if args.allocation == "proportional":
        n_by_category = allocate_proportional(args.n, pop_counts)
        print("Proportional allocation (total budget "
              f"{args.n}, weighted by category population):", n_by_category)
    else:
        n_by_category = {c: args.n for c in CATEGORIES}

    sample = {
        cat: random.sample(rows, min(n_by_category[cat], len(rows)))
        for cat, rows in by_cat.items()
    }

    results = []
    total = sum(len(v) for v in sample.values())
    done = 0

    for cat in CATEGORIES:
        rows = sample.get(cat, [])
        for r in rows:
            done += 1
            file_number = r[idx[FILE_NUMBER_FIELD]]
            doc_type = r[idx[DOC_TYPE_FIELD]]
            order_date = r[idx[ORDER_DATE_FIELD]]
            url = extract_url(r[idx[URL_FIELD]])
            fsa = extract_fsa(r[idx[ADDRESS_FIELD]])

            print(f"[{done}/{total}] {cat} {file_number} ...", end=" ")

            row = {
                "file_number": file_number,
                "category": cat,
                "doc_type": doc_type,
                "order_date": order_date,
                "fsa": fsa,
                "url": url,
                "extraction_method": None,
                "all_amounts_found": None,
                "fee_amounts_found": None,
                "primary_amount": None,
                "amount_type": None,
                "matched_context": None,
                "notes": None,
            }

            if not url:
                row["notes"] = "no download URL"
                results.append(row)
                print("no URL")
                continue

            pdf_path = PDF_DIR / f"{file_number}.pdf"
            ok, status = download_pdf(url, pdf_path)
            if status == "downloaded":
                time.sleep(0.75)
            if not ok:
                row["notes"] = f"download failed: {status}"
                results.append(row)
                print("download FAILED")
                continue

            text, method = extract_text(pdf_path)
            row["extraction_method"] = method

            if method not in ("text", "ocr"):
                row["notes"] = method
                results.append(row)
                print(method)
                continue

            primary, amount_type, note, fee_amounts, context, all_amounts = pick_primary(text, cat)

            row["all_amounts_found"] = all_amounts
            row["fee_amounts_found"] = fee_amounts
            row["primary_amount"] = primary
            row["amount_type"] = amount_type
            row["matched_context"] = context
            row["notes"] = note

            results.append(row)
            print(f"{method}, primary={primary}")

    df = pd.DataFrame(results)
    df.to_csv(raw_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved raw per-document results to {raw_csv}")

    summary_rows = []
    for cat, g in df.groupby("category"):
        with_amt = g["primary_amount"].dropna()
        summary_rows.append({
            "category": cat,
            "count_total": len(g),
            "count_with_amount": len(with_amt),
            "found_rate": round(len(with_amt) / len(g), 2) if len(g) else None,
            "min": round(with_amt.min(), 2) if len(with_amt) else None,
            "max": round(with_amt.max(), 2) if len(with_amt) else None,
            "median": round(with_amt.median(), 2) if len(with_amt) else None,
            "mean": round(with_amt.mean(), 2) if len(with_amt) else None,
        })
    summary_df = pd.DataFrame(summary_rows).set_index("category").loc[
        [c for c in CATEGORIES if c in df["category"].unique()]
    ].reset_index()
    summary_df.to_csv(summary_csv, index=False)
    print(f"Saved summary to {summary_csv}")

    print("\n=== SUMMARY ===")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
