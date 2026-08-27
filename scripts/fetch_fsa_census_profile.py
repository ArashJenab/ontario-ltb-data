# -*- coding: utf-8 -*-
"""
Fetch the 2021 Census Profile by Forward Sortation Area (StatCan
98-401-X2021013) and extract the housing/income characteristics the LTB
analysis needs, for Ontario FSAs only.

Why this file rather than the individual StatCan tables: the Census Profile
carries tenure, income, shelter cost and core-housing-need for every FSA in
one download, so a single fetch replaces four table-specific ones and every
figure is guaranteed to come from the same census release.

The existing data/fsa_population.csv (table 98-10-0019-01) stays as the
population denominator. What this adds is the *renter household* denominator,
which is the honest one for a rental-dispute rate: an FSA that is 80% renters
will show more LTB activity per resident than one that is 20% renters without
anything else being different about it.

Ontario FSAs are exactly those beginning K, L, M, N or P; no other province
uses those letters.
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
OUT_PATH = BASE / "data" / "fsa_census_profile.csv"
RAW_DIR = BASE / "data" / "raw_statcan_98401X2021013"
RAW_ZIP = RAW_DIR / "98-401-X2021013_eng_CSV.zip"

SOURCE_URL = (
    "https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/"
    "download-telecharger/comp/GetFile.cfm?Lang=E&FILETYPE=CSV&GEONO=013"
)

ONTARIO_FSA_LETTERS = ("K", "L", "M", "N", "P")

# CHARACTERISTIC_ID -> output column. IDs are stable within a census cycle and
# were read off the province-level profile (98-401-X2021001), where Ontario
# reports e.g. 1,724,970 renter households and $91,000 median household income
# — those provincial totals are the check that these IDs mean what we think.
CHARACTERISTICS = {
    1: "population_2021",
    243: "median_household_income",
    244: "median_household_income_after_tax",
    1414: "households_total",
    1415: "households_owner",
    1416: "households_renter",
    1490: "tenant_households",
    1491: "pct_tenant_subsidized",
    1492: "pct_tenant_shelter_over_30pct",
    1493: "pct_tenant_core_housing_need",
    1494: "median_monthly_rent",
    1495: "average_monthly_rent",
}

# Column order in the output, after fsa.
COLUMNS = [
    "population_2021",
    "households_total",
    "households_owner",
    "households_renter",
    "pct_renter",
    "median_household_income",
    "median_household_income_after_tax",
    "tenant_households",
    "pct_tenant_subsidized",
    "pct_tenant_shelter_over_30pct",
    "pct_tenant_core_housing_need",
    "median_monthly_rent",
    "average_monthly_rent",
    "rent_to_income_ratio",
]


def download(force=False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_ZIP.exists() and not force:
        print(f"Using cached {RAW_ZIP} ({RAW_ZIP.stat().st_size / 1e6:.0f} MB)")
        return RAW_ZIP

    print(f"Downloading {SOURCE_URL}")
    resp = requests.get(SOURCE_URL, timeout=600, stream=True)
    resp.raise_for_status()
    written = 0
    with open(RAW_ZIP, "wb") as fh:
        for chunk in resp.iter_content(1 << 20):
            fh.write(chunk)
            written += len(chunk)
            print(f"\r  {written / 1e6:.0f} MB", end="", file=sys.stderr)
    print(f"\r  {written / 1e6:.0f} MB total", file=sys.stderr)
    return RAW_ZIP


def parse_number(raw):
    """Census profile suppresses/withholds cells with x, F, .., or blanks."""
    raw = (raw or "").strip()
    if not raw or raw in ("x", "F", "..", "...", "n/a"):
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def main():
    force = "--force" in sys.argv
    zip_path = download(force=force)

    with zipfile.ZipFile(zip_path) as zf:
        data_name = next(
            n for n in zf.namelist() if n.endswith("_data.csv") or n.endswith("data.csv")
        )
        print(f"Reading {data_name}")

        rows = {}
        with zf.open(data_name) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="latin-1"))
            header = next(reader)
            i_code = header.index("ALT_GEO_CODE")
            i_char = header.index("CHARACTERISTIC_ID")
            i_val = header.index("C1_COUNT_TOTAL")

            for row in reader:
                if len(row) <= i_val:
                    continue
                fsa = row[i_code].strip().upper()
                if len(fsa) != 3 or not fsa.startswith(ONTARIO_FSA_LETTERS):
                    continue
                try:
                    char_id = int(row[i_char])
                except ValueError:
                    continue
                col = CHARACTERISTICS.get(char_id)
                if col is None:
                    continue
                rows.setdefault(fsa, {})[col] = parse_number(row[i_val])

    if not rows:
        raise SystemExit("No Ontario FSA rows found — the file layout may have changed.")

    # Derived columns. pct_renter is the one the maps actually need; the rent
    # burden ratio is a convenience for the income scatter.
    for fsa, rec in rows.items():
        total = rec.get("households_total")
        renter = rec.get("households_renter")
        rec["pct_renter"] = round(100 * renter / total, 2) if total and renter else None

        rent = rec.get("average_monthly_rent")
        income = rec.get("median_household_income")
        rec["rent_to_income_ratio"] = (
            round(100 * (rent * 12) / income, 1) if rent and income else None
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["fsa"] + COLUMNS)
        for fsa in sorted(rows):
            rec = rows[fsa]
            writer.writerow([fsa] + [_fmt(rec.get(c)) for c in COLUMNS])

    renter_total = sum(
        r.get("households_renter") or 0 for r in rows.values()
    )
    print(f"\nOntario FSAs: {len(rows)}")
    print(f"Renter households summed across FSAs: {renter_total:,.0f}")
    print("  (province-level profile reports 1,724,970 — small gaps are suppressed cells)")
    missing = sum(1 for r in rows.values() if r.get("median_household_income") is None)
    print(f"FSAs with no median income (suppressed): {missing}")
    print(f"\nSaved to {OUT_PATH}")


def _fmt(value):
    if value is None:
        return ""
    if float(value).is_integer():
        return int(value)
    return value


if __name__ == "__main__":
    main()
