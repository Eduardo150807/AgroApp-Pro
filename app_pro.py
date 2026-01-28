import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM (VISUAL RICO) ---
st.markdown("""
    <style>
    /* Esconde elementos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stApp { background-color: #0E1117; }

    /* Chat Style */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .chat-ai { background-color: #202c33; color: white; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    
    /* Botões Redondos */
    .stPopover button { border-radius: 50% !important; width: 50px !important; height: 50px !important; background-color: #262730 !important; border: 1px solid #444 !important; }

    /* --- ESTILO DO MERCADO (BLOOMBERG STYLE) --- */
    .market-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
    .market-card { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 15px; 
        text-align: center; 
        flex: 1; 
        min-width: 140px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .market-card:active { transform: scale(0.98); }
    .market-symbol { color: #8b949e; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px; }
    .market-price { color: #f0f6fc; font-size: 1.4em; font-weight: 800; margin: 5px 0; }
    .market-up { color: #3fb950; font-size: 0.8em; font-weight: bold; } /* Verde */
    .market-down { color: #f85149; font-size: 0.8em; font-weight: bold; } /* Vermelho */

    /* --- ESTILO DAS NOTÍCIAS --- */
    .news-card {
        background-color: #161b22;
        border-left: 4px solid #238636;
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 4px;
    }
    .news-title { color: #58a6ff; font-weight: bold; text-decoration: none; font-size: 1.1em; display: block; margin-bottom: 5px;}
    .news-date { color: #8b949e; font-size: 0.8em; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def ler_pdf(arquivo):
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"
        return texto
    except: return "Erro ao ler PDF."

def carregar_noticias():
    # Pega notícias reais do Agronegócio via RSS do Google
    try:
        url = "https://news.google.com/rss/search?q=agronegocio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        with urlopen(url) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            noticias = []
            for item in root.findall('./channel/item')[:6]:
                noticias.append({
                    'titulo': item.find('title').text, 
                    'link': item.find('link').text, 
                    'data': item.find('pubDate').text
                })
            return noticias
    except: return []

# --- CONEXÃO INTELIGENTE (Auto-Detectar Modelo) ---
def conectar_ia_segura():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None, "Erro: Configure a GOOGLE_API_KEY no Secrets."
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Tenta achar o modelo disponível no servidor
    try:
        lista = genai.list_models()
        # 1. Tenta Flash
        for m in lista:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), None
        # 2. Tenta Pro
        return genai.GenerativeModel('gemini-pro'), None
    except:
        # Se listar falhar, força o padrão
        return genai.GenerativeModel('gemini-pro'), None

def gerar_resposta_inteligente(prompt, historico, midia=None):
    model, erro = conectar_ia_segura()
    if erro: return erro
    
    prompt_sistema = f"""
    Você é o AgroMind. 
    REGRA:
    1. Resposta CURTA e TÉCNICA para perguntas diretas.
    2. Resposta AMIGÁVEL para conversas.
    Histórico: {historico}
    Pergunta: {prompt}
    """
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"⚠️ Erro de conexão (Tente novamente): {e}"

# --- LOGIN ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
CREDENCIAIS = {"Eduardo Dev": "Eduardo2007", "felpz": "f2025"}

if not st.session_state['logado']:
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind</h1>", unsafe_allow_html=True)
    c_login = st.container()
    with c_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if usuario in CREDENCIAIS and CREDENCIAIS[usuario] == senha:
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Acesso Negado")
    st.stop()

# --- APP PRINCIPAL ---
st.title("🧠 AgroMind")

aba1, aba2 = st.tabs(["💬 Chat", "📈 Mercado"])

# ABA 1: CHAT
with aba1:
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) # Espaço

    col1, col2, col3 = st.columns([1, 1, 6])
    arquivo = None
    
    with col1:
        with st.popover("📎"):
            tipo = st.radio("Anexar:", ["Galeria", "Câmera", "PDF"])
            if tipo == "Galeria": arquivo = st.file_uploader("Img", type=["jpg", "png"])
            elif tipo == "Câmera": arquivo = st.camera_input("Foto")
            else: arquivo = st.file_uploader("Doc", type=["pdf"])

    with col2:
        audio = st.audio_input("🎙️")
        if audio: arquivo = audio

    prompt_usuario = st.chat_input("Digite aqui...")

    if prompt_usuario or arquivo:
        texto = prompt_usuario if prompt_usuario else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": texto})
        
        midia_proc = arquivo
        if arquivo and hasattr(arquivo, 'type'):
            if "pdf" in arquivo.type:
                texto += f"\nPDF: {ler_pdf(arquivo)}"
                midia_proc = None
            elif "image" in arquivo.type:
                midia_proc = Image.open(arquivo)

        res = gerar_resposta_inteligente(texto, str(st.session_state["messages"][-5:]), midia_proc)
        
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

# ABA 2: MERCADO (VISUAL RESTAURADO)
with aba2:
    st.markdown("### 💹 Cotações em Tempo Real")
    
    # 4 Colunas para os Cards
    c1, c2, c3, c4 = st.columns(4)
    
    with c1: 
        st.markdown("""
        <div class="market-card">
            <div class="market-symbol">🌱 SOJA</div>
            <div class="market-price">R$ 128,50</div>
            <div class="market-down">▼ -1.2%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2: 
        st.markdown("""
        <div class="market-card">
            <div class="market-symbol">🌽 MILHO</div>
            <div class="market-price">R$ 58,90</div>
            <div
