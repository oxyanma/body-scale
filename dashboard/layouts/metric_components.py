"""Shared metric UI components.

Reusable ref-bar and expandable metric row for dashboard + composition.
"""
import base64
from dash import html
from i18n import t


# ── Color maps ──
STATUS_COLORS = {
    "success": "var(--green)", "primary": "var(--blue)",
    "warning": "var(--yellow)", "danger": "var(--red)", "info": "var(--purple)"
}
STATUS_BG = {
    "success": "var(--green-light)", "primary": "var(--blue-light)",
    "warning": "var(--yellow-light)", "danger": "var(--red-light)", "info": "var(--purple-light)"
}

# ── Zone colors for ref-bar segments ──
ZONE_COLORS = {
    "info": "#4A90D9",    # blue
    "success": "#2ECC71", # green
    "warning": "#F1C40F", # yellow
    "danger": "#E74C3C",  # red
    "primary": "#6C5CE7", # purple
}


def _ref_bar_position(value, bounds, bar_min=None, bar_max=None):
    """Calculate position (0-100%) of value on a reference bar.

    bounds = [b1, b2, b3] creating 4 zones
    bar spans from bar_min to bar_max (auto-calculated if not given)
    """
    if not bounds or len(bounds) < 2:
        return 50  # centered

    b_min = bar_min if bar_min is not None else bounds[0] * 0.65
    b_max = bar_max if bar_max is not None else bounds[-1] * 1.35

    if b_max == b_min:
        return 50

    pos = (value - b_min) / (b_max - b_min) * 100
    return max(2, min(98, pos))


def create_ref_bar(value, bounds, zone_labels, zone_colors_list):
    """Create a color reference bar with indicator.

    Args:
        value: current metric value
        bounds: [b1, b2, b3] — 3 thresholds creating 4 zones
        zone_labels: ["Low", "Normal", "High", "Obese"]
        zone_colors_list: ["info", "success", "warning", "danger"]
    """
    if not bounds or len(bounds) < 2:
        return ""

    # Calculate bar range and position
    b_min = bounds[0] * 0.65
    b_max = bounds[-1] * 1.35
    pos = _ref_bar_position(value, bounds, b_min, b_max)

    # Create segments with proportional widths
    total = b_max - b_min
    segments = []
    zone_starts = [b_min] + list(bounds) + [b_max]

    for i in range(len(zone_starts) - 1):
        width_pct = (zone_starts[i + 1] - zone_starts[i]) / total * 100
        color = ZONE_COLORS.get(
            zone_colors_list[i] if i < len(zone_colors_list) else "info",
            "#CCC"
        )

        segments.append(html.Div(
            style={
                "width": f"{width_pct:.1f}%", "height": "8px",
                "background": color, "display": "inline-block",
                "verticalAlign": "top",
            } | ({"borderRadius": "4px 0 0 4px"} if i == 0 else
                 {"borderRadius": "0 4px 4px 0"} if i == len(zone_starts) - 2 else {})
        ))

    # Zone labels
    labels = []
    for i, label in enumerate(zone_labels):
        if i < len(zone_starts) - 1:
            width_pct = (zone_starts[i + 1] - zone_starts[i]) / total * 100
            labels.append(html.Span(label, style={
                "width": f"{width_pct:.1f}%", "display": "inline-block",
                "textAlign": "center", "fontSize": "0.58rem",
                "color": "var(--text-muted)", "textTransform": "uppercase",
            }))

    return html.Div([
        # Bar with indicator
        html.Div([
            html.Div(segments, style={"display": "flex", "width": "100%"}),
            html.Div(style={
                "position": "absolute", "left": f"{pos}%",
                "top": "-2px", "width": "12px", "height": "12px",
                "borderRadius": "50%", "background": "var(--text-primary)",
                "border": "2px solid white",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
                "transform": "translateX(-50%)",
            }),
        ], style={
            "position": "relative", "marginTop": "8px",
            "borderRadius": "4px", "overflow": "visible",
        }),
        # Labels
        html.Div(labels, style={
            "display": "flex", "marginTop": "4px",
        }),
    ], style={"marginTop": "4px"})


# ── Zone label helper ──
def _get_zone_labels(key):
    """Get translated zone labels for a metric."""
    return [t(f"zone.{key}.1"), t(f"zone.{key}.2"), t(f"zone.{key}.3"), t(f"zone.{key}.4")]


