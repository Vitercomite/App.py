import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from dotenv import load_dotenv


def send_rdp_email(pdf_path, resumo_ia, link_sheets):
    load_dotenv()
    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    gestor = os.getenv("GESTOR_EMAIL", "")
    rh = os.getenv("RH_EMAIL", "")
    to_emails = [e for e in [gestor, rh] if e]

    if not from_email or not password:
        raise ValueError("SMTP_EMAIL e SMTP_PASSWORD não configurados no .env")
    if not to_emails:
        raise ValueError("Configure GESTOR_EMAIL e/ou RH_EMAIL no .env")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = f"RDP Executivo Dürr – {datetime.now().strftime('%d/%m/%Y')} | Vitor Emílio"

    body = f"""Prezado(a),

Segue o Relatório Diário de Progresso (RDP) com análise gerada por IA.

📋 RESUMO DO DIA:
{resumo_ia}

📊 Dashboard completo (RDPs + Estudo FUVEST):
{link_sheets}

Documento PDF em anexo com análise bilíngue (PT/DE).

Atenciosamente,
Vitor Emílio Quirino
Técnico de Mecatrônica | Dürr Brasil
linkedin.com/in/vitor-quirino
"""

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Anexar PDF se existir
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_emails, msg.as_string())
    server.quit()
    return True


def send_weekly_summary(df_rdp, df_study, link_sheets):
    """Envia resumo semanal automático."""
    load_dotenv()
    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    to_emails = [e for e in [os.getenv("GESTOR_EMAIL"), os.getenv("RH_EMAIL")] if e]

    if not from_email or not to_emails:
        return False

    avg_eff = df_rdp['efetividade'].astype(float).mean() if not df_rdp.empty and 'efetividade' in df_rdp.columns else 0
    avg_nps = df_rdp['nps_score'].astype(float).mean() if not df_rdp.empty and 'nps_score' in df_rdp.columns else 0
    total_study_h = df_study['horas_estudo'].astype(float).sum() if not df_study.empty and 'horas_estudo' in df_study.columns else 0

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = f"Resumo Semanal – Semana {datetime.now().isocalendar()[1]}/{datetime.now().year} | Vitor Emílio"

    body = f"""Resumo Semanal – Dürr Brasil

📊 KPIs da Semana:
• Efetividade Média: {avg_eff:.1f}%
• NPS Médio: {avg_nps:.1f}/100
• RDPs Registrados: {len(df_rdp)}

📚 FUVEST Progress:
• Horas de Estudo: {total_study_h:.1f}h

Dashboard completo: {link_sheets}

Vitor Emílio Quirino | Dürr Brasil
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_emails, msg.as_string())
    server.quit()
    return True
