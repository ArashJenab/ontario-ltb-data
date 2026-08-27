# -*- coding: utf-8 -*-
"""
Inline SVG chart builders for the site pages.

These render to SVG rather than PNG so a figure follows the reader's light or
dark theme: every colour is a CSS custom property resolved by the page, which
a raster image cannot do. They are also crisp at any zoom, which matters for
the print one-pager.

Conventions held across every chart here:

  * horizontal bars for ranked categories, because the labels are sentences
    ("Breached a settlement or order") and horizontal is the only orientation
    that can set them as running text
  * hairline recessive grid, no dashes, no chart junk, no border around marks
  * 4px rounded bar ends anchored to the baseline, a 2px surface gap between
    adjacent fills
  * a legend whenever two or more series are present, and direct value labels
    on every bar, so identity is never carried by colour alone - which is also
    what the aqua slot's sub-3:1 contrast on the light surface obliges
  * a native <title> on each mark, so there is a hover tooltip without script

Text is measured rather than hoped for: labels are truncated to their
allowance and the right margin is reserved from the widest value label, so
nothing can overrun the box. scripts/check_pages.py re-checks that in a real
browser, because the estimate here is only an estimate.

Pass real characters, not HTML entities: this module escapes its input, so
"&middot;" would render literally. Use "·".
"""
import html

# viewBox width every chart is authored against; the SVG then scales to its
# container. Font sizes below are in these units.
W = 720
BAR_RADIUS = 4
GAP = 2  # surface gap between adjacent fills

LABEL_SIZE = 12.5
VALUE_SIZE = 12.5
LEGEND_SIZE = 12

# Approximate advance width per character as a fraction of font size, for the
# UI sans stack these charts render in.
CHAR_W = 0.545


def esc(text):
    return html.escape(str(text), quote=True)


def text_width(text, size):
    return len(str(text)) * size * CHAR_W


def fit(text, width, size):
    """Truncate to fit `width`, with an ellipsis."""
    text = str(text)
    if text_width(text, size) <= width:
        return text
    budget = max(1, int(width / (size * CHAR_W)) - 1)
    return text[:budget].rstrip(" ,.-") + "…"


def _open(width, height, label):
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(label)}" '
        f'preserveAspectRatio="xMinYMin meet">'
    )


def _label(x, y, text, allowance, full=None):
    """Right-aligned category label, truncated to its allowance."""
    shown = fit(text, allowance, LABEL_SIZE)
    title = (
        f"<title>{esc(full or text)}</title>" if shown != text else ""
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="c-label" text-anchor="end">'
        f"{esc(shown)}{title}</text>"
    )


def _legend(series, x, y, max_x=None):
    """Wraps to further rows rather than overrunning. -> (svg, rows_used)."""
    max_x = max_x or W
    parts = []
    cursor, row = x, 0
    for label, var in series:
        entry = 15 + text_width(label, LEGEND_SIZE) + 20
        if cursor + entry > max_x and cursor > x:
            row += 1
            cursor = x
        ly = y + row * 16
        parts.append(
            f'<rect x="{cursor:.1f}" y="{ly - 8}" width="10" height="10" rx="2" '
            f'fill="var({var})"/>'
        )
        parts.append(
            f'<text x="{cursor + 15:.1f}" y="{ly}" class="c-legend">{esc(label)}</text>'
        )
        cursor += entry
    return "".join(parts), row + 1


def _value_margin(displays):
    """Right margin wide enough for the longest value label, plus slack."""
    widest = max((text_width(d, VALUE_SIZE) for d in displays), default=0)
    return widest + 14


