# -*- coding: utf-8 -*-
"""
Fetch Ontario FSA boundary polygons from the StatCan 2021 Cartographic
Boundary Files ArcGIS REST service, paginating (server caps ~200-400
features per request), and save as a single GeoJSON FeatureCollection.
"""
import json
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "raw_fsa_boundaries"
OUT_PATH = OUT_DIR / "ontario_fsa.geojson"

SERVICE_URL = "https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/14/query"
PAGE_SIZE = 200
ONTARIO_PRUID = "35"


def esri_rings_to_geojson_polygon(rings):
    # Esri polygons and GeoJSON polygons both use [ring, ring, ...] with
    # outer ring + holes; Esri doesn't distinguish outer/inner by nesting
    # the way GeoJSON MultiPolygon does, so a single Polygon with multiple
    # rings is a reasonable direct mapping for cartographic boundaries.
    return {"type": "Polygon", "coordinates": rings}


def fetch_page(offset, page_size):
    params = {
        "where": f"PRUID='{ONTARIO_PRUID}'",
        "outFields": "CFSAUID,PRUID,PRNAME,LANDAREA",
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
        # The server's payload-size limit depends on geometry complexity, not
        # just record count — some FSAs (large rural/coastal ones) blow past
        # it well under PAGE_SIZE. Halve and retry on error, then ease back
        # up to the standard page size once we're past the dense patch.
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
                    "fsa": attrs["CFSAUID"],
                    "pruid": attrs["PRUID"],
                    "prname": attrs["PRNAME"],
                    "landarea": attrs["LANDAREA"],
                },
                "geometry": esri_rings_to_geojson_polygon(geom["rings"]),
            })

        if not data.get("exceededTransferLimit"):
            break
        offset += len(feats)
        time.sleep(0.3)

    fc = {"type": "FeatureCollection", "features": all_features}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(fc, f)

    print(f"\nSaved {len(all_features)} FSA polygons to {OUT_PATH}")
    fsas = sorted(set(f["properties"]["fsa"] for f in all_features))
    print("Sample FSAs:", fsas[:10], "...")


if __name__ == "__main__":
    main()
