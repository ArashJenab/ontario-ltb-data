# -*- coding: utf-8 -*-
"""
Assemble the single, self-contained choropleth map: both geographies and both
denominators in one page.

Replaces the pair of near-identical maps (map.html and city-map.html) that
showed the same data at two levels and forced a 2.8MB page load to switch
between them. Geography is now a toggle.

The CSS, the pan/zoom, the tooltip and the ranked list are lifted verbatim from
scripts/build_fsa_map_html.py, which was working; what changed is that the
feature list, the labels and the reliability floor are now functions of which
layer and which denominator is selected, rather than baked in at build time.

The denominator toggle is the substantive addition. Per 10,000 residents was
the only option before, and it mostly measures tenure mix: an area that is 80%
renters shows more rental disputes per resident than one that is 20% renters
with nothing else differing. Per 1,000 renter households is the rate this
analysis actually argues from, and it reorders the map.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAYLOAD_PATH = BASE / "data" / "map_payload.json"
SOURCE_TEMPLATE = BASE / "scripts" / "build_fsa_map_html.py"
OUT_PATH = BASE / "map.html"


def extract_css():
    """Take the <style> block from the existing FSA builder, unchanged.

    Read rather than duplicated so the two cannot drift apart while both exist,
    and so this file stays about the merge rather than about 320 lines of CSS
    that were already right.
    """
    source = SOURCE_TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r"<style>.*?</style>", source, re.S)
    if not match:
        raise SystemExit("No <style> block found in build_fsa_map_html.py")
    return match.group(0)


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where Ontario's rental disputes concentrate</title>
<meta name="description" content="Landlord and Tenant Board applications by postal area or municipality, per renter household or per resident. Built from Ontario open data and the 2021 Census.">
__CSS__
<style>
  /* The inherited CSS gives every pressed segmented button white text but only
     paints a background for [data-lens] and [data-metric]. The geography
     toggle is new, so without this its active button is white on white. */
  .segmented button[data-geo][aria-pressed="true"] { background: var(--ink); }
  .segmented button.wide { padding-left: 14px; padding-right: 14px; }
  /* The inherited grid reserves a fixed 46px for the label, which fits a
     postal code and truncates "East Gwillimbury" into the bar beside it.
     Let the label take the slack and ellipsis instead. */
  .rank-row { grid-template-columns: 20px minmax(0, 1fr) 76px 46px; }
  .rank-val { text-align: right; }
  .rank-fsa { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .denominator-note {
    margin-top: 10px; font-size: 12.5px; line-height: 1.55; color: var(--ink-muted);
  }
  .denominator-note b { color: var(--ink); }
</style>
</head>
<body>
<div class="page">
  <div class="nav-links"><a href="index.html">&larr; Ontario LTB Data</a> &middot; <a href="report.html">Read the report &rarr;</a></div>
  <div>
    <div class="eyebrow">Ontario &middot; LTB open-data applications &times; 2021 Census</div>
    <h1>Where Ontario's rental disputes concentrate</h1>
    <p class="dek">Landlord and Tenant Board applications, by postal area or by municipality,
       measured against renter households or against resident population. Hover any area for the
       full breakdown; click to pin it.</p>
  </div>

  <div class="controls">
    <div class="control-group">
      <span class="control-label">Geography</span>
      <div class="segmented" id="geo-toggle">
        <button data-geo="fsa" aria-pressed="true" class="wide">Postal area</button>
        <button data-geo="csd" aria-pressed="false" class="wide">City / municipality</button>
      </div>
    </div>
    <div class="control-group">
      <span class="control-label">Measured against</span>
      <div class="segmented" id="metric-toggle">
        <button data-metric="per1k" aria-pressed="true" class="wide">Per 1,000 renter households</button>
        <button data-metric="per10k" aria-pressed="false" class="wide">Per 10,000 residents</button>
        <button data-metric="raw" aria-pressed="false">Raw count</button>
      </div>
    </div>
    <div class="control-group">
      <span class="control-label">Lens</span>
      <div class="segmented" id="lens-toggle">
        <button data-lens="total" aria-pressed="true">Total</button>
        <button data-lens="landlord" aria-pressed="false">Landlord-filed</button>
        <button data-lens="tenant" aria-pressed="false">Tenant-filed</button>
      </div>
    </div>
  </div>
  <p class="denominator-note" id="denominator-note"></p>

  <div class="layout">
    <div class="map-card">
      <svg id="map-svg" viewBox="0 0 __WIDTH__ __HEIGHT__" xmlns="http://www.w3.org/2000/svg"></svg>
      <div class="zoom-hint" id="zoom-hint">Scroll to zoom &middot; drag to pan</div>
      <div class="legend">
        <div class="legend-title" id="legend-title"></div>
        <div class="legend-gradient" id="legend-gradient">
          <div class="legend-gradient-bar" id="legend-gradient-bar"></div>
          <div class="legend-gradient-scale"><span id="legend-grad-min">0</span><span id="legend-grad-max"></span></div>
        </div>
        <div class="legend-note" id="legend-note">Coloured on a smooth scale, so every area gets its own shade. Grey means no matching applications, or too small a denominator to give a stable rate.</div>
      </div>
      <div class="zoom-controls">
        <button id="zoom-in" title="Zoom in" aria-label="Zoom in">+</button>
        <button id="zoom-out" title="Zoom out" aria-label="Zoom out">&minus;</button>
        <button id="zoom-reset" title="Reset to default view" aria-label="Reset view">&#8634;</button>
      </div>
      <div class="tooltip" id="tooltip"></div>
    </div>

    <aside class="side">
      <section class="panel">
        <h2 id="rank-title">Top 10</h2>
        <div id="rank-list"></div>
      </section>
      <section class="panel">
        <h2>Province-wide</h2>
        <div class="stat-row"><span class="k" id="stat-matched-label">Areas with matched data</span><span class="v" id="stat-matched"></span></div>
        <div class="stat-row"><span class="k">Total applications</span><span class="v" id="stat-total"></span></div>
        <div class="stat-row"><span class="k">Landlord-filed</span><span class="v" id="stat-landlord"></span></div>
        <div class="stat-row"><span class="k">Tenant-filed</span><span class="v" id="stat-tenant"></span></div>
        <div class="stat-row"><span class="k">Renter households</span><span class="v" id="stat-renters"></span></div>
      </section>
    </aside>
  </div>

  <footer>
    Ranked lists exclude areas with fewer than 50 applications, because a rate built on a
    handful of cases says more about the size of the area than about the area.
    Application counts: Landlord and Tenant Board open-data export, area parsed from the rental unit address.
    Renter households and population: Statistics Canada, 2021 Census.
    Municipality figures are rolled up from postal areas by area-weighted overlap, so they are estimates
    at the boundary and can carry a fraction of a case.
    Grey areas have a boundary but no matching applications, or too small a denominator to rate reliably.
    <p style="margin:10px 0 0">This is an independent analysis developed using data published by the
    Government of Ontario. It is not an official publication of, and is not affiliated with or endorsed
    by, the Government of Ontario or the Landlord and Tenant Board.</p>
  </footer>
</div>

<script type="application/json" id="map-data">__PAYLOAD__</script>
<script>
(function () {
  var payload = JSON.parse(document.getElementById('map-data').textContent);
  var LAYERS = payload.layers;

  // One shared green-to-red ramp (low = green, high = red), ColorBrewer RdYlGn
  // reversed, so the reading is the same whichever lens is on.
  var RAMP = ["#1a9850", "#66bd63", "#a6d96a", "#fee08b", "#f46d43", "#a50026"];
  var LENS_LABEL = { total: "Total", landlord: "Landlord-filed", tenant: "Tenant-filed" };

  var METRIC = {
    per1k: {
      suffix: "_per1k",
      unit: "/1k renters",
      legend: "per 1,000 renter households",
      floorKey: "renters",
      floor: payload.renterFloor,
      decimals: 1
    },
    per10k: {
      suffix: "_per10k",
      unit: "/10k residents",
      legend: "per 10,000 residents",
      floorKey: "population",
      floor: payload.popFloor,
      decimals: 1
    },
    raw: { suffix: "", unit: "", legend: "raw count", floorKey: null, floor: 0, decimals: 0 }
  };

  var NOTE = {
    per1k: "<b>Per 1,000 renter households.</b> The denominator this analysis argues from: it asks how many disputes there are per household that could possibly have one.",
    per10k: "<b>Per 10,000 residents.</b> Kept for continuity with earlier versions of this map, but it largely measures tenure mix. An area that is 80% renters looks busier than one that is 20% renters with nothing else differing.",
    raw: "<b>Raw counts.</b> Useful for seeing where the volume is, but it mostly tracks how many people live somewhere."
  };

  var state = { geo: "fsa", metric: "per1k", lens: "total" };

  // A rate needs a numerator as well as a denominator before it can head a
  // league table. Without this, two townships with seventeen cases each between
  // them top the municipality ranking, which is an artifact of dividing a small
  // number by a smaller one, not a finding about those places. Colouring keeps
  // the denominator floor only; this applies to the ranked list.
  var RANK_CASE_FLOOR = 50;

  var svg = document.getElementById('map-svg');
  var tooltip = document.getElementById('tooltip');
  var pinned = null;
  var wasDragged = false;
  var dragStart = null;
  var pathEls = [];
  var features = [];

  function layer() { return LAYERS[state.geo]; }

  function valueFor(f, lens, metric) {
    var spec = METRIC[metric];
    var v = f[lens + spec.suffix];
    return (v === undefined || v === null) ? null : v;
  }
  function isReliable(f, metric) {
    var spec = METRIC[metric];
    if (!spec.floorKey) return true;
    var d = f[spec.floorKey];
    return d !== null && d !== undefined && d >= spec.floor;
  }

  // A smooth gradient across the ramp rather than discrete bins, on a sqrt
  // transform because the data is heavily right-skewed: a linear scale leaves
  // almost everything pale with one or two outliers eating the dark end.
  function computeDomain(lens, metric) {
    var vals = features
      .filter(function (f) { return isReliable(f, metric); })
      .map(function (f) { return valueFor(f, lens, metric); })
      .filter(function (v) { return v !== null; });
    return { min: vals.length ? Math.min.apply(null, vals) : 0,
             max: vals.length ? Math.max.apply(null, vals) : 1 };
  }
  function hexToRgb(h) {
    h = h.replace('#', '');
    return [parseInt(h.substring(0,2),16), parseInt(h.substring(2,4),16), parseInt(h.substring(4,6),16)];
  }
  function mixHex(a, b, t) {
    var ca = hexToRgb(a), cb = hexToRgb(b);
    return "rgb(" + Math.round(ca[0]+(cb[0]-ca[0])*t) + "," +
                    Math.round(ca[1]+(cb[1]-ca[1])*t) + "," +
                    Math.round(ca[2]+(cb[2]-ca[2])*t) + ")";
  }
  function continuousColor(v, domain) {
    var span = domain.max - domain.min;
    var t = span > 0 ? Math.sqrt(Math.max(0, v - domain.min)) / Math.sqrt(span) : 0;
    t = Math.max(0, Math.min(1, t));
    var idx = t * (RAMP.length - 1);
    var i0 = Math.floor(idx), i1 = Math.min(RAMP.length - 1, i0 + 1);
    return mixHex(RAMP[i0], RAMP[i1], idx - i0);
  }
  function colorForFeature(f, lens, metric, domain) {
    var v = valueFor(f, lens, metric);
    if (v === null || !isReliable(f, metric)) return null;
    return continuousColor(v, domain);
  }

  function fmt(n) { return (n === null || n === undefined) ? "N/A" : Math.round(n).toLocaleString(); }
  function fmtRate(n, d) { return (n === null || n === undefined) ? "N/A" : n.toFixed(d === undefined ? 1 : d); }
  function getVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  // Paths are rebuilt whenever the geography changes, because the two layers
  // have different features. Everything else only recolours.
  function buildPaths() {
    svg.innerHTML = '';
    pinned = null;
    features = layer().features;
    pathEls = features.map(function (f) {
      var el = document.createElementNS("http://www.w3.org/2000/svg", "path");
      el.setAttribute("d", f.d);
      el.setAttribute("data-id", f.id);
      el.addEventListener("mousemove", function (e) { showTooltip(e, f); });
      el.addEventListener("mouseleave", function () { if (!pinned) hideTooltip(); });
      el.addEventListener("click", function () {
        if (wasDragged) return;
        if (pinned === f.id) { pinned = null; el.classList.remove('pinned'); hideTooltip(); }
        else {
          pathEls.forEach(function (p) { p.classList.remove('pinned'); });
          pinned = f.id; el.classList.add('pinned');
        }
      });
      svg.appendChild(el);
      return el;
    });
  }

  function showTooltip(e, f) {
    if (dragStart) return;
    var dot = { landlord: getVar('--landlord'), tenant: getVar('--tenant') };
    var spec = METRIC[state.metric];
    // An area the map refuses to colour must not be handed a confident-looking
    // rate on hover. Below the floor the denominator is small enough that one
    // case swings the rate by tens of points, so the tooltip says so instead.
    var rateable = isReliable(f, state.metric) && state.metric !== 'raw';
    var tooSmall = !isReliable(f, state.metric) && state.metric !== 'raw';
    function line(lens, label, colour) {
      var v = valueFor(f, lens, state.metric);
      var tail = rateable ? ' &middot; ' + fmtRate(v) + spec.unit : '';
      return '<div class="t-row"><span><span class="t-dot" style="background:' + colour + '"></span>' +
             label + '</span><span>' + fmt(f[lens]) + tail + '</span></div>';
    }
    var totalTail = rateable
      ? ' &middot; ' + fmtRate(valueFor(f, 'total', state.metric)) + spec.unit : '';
    tooltip.innerHTML =
      '<div class="t-fsa">' + f.label + '</div>' +
      '<div class="t-row t-muted"><span>Renter households</span><span>' + fmt(f.renters) + '</span></div>' +
      '<div class="t-row t-muted"><span>Population (2021)</span><span>' + fmt(f.population) + '</span></div>' +
      line('landlord', 'Landlord-filed', dot.landlord) +
      line('tenant', 'Tenant-filed', dot.tenant) +
      '<div class="t-row" style="margin-top:4px;border-top:1px solid rgba(128,128,128,0.4);padding-top:4px;">' +
      '<span>Total</span><span>' + fmt(f.total) + totalTail + '</span></div>' +
      (tooSmall
        ? '<div class="t-row t-muted" style="margin-top:4px;"><span>Not rated: too few ' +
          (spec.floorKey === 'renters' ? 'renter households' : 'residents') +
          ' for a stable rate</span></div>'
        : '');
    tooltip.classList.add('visible');
    positionTooltip(e);
  }
  function positionTooltip(e) {
    var pad = 14, tw = 260, th = 180;
    var x = e.clientX + pad, y = e.clientY + pad;
    if (x + tw > window.innerWidth) x = e.clientX - tw - pad;
    if (y + th > window.innerHeight) y = window.innerHeight - th - pad;
    tooltip.style.left = Math.max(pad, x) + "px";
    tooltip.style.top = Math.max(pad, y) + "px";
  }
  function hideTooltip() { tooltip.classList.remove('visible'); }

  svg.addEventListener('mousemove', function (e) {
    if (e.target && e.target.tagName === 'path') positionTooltip(e);
  });

  function render() {
    var lens = state.lens, metric = state.metric, spec = METRIC[metric];
    var domain = computeDomain(lens, metric);
    var colorOf = function (f) { return colorForFeature(f, lens, metric, domain); };

    pathEls.forEach(function (el, i) {
      el.setAttribute("fill", colorOf(features[i]) || getVar('--no-data'));
    });

    document.getElementById('denominator-note').innerHTML = NOTE[metric];
    document.getElementById('legend-title').textContent =
      LENS_LABEL[lens] + ' applications, ' + spec.legend;
    var fmtBin = metric === 'raw' ? function (v) { return fmt(v); }
                                  : function (v) { return v.toFixed(spec.decimals); };
    document.getElementById('legend-gradient-bar').style.background =
      'linear-gradient(90deg,' + RAMP.join(',') + ')';
    document.getElementById('legend-grad-min').textContent = fmtBin(domain.min);
    document.getElementById('legend-grad-max').textContent = fmtBin(domain.max);

    var ranked = features
      .filter(function (f) { return valueFor(f, lens, metric) !== null && isReliable(f, metric); })
      .filter(function (f) { return metric === 'raw' || (f.total || 0) >= RANK_CASE_FLOOR; })
      .sort(function (a, b) { return valueFor(b, lens, metric) - valueFor(a, lens, metric); })
      .slice(0, 10);
    var maxVal = ranked.length ? valueFor(ranked[0], lens, metric) : 1;
    document.getElementById('rank-list').innerHTML = ranked.map(function (f, i) {
      var v = valueFor(f, lens, metric);
      // The panel title already names the unit; repeating it on all ten rows
      // costs about 70px that the municipality names need.
      var label = metric === 'raw' ? fmt(v) : fmtRate(v);
      return '<div class="rank-row">' +
        '<span class="rank-idx">' + (i + 1) + '</span>' +
        '<span class="rank-fsa" title="' + f.label + '">' + f.label + '</span>' +
        '<span class="rank-bar-track"><span class="rank-bar-fill" style="width:' +
          (maxVal > 0 ? v / maxVal * 100 : 0) + '%;background:' + (colorOf(f) || getVar('--no-data')) + '"></span></span>' +
        '<span class="rank-val">' + label + '</span></div>';
    }).join('');
    document.getElementById('rank-title').textContent =
      'Top 10 ' + layer().plural + ': ' + LENS_LABEL[lens] +
      (metric === 'raw' ? ' (raw)' : ' ' + spec.legend);

    var usable = features.filter(function (f) { return isReliable(f, metric); }).length;
    var plural = layer().plural;
    document.getElementById('stat-matched-label').textContent =
      plural.charAt(0).toUpperCase() + plural.slice(1) + ' rated';
    document.getElementById('stat-matched').textContent = usable + ' / ' + features.length;
    document.getElementById('stat-total').textContent =
      fmt(features.reduce(function (a, f) { return a + (f.total || 0); }, 0));
    document.getElementById('stat-landlord').textContent =
      fmt(features.reduce(function (a, f) { return a + (f.landlord || 0); }, 0));
    document.getElementById('stat-tenant').textContent =
      fmt(features.reduce(function (a, f) { return a + (f.tenant || 0); }, 0));
    document.getElementById('stat-renters').textContent =
      fmt(features.reduce(function (a, f) { return a + (f.renters || 0); }, 0));
  }

  // ---- pan / zoom -------------------------------------------------------
  var view;
  function defaultView() {
    var f = layer().focusView;
    return { x: f.x, y: f.y, w: f.width, h: f.height };
  }
  function applyView() {
    svg.setAttribute('viewBox', view.x + ' ' + view.y + ' ' + view.w + ' ' + view.h);
  }
  function resetView() { view = defaultView(); applyView(); }

  function zoomBy(factor, cx, cy) {
    var nw = Math.max(20, Math.min(payload.width * 2, view.w * factor));
    var nh = nw * (view.h / view.w);
    if (cx === undefined) { cx = view.x + view.w / 2; cy = view.y + view.h / 2; }
    view.x = cx - (cx - view.x) * (nw / view.w);
    view.y = cy - (cy - view.y) * (nh / view.h);
    view.w = nw; view.h = nh;
    applyView();
  }
  function svgPoint(e) {
    var r = svg.getBoundingClientRect();
    return { x: view.x + (e.clientX - r.left) / r.width * view.w,
             y: view.y + (e.clientY - r.top) / r.height * view.h };
  }
  svg.addEventListener('wheel', function (e) {
    e.preventDefault();
    var p = svgPoint(e);
    zoomBy(e.deltaY > 0 ? 1.15 : 1 / 1.15, p.x, p.y);
  }, { passive: false });
  svg.addEventListener('mousedown', function (e) {
    dragStart = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
    wasDragged = false;
    svg.style.cursor = 'grabbing';
  });
  window.addEventListener('mousemove', function (e) {
    if (!dragStart) return;
    var r = svg.getBoundingClientRect();
    var dx = (e.clientX - dragStart.x) / r.width * view.w;
    var dy = (e.clientY - dragStart.y) / r.height * view.h;
    if (Math.abs(e.clientX - dragStart.x) > 3 || Math.abs(e.clientY - dragStart.y) > 3) wasDragged = true;
    view.x = dragStart.vx - dx; view.y = dragStart.vy - dy;
    applyView();
  });
  window.addEventListener('mouseup', function () {
    dragStart = null; svg.style.cursor = '';
    setTimeout(function () { wasDragged = false; }, 0);
  });
  document.getElementById('zoom-in').addEventListener('click', function () { zoomBy(1 / 1.3); });
  document.getElementById('zoom-out').addEventListener('click', function () { zoomBy(1.3); });
  document.getElementById('zoom-reset').addEventListener('click', resetView);

  // ---- controls ---------------------------------------------------------
  function wire(id, key, onChange) {
    document.getElementById(id).addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var value = btn.getAttribute('data-' + key);
      if (!value || state[key] === value) return;
      state[key] = value;
      Array.prototype.forEach.call(this.querySelectorAll('button'), function (b) {
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      if (onChange) onChange();
      render();
    });
  }
  wire('metric-toggle', 'metric');
  wire('lens-toggle', 'lens');
  wire('geo-toggle', 'geo', function () {
    buildPaths();
    resetView();
    hideTooltip();
  });

  buildPaths();
  resetView();
  render();
})();
</script>
</body>
</html>
"""


def main():
    payload_text = PAYLOAD_PATH.read_text(encoding="utf-8")
    # A literal "</script" inside JSON would close the tag early.
    payload_text = payload_text.replace("</script", "<\\/script")
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))

    html = HEAD.replace("__CSS__", extract_css())
    html = html.replace("__WIDTH__", str(payload["width"]))
    html = html.replace("__HEIGHT__", str(payload["height"]))
    html = html.replace("__PAYLOAD__", payload_text)

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.2f} MB)")
    for key, layer in payload["layers"].items():
        print(f"  {key}: {len(layer['features'])} features")


if __name__ == "__main__":
    main()