def hbar(rows, label_width=250, bar_height=22, row_gap=10, max_value=None,
         title=None, footnote=None, chart_label="Bar chart"):
    """One series of horizontal bars.

    rows: [{"label", "value", "display", "color" (css var name)}]
    """
    top = 8 if not title else 30
    height = top + len(rows) * (bar_height + row_gap) + (26 if footnote else 8)
    plot_x = label_width
    margin = _value_margin([r.get("display", r["value"]) for r in rows])
    plot_w = max(60.0, W - label_width - margin)
    top_value = max_value or max((r["value"] for r in rows), default=1) or 1
    allowance = label_width - 12

    out = [_open(W, height, chart_label)]
    if title:
        out.append(f'<text x="1" y="16" class="c-title">{esc(title)}</text>')

    y = top
    for row in rows:
        colour = row.get("color", "--series-1")
        width = max(2.0, plot_w * (row["value"] / top_value))
        mid = y + bar_height / 2 + 4
        display = row.get("display", row["value"])
        out.append(_label(plot_x - 10, mid, row["label"], allowance))
        out.append(
            f'<rect x="{plot_x}" y="{y}" width="{width:.1f}" height="{bar_height}" '
            f'rx="{BAR_RADIUS}" fill="var({colour})">'
            f'<title>{esc(row["label"])}: {esc(display)}</title></rect>'
        )
        out.append(
            f'<text x="{plot_x + width + 8:.1f}" y="{mid:.1f}" class="c-value">'
            f"{esc(display)}</text>"
        )
        y += bar_height + row_gap

    if footnote:
        out.append(f'<text x="1" y="{height - 8}" class="c-note">{esc(footnote)}</text>')
    out.append("</svg>")
    return "".join(out)


def grouped_hbar(rows, series, label_width=250, bar_height=16, row_gap=16,
                 title=None, footnote=None, chart_label="Grouped bar chart"):
    """Two or more series per category, stacked within the category band.

    rows:   [{"label", "values": [...], "displays": [...]}]
    series: [(series label, css var)]
    """
    margin = _value_margin([d for r in rows for d in r["displays"]])
    plot_x = label_width
    plot_w = max(60.0, W - label_width - margin)
    legend_svg, legend_rows = _legend(series, plot_x, (26 if not title else 46) - 12, W)
    top = (26 if not title else 46) + (legend_rows - 1) * 16
    band = len(series) * bar_height + (len(series) - 1) * GAP
    height = top + len(rows) * (band + row_gap) + (26 if footnote else 10)
    top_value = max((max(r["values"]) for r in rows), default=1) or 1
    allowance = label_width - 12

    out = [_open(W, height, chart_label)]
    if title:
        out.append(f'<text x="1" y="16" class="c-title">{esc(title)}</text>')
    out.append(legend_svg)

    y = top
    for row in rows:
        out.append(_label(plot_x - 10, y + band / 2 + 4, row["label"], allowance))
        for i, (series_label, var) in enumerate(series):
            value = row["values"][i]
            width = max(2.0, plot_w * (value / top_value))
            by = y + i * (bar_height + GAP)
            display = row["displays"][i]
            out.append(
                f'<rect x="{plot_x}" y="{by:.1f}" width="{width:.1f}" '
                f'height="{bar_height}" rx="{BAR_RADIUS}" fill="var({var})">'
                f'<title>{esc(row["label"])}, {esc(series_label)}: '
                f"{esc(display)}</title></rect>"
            )
            out.append(
                f'<text x="{plot_x + width + 8:.1f}" y="{by + bar_height - 3:.1f}" '
                f'class="c-value">{esc(display)}</text>'
            )
        y += band + row_gap

    if footnote:
        out.append(f'<text x="1" y="{height - 8}" class="c-note">{esc(footnote)}</text>')
    out.append("</svg>")
    return "".join(out)


