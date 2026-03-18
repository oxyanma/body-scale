"""Comparison view — Side-by-side measurement comparison.

Layout inspired by the scale app's comparison screen:
badge temporal, 3 summary cards, ANTERIOR/ATUAL tabs, metric table.
"""
from dash import html, dcc
from database.db import SessionLocal
from database.models import User, Measurement
from calculations.body_composition import get_all_metrics, get_classifications

MONTHS_PT_SHORT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                   7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# Groups of (classification_key, display_name, higher_is_better)
COMPARE_GROUPS = {
    "Resumo": [
        ("weight_kg",      "Peso (Kg)",          False),
        ("bmi",            "IMC",                False),
        ("body_score",     "Pontuação Corporal", True),
        ("metabolic_age",  "Idade Metabólica",   False),
    ],
    "Gordura": [
        ("body_fat",       "Gordura (%)",        False),
        ("fat_mass",       "Peso Gordura (Kg)",  False),
        ("visceral_fat",   "Gordura Visceral",   False),
    ],
    "Muscular": [
        ("muscle_mass",    "Músculo (%)",        True),
        ("muscle_mass_kg", "Peso Músculo (Kg)",  True),
        ("smm",            "SMM (Kg)",           True),
        ("ffmi",           "FFMI",               True),
        ("lbm",            "LBM (Kg)",           True),
    ],
    "Composição": [
        ("body_water",     "Água (%)",           True),
        ("water_mass",     "Peso Água (Kg)",     True),
        ("bone_mass",      "Massa Óssea (Kg)",   True),
        ("protein",        "Proteína (%)",       True),
        ("bmr",            "TMB (kcal)",         True),
    ],
}


def _format_date(dt):
    if not dt:
        return "--"
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year}\n{dt.hour:02d}:{dt.minute:02d}"


def _delta_color(diff, higher_is_better):
    if diff == 0:
        return "var(--text-muted)"
    improved = (diff > 0) if higher_is_better else (diff < 0)
    return "var(--green)" if improved else "var(--red)"


def _format_val(v, key):
    if v is None:
        return "--"
    if isinstance(v, float):
        if key in ("metabolic_age", "body_score", "visceral_fat"):
            return f"{v:.0f}"
        return f"{v:.1f}"
    return str(v)


def _format_diff(diff, key):
    if diff == 0:
        return "="
    sign = "+" if diff > 0 else ""
    if key in ("metabolic_age", "body_score", "visceral_fat"):
        return f"{sign}{diff:.0f}"
    return f"{sign}{diff:.1f}"


