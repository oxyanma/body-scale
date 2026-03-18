"""Settings view — Light theme, mobile-friendly."""
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from i18n import t


def create_settings_view():
    header = html.Div([
        dcc.Link(html.Button("‹", className="back-btn"), href="/"),
        html.H1(t("settings.title")),
    ], className="page-header")

    # Data management
    data_section = html.Div([
        html.Div(t("settings.manage_data"), style={"fontFamily": "'Nunito'", "fontWeight": "800",
                                            "fontSize": "1rem", "color": "var(--text-primary)", "marginBottom": "12px"}),
        html.Div([
            html.Button(t("settings.export_csv"), id="btn-export-csv", n_clicks=0,
                        className="btn-outline-health", style={"marginBottom": "8px"}),
            html.Button(t("settings.backup_db"), id="btn-backup-db", n_clicks=0,
                        className="btn-outline-health", style={"marginBottom": "8px"}),
            html.Button(t("settings.clear_history"), id="btn-clear-history", n_clicks=0,
                        className="btn-outline-health", style={"marginBottom": "8px", "color": "var(--red)", "borderColor": "var(--red-light)"}),
        ]),
        html.Div(id="settings-data-alert"),
    ], className="health-card")

    # Privacy
    privacy_section = html.Div([
        html.Div(t("settings.privacy"), style={"fontFamily": "'Nunito'", "fontWeight": "800",
                                        "fontSize": "1rem", "color": "var(--text-primary)", "marginBottom": "12px"}),
        html.P(t("settings.privacy_text"),
               style={"color": "var(--text-secondary)", "fontSize": "0.85rem", "lineHeight": "1.6"}),
        html.Button(t("settings.delete_all_btn"), id="btn-delete-all", n_clicks=0,
                    className="btn-outline-health",
                    style={"color": "var(--red)", "borderColor": "var(--red-light)", "marginTop": "8px"}),
        html.Div(id="settings-privacy-alert"),
    ], className="health-card")

    # About
    about_section = html.Div([
        html.Div(t("settings.about"), style={"fontFamily": "'Nunito'", "fontWeight": "800",
                                  "fontSize": "1rem", "color": "var(--text-primary)", "marginBottom": "8px"}),
        html.Div([
            html.Span("BioScale", style={"fontFamily": "'Nunito'", "fontWeight": "800", "color": "var(--blue)", "fontSize": "1.1rem"}),
            html.Span(" v2.0.0", style={"color": "var(--text-muted)", "marginLeft": "6px"}),
        ]),
        html.P(t("settings.about_desc"),
               style={"color": "var(--text-secondary)", "fontSize": "0.82rem", "marginTop": "4px"}),
        html.P(t("settings.about_copyright"),
               style={"color": "var(--text-muted)", "fontSize": "0.72rem", "fontStyle": "italic"}),
    ], className="health-card")

    # Delete-all confirmation modal
    delete_all_modal = dbc.Modal([
        dbc.ModalHeader(t("settings.delete_all_title"), style={"color": "var(--red)"}),
        dbc.ModalBody([
            html.P(t("settings.delete_all_confirm"), style={"fontWeight": "600", "color": "var(--text-primary)"}),
            html.P(t("settings.delete_all_warning"),
                   style={"color": "var(--text-secondary)", "fontSize": "0.85rem"}),
        ]),
        dbc.ModalFooter([
            dbc.Button(t("common.cancel"), id="btn-cancel-delete-all", className="btn-outline-health", style={"width": "auto", "marginRight": "8px"}),
            dbc.Button(t("settings.delete_all_btn_confirm"), id="btn-confirm-delete-all", className="btn-danger"),
        ]),
    ], id="modal-delete-all", is_open=False)

    return html.Div([header, data_section, privacy_section, about_section, delete_all_modal])


