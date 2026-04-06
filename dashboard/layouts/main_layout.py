"""Main layout — no sidebar, single mobile container."""
from dash import html, dcc


def create_layout():
    return html.Div([
        dcc.Location(id="url"),
        html.Div(id="page-content", className="app-container"),
    ])
