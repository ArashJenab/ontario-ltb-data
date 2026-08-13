# -*- coding: utf-8 -*-
"""
The "big picture" chart: cases filed vs. dollars awarded, landlord- vs.
tenant-side, side by side — plus the average-award-per-case comparison,
which is the sharper story (dollars are MORE lopsided than case volume).

Both halves use the same six tracked categories (L1+L2+L4 vs T1+T2+T6) so
the comparison is apples-to-apples: the volume donut is NOT "all landlord
filings" vs "all tenant filings" (that ratio is 5.7x, using every L/T code
in the dataset) — it's restricted to the same categories the dollar figures
come from, so the two donuts describe the same slice of the system.
"""
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
POP_JSON = BASE / "data" / "ltb_open_data_export.json"
PERSPECTIVE_TOTALS = BASE / "results" / "amounts_equal_sample_100_per_category" / "perspective_chart_totals.csv"
OUT_DIR = BASE / "results" / "landlord_vs_tenant_overview"
OUT_PNG = OUT_DIR / "overview_chart.png"
OUT_CSV = OUT_DIR / "overview_data.csv"

LANDLORD_CODES = ["L1", "L2", "L4"]
TENANT_CODES = ["T1", "T2", "T6"]

BLUE = "#2a78d6"
ORANGE = "#eb6834"


def load_field_name(fields, must_contain):
    for f in fields:
        if must_contain in f["id"]:
            return f["id"]
    raise KeyError(must_contain)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(POP_JSON, encoding="utf-8") as f:
        data = json.load(f)
    apps_field = load_field_name(data["fields"], "Applications/Requ")
    idx = {f["id"]: i for i, f in enumerate(data["fields"])}
    col = idx[apps_field]

    from collections import Counter
    counts = Counter(r[col] for r in data["records"])
    landlord_cases = sum(counts[c] for c in LANDLORD_CODES)
    tenant_cases = sum(counts[c] for c in TENANT_CODES)

    totals = {}
    with open(PERSPECTIVE_TOTALS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            totals[row["metric"]] = float(row["value"])
    landlord_dollars = totals["landlord_owed_total_L1_L2_L4"]
    tenant_dollars = totals["tenant_owed_total_T1_T2_T6"]

    landlord_avg = landlord_dollars / landlord_cases
    tenant_avg = tenant_dollars / tenant_cases

    rows = [
        {"side": "landlord", "categories": "L1+L2+L4", "cases_filed": landlord_cases,
         "estimated_dollars_awarded": round(landlord_dollars), "avg_dollars_per_case": round(landlord_avg)},
        {"side": "tenant", "categories": "T1+T2+T6", "cases_filed": tenant_cases,
         "estimated_dollars_awarded": round(tenant_dollars), "avg_dollars_per_case": round(tenant_avg)},
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    case_ratio = landlord_cases / tenant_cases
    dollar_ratio = landlord_dollars / tenant_dollars
    avg_ratio = landlord_avg / tenant_avg
    print(f"Cases filed: landlord {landlord_cases:,} vs tenant {tenant_cases:,}  ({case_ratio:.1f}x)")
    print(f"Dollars awarded: landlord ${landlord_dollars:,.0f} vs tenant ${tenant_dollars:,.0f}  ({dollar_ratio:.1f}x)")
    print(f"Avg $ per case: landlord ${landlord_avg:,.0f} vs tenant ${tenant_avg:,.0f}  ({avg_ratio:.1f}x)")
    print(f"Saved data to {OUT_CSV}")

    # ---- chart: two donuts + a synthesizing stat line ----
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 7.2))

    def donut(ax, landlord_val, tenant_val, title):
        vals = [landlord_val, tenant_val]
        colors = [BLUE, ORANGE]
        total = sum(vals)
        wedges, _ = ax.pie(
            vals, colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        )
        for w, v in zip(wedges, vals):
            ang = (w.theta1 + w.theta2) / 2
            import math
            x = 0.78 * math.cos(math.radians(ang))
            y = 0.78 * math.sin(math.radians(ang))
            pct = v / total * 100
            ax.text(x, y, f"{pct:.0f}%", ha="center", va="center",
                     fontsize=13, fontweight="bold", color="white")
        ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
        ax.set_aspect("equal")

    donut(axes[0], landlord_cases, tenant_cases,
          f"Cases filed\n(L1+L2+L4 vs T1+T2+T6)")
    donut(axes[1], landlord_dollars, tenant_dollars,
          f"Dollars awarded (estimated)")

    fig.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Landlord-side"),
            plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="Tenant-side"),
        ],
        loc="center", ncol=2, frameon=False, fontsize=11, bbox_to_anchor=(0.5, 0.205),
    )

    fig.suptitle("The big picture: volume vs. dollars, landlord- vs. tenant-side",
                  fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.98)

    stat_line = (
        f"{case_ratio:.1f}\u00d7 more cases filed landlord-side   \u2022   "
        f"{dollar_ratio:.1f}\u00d7 more dollars awarded landlord-side   \u2022   "
        f"{avg_ratio:.1f}\u00d7 higher average award per case"
    )
    fig.text(0.5, 0.145, stat_line, ha="center", fontsize=12, color="#1a2130", fontweight="bold")
    fig.text(0.5, 0.10,
              f"Landlord-side average: \\${landlord_avg:,.0f}/case   vs.   tenant-side average: \\${tenant_avg:,.0f}/case",
              ha="center", fontsize=10.5, color="#444444")
    fig.text(0.5, 0.06, "The dollar gap is larger than the volume gap: landlords don't just file more — they win more per case, too.",
              ha="center", fontsize=10, color="#666666", style="italic")
    fig.text(0.02, 0.012,
              "Volume: full population, tracked categories only. Dollars: order-of-magnitude estimate from a 100-doc/category sample.",
              fontsize=8.5, color="#888888", ha="left")

    fig.tight_layout(rect=(0, 0.25, 1, 0.94))
    fig.savefig(OUT_PNG, dpi=200, facecolor="white")
    print(f"\nSaved chart to {OUT_PNG}")


if __name__ == "__main__":
    main()
