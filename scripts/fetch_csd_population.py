# -*- coding: utf-8 -*-
"""
Extract Ontario municipality (Census Subdivision) population from the
already-downloaded StatCan table 98-10-0002-01, which covers all of Canada
at multiple geographic levels in one file (country/province/division/
subdivision) mixed together — filtered here to CSD-level, Ontario only.
"""
import re
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "raw_statcan_98100002" / "98100002.csv"
OUT_PATH = BASE / "data" / "csd_population.csv"

POP_COL = "Population and dwelling counts (13): Population, 2021 [1]"


def main():
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig")

    # DGUID format for a CSD-level row: <year><type>A0005<7-digit CSDUID>
    # e.g. "2021A00053520005" -> csduid "3520005" (Toronto). Ontario CSDUIDs
    # start with the 2-digit province code "35".
    is_csd = df["DGUID"].astype(str).str.contains("A0005", na=False)
    csd = df[is_csd].copy()
    csd["csduid"] = csd["DGUID"].astype(str).str[-7:]
    csd = csd[csd["csduid"].str.startswith("35")]

    out = csd[["csduid", "GEO", POP_COL]].rename(columns={"GEO": "name", POP_COL: "population"})
    out["population"] = pd.to_numeric(out["population"], errors="coerce")
    out = out.dropna(subset=["population"])
    out["population"] = out["population"].astype(int)
    out = out.sort_values("population", ascending=False).reset_index(drop=True)

    out.to_csv(OUT_PATH, index=False)
    print(f"Ontario CSDs: {len(out)}")
    print(out.head(15).to_string(index=False))
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