# ── Zone colors by metric key ──
METRIC_ZONE_COLORS = {
    "weight":          ["info", "success", "warning", "danger"],
    "bmi":             ["info", "success", "warning", "danger"],
    "obesity_percent": ["info", "success", "warning", "danger"],
    "body_fat":        ["info", "success", "warning", "danger"],
    "visceral_fat":    ["success", "warning", "danger", "danger"],
    "subcutaneous_fat":["success", "warning", "danger", "danger"],
    "body_water":      ["info", "success", "warning", "danger"],
    "muscle_mass":     ["warning", "success", "primary", "info"],
    "smm_percent":     ["warning", "success", "primary", "info"],
    "smm":             ["warning", "success", "primary", "info"],
    "ffmi":            ["warning", "success", "primary", "info"],
    "smi":             ["danger", "warning", "success", "primary"],
    "bone_mass":       ["warning", "success", "primary", "info"],
    "protein":         ["warning", "success", "primary", "info"],
    "bmr":             ["warning", "success", "primary", "info"],
    "metabolic_age":   ["primary", "success", "warning", "danger"],
    "ideal_weight":    ["info", "success", "warning", "danger"],
    "body_score":      ["danger", "warning", "success", "primary"],
    "whr":             ["primary", "success", "warning", "danger"],
    "whtr":            ["info", "success", "warning", "danger"],
    "fat_mass":        ["info", "success", "warning", "danger"],
    "muscle_mass_kg":  ["warning", "success", "primary", "info"],
    "water_mass":      ["info", "success", "warning", "danger"],
    "lbm":             ["warning", "success", "primary", "info"],
}

# ── Unique SVG icon paths per metric (24x24 viewBox, stroke-based) ──
_C = "#9CA3AF"
METRIC_SVG = {
    # ★ Star
    "body_score": f'<polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" fill="{_C}" stroke="none"/>',
    # ⚖ Balance scale
    "bmi": f'<path d="M3 7l9-4 9 4"/><path d="M3 7c0 2.5 2 4.5 4.5 4.5S12 9.5 12 7"/><path d="M12 7c0 2.5 2 4.5 4.5 4.5S21 9.5 21 7"/><path d="M12 3v18"/><path d="M8 21h8"/>',
    # ◉ Gauge / speedometer
    "obesity_percent": f'<path d="M5.6 17A9 9 0 1 1 18.4 17"/><path d="M12 14l4-6"/><circle cx="12" cy="14" r="1.5" fill="{_C}" stroke="none"/>',
    # ⊕ Target / crosshair
    "ideal_weight": f'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="{_C}" stroke="none"/>',
    # ⏳ Hourglass
    "metabolic_age": '<path d="M5 3h14M5 21h14"/><path d="M7 3c0 5 5 7 5 9s-5 4-5 9"/><path d="M17 3c0 5-5 7-5 9s5 4 5 9"/>',
    # 🔥 Flame with inner flame
    "body_fat": '<path d="M12 22c-4 0-7-2.5-7-6.5C5 10.5 12 2 12 2s7 8.5 7 13.5c0 4-3 6.5-7 6.5z"/><path d="M10 16.5c0-2 2-4.5 2-4.5s2 2.5 2 4.5a2 2 0 0 1-4 0z"/>',
    # 💧 Droplet with horizontal line
    "fat_mass": '<path d="M12 2C12 2 5 10 5 15a7 7 0 0 0 14 0c0-5-7-13-7-13z"/><line x1="8.5" y1="16" x2="15.5" y2="16"/>',
    # 🛡 Shield with alert
    "visceral_fat": f'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="16" r="1" fill="{_C}" stroke="none"/>',
    # ≡ Stacked layers
    "subcutaneous_fat": '<path d="M12 2L2 7l10 5 10-5z"/><path d="M2 12l10 5 10-5"/><path d="M2 17l10 5 10-5"/>',
    # 🧍 Person silhouette
    "muscle_mass": '<circle cx="12" cy="5" r="3"/><path d="M6 21v-4a6 6 0 0 1 12 0v4"/>',
    # 🏋 Dumbbell
    "muscle_mass_kg": '<rect x="2" y="9" width="4" height="6" rx="1"/><rect x="18" y="9" width="4" height="6" rx="1"/><rect x="6" y="10.5" width="12" height="3" rx=".5"/>',
    # 📈 Activity pulse
    "smm_percent": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    # 🫙 Kettlebell
    "smm": '<path d="M8 8a4 4 0 0 1 8 0"/><rect x="6" y="11" width="12" height="8" rx="3"/><line x1="12" y1="8" x2="12" y2="11"/>',
    # 📊 Bar chart ascending
    "ffmi": '<path d="M18 20V10M14 20V14M10 20v-4M6 20v-2"/><path d="M4 22h16"/>',
    # 📋 Clipboard
    "smi": '<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="12" y2="15"/>',
    # ⊞ Grid / body composition
    "lbm": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 12h18"/><path d="M12 3v18"/>',
    # 💧 Droplet with wave
    "body_water": f'<path d="M12 2c0 0-7 8-7 12a7 7 0 0 0 14 0c0-4-7-12-7-12z"/><path d="M7.5 16c1.5-1 3-1 4.5 0s3 1 4.5 0"/>',
    # 🌊 Three waves
    "water_mass": '<path d="M2 7c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/><path d="M2 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/><path d="M2 17c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/>',
    # 🦴 Bone
    "bone_mass": f'<circle cx="9" cy="5" r="2"/><circle cx="15" cy="5" r="2"/><circle cx="9" cy="19" r="2"/><circle cx="15" cy="19" r="2"/><rect x="9" y="5" width="6" height="14" rx="2" fill="{_C}" stroke="none"/><circle cx="9" cy="5" r="2"/><circle cx="15" cy="5" r="2"/><circle cx="9" cy="19" r="2"/><circle cx="15" cy="19" r="2"/>',
    # ⬡ Hexagon molecule
    "protein": f'<path d="M12 2l6 3.5v5L12 14l-6-3.5v-5z"/><circle cx="12" cy="8" r="2" fill="{_C}" stroke="none"/><path d="M12 14v8"/><path d="M8 18h8"/>',
    # ⚡ Lightning bolt
    "bmr": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    # ⊙ Compass / waist measure
    "whr": f'<circle cx="12" cy="12" r="8"/><path d="M12 4v2M12 18v2M4 12h2M18 12h2"/><circle cx="12" cy="12" r="2" fill="{_C}" stroke="none"/>',
    # 📏 Vertical ruler
    "whtr": '<rect x="9" y="2" width="6" height="20" rx="1"/><line x1="9" y1="6" x2="12" y2="6"/><line x1="9" y1="10" x2="11" y2="10"/><line x1="9" y1="14" x2="12" y2="14"/><line x1="9" y1="18" x2="11" y2="18"/>',
    # ⚖ Weight scale
    "weight": f'<rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 14V9a5 5 0 0 1 10 0v5"/><circle cx="12" cy="17" r="1.5" fill="{_C}" stroke="none"/>',
}

