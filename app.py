import streamlit as st
import datetime
import os
import tempfile
from dotenv import load_dotenv
from database import (
    init_db, save_rdp, save_study, save_career_goal,
    update_goal_progress, save_flashcard,
    get_history, get_study_history, get_career_goals,
    get_flashcards, get_rdp_stats
)
from generator import RDPGenerator
from sheets_sync import sync_to_google_sheets
from notifier import send_rdp_email
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
load_dotenv()
init_db()

API_KEY = os.getenv("GEMINI_API_KEY", "")

st.set_page_config(
    page_title="Eternal Empire v10.0",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #080f0a; color: #e0e8e2; }

.main-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.8rem; font-weight: 700;
    background: linear-gradient(135deg, #22c55e, #16a34a, #86efac);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: 2px; margin-bottom: 0;
}
.sub-caption { color: #6b9e7c; font-size: 0.85rem; letter-spacing: 1px; }

.kpi-card {
    background: linear-gradient(135deg, #0d2018, #0a1a12);
    border: 1px solid #1a4a2a; border-radius: 12px;
    padding: 16px 20px; text-align: center;
}
.kpi-value { font-family: 'Rajdhani', sans-serif; font-size: 2.2rem; color: #22c55e; font-weight: 700; }
.kpi-label { font-size: 0.75rem; color: #6b9e7c; text-transform: uppercase; letter-spacing: 1px; }

.section-header {
    background: linear-gradient(90deg, #0a3d1a, #051508);
    border-left: 4px solid #22c55e;
    padding: 8px 16px; border-radius: 0 8px 8px 0;
    font-family: 'Rajdhani', sans-serif; font-size: 1.1rem;
    color: #86efac; letter-spacing: 1px; margin: 16px 0 12px;
}

.status-badge {
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-weight: 700; font-size: 0.85rem; letter-spacing: 1px;
}
.status-on-track  { background: #14532d; color: #86efac; }
.status-at-risk   { background: #451a03; color: #fdba74; }
.status-delayed   { background: #450a0a; color: #fca5a5; }

.flashcard-box {
    background: #0d2018; border: 1px solid #1a4a2a;
    border-radius: 10px; padding: 16px; margin: 8px 0;
    transition: border-color 0.2s;
}
.flashcard-box:hover { border-color: #22c55e; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="main-title">🛡️ ETERNAL<br>EMPIRE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-caption">v10.0 – The Supreme Protocol</p>', unsafe_allow_html=True)
    st.divider()

    stats = get_rdp_stats()
    st.metric("Total RDPs", stats['total_rdps'])
    st.metric("Efetividade Média", f"{stats['avg_efetividade']}%")
    st.metric("NPS Médio", f"{stats['avg_nps']}")
    st.metric("On Track", stats['on_track'])
    st.divider()

    if not API_KEY:
        st.error("⚠️ GEMINI_API_KEY não configurado no .env")
    else:
        st.success("✅ Gemini 1.5 Flash conectado")

    st.markdown("**Vitor Emílio Quirino**")
    st.caption("Dürr Brasil • Poli-USP • Bietigheim-Bissingen")
    linkedin = os.getenv("LINKEDIN_PROFILE", "")
    if linkedin:
        st.markdown(f"[LinkedIn]({linkedin})")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎤 Novo RDP",
    "📊 Dashboard",
    "🎯 Carreira",
    "📚 FUVEST Twin",
    "🇩🇪 Alemão Técnico",
    "🌍 Global Mobility"
])

# ═══════════════════════════════════════════════
# TAB 1 – NOVO RDP
# ═══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">📋 Relatório Diário de Progresso</div>', unsafe_allow_html=True)

    # Voz (st.audio_input – disponível no Streamlit 1.31+)
    st.markdown('<div class="section-header">🎙️ Entrada por Voz</div>', unsafe_allow_html=True)
    try:
        audio_bytes = st.audio_input("Grave seu RDP (atividades, impedimentos, next steps)")
        if audio_bytes and API_KEY:
            if st.button("🤖 Transcrever com Gemini"):
                with st.spinner("Transcrevendo..."):
                    import google.generativeai as genai
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(audio_bytes.getvalue())
                        tmp_path = tmp.name
                    audio_file = genai.upload_file(tmp_path, mime_type="audio/wav")
                    transcricao = model.generate_content([
                        "Transcreva este áudio técnico da Dürr. Organize em: ATIVIDADES, IMPEDIMENTOS, NEXT STEPS.",
                        audio_file
                    ]).text
                    st.session_state['atividades_voz'] = transcricao
                    os.unlink(tmp_path)
                    st.success("✅ Transcrito!")
    except Exception:
        st.info("ℹ️ Entrada de voz requer Streamlit ≥ 1.31")

    # Formulário
    st.markdown('<div class="section-header">📝 Dados do RDP</div>', unsafe_allow_html=True)
    with st.form("rdp_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente = st.selectbox("Cliente", [
                "Volkswagen", "General Motors", "Stellantis",
                "Toyota", "BMW", "Mercedes-Benz", "Fiat", "Outro"
            ])
            projeto = st.text_input("Projeto / OS")
        with col2:
            data = st.date_input("Data", datetime.date.today())
            h_inicio = st.time_input("Início", datetime.time(7, 0))
            h_fim = st.time_input("Fim", datetime.time(17, 0))
        with col3:
            h_espera = st.number_input("Horas de Espera", min_value=0.0, max_value=24.0, step=0.5, value=0.0)
            st.caption("Aguarda liberação, peças, etc.")

        atividades = st.text_area(
            "Atividades Executadas",
            value=st.session_state.get('atividades_voz', ''),
            height=140,
            placeholder="Descreva o que foi realizado hoje..."
        )
        col_i, col_c = st.columns(2)
        with col_i:
            impedimentos = st.multiselect("Impedimentos", [
                "Área não liberada", "Falta de peças", "Aguardando segurança",
                "Problema TI", "Equipamento danificado", "Acesso negado",
                "Alteração de escopo", "Outro"
            ])
        with col_c:
            clima_cliente = st.text_area("Clima do Cliente", height=80,
                                         placeholder="Satisfeito, ansioso, neutro...")

        next_steps_manual = st.text_area("Próximos Passos (opcional)", height=80)
        enviar_email = st.checkbox("📧 Enviar e-mail ao gestor após gerar")
        submit = st.form_submit_button("🚀 GERAR RDP SUPREMO", use_container_width=True)

    if submit:
        if not projeto:
            st.error("Informe o nome do Projeto / OS.")
        elif not API_KEY:
            st.error("Configure GEMINI_API_KEY no arquivo .env")
        else:
            with st.spinner("Gerando RDP com IA..."):
                # Cálculos
                dt_inicio = datetime.datetime.combine(data, h_inicio)
                dt_fim = datetime.datetime.combine(data, h_fim)
                total_h = max((dt_fim - dt_inicio).total_seconds() / 3600, 0.1)
                h_efetivo = max(total_h - h_espera, 0)
                efetividade = round((h_efetivo / total_h) * 100, 1)

                raw_data = {
                    "cliente": cliente, "projeto": projeto,
                    "atividades": atividades, "impedimentos": impedimentos,
                    "clima_cliente": clima_cliente, "data": str(data),
                    "total_horas": total_h, "horas_espera": h_espera
                }

                gen = RDPGenerator(API_KEY)
                ia_content = gen.get_ai_analysis(raw_data)
                chart_path = gen.generate_charts(h_efetivo, h_espera, efetividade)

                pdf_path = gen.create_pdf(
                    data=data, cliente=cliente, projeto=projeto,
                    atividades=atividades, impedimentos=impedimentos,
                    clima_cliente=clima_cliente, h_inicio=h_inicio,
                    h_fim=h_fim, h_espera=h_espera, h_efetivo=h_efetivo,
                    total_h=total_h, efetividade=efetividade,
                    ia_content=ia_content, chart_path=chart_path,
                    next_steps_manual=next_steps_manual
                )

                save_rdp(str(data), cliente, projeto, efetividade, h_espera,
                         total_h, ia_content["status"], ia_content["risco_atraso"],
                         ia_content["nps_score"])

                df_rdp = get_history()
                df_study = get_study_history()
                link_sheets = sync_to_google_sheets(df_rdp, df_study)

            # Resultado
            status = ia_content["status"]
            badge_class = {
                "On Track": "status-on-track",
                "At Risk": "status-at-risk",
                "Delayed": "status-delayed"
            }.get(status, "status-on-track")

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Efetividade", f"{efetividade}%")
            col_b.metric("NPS Score", f"{ia_content['nps_score']}/100")
            col_c.metric("Horas Efetivas", f"{h_efetivo:.1f}h")
            col_d.metric("Status", status)

            st.markdown(f"""
            <div style="background:#0d2018;border:1px solid #1a4a2a;border-radius:10px;padding:16px;margin:12px 0">
            <b>📋 Resumo (PT):</b><br>{ia_content.get("resumo_pt", "")}
            <br><br><b>🎯 Next Steps:</b><br>{ia_content.get("next_steps_pt", "")}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#0a1428;border:1px solid #1a2a4a;border-radius:10px;padding:16px;margin:4px 0">
            <b>🇩🇪 Zusammenfassung:</b><br>{ia_content.get("resumo_de", "")}
            <br><br><b>Nächste Schritte:</b><br>{ia_content.get("next_steps_de", "")}
            </div>
            """, unsafe_allow_html=True)

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Baixar PDF", f.read(), pdf_path, "application/pdf", use_container_width=True)

            if link_sheets.startswith("http"):
                st.markdown(f"[📊 Abrir Google Sheets]({link_sheets})")

            if enviar_email:
                try:
                    send_rdp_email(pdf_path, ia_content["resumo_pt"], link_sheets)
                    st.success("📧 E-mail enviado para gestor e RH!")
                except Exception as e:
                    st.warning(f"E-mail não enviado: {e}")

# ═══════════════════════════════════════════════
# TAB 2 – DASHBOARD
# ═══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">📊 Dashboard de Performance</div>', unsafe_allow_html=True)
    df = get_history()

    if df.empty:
        st.info("Nenhum RDP registrado ainda. Gere seu primeiro RDP na aba anterior.")
    else:
        df['data'] = pd.to_datetime(df['data'])
        df['efetividade'] = pd.to_numeric(df['efetividade'], errors='coerce')
        df['nps_score'] = pd.to_numeric(df['nps_score'], errors='coerce')

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-value">{len(df)}</div><div class="kpi-label">Total RDPs</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-value">{df["efetividade"].mean():.1f}%</div><div class="kpi-label">Efetividade Média</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-value">{df["nps_score"].mean():.1f}</div><div class="kpi-label">NPS Médio</div></div>', unsafe_allow_html=True)
        on_track = len(df[df['status'] == 'On Track'])
        k4.markdown(f'<div class="kpi-card"><div class="kpi-value">{on_track}</div><div class="kpi-label">On Track</div></div>', unsafe_allow_html=True)

        st.markdown("")

        col1, col2 = st.columns(2)
        with col1:
            fig_eff = px.line(
                df.sort_values('data'), x='data', y='efetividade',
                title='Efetividade ao Longo do Tempo (%)',
                template='plotly_dark', color_discrete_sequence=['#22c55e']
            )
            fig_eff.update_layout(
                paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018',
                font=dict(color='#86efac')
            )
            st.plotly_chart(fig_eff, use_container_width=True)

        with col2:
            fig_nps = px.bar(
                df.sort_values('data'), x='data', y='nps_score',
                title='NPS Score por RDP',
                template='plotly_dark', color_discrete_sequence=['#16a34a']
            )
            fig_nps.update_layout(
                paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018',
                font=dict(color='#86efac')
            )
            st.plotly_chart(fig_nps, use_container_width=True)

        # Status distribution
        col3, col4 = st.columns(2)
        with col3:
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_status = px.pie(
                status_counts, names='Status', values='Count',
                title='Distribuição de Status',
                template='plotly_dark',
                color_discrete_map={
                    'On Track': '#22c55e',
                    'At Risk': '#f97316',
                    'Delayed': '#ef4444'
                }
            )
            fig_status.update_layout(paper_bgcolor='#0a1a0f', font=dict(color='#86efac'))
            st.plotly_chart(fig_status, use_container_width=True)

        with col4:
            cliente_eff = df.groupby('cliente')['efetividade'].mean().reset_index()
            fig_cli = px.bar(
                cliente_eff, x='cliente', y='efetividade',
                title='Efetividade por Cliente',
                template='plotly_dark', color_discrete_sequence=['#22c55e']
            )
            fig_cli.update_layout(paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018', font=dict(color='#86efac'))
            st.plotly_chart(fig_cli, use_container_width=True)

        # Tabela
        st.markdown('<div class="section-header">📋 Histórico Completo</div>', unsafe_allow_html=True)
        st.dataframe(
            df[['data', 'cliente', 'projeto', 'efetividade', 'nps_score', 'status', 'risco_atraso']],
            use_container_width=True
        )

        # Sync manual
        if st.button("🔄 Sincronizar com Google Sheets"):
            df_study = get_study_history()
            link = sync_to_google_sheets(df, df_study)
            if link.startswith("http"):
                st.success(f"✅ Sincronizado! [Abrir Planilha]({link})")
            else:
                st.warning(link)

# ═══════════════════════════════════════════════
# TAB 3 – CARREIRA SIMULATOR
# ═══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🎯 Carreira Simulator – Rota para Dürr Alemanha</div>', unsafe_allow_html=True)

    df_rdp = get_history()
    avg_eff = df_rdp['efetividade'].astype(float).mean() if not df_rdp.empty else 0

    if not df_rdp.empty and API_KEY:
        if st.button("🤖 Analisar Projeção de Promoção com IA"):
            with st.spinner("Analisando histórico..."):
                gen = RDPGenerator(API_KEY)
                analysis = gen.predict_promotion(df_rdp, avg_eff)
            st.markdown(f"""
            <div style="background:#0d2018;border:1px solid #22c55e;border-radius:10px;padding:20px">
            {analysis.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Registre RDPs para ativar a análise de projeção de carreira.")

    st.divider()

    # Metas de carreira
    st.markdown('<div class="section-header">🎯 Metas de Carreira</div>', unsafe_allow_html=True)
    with st.expander("➕ Adicionar Meta"):
        with st.form("meta_form"):
            meta_desc = st.text_input("Descrição da meta")
            meta_prazo = st.date_input("Prazo")
            meta_cat = st.selectbox("Categoria", ["Certificação", "Promoção", "Idioma", "Educação", "Rede", "Outro"])
            meta_prog = st.slider("Progresso atual (%)", 0, 100, 0)
            if st.form_submit_button("Salvar Meta"):
                save_career_goal(meta_desc, str(meta_prazo), meta_prog, meta_cat)
                st.success("Meta salva!")
                st.rerun()

    df_goals = get_career_goals()
    if not df_goals.empty:
        for _, row in df_goals.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(int(row['progresso']) / 100, text=f"**{row['meta']}** – {row['categoria']} | Prazo: {row['prazo']}")
            with col2:
                new_prog = st.number_input(f"% #{row['id']}", 0, 100, int(row['progresso']), key=f"goal_{row['id']}", label_visibility="collapsed")
                if new_prog != int(row['progresso']):
                    update_goal_progress(row['id'], new_prog)
                    st.rerun()

    # LinkedIn Networking
    st.divider()
    st.markdown('<div class="section-header">🔗 LinkedIn Networking Assistant</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        nome_ct = st.text_input("Nome do contato")
        cargo_ct = st.text_input("Cargo")
    with col2:
        empresa_ct = st.text_input("Empresa")
        objetivo_ct = st.selectbox("Objetivo", [
            "Conexão profissional", "Vaga de emprego",
            "Mentoria", "Parceria técnica", "Expatriação Alemanha"
        ])
    if st.button("✍️ Gerar Mensagem LinkedIn") and nome_ct and API_KEY:
        with st.spinner("Redigindo..."):
            gen = RDPGenerator(API_KEY)
            msg = gen.generate_linkedin_message(nome_ct, cargo_ct, empresa_ct, objetivo_ct)
        st.text_area("Mensagem gerada", msg, height=200)

# ═══════════════════════════════════════════════
# TAB 4 – FUVEST STUDY TWIN
# ═══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📚 FUVEST Study Twin – Poli-USP Engenharia Mecânica</div>', unsafe_allow_html=True)

    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🤖 Sessão de Estudo", "📅 Plano de Estudos", "📈 Histórico"])

    with sub_tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            topico = st.selectbox("Tópico", [
                "Cinemática", "Dinâmica", "Termodinâmica",
                "Eletricidade", "Óptica", "Ondas",
                "Funções", "Geometria", "Trigonometria",
                "Cálculo", "Química Orgânica", "Estequiometria",
                "Redação FUVEST", "Biologia", "História", "Geografia"
            ])
            with st.form("study_form"):
                questao = st.text_area("Questão ou dúvida", height=100)
                resposta = st.text_area("Sua resposta", height=80)
                if st.form_submit_button("🤖 Analisar com Study Twin") and API_KEY:
                    with st.spinner("Analisando..."):
                        gen = RDPGenerator(API_KEY)
                        feedback = gen.fuvest_study_session(topico, questao, resposta)
                    st.session_state['fuvest_feedback'] = feedback

        with col2:
            if 'fuvest_feedback' in st.session_state:
                st.markdown(f"""
                <div style="background:#0d2018;border:1px solid #22c55e;border-radius:10px;padding:20px;height:100%">
                {st.session_state['fuvest_feedback'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

        # Registro de sessão
        st.divider()
        st.markdown("**📝 Registrar Sessão de Estudo**")
        with st.form("log_study"):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                s_data = st.date_input("Data", datetime.date.today(), key="s_data")
                s_horas = st.number_input("Horas", 0.0, 12.0, 1.0, 0.5)
            with sc2:
                s_questoes = st.number_input("Questões", 0, 200, 0)
                s_acertos = st.number_input("Acertos", 0, 200, 0)
            with sc3:
                s_topicos = st.text_input("Tópicos estudados")
            if st.form_submit_button("💾 Salvar Sessão"):
                save_study(str(s_data), s_horas, s_questoes, s_acertos, s_topicos)
                st.success("Sessão registrada!")

    with sub_tab2:
        if API_KEY:
            col1, col2 = st.columns(2)
            with col1:
                horas_sem = st.slider("Horas disponíveis/semana", 3, 30, 12)
                pontos_fracos = st.multiselect("Pontos fracos", [
                    "Física Moderna", "Cálculo", "Química Orgânica",
                    "Geometria Espacial", "Redação", "Biologia", "Trigonometria"
                ])
            with col2:
                data_fuvest = st.date_input("Data estimada FUVEST", datetime.date(2027, 11, 1))

            if st.button("📅 Gerar Plano Personalizado"):
                with st.spinner("Criando plano..."):
                    gen = RDPGenerator(API_KEY)
                    plano = gen.generate_study_plan(horas_sem, pontos_fracos, str(data_fuvest))
                st.markdown(f"""
                <div style="background:#0d2018;border:1px solid #22c55e;border-radius:10px;padding:20px">
                {plano.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

    with sub_tab3:
        df_study = get_study_history()
        if df_study.empty:
            st.info("Nenhuma sessão registrada ainda.")
        else:
            df_study['data'] = pd.to_datetime(df_study['data'])
            df_study['horas_estudo'] = pd.to_numeric(df_study['horas_estudo'], errors='coerce')
            df_study['questoes_resolvidas'] = pd.to_numeric(df_study['questoes_resolvidas'], errors='coerce')
            df_study['acertos'] = pd.to_numeric(df_study['acertos'], errors='coerce')

            col1, col2 = st.columns(2)
            with col1:
                fig_h = px.bar(df_study, x='data', y='horas_estudo', title='Horas de Estudo',
                               template='plotly_dark', color_discrete_sequence=['#22c55e'])
                fig_h.update_layout(paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018')
                st.plotly_chart(fig_h, use_container_width=True)
            with col2:
                df_study['taxa_acerto'] = (df_study['acertos'] / df_study['questoes_resolvidas'].replace(0, 1) * 100).round(1)
                fig_q = px.line(df_study, x='data', y='taxa_acerto', title='Taxa de Acerto (%)',
                                template='plotly_dark', color_discrete_sequence=['#86efac'])
                fig_q.update_layout(paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018')
                st.plotly_chart(fig_q, use_container_width=True)

            total_h = df_study['horas_estudo'].sum()
            total_q = df_study['questoes_resolvidas'].sum()
            st.metric("Total de Horas", f"{total_h:.1f}h")
            st.metric("Total de Questões", int(total_q))
            st.dataframe(df_study[['data', 'horas_estudo', 'questoes_resolvidas', 'acertos', 'topicos']], use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 5 – ALEMÃO TÉCNICO
# ═══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">🇩🇪 Alemão Técnico – Dürr Vocabulary</div>', unsafe_allow_html=True)

    sub_a, sub_b = st.tabs(["📖 Gerar Flashcards do RDP", "🗃️ Minha Coleção"])

    with sub_a:
        df_rdp = get_history()
        if df_rdp.empty:
            st.info("Gere um RDP para extrair vocabulário técnico.")
        else:
            ultimo_rdp = df_rdp.iloc[0].to_dict()
            st.write(f"**Último RDP:** {ultimo_rdp.get('projeto', '')} – {ultimo_rdp.get('cliente', '')}")
            if st.button("🤖 Extrair 5 Termos Técnicos com Gemini") and API_KEY:
                with st.spinner("Extraindo vocabulário..."):
                    gen = RDPGenerator(API_KEY)
                    cards = gen.generate_alemao_flashcards(str(ultimo_rdp))

                if isinstance(cards, list):
                    for card in cards:
                        st.markdown(f"""
                        <div class="flashcard-box">
                            <b style="color:#22c55e;font-size:1.1rem">{card.get('termo_de', '')}  
                            <span style="color:#6b9e7c;font-size:0.85rem">{card.get('pronuncia', '')}</span></b><br>
                            🇧🇷 {card.get('termo_pt', '')}<br>
                            <i style="color:#9ca3af">{card.get('frase_corporativa', '')}</i><br>
                            <span style="background:#1a4a2a;padding:2px 8px;border-radius:10px;font-size:0.75rem">{card.get('nivel', 'B1')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"💾 Salvar '{card.get('termo_de', '')}'", key=f"save_card_{card.get('termo_de', '')}"):
                            save_flashcard(
                                card.get('termo_pt', ''), card.get('termo_de', ''),
                                card.get('pronuncia', ''), card.get('frase_corporativa', ''),
                                card.get('nivel', 'B1')
                            )
                            st.success("Salvo!")
                else:
                    st.write(cards)

    with sub_b:
        df_cards = get_flashcards()
        if df_cards.empty:
            st.info("Nenhum flashcard salvo ainda.")
        else:
            st.metric("Total de Flashcards", len(df_cards))
            nivel_filter = st.multiselect("Filtrar por nível", ["B1", "B2", "C1"], default=["B1", "B2", "C1"])
            df_filtered = df_cards[df_cards['nivel'].isin(nivel_filter)]

            cols = st.columns(2)
            for i, (_, row) in enumerate(df_filtered.iterrows()):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="flashcard-box">
                        <b style="color:#22c55e">{row['termo_de']}</b>  
                        <span style="color:#6b9e7c;font-size:0.8rem">{row['pronuncia']}</span><br>
                        🇧🇷 {row['termo_pt']}<br>
                        <i style="color:#9ca3af;font-size:0.85rem">{row['frase_corporativa']}</i>
                    </div>
                    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 6 – GLOBAL MOBILITY
# ═══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">🌍 Global Mobility – Simulador Alemanha</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        salario_brl = st.number_input("Salário atual (R$)", 1000, 50000, 8000, 500)
        salario_eur = st.number_input("Oferta na Alemanha (€/mês)", 500, 15000, 4500, 100)
    with col2:
        cidade_destino = st.selectbox("Cidade destino", [
            "Bietigheim-Bissingen", "Stuttgart", "Munich",
            "Hamburg", "Berlin", "Frankfurt"
        ])
        st.metric("Câmbio estimado", "1 EUR ≈ R$ 5,50")
        st.metric("Equivalente em R$", f"R$ {salario_eur * 5.5:,.0f}")

    if st.button("🤖 Análise Completa com IA") and API_KEY:
        with st.spinner("Analisando viabilidade da mudança..."):
            gen = RDPGenerator(API_KEY)
            analysis = gen.analyze_germany_move(salario_brl, salario_eur, cidade_destino)

        st.markdown(f"""
        <div style="background:#0d2018;border:1px solid #22c55e;border-radius:12px;padding:24px">
        {analysis.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # Comparativo visual
    st.divider()
    st.markdown('<div class="section-header">📊 Comparativo de Custo de Vida</div>', unsafe_allow_html=True)

    comparativo = {
        "Categoria": ["Aluguel 1-bed", "Alimentação/mês", "Transporte", "Seguro Saúde", "Internet"],
        "São Paulo (R$)": [3500, 1200, 250, 600, 120],
        f"{cidade_destino} (€)": [900, 400, 90, 0, 40],
        f"{cidade_destino} (R$≈)": [4950, 2200, 495, 0, 220]
    }
    df_comp = pd.DataFrame(comparativo)
    st.dataframe(df_comp, use_container_width=True)

    fig_comp = go.Figure(data=[
        go.Bar(name='São Paulo (R$)', x=df_comp['Categoria'], y=df_comp['São Paulo (R$)'],
               marker_color='#16a34a'),
        go.Bar(name=f'{cidade_destino} (R$≈)', x=df_comp['Categoria'], y=df_comp[f'{cidade_destino} (R$≈)'],
               marker_color='#4f46e5'),
    ])
    fig_comp.update_layout(
        barmode='group', template='plotly_dark',
        paper_bgcolor='#0a1a0f', plot_bgcolor='#0d2018',
        font=dict(color='#86efac'), title=f"SP vs {cidade_destino} – Custo de Vida"
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Checklist de documentos
    st.divider()
    st.markdown('<div class="section-header">📋 Checklist – Documentos para Alemanha</div>', unsafe_allow_html=True)
    docs = {
        "Passaporte válido (10 anos)": True,
        "Visto de trabalho (Arbeitsvisum)": False,
        "Registro na Prefeitura (Anmeldung)": False,
        "Número de Identificação Fiscal (Steuer-ID)": False,
        "Conta bancária alemã": False,
        "Seguro saúde (Krankenversicherung)": False,
        "Reconhecimento de diploma (Anerkennungsstelle)": False,
        "Contrato de trabalho assinado": False,
        "Comprovante de moradia": False,
        "Tradução juramentada de documentos BR": False,
    }
    cols_doc = st.columns(2)
    for i, (doc, status) in enumerate(docs.items()):
        with cols_doc[i % 2]:
            checked = st.checkbox(doc, value=status, key=f"doc_{i}")

    progresso_docs = sum(1 for v in docs.values() if v) / len(docs) * 100
    st.progress(int(progresso_docs) / 100, text=f"Documentação: {progresso_docs:.0f}% completa")
