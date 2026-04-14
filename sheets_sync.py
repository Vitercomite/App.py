import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os


def sync_to_google_sheets(df_rdp, df_study):
    """Sincroniza dados com Google Sheets. Requer service_account.json."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    if not os.path.exists("service_account.json"):
        return "⚠️ service_account.json não encontrado – sync desativado"

    try:
        creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
        gc = gspread.authorize(creds)

        try:
            sh = gc.open("Vitor Empire Dashboard")
        except gspread.SpreadsheetNotFound:
            sh = gc.create("Vitor Empire Dashboard")

        existing_titles = [ws.title for ws in sh.worksheets()]

        # ── Aba RDP ──────────────────────────────────
        if "RDP" in existing_titles:
            worksheet_rdp = sh.worksheet("RDP")
        else:
            worksheet_rdp = sh.add_worksheet("RDP", 1000, 20)

        if not df_rdp.empty:
            data_rdp = [df_rdp.columns.tolist()] + df_rdp.astype(str).values.tolist()
            worksheet_rdp.clear()
            worksheet_rdp.update(data_rdp)

        # ── Aba Estudo ───────────────────────────────
        if "Estudo" in existing_titles:
            worksheet_study = sh.worksheet("Estudo")
        else:
            worksheet_study = sh.add_worksheet("Estudo", 1000, 10)

        if not df_study.empty:
            data_study = [df_study.columns.tolist()] + df_study.astype(str).values.tolist()
            worksheet_study.clear()
            worksheet_study.update(data_study)

        # ── Aba KPIs ─────────────────────────────────
        if "KPIs" not in existing_titles:
            ws_kpi = sh.add_worksheet("KPIs", 50, 10)
        else:
            ws_kpi = sh.worksheet("KPIs")

        if not df_rdp.empty:
            avg_eff = df_rdp['efetividade'].astype(float).mean() if 'efetividade' in df_rdp.columns else 0
            avg_nps = df_rdp['nps_score'].astype(float).mean() if 'nps_score' in df_rdp.columns else 0
            total = len(df_rdp)
            kpi_data = [
                ["KPI", "Valor"],
                ["Total de RDPs", str(total)],
                ["Efetividade Média", f"{avg_eff:.1f}%"],
                ["NPS Médio", f"{avg_nps:.1f}"],
                ["Última Atualização", pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")],
            ]
            ws_kpi.clear()
            ws_kpi.update(kpi_data)

        return sh.url

    except Exception as e:
        return f"⚠️ Erro no sync: {str(e)}"
