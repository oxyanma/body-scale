"""Composition view — Full metric list with expandable rows.

Follows stitch ref: weight card + BMI bar at top, then list of all metrics
as rows with icon + name + status + value. Clicking a row expands detail.
"""
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from database.db import SessionLocal
from database.models import User, Measurement
from calculations.body_composition import get_classifications, get_all_metrics

MONTHS_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
             7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}





def _bmi_position(bmi):
    if bmi < 15: return 0
    if bmi > 40: return 100
    return ((bmi - 15) / 25) * 100


def _bmi_status(bmi):
    if bmi < 18.5: return "Abaixo do peso", "low"
    if bmi < 25: return "Normal", "normal"
    if bmi < 30: return "Sobrepeso", "high"
    return "Obeso", "obese"


def _status_class(color):
    mapping = {"success": "status-success", "primary": "status-primary",
               "warning": "status-warning", "danger": "status-danger",
               "info": "status-info"}
    return mapping.get(color, "status-info")


def create_composition_view(measurement_id=None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            return html.Div("Nenhum perfil encontrado.")

        if measurement_id:
            m = db.query(Measurement).filter(Measurement.id == int(measurement_id)).first()
        else:
            m = db.query(Measurement).filter(Measurement.user_id == user.id).order_by(Measurement.measured_at.desc()).first()

        prev = None
        if m:
            prev = db.query(Measurement).filter(
                Measurement.user_id == user.id,
                Measurement.measured_at < m.measured_at
            ).order_by(Measurement.measured_at.desc()).first()

        if not m:
            return html.Div([
                html.Div([
                    dcc.Link(html.Button("‹", className="back-btn"), href="/"),
                    html.H1("Composição Corporal"),
                ], className="page-header"),
                html.Div([
                    html.P("Nenhuma medição encontrada.", style={"textAlign": "center", "padding": "40px 0", "color": "var(--text-secondary)"}),
                    dcc.Link("← Pesar agora", href="/", style={"display": "block", "textAlign": "center", "color": "var(--blue)", "fontWeight": "600"})
                ], className="health-card")
            ])

        # Get classifications
        metrics = get_all_metrics(
            m.weight_kg, user.height_cm, user.age, user.sex,
            m.impedance, user.activity_level,
            waist_cm=user.waist_cm, hip_cm=user.hip_cm
        )
        classifications = get_classifications(metrics, user.sex, user.age, user.height_cm)

    finally:
        db.close()

    dt = m.measured_at
    date_str = f"{dt.day:02d} de {MONTHS_PT.get(dt.month, '')} de {dt.year}, {dt.hour:02d}:{dt.minute:02d}"
    bmi_val = m.bmi or 0
    bmi_label, bmi_class = _bmi_status(bmi_val)
    bmi_pos = _bmi_position(bmi_val)
    delta_w = round(m.weight_kg - prev.weight_kg, 2) if prev else None

    # ── Page Header ──
    header = html.Div([
        dcc.Link(html.Button("‹", className="back-btn"), href="/"),
        html.Div([
            html.H1("Composição Corporal"),
            html.Span(date_str, className="header-subtitle"),
        ], style={"flex": "1"}),
        html.Button([
            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8'/%3E%3Cpolyline points='16 6 12 2 8 6'/%3E%3Cline x1='12' y1='2' x2='12' y2='15'/%3E%3C/svg%3E",
                     className="export-icon"),
            html.Div(className="export-spinner"),
        ], className="btn-export", **{"data-filename": "composicao"}),
    ], className="page-header")

    # ── Weight Card ──
    weight_card = html.Div([
        html.Div("PESO ATUAL", style={"fontSize": "0.72rem", "fontWeight": "600", "color": "var(--text-label)", "textTransform": "uppercase", "letterSpacing": "0.08em"}),
        html.Div([
            html.Div([
                html.Span(f"{m.weight_kg:.2f}", style={"fontFamily": "'Nunito'", "fontSize": "2.8rem", "fontWeight": "800", "color": "var(--text-primary)"}),
                html.Span(" kg", style={"fontSize": "1rem", "color": "var(--text-muted)"}),
            ]),
            html.Div([
                html.Div("vs. Anterior", style={"fontSize": "0.68rem", "color": "var(--text-muted)"}),
                html.Div(
                    f"{'+'if delta_w and delta_w>0 else ''}{delta_w:.1f}" if delta_w and delta_w != 0 else "=",
                    style={"fontFamily": "'Nunito'", "fontSize": "1.3rem", "fontWeight": "800",
                           "color": "var(--red)" if delta_w and delta_w > 0 else "var(--green)" if delta_w and delta_w < 0 else "var(--text-muted)"}),
            ], style={"textAlign": "right"}) if prev else "",
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end"}),

        # BMI bar
        html.Div([
            html.Div([
                html.Span("BAIXO"), html.Span("IDEAL"), html.Span("ALTO"), html.Span("OBESO")
            ], className="bmi-labels"),
            html.Div([
                html.Div(className="bmi-indicator", style={"left": f"{bmi_pos}%"})
            ], className="bmi-bar"),
        ], className="bmi-bar-container"),
        html.P(bmi_label, style={"color": "var(--green)" if bmi_class == "normal" else "var(--blue)" if bmi_class == "low" else "var(--yellow)" if bmi_class == "high" else "var(--red)",
                                  "fontSize": "0.82rem", "fontWeight": "600", "marginTop": "4px"}),
    ], className="health-card")

    # ── Metric Groups ──
    from dashboard.layouts.metric_components import create_metric_row
    
    METRIC_GROUPS = {
        "Resumo Geral": ["body_score", "bmi", "obesity_percent", "ideal_weight", "metabolic_age"],
        "Índices de Gordura": ["body_fat", "fat_mass", "visceral_fat", "subcutaneous_fat"],
        "Índices Musculares": ["muscle_mass", "muscle_mass_kg", "smm_percent", "smm", "ffmi", "smi", "lbm"],
        "Composição e Outros": ["body_water", "water_mass", "bone_mass", "protein", "bmr", "whr", "whtr"]
    }
    
    all_items = []
    for i, (group_name, keys) in enumerate(METRIC_GROUPS.items()):
        all_items.append(html.Div(group_name.upper(), className="section-label", style={
            "padding": "16px 20px 8px",
            "borderTop": "1px solid var(--border-light)" if i > 0 else "none",
            "marginTop": "4px" if i > 0 else "0",
        }))
        for key in keys:
            if key in classifications:
                row, detail = create_metric_row(key, classifications[key], is_missing=False, row_id_prefix="metric")
            else:
                row, detail = create_metric_row(key, None, is_missing=True, row_id_prefix="metric")
            all_items.extend([row, detail])

    metrics_section = html.Div(all_items, className="metric-list")

    # ── Link to history ──
    history_link = dcc.Link("Ver Histórico Completo", href="/historico",
                            className="btn-health", style={"display": "block", "textAlign": "center",
                                                           "textDecoration": "none", "marginTop": "16px"})

    footnote = html.P("* Estimativas baseadas em bioimpedância elétrica (BIA)", className="footnote")

    return html.Div([header, weight_card, metrics_section, history_link, footnote])


# ── Toggle metric detail ──
@callback(
    Output({"type": "metric-row-detail", "index": ALL}, "style"),
    Input({"type": "metric-row-click", "index": ALL}, "n_clicks"),
    State({"type": "metric-row-detail", "index": ALL}, "style"),
    prevent_initial_call=True
)
def toggle_metric_detail(clicks, styles):
    if not ctx.triggered_id:
        return [no_update] * len(styles)
    key = ctx.triggered_id["index"]
    new_styles = []
    for i, s in enumerate(styles):
        detail_key = ctx.inputs_list[0][i]["id"]["index"]
        if detail_key == key:
            is_open = s.get("display") != "none"
            new_s = dict(s)
            new_s["display"] = "none" if is_open else "block"
            new_styles.append(new_s)
        else:
            new_styles.append(s)
    return new_styles

