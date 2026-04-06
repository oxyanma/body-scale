"""Dashboard overview — Health-first mobile design.

QA-fixed version: proper no-measurement state, BLE status separated,
link styles fixed, live weight update.
"""
from dash import html, dcc, callback, Input, Output, State, no_update, ctx, ALL
import dash_bootstrap_components as dbc
from database.db import SessionLocal
from database.models import User, Measurement, Goal
from dashboard.state import app_state
from dashboard.ble_worker import start_ble_measurement_thread
from datetime import datetime
from i18n import t


def _month_name(n):
    return t(f"month.{n}")


def _bmi_position(bmi):
    if not bmi or bmi < 15: return 0
    if bmi > 40: return 100
    return ((bmi - 15) / 25) * 100


def _bmi_status(bmi):
    if not bmi or bmi < 18.5: return t("bmi.underweight"), "low"
    if bmi < 25: return t("bmi.normal"), "normal"
    if bmi < 30: return t("bmi.overweight"), "high"
    return t("bmi.obese"), "obese"


def _greeting():
    hour = datetime.now().hour
    if hour < 12: return t("overview.greeting_morning")
    if hour < 18: return t("overview.greeting_afternoon")
    return t("overview.greeting_evening")


def _format_date_pt(dt):
    if not dt: return "--"
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year} {dt.hour:02d}:{dt.minute:02d}"


def _build_goal_stats(target, diff, is_custom_goal, has_data, last):
    """Redesigned goal stats view — progress bar + clean layout."""
    current_w = last.weight_kg if has_data and last else 0

    # Progress calculation (0-100%)
    if diff > 0:
        # Need to lose weight
        start_offset = abs(diff) + target  # rough estimate of starting point
        progress = max(0, min(100, (1 - abs(diff) / max(start_offset - target, 1)) * 100))
        status_text = t("overview.goal_remain").format(diff=f"{abs(diff):.2f}")
        status_color = "var(--red)"
        bar_color = "linear-gradient(90deg, #FF6B6B, #EE5A24)"
    elif diff < 0:
        status_text = t("overview.goal_gain").format(diff=f"{abs(diff):.2f}")
        status_color = "var(--blue)"
        bar_color = "linear-gradient(90deg, #4A90D9, #6C5CE7)"
        progress = max(0, min(100, 50))
    else:
        status_text = t("overview.goal_reached")
        status_color = "var(--green)"
        bar_color = "linear-gradient(90deg, #00B894, #55E6C1)"
        progress = 100

    # Clamp progress for visual
    bar_width = max(8, min(100, progress if diff == 0 else max(20, 100 - min(abs(diff) * 3, 80))))

    return html.Div([
        # Current weight vs target in a clean row
        html.Div([
            html.Div([
                html.Div(f"{current_w:.2f}" if current_w else "--", style={
                    "fontFamily": "'Nunito'", "fontSize": "1.6rem", "fontWeight": "800", "color": "var(--text-primary)", "lineHeight": "1"}),
                html.Div(t("overview.goal_current"), style={"fontSize": "0.6rem", "fontWeight": "700", "color": "var(--text-label)",
                                          "letterSpacing": "0.08em", "marginTop": "2px"}),
            ], style={"textAlign": "center"}),

            # Arrow
            html.Div("→", style={"fontSize": "1.2rem", "color": "var(--text-muted)", "alignSelf": "center"}),

            html.Div([
                html.Div(f"{target:.2f}", style={
                    "fontFamily": "'Nunito'", "fontSize": "1.6rem", "fontWeight": "800", "color": "var(--blue)", "lineHeight": "1"}),
                html.Div(t("overview.goal_target"), style={"fontSize": "0.6rem", "fontWeight": "700", "color": "var(--text-label)",
                                         "letterSpacing": "0.08em", "marginTop": "2px"}),
            ], style={"textAlign": "center"}),
        ], style={"display": "flex", "justifyContent": "center", "gap": "24px", "alignItems": "center", "padding": "8px 0 12px"}),

        # Progress bar
        html.Div([
            html.Div(style={
                "width": f"{bar_width}%", "height": "100%", "borderRadius": "4px",
                "background": bar_color, "transition": "width 0.5s ease"
            })
        ], style={
            "width": "100%", "height": "6px", "borderRadius": "4px",
            "background": "var(--bg-secondary)", "overflow": "hidden"
        }),

        # Status text
        html.Div([
            html.Span(status_text, style={"fontWeight": "700", "color": status_color, "fontSize": "0.78rem"}),
            html.Span(" kg" if diff == 0 else "", style={"display": "none"}),
        ], style={"textAlign": "center", "marginTop": "8px"}),

        # Subtitle
        html.Div(
            t("overview.goal_ideal") if not is_custom_goal else t("overview.goal_custom"),
            style={"textAlign": "center", "fontSize": "0.62rem", "color": "var(--text-label)", "marginTop": "4px"}
        ),
    ])


