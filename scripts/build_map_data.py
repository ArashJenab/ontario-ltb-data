# -*- coding: utf-8 -*-
"""
Merge the postal-area and municipality payloads into one, and add the
renter-household denominator to both.

Two separate maps of the same data was one map too many: a reader had to leave
the page and load a second 2.8MB document to answer "which city is that?".
This produces a single payload with both geographies, which the merged map
swaps between in place.

The two existing payloads are already co-registered: both are projected to the
same 900-unit width and the same latitude span, so their path data can be
dropped into one SVG viewBox unchanged. That is why this merges the built
payloads rather than reprojecting from the boundary files.

It also normalises the feature schema, because the two levels disagreed about
what a feature is called (`fsa` against `csduid` plus `name`). Every feature
here has `id` and `label`, so the map's rendering code has one path rather than
a branch per geography.

Denominators, both carried per feature:
  * population, kept for continuity with the earlier maps
  * renter households, which is the defensible one. An area that is 80%
    renters will show more rental disputes per resident than one that is 20%
    renters without anything else differing, so a per-resident rate mostly
    measures tenure mix.
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FSA_PAYLOAD = BASE / "data" / "fsa_map_payload.json"
CSD_PAYLOAD = BASE / "data" / "csd_map_payload.json"
FSA_CENSUS = BASE / "data" / "fsa_census_profile.csv"
CSD_STATS = BASE / "data" / "csd_applications_normalized.csv"
OUT_PATH = BASE / "data" / "map_payload.json"

# Below this many renter households a per-1,000 rate swings wildly on a single
# case, so the area is drawn grey rather than given a colour it cannot support.
RENTER_FLOOR = 200
POP_FLOOR = 1000


def rate(numerator, denominator, per):
    if not denominator or denominator <= 0:
        return None
    return round(numerator / denominator * per, 2)


def load_fsa_renters():
    renters = {}
    with open(FSA_CENSUS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            value = row.get("households_renter")
            if value:
                renters[row["fsa"]] = int(float(value))
    return renters


def load_csd_renters():
    renters = {}
    with open(CSD_STATS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            value = row.get("households_renter")
            if value:
                renters[row["csduid"]] = int(float(value))
    return renters


def normalise(feature, level, renters_by_id):
    if level == "fsa":
        key = feature["fsa"]
        identifier, label, sublabel = key, key, "Postal area"
    else:
        key = feature["csduid"]
        identifier, label, sublabel = key, feature["name"], "Municipality"

    renters = renters_by_id.get(key)
    population = feature.get("population")
    counts = {k: feature.get(k) or 0 for k in ("total", "landlord", "tenant")}

    out = {
        "id": identifier,
        "label": label,
        "sublabel": sublabel,
        "d": feature["d"],
        "population": population,
        "renters": renters,
    }
    out.update(counts)
    for k, value in counts.items():
        out[f"{k}_per10k"] = rate(value, population, 10000)
        out[f"{k}_per1k"] = rate(value, renters, 1000)
    return out


def main():
    with open(FSA_PAYLOAD, encoding="utf-8") as fh:
        fsa = json.load(fh)
    with open(CSD_PAYLOAD, encoding="utf-8") as fh:
        csd = json.load(fh)

    if abs(fsa["width"] - csd["width"]) > 1 or abs(fsa["height"] - csd["height"]) > 2:
        raise SystemExit(
            "The two payloads are not co-registered "
            f"({fsa['width']}x{fsa['height']} against {csd['width']}x{csd['height']}); "
            "rebuild both before merging, or the layers will not line up."
        )

    fsa_renters = load_fsa_renters()
    csd_renters = load_csd_renters()

    payload = {
        "width": fsa["width"],
        "height": max(fsa["height"], csd["height"]),
        "renterFloor": RENTER_FLOOR,
        "popFloor": POP_FLOOR,
        "layers": {
            "fsa": {
                "name": "Postal area",
                "plural": "postal areas",
                "focusView": fsa["focusView"],
                "features": [normalise(f, "fsa", fsa_renters) for f in fsa["features"]],
            },
            "csd": {
                "name": "Municipality",
                "plural": "municipalities",
                "focusView": csd["focusView"],
                "features": [normalise(f, "csd", csd_renters) for f in csd["features"]],
            },
        },
    }

    OUT_PATH.write_text(
        json.dumps(payload, separators=(",", ":")), encoding="utf-8"
    )

    for key, layer in payload["layers"].items():
        features = layer["features"]
        with_renters = sum(1 for f in features if f["renters"])
        usable = sum(1 for f in features if (f["renters"] or 0) >= RENTER_FLOOR)
        total_renters = sum(f["renters"] or 0 for f in features)
        print(
            f"{key}: {len(features)} features, {with_renters} with a renter count, "
            f"{usable} above the {RENTER_FLOOR}-household floor, "
            f"{total_renters:,} renter households total"
        )
    print(f"\nSaved to {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
