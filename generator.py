import google.generativeai as genai
import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF
import requests


# 🔥 FIX UNICODE (FPDF)
def safe_text(text):
    if not text:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


class RDPGenerator:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada.")

        genai.configure(api_key=api_key)

        # 🔥 fallback de modelo
        for m in [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro"
        ]:
            try:
                self.model = genai.GenerativeModel(m)
                break
            except:
                continue

    # 🔥 anti-crash IA
    def safe_generate(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return (response.text or "").strip()
        except Exception as e:
            return f"Erro IA: {str(e)}"

    def extract_json(self, text):
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except:
            return {}

    # ─────────────────────────────
    def get_ai_analysis(self, data):
        prompt = f"""
Retorne APENAS JSON válido:

{{
 "resumo_pt":"...",
 "resumo_de":"...",
 "status":"On Track | At Risk | Delayed",
 "risco_atraso":"Baixo | Médio | Alto",
 "next_steps_pt":"...",
 "next_steps_de":"...",
 "nps_score":80,
 "customer_climate":"..."
}}

Dados:
{json.dumps(data, ensure_ascii=False)}
"""
        text = self.safe_generate(prompt)

        try:
            return self.extract_json(text)
        except:
            return {
                "resumo_pt": "Execução normal",
                "resumo_de": "Normal",
                "status": "On Track",
                "risco_atraso": "Baixo",
                "next_steps_pt": "Continuar",
                "next_steps_de": "Weiter",
                "nps_score": 80,
                "customer_climate": "Neutro"
            }

    # ─────────────────────────────
    def generate_charts(self, efetivo, espera, efetividade):
        fig, ax = plt.subplots()
        ax.pie([efetivo, espera], labels=["Efetivo", "Espera"], autopct='%1.1f%%')
        path = "chart.png"
        plt.savefig(path)
        plt.close()
        return path

    # ─────────────────────────────
    def create_pdf(
        self,
        data,
        cliente,
        projeto,
        atividades,
        impedimentos,
        clima_cliente,
        h_inicio,
        h_fim,
        h_espera,
        h_efetivo,
        total_h,
        efetividade,
        ia_content,
        chart_path,
        next_steps_manual=""
    ):

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", size=12)

        pdf.cell(0, 10, safe_text(f"Cliente: {cliente}"), ln=True)
        pdf.cell(0, 10, safe_text(f"Projeto: {projeto}"), ln=True)
        pdf.cell(0, 10, safe_text(f"Data: {data}"), ln=True)

        pdf.ln(5)

        pdf.multi_cell(0, 8, safe_text("ATIVIDADES"))
        pdf.multi_cell(0, 6, safe_text(atividades))

        pdf.ln(5)

        pdf.multi_cell(0, 8, safe_text("ANALISE IA"))
        pdf.multi_cell(0, 6, safe_text(ia_content.get("resumo_pt", "")))

        pdf.ln(5)

        pdf.cell(0, 10, safe_text(f"Efetividade: {efetividade}%"), ln=True)

        if chart_path and os.path.exists(chart_path):
            pdf.image(chart_path, w=100)

        filename = f"RDP_{str(data)}.pdf"
        pdf.output(filename)

        return filename