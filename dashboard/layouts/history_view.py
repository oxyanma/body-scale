"""History view — Trend chart + colored records + compare button.

Records show BMI status color. Select 2 records to compare on a dedicated page.
"""
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from database.db import SessionLocal
from database.models import User, Measurement
from datetime import datetime, timedelta

MONTHS_PT_SHORT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                   7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

STATUS_COLORS = {
    "success": "var(--green)", "primary": "var(--blue)",
    "warning": "var(--yellow)", "danger": "var(--red)", "info": "var(--purple)"
}
STATUS_BG = {
    "success": "var(--green-light)", "primary": "var(--blue-light)",
    "warning": "var(--yellow-light)", "danger": "var(--red-light)", "info": "var(--purple-light)"
}


def _bmi_status(bmi):
    if not bmi or bmi < 18.5: return "Abaixo", "primary"
    if bmi < 25: return "Normal", "success"
    if bmi < 30: return "Sobrepeso", "warning"
    return "Obeso", "danger"


def _format_date(dt):
    if not dt: return "--"
    return f"{dt.day:02d} {MONTHS_PT_SHORT.get(dt.month, '')}, {dt.hour:02d}:{dt.minute:02d}"


def create_history_view():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            return html.Div("Nenhum perfil encontrado.")

        measurements = db.query(Measurement).filter(
            Measurement.user_id == user.id
        ).order_by(Measurement.measured_at.desc()).all()
    finally:
        db.close()

    header = html.Div([
        dcc.Link(html.Button("‹", className="back-btn"), href="/"),
        html.H1("Histórico"),
        html.Button([
            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8'/%3E%3Cpolyline points='16 6 12 2 8 6'/%3E%3Cline x1='12' y1='2' x2='12' y2='15'/%3E%3C/svg%3E",
                     className="export-icon"),
            html.Div(className="export-spinner"),
        ], className="btn-export", **{"data-filename": "historico"}),
    ], className="page-header")

    if not measurements:
        return html.Div([
            header,
            html.Div([
                html.P("Nenhuma medição registrada ainda.",
                       style={"textAlign": "center", "padding": "40px 0", "color": "var(--text-secondary)"}),
                dcc.Link("← Pesar agora", href="/",
                         style={"display": "block", "textAlign": "center", "color": "var(--blue)", "fontWeight": "600"})
            ], className="health-card")
        ])

    # Stats
    weights = [m.weight_kg for m in measurements]
    avg_weight = sum(weights) / len(weights)
    max_weight = max(weights)
    min_weight = min(weights)
    delta_30d = 0
    if len(measurements) > 1:
        cutoff = datetime.now() - timedelta(days=30)
        older = [m for m in measurements if m.measured_at and m.measured_at < cutoff]
        if older:
            delta_30d = round(measurements[0].weight_kg - older[0].weight_kg, 1)
        else:
            delta_30d = round(measurements[0].weight_kg - measurements[-1].weight_kg, 1)

    delta_color_cls = "delta-down" if delta_30d <= 0 else "delta-up"

    # ── Trend Chart ──
    dates = [m.measured_at for m in reversed(measurements) if m.measured_at]
    wts = [m.weight_kg for m in reversed(measurements) if m.measured_at]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=wts,
        mode='lines+markers',
        line=dict(color='#4A90D9', width=2.5),
        marker=dict(size=5, color='#4A90D9'),
        fill='tozeroy',
        fillcolor='rgba(74,144,217,0.08)',
        hovertemplate='%{y:.1f} kg<br>%{x|%d/%m}<extra></extra>'
    ))
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=0, r=0, t=10, b=30),
        height=200,
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, color='#A0B0C0')),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0', showline=False, tickfont=dict(size=10, color='#A0B0C0')),
        font=dict(family='Inter'),
    )

    trend_card = html.Div([
        html.Div([
            html.Div([
                html.Div("TENDÊNCIA DE PESO", className="trend-label"),
                html.Div([
                    html.Span(f"{avg_weight:.2f}", className="trend-value"),
                    html.Span(" kg (média)", className="trend-unit"),
                ]),
            ]),
            html.Div([
                html.Div(f"{'↓' if delta_30d <= 0 else '↑'} {abs(delta_30d):.2f} kg",
                         className=f"trend-delta-value {delta_color_cls}"),
                html.Div("VARIAÇÃO 30D", className="trend-delta-label"),
            ], className="trend-delta"),
        ], className="trend-header"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"marginTop": "8px"}),

        # Stats inline inside trend card
        html.Div([
            html.Div([
                html.Div("MÁXIMO", className="stat-box-label"),
                html.Div(f"{max_weight:.2f} kg", className="stat-box-value",
                         style={"fontSize": "1rem", "marginTop": "2px"}),
            ], className="stat-box", style={"boxShadow": "none", "border": "none",
                                             "background": "var(--bg-main)", "padding": "10px 14px"}),
            html.Div([
                html.Div("MÍNIMO", className="stat-box-label"),
                html.Div(f"{min_weight:.2f} kg", className="stat-box-value",
                         style={"fontSize": "1rem", "marginTop": "2px"}),
            ], className="stat-box", style={"boxShadow": "none", "border": "none",
                                             "background": "var(--bg-main)", "padding": "10px 14px"}),
        ], className="stat-row", style={"marginBottom": "0", "marginTop": "8px"}),
    ], className="trend-card")

    # ── Compare card (blue gradient like index) ──
    compare_bar = html.Div(id="compare-bar", children=[
        html.Div("📊", style={"fontSize": "1.2rem"}),
        html.Div([
            html.Div("Comparar Medições", style={"fontWeight": "700", "fontSize": "0.88rem"}),
            html.Span("Selecione 2 medições abaixo", id="compare-bar-text",
                       style={"fontSize": "0.72rem", "opacity": "0.85"}),
        ], style={"flex": "1"}),
        dcc.Link("Comparar →", id="compare-bar-link", href="#",
                 style={"display": "none", "fontSize": "0.78rem", "fontWeight": "700",
                        "color": "var(--blue)", "background": "white",
                        "padding": "6px 16px", "borderRadius": "20px", "textDecoration": "none",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.15)"}),
    ], style={"display": "flex", "alignItems": "center", "gap": "12px",
              "padding": "14px 18px", "borderRadius": "var(--radius-card)",
              "background": "linear-gradient(135deg, #4A90D9, #6C5CE7)",
              "color": "white", "marginBottom": "16px",
              "boxShadow": "0 4px 12px rgba(74,144,217,0.3)"})

    # ── Records with status colors ──
    records = []
    for i, m in enumerate(measurements[:30]):
        date_str = _format_date(m.measured_at)
        bmi_label, bmi_color_key = _bmi_status(m.bmi)
        bmi_txt = STATUS_COLORS.get(bmi_color_key, "var(--text-muted)")
        bmi_bg = STATUS_BG.get(bmi_color_key, "var(--blue-light)")

        delta = ""
        delta_c = "var(--text-muted)"
        if i + 1 < len(measurements):
            d = round(m.weight_kg - measurements[i + 1].weight_kg, 1)
            if d != 0:
                delta = f"{'↑' if d > 0 else '↓'} {abs(d)}"
                delta_c = "var(--red)" if d > 0 else "var(--green)"

        bf_str = f"{m.body_fat_percent:.0f}%" if m.body_fat_percent else ""

        records.append(html.Div([
            # Checkbox for comparison
            dbc.Checkbox(id={"type": "compare-check", "index": m.id},
                         value=False, className="compare-checkbox"),
            dcc.Link(
                html.Div([
                    html.Div([
                        html.Div(f"{m.weight_kg:.2f} kg", className="record-weight"),
                        html.Div(date_str, className="record-date"),
                    ], className="record-info"),
                    html.Div([
                        html.Span(bmi_label, style={
                            "fontSize": "0.65rem", "fontWeight": "600", "padding": "2px 6px",
                            "borderRadius": "6px", "color": bmi_txt, "background": bmi_bg,
                            "marginRight": "6px"
                        }),
                        html.Span(bf_str, style={
                            "fontSize": "0.72rem", "color": "var(--text-muted)",
                        }) if bf_str else "",
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Div(delta, className="record-delta", style={"color": delta_c}),
                ], style={"display": "flex", "alignItems": "center", "gap": "10px", "flex": "1"}),
                href=f"/composicao?id={m.id}", style={"textDecoration": "none", "color": "inherit", "flex": "1"}
            ),
            html.Button("🗑", className="record-action-btn",
                        id={"type": "delete-measurement-btn", "index": m.id}),
        ], className="record-row"))

    records_section = html.Div([
        html.Div("REGISTROS", className="section-label"),
        html.Div(records, className="metric-list"),
    ])

    # ── Delete Modal ──
    delete_modal = dbc.Modal([
        dbc.ModalHeader("Excluir Medição", style={"color": "var(--text-primary)"}),
        dbc.ModalBody("Tem certeza que deseja excluir esta medição?",
                      style={"color": "var(--text-secondary)"}),
        dbc.ModalFooter([
            dbc.Button("Cancelar", id="btn-cancel-delete", className="btn-outline-health",
                       style={"width": "auto", "marginRight": "8px"}),
            dbc.Button("Excluir", id="btn-confirm-delete", className="btn-danger"),
        ]),
    ], id="modal-delete-measurement", is_open=False)

    stores = html.Div([
        dcc.Store(id="store-delete-id", data=None),
        dcc.Store(id="store-compare-ids", data=[]),
    ])

    return html.Div([header, trend_card, compare_bar, records_section, delete_modal, stores])


# ── Compare button callback ──
@callback(
    [Output("compare-bar-text", "children"),
     Output("compare-bar-text", "style"),
     Output("compare-bar-link", "href"),
     Output("compare-bar-link", "style")],
    Input({"type": "compare-check", "index": ALL}, "value"),
    prevent_initial_call=True
)
def update_compare_bar(values):
    base_text_style = {"fontSize": "0.72rem", "opacity": "0.85"}
    hidden_link = {"display": "none"}
    visible_link = {"display": "inline-block", "fontSize": "0.78rem", "fontWeight": "700",
                    "color": "var(--blue)", "background": "white",
                    "padding": "6px 16px", "borderRadius": "20px", "textDecoration": "none",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.15)", "whiteSpace": "nowrap"}

    if not values:
        return ("Selecione 2 medições abaixo", base_text_style, "#", hidden_link)

    checked_ids = []
    for i, v in enumerate(values):
        if v:
            checked_ids.append(ctx.inputs_list[0][i]["id"]["index"])

    if len(checked_ids) == 0:
        return ("Selecione 2 medições abaixo", base_text_style, "#", hidden_link)
    elif len(checked_ids) == 1:
        return ("1 de 2 selecionada...",
                {"fontSize": "0.72rem", "opacity": "1", "fontWeight": "600"},
                "#", hidden_link)
    elif len(checked_ids) == 2:
        href = f"/comparacao?a={checked_ids[0]}&b={checked_ids[1]}"
        return ("2 selecionadas",
                {"fontSize": "0.72rem", "opacity": "1", "fontWeight": "600"},
                href, visible_link)
    else:
        return ("Selecione apenas 2",
                {"fontSize": "0.72rem", "opacity": "1", "color": "#FFD6DB", "fontWeight": "600"},
                "#", hidden_link)


# ── Delete callbacks ──
@callback(
    [Output("modal-delete-measurement", "is_open"),
     Output("store-delete-id", "data")],
    [Input({"type": "delete-measurement-btn", "index": ALL}, "n_clicks"),
     Input("btn-cancel-delete", "n_clicks")],
    [State("modal-delete-measurement", "is_open")],
    prevent_initial_call=True
)
def open_delete_modal(delete_clicks, cancel, is_open):
    triggered = ctx.triggered_id
    if triggered == "btn-cancel-delete":
        return False, None
    if isinstance(triggered, dict) and triggered.get("type") == "delete-measurement-btn":
        return True, triggered["index"]
    return no_update, no_update


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("btn-confirm-delete", "n_clicks"),
    State("store-delete-id", "data"),
    prevent_initial_call=True
)
def confirm_delete(n, measurement_id):
    if not n or not measurement_id:
        return no_update
    db = SessionLocal()
    try:
        m = db.query(Measurement).filter(Measurement.id == int(measurement_id)).first()
        if m:
            db.delete(m)
            db.commit()
    finally:
        db.close()
    return "/historico"
