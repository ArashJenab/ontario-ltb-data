# -*- coding: utf-8 -*-
"""
One palette and one chart style for every figure on the site.

The three categorical hues are slots 1, 2 and 3 of a palette validated for
colour-vision deficiency: run

    node validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all

and the dark steps "#3987e5,#d95926,#199e70" against the dark surface. Both
pass the lightness band, chroma floor, CVD separation (worst all-pairs dE 9.2
light / 9.4 dark), and normal-vision floor. Aqua sits at 2.74:1 on the light
surface, below the 3:1 bar, so every chart that uses it ships visible direct
labels or a table view rather than relying on the fill alone.

Semantics held constant across the whole site, because a reader who learns a
colour on the map must not have to relearn it on the report:

    blue    landlord side; and, where the landlord side is split, the
            INDIVIDUAL owner (the party this analysis is most often about)
    orange  tenant side
    aqua    CORPORATE / institutional landlord

Colour follows the party, never the rank, so re-sorting a chart never
repaints it.
"""

# Light-mode steps.
LANDLORD = "#2a78d6"
TENANT = "#eb6834"
CORPORATE = "#1baf7a"
INDIVIDUAL = LANDLORD

# Dark-mode steps, chosen for the dark surface rather than lightened.
DARK = {
    LANDLORD: "#3987e5",
    TENANT: "#d95926",
    CORPORATE: "#199e70",
}

# Single-hue sequential ramp (blue), light -> dark, for magnitude encoding.
SEQUENTIAL = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]

# Diverging pair for "above / below the provincial figure": warm and cool
# poles with a neutral grey midpoint, never a hue in the middle.
DIVERGING_LOW = "#2a78d6"
DIVERGING_MID_LIGHT = "#f0efec"
DIVERGING_MID_DARK = "#383835"
DIVERGING_HIGH = "#e34948"

# Ink and surface tokens. Text always wears an ink token, never a series hue.
LIGHT = {
    "surface": "#ffffff",
    "surface_alt": "#f7f8fb",
    "ink": "#1a2130",
    "ink_muted": "#5c6675",
    "ink_faint": "#8b93a1",
    "grid": "#e4e8ee",
}
DARKTOKENS = {
    "surface": "#171c25",
    "surface_alt": "#12161d",
    "ink": "#e8ecf3",
    "ink_muted": "#9aa4b4",
    "ink_faint": "#6b7484",
    "grid": "#262d3a",
}

FONT_STACK = [
    "Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans", "sans-serif",
]


def apply_matplotlib_style(dark=False):
    """Style matplotlib to match the site: thin marks, hairline recessive grid.

    Used for the PNG copies kept under results/ as reproducibility artifacts.
    The figures shown on the site itself are inline SVG so they can follow the
    reader's theme, which a PNG cannot.
    """
    import matplotlib as mpl

    tokens = DARKTOKENS if dark else LIGHT
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FONT_STACK,
            "figure.facecolor": tokens["surface"],
            "axes.facecolor": tokens["surface"],
            "savefig.facecolor": tokens["surface"],
            "text.color": tokens["ink"],
            "axes.labelcolor": tokens["ink_muted"],
            "axes.edgecolor": tokens["grid"],
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.grid.axis": "x",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "grid.color": tokens["grid"],
            "grid.linewidth": 0.8,
            "grid.linestyle": "-",
            "xtick.color": tokens["ink_faint"],
            "ytick.color": tokens["ink_muted"],
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlecolor": tokens["ink"],
            "axes.titlelocation": "left",
            "axes.titlepad": 14,
            "legend.frameon": False,
            "legend.fontsize": 10,
            "figure.dpi": 150,
        }
    )


def fmt_money(value, precision=0):
    """$1,234 / $1.2M / $130M, whichever reads best at that magnitude."""
    value = float(value)
    if abs(value) >= 1e9:
        return f"${value / 1e9:.1f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.1f}M"
    if abs(value) >= 1e5:
        return f"${value / 1e3:.0f}K"
    return f"${value:,.{precision}f}"


def fmt_count(value):
    return f"{value:,.0f}"


def fmt_pct(value, precision=1):
    return f"{value:.{precision}f}%"
