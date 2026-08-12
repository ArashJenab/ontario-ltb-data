# -*- coding: utf-8 -*-
"""Top 10 LTB application types by order count -> horizontal bar chart."""
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "results" / "application_volume"
DATA_PATH = BASE / "data" / "ltb_open_data_export.json"
OUT_PNG = OUT_DIR / "top_categories_by_count.png"
OUT_CSV = OUT_DIR / "top_categories_by_count.csv"

APPLICATIONS_FIELD = "Applications/Requêtes"

CODES = ["L1", "L2", "L4", "T2", "T6", "T1", "L10", "L3", "T5", "L5"]

FULL_NAMES = {
    "L1": "non-payment of rent",
    "L2": "end tenancy / evict, other reasons",
    "L4": "evict — breached settlement/order",
    "T2": "tenant rights",
    "T6": "maintenance",
    "T1": "rent rebate",
    "L10": "collect money from former tenant",
    "L3": "tenant gave notice to terminate",
    "T5": "landlord's bad faith notice to terminate",
    "L5": "above-guideline rent increase",
}

BLUE = "#2a78d6"   # landlord (L-prefixed)
ORANGE = "#eb6834"  # tenant (T-prefixed)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    idx = {f["id"]: i for i, f in enumerate(data["fields"])}
    col = idx[APPLICATIONS_FIELD]

    counts = Counter()
    for r in data["records"]:
        code = r[col]
        if code in CODES:
            counts[code] += 1

    # sort by count descending
    ordered = sorted(CODES, key=lambda c: counts.get(c, 0), reverse=True)
    values = [counts.get(c, 0) for c in ordered]
    colors = [BLUE if c.startswith("L") else ORANGE for c in ordered]
    labels = [f"{c} — {FULL_NAMES[c]}" for c in ordered]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    y_pos = range(len(ordered))
    bars = ax.barh(y_pos, values, color=colors, height=0.65, zorder=3)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=10.5)
    ax.invert_yaxis()  # highest count on top

    ax.set_xlabel("Order count", fontsize=10.5, color="#444444")
    ax.set_title(
        "Top 10 LTB application types by order count",
        fontsize=14, fontweight="bold", pad=14, loc="left",
    )

    # recessive gridlines behind bars
    ax.grid(axis="x", color="#e3e3e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(left=False, bottom=False, colors="#444444")

    # direct value labels at bar ends
    max_val = max(values)
    for bar, val in zip(bars, values):
        ax.text(
            val + max_val * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}",
            va="center", ha="left", fontsize=9.5, color="#222222",
        )

    ax.set_xlim(0, max_val * 1.12)

    # legend for who files: landlord vs tenant
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Landlord-filed (L-codes)"),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="Tenant-filed (T-codes)"),
    ]
    ax.legend(
        handles=legend_handles, loc="lower right", frameon=False, fontsize=9.5,
    )

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=200, facecolor="white")
    print("Saved chart to", OUT_PNG)

    out_df = pd.DataFrame({
        "code": ordered,
        "full_name": [FULL_NAMES[c] for c in ordered],
        "filed_by": ["landlord" if c.startswith("L") else "tenant" for c in ordered],
        "order_count": values,
    })
    out_df.to_csv(OUT_CSV, index=False)
    print("Saved data to", OUT_CSV)
    print("\nCounts:")
    for c, v in zip(ordered, values):
        print(f"  {c}: {v:,}")


if __name__ == "__main__":
    main()
