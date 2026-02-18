import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import time

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind Pro", page_icon="🚜", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM (VISUAL LIMPO E MODERNO) ---
st.markdown("""
    <style>
    /* Esconde menu padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    .stApp { background-color: #0E1117; }

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161b22;
        border-radius: 4px 4px 0px 0px;
        color: #fff;
        border: 1px solid #30363d;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
        border-color: #2ea043;
    }

    /* Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Mercado */
    .market-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #8b949e; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px; }
    .market-price { color: #f0f6fc; font-size: 1.4em; font-weight: 800; margin: 5px 0; }
    
    /* Resultados Calculadoras */
    .result-box {
        background-color: #0d4429;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00a86b;
        margin-top: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def ler_pdf(arquivo):
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"
        return texto
    except: return "Erro ao ler PDF."

def carregar_noticias():
    try:
        url = "https://news.google.com/rss/search?q=agronegocio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        with urlopen(url) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            noticias = []
            for item in root.findall('./channel/item')[:6]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

def conectar_ia_segura():
    if "
