from dash import html, dcc
from dash.dependencies import Input, Output
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

logger = logging.getLogger(__name__)

# Layout base
app.layout = create_layout()

# Routing with query parameter support
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("url", "search"),
)
def render_page_content(pathname, search):
    if pathname == "/":
        show_goal_stats = False
        if search:
            params = parse_qs(search.lstrip("?"))
            show_goal_stats = "saved" in params
        content = create_overview_layout(show_goal_stats=show_goal_stats)
    elif pathname == "/composicao":
        # Support ?id=X to show specific measurement
        measurement_id = None
        if search:
            params = parse_qs(search.lstrip("?"))
            measurement_id = params.get("id", [None])[0]
        content = create_composition_view(measurement_id=measurement_id)
    elif pathname == "/comparacao":
        id_a, id_b = None, None
        if search:
            params = parse_qs(search.lstrip("?"))
            id_a = params.get("a", [None])[0]
            id_b = params.get("b", [None])[0]
        content = create_comparison_view(id_a, id_b)
    elif pathname == "/historico":
        content = create_history_view()
    elif pathname == "/perfil":
        content = create_profile_view()
    elif pathname == "/config":
        content = create_settings_view()
    else:
        content = html.Div([
            html.Div([
                dcc.Link(html.Button("‹", className="back-btn"), href="/"),
                html.H1("Página não encontrada"),
            ], className="page-header"),
            html.Div([
                html.P("404 — Esta página não existe.", style={"textAlign": "center", "padding": "40px 0", "color": "var(--text-secondary)"}),
                dcc.Link("← Voltar ao Dashboard", href="/", style={"display": "block", "textAlign": "center", "color": "var(--blue)", "fontWeight": "600"})
            ], className="health-card")
        ])

    return content

if __name__ == "__main__":
    app.run(debug=True, port=8050)