def split_bar(rows, series, label_width=250, bar_height=24, row_gap=12,
              title=None, footnote=None, chart_label="Composition bar chart"):
    """One 100%-wide bar per row, split into segments summing to 100."""
    plot_x = label_width
    plot_w = W - label_width - 16
    legend_svg, legend_rows = _legend(series, plot_x, (26 if not title else 46) - 12, W)
    top = (26 if not title else 46) + (legend_rows - 1) * 16
    height = top + len(rows) * (bar_height + row_gap) + (26 if footnote else 10)
    allowance = label_width - 12

    out = [_open(W, height, chart_label)]
    if title:
        out.append(f'<text x="1" y="16" class="c-title">{esc(title)}</text>')
    out.append(legend_svg)

    y = top
    for row in rows:
        out.append(_label(plot_x - 10, y + bar_height / 2 + 4, row["label"], allowance))
        cursor = plot_x
        for i, (series_label, var) in enumerate(series):
            value = row["values"][i]
            width = plot_w * value / 100.0
            draw = max(0.0, width - (GAP if i < len(series) - 1 else 0))
            out.append(
                f'<rect x="{cursor:.1f}" y="{y}" width="{draw:.1f}" '
                f'height="{bar_height}" rx="{BAR_RADIUS}" fill="var({var})">'
                f'<title>{esc(row["label"])}, {esc(series_label)}: '
                f"{value:.1f}%</title></rect>"
            )
            if draw > 40:
                out.append(
                    f'<text x="{cursor + draw / 2:.1f}" y="{y + bar_height / 2 + 4}" '
                    f'class="c-inbar" text-anchor="middle">{value:.0f}%</text>'
                )
            cursor += width
        y += bar_height + row_gap

    if footnote:
        out.append(f'<text x="1" y="{height - 8}" class="c-note">{esc(footnote)}</text>')
    out.append("</svg>")
    return "".join(out)


def scatter(points, x_label, y_label, height=340, title=None, footnote=None,
            highlight=None, chart_label="Scatter plot"):
    """points: [{"x","y","label"}]; highlight: labels to emphasise and name."""
    left, right = 74, 22
    top = 34 if title else 14
    bottom = 50
    plot_w = W - left - right
    plot_h = height - top - bottom
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_max = max(ys)
    x_range = (x_max - x_min) or 1
    y_range = y_max or 1

    def px(x):
        return left + plot_w * (x - x_min) / x_range

    def py(y):
        return top + plot_h - plot_h * y / y_range

    out = [_open(W, height, chart_label)]
    if title:
        out.append(f'<text x="1" y="16" class="c-title">{esc(title)}</text>')

    for i in range(5):
        gy = top + plot_h * i / 4
        value = y_max - (y_range * i / 4)
        out.append(
            f'<line x1="{left}" y1="{gy:.1f}" x2="{W - right}" y2="{gy:.1f}" class="c-grid"/>'
        )
        out.append(
            f'<text x="{left - 8}" y="{gy + 4:.1f}" class="c-axis" '
            f'text-anchor="end">{value:.2f}</text>'
        )
    for i in range(5):
        gx = left + plot_w * i / 4
        value = x_min + (x_range * i / 4)
        anchor = "start" if i == 0 else ("end" if i == 4 else "middle")
        out.append(
            f'<text x="{gx:.1f}" y="{height - 28}" class="c-axis" '
            f'text-anchor="{anchor}">${value / 1000:.0f}k</text>'
        )

    highlight = highlight or set()
    for point in points:
        is_key = point["label"] in highlight
        cx, cy = px(point["x"]), py(point["y"])
        out.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{5 if is_key else 3.4}" '
            f'fill="var({"--series-2" if is_key else "--series-1"})" '
            f'fill-opacity="{1 if is_key else 0.42}">'
            f'<title>{esc(point["label"])}: {point["y"]:.3f} tenant cases per '
            f'landlord case, median income ${point["x"]:,.0f}</title></circle>'
        )
        if is_key:
            # Keep the callout inside the box: flip it left near the right edge.
            width = text_width(point["label"], 11.5)
            if cx + 9 + width > W - right:
                out.append(
                    f'<text x="{cx - 9:.1f}" y="{cy + 4:.1f}" class="c-point" '
                    f'text-anchor="end">{esc(point["label"])}</text>'
                )
            else:
                out.append(
                    f'<text x="{cx + 9:.1f}" y="{cy + 4:.1f}" class="c-point">'
                    f'{esc(point["label"])}</text>'
                )

    out.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 8}" class="c-axistitle" '
        f'text-anchor="middle">{esc(x_label)}</text>'
    )
    # Rotated about its own anchor so the glyphs stay inside the viewBox.
    cy = top + plot_h / 2
    out.append(
        f'<text x="14" y="{cy:.1f}" class="c-axistitle" text-anchor="middle" '
        f'transform="rotate(-90 14 {cy:.1f})">{esc(y_label)}</text>'
    )
    if footnote:
        out.append(f'<text x="1" y="{height - 38}" class="c-note">{esc(footnote)}</text>')
    out.append("</svg>")
    return "".join(out)


