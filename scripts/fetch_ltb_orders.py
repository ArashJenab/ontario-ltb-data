# -*- coding: utf-8 -*-
"""Fetch the LTB Order Catalogue from Ontario's CKAN Data API and refresh
data/ltb_open_data_export.json in place.

Every fetch is archived to data/snapshots/ (gitignored — a local safety net
in case the government changes or removes records between fetches; the
project directory itself already lives inside OneDrive sync).

The fetch is only *adopted* as the active dataset if it differs from the
current active dataset by more than --threshold percent (by Document ID
churn: records added + removed, divided by the old total). A small change
(e.g. a few thousand new orders on top of ~40,000) is expected drift and
does not by itself invalidate the existing dollar-amount sample, which is
expensive to regenerate (PDF download + OCR/extraction over a few hundred
sampled orders). A large change is flagged so that sample can be redrawn
deliberately — this script never re-runs extract_amounts.py itself.

Usage:
    python scripts/fetch_ltb_orders.py                  # fetch, compare, adopt if significant
    python scripts/fetch_ltb_orders.py --threshold 5     # use a 5% churn threshold
    python scripts/fetch_ltb_orders.py --force            # always adopt the new fetch
    python scripts/fetch_ltb_orders.py --dry-run           # fetch + compare, write nothing
"""
import argparse
import csv
import datetime
import gzip
import json
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ACTIVE_PATH = BASE / "data" / "ltb_open_data_export.json"
SNAPSHOT_DIR = BASE / "data" / "snapshots"
LOG_PATH = BASE / "data" / "fetch_log.csv"
KEEP_SNAPSHOTS = 5

CKAN_BASE_URL = "https://data.ontario.ca/api/3/action/datastore_search"
RESOURCE_ID = "86e75d11-1c2c-4cd9-9b0d-9fccec302b30"  # LTB Order Catalogue, data.ontario.ca
PAGE_SIZE = 20000

DOC_ID_FIELD = "Document ID/Identifiant du document"


def fetch_all_records():
    """Paginate datastore_search until every record is retrieved."""
    fields = None
    records = []
    offset = 0
    while True:
        url = (
            f"{CKAN_BASE_URL}?resource_id={RESOURCE_ID}"
            f"&limit={PAGE_SIZE}&offset={offset}"
        )
        with urllib.request.urlopen(url) as resp:
            payload = json.load(resp)
        if not payload.get("success", False):
            raise RuntimeError(f"CKAN API error: {payload}")
        result = payload["result"]
        if fields is None:
            fields = result["fields"]
        page = result["records"]
        records.extend(page)
        total = result.get("total", len(records))
        offset += len(page)
        print(f"  fetched {offset}/{total}")
        if len(page) < PAGE_SIZE or offset >= total:
            break
    return fields, records


def to_legacy_shape(fields, record_dicts):
    """Convert CKAN's list-of-dicts records into the {fields, records-as-arrays}
    shape the rest of the pipeline (postal_analysis.py, extract_amounts.py,
    make_chart.py, ...) already expects."""
    field_ids = [f["id"] for f in fields]
    records = [[r.get(fid) for fid in field_ids] for r in record_dicts]
    return {"fields": fields, "records": records}


def doc_ids(data):
    idx = {f["id"]: i for i, f in enumerate(data["fields"])}
    col = idx[DOC_ID_FIELD]
    return {r[col] for r in data["records"]}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def write_snapshot(data, today):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_path = SNAPSHOT_DIR / f"ltb_orders_{today}.json.gz"
    with gzip.open(snap_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    # prune to the most recent KEEP_SNAPSHOTS
    snaps = sorted(SNAPSHOT_DIR.glob("ltb_orders_*.json.gz"))
    for old in snaps[:-KEEP_SNAPSHOTS]:
        old.unlink()
    return snap_path


def log_run(today, total_new, added, removed, churn_pct, threshold, adopted):
    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["date", "total_records", "added", "removed",
                        "churn_pct", "threshold_pct", "adopted"])
        w.writerow([today, total_new, added, removed,
                    f"{churn_pct:.2f}", threshold, adopted])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=10.0,
                    help="churn %% (added+removed / old total) above which the fetch is adopted (default: 10)")
    p.add_argument("--force", action="store_true", help="always adopt the new fetch")
    p.add_argument("--dry-run", action="store_true", help="fetch + compare, write nothing")
    args = p.parse_args()

    today = datetime.date.today().isoformat()

    print(f"Fetching LTB Order Catalogue from CKAN (resource {RESOURCE_ID})...")
    fields, record_dicts = fetch_all_records()
    new_data = to_legacy_shape(fields, record_dicts)
    new_total = len(new_data["records"])
    new_ids = doc_ids(new_data)
    print(f"Fetched {new_total} records.")

    if ACTIVE_PATH.exists():
        with open(ACTIVE_PATH, encoding="utf-8") as f:
            old_data = json.load(f)
        old_ids = doc_ids(old_data)
    else:
        old_ids = set()

    added = new_ids - old_ids
    removed = old_ids - new_ids
    churn_pct = (len(added) + len(removed)) / max(len(old_ids), 1) * 100
    adopt = args.force or not old_ids or churn_pct >= args.threshold

    print(f"\nCompared to current active snapshot ({len(old_ids)} records):")
    print(f"  + {len(added)} added, - {len(removed)} removed  ->  {churn_pct:.2f}% churn "
          f"(threshold: {args.threshold}%)")

    if args.dry_run:
        print("\n--dry-run: not writing snapshot, active file, or log.")
        return

    write_snapshot(new_data, today)
    log_run(today, new_total, len(added), len(removed), churn_pct, args.threshold, adopt)

    if adopt:
        write_json(ACTIVE_PATH, new_data)
        if churn_pct >= args.threshold and old_ids:
            print(
                "\n*** SIGNIFICANT CHANGE — adopted. ***\n"
                "The dollar-amount sample was drawn against the previous population and may no\n"
                "longer be representative. Consider redrawing it:\n"
                "  python scripts/extract_amounts.py --n 600 --allocation proportional "
                "--outdir amounts_proportional_sample\n"
                "  python scripts/make_perspective_chart.py --n 600 --allocation proportional "
                "--outdir amounts_proportional_sample\n"
                "then re-run the chart/map build scripts that read from data/ltb_open_data_export.json."
            )
        else:
            print("\nAdopted (first fetch or --force).")
    else:
        print(
            f"\nChange is within normal drift ({churn_pct:.2f}% < {args.threshold}% threshold).\n"
            "Keeping the existing data/ltb_open_data_export.json as-is — no resampling needed.\n"
            "The new fetch was still archived to data/snapshots/ for backup."
        )


if __name__ == "__main__":
    main()
