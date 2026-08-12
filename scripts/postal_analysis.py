# -*- coding: utf-8 -*-
"""
Geographic breakdown of LTB applications by FSA (Forward Sortation Area — the
first 3 characters of a Canadian postal code, e.g. "N6J"). This is the
standard unit Statistics Canada publishes population data for; a full 6-char
postal code is usually a single building and too granular to normalize
against population.

Runs over the FULL population (40,844 records) — no PDF downloads needed,
since the rental unit address (and therefore postal code) is already present
in the open-data export for every record.

NOTE: this produces raw application COUNTS by area, not per-capita rates.
Turning this into "applications per 10,000 residents" requires joining
against a population-by-FSA table (e.g. Statistics Canada census data),
which is a deliberate follow-up step, not done here.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "ltb_open_data_export.json"
OUT_DIR = BASE / "results" / "applications_by_area"

TRACKED_CODES = ["L1", "L2", "L4", "T2", "T6", "T1"]

POSTAL_RE = re.compile(r"([A-Za-z]\d[A-Za-z])\s?\d[A-Za-z]\d")
BLUE = "#2a78d6"
ORANGE = "#eb6834"


def load_address_field(fields):
    """
    There are two near-duplicate field ids in this export:
      'Rental Unit Address/Adresse du logement locatif'   (populated, 99.99%)
      'Rental Unit Address//Adresse du logement locatif'  (double slash, mostly empty)
    Pick the single-slash one specifically — a plain prefix match would grab
    whichever comes first in the fields list, which isn't reliably the
    populated one.
    """
    candidates = [f["id"] for f in fields if f["id"].startswith("Rental Unit Address/")]
    single_slash = [c for c in candidates if not c.startswith("Rental Unit Address//")]
    if single_slash:
        return single_slash[0]
    if candidates:
        return candidates[0]
    raise KeyError("Rental Unit Address")


def extract_fsa(address):
    if not address:
        return None
    m = POSTAL_RE.search(address)
    return m.group(1).upper() if m else None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    fields = data["fields"]
    idx = {f["id"]: i for i, f in enumerate(fields)}
    addr_field = load_address_field(fields)
    addr_col = idx[addr_field]

    apptype_field = [f["id"] for f in fields if "Application Type" in f["id"]][0]
    apptype_col = idx[apptype_field]

    apps_field = [f["id"] for f in fields if "Applications/Requ" in f["id"]][0]
    apps_col = idx[apps_field]

    total = Counter()
    by_type = defaultdict(Counter)      # fsa -> {'L': n, 'T': n, 'C': n}
    by_tracked_code = defaultdict(Counter)  # fsa -> {'L1': n, 'T2': n, ...}
    no_fsa = 0

    for r in data["records"]:
        fsa = extract_fsa(r[addr_col])
        if not fsa:
            no_fsa += 1
            continue
        total[fsa] += 1
        atype = r[apptype_col]
        if atype:
            by_type[fsa][atype] += 1
        code = r[apps_col]
        if code in TRACKED_CODES:
            by_tracked_code[fsa][code] += 1

    rows = []
    for fsa, cnt in total.items():
        row = {
            "fsa": fsa,
            "total_applications": cnt,
            "landlord_filed": by_type[fsa].get("L", 0),
            "tenant_filed": by_type[fsa].get("T", 0),
            "coop_filed": by_type[fsa].get("C", 0),
        }
        for code in TRACKED_CODES:
            row[code] = by_tracked_code[fsa].get(code, 0)
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("total_applications", ascending=False).reset_index(drop=True)
    out_csv = OUT_DIR / "fsa_application_counts.csv"
    df.to_csv(out_csv, index=False)

    print(f"Records with no extractable FSA (e.g. 'Multiple Rental Units'): {no_fsa} / {len(data['records'])}")
    print(f"Distinct FSAs found: {len(df)}")
    print(f"Saved full FSA count table to {out_csv}")
    print("\nTop 20 FSAs by total applications:")
    print(df.head(20).to_string(index=False))

    # --- chart: top 20 FSAs, landlord- vs tenant-filed split ---
    top20 = df.head(20).sort_values("total_applications", ascending=True)

    fig, ax = plt.subplots(figsize=(11.5, 8.5))
    y_pos = range(len(top20))
    ax.barh(y_pos, top20["landlord_filed"], color=BLUE, height=0.65, zorder=3, label="Landlord-filed")
    ax.barh(y_pos, top20["tenant_filed"], left=top20["landlord_filed"], color=ORANGE, height=0.65, zorder=3, label="Tenant-filed")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(top20["fsa"], fontsize=10.5)
    ax.set_xlabel("Number of LTB applications (orders issued Jan–May 2026)", fontsize=10.5, color="#444444")
    ax.set_title(
        "Top 20 postal FSAs by LTB application volume",
        fontsize=13.5, fontweight="bold", pad=14, loc="left",
    )

    ax.grid(axis="x", color="#e3e3e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(left=False, bottom=False, colors="#444444")

    for i, (total_val,) in enumerate(zip(top20["total_applications"])):
        ax.text(total_val + max(top20["total_applications"]) * 0.012, i, f"{total_val:,}",
                 va="center", ha="left", fontsize=9.5, color="#222222")

    ax.set_xlim(0, top20["total_applications"].max() * 1.12)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)

    fig.text(
        0.02, 0.01,
        "Raw counts, not normalized by population — a high-population area will naturally show more applications",
        fontsize=9.5, color="#777777", ha="left",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out_png = OUT_DIR / "top20_fsa_by_volume.png"
    fig.savefig(out_png, dpi=200, facecolor="white")
    print("\nSaved chart to", out_png)


if __name__ == "__main__":
    main()
