# -*- coding: utf-8 -*-
"""
Extrapolate the amount-extraction sample to population-level dollar totals,
to put "landlord owed $200M" claims in perspective against what tenants are
awarded in the same system.

Method: estimated_total(category) = population_count * found_rate * mean_amount
This is a back-of-envelope scale-up of a SAMPLE, not a census — treat as
order-of-magnitude, not a precise figure. Larger --n narrows the error.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "ltb_open_data_export.json"

APPLICATIONS_FIELD_PREFIX = "Applications/Requ"

CATEGORIES = ["L1", "L2", "L4", "T2", "T6", "T1"]
FULL_NAMES = {
    "L1": "non-payment of rent",
    "L2": "end tenancy / evict, other reasons",
    "L4": "evict — breached settlement/order",
    "T2": "tenant rights",
    "T6": "maintenance",
    "T1": "rent rebate",
}

BLUE = "#2a78d6"    # landlord-owed
ORANGE = "#eb6834"  # tenant-owed


def load_field_name(fields, must_contain):
    for f in fields:
        if must_contain in f["id"]:
            return f["id"]
    raise KeyError(must_contain)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10, help="sample size used upstream (per-category for equal, total budget for proportional)")
    p.add_argument("--allocation", choices=["equal", "proportional"], default="equal")
    p.add_argument("--outdir", required=True, help="results subfolder name (must match the folder extract_amounts.py wrote to)")
    return p.parse_args()


def main():
    args = parse_args()
    n_per_category = args.n
    results_dir = BASE / "results" / args.outdir
    summary_path = results_dir / "extraction_summary.csv"
    out_png = results_dir / "landlord_vs_tenant_perspective.png"
    out_data_csv = results_dir / "perspective_chart_data.csv"

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    applications_field = load_field_name(data["fields"], APPLICATIONS_FIELD_PREFIX)
    idx = {f["id"]: i for i, f in enumerate(data["fields"])}
    col = idx[applications_field]

    pop_counts = Counter()
    for r in data["records"]:
        code = r[col]
        if code in CATEGORIES:
            pop_counts[code] += 1

    summary = pd.read_csv(summary_path).set_index("category")

    rows = []
    for cat in CATEGORIES:
        s = summary.loc[cat]
        pop = pop_counts[cat]
        est_total = pop * s["found_rate"] * s["mean"]
        rows.append({
            "category": cat,
            "population": pop,
            "sample_n": s["count_total"],
            "found_rate": s["found_rate"],
            "sample_mean": s["mean"],
            "estimated_total": est_total,
        })
    df = pd.DataFrame(rows).sort_values("estimated_total", ascending=False)

    landlord_total = df[df["category"].isin(["L1", "L2", "L4"])]["estimated_total"].sum()
    tenant_total = df[df["category"].isin(["T1", "T2", "T6"])]["estimated_total"].sum()

    # This is the exact table the chart bars are computed from — save it so
    # the PNG can always be traced back to the numbers that built it.
    df.to_csv(out_data_csv, index=False)
    totals_df = pd.DataFrame([
        {"metric": "landlord_owed_total_L1_L2_L4", "value": landlord_total},
        {"metric": "tenant_owed_total_T1_T2_T6", "value": tenant_total},
        {"metric": "ratio_landlord_to_tenant", "value": landlord_total / tenant_total},
    ])
    totals_df.to_csv(results_dir / "perspective_chart_totals.csv", index=False)

    print(df.to_string(index=False))
    print(f"\nEstimated landlord-owed total (L1+L2+L4): ${landlord_total:,.0f}")
    print(f"Estimated tenant-owed total (T1+T2+T6):   ${tenant_total:,.0f}")
    print(f"Ratio: {landlord_total / tenant_total:.1f}x")
    print(f"Saved calculation table to {out_data_csv}")
    print(f"Saved totals to {results_dir / 'perspective_chart_totals.csv'}")

    labels = [f"{c} — {FULL_NAMES[c]}" for c in df["category"]]
    colors = [BLUE if c.startswith("L") else ORANGE for c in df["category"]]
    values = df["estimated_total"].values

    fig, ax = plt.subplots(figsize=(12.5, 6.8))
    y_pos = range(len(df))
    bars = ax.barh(y_pos, values, color=colors, height=0.65, zorder=3)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=10.5)
    ax.invert_yaxis()

    ax.set_xlabel("Estimated total dollar amount ordered, province-wide (\\$)", fontsize=10.5, color="#444444")
    if args.allocation == "proportional":
        title_suffix = f"proportional sample, n={n_per_category} total"
    else:
        title_suffix = f"n={n_per_category}/category"
    ax.set_title(
        f"Estimated dollars ordered: landlord- vs tenant-side ({title_suffix})",
        fontsize=13.5, fontweight="bold", pad=14, loc="left",
    )

    ax.grid(axis="x", color="#e3e3e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(left=False, bottom=False, colors="#444444")

    max_val = max(values)
    for bar, val in zip(bars, values):
        ax.text(
            val + max_val * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"\\${val/1e6:,.1f}M" if val >= 1e6 else f"\\${val:,.0f}",
            va="center", ha="left", fontsize=9.5, color="#222222",
        )

    ax.set_xlim(0, max_val * 1.15)

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Landlord-owed (L-codes)"),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="Tenant-owed (T-codes)"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", frameon=False, fontsize=9.5)

    footnote = (
        f"Order-of-magnitude estimate (not a precise figure)   •   "
        f"Landlord-owed total (L1+L2+L4): \\${landlord_total/1e6:,.1f}M   •   "
        f"Tenant-owed total (T1+T2+T6): \\${tenant_total/1e6:,.1f}M   •   "
        f"Ratio \u2248 {landlord_total/tenant_total:,.0f}x"
    )
    fig.text(0.02, 0.01, footnote, fontsize=9.5, color="#333333", ha="left")

    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(out_png, dpi=200, facecolor="white")
    print("\nSaved chart to", out_png)


if __name__ == "__main__":
    main()