def create_comparison_view(id_a=None, id_b=None):
    if not id_a or not id_b:
        return html.Div([
            html.Div([
                dcc.Link(html.Button("‹", className="back-btn"), href="/historico"),
                html.H1("Comparar Medições"),
            ], className="page-header"),
            html.Div([
                html.P("Selecione 2 medições no histórico para comparar.",
                       style={"textAlign": "center", "padding": "40px 0", "color": "var(--text-secondary)"}),
                dcc.Link("← Voltar ao Histórico", href="/historico",
                         style={"display": "block", "textAlign": "center", "color": "var(--blue)", "fontWeight": "600"})
            ], className="health-card")
        ])

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_active == True).first()
        m_a = db.query(Measurement).filter(Measurement.id == int(id_a)).first()
        m_b = db.query(Measurement).filter(Measurement.id == int(id_b)).first()

        if not m_a or not m_b or not user:
            return html.Div([
                html.Div([
                    dcc.Link(html.Button("‹", className="back-btn"), href="/historico"),
                    html.H1("Comparar Medições"),
                ], className="page-header"),
                html.Div("Medições não encontradas.", className="health-card",
                         style={"textAlign": "center", "padding": "24px"})
            ])

        # Ensure m_a is the newer (ATUAL), m_b is the older (ANTERIOR)
        if m_b.measured_at > m_a.measured_at:
            m_a, m_b = m_b, m_a

        # Calculate metrics
        try:
            metrics_a = get_all_metrics(m_a.weight_kg, user.height_cm, user.age, user.sex,
                                         m_a.impedance, user.activity_level,
                                         waist_cm=user.waist_cm, hip_cm=user.hip_cm)
            class_a = get_classifications(metrics_a, user.sex, user.age, user.height_cm)
        except Exception:
            metrics_a, class_a = {}, {}

        try:
            metrics_b = get_all_metrics(m_b.weight_kg, user.height_cm, user.age, user.sex,
                                         m_b.impedance, user.activity_level,
                                         waist_cm=user.waist_cm, hip_cm=user.hip_cm)
            class_b = get_classifications(metrics_b, user.sex, user.age, user.height_cm)
        except Exception:
            metrics_b, class_b = {}, {}
    finally:
        db.close()

    # ── Header ──
    header = html.Div([
        dcc.Link(html.Button("‹", className="back-btn"), href="/historico"),
        html.H1("Comparar Medições"),
        html.Button([
            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8'/%3E%3Cpolyline points='16 6 12 2 8 6'/%3E%3Cline x1='12' y1='2' x2='12' y2='15'/%3E%3C/svg%3E",
                     className="export-icon"),
            html.Div(className="export-spinner"),
        ], className="btn-export", **{"data-filename": "comparacao"}),
    ], className="page-header")

    # ── Time Badge ──
    days_diff = abs((m_a.measured_at - m_b.measured_at).days)
    if days_diff == 0:
        badge_text = "Mesmo dia"
    elif days_diff == 1:
        badge_text = "1 Dia"
    else:
        badge_text = f"{days_diff} Dias"

    time_badge = html.Div([
        html.Span("Dentro de ", style={"fontWeight": "400"}),
        html.Span(badge_text, style={"fontWeight": "800"}),
    ], className="compare-badge")

    # ── Summary Cards (3 key metrics) ──
    w_diff = round(m_a.weight_kg - m_b.weight_kg, 1)
    bmi_a = class_a.get("bmi", {}).get("value", 0)
    bmi_b = class_b.get("bmi", {}).get("value", 0)
    bmi_diff = round(bmi_a - bmi_b, 1) if bmi_a and bmi_b else 0
    bf_a = class_a.get("body_fat", {}).get("value", 0)
    bf_b = class_b.get("body_fat", {}).get("value", 0)
    bf_diff = round(bf_a - bf_b, 1) if bf_a and bf_b else 0

    def _summary_card(icon_svg, value, label, higher_is_better):
        if value == 0:
            val_str = "="
            color = "var(--text-muted)"
        else:
            sign = "+" if value > 0 else ""
            val_str = f"{sign}{value:.1f}"
            improved = (value > 0) if higher_is_better else (value < 0)
            color = "var(--green)" if improved else "var(--red)"

        return html.Div([
            html.Div(icon_svg, className="compare-summary-icon"),
            html.Div(val_str, className="compare-summary-value", style={"color": color}),
            html.Div(label, className="compare-summary-label"),
        ], style={"textAlign": "center", "flex": "1"})

    summary = html.Div([
        _summary_card("⚖️", w_diff, "PESO (KG)", False),
        _summary_card("📊", bmi_diff, "IMC", False),
        _summary_card("⚡", bf_diff, "GORDURA\nCORPORAL %", False),
    ], className="compare-summary")

    # ── Tabs ANTERIOR / ATUAL ──
    date_b = _format_date(m_b.measured_at).replace("\n", " ")
    date_a = _format_date(m_a.measured_at).replace("\n", " ")

    tabs = html.Div([
        html.Div("ANTERIOR", className="compare-tab before"),
        html.Div("ATUAL", className="compare-tab after"),
    ], className="compare-tabs")

    # ── Table Header ──
    table_header = html.Div([
        html.Div(date_b, style={
            "flex": "1", "textAlign": "center", "fontSize": "0.68rem",
            "color": "var(--text-muted)", "lineHeight": "1.3"}),
        html.Div("MUDANÇA", style={
            "flex": "1.2", "textAlign": "center", "fontSize": "0.68rem",
            "color": "var(--text-muted)", "fontWeight": "600", "textTransform": "uppercase"}),
        html.Div(date_a, style={
            "flex": "1", "textAlign": "center", "fontSize": "0.68rem",
            "color": "var(--text-muted)", "lineHeight": "1.3"}),
    ], style={"display": "flex", "padding": "10px 16px",
              "borderBottom": "2px solid var(--border-light)"})

    # ── Metric Rows by Group ──
    all_items = []
    for gi, (group_name, metrics_list) in enumerate(COMPARE_GROUPS.items()):
        group_rows = []
        for key, name, higher_is_better in metrics_list:
            # Special handling for weight (not in classifications)
            if key == "weight_kg":
                va = m_a.weight_kg
                vb = m_b.weight_kg
            elif key in class_a and key in class_b:
                va = class_a[key].get("value")
                vb = class_b[key].get("value")
            else:
                continue

            if va is None and vb is None:
                continue

            diff = round((va or 0) - (vb or 0), 2)
            dc = _delta_color(diff, higher_is_better)

            group_rows.append(html.Div([
                # Left value (ANTERIOR / older)
                html.Div(_format_val(vb, key), className="compare-cell-value",
                         style={"flex": "1", "textAlign": "center"}),
                # Center: metric name + delta
                html.Div([
                    html.Div(name, className="compare-metric-name"),
                    html.Div(_format_diff(diff, key), className="compare-metric-delta",
                             style={"color": dc}),
                ], style={"flex": "1.2", "textAlign": "center"}),
                # Right value (ATUAL / newer)
                html.Div(_format_val(va, key), className="compare-cell-value",
                         style={"flex": "1", "textAlign": "center"}),
            ], className="compare-row"))

        if group_rows:
            all_items.append(html.Div(group_name.upper(), className="section-label", style={
                "padding": "12px 16px 6px",
                "borderTop": "1px solid var(--border-light)" if gi > 0 else "none",
                "marginTop": "4px" if gi > 0 else "0",
            }))
            all_items.extend(group_rows)

    # ── Assemble ──
    card = html.Div([
        time_badge,
        summary,
        tabs,
        table_header,
        *all_items,
    ], className="compare-card")

    return html.Div([header, card])
