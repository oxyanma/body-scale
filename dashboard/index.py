from dash import html, dcc, ctx, no_update
from dash.dependencies import Input, Output, State
import logging
from urllib.parse import parse_qs

from dashboard.app import app
from dashboard.layouts.main_layout import create_layout
from dashboard.layouts.overview import create_overview_layout
from dashboard.layouts.history_view import create_history_view
from dashboard.layouts.profile_view import create_profile_view
from dashboard.layouts.settings_view import create_settings_view
from dashboard.layouts.composition_view import create_composition_view
from dashboard.layouts.comparison_view import create_comparison_view
from i18n import t, set_language, get_language, LANGUAGES

logger = logging.getLogger(__name__)

# Load language from active user on startup
def _load_user_language():
    try:
        from database.db import SessionLocal
        from database.models import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.is_active == True).first()
            if user and hasattr(user, 'language') and user.language:
                set_language(user.language)
        finally:
            db.close()
    except Exception:
        pass

_load_user_language()

# Layout base
app.layout = create_layout()


def _render_page(pathname, search):
    """Render page content based on pathname."""
    if pathname == "/":
        show_goal_stats = False
        if search:
            params = parse_qs(search.lstrip("?"))
            show_goal_stats = "saved" in params
        return create_overview_layout(show_goal_stats=show_goal_stats)
    elif pathname == "/composicao":
        measurement_id = None
        if search:
            params = parse_qs(search.lstrip("?"))
            measurement_id = params.get("id", [None])[0]
        return create_composition_view(measurement_id=measurement_id)
    elif pathname == "/comparacao":
        id_a, id_b = None, None
        if search:
            params = parse_qs(search.lstrip("?"))
            id_a = params.get("a", [None])[0]
            id_b = params.get("b", [None])[0]
        return create_comparison_view(id_a, id_b)
    elif pathname == "/historico":
        return create_history_view()
    elif pathname == "/perfil":
        return create_profile_view()
    elif pathname == "/config":
        return create_settings_view()
    else:
        return html.Div([
            html.Div([
                dcc.Link(html.Button("‹", className="back-btn"), href="/"),
                html.H1(t("error.page_not_found")),
            ], className="page-header"),
            html.Div([
                html.P(t("error.404_message"), style={"textAlign": "center", "padding": "40px 0", "color": "var(--text-secondary)"}),
                dcc.Link(t("error.back_dashboard"), href="/", style={"display": "block", "textAlign": "center", "color": "var(--blue)", "fontWeight": "600"})
            ], className="health-card")
        ])


# Routing with query parameter support
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("url", "search"),
)
def render_page_content(pathname, search):
    return _render_page(pathname, search)


# Language switching callback
@app.callback(
    [Output("page-content", "children", allow_duplicate=True),
     Output("lang-pt", "style"),
     Output("lang-en", "style"),
     Output("lang-es", "style"),
     Output("lang-fr", "style")],
    [Input("lang-pt", "n_clicks"),
     Input("lang-en", "n_clicks"),
     Input("lang-es", "n_clicks"),
     Input("lang-fr", "n_clicks")],
    [State("url", "pathname"),
     State("url", "search")],
    prevent_initial_call=True
)
def change_language(pt, en, es, fr, pathname, search):
    triggered = ctx.triggered_id
    if not triggered:
        return [no_update] * 5

    lang_map = {'lang-pt': 'pt', 'lang-en': 'en', 'lang-es': 'es', 'lang-fr': 'fr'}
    lang = lang_map.get(triggered, 'pt')
    set_language(lang)

    # Save to database
    try:
        from database.db import SessionLocal
        from database.models import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.is_active == True).first()
            if user:
                user.language = lang
                db.commit()
        finally:
            db.close()
    except Exception:
        pass

    # Update button styles
    styles = []
    for code in LANGUAGES:
        if code == lang:
            styles.append({"opacity": "1"})
        else:
            styles.append({})

    return [_render_page(pathname, search)] + styles


if __name__ == "__main__":
    app.run(debug=True, port=8050)