@callback(
    Output("settings-data-alert", "children"),
    [Input("btn-export-csv", "n_clicks"),
     Input("btn-backup-db", "n_clicks"),
     Input("btn-clear-history", "n_clicks")],
    prevent_initial_call=True
)
def handle_data_actions(csv_clicks, backup_clicks, clear_clicks):
    from dash import ctx
    if not ctx.triggered_id:
        return no_update

    if ctx.triggered_id == "btn-export-csv":
        try:
            from database.db import SessionLocal
            from database.models import Measurement, User
            import csv
            from pathlib import Path

            db = SessionLocal()
            try:
                user = db.query(User).filter(User.is_active == True).first()
                if not user:
                    return html.Div(t("settings.no_active_profile"), className="alert-health alert-info")

                measurements = db.query(Measurement).filter(
                    Measurement.user_id == user.id
                ).order_by(Measurement.created_at.desc()).all()

                desktop = Path.home() / "Desktop"
                filepath = desktop / f"bioscale_{user.name.lower().replace(' ', '_')}.csv"

                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([t("csv.date"), t("csv.weight"), t("csv.bmi"), t("csv.fat"), t("csv.muscle"),
                                    t("csv.water"), t("csv.visceral"), t("csv.metabolic_age"), t("csv.bmr"), t("csv.protein")])
                    for m in measurements:
                        writer.writerow([
                            m.measured_at.strftime("%d/%m/%Y %H:%M") if m.measured_at else "",
                            m.weight_kg, m.bmi,
                            m.body_fat_percent, m.muscle_mass_percent, m.body_water_percent,
                            m.visceral_fat, m.metabolic_age, m.bmr, m.protein_percent
                        ])
            finally:
                db.close()

            return html.Div(t("settings.csv_exported").format(path=filepath), className="alert-health alert-success")
        except Exception as e:
            return html.Div(f"{t('common.error')}: {e}", className="alert-health alert-danger")

    elif ctx.triggered_id == "btn-backup-db":
        try:
            import shutil
            from pathlib import Path
            src = Path.home() / ".bioscale" / "bioscale.db"
            dst = Path.home() / "Desktop" / "bioscale_backup.db"
            shutil.copy2(src, dst)
            return html.Div(t("settings.backup_saved").format(path=dst), className="alert-health alert-success")
        except Exception as e:
            return html.Div(f"{t('common.error')}: {e}", className="alert-health alert-danger")

    elif ctx.triggered_id == "btn-clear-history":
        try:
            from database.db import SessionLocal
            from database.models import Measurement, User
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.is_active == True).first()
                if user:
                    db.query(Measurement).filter(Measurement.user_id == user.id).delete()
                    db.commit()
                    return html.Div(t("settings.history_cleared"), className="alert-health alert-info")
            finally:
                db.close()
        except Exception as e:
            return html.Div(f"{t('common.error')}: {e}", className="alert-health alert-danger")

    return no_update


@callback(
    Output("modal-delete-all", "is_open"),
    [Input("btn-delete-all", "n_clicks"),
     Input("btn-cancel-delete-all", "n_clicks"),
     Input("btn-confirm-delete-all", "n_clicks")],
    State("modal-delete-all", "is_open"),
    prevent_initial_call=True
)
def toggle_delete_all_modal(open_clicks, cancel, confirm, is_open):
    from dash import ctx as dash_ctx
    if dash_ctx.triggered_id == "btn-delete-all":
        return True
    return False


@callback(
    Output("settings-privacy-alert", "children"),
    Input("btn-confirm-delete-all", "n_clicks"),
    prevent_initial_call=True
)
def handle_delete_all(n):
    if not n:
        return no_update
    try:
        from database.db import SessionLocal
        from database.models import Measurement, User, Goal
        db = SessionLocal()
        try:
            db.query(Measurement).delete()
            db.query(Goal).delete()
            db.query(User).delete()
            db.commit()
            return html.Div(t("settings.all_deleted"), className="alert-health alert-danger")
        finally:
            db.close()
    except Exception as e:
        return html.Div(f"{t('common.error')}: {e}", className="alert-health alert-danger")