# ── Metric name helper ──
def _get_metric_name(key):
    return t(f"metric.{key}")


def _make_icon_uri(key):
    """Build a data URI for the metric's SVG icon."""
    inner = METRIC_SVG.get(key, '<circle cx="12" cy="12" r="8"/>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        f'viewBox="0 0 24 24" fill="none" stroke="{_C}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}</svg>'
    )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


def create_metric_row(key, classification, is_missing=False, row_id_prefix="metric"):
    """Create a single expandable metric row with ref bar.

    Returns (row_div, detail_div) tuple.
    """
    icon_uri = _make_icon_uri(key)
    icon_el = html.Img(src=icon_uri, style={"width": "22px", "height": "22px"})

    if is_missing:
        val_str = "--"
        unit = ""
        name = _get_metric_name(key)
        label = t("metric.pending")
        txt_color = "var(--text-muted)"
        bg_color = "transparent"
        desc = t("metric.pending_desc")
        ref_bar = ""
        opacity = "0.5"
    else:
        c = classification
        val = c["value"]
        unit = c.get("unit", "")
        name = c["name"]
        label = c["label"]
        color_key = c.get("color", "info")
        desc = c.get("desc", "")
        bounds = c.get("bounds")

        txt_color = STATUS_COLORS.get(color_key, "var(--text-muted)")
        bg_color = STATUS_BG.get(color_key, "var(--purple-light)")

        # Format value with unit
        if isinstance(val, (float, int)):
            val_str = f"{val:.1f}"
        else:
            val_str = str(val)

        # Get zone info
        zone_labels = _get_zone_labels(key)
        zone_colors = METRIC_ZONE_COLORS.get(key, ["info", "success", "warning", "danger"])

        # Ref bar
        ref_bar = create_ref_bar(val, bounds, zone_labels, zone_colors) if bounds else ""
        opacity = "1"

    # Row (clickable)
    row = html.Div([
        html.Div(icon_el, className="metric-row-icon",
                 style={"background": "#F3F4F6", "padding": "0",
                        "display": "flex", "alignItems": "center", "justifyContent": "center"}),
        html.Div([
            html.Div(name, className="metric-row-name"),
            html.Span(label, style={
                "fontSize": "0.65rem", "fontWeight": "600", "padding": "2px 8px",
                "borderRadius": "8px", "color": txt_color, "background": bg_color,
            }),
        ], className="metric-row-info"),
        html.Div([
            html.Span(val_str, className="metric-row-number", style={"color": txt_color}),
            html.Span(unit, className="metric-row-unit") if unit else "",
        ], className="metric-row-value"),
        html.Span("▸", style={"color": "var(--text-muted)", "fontSize": "1rem", "marginLeft": "4px", "minWidth": "10px"}),
    ], className="metric-row", id={"type": f"{row_id_prefix}-row-click", "index": key}, style={"opacity": opacity})

    # Detail (hidden by default)
    detail = html.Div([
        html.P(desc, style={
            "fontSize": "0.78rem", "color": "var(--text-secondary)",
            "lineHeight": "1.4", "margin": "0 0 4px 0",
        }),
        ref_bar,
    ], className="metric-detail", id={"type": f"{row_id_prefix}-row-detail", "index": key},
       style={"display": "none", "padding": "8px 16px 12px", "background": "var(--bg-main)",
              "borderRadius": "0 0 12px 12px", "marginTop": "-4px", "marginBottom": "4px"})

    return row, detail
