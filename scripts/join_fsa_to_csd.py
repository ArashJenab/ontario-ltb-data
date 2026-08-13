# -*- coding: utf-8 -*-
"""
Roll the FSA-level LTB application counts up to the municipality (Census
Subdivision) level using area-weighted overlap: for each FSA polygon, find
every municipality polygon it intersects and split that FSA's application
counts proportionally by the fraction of the FSA's area inside each one.

Why not simpler centroid-in-polygon assignment: it works fine in cities
(many small FSAs, each cleanly inside one municipality) but breaks badly in
rural areas, where a single large FSA can span many small townships — a
centroid-based method dumps the FSA's entire count onto whichever township
happens to be nearest the centroid, wildly inflating that one township's
rate. Area-weighted overlap degrades gracefully in both cases: it reduces
to ~100% weight on one municipality for urban FSAs, and splits proportionally
across several for large rural ones.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

from shapely.geometry import shape
from shapely.strtree import STRtree

BASE = Path(__file__).resolve().parent.parent
FSA_GEOJSON = BASE / "data" / "ontario_fsa_simplified.geojson"
CSD_GEOJSON = BASE / "data" / "ontario_csd_simplified.geojson"
FSA_COUNTS = BASE / "results" / "applications_by_area" / "fsa_application_counts.csv"
CSD_POP = BASE / "data" / "csd_population.csv"
OUT_PATH = BASE / "data" / "csd_applications_normalized.csv"

COUNT_FIELDS = ["total_applications", "landlord_filed", "tenant_filed", "coop_filed"]


def load_fsa_polygons():
    with open(FSA_GEOJSON, encoding="utf-8") as f:
        fc = json.load(f)
    return {feat["properties"]["fsa"]: shape(feat["geometry"]) for feat in fc["features"]}


def load_csd_polygons():
    with open(CSD_GEOJSON, encoding="utf-8") as f:
        fc = json.load(f)
    polys, meta = [], {}
    for feat in fc["features"]:
        geom = shape(feat["geometry"]).buffer(0)  # buffer(0) repairs minor self-intersections from simplification
        polys.append(geom)
        meta[id(geom)] = (feat["properties"]["csduid"], feat["properties"]["name"])
    return polys, meta


def area_weighted_overlaps(fsa_polys, csd_polys, csd_meta):
    """For each FSA, return [(csduid, name, weight), ...] with weights summing to ~1.0."""
    tree = STRtree(csd_polys)
    result = {}
    unmatched = []
    for fsa, fsa_geom in fsa_polys.items():
        fsa_geom = fsa_geom.buffer(0)
        fsa_area = fsa_geom.area
        if fsa_area == 0:
            continue
        candidate_idx = tree.query(fsa_geom, predicate="intersects")
        overlaps = []
        for idx in candidate_idx:
            csd_geom = csd_polys[idx]
            inter_area = fsa_geom.intersection(csd_geom).area
            if inter_area > 0:
                csduid, name = csd_meta[id(csd_geom)]
                overlaps.append((csduid, name, inter_area / fsa_area))

        covered = sum(w for _, _, w in overlaps)
        if not overlaps or covered < 0.5:
            # little/no true overlap found (simplification gaps at edges) —
            # fall back to nearest municipality for the uncovered remainder
            nearest_idx = tree.nearest(fsa_geom.centroid)
            csd_geom = csd_polys[nearest_idx]
            csduid, name = csd_meta[id(csd_geom)]
            if not overlaps:
                overlaps = [(csduid, name, 1.0)]
                unmatched.append(fsa)
            else:
                # top up the missing weight onto the nearest municipality
                overlaps.append((csduid, name, 1.0 - covered))
                unmatched.append(fsa)

        result[fsa] = overlaps
    return result, unmatched


def main():
    fsa_polys = load_fsa_polygons()
    csd_polys, csd_meta = load_csd_polygons()
    overlaps, unmatched = area_weighted_overlaps(fsa_polys, csd_polys, csd_meta)
    print(f"FSAs processed: {len(overlaps)}")
    print(f"FSAs needing a nearest-polygon top-up (partial or no direct overlap): {len(unmatched)}")

    fsa_rows = {}
    with open(FSA_COUNTS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fsa_rows[row["fsa"]] = row

    csd_totals = defaultdict(lambda: {"name": None, "fsa_count": 0.0,
                                       **{k: 0.0 for k in COUNT_FIELDS}})
    for fsa, row in fsa_rows.items():
        if fsa not in overlaps:
            continue
        for csduid, name, weight in overlaps[fsa]:
            t = csd_totals[csduid]
            t["name"] = name
            t["fsa_count"] += weight
            for k in COUNT_FIELDS:
                t[k] += int(row[k]) * weight

    pop = {}
    with open(CSD_POP, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pop[row["csduid"]] = int(row["population"])

    rows = []
    for csduid, t in csd_totals.items():
        population = pop.get(csduid)
        row = {"csduid": csduid, "name": t["name"], "fsa_count": round(t["fsa_count"], 2),
               "population": population}
        for k in COUNT_FIELDS:
            row[k] = round(t[k], 1)
        if population:
            for k in COUNT_FIELDS:
                if k == "coop_filed":
                    continue
                row[f"{k}_per_10k"] = round(t[k] / population * 10000, 2)
        else:
            for k in COUNT_FIELDS:
                if k == "coop_filed":
                    continue
                row[f"{k}_per_10k"] = None
        rows.append(row)

    rows.sort(key=lambda r: -(r["total_applications_per_10k"] or 0))

    fieldnames = ["csduid", "name", "fsa_count", "population", "total_applications", "landlord_filed",
                  "tenant_filed", "coop_filed", "total_applications_per_10k", "landlord_filed_per_10k",
                  "tenant_filed_per_10k"]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    no_pop = [r["name"] for r in rows if r["population"] is None]
    print(f"\nMunicipalities with application data: {len(rows)}")
    print(f"No population match: {len(no_pop)} {no_pop[:10]}")
    print(f"Saved to {OUT_PATH}")

    reliable = [r for r in rows if r["population"] and r["population"] >= 10000]
    print("\nTop 15 by total applications per 10,000 residents (population >= 10,000):")
    for r in reliable[:15]:
        print(f"  {r['name']:30s} pop={r['population']:>9,}  total={r['total_applications']:>7.1f}  "
              f"rate={r['total_applications_per_10k']:>6.1f}/10k  fsas={r['fsa_count']:.1f}")


if __name__ == "__main__":
    main()
