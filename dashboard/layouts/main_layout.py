"""Main layout — no sidebar, single mobile container."""
from dash import html, dcc
from i18n import LANGUAGES, get_language


def create_layout():
    lang_buttons = []
    for code, info in LANGUAGES.items():
        lang_buttons.append(
            html.Button(info['flag'], id=f"lang-{code}", className="lang-btn",
                        title=info['name'],
                        style={"opacity": "1"} if code == get_language() else {})
        )

    lang_selector = html.Div(lang_buttons, className="lang-selector", id="lang-selector")

    return html.Div([
        dcc.Location(id="url"),
        lang_selector,
        html.Div(id="page-content", className="app-container"),
    ])
