# -*- coding: utf-8 -*-
"""
Fetch Ontario municipality (Census Subdivision) boundary polygons from the
StatCan 2021 Cartographic Boundary Files ArcGIS REST service (layer 9 = CSD,
vs. layer 14 = FSA used in fetch_fsa_boundaries.py), same adaptive-pagination
approach since the server's payload limit is geometry-complexity-based, not
a fixed record count.
"""
import json
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "raw_csd_boundaries"
OUT_PATH = OUT_DIR / "ontario_csd.geojson"

SERVICE_URL = "https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/9/query"
PAGE_SIZE = 200
ONTARIO_PRUID = "35"


def _ring_is_exterior(ring):
    # Esri (like shapefiles) winds exterior rings clockwise and holes
    # counter-clockwise; a positive shoelace sum here means clockwise.
    total = sum((x2 - x1) * (y2 + y1) for (x1, y1), (x2, y2) in zip(ring, ring[1:]))
    return total >= 0


def esri_rings_to_geojson(rings):
    """
    Esri geometries don't nest holes inside their exterior ring the way
    GeoJSON Polygon coordinates do — a single Esri "polygon" can contain
    several genuinely disjoint parts (e.g. a municipality with river
    islands), distinguished only by ring winding order, not nesting. Dumping
    every ring into one GeoJSON Polygon (treating rings 2+ as holes of ring
    1) silently produces a degenerate near-empty shape whenever a feature
    has more than one true exterior ring — exactly what broke Windsor
    (20 rings, most of them separate small parts, not holes).
    Holes are assigned to the most recently started exterior ring, which is
    the standard Esri ring ordering guarantee.
    """
    parts = []
    for ring in rings:
        if _ring_is_exterior(ring) or not parts:
            parts.append([ring])
        else:
            parts[-1].append(ring)
    if len(parts) == 1:
        return {"type": "Polygon", "coordinates": parts[0]}
    return {"type": "MultiPolygon", "coordinates": parts}


def fetch_page(offset, page_size):
    params = {
        "where": f"PRUID='{ONTARIO_PRUID}'",
        "outFields": "CSDUID,CSDNAME,CSDTYPE,PRUID,LANDAREA",
        "outSR": "4326",
        "f": "json",
        "geometryPrecision": 5,
        "resultRecordCount": page_size,
        "resultOffset": offset,
    }
    resp = requests.get(SERVICE_URL, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_features = []
    offset = 0
    page_size = PAGE_SIZE

    while True:
        data = None
        attempt_size = page_size
        while attempt_size >= 1:
            data = fetch_page(offset, attempt_size)
            if "error" not in data:
                break
            print(f"  offset={offset} page_size={attempt_size} failed, halving...")
            attempt_size = attempt_size // 2
            time.sleep(0.3)
        if data is None or "error" in data:
            raise RuntimeError(f"Could not fetch offset={offset} even at page_size=1: {data}")
        page_size = min(PAGE_SIZE, attempt_size * 2) if attempt_size < page_size else page_size

        feats = data.get("features", [])
        print(f"offset={offset}: got {len(feats)} features, exceededTransferLimit={data.get('exceededTransferLimit')}")
        if not feats:
            break

        for f in feats:
            attrs = f["attributes"]
            geom = f.get("geometry")
            if not geom or "rings" not in geom:
                continue
            all_features.append({
                "type": "Feature",
                "properties": {
                    "csduid": attrs["CSDUID"],
                    "name": attrs["CSDNAME"],
                    "type": attrs["CSDTYPE"],
                    "pruid": attrs["PRUID"],
                    "landarea": attrs["LANDAREA"],
                },
                "geometry": esri_rings_to_geojson(geom["rings"]),
            })

        if not data.get("exceededTransferLimit"):
            break
        offset += len(feats)
        time.sleep(0.3)

    fc = {"type": "FeatureCollection", "features": all_features}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(fc, f)

    print(f"\nSaved {len(all_features)} CSD polygons to {OUT_PATH}")
    names = sorted(set(f["properties"]["name"] for f in all_features))
    print(f"Total municipalities: {len(names)}")
    print("Sample:", names[:10], "...")


if __name__ == "__main__":
    main()
