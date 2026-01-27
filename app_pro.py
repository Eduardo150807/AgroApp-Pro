import streamlit as st
import google.generativeai as genai
import os
import tempfile
from PIL import Image
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import PyPDF2

# --- Configuração Visual ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide")

# --- CSS PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background-color: transparent;}
    .stTextInput input, .stTextArea textarea { background-color: #1E1E1E !important; color: white !important; border-radius: 10px; }
    
    /* MERCADO */
    .market-card { background-color: #121212; border: 1px solid #333; border-radius: 12px; padding: 15px; text-align: center; transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .market-card:hover { border-color: #4CAF50; transform: translateY(-2px); }
    .market-symbol { color: #888; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; }
    .market-price { color: #fff; font-size: 1.8em; font-weight: 700; margin: 5px 0; }
    .market-change-up { color: #00E676; font-weight: bold; font-size: 0.9em; }
    .market-change-down { color: #FF5252; font-weight: bold; font-size: 0.9em; }

    /* CHAT */
    .chat-user { text-align: right; background-color: #0D47A1; color: white; padding: 12px 18px; border-radius: 18px 18px 0 18px; display: inline-block; margin: 5px 0 5px auto; max-width: 80%; }
    .chat-ai { text-align: left; background-color: #263238; color: #ECEFF1; padding: 12px 18px; border-radius: 18px 18px 18px 0; display: inline-block; margin: 5px auto 5px 0; max-width: 80%; border: 1px solid #37474F; }
    .chat-container { display: flex; flex-direction: column; margin-bottom: 20px;}
    
    /* ABAS DE UPLOAD */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1E1E1E; border-radius: 4px; color: #fff; }
    .stTabs [aria-selected="true"] { background-color: #2E7D32; color: white; }
    
    /* NOTÍCIAS */
    .news-item { background-color: #1E1E1E; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #4CAF50; }
    .news-link { color: #E0E0E0; text-decoration: none; font-weight: 600; font-size: 1.05em; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNÇÕES
# ==========================================
def descobrir_modelo_disponivel(key):
    genai.configure(api_key=key)
    try:
        modelos = list(genai.list_models())
        for m in modelos:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods: return m.name
        for m in modelos:
            if 'pro' in m.name and 'generateContent' in m.supported_generation_methods: return m.name
        return modelos[0].name
    except: return "gemini-1.5-flash"

def ler_pdf(arquivo):
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"
        return texto
    except: return "Erro ao ler PDF."

def carregar_noticias():
    url = "https://news.google.com/rss/search?q=agronegocio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        with urlopen(url) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            noticias = []
            for item in root.findall('./channel/item')[:6]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

# ==========================================
# 🔄 INICIALIZAÇÃO E LOGIN
# ==========================================
if "messages" not in st.session_state: st.session_state["messages"] = []
if "uploader_key" not in st.session_state: st.session_state["uploader_key"] = 0

if 'logado' not in st.session_state: st.session_state['logado'] = False
CREDENCIAIS = {"Eduardo Dev": "Eduardo2007", "felpz": "f2025"}

def login():
    u = st.session_state.get('w_u', '')
    s = st.session_state.get('w_p', '')
    if u in CREDENCIAIS and CREDENCIAIS[u] == s: st.session_state['logado'] = True
    else: st.error("Erro.")

if not st.session_state['logado']:
    st.title("🔐 Login AgroMind")
    st.text_input("User", key="w_u"); st.text_input("Senha", type="password", key="w_p")
    st.button("Entrar", on_click=login); st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("🗑️ Nova Conversa"):
        st.session_state["messages"] = []
        st.session_state["uploader_key"] += 1 
        st.rerun()
    if st.button("Sair"): st.session_state['logado'] = False; st.rerun()
    st.divider()
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("Chave Google API:", type="password")

# ==========================================
# 📱 APP PRINCIPAL
# ==========================================
st.title("🧠 AgroMind") 
aba_assistente, aba_mercado = st.tabs(["💬 Chat & Diagnóstico", "📊 Mercado"])

# --- ABA 1: CHAT CAMALEÃO ---
with aba_assistente:
    
    # --- ÁREA DE UPLOAD INTELIGENTE (ARQUIVO OU CÂMERA) ---
    st.markdown("##### 📎 Anexar Arquivo ou Foto")
    tab_up, tab_cam = st.tabs(["📂 Upload de Arquivo", "📸 Usar Câmera"])
    
    arquivo = None
    
    with tab_up:
        arquivo_up = st.file_uploader("Selecione PDF ou Imagem", type=["jpg", "png", "jpeg", "pdf"], key=f"up_{st.session_state['uploader_key']}")
        if arquivo_up: arquivo = arquivo_up
        
    with tab_cam:
        foto_cam = st.camera_input("Tirar foto agora")
        if foto_cam: arquivo = foto_cam

    # --- HISTÓRICO ---
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "chat-user" if msg["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{role}'>{msg['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("Digite sua pergunta...")

    if prompt:
        if not api_key: st.error("Falta API Key"); st.stop()
        
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        nome_modelo = descobrir_modelo_disponivel(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(nome_modelo)
        resposta = ""

        with st.spinner("AgroMind pensando..."):
            try:
                # --- MODO 1: FOTO (DIAGNÓSTICO) ---
                if arquivo and arquivo.type in ["image/jpeg", "image/png"]:
                    img = Image.open(arquivo)
                    prompt_foto = f"""
                    Atue como Fitopatologista Sênior.
                    Pergunta do Usuário: '{prompt}'
                    Analise a imagem. Se for planta, identifique pragas/doenças e recomende manejo.
                    Seja direto e técnico.
                    """
                    resposta = model.generate_content([prompt_foto, img]).text

                # --- MODO 2: PDF (RESUMO) ---
                elif arquivo and arquivo.type == "application/pdf":
                    texto_pdf = ler_pdf(arquivo)
                    prompt_pdf = f"Usuário: '{prompt}'. Resuma o PDF: {texto_pdf[:30000]}"
                    resposta = model.generate_content(prompt_pdf).text

                # --- MODO 3: TEXTO (O CÉREBRO CAMALEÃO) ---
                else:
                    historico_conversa = ""
                    for m in st.session_state["messages"]:
                        quem = "Usuário" if m["role"] == "user" else "AgroMind"
                        historico_conversa += f"{quem}: {m['content']}\n"
                    
                    # --- PERSONALIDADE AGROMIND ---
                    prompt_sistema = f"""
                    Você é o 'AgroMind', um Assistente Agronômico Sênior de elite.
                    
                    DIRETRIZ DE COMPORTAMENTO (IMPORTANTE):
                    Analise a pergunta do usuário:
                    1. SE FOR UMA PERGUNTA DIRETA/CURTA (Ex: "Fórmula calagem", "Preço soja", "Dose glifosato"):
                       -> RESPONDA DE FORMA SECA, DIRETA E TÉCNICA.
                       -> NÃO use saudações, não use gírias, não enrole. Dê a fórmula ou o dado imediatamente.
                    
                    2. SE FOR UMA CONVERSA/EXPLICAÇÃO (Ex: "Como eu faço pra corrigir...", "O que você acha de...", "Me explica melhor"):
                       -> Use uma personalidade de consultor experiente, didático e parceiro (Estilo rústico educado).
                    
                    --- HISTÓRICO DA CONVERSA ---
                    {historico_conversa}
                    --- FIM HISTÓRICO ---
                    
                    PERGUNTA ATUAL: {prompt}
                    """
                    resposta = model.generate_content(prompt_sistema).text

                st.session_state["messages"].append({"role": "assistant", "content": resposta})
                st.rerun()

            except Exception as e:
                st.error(f"Erro: {e}")

# --- ABA 2: MERCADO ---
with aba_mercado:
    st.subheader("💹 Cotações")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div><div class="market-change-down">▼ -1.20%</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div><div class="market-change-up">▲ +0.50%</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div><div class="market-change-down">▼ -0.85%</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div><div class="market-change-up">▲ +0.10%</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Atualizar"): st.rerun()
    noticias = carregar_noticias()
    if noticias:
        c_n1, c_n2 = st.columns(2)
        for i, n in enumerate(noticias):
            with (c_n1 if i % 2 == 0 else c_n2):
                st.markdown(f"""<div class="news-item"><a href="{n['link']}" target="_blank" class="news-link">{n['titulo']}</a><div class="news-date">📅 {n['data']}</div></div>""", unsafe_allow_html=True)
