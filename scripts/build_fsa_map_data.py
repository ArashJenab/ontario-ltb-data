# -*- coding: utf-8 -*-
"""
Build the data payload for the FSA choropleth map: project each FSA polygon
(lon/lat) to SVG path coordinates, join in the normalized application stats,
and write a single JSON file the HTML page inlines directly (self-contained,
no runtime fetch — required for the Artifact CSP).
"""
import csv
import json
import math
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent
GEOJSON_PATH = BASE / "data" / "ontario_fsa_simplified.geojson"
STATS_PATH = BASE / "data" / "fsa_applications_normalized.csv"
OUT_PATH = BASE / "data" / "fsa_map_payload.json"

TARGET_WIDTH = 900
# The default viewport crops to where the application-weighted MASS of centroids
# falls, not just "any FSA with data" — a bounding box of qualifying FSAs still
# includes the sparse north because a handful of northern city FSAs (Thunder
# Bay, Sudbury, etc.) each clear a low count threshold; weighted percentiles on
# centroid lat/lon correctly treat those as a small tail rather than anchoring
# the crop.
FOCUS_PERCENTILE_LOW = 0.02
FOCUS_PERCENTILE_HIGH = 0.98


def load_stats():
    stats = {}
    with open(STATS_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pop = row["population"]
            stats[row["fsa"]] = {
                "population": int(float(pop)) if pop else None,
                "total": int(row["total_applications"]),
                "landlord": int(row["landlord_filed"]),
                "tenant": int(row["tenant_filed"]),
                "total_per10k": float(row["total_applications_per_10k"]) if row["total_applications_per_10k"] else None,
                "landlord_per10k": float(row["landlord_filed_per_10k"]) if row["landlord_filed_per_10k"] else None,
                "tenant_per10k": float(row["tenant_filed_per_10k"]) if row["tenant_filed_per_10k"] else None,
            }
    return stats


def project_factory(lon_min, lon_max, lat_min, lat_max, target_width):
    mean_lat_rad = math.radians((lat_min + lat_max) / 2)
    cos_lat = math.cos(mean_lat_rad)
    x_span = (lon_max - lon_min) * cos_lat
    y_span = (lat_max - lat_min)
    scale = target_width / x_span
    target_height = y_span * scale

    def project(lon, lat):
        x = (lon - lon_min) * cos_lat * scale
        y = (lat_max - lat) * scale  # flip so north is up
        return round(x, 2), round(y, 2)

    return project, target_width, round(target_height, 2)


def weighted_percentile(values, weights, pct):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cum = np.cumsum(weights)
    cum /= cum[-1]
    return float(np.interp(pct, cum, values))


def ring_to_path(ring, project):
    pts = [project(lon, lat) for lon, lat in ring]
    d = f"M{pts[0][0]},{pts[0][1]} " + " ".join(f"L{x},{y}" for x, y in pts[1:]) + " Z"
    return d


def geometry_to_path(geom, project):
    if geom["type"] == "Polygon":
        rings = geom["coordinates"]
    else:  # MultiPolygon
        rings = [r for poly in geom["coordinates"] for r in poly]
    return " ".join(ring_to_path(ring, project) for ring in rings)


def main():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        fc = json.load(f)
    stats = load_stats()

    lons, lats = [], []
    for feat in fc["features"]:
        geom = feat["geometry"]
        rings = geom["coordinates"] if geom["type"] == "Polygon" else [r for poly in geom["coordinates"] for r in poly]
        for ring in rings:
            for lon, lat in ring:
                lons.append(lon)
                lats.append(lat)

    project, width, height = project_factory(min(lons), max(lons), min(lats), max(lats), TARGET_WIDTH)

    features_out = []
    matched, unmatched = 0, 0
    centroid_lons, centroid_lats, centroid_weights = [], [], []
    for feat in fc["features"]:
        fsa = feat["properties"]["fsa"]
        s = stats.get(fsa)
        if s:
            matched += 1
        else:
            unmatched += 1
        path_d = geometry_to_path(feat["geometry"], project)
        rings = feat["geometry"]["coordinates"] if feat["geometry"]["type"] == "Polygon" \
            else [r for poly in feat["geometry"]["coordinates"] for r in poly]

        if s and s["total"] > 0:
            ring_lons = [pt[0] for ring in rings for pt in ring]
            ring_lats = [pt[1] for ring in rings for pt in ring]
            centroid_lons.append((min(ring_lons) + max(ring_lons)) / 2)
            centroid_lats.append((min(ring_lats) + max(ring_lats)) / 2)
            centroid_weights.append(s["total"])

        features_out.append({
            "fsa": fsa,
            "d": path_d,
            **(s or {"population": None, "total": 0, "landlord": 0, "tenant": 0,
                      "total_per10k": None, "landlord_per10k": None, "tenant_per10k": None}),
        })

    lon_lo = weighted_percentile(centroid_lons, centroid_weights, FOCUS_PERCENTILE_LOW)
    lon_hi = weighted_percentile(centroid_lons, centroid_weights, FOCUS_PERCENTILE_HIGH)
    lat_lo = weighted_percentile(centroid_lats, centroid_weights, FOCUS_PERCENTILE_LOW)
    lat_hi = weighted_percentile(centroid_lats, centroid_weights, FOCUS_PERCENTILE_HIGH)

    # project the 4 corners of the lon/lat percentile box to get its SVG-space bbox
    corners = [project(lo, la) for lo in (lon_lo, lon_hi) for la in (lat_lo, lat_hi)]
    fx0, fx1 = min(c[0] for c in corners), max(c[0] for c in corners)
    fy0, fy1 = min(c[1] for c in corners), max(c[1] for c in corners)

    pad_frac = 0.08
    fw, fh = fx1 - fx0, fy1 - fy0
    focus_view = {
        "x": round(fx0 - fw * pad_frac, 1),
        "y": round(fy0 - fh * pad_frac, 1),
        "width": round(fw * (1 + 2 * pad_frac), 1),
        "height": round(fh * (1 + 2 * pad_frac), 1),
    }

    payload = {
        "width": width,
        "height": height,
        "focusView": focus_view,
        "features": features_out,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"Projected {len(features_out)} FSA polygons into a {width}x{height} viewBox")
    print(f"Matched to application stats: {matched}, unmatched (grey, no data): {unmatched}")
    print(f"Default focus viewport ({FOCUS_PERCENTILE_LOW*100:.0f}-{FOCUS_PERCENTILE_HIGH*100:.0f}th percentile of application-weighted centroids): {focus_view}")
    print(f"  (full extent is 0,0,{width},{height} for comparison)")
    print(f"Saved payload to {OUT_PATH} ({OUT_PATH.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
