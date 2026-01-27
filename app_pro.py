import streamlit as st
import google.generativeai as genai
import os
import tempfile
from PIL import Image
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import PyPDF2

# ==========================================
# ⚙️ CONFIGURAÇÃO INICIAL (FORÇANDO ÍCONE)
# ==========================================
st.set_page_config(
    page_title="AgroMind", 
    page_icon="🧠", # Esse ícone aparece na aba
    layout="wide",
    initial_sidebar_state="collapsed" # Esconde a barra lateral ao abrir
)

# ==========================================
# 🎨 CSS PREMIUM (MODO APP NATIVO DARK)
# ==========================================
st.markdown("""
    <style>
    /* 1. ESCONDER TUDO QUE É DO STREAMLIT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* Esconde a barra colorida superior */
    [data-testid="stToolbar"] {visibility: hidden;} /* Esconde opções do canto direito */
    [data-testid="stSidebarNav"] {display: none;} /* Esconde navegação padrão */
    
    /* 2. FORÇAR FUNDO ESCURO (DARK MODE ABSOLUTO) */
    .stApp {
        background-color: #0E1117;
    }
    
    /* 3. CAMPOS DE TEXTO E BOTÕES ESTILO 'ZAP' */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { 
        background-color: #1F2937 !important; 
        color: #F3F4F6 !important; 
        border-radius: 12px; 
        border: 1px solid #374151;
    }
    
    /* 4. ABAS (TABS) MODERNAS E DISCRETAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 10px 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #111827;
        border-radius: 12px;
        color: #9CA3AF;
        padding: 0 16px;
        border: 1px solid #374151;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #059669; /* Verde Agro */
        color: white;
        border: none;
    }

    /* 5. CARDS DE MERCADO (ESTILO BLOOMBERG DARK) */
    .market-card { 
        background-color: #111827; 
        border: 1px solid #374151; 
        border-radius: 12px; 
        padding: 15px; 
        text-align: center; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); 
    }
    .market-symbol { color: #9CA3AF; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;}
    .market-price { color: #F9FAFB; font-size: 1.5em; font-weight: 700; }
    .market-change-up { color: #34D399; font-weight: bold; font-size: 0.85em; }
    .market-change-down { color: #F87171; font-weight: bold; font-size: 0.85em; }

    /* 6. BALÕES DE CHAT (WHATSAPP DARK) */
    .chat-user { 
        text-align: right; 
        background-color: #005c4b; 
        color: #E9EDEF; 
        padding: 10px 15px; 
        border-radius: 12px 0 12px 12px; 
        display: inline-block; 
        margin: 5px 0 5px auto; 
        max-width: 85%; 
        font-size: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    .chat-ai { 
        text-align: left; 
        background-color: #202c33; 
        color: #E9EDEF; 
        padding: 10px 15px; 
        border-radius: 0 12px 12px 12px; 
        display: inline-block; 
        margin: 5px auto 5px 0; 
        max-width: 85%; 
        border: 1px solid #37474F; 
        font-size: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    .chat-container { display: flex; flex-direction: column; margin-bottom: 60px;} /* Espaço extra pro input */
    
    /* 7. LIMPEZA DE INTERFACE EXTRA */
    [data-testid="stFileUploader"] label {display: none;}
    [data-testid="stCameraInput"] label {display: none;}
    [data-testid="stHeader"] {display: none;} /* Tchau header do Streamlit */
    
    /* Botão de Clips (Popover) */
    [data-testid="stPopover"] button {
        border-radius: 50%;
        width: 45px;
        height: 45px;
        background-color: #202c33;
        border: none;
        color: #8696a0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNÇÕES DE BACKEND
# ==========================================
def descobrir_modelo_disponivel(key):
    genai.configure(api_key=key)
    try:
        modelos = list(genai.list_models())
        for m in modelos:
            if 'flash' in m.name: return m.name
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
            for item in root.findall('./channel/item')[:5]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

# ==========================================
# 🔐 LOGIN & SETUP
# ==========================================
if "messages" not in st.session_state: st.session_state["messages"] = []
if "uploader_key" not in st.session_state: st.session_state["uploader_key"] = 0

if 'logado' not in st.session_state: st.session_state['logado'] = False
CREDENCIAIS = {"Eduardo Dev": "Eduardo2007", "felpz": "f2025"} # Mantenha suas senhas aqui

def login():
    u = st.session_state.get('w_u', '')
    s = st.session_state.get('w_p', '')
    if u in CREDENCIAIS and CREDENCIAIS[u] == s: st.session_state['logado'] = True
    else: st.error("Acesso Negado.")

if not st.session_state['logado']:
    st.markdown("<h1 style='text-align: center;'>🔐 AgroMind</h1>", unsafe_allow_html=True)
    c_log1, c_log2, c_log3 = st.columns([1,2,1])
    with c_log2:
        st.text_input("Usuário", key="w_u")
        st.text_input("Senha", type="password", key="w_p")
        st.button("Entrar no Sistema", on_click=login, use_container_width=True)
    st.stop()

# --- SIDEBAR OCULTA (SÓ ABRE SE CLICAR) ---
with st.sidebar:
    st.title("🧠 Config")
    if st.button("🗑️ Nova Conversa", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["uploader_key"] += 1 
        st.rerun()
    if st.button("Sair", use_container_width=True): st.session_state['logado'] = False; st.rerun()
    st.divider()
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("Chave Google API:", type="password")

# ==========================================
# 📱 INTERFACE PRINCIPAL
# ==========================================
# Cabeçalho Minimalista
c_head1, c_head2 = st.columns([1, 5])
with c_head1: st.markdown("## 🧠")
with c_head2: st.markdown("## AgroMind AI")

aba_chat, aba_mercado = st.tabs(["💬 Chat", "📈 Mercado"])

# --- ABA 1: CHAT PRO ---
with aba_chat:
    
    # Histórico de Mensagens
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "chat-user" if msg["role"] == "user" else "chat-ai"
        icon = ""
        st.markdown(f"<div class='{role}'>{icon} {msg['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # BARRA DE FERRAMENTAS
    col_clip, col_mic, col_space = st.columns([1, 1, 6])
    
    midia_enviada = None
    tipo_midia = None

    with col_clip:
        # MENU TIPO ZAP (CLIPS)
        with st.popover("📎", help="Anexar"):
            st.caption("Selecione:")
            tab_foto, tab_cam, tab_doc = st.tabs(["🖼️", "📸", "📄"])
            with tab_foto:
                upl_img = st.file_uploader("Galeria", type=["jpg","png"], key=f"img_{st.session_state['uploader_key']}")
                if upl_img: midia_enviada = upl_img; tipo_midia = 'imagem'
            with tab_cam:
                cam_img = st.camera_input("Câmera")
                if cam_img: midia_enviada = cam_img; tipo_midia = 'imagem'
            with tab_doc:
                upl_doc = st.file_uploader("PDF", type=["pdf"], key=f"doc_{st.session_state['uploader_key']}")
                if upl_doc: midia_enviada = upl_doc; tipo_midia = 'pdf'

    with col_mic:
        audio_rec = st.audio_input("🎙️")
        if audio_rec: midia_enviada = audio_rec; tipo_midia = 'audio'

    if midia_enviada:
        st.toast(f"📎 {tipo_midia.upper()} Pronto! Digite e envie.", icon="✅")

    # INPUT TEXTO
    prompt = st.chat_input("Mensagem...")

    # LÓGICA DE ENVIO
    if prompt or (midia_enviada and tipo_midia == 'audio'):
        if not api_key: st.error("Falta API Key"); st.stop()
        
        texto_usuario = prompt if prompt else "Analise este áudio/arquivo."
        st.session_state["messages"].append({"role": "user", "content": texto_usuario})
        
        nome_modelo = descobrir_modelo_disponivel(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(nome_modelo)
        resposta = ""

        with st.spinner("AgroMind pensando..."):
            try:
                # 1. IMAGEM
                if tipo_midia == 'imagem':
                    img = Image.open(midia_enviada)
                    prompt_final = f"Atue como Agrônomo Sênior. Usuário: '{texto_usuario}'. Identifique o problema na imagem e dê a solução técnica."
                    resposta = model.generate_content([prompt_final, img]).text
                
                # 2. PDF
                elif tipo_midia == 'pdf':
                    texto_extraido = ler_pdf(midia_enviada)
                    prompt_final = f"Resuma e analise. Contexto: '{texto_usuario}'. Texto: {texto_extraido[:30000]}"
                    resposta = model.generate_content(prompt_final).text

                # 3. ÁUDIO
                elif tipo_midia == 'audio':
                    prompt_final = "Ouça o produtor e responda como Agrônomo Especialista."
                    resposta = model.generate_content([prompt_final, {"mime_type": "audio/mp3", "data": midia_enviada.read()}]).text

                # 4. TEXTO PURO (LÓGICA CAMALEÃO)
                else:
                    historico = ""
                    for m in st.session_state["messages"]:
                        h_role = "Produtor" if m["role"] == "user" else "AgroMind"
                        historico += f"{h_role}: {m['content']}\n"

                    prompt_sistema = f"""
                    Você é o AgroMind, Inteligência Agronômica.
                    
                    REGRA DE PERSONALIDADE:
                    1. Pergunta técnica curta (ex: "fórmula calagem") -> Resposta DIRETA e MATEMÁTICA.
                    2. Conversa ou dúvida complexa -> Resposta CONSULTIVA, PARCEIRA e DIDÁTICA.
                    
                    HISTÓRICO:
                    {historico}
                    
                    PERGUNTA ATUAL: {texto_usuario}
                    """
                    resposta = model.generate_content(prompt_sistema).text

                st.session_state["messages"].append({"role": "assistant", "content": resposta})
                if midia_enviada: st.session_state["uploader_key"] += 1
                st.rerun()

            except Exception as e:
                st.error(f"Erro: {e}")

# --- ABA 2: MERCADO ---
with aba_mercado:
    st.caption("Cotações Atualizadas")
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA (SC)</div><div class="market-price">R$ 128,50</div><div class="market-change-down">▼ -1.2%</div></div>""", unsafe_allow_html=True)
    with col2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO (SC)</div><div class="market-price">R$ 58,90</div><div class="market-change-up">▲ +0.5%</div></div>""", unsafe_allow_html=True)
    with col3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI (@)</div><div class="market-price">R$ 235,00</div><div class="market-change-down">▼ -0.8%</div></div>""", unsafe_allow_html=True)
    with col4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div><div class="market-change-up">▲ +0.1%</div></div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Atualizar Feed", use_container_width=True): st.rerun()
    
    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"**[{n['titulo']}]({n['link']})**")
            st.caption(f"📅 {n['data']}")
            st.markdown("---")
