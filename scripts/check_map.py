# -*- coding: utf-8 -*-
"""
Drive the merged map in a real browser and assert it actually works.

A 5.7MB self-contained page with three interacting toggles is exactly the kind
of thing that looks fine in the source and is broken on load. This clicks
through every combination of geography, denominator and lens, and checks after
each that paths were drawn, that some of them are coloured rather than all
grey, that the ranked list filled in, and that no console error fired.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
MAP = BASE / "map.html"
SHOTS = BASE / "docs" / "checks"

GEOS = ["fsa", "csd"]
METRICS = ["per1k", "per10k", "raw"]
LENSES = ["total", "landlord", "tenant"]

STATE = """
() => {
  const paths = Array.from(document.querySelectorAll('#map-svg path'));
  const fills = paths.map(p => p.getAttribute('fill'));
  const grey = fills.filter(f => !f || f === 'rgb(224,228,234)' || /^#|no-data/.test(f) === false && f.indexOf('rgb') !== 0).length;
  return {
    paths: paths.length,
    coloured: fills.filter(f => f && f.indexOf('rgb(') === 0).length,
    distinct: new Set(fills).size,
    rankRows: document.querySelectorAll('#rank-list .rank-row').length,
    rankTitle: (document.getElementById('rank-title').textContent || '').trim(),
    legend: (document.getElementById('legend-title').textContent || '').trim(),
    legendMax: (document.getElementById('legend-grad-max').textContent || '').trim(),
    statTotal: (document.getElementById('stat-total').textContent || '').trim(),
    statRenters: (document.getElementById('stat-renters').textContent || '').trim(),
    viewBox: document.getElementById('map-svg').getAttribute('viewBox'),
  };
}
"""


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(MAP.as_uri())
        page.wait_for_timeout(1200)
        if errors:
            problems.append(f"console errors on load: {errors[:3]}")

        for geo in GEOS:
            page.click(f'#geo-toggle button[data-geo="{geo}"]')
            page.wait_for_timeout(500)
            for metric in METRICS:
                page.click(f'#metric-toggle button[data-metric="{metric}"]')
                page.wait_for_timeout(250)
                for lens in LENSES:
                    page.click(f'#lens-toggle button[data-lens="{lens}"]')
                    page.wait_for_timeout(150)
                    s = page.evaluate(STATE)
                    tag = f"{geo}/{metric}/{lens}"
                    if s["paths"] < 400:
                        problems.append(f"{tag}: only {s['paths']} paths drawn")
                    if s["coloured"] < 50:
                        problems.append(f"{tag}: only {s['coloured']} coloured areas")
                    if s["distinct"] < 20:
                        problems.append(f"{tag}: only {s['distinct']} distinct fills")
                    if s["rankRows"] != 10:
                        problems.append(f"{tag}: {s['rankRows']} rank rows, expected 10")
                    if not s["legendMax"]:
                        problems.append(f"{tag}: legend has no maximum")
                    print(f"  [{tag:22s}] paths={s['paths']:4d} coloured={s['coloured']:4d} "
                          f"shades={s['distinct']:4d} rank={s['rankRows']:2d}  {s['legend']}")
                if errors:
                    problems.append(f"{geo}/{metric}: console errors {errors[:2]}")
                    errors.clear()

        # Tooltip on hover, and the pin on click.
        page.click('#geo-toggle button[data-geo="fsa"]')
        page.wait_for_timeout(400)
        page.click('#metric-toggle button[data-metric="per1k"]')
        page.wait_for_timeout(200)
        box = page.evaluate("""() => {
          const p = document.querySelector('#map-svg path[fill^="rgb("]');
          if (!p) return null;
          const r = p.getBoundingClientRect();
          return {x: r.x + r.width/2, y: r.y + r.height/2};
        }""")
        if not box:
            problems.append("no coloured path found to hover")
        else:
            page.mouse.move(box["x"], box["y"])
            page.wait_for_timeout(250)
            visible = page.evaluate(
                "() => document.getElementById('tooltip').classList.contains('visible')")
            text = page.evaluate("() => document.getElementById('tooltip').textContent")
            if not visible:
                problems.append("tooltip did not appear on hover")
            elif "Renter households" not in text:
                problems.append(f"tooltip missing renter line: {text[:90]}")
            else:
                print(f"  tooltip OK: {text[:70]}")

        page.screenshot(path=str(SHOTS / "map-merged.png"), full_page=False)
        browser.close()

    print()
    if problems:
        for problem in dict.fromkeys(problems):
            print(f"  PROBLEM  {problem}")
        print(f"\n{len(problems)} problem(s)")
        return 1
    print("map: all geography x denominator x lens combinations render")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
