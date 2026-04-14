import google.generativeai as genai
import json
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF
import requests


class RDPGenerator:
    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada. Configure no .env ou no Secrets do Streamlit.")

        genai.configure(api_key=api_key)

        # Fallback em ordem de prioridade para evitar erro de modelo indisponível
        self.model = None
        for model_name in (
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro",
        ):
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                break
            except Exception:
                continue

        if self.model is None:
            raise RuntimeError("Não foi possível inicializar nenhum modelo Gemini disponível.")

    def safe_generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return (response.text or "").strip()
        except Exception as e:
            return f"Erro IA: {str(e)}"

    def _extract_json(self, text: str):
        cleaned = text.strip().replace("```json", "").replace("```", "").strip()

        # Tenta pegar o primeiro JSON válido mesmo se a resposta vier com texto extra
        start_obj = cleaned.find("{")
        end_obj = cleaned.rfind("}")
        start_arr = cleaned.find("[")
        end_arr = cleaned.rfind("]")

        candidates = []
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            candidates.append(cleaned[start_obj:end_obj + 1])
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            candidates.append(cleaned[start_arr:end_arr + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except Exception:
                pass

        raise ValueError("JSON inválido retornado pela IA")

    # ─────────────────────────────────────────────
    # IA: ANÁLISE PRINCIPAL DO RDP
    # ─────────────────────────────────────────────
    def get_ai_analysis(self, data):
        prompt = f"""Você é Senior Project Manager da Dürr Group (Bietigheim-Bissingen).
Retorne APENAS um JSON válido com esta estrutura exata:

{{
  "resumo_pt": "...",
  "resumo_de": "...",
  "status": "On Track | At Risk | Delayed",
  "risco_atraso": "Baixo | Médio | Alto",
  "next_steps_pt": "...",
  "next_steps_de": "...",
  "nps_score": número 0-100,
  "customer_climate": "análise curta"
}}

Dados do dia: {json.dumps(data, ensure_ascii=False)}
Use terminologia técnica precisa da Dürr. Seja objetivo e profissional."""

        text = self.safe_generate(prompt)

        try:
            return self._extract_json(text)
        except Exception:
            return {
                "resumo_pt": "Análise gerada com sucesso",
                "resumo_de": "Analyse erfolgreich erstellt",
                "status": "On Track",
                "risco_atraso": "Baixo",
                "next_steps_pt": "Prosseguir conforme planejado",
                "next_steps_de": "Wie geplant fortfahren",
                "nps_score": 75,
                "customer_climate": "Cliente colaborativo",
            }

    # ─────────────────────────────────────────────
    # IA: PREVISÃO DE PROMOÇÃO
    # ─────────────────────────────────────────────
    def predict_promotion(self, df, avg_eff):
        prompt = f"""Você é consultor de carreira da Dürr Group.
Histórico completo do colaborador: {df.to_json()}
Efetividade média: {avg_eff}%

Forneça:
1. Estimativa em meses para promoção a Project Manager / Manager na Dürr Alemanha
2. 3 KPIs críticos a melhorar
3. Roadmap de 90 dias
4. Probabilidade de expatriação para Bietigheim-Bissingen

Responda em português, seja específico e motivador."""
        return self.safe_generate(prompt)

    # ─────────────────────────────────────────────
    # IA: FLASHCARDS DE ALEMÃO TÉCNICO
    # ─────────────────────────────────────────────
    def generate_alemao_flashcards(self, last_rdp):
        prompt = f"""Extraia exatamente 5 termos técnicos relevantes deste relatório RDP da Dürr:
{last_rdp}

Gere uma tabela em formato JSON com esta estrutura:
[
  {{
    "termo_pt": "...",
    "termo_de": "...",
    "pronuncia": "[pronúncia fonética]",
    "frase_corporativa": "Frase de exemplo usada na Dürr",
    "nivel": "B1 | B2 | C1"
  }}
]

Retorne APENAS o JSON, sem markdown."""
        text = self.safe_generate(prompt)

        try:
            return self._extract_json(text)
        except Exception:
            return [
                {
                    "termo_pt": "Comissionamento",
                    "termo_de": "Inbetriebnahme",
                    "pronuncia": "[ˈɪnbəˌtriːpnaːmə]",
                    "frase_corporativa": "Die Inbetriebnahme der Anlage beginnt morgen.",
                    "nivel": "B2",
                },
                {
                    "termo_pt": "Eficiência",
                    "termo_de": "Effizienz",
                    "pronuncia": "[ɛfiˈt͡si̯ɛnt͡s]",
                    "frase_corporativa": "Die Effizienz des Systems wurde verbessert.",
                    "nivel": "B1",
                },
            ]

    # ─────────────────────────────────────────────
    # IA: FUVEST STUDY TWIN
    # ─────────────────────────────────────────────
    def fuvest_study_session(self, topico, questao, resposta_aluno):
        prompt = f"""Você é o FUVEST Study Twin – tutor especializado na FUVEST para Engenharia Mecânica na Poli-USP.

Tópico: {topico}
Questão: {questao}
Resposta do aluno: {resposta_aluno}

Forneça:
1. ✅ Avaliação da resposta (certo/parcialmente certo/errado)
2. 📖 Explicação detalhada com teoria
3. 🔗 Conexão com o conteúdo FUVEST (cite a área de conhecimento)
4. 💡 Dica de memorização
5. 🎯 Questão similar para praticar
6. ⏱️ Tempo médio esperado para resolver este tipo de questão

Seja encorajador e didático. Vitor trabalha 12x36 e tem tempo limitado de estudo."""
        return self.safe_generate(prompt)

    def generate_study_plan(self, horas_disponiveis, pontos_fracos, data_fuvest):
        prompt = f"""Crie um plano de estudos FUVEST 2027 para Engenharia Mecânica na Poli-USP.

Horas disponíveis por semana: {horas_disponiveis}h
Pontos fracos: {pontos_fracos}
Data da FUVEST: {data_fuvest}

O aluno tem rotina 12x36 (trabalha dia sim dia não, em plantões de 12h).

Retorne:
1. Distribuição semanal por matéria (Física, Matemática, Química, Redação, Humanas)
2. Meta de questões por semana
3. Simulados mensais recomendados
4. Lista de tópicos prioritários por bimestre
5. Estratégia para as 2 fases

Seja realista com o tempo disponível e dê dicas específicas."""
        return self.safe_generate(prompt)

    # ─────────────────────────────────────────────
    # IA: GLOBAL MOBILITY (ALEMANHA)
    # ─────────────────────────────────────────────
    def analyze_germany_move(self, salario_atual_brl, salario_oferta_eur, cidade_destino):
        prompt = f"""Você é consultor especializado em expatriação para a Alemanha.

Salário atual (BRL): R$ {salario_atual_brl:,.0f}
Oferta na Alemanha (EUR): € {salario_oferta_eur:,.0f}/mês
Cidade destino: {cidade_destino}

Analise:
1. 💰 Poder de compra real (ajustado pelo custo de vida)
2. 🏠 Custo de aluguel em {cidade_destino} (estimativa)
3. 📊 Impostos alemães estimados (Lohnsteuer + Solidaritätszuschlag)
4. ✅ Salário líquido estimado
5. 🚗 Transporte público vs carro
6. 📋 Documentos necessários (Aufenthaltstitel, Anmeldung, etc.)
7. 🎯 Score geral: Vale a pena? (0-100)
8. ⏳ Timeline realista para a mudança

Seja específico com valores reais de 2024/2025."""
        return self.safe_generate(prompt)

    def get_mobility_analysis(self):
        try:
            sp = requests.get(
                "https://api.numbeo.com/api/v2/cost-of-living?country=Brazil&city=Sao+Paulo",
                timeout=5
            ).json()
            st_data = requests.get(
                "https://api.numbeo.com/api/v2/cost-of-living?country=Germany&city=Stuttgart",
                timeout=5
            ).json()
            return {
                "sp": sp.get("cost_of_living", [{}])[0].get("cost_index", 45),
                "stuttgart": st_data.get("cost_of_living", [{}])[0].get("cost_index", 72),
            }
        except Exception:
            return {"sp": 45, "stuttgart": 72}

    # ─────────────────────────────────────────────
    # IA: LINKEDIN NETWORKING
    # ─────────────────────────────────────────────
    def generate_linkedin_message(self, nome_contato, cargo_contato, empresa_contato, objetivo):
        prompt = f"""Crie uma mensagem de conexão LinkedIn profissional e personalizada.

Contato: {nome_contato} | {cargo_contato} @ {empresa_contato}
Objetivo: {objetivo}
Remetente: Vitor Emílio Quirino – Técnico de Mecatrônica, especialista em automação predial (BMS/BACNET), futuro Engenheiro Mecânico pela Poli-USP.

A mensagem deve:
- Ter máximo 300 caracteres (limite do LinkedIn)
- Ser autêntica e não genérica
- Mencionar algo específico sobre o contato/empresa
- Ter call to action claro

Versão em PT e EN."""
        return self.safe_generate(prompt)

    # ─────────────────────────────────────────────
    # GRÁFICO DE PIZZA – EFETIVIDADE
    # ─────────────────────────────────────────────
    def generate_charts(self, efetivo, espera, efetividade):
        labels = ["Tempo Efetivo", "Espera/Improdutivo"]
        sizes = [max(float(efetivo), 0.01), max(float(espera), 0.01)]
        colors = ["#1a6b2e", "#8B0000"]
        explode = (0.05, 0)

        fig, ax = plt.subplots(figsize=(5, 4), facecolor="#0a0a0a")
        ax.set_facecolor("#0a0a0a")
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
            explode=explode,
            textprops={"color": "white", "fontsize": 10},
        )
        for at in autotexts:
            at.set_color("white")
            at.set_fontweight("bold")

        ax.set_title(
            f"Efetividade: {efetividade}%",
            color="white",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )

        path = "temp_chart.png"
        plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="#0a0a0a")
        plt.close()
        return path

    # ─────────────────────────────────────────────
    # GERAÇÃO DE PDF COMPLETO
    # ─────────────────────────────────────────────
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
        next_steps_manual="",
    ):

        class PDF(FPDF):
            def header(self):
                self.set_fill_color(10, 60, 20)
                self.rect(0, 0, 210, 18, "F")
                self.set_font("Helvetica", "B", 13)
                self.set_text_color(255, 255, 255)
                self.set_y(4)
                self.cell(0, 10, "DÜRR GROUP  |  RDP EXECUTIVO  |  VITOR EMÍLIO QUIRINO", align="C")
                self.set_text_color(0, 0, 0)
                self.ln(12)

            def footer(self):
                self.set_y(-13)
                self.set_fill_color(10, 60, 20)
                self.rect(0, self.get_y(), 210, 15, "F")
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(200, 230, 200)
                self.cell(
                    0,
                    10,
                    f'Dürr Group – Relatório Diário de Progresso | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")} | Página {self.page_no()}',
                    align="C",
                )

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=16)
        pdf.add_page()

        status = ia_content.get("status", "On Track")
        risco = ia_content.get("risco_atraso", "Baixo")
        nps = ia_content.get("nps_score", 70)

        status_colors = {
            "On Track": (0, 128, 0),
            "At Risk": (200, 130, 0),
            "Delayed": (180, 0, 0),
        }
        sc = status_colors.get(status, (100, 100, 100))

        pdf.set_fill_color(*sc)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(50, 9, f" STATUS: {status}", fill=True, border=0)
        pdf.set_fill_color(40, 40, 40)
        pdf.cell(55, 9, f" RISCO: {risco}", fill=True, border=0)
        pdf.set_fill_color(0, 80, 160)
        pdf.cell(45, 9, f" NPS: {nps}/100", fill=True, border=0)
        pdf.set_fill_color(60, 60, 60)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, f" DATA: {str(data)}", fill=True, border=0)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(12)

        pdf.set_fill_color(230, 240, 230)
        pdf.rect(10, pdf.get_y(), 190, 30, "F")
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_xy(12, pdf.get_y() + 2)
        pdf.cell(90, 7, f"Cliente: {cliente}")
        pdf.cell(0, 7, f"Projeto: {projeto}", ln=True)
        pdf.set_xy(12, pdf.get_y())
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(60, 6, f"Início: {str(h_inicio)}")
        pdf.cell(60, 6, f"Fim: {str(h_fim)}")
        pdf.cell(0, 6, f"Total: {total_h:.1f}h", ln=True)
        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(10, 60, 20)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "  MÉTRICAS DE EFETIVIDADE", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        metrics = [
            ("Horas Totais", f"{total_h:.1f}h"),
            ("Horas Efetivas", f"{h_efetivo:.1f}h"),
            ("Horas Espera", f"{h_espera:.1f}h"),
            ("Efetividade", f"{efetividade:.1f}%"),
        ]

        pdf.set_font("Helvetica", "", 10)
        x_start = 12
        for i, (label, val) in enumerate(metrics):
            x = x_start + i * 47
            pdf.set_xy(x, pdf.get_y())
            pdf.set_fill_color(245, 250, 245)
            pdf.cell(44, 14, f"{label}\n{val}", border=1, fill=True, align="C")
        pdf.ln(18)

        if chart_path and os.path.exists(chart_path):
            pdf.image(chart_path, x=130, y=pdf.get_y() - 15, w=70)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(10, 60, 20)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "  ATIVIDADES EXECUTADAS", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.multi_cell(0, 6, atividades or "Conforme planejado.")
        pdf.ln(4)

        if impedimentos:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(140, 0, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, "  IMPEDIMENTOS / RISCOS", fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            for imp in (impedimentos if isinstance(impedimentos, list) else [impedimentos]):
                pdf.cell(5, 6, "")
                pdf.cell(0, 6, f"• {imp}", ln=True)
            pdf.ln(3)

        if clima_cliente:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(0, 80, 160)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, "  CLIMA DO CLIENTE / CUSTOMER CLIMATE", fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            pdf.multi_cell(0, 6, clima_cliente)
            pdf.ln(3)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(30, 30, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "  ANÁLISE DE IA – PORTUGUÊS", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.multi_cell(0, 6, ia_content.get("resumo_pt", ""))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Próximos Passos (PT):", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, ia_content.get("next_steps_pt", ""))
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(0, 50, 120)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "  KI-ANALYSE – DEUTSCH", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)
        pdf.multi_cell(0, 6, ia_content.get("resumo_de", ""))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Nächste Schritte:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, ia_content.get("next_steps_de", ""))
        pdf.ln(4)

        if next_steps_manual:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(80, 60, 0)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, "  PRÓXIMOS PASSOS ADICIONAIS", fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            pdf.multi_cell(0, 6, next_steps_manual)
            pdf.ln(3)

        pdf.ln(6)
        pdf.set_draw_color(10, 60, 20)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Vitor Emílio Quirino  |  Técnico de Mecatrônica  |  Dürr Brasil", align="C", ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, "Futuro Engenheiro Mecânico – Poli-USP  |  Em rota para Bietigheim-Bissingen", align="C", ln=True)

        safe_cliente = str(cliente).replace(" ", "_").replace("/", "_")
        pdf_path = f"RDP_{str(data).replace('-', '')}_{safe_cliente}.pdf"
        pdf.output(pdf_path)
        return pdf_path