def create_overview_layout(show_goal_stats=False):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            return html.Div([
                html.Div([
                    html.Div([
                        html.Div(t("overview.app_name"), className="dash-greeting"),
                        html.Div(t("overview.subtitle"), className="dash-subtitle"),
                    ]),
                ], className="dash-header"),
                html.Div([
                    html.Div("👤", style={"fontSize": "3rem", "textAlign": "center", "marginBottom": "8px"}),
                    html.P(t("overview.create_profile_cta"), style={"color": "var(--text-secondary)", "textAlign": "center"}),
                    dcc.Link(t("overview.create_profile_btn"), href="/profile",
                             style={"display": "block", "textAlign": "center", "textDecoration": "none",
                                    "padding": "14px", "background": "linear-gradient(135deg, #6C5CE7, #4A90D9)",
                                    "color": "white", "borderRadius": "12px", "fontWeight": "600", "marginTop": "16px"})
                ], className="health-card"),
            ])

        name = user.name.split()[0] if user.name else "User"

        last = db.query(Measurement).filter(Measurement.user_id == user.id).order_by(Measurement.measured_at.desc()).first()
        prev = db.query(Measurement).filter(Measurement.user_id == user.id).order_by(Measurement.measured_at.desc()).offset(1).first()
        goal_row = db.query(Goal).filter(Goal.user_id == user.id, Goal.achieved_at == None).first()
        goal_target_value = goal_row.target_value if goal_row else None
    finally:
        db.close()

    has_data = last is not None

    # ── Header ──
    header = html.Div([
        html.Div([
            html.Div(f"{_greeting()}, {name}", className="dash-greeting"),
            html.Div(t("overview.app_subtitle"), className="dash-subtitle"),
        ]),
        dcc.Link(
            html.Div(name[0].upper(), style={
                "width": "40px", "height": "40px", "borderRadius": "50%",
                "background": "linear-gradient(135deg, #4A90D9, #6C5CE7)",
                "color": "white", "fontSize": "1rem", "fontWeight": "700",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "boxShadow": "0 2px 8px rgba(74,144,217,0.3)",
                "lineHeight": "1", "textDecoration": "none"
            }),
            href="/profile", style={"textDecoration": "none"}
        )
    ], className="dash-header")

    # ── Weight Hero Card ──
    if has_data:
        weight_val = last.weight_kg
        bmi_val = last.bmi or 0
        date_str = _format_date_pt(last.measured_at)
        delta_weight = round(last.weight_kg - prev.weight_kg, 2) if prev else None
        bmi_label, bmi_class = _bmi_status(bmi_val)
        bmi_pos = _bmi_position(bmi_val)

        # Delta display: show previous weight + difference
        delta_block = ""
        if prev:
            prev_w = prev.weight_kg
            if delta_weight != 0:
                delta_sign = "+" if delta_weight > 0 else ""
                delta_color = "var(--red)" if delta_weight > 0 else "var(--green)"
                delta_block = html.Div([
                    html.Div(f"{delta_sign}{delta_weight:.2f} kg", style={
                        "fontFamily": "'Nunito'", "fontSize": "1.1rem", "fontWeight": "800", "color": delta_color}),
                    html.Div(t("overview.previous") + f": {prev_w:.2f}", style={
                        "fontSize": "0.68rem", "color": "var(--text-muted)"}),
                ], style={"textAlign": "right"})
            else:
                delta_block = html.Div([
                    html.Div(f"= {prev_w:.2f} kg", style={
                        "fontFamily": "'Nunito'", "fontSize": "1.1rem", "fontWeight": "800", "color": "var(--text-muted)"}),
                    html.Div(t("overview.same_weight"), style={
                        "fontSize": "0.68rem", "color": "var(--text-muted)"}),
                ], style={"textAlign": "right"})

        weight_hero = html.Div([
            # Top part: clickable to composicao
            dcc.Link(
                html.Div([
                    html.Div(t("overview.current_weight"), className="label"),
                    html.Div([
                        html.Div([
                            html.Span(f"{weight_val:.2f}", className="weight-big", id="home-weight-display"),
                            html.Span("kg", className="weight-unit"),
                        ]),
                        delta_block,
                    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-end"}),
                    html.Div(date_str, className="date"),

                    # BMI bar
                    html.Div([
                        html.Span(bmi_label, className=f"bmi-status-pill {bmi_class}"),
                        html.Div([
                            html.Div(className="bmi-indicator", style={"left": f"{bmi_pos}%"})
                        ], className="bmi-bar"),
                        html.Div([
                            html.Span(t("bmi.low")), html.Span(t("bmi.ideal")), html.Span(t("bmi.high")), html.Span(t("bmi.obese_short"))
                        ], className="bmi-labels"),
                    ], className="bmi-bar-container"),
                ]),
                href=f"/composition?id={last.id}", style={"textDecoration": "none", "color": "inherit"}
            ),

            # BLE controls inside the card
            html.Hr(style={"border": "none", "borderTop": "1px solid var(--border-light)", "margin": "12px 0"}),
            html.Button(t("overview.weigh_now_btn"), id="btn-start-measurement", n_clicks=0, className="btn-pesar"),
            html.Div(id="home-measure-status"),
            html.Div([
                html.Div(id="home-ble-indicator", style={"display": "inline-block", "verticalAlign": "middle"}),
                html.Span("", id="home-ble-msg", style={"fontSize": "0.75rem", "color": "var(--text-muted)", "verticalAlign": "middle"}),
            ], style={"marginTop": "6px"}),
            html.Div(id="home-save-alert"),
        ], className="weight-hero")
    else:
        weight_hero = html.Div([
            html.Div(t("overview.current_weight"), className="label"),
            html.Div([
                html.Span("--", className="weight-big", id="home-weight-display"),
                html.Span("kg", className="weight-unit"),
            ]),
            html.P(t("overview.no_measurements"),
                   style={"color": "var(--text-muted)", "fontSize": "0.85rem", "marginTop": "8px"}),
            html.Hr(style={"border": "none", "borderTop": "1px solid var(--border-light)", "margin": "12px 0"}),
            html.Button(t("overview.weigh_now_btn"), id="btn-start-measurement", n_clicks=0, className="btn-pesar"),
            html.Div(id="home-measure-status"),
            html.Div([
                html.Div(id="home-ble-indicator", style={"display": "inline-block", "verticalAlign": "middle"}),
                html.Span("", id="home-ble-msg", style={"fontSize": "0.75rem", "color": "var(--text-muted)", "verticalAlign": "middle"}),
            ], style={"marginTop": "6px"}),
            html.Div(id="home-save-alert"),
        ], className="weight-hero")

    # ── Quick Actions ──
    link_style = {"textDecoration": "none", "color": "inherit"}
    quick_actions = html.Div([
        dcc.Link(html.Div([
            html.Div(html.Img(src="/assets/icon_historico.png"), className="quick-action-icon"),
            html.Span(t("overview.quick_history"), className="quick-action-label")
        ], className="quick-action"), href="/history", style=link_style),
        dcc.Link(html.Div([
            html.Div(html.Img(src="/assets/icon_composicao.png"), className="quick-action-icon"),
            html.Span(t("overview.quick_composition"), className="quick-action-label")
        ], className="quick-action"), href="/composition", style=link_style),
        dcc.Link(html.Div([
            html.Div(html.Img(src="/assets/icon_config.png"), className="quick-action-icon"),
            html.Span(t("overview.quick_settings"), className="quick-action-label")
        ], className="quick-action"), href="/settings", style=link_style),
    ], className="quick-actions")

    # ── Goal Card ──
    ideal_weight = 0
    if user and user.height_cm:
        height_m = user.height_cm / 100
        ideal_weight = 22.0 * (height_m * height_m)

    # Auto-create goal with ideal weight if none exists
    if goal_target_value:
        target = goal_target_value
    elif ideal_weight > 0:
        target = round(ideal_weight, 1)
        try:
            db2 = SessionLocal()
            try:
                new_goal = Goal(
                    user_id=user.id, metric="weight",
                    target_value=target,
                )
                db2.add(new_goal)
                db2.commit()
            finally:
                db2.close()
        except Exception:
            pass
    else:
        target = 0

    is_custom_goal = bool(goal_target_value)
    diff = round(last.weight_kg - target, 1) if has_data and target > 0 else 0

    # After saving, show stats; otherwise show edit form
    stats_style = {"display": "block"} if show_goal_stats else {"display": "none"}
    form_style = {"display": "none"} if show_goal_stats else {}
    toggle_icon = "✎" if show_goal_stats else "📊"

    goal_card = html.Div(id="goal-card-container", children=[
        html.Div([
            html.Span(t("overview.goal_title"), className="goal-card-title"),
            html.Div(
                toggle_icon,
                id="btn-toggle-goal-form",
                className="goal-card-link",
                style={"cursor": "pointer", "fontSize": "1rem", "color": "var(--text-muted)"}
            ),
        ], className="goal-card-header"),

        # Display Stats view
        html.Div(id="goal-view-stats", style=stats_style, children=[
            _build_goal_stats(target, diff, is_custom_goal, has_data, last)
        ]) if target > 0 else html.Div(id="goal-view-stats", style=stats_style, children=[
            html.P(t("overview.goal_fill_height"),
                   style={"textAlign": "center", "fontSize": "0.8rem", "color": "var(--text-muted)", "padding": "12px 0"})
        ]),

        # Edit Form view
        html.Div(id="goal-edit-form", style=form_style, children=[
            html.P(t("overview.goal_define"), style={"fontSize": "0.8rem", "color": "var(--text-secondary)", "marginTop": "8px", "marginBottom": "8px"}),
            html.Div([
                dcc.Input(
                    id="input-new-goal-weight",
                    type="number",
                    min=20, max=250, step=0.1,
                    placeholder=f"{target:.1f}",
                    style={
                        "flex": "1", "padding": "10px", "borderRadius": "8px",
                        "border": "1px solid var(--border-light)", "fontFamily": "Nunito", "fontSize": "1rem"
                    }
                ),
                html.Button(
                    t("common.save"),
                    id="btn-save-new-goal",
                    style={
                        "padding": "10px 16px", "borderRadius": "8px", "border": "none",
                        "background": "linear-gradient(135deg, var(--blue), #6C5CE7)",
                        "color": "white", "fontWeight": "600", "cursor": "pointer"
                    }
                )
            ], style={"display": "flex", "gap": "8px"}),
            html.Button(
                t("overview.goal_use_ideal").format(weight=f"{ideal_weight:.1f}") if ideal_weight > 0 else t("overview.goal_use_ideal_no_weight"),
                id="btn-use-ideal-weight",
                style={
                    "width": "100%", "marginTop": "8px", "padding": "10px 16px", "borderRadius": "8px",
                    "border": "1px solid var(--blue)", "background": "transparent",
                    "color": "var(--blue)", "fontWeight": "600", "cursor": "pointer",
                    "display": "block" if ideal_weight > 0 else "none"
                }
            ),
            html.Div(id="goal-save-alert", style={"marginTop": "8px", "fontSize": "0.75rem", "textAlign": "center"})
        ])
    ], className="goal-card")

    # ── Stores (hidden) ──
    stores = html.Div([
        dcc.Interval(id="home-ble-poll", interval=500, n_intervals=0, disabled=False),
        html.Div(id="home-metrics-cards", style={"display": "none"}),
        html.Div(id="home-results-container", style={"display": "none"}),
        dcc.Store(id="auto-save-done", data=False),
    ], style={"display": "none"})

    return html.Div([header, weight_hero, quick_actions, goal_card, stores])


# ── Callbacks ──

@callback(
    Output("home-ble-msg", "children"),
    Input("btn-start-measurement", "n_clicks"),
    prevent_initial_call=True
)
def start_measurement(n):
    if n and n > 0:
        start_ble_measurement_thread()
    return t("overview.starting")


@callback(
    [Output("home-ble-indicator", "children"),
     Output("home-ble-msg", "children", allow_duplicate=True),
     Output("home-weight-display", "children"),
     Output("home-measure-status", "children"),
     Output("home-measure-status", "style"),
     Output("home-results-container", "style"),
     Output("home-metrics-cards", "children"),
     Output("home-save-alert", "children"),
     Output("auto-save-done", "data"),
     Output("url", "pathname", allow_duplicate=True)],
    [Input("home-ble-poll", "n_intervals")],
    [State("auto-save-done", "data")],
    prevent_initial_call=True
)
def home_poll_ble(n, already_saved):
    snap = app_state.get_snapshot()
    status = snap["status"]

    # BLE indicator (hide when idle - no floating dot)
    if status == "Disconnected" or "Timeout" in (snap.get("scan_error") or ""):
        indicator = ""
    elif "Listening" in status or "step on" in status.lower() or "Starting" in status:
        indicator = html.Span(className="ble-indicator ble-scanning")
    elif "Connected" in status:
        indicator = html.Span(className="ble-indicator ble-connected")
    elif status == "Done":
        indicator = html.Span(className="ble-indicator ble-done")
    else:
        indicator = html.Span(className="ble-indicator ble-idle")

    msg = snap.get("scan_error") or ""
    weight_str = no_update  # Don't update unless measuring

    m_text = ""
    m_style = {"textAlign": "center", "fontSize": "0.85rem", "marginTop": "8px", "padding": "8px", "borderRadius": "10px"}
    if "step on" in status.lower() or "Listening" in status:
        m_text = t("overview.step_on_scale")
        m_style.update({"color": "var(--blue)", "background": "var(--blue-light)"})
    elif "Connected" in status:
        w = snap["weight"]
        weight_str = f"{w:.2f}"  # Live update!
        m_text = t("overview.measuring").format(weight=f"{w:.2f}")
        m_style.update({"color": "var(--green)", "background": "var(--green-light)"})
    elif status == "Done":
        w = snap["weight"]
        weight_str = f"{w:.2f}"
        m_text = t("overview.measurement_complete").format(weight=f"{w:.2f}")
        m_style.update({"color": "var(--green)", "background": "var(--green-light)"})
    elif snap.get("scan_error"):
        m_text = f"⚠️ {snap['scan_error']}"
        m_style.update({"color": "var(--red)", "background": "var(--red-light)"})

    results_style = {"display": "none"}
    cards = no_update
    redirect = no_update

    # Auto-save
    save_alert = no_update
    save_done = no_update
    if snap.get("metrics") and not already_saved:
        if status == "Done" or (status.startswith("Connected") and snap.get("impedance") is not None):
            try:
                db3 = SessionLocal()
                try:
                    user3 = db3.query(User).filter(User.is_active == True).first()
                    if user3:
                        from datetime import timedelta
                        cutoff = datetime.now() - timedelta(seconds=60)
                        recent = db3.query(Measurement).filter(
                            Measurement.user_id == user3.id,
                            Measurement.created_at >= cutoff,
                            Measurement.weight_kg == snap["weight"]
                        ).first()
                        if recent:
                            save_done = True
                        else:
                            md = snap["metrics"]
                            m_obj = Measurement(
                                user_id=user3.id, weight_kg=snap["weight"], impedance=snap.get("impedance"),
                                bmi=md.get("bmi"), body_fat_percent=md.get("body_fat_percent"),
                                muscle_mass_percent=md.get("muscle_mass_percent"),
                                body_water_percent=md.get("body_water_percent"),
                                bone_mass_kg=md.get("bone_mass_kg"), visceral_fat=md.get("visceral_fat"),
                                bmr=md.get("bmr"), tdee=md.get("tdee"),
                                metabolic_age=md.get("metabolic_age"), protein_percent=md.get("protein_percent"),
                                fat_free_mass_kg=md.get("fat_free_mass_kg"),
                                smm_kg=md.get("smm_kg"), lbm_kg=md.get("lbm_kg"),
                                impedance_index=md.get("impedance_index"),
                                body_score=md.get("body_score"), ideal_weight_kg=md.get("ideal_weight_kg"),
                                ffmi=md.get("ffmi"), smi=md.get("smi"),
                                subcutaneous_fat_kg=md.get("subcutaneous_fat_kg"),
                                whr=md.get("whr"), whtr=md.get("whtr"),
                            )
                            db3.add(m_obj)
                            db3.commit()
                            save_alert = html.Div(t("overview.measurement_saved"), className="alert-health alert-success")
                            save_done = True
                            # Clear BLE state so redirect doesn't re-save
                            app_state.reset()
                            # Force page refresh so BMI/delta/date update
                            redirect = "/"
                finally:
                    db3.close()
            except Exception as e:
                print(f"Auto-save error: {e}")

    return indicator, msg, weight_str, m_text, m_style, results_style, cards, save_alert, save_done, redirect

@callback(
    [Output("goal-view-stats", "style"),
     Output("goal-edit-form", "style"),
     Output("goal-save-alert", "children"),
     Output("url", "pathname", allow_duplicate=True)],
    [Input("btn-toggle-goal-form", "n_clicks"),
     Input("btn-save-new-goal", "n_clicks"),
     Input("btn-use-ideal-weight", "n_clicks")],
    [State("input-new-goal-weight", "value"),
     State("goal-view-stats", "style")],
    prevent_initial_call=True
)
def toggle_and_save_goal(toggle_clicks, save_clicks, ideal_clicks, new_weight, current_stats_style):
    import dash
    from dash.exceptions import PreventUpdate
    from datetime import datetime, timedelta
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle Toggle Click
    if trigger_id == "btn-toggle-goal-form":
        is_hidden = current_stats_style and current_stats_style.get("display") == "none"
        if is_hidden:
            return {"display": "block"}, {"display": "none"}, no_update, no_update
        else:
            return {"display": "none"}, {"display": "block"}, no_update, no_update

    # Handle Save / Ideal Click
    if trigger_id in ["btn-save-new-goal", "btn-use-ideal-weight"]:
        try:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.is_active == True).first()
                if user:
                    # Deactivate old goals
                    old_goals = db.query(Goal).filter(Goal.user_id == user.id, Goal.achieved_at == None).all()
                    for og in old_goals:
                        og.achieved_at = datetime.now()
                    
                    if trigger_id == "btn-save-new-goal":
                        if not new_weight or new_weight < 20 or new_weight > 250:
                            msg = html.Div(t("overview.goal_invalid"), className="alert-health alert-error")
                            return no_update, no_update, msg, no_update
                        target_val = new_weight
                    else:
                        # btn-use-ideal-weight: calculate ideal weight
                        height_m = user.height_cm / 100 if user.height_cm else 1.75
                        target_val = round(22.0 * height_m * height_m, 1)

                    new_goal = Goal(
                        user_id=user.id,
                        metric="weight",
                        target_value=target_val,
                        target_date=datetime.now() + timedelta(days=90)
                    )
                    db.add(new_goal)
                        
                    db.commit()
                    # Refresh page with flag to show stats view
                    return {"display": "block"}, {"display": "none"}, no_update, "/?saved=1"
            finally:
                db.close()
        except Exception as e:
            print(f"Erro ao salvar objetivo: {e}")
            msg = html.Div(f"Erro ao salvar: {e}", className="alert-health alert-error")
            return no_update, no_update, msg, no_update
            
    raise PreventUpdate
