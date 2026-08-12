# -*- coding: utf-8 -*-
"""
Simplify the raw Ontario FSA cartographic boundaries (98MB of full-detail
shoreline-following polygons) down to something a browser can render as
inline SVG for a choropleth map. Also drop coordinate precision to 4
decimals (~11m) after simplification.
"""
import json
from pathlib import Path

from shapely.geometry import shape, mapping

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "raw_fsa_boundaries" / "ontario_fsa.geojson"
OUT_PATH = BASE / "data" / "ontario_fsa_simplified.geojson"

TOLERANCE_DEGREES = 0.004  # ~350-450m at Ontario's latitude — fine for a small-multiple choropleth


def round_coords(geom_dict, ndigits=4):
    def _round(coords):
        if isinstance(coords[0], (int, float)):
            return [round(c, ndigits) for c in coords]
        return [_round(c) for c in coords]
    geom_dict["coordinates"] = _round(geom_dict["coordinates"])
    return geom_dict


def main():
    with open(IN_PATH, encoding="utf-8") as f:
        fc = json.load(f)

    out_features = []
    for feat in fc["features"]:
        geom = shape(feat["geometry"])
        simplified = geom.simplify(TOLERANCE_DEGREES, preserve_topology=True)
        if simplified.is_empty:
            simplified = geom  # fall back to original rather than dropping the FSA
        geom_dict = round_coords(mapping(simplified))
        out_features.append({
            "type": "Feature",
            "properties": feat["properties"],
            "geometry": geom_dict,
        })

    out_fc = {"type": "FeatureCollection", "features": out_features}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out_fc, f, separators=(",", ":"))

    print(f"Simplified {len(out_features)} features")
    print(f"Saved to {OUT_PATH}")
    print(f"Output size: {OUT_PATH.stat().st_size / 1e6:.2f} MB (input was {IN_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
