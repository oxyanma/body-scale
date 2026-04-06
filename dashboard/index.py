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
from i18n import t

logger = logging.getLogger(__name__)

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
    elif pathname == "/composition":
        measurement_id = None
        if search:
            params = parse_qs(search.lstrip("?"))
            measurement_id = params.get("id", [None])[0]
        return create_composition_view(measurement_id=measurement_id)
    elif pathname == "/comparison":
        id_a, id_b = None, None
        if search:
            params = parse_qs(search.lstrip("?"))
            id_a = params.get("a", [None])[0]
            id_b = params.get("b", [None])[0]
        return create_comparison_view(id_a, id_b)
    elif pathname == "/history":
        return create_history_view()
    elif pathname == "/profile":
        return create_profile_view()
    elif pathname == "/settings":
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


if __name__ == "__main__":
    app.run(debug=True, port=8050)
