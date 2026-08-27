# -*- coding: utf-8 -*-
"""
Render the built pages and check what a validator cannot: layout.

Colour is checked by the palette validator; this catches the rest, which is
where charts actually break. For each page, in light and dark, at desktop and
phone width, it reports:

  * horizontal overflow of the document (the page must never scroll sideways)
  * any SVG text whose box falls outside its chart's viewBox (a clipped label)
  * any bar overrunning the plot area
  * elements overflowing their figure container

and saves a screenshot of each so the result can be looked at rather than
assumed.

    python scripts/check_pages.py            # check + screenshot
    python scripts/check_pages.py --open     # also print the screenshot paths
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
SHOTS = BASE / "docs" / "checks"
PAGES = ["report.html", "sources.html", "onepager.html", "index.html"]
VIEWPORTS = [("desktop", 1280, 1000), ("phone", 390, 844)]

PROBE = """
() => {
  const problems = [];
  const de = document.documentElement;
  if (de.scrollWidth > de.clientWidth + 1) {
    problems.push(`document scrolls horizontally: ${de.scrollWidth} > ${de.clientWidth}`);
  }
  document.querySelectorAll('svg.chart').forEach((svg, i) => {
    const vb = svg.viewBox.baseVal;
    svg.querySelectorAll('text').forEach(t => {
      let b;
      try { b = t.getBBox(); } catch (e) { return; }
      // getBBox reports pre-transform coordinates, so a rotated axis title
      // looks out of bounds when it is not. Skip those.
      if (t.getAttribute('transform')) return;
      const label = (t.textContent || '').slice(0, 40);
      // Sub-pixel side bearing on the first glyph is not a layout problem.
      if (b.x < -4) {
        problems.push(`chart ${i}: text starts left of the box (x=${b.x.toFixed(1)}): "${label}"`);
      }
      if (b.x + b.width > vb.width + 0.5) {
        problems.push(`chart ${i}: text overruns right edge by ${(b.x + b.width - vb.width).toFixed(1)}: "${label}"`);
      }
      if (b.y + b.height > vb.height + 0.5) {
        problems.push(`chart ${i}: text below the box: "${label}"`);
      }
    });
    svg.querySelectorAll('rect').forEach(r => {
      const x = parseFloat(r.getAttribute('x') || 0);
      const w = parseFloat(r.getAttribute('width') || 0);
      if (x + w > vb.width + 0.5) {
        problems.push(`chart ${i}: a bar overruns the plot area by ${(x + w - vb.width).toFixed(1)}`);
      }
    });
  });
  document.querySelectorAll('figure, .tile, .finding').forEach(el => {
    if (el.scrollWidth > el.clientWidth + 1 && !el.querySelector('.scroll')) {
      problems.push(`${el.className || el.tagName} overflows its container`);
    }
  });
  return problems;
}
"""


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    total = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for theme in ("light", "dark"):
            for name, width, height in VIEWPORTS:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    color_scheme=theme,
                    device_scale_factor=2 if name == "phone" else 1,
                )
                page = context.new_page()
                for filename in PAGES:
                    path = BASE / filename
                    if not path.exists():
                        continue
                    page.goto(path.as_uri())
                    page.wait_for_timeout(220)
                    problems = page.evaluate(PROBE)
                    tag = f"{filename.replace('.html','')} {theme}/{name}"
                    if problems:
                        total += len(problems)
                        print(f"[{len(problems):2d}] {tag}")
                        for problem in dict.fromkeys(problems):
                            print(f"       {problem}")
                    else:
                        print(f"[ ok] {tag}")
                    if name == "desktop":
                        shot = SHOTS / f"{filename.replace('.html','')}-{theme}.png"
                        page.screenshot(path=str(shot), full_page=True)
                context.close()
        browser.close()

    print(f"\n{total} layout problem(s)")
    if "--open" in sys.argv:
        for shot in sorted(SHOTS.glob("*.png")):
            print(" ", shot)
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
