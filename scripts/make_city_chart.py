# -*- coding: utf-8 -*-
"""Top 15 municipalities by LTB applications per 10,000 residents — the
city-level counterpart to results/applications_by_area's FSA-level chart."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
IN_CSV = BASE / "data" / "csd_applications_normalized.csv"
OUT_DIR = BASE / "results" / "applications_by_city"
OUT_CSV = OUT_DIR / "csd_applications_normalized.csv"
OUT_PNG = OUT_DIR / "top15_cities_by_rate_per_10k.png"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
POP_FLOOR = 10000


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(IN_CSV)
    df.to_csv(OUT_CSV, index=False)

    reliable = df[df["population"] >= POP_FLOOR].sort_values("total_applications_per_10k", ascending=False)
    top15 = reliable.head(15).sort_values("total_applications_per_10k", ascending=True)

    fig, ax = plt.subplots(figsize=(11.5, 7.5))
    y_pos = range(len(top15))
    ax.barh(y_pos, top15["landlord_filed_per_10k"], color=BLUE, height=0.65, zorder=3, label="Landlord-filed")
    ax.barh(y_pos, top15["tenant_filed_per_10k"], left=top15["landlord_filed_per_10k"],
            color=ORANGE, height=0.65, zorder=3, label="Tenant-filed")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(top15["name"], fontsize=10.5)
    ax.set_xlabel("LTB applications per 10,000 residents (2021 Census population)", fontsize=10.5, color="#444444")
    ax.set_title(
        f"Top 15 Ontario municipalities by LTB applications per capita (population ≥ {POP_FLOOR:,})",
        fontsize=13.5, fontweight="bold", pad=14, loc="left",
    )

    ax.grid(axis="x", color="#e3e3e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(left=False, bottom=False, colors="#444444")

    max_val = top15["total_applications_per_10k"].max()
    for i, val in enumerate(top15["total_applications_per_10k"]):
        ax.text(val + max_val * 0.012, i, f"{val:.1f}", va="center", ha="left", fontsize=9.5, color="#222222")

    ax.set_xlim(0, max_val * 1.12)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)

    fig.text(
        0.02, 0.01,
        f"Rolled up from FSA-level data by area-weighted overlap; municipalities with population < {POP_FLOOR:,} excluded (rate too noisy at that size)",
        fontsize=9.5, color="#777777", ha="left",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT_PNG, dpi=200, facecolor="white")
    print(f"Saved chart to {OUT_PNG}")
    print(f"Saved data to {OUT_CSV}")


if __name__ == "__main__":
    main()
