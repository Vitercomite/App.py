import streamlit as st
import google.generativeai as genai

def init_gemini():
    try:
        # Puxa a chave diretamente dos Secrets do Streamlit
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return True
    except Exception:
        return False

def generate_report_text(dados):
    if not init_gemini():
        return f"Relatório Técnico (IA Offline - Falha na Chave):\n{dados}"
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Organize e crie um relatório técnico profissional com base nestes dados brutos:\n{dados}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro de comunicação com a IA: {e}\n\nDados brutos:\n{dados}"
