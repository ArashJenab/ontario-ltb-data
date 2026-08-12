# -*- coding: utf-8 -*-
"""
Join LTB application counts by FSA against 2021 Census population by FSA
(Statistics Canada table 98-10-0019-01), and compute applications per
10,000 residents — the per-capita view that raw counts alone can't give.

Writes the normalized table to BOTH data/ (the join pipeline's home) and
results/applications_by_area/ (the "applications by area" deliverable
folder, so it's a complete, self-contained answer rather than split across
two places), plus a top-20-by-rate chart alongside the folder's existing
top-20-by-raw-volume chart.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE / "results" / "applications_by_area"
APPS_PATH = RESULTS_DIR / "fsa_application_counts.csv"
POP_PATH = BASE / "data" / "fsa_population.csv"
OUT_PATH = BASE / "data" / "fsa_applications_normalized.csv"
RESULTS_OUT_PATH = RESULTS_DIR / "fsa_applications_normalized.csv"
CHART_OUT_PATH = RESULTS_DIR / "top20_fsa_by_rate_per_10k.png"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
RELIABLE_POP_FLOOR = 1000  # below this, a handful of cases swings the rate wildly


def main():
    apps = pd.read_csv(APPS_PATH)
    pop = pd.read_csv(POP_PATH)

    merged = apps.merge(pop, on="fsa", how="left")

    unmatched = merged[merged["population"].isna()]
    print(f"FSAs in application data: {len(apps)}")
    print(f"FSAs with no population match: {len(unmatched)}")
    if len(unmatched):
        print(unmatched[["fsa", "total_applications"]].sort_values("total_applications", ascending=False).head(15).to_string(index=False))

    for col in ["total_applications", "landlord_filed", "tenant_filed"]:
        merged[f"{col}_per_10k"] = (merged[col] / merged["population"] * 10000).round(2)

    merged = merged.sort_values("total_applications_per_10k", ascending=False)
    merged.to_csv(OUT_PATH, index=False)
    merged.to_csv(RESULTS_OUT_PATH, index=False)
    print(f"\nSaved {len(merged)} rows to {OUT_PATH}")
    print(f"Saved a copy to {RESULTS_OUT_PATH}")

    reliable = merged[merged["population"] >= RELIABLE_POP_FLOOR]
    print(f"\nTop 15 FSAs by total applications per 10,000 residents (population >= {RELIABLE_POP_FLOOR:,}):")
    print(reliable[["fsa", "population", "total_applications", "total_applications_per_10k",
                     "landlord_filed_per_10k", "tenant_filed_per_10k"]].head(15).to_string(index=False))

    # --- chart: top 20 FSAs by total applications per 10,000 residents ---
    top20 = reliable.head(20).sort_values("total_applications_per_10k", ascending=True)

    fig, ax = plt.subplots(figsize=(11.5, 8.5))
    y_pos = range(len(top20))
    ax.barh(y_pos, top20["landlord_filed_per_10k"], color=BLUE, height=0.65, zorder=3, label="Landlord-filed")
    ax.barh(y_pos, top20["tenant_filed_per_10k"], left=top20["landlord_filed_per_10k"],
            color=ORANGE, height=0.65, zorder=3, label="Tenant-filed")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(top20["fsa"], fontsize=10.5)
    ax.set_xlabel("LTB applications per 10,000 residents (2021 Census population)", fontsize=10.5, color="#444444")
    ax.set_title(
        f"Top 20 postal FSAs by LTB applications per capita (population ≥ {RELIABLE_POP_FLOOR:,})",
        fontsize=13.5, fontweight="bold", pad=14, loc="left",
    )

    ax.grid(axis="x", color="#e3e3e3", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(left=False, bottom=False, colors="#444444")

    max_val = top20["total_applications_per_10k"].max()
    for i, val in enumerate(top20["total_applications_per_10k"]):
        ax.text(val + max_val * 0.012, i, f"{val:.1f}", va="center", ha="left", fontsize=9.5, color="#222222")

    ax.set_xlim(0, max_val * 1.12)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)

    fig.text(
        0.02, 0.01,
        f"Normalized by 2021 Census population — FSAs with population < {RELIABLE_POP_FLOOR:,} excluded (rate too noisy at that size)",
        fontsize=9.5, color="#777777", ha="left",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(CHART_OUT_PATH, dpi=200, facecolor="white")
    print(f"\nSaved chart to {CHART_OUT_PATH}")


if __name__ == "__main__":
    main()
