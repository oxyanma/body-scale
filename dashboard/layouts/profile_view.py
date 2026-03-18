"""Profile view — Light theme, mobile-friendly form."""
from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import dash_bootstrap_components as dbc
from database.db import SessionLocal
from database.models import User


def create_profile_view():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        user_options = [{"label": u.name, "value": str(u.id)} for u in users]
        active_user = next((u for u in users if u.is_active), None)
        active_value = str(active_user.id) if active_user else None
    finally:
        db.close()

    header = html.Div([
        dcc.Link(html.Button("‹", className="back-btn"), href="/"),
        html.H1("Perfis"),
    ], className="page-header")

    selector = html.Div([
        html.Div([
            html.Div([
                html.Label("Membro da Família", className="form-label"),
                dbc.Select(id="profile-selector", options=user_options, value=active_value)
            ], style={"flex": "1"}),
            html.Button("+ Novo", id="btn-new-profile", n_clicks=0,
                        className="btn-outline-health", style={"width": "auto", "marginTop": "20px", "padding": "8px 16px"}),
        ], style={"display": "flex", "gap": "12px", "alignItems": "flex-start"})
    ], className="health-card")

    form = html.Div([


        html.Div([
            html.Label("Nome", className="form-label"),
            dbc.Input(id="input-profile-name", type="text", placeholder="Nome completo"),
        ], className="form-group"),

        html.Div([
            html.Div([
                html.Label("Sexo", className="form-label"),
                dbc.Select(id="input-profile-sex", options=[
                    {"label": "Masculino", "value": "M"},
                    {"label": "Feminino", "value": "F"}
                ]),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Idade", className="form-label"),
                dbc.Input(id="input-profile-age", type="number", min=1, max=120),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "12px"}, className="form-group"),

        html.Div([
            html.Div([
                html.Label("Altura (cm)", className="form-label"),
                dbc.Input(id="input-profile-height", type="number", min=50, max=250),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Atividade", className="form-label"),
                dbc.Select(id="input-profile-activity", options=[
                    {"label": "Sedentário", "value": "sedentary"},
                    {"label": "Leve", "value": "light"},
                    {"label": "Moderado", "value": "moderate"},
                    {"label": "Intenso", "value": "intense"},
                    {"label": "Atleta", "value": "athlete"},
                ]),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "12px"}, className="form-group"),

        # Optional anthropometrics
        html.Div([
            html.Label("Medidas Opcionais", className="form-label"),
            html.P("Desbloqueia WHR, WHtR e Risco Cardiovascular",
                   style={"fontSize": "0.75rem", "color": "var(--text-muted)", "marginBottom": "8px"}),
            html.Div([
                html.Div([
                    dbc.Input(id="input-profile-waist", type="number", min=40, max=200, placeholder="Cintura (cm)"),
                ], style={"flex": "1"}),
                html.Div([
                    dbc.Input(id="input-profile-hip", type="number", min=40, max=200, placeholder="Quadril (cm)"),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "12px"}),
        ], className="form-group"),

        html.Button("Salvar Perfil", id="btn-save-profile", n_clicks=0, className="btn-health full"),
        html.Div(id="profile-alert-container", style={"marginTop": "12px"}),
    ], className="health-card", style={"marginTop": "12px"})

    return html.Div([header, selector, form, html.Div(id="profile-load-trigger", style={"display": "none"})])


@callback(
    [Output("profile-selector", "options"),
     Output("profile-selector", "value"),
     Output("input-profile-name", "value"),
     Output("input-profile-sex", "value"),
     Output("input-profile-age", "value"),
     Output("input-profile-height", "value"),
     Output("input-profile-activity", "value"),
     Output("input-profile-waist", "value"),
     Output("input-profile-hip", "value"),
     Output("profile-alert-container", "children")],
    [Input("profile-load-trigger", "children"),
     Input("profile-selector", "value"),
     Input("btn-new-profile", "n_clicks"),
     Input("btn-save-profile", "n_clicks")],
    [State("input-profile-name", "value"),
     State("input-profile-sex", "value"),
     State("input-profile-age", "value"),
     State("input-profile-height", "value"),
     State("input-profile-activity", "value"),
     State("input-profile-waist", "value"),
     State("input-profile-hip", "value")]
)
def handle_profile(load_trigger, selected_user_id, btn_new, btn_save, name, sex, age, height, activity, waist, hip):
    trigger_id = ctx.triggered_id
    alert = no_update

    if trigger_id == "btn-new-profile":
        return no_update, None, "", "M", 30, 170, "moderate", None, None, html.Div("Preencha os dados do novo perfil.", className="alert-health alert-info")

    db = SessionLocal()
    try:
        if trigger_id == "btn-save-profile":
            if selected_user_id:
                user = db.query(User).filter(User.id == int(selected_user_id)).first()
            else:
                user = User()
                db.add(user)

            user.name = name or "Novo Membro"
            user.sex = sex or "M"
            user.age = age or 30
            user.height_cm = height or 170.0
            user.activity_level = activity or "moderate"
            user.waist_cm = waist if waist else None
            user.hip_cm = hip if hip else None

            db.query(User).update({User.is_active: False})
            user.is_active = True
            db.commit()
            selected_user_id = str(user.id)
            alert = html.Div(f"✓ Perfil '{user.name}' salvo!", className="alert-health alert-success")

        elif trigger_id == "profile-selector" and selected_user_id:
            db.query(User).update({User.is_active: False})
            user = db.query(User).filter(User.id == int(selected_user_id)).first()
            if user:
                user.is_active = True
                db.commit()
                alert = html.Div(f"Perfil de {user.name} ativado.", className="alert-health alert-success")

        users = db.query(User).all()
        options = [{"label": u.name, "value": str(u.id)} for u in users]

        user_to_load = None
        if selected_user_id:
            user_to_load = db.query(User).filter(User.id == int(selected_user_id)).first()
        if not user_to_load:
            user_to_load = db.query(User).filter(User.is_active == True).first()
            if user_to_load:
                selected_user_id = str(user_to_load.id)

        if user_to_load:
            return (options, selected_user_id, user_to_load.name, user_to_load.sex,
                    user_to_load.age, user_to_load.height_cm, user_to_load.activity_level,
                    user_to_load.waist_cm, user_to_load.hip_cm, alert)
        else:
            return options, None, "", "M", 30, 170, "moderate", None, None, alert
    finally:
        db.close()