CHART_CSS = """
.chart { width: 100%; height: auto; display: block; }
.c-title { font-size: 13px; font-weight: 700; fill: var(--ink); }
.c-label { font-size: 12.5px; fill: var(--ink-muted); }
.c-value { font-size: 12.5px; font-weight: 700; fill: var(--ink);
           font-variant-numeric: tabular-nums; }
.c-inbar { font-size: 11.5px; font-weight: 700; fill: #ffffff; }
.c-legend { font-size: 12px; fill: var(--ink-muted); }
.c-note { font-size: 11.5px; fill: var(--ink-faint); }
.c-axis { font-size: 11px; fill: var(--ink-faint); font-variant-numeric: tabular-nums; }
.c-axistitle { font-size: 11.5px; fill: var(--ink-muted); }
.c-point { font-size: 11.5px; font-weight: 700; fill: var(--ink); }
.c-grid { stroke: var(--grid); stroke-width: 1; }
.chart rect, .chart circle { transition: fill-opacity .12s ease; }
.chart rect:hover, .chart circle:hover { fill-opacity: .82; }
"""


def paired_rows(rows, series, label_width=210, bar_height=15, row_gap=17,
                title=None, chart_label="Paired comparison"):
    """Two values per row, each ROW scaled to its own maximum.

    For comparing the same two entities across measures that do not share a
    unit (months, dollars, percentages). Putting those on one axis is the
    dual-axis mistake in another guise: the smallest-unit measure becomes an
    invisible sliver against the largest. Here each row is its own scale, every
    bar is directly labelled, and no shared axis is drawn, so nothing invites a
    cross-row comparison of lengths.

    rows: [{"label", "values": [a, b], "displays": [da, db]}]
    """
    margin = _value_margin([d for r in rows for d in r["displays"]])
    plot_x = label_width
    plot_w = max(60.0, W - label_width - margin)
    legend_svg, legend_rows = _legend(series, plot_x, (26 if not title else 46) - 12, W)
    top = (26 if not title else 46) + (legend_rows - 1) * 16
    band = len(series) * bar_height + (len(series) - 1) * GAP
    height = top + len(rows) * (band + row_gap) + 24
    allowance = label_width - 12

    out = [_open(W, height, chart_label)]
    if title:
        out.append(f'<text x="1" y="16" class="c-title">{esc(title)}</text>')
    out.append(legend_svg)

    y = top
    for row in rows:
        row_max = max(row["values"]) or 1
        out.append(_label(plot_x - 10, y + band / 2 + 4, row["label"], allowance))
        for i, (series_label, var) in enumerate(series):
            value = row["values"][i]
            width = max(2.0, plot_w * (value / row_max))
            by = y + i * (bar_height + GAP)
            display = row["displays"][i]
            out.append(
                f'<rect x="{plot_x}" y="{by:.1f}" width="{width:.1f}" '
                f'height="{bar_height}" rx="{BAR_RADIUS}" fill="var({var})">'
                f'<title>{esc(row["label"])}, {esc(series_label)}: '
                f"{esc(display)}</title></rect>"
            )
            out.append(
                f'<text x="{plot_x + width + 8:.1f}" y="{by + bar_height - 2:.1f}" '
                f'class="c-value">{esc(display)}</text>'
            )
        y += band + row_gap

    out.append(
        f'<text x="1" y="{height - 6}" class="c-note">'
        "Each row is scaled to its own largest value; the rows use different units "
        "and are not comparable to each other.</text>"
    )
    out.append("</svg>")
    return "".join(out)
