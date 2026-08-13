# -*- coding: utf-8 -*-
"""Simplify the raw Ontario municipality boundaries for inline-SVG use — same
approach as simplify_fsa_boundaries.py."""
import json
from pathlib import Path

from shapely.geometry import shape, mapping

BASE = Path(__file__).resolve().parent.parent
IN_PATH = BASE / "data" / "raw_csd_boundaries" / "ontario_csd.geojson"
OUT_PATH = BASE / "data" / "ontario_csd_simplified.geojson"

TOLERANCE_DEGREES = 0.004


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
            simplified = geom
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
