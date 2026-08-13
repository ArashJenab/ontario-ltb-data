# -*- coding: utf-8 -*-
"""Assemble the self-contained FSA choropleth map HTML artifact."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAYLOAD_PATH = BASE / "data" / "fsa_map_payload.json"
OUT_PATH = BASE / "scripts" / "_build" / "fsa_dispute_map.html"

TEMPLATE = r"""
<meta charset="utf-8">
<title>Ontario Rental Dispute Map</title>
<style>
  :root {
    --bg: #eef1f5;
    --surface: #ffffff;
    --surface-2: #f7f8fb;
    --ink: #1a2130;
    --ink-muted: #5c6675;
    --ink-faint: #8b93a1;
    --border: #dde1e8;
    --border-strong: #c7cdd7;
    --landlord: #2a78d6;
    --landlord-ink: #14477f;
    --tenant: #eb6834;
    --tenant-ink: #8a3a16;
    --neutral-accent: #4b3f8f;
    --neutral-ink: #322875;
    --no-data: #e4e7ec;
    --map-water: #e4eaf1;
    --shadow: 0 1px 2px rgba(20, 24, 32, 0.06), 0 8px 24px rgba(20, 24, 32, 0.06);
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #0f1319;
      --surface: #171c25;
      --surface-2: #12161d;
      --ink: #e8ecf3;
      --ink-muted: #9aa4b4;
      --ink-faint: #6b7484;
      --border: #262d3a;
      --border-strong: #333c4c;
      --landlord: #5b9be0;
      --landlord-ink: #bcdcff;
      --tenant: #f0895a;
      --tenant-ink: #ffd2b8;
      --neutral-accent: #8b81d6;
      --neutral-ink: #d8d4f5;
      --no-data: #333d4d;
      --map-water: #161b24;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.35);
    }
  }
  :root[data-theme="dark"] {
    --bg: #0f1319;
    --surface: #171c25;
    --surface-2: #12161d;
    --ink: #e8ecf3;
    --ink-muted: #9aa4b4;
    --ink-faint: #6b7484;
    --border: #262d3a;
    --border-strong: #333c4c;
    --landlord: #5b9be0;
    --landlord-ink: #bcdcff;
    --tenant: #f0895a;
    --tenant-ink: #ffd2b8;
    --neutral-accent: #8b81d6;
    --neutral-ink: #d8d4f5;
    --no-data: #333d4d;
    --map-water: #161b24;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.35);
  }

  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  body {
    padding: clamp(16px, 3vw, 40px);
    display: flex;
    justify-content: center;
  }
  .page {
    width: 100%;
    max-width: 1180px;
    display: flex;
    flex-direction: column;
    gap: 22px;
  }

  .nav-links { font-size: 13px; }
  .nav-links a { color: var(--ink-faint); text-decoration: none; }
  .nav-links a:hover { color: var(--ink-muted); }

  .eyebrow {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  h1 {
    margin: 4px 0 0 0;
    font-size: clamp(24px, 3.4vw, 34px);
    font-weight: 700;
    letter-spacing: -0.01em;
    text-wrap: balance;
  }
  .dek {
    margin: 8px 0 0 0;
    max-width: 100%;
    text-wrap: pretty;
    font-size: 15px;
    line-height: 1.55;
    color: var(--ink-muted);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 20px;
    padding: 14px 18px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
  }
  .control-group { display: flex; flex-direction: column; gap: 7px; }
  .control-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--ink-faint);
  }
  .segmented {
    display: inline-flex;
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    overflow: hidden;
  }
  .segmented button {
    appearance: none;
    border: none;
    background: var(--surface);
    color: var(--ink-muted);
    font-size: 13.5px;
    font-weight: 600;
    padding: 7px 14px;
    cursor: pointer;
    border-right: 1px solid var(--border-strong);
    font-family: inherit;
  }
  .segmented button:last-child { border-right: none; }
  .segmented button:focus-visible { outline: 2px solid var(--neutral-accent); outline-offset: -2px; }
  .segmented button[aria-pressed="true"] { color: #fff; }
  .segmented button[data-lens="total"][aria-pressed="true"] { background: var(--neutral-accent); }
  .segmented button[data-lens="landlord"][aria-pressed="true"] { background: var(--landlord); }
  .segmented button[data-lens="tenant"][aria-pressed="true"] { background: var(--tenant); }
  .segmented button[data-metric][aria-pressed="true"] { background: var(--ink); }
  .segmented button[data-colormode][aria-pressed="true"] { background: var(--ink); }

  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 18px;
    align-items: start;
  }
  @media (max-width: 860px) {
    .layout { grid-template-columns: 1fr; }
  }

  .map-card {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow);
    padding: 14px;
    overflow: hidden;
  }
  #map-svg { width: 100%; height: auto; display: block; background: var(--map-water); border-radius: 8px; }
  #map-svg path {
    stroke: var(--surface);
    stroke-width: 0.6;
    vector-effect: non-scaling-stroke;
    cursor: pointer;
    transition: filter 0.12s ease;
  }
  #map-svg path:hover, #map-svg path.pinned { filter: brightness(1.12); stroke: var(--ink); stroke-width: 1.4; }

  .legend {
    position: absolute;
    left: 26px;
    bottom: 26px;
    background: color-mix(in srgb, var(--surface) 92%, transparent);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 11.5px;
    color: var(--ink-muted);
    backdrop-filter: blur(3px);
  }
  .legend-title { font-weight: 700; color: var(--ink); margin-bottom: 8px; font-size: 12px; }
  .legend-bins { display: flex; flex-direction: column; gap: 3px; }
  .legend-bin-row { display: flex; align-items: center; gap: 7px; font-variant-numeric: tabular-nums; }
  .legend-bin-swatch { width: 15px; height: 11px; border-radius: 3px; flex: none; }
  .legend-nodata { display: flex; align-items: center; gap: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
  .legend-swatch { width: 11px; height: 11px; border-radius: 3px; background: var(--no-data); border: 1px solid var(--border-strong); flex: none; }
  .legend-note { font-size: 10.5px; color: var(--ink-faint); margin-top: 3px; max-width: 190px; line-height: 1.4; }
  .legend-gradient-bar { width: 170px; height: 12px; border-radius: 4px; }
  .legend-gradient-scale { display: flex; justify-content: space-between; font-variant-numeric: tabular-nums; margin-top: 4px; }

  .zoom-controls {
    position: absolute;
    right: 26px;
    bottom: 26px;
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .zoom-controls button {
    appearance: none;
    border: none;
    background: var(--surface);
    color: var(--ink);
    width: 34px;
    height: 34px;
    font-size: 17px;
    line-height: 1;
    cursor: pointer;
    border-bottom: 1px solid var(--border);
    font-family: inherit;
  }
  .zoom-controls button:last-child { border-bottom: none; }
  .zoom-controls button:hover { background: var(--surface-2); }
  .zoom-controls button:focus-visible { outline: 2px solid var(--neutral-accent); outline-offset: -2px; }
  .zoom-hint {
    position: absolute;
    left: 50%;
    top: 14px;
    transform: translateX(-50%);
    font-size: 11px;
    color: var(--ink-faint);
    background: color-mix(in srgb, var(--surface) 85%, transparent);
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid var(--border);
    pointer-events: none;
  }
  #map-svg.grabbing { cursor: grabbing; }
  #map-svg { cursor: grab; touch-action: none; }

  .tooltip {
    position: fixed;
    pointer-events: none;
    background: var(--ink);
    color: var(--bg);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 12.5px;
    line-height: 1.5;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    opacity: 0;
    transition: opacity 0.08s ease;
    z-index: 50;
    max-width: 240px;
  }
  .tooltip.visible { opacity: 1; }
  .tooltip .t-fsa { font-weight: 700; font-size: 14px; letter-spacing: 0.02em; }
  .tooltip .t-row { display: flex; justify-content: space-between; gap: 14px; font-variant-numeric: tabular-nums; }
  .tooltip .t-muted { opacity: 0.7; }
  .tooltip .t-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }

  .side {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow);
    padding: 16px 18px;
  }
  .panel h2 {
    margin: 0 0 12px 0;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: var(--ink);
  }
  .rank-row {
    display: grid;
    grid-template-columns: 22px 46px 1fr auto;
    align-items: center;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  .rank-row:last-child { border-bottom: none; }
  .rank-idx { color: var(--ink-faint); font-variant-numeric: tabular-nums; font-size: 12px; }
  .rank-fsa { font-weight: 700; letter-spacing: 0.02em; }
  .rank-bar-track { height: 6px; border-radius: 3px; background: var(--surface-2); overflow: hidden; }
  .rank-bar-fill { height: 100%; border-radius: 3px; }
  .rank-val { font-variant-numeric: tabular-nums; font-size: 12.5px; color: var(--ink-muted); white-space: nowrap; }

  .stat-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
  .stat-row:last-child { border-bottom: none; }
  .stat-row .k { color: var(--ink-muted); }
  .stat-row .v { font-weight: 700; font-variant-numeric: tabular-nums; }

  footer {
    font-size: 12px;
    line-height: 1.6;
    color: var(--ink-faint);
    padding-top: 4px;
    border-top: 1px solid var(--border);
  }
  footer a { color: var(--ink-muted); }

  @media (prefers-reduced-motion: reduce) {
    #map-svg path { transition: none; }
    .tooltip { transition: none; }
  }
</style>

<div class="page">
  <div class="nav-links"><a href="index.html">&larr; Ontario LTB Data</a> &middot; <a href="city-map.html">City-level map &rarr;</a></div>
  <div>
    <div class="eyebrow">Ontario &middot; 2021 census population &times; LTB open-data applications</div>
    <h1>Where Ontario's rental disputes concentrate</h1>
    <p class="dek">Landlord and Tenant Board applications by postal FSA (Forward Sortation Area &mdash; the first
       3 characters of a postal code, e.g. <b>N6J</b>), normalized against resident population.
       Toggle between raw volume and per-10,000-resident rates, and between landlord-filed and tenant-filed cases &mdash;
       hover any area for the full breakdown. Prefer city names to postal codes?
       <a href="city-map.html">See the city-level map</a>.</p>
  </div>

  <div class="controls">
    <div class="control-group">
      <span class="control-label">Basis</span>
      <div class="segmented" id="metric-toggle">
        <button data-metric="per10k" aria-pressed="true">Per 10,000 residents</button>
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
    <div class="control-group">
      <span class="control-label">Color by</span>
      <div class="segmented" id="colormode-toggle">
        <button data-colormode="quantile" aria-pressed="true">Rank (6 groups)</button>
        <button data-colormode="continuous" aria-pressed="false">Value (every area distinct)</button>
      </div>
    </div>
  </div>

  <div class="layout">
    <div class="map-card">
      <svg id="map-svg" viewBox="0 0 __WIDTH__ __HEIGHT__" xmlns="http://www.w3.org/2000/svg"></svg>
      <div class="zoom-hint" id="zoom-hint">Scroll to zoom &middot; drag to pan</div>
      <div class="legend">
        <div class="legend-title" id="legend-title">Total applications / 10,000 residents</div>
        <div class="legend-bins" id="legend-bins"></div>
        <div class="legend-gradient" id="legend-gradient" style="display:none;">
          <div class="legend-gradient-bar" id="legend-gradient-bar"></div>
          <div class="legend-gradient-scale"><span id="legend-grad-min">0</span><span id="legend-grad-max">&mdash;</span></div>
        </div>
        <div class="legend-nodata"><span class="legend-swatch"></span><span>No data / population too small</span></div>
        <div class="legend-note" id="legend-note">Colored by rank (equal-count bins), not raw value &mdash; a few extreme FSAs no longer wash out the rest.</div>
      </div>
      <div class="zoom-controls">
        <button id="zoom-in" title="Zoom in" aria-label="Zoom in">+</button>
        <button id="zoom-out" title="Zoom out" aria-label="Zoom out">&minus;</button>
        <button id="zoom-reset" title="Reset to default view" aria-label="Reset view">&#8634;</button>
      </div>
      <div class="tooltip" id="tooltip"></div>
    </div>

    <div class="side">
      <div class="panel">
        <h2 id="rank-title">Top 10 FSAs</h2>
        <div id="rank-list"></div>
      </div>
      <div class="panel">
        <h2>Province-wide</h2>
        <div class="stat-row"><span class="k">FSAs with matched data</span><span class="v" id="stat-matched"></span></div>
        <div class="stat-row"><span class="k">Total applications</span><span class="v" id="stat-total"></span></div>
        <div class="stat-row"><span class="k">Landlord-filed</span><span class="v" id="stat-landlord"></span></div>
        <div class="stat-row"><span class="k">Tenant-filed</span><span class="v" id="stat-tenant"></span></div>
      </div>
    </div>
  </div>

  <footer>
    Application counts: Landlord and Tenant Board open-data export (40,844 records, FSA parsed from rental unit address).
    Population: Statistics Canada table 98-10-0019-01, 2021 Census. Per-10,000 rate = applications &divide; population &times; 10,000.
    Raw counts favor high-population areas; per-10,000 rates get noisy for small-population FSAs &mdash; treat single-digit-population-thousands
    FSAs with some caution. Grey areas have an FSA boundary but no matching LTB applications in this export.
  </footer>
</div>

<script type="application/json" id="map-data">__PAYLOAD__</script>
<script>
(function () {
  var payload = JSON.parse(document.getElementById('map-data').textContent);
  var features = payload.features;

  var RAMPS = {
    total:    ["#eef0fb", "#d6d9f5", "#b3b7ea", "#8288d6", "#574fb0", "#322875"],
    landlord: ["#eaf2fc", "#c9e0f7", "#93c2ee", "#5ca0e2", "#2e7dd1", "#163f6e"],
    tenant:   ["#fdf1e9", "#fad9be", "#f4b383", "#eb8c50", "#d66325", "#7a3210"]
  };
  var LENS_LABEL = { total: "Total", landlord: "Landlord-filed", tenant: "Tenant-filed" };
  var LENS_DOT = { total: "var(--neutral-accent)", landlord: "var(--landlord)", tenant: "var(--tenant)" };

  var state = { metric: "per10k", lens: "total", colormode: "quantile" };
  var POP_FLOOR = 1000; // below this, a per-10k rate is too noisy to color reliably

  var svg = document.getElementById('map-svg');
  var tooltip = document.getElementById('tooltip');
  var pinned = null;
  var wasDragged = false;

  function valueFor(f, lens, metric) {
    var key = lens + (metric === "per10k" ? "_per10k" : "");
    if (metric === "raw") return f[lens] === undefined ? null : f[lens];
    return f[key] === undefined ? null : f[key];
  }
  function isReliable(f, metric) {
    if (metric !== "per10k") return true;
    return f.population === null || f.population >= POP_FLOOR;
  }

  // Quantile (equal-COUNT) bins instead of linear min-max: this data is
  // heavily right-skewed (a couple of tiny-population FSAs post rates in
  // the hundreds/10k while the typical FSA sits under 30/10k), so a linear
  // scale leaves almost everything the same pale shade with one or two
  // outliers eating the dark end. Ranking into equal-sized bins guarantees
  // real, visible contrast is spent where the data actually varies.
  function computeBins(lens, metric) {
    var vals = features
      .filter(function (f) { return isReliable(f, metric); })
      .map(function (f) { return valueFor(f, lens, metric); })
      .filter(function (v) { return v !== null && v !== undefined; })
      .sort(function (a, b) { return a - b; });
    var nBins = RAMPS[lens].length;
    var breaks = [];
    for (var i = 0; i <= nBins; i++) {
      var p = i / nBins;
      var idx = p * (vals.length - 1);
      var i0 = Math.floor(idx), i1 = Math.min(vals.length - 1, i0 + 1), frac = idx - i0;
      breaks.push(vals.length ? vals[i0] + (vals[i1] - vals[i0]) * frac : 0);
    }
    return breaks; // nBins+1 edges
  }
  function binIndex(v, breaks) {
    for (var i = 0; i < breaks.length - 2; i++) {
      if (v <= breaks[i + 1]) return i;
    }
    return breaks.length - 2;
  }

  // "By value" mode: a smooth gradient across the ramp instead of 6 discrete
  // groups, so two nearby-but-different areas (e.g. two FSAs both in the top
  // rank bin) get visibly different shades instead of identical ones. Uses a
  // sqrt transform, not linear, for the same right-skew reason quantile bins
  // exist — a few extreme values would otherwise still wash out the rest even
  // on a continuous scale.
  function computeContinuousDomain(lens, metric) {
    var vals = features
      .filter(function (f) { return isReliable(f, metric); })
      .map(function (f) { return valueFor(f, lens, metric); })
      .filter(function (v) { return v !== null && v !== undefined; });
    return { min: vals.length ? Math.min.apply(null, vals) : 0, max: vals.length ? Math.max.apply(null, vals) : 1 };
  }
  function hexToRgb(h) {
    h = h.replace('#', '');
    return [parseInt(h.substring(0, 2), 16), parseInt(h.substring(2, 4), 16), parseInt(h.substring(4, 6), 16)];
  }
  function mixHex(a, b, t) {
    var ca = hexToRgb(a), cb = hexToRgb(b);
    var r = Math.round(ca[0] + (cb[0] - ca[0]) * t);
    var g = Math.round(ca[1] + (cb[1] - ca[1]) * t);
    var bl = Math.round(ca[2] + (cb[2] - ca[2]) * t);
    return "rgb(" + r + "," + g + "," + bl + ")";
  }
  function continuousColor(ramp, v, domain) {
    var span = domain.max - domain.min;
    var t = span > 0 ? Math.sqrt(Math.max(0, v - domain.min)) / Math.sqrt(span) : 0;
    t = Math.max(0, Math.min(1, t));
    var idx = t * (ramp.length - 1);
    var i0 = Math.floor(idx), i1 = Math.min(ramp.length - 1, i0 + 1), frac = idx - i0;
    return mixHex(ramp[i0], ramp[i1], frac);
  }

  // single source of truth for a feature's fill color — used for both the
  // map path and the matching swatch in the ranked list, so they never
  // disagree with each other
  function colorForFeature(f, lens, metric, ramp, breaks, domain) {
    var v = valueFor(f, lens, metric);
    if (v === null || v === undefined || !isReliable(f, metric)) return null;
    if (state.colormode === 'continuous') return continuousColor(ramp, v, domain);
    return ramp[binIndex(v, breaks)];
  }

  // build path elements once; recolor on state change
  var pathEls = features.map(function (f) {
    var el = document.createElementNS("http://www.w3.org/2000/svg", "path");
    el.setAttribute("d", f.d);
    el.setAttribute("data-fsa", f.fsa);
    el.addEventListener("mousemove", function (e) { showTooltip(e, f); });
    el.addEventListener("mouseleave", function () { if (!pinned) hideTooltip(); });
    el.addEventListener("click", function () {
      if (wasDragged) return; // a pan ending on top of a path shouldn't also toggle its pin
      if (pinned === f.fsa) { pinned = null; el.classList.remove('pinned'); hideTooltip(); }
      else {
        pathEls.forEach(function(p){ p.classList.remove('pinned'); });
        pinned = f.fsa; el.classList.add('pinned');
      }
    });
    svg.appendChild(el);
    return el;
  });

  function fmt(n) {
    if (n === null || n === undefined) return "—";
    return n.toLocaleString();
  }
  function fmtRate(n) {
    if (n === null || n === undefined) return "—";
    return n.toFixed(1);
  }

  function showTooltip(e, f) {
    if (dragStart) return;
    var dotColor = { total: getVar('--neutral-accent'), landlord: getVar('--landlord'), tenant: getVar('--tenant') };
    tooltip.innerHTML =
      '<div class="t-fsa">' + f.fsa + '</div>' +
      '<div class="t-row t-muted"><span>Population (2021)</span><span>' + fmt(f.population) + '</span></div>' +
      '<div class="t-row"><span><span class="t-dot" style="background:' + dotColor.landlord + '"></span>Landlord-filed</span><span>' + fmt(f.landlord) + ' &middot; ' + fmtRate(f.landlord_per10k) + '/10k</span></div>' +
      '<div class="t-row"><span><span class="t-dot" style="background:' + dotColor.tenant + '"></span>Tenant-filed</span><span>' + fmt(f.tenant) + ' &middot; ' + fmtRate(f.tenant_per10k) + '/10k</span></div>' +
      '<div class="t-row" style="margin-top:4px;border-top:1px solid rgba(128,128,128,0.4);padding-top:4px;"><span>Total</span><span>' + fmt(f.total) + ' &middot; ' + fmtRate(f.total_per10k) + '/10k</span></div>';
    tooltip.classList.add('visible');
    positionTooltip(e);
  }
  function positionTooltip(e) {
    var pad = 14, tw = 250, th = 160;
    var x = e.clientX + pad, y = e.clientY + pad;
    if (x + tw > window.innerWidth) x = e.clientX - tw - pad;
    if (y + th > window.innerHeight) y = window.innerHeight - th - pad;
    tooltip.style.left = Math.max(pad, x) + "px";
    tooltip.style.top = Math.max(pad, y) + "px";
  }
  function hideTooltip() { tooltip.classList.remove('visible'); }
  function getVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  svg.addEventListener('mousemove', function(e){
    var target = e.target;
    if (target && target.tagName === 'path') positionTooltip(e);
  });

  function render() {
    var lens = state.lens, metric = state.metric;
    var ramp = RAMPS[lens];
    var breaks = computeBins(lens, metric);
    var domain = computeContinuousDomain(lens, metric);
    var maxVal = breaks[breaks.length - 1];
    var colorOf = function (f) { return colorForFeature(f, lens, metric, ramp, breaks, domain); };

    pathEls.forEach(function (el, i) {
      var f = features[i];
      el.setAttribute("fill", colorOf(f) || getVar('--no-data'));
    });

    // legend: quantile mode gets one swatch per bin (a continuous min-max
    // gradient is exactly what hid the contrast in the first place); value
    // mode gets a smooth gradient bar with a min/max scale since it's a
    // genuinely continuous mapping.
    var quantileMode = state.colormode !== 'continuous';
    document.getElementById('legend-title').textContent =
      LENS_LABEL[lens] + ' applications' + (metric === 'per10k' ? ' / 10,000 residents' : ' (raw count)') +
      (quantileMode ? ', by rank' : ', by value');
    var fmtBin = metric === 'per10k' ? function(v){ return v.toFixed(1); } : function(v){ return fmt(Math.round(v)); };

    document.getElementById('legend-bins').style.display = quantileMode ? '' : 'none';
    document.getElementById('legend-gradient').style.display = quantileMode ? 'none' : '';
    if (quantileMode) {
      var binsHtml = '';
      for (var b = 0; b < ramp.length; b++) {
        var lo = breaks[b], hi = breaks[b + 1];
        var label = (b === ramp.length - 1) ? (fmtBin(lo) + '+') : (fmtBin(lo) + '\u2013' + fmtBin(hi));
        binsHtml += '<div class="legend-bin-row"><span class="legend-bin-swatch" style="background:' + ramp[b] + '"></span><span>' + label + '</span></div>';
      }
      document.getElementById('legend-bins').innerHTML = binsHtml;
      document.getElementById('legend-note').textContent =
        'Colored by rank (equal-count bins) \u2014 every group has the same number of areas, regardless of how close their values are.';
    } else {
      document.getElementById('legend-gradient-bar').style.background = 'linear-gradient(90deg,' + ramp.join(',') + ')';
      document.getElementById('legend-grad-min').textContent = fmtBin(domain.min);
      document.getElementById('legend-grad-max').textContent = fmtBin(domain.max);
      document.getElementById('legend-note').textContent =
        'Colored by value on a smooth scale \u2014 every area gets its own shade, so nearby values look similar but rarely identical.';
    }

    // rank list \u2014 the swatch/bar color here always matches colorForFeature,
    // i.e. exactly what that area looks like on the map right now
    var ranked = features
      .filter(function(f){ return f.population !== null && valueFor(f, lens, metric) !== null; })
      .filter(function(f){ return isReliable(f, metric); })
      .sort(function(a,b){ return valueFor(b, lens, metric) - valueFor(a, lens, metric); })
      .slice(0, 10);
    var rankHtml = ranked.map(function(f, i) {
      var v = valueFor(f, lens, metric);
      var pct = maxVal > 0 ? (v / maxVal * 100) : 0;
      var barColor = colorOf(f) || getVar('--no-data');
      var label = metric === 'per10k' ? fmtRate(v) + '/10k' : fmt(v);
      return '<div class="rank-row">' +
        '<span class="rank-idx">' + (i+1) + '</span>' +
        '<span class="rank-fsa">' + f.fsa + '</span>' +
        '<span class="rank-bar-track"><span class="rank-bar-fill" style="width:' + pct + '%;background:' + barColor + '"></span></span>' +
        '<span class="rank-val">' + label + '</span>' +
      '</div>';
    }).join('');
    document.getElementById('rank-list').innerHTML = rankHtml;
    document.getElementById('rank-title').textContent =
      'Top 10 FSAs — ' + LENS_LABEL[lens] + (metric === 'per10k' ? ' per 10k' : ' (raw)');

    // province stats (constant regardless of lens/metric)
    var matchedCount = features.filter(function(f){ return f.population !== null; }).length;
    var sumTotal = features.reduce(function(a,f){ return a + (f.total||0); }, 0);
    var sumLandlord = features.reduce(function(a,f){ return a + (f.landlord||0); }, 0);
    var sumTenant = features.reduce(function(a,f){ return a + (f.tenant||0); }, 0);
    document.getElementById('stat-matched').textContent = matchedCount + ' / ' + features.length;
    document.getElementById('stat-total').textContent = fmt(sumTotal);
    document.getElementById('stat-landlord').textContent = fmt(sumLandlord);
    document.getElementById('stat-tenant').textContent = fmt(sumTenant);
  }

  // ---- pan / zoom (viewBox-based; the map defaults to a crop around the
  // populated area since most of Ontario's land area has near-zero LTB
  // activity, but the full province is still reachable by zooming out) ----
  var fullView = { x: 0, y: 0, w: payload.width, h: payload.height };
  var view = { x: payload.focusView.x, y: payload.focusView.y, w: payload.focusView.width, h: payload.focusView.height };
  var MIN_W = fullView.w * 0.015;
  var MAX_W = fullView.w * 1.15;
  var dragStart = null;

  function applyView() {
    svg.setAttribute('viewBox', view.x.toFixed(1) + ' ' + view.y.toFixed(1) + ' ' + view.w.toFixed(1) + ' ' + view.h.toFixed(1));
  }
  function zoomAt(factor, cx, cy) {
    var newW = Math.max(MIN_W, Math.min(MAX_W, view.w * factor));
    var actualFactor = newW / view.w;
    var newH = view.h * actualFactor;
    var fx = (cx - view.x) / view.w, fy = (cy - view.y) / view.h;
    view.x = cx - fx * newW;
    view.y = cy - fy * newH;
    view.w = newW; view.h = newH;
    applyView();
  }
  function svgPointFromEvent(clientX, clientY) {
    var rect = svg.getBoundingClientRect();
    var mx = (clientX - rect.left) / rect.width, my = (clientY - rect.top) / rect.height;
    return { x: view.x + mx * view.w, y: view.y + my * view.h };
  }
  function hideZoomHint() {
    var hint = document.getElementById('zoom-hint');
    if (hint) hint.style.display = 'none';
  }

  applyView();

  svg.addEventListener('wheel', function (e) {
    e.preventDefault();
    hideZoomHint();
    var pt = svgPointFromEvent(e.clientX, e.clientY);
    zoomAt(e.deltaY < 0 ? 0.85 : 1 / 0.85, pt.x, pt.y);
  }, { passive: false });

  svg.addEventListener('mousedown', function (e) {
    if (e.button !== 0) return;
    dragStart = { x: e.clientX, y: e.clientY, viewX: view.x, viewY: view.y };
    wasDragged = false;
    svg.classList.add('grabbing');
  });
  window.addEventListener('mousemove', function (e) {
    if (!dragStart) return;
    var rect = svg.getBoundingClientRect();
    var dx = (e.clientX - dragStart.x) / rect.width * view.w;
    var dy = (e.clientY - dragStart.y) / rect.height * view.h;
    if (Math.abs(e.clientX - dragStart.x) > 3 || Math.abs(e.clientY - dragStart.y) > 3) {
      wasDragged = true;
      hideZoomHint();
      hideTooltip();
    }
    view.x = dragStart.viewX - dx;
    view.y = dragStart.viewY - dy;
    applyView();
  });
  window.addEventListener('mouseup', function () {
    dragStart = null;
    svg.classList.remove('grabbing');
  });

  var touchStart = null;
  svg.addEventListener('touchstart', function (e) {
    if (e.touches.length !== 1) return;
    var t = e.touches[0];
    touchStart = { x: t.clientX, y: t.clientY, viewX: view.x, viewY: view.y };
    wasDragged = false;
  }, { passive: true });
  svg.addEventListener('touchmove', function (e) {
    if (!touchStart || e.touches.length !== 1) return;
    e.preventDefault();
    var t = e.touches[0];
    var rect = svg.getBoundingClientRect();
    var dx = (t.clientX - touchStart.x) / rect.width * view.w;
    var dy = (t.clientY - touchStart.y) / rect.height * view.h;
    if (Math.abs(t.clientX - touchStart.x) > 3 || Math.abs(t.clientY - touchStart.y) > 3) { wasDragged = true; hideZoomHint(); }
    view.x = touchStart.viewX - dx;
    view.y = touchStart.viewY - dy;
    applyView();
  }, { passive: false });
  svg.addEventListener('touchend', function () { touchStart = null; });

  document.getElementById('zoom-in').addEventListener('click', function () {
    zoomAt(0.7, view.x + view.w / 2, view.y + view.h / 2);
  });
  document.getElementById('zoom-out').addEventListener('click', function () {
    zoomAt(1 / 0.7, view.x + view.w / 2, view.y + view.h / 2);
  });
  document.getElementById('zoom-reset').addEventListener('click', function () {
    view.x = payload.focusView.x; view.y = payload.focusView.y;
    view.w = payload.focusView.width; view.h = payload.focusView.height;
    applyView();
  });

  function wireToggle(id, key) {
    var group = document.getElementById(id);
    group.querySelectorAll('button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        group.querySelectorAll('button').forEach(function(b){ b.setAttribute('aria-pressed','false'); });
        btn.setAttribute('aria-pressed', 'true');
        state[key] = btn.dataset[key];
        render();
      });
    });
  }
  wireToggle('colormode-toggle', 'colormode');
  wireToggle('metric-toggle', 'metric');
  wireToggle('lens-toggle', 'lens');

  render();
})();
</script>
"""


def main():
    with open(PAYLOAD_PATH, encoding="utf-8") as f:
        payload_text = f.read()
    payload_text = payload_text.replace("</script", "<\\/script")

    import json
    with open(PAYLOAD_PATH, encoding="utf-8") as f:
        meta = json.load(f)

    html = TEMPLATE.replace("__WIDTH__", str(meta["width"])).replace("__HEIGHT__", str(meta["height"]))
    html = html.replace("__PAYLOAD__", payload_text)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
