import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS AGRESSIVO (ESCONDE STREAMLIT E FORÇA DARK) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stApp { background-color: #0E1117; }

    /* Estilo de Chat Minimalista */
    .chat-user { background-color: #005c4b; color: white; padding: 10px; border-radius: 10px; margin: 5px 0 5px auto; max-width: 80%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 10px; border-radius: 10px; margin: 5px auto 5px 0; max-width: 80%; border: 1px solid #333; }
    
    /* Botões flutuantes de ferramentas */
    .stPopover button { border-radius: 50% !important; width: 50px !important; height: 50px !important; background-color: #262730 !important; border: none !important; }

    /* MERCADO */
    .market-card { background-color: #121212; border: 1px solid #333; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #888; font-size: 0.8em; text-transform: uppercase; }
    .market-price { color: #fff; font-size: 1.5em; font-weight: 700; }
    .market-change-up { color: #00E676; font-size: 0.9em; }
    .market-change-down { color: #FF5252; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES EXTRAS (Mercado e PDF) ---
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

# --- LÓGICA DE PERSONALIDADE (CAMALEÃO) ---
def gerar_resposta_inteligente(prompt, historico, midia=None):
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        return "Erro: Falta a API Key no Secrets."
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt_sistema = f"""
    Você é o AgroMind. 
    REGRA DE OURO: 
    1. Se o usuário mandar uma mensagem curta/seca (ex: "Fórmula calagem"), responda APENAS o dado técnico.
    2. Se o usuário conversar, seja amigável e use um tom de consultor do campo.
    
    Histórico: {historico}
    Pergunta: {prompt}
    """
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except:
        return "Erro de conexão com a IA. Tente novamente."

# --- LOGIN (RESTAURADO COM USUÁRIO) ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False

# Credenciais (Edite aqui)
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
                st.error("Usuário ou Senha incorretos")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("🧠 AgroMind Chat")

aba1, aba2 = st.tabs(["💬 Conversa", "📊 Mercado"])

with aba1:
    # Exibir chat
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    # BARRA DE FERRAMENTAS
    col1, col2, col3 = st.columns([1, 1, 6])
    arquivo = None
    
    with col1:
        with st.popover("📎"):
            tipo = st.radio("O que enviar?", ["Foto", "Câmera", "Documento"])
            if tipo == "Foto": arquivo = st.file_uploader("Imagem", type=["jpg", "png"])
            elif tipo == "Câmera": arquivo = st.camera_input("Tirar Foto")
            else: arquivo = st.file_uploader("Anexo", type=["pdf"])

    with col2:
        audio = st.audio_input("🎙️")
        if audio: arquivo = audio

    prompt_usuario = st.chat_input("Digite sua pergunta...")

    if prompt_usuario or arquivo:
        texto = prompt_usuario if prompt_usuario else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": texto})
        
        # Converte histórico para string simples (evita erro de memória)
        hist_str = str(st.session_state["messages"][-5:])
        
        # Se for PDF, lê o texto antes
        midia_processada = arquivo
        if arquivo and hasattr(arquivo, 'type') and arquivo.type == "application/pdf":
            texto += f"\n\nCONTEÚDO DO PDF:\n{ler_pdf(arquivo)}"
            midia_processada = None # Já virou texto

        # Se for imagem, abre com PIL
        if arquivo and hasattr(arquivo, 'type') and "image" in arquivo.type:
             midia_processada = Image.open(arquivo)

        res = gerar_resposta_inteligente(texto, hist_str, midia_processada)
        
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

with aba2:
    st.markdown("### 💹 Cotações do Dia")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div><div class="market-change-down">▼ -1.2%</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div><div class="market-change-up">▲ +0.5%</div></div>""", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div><div class="market-change-down">▼ -0.8%</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div><div class="market-change-up">▲ +0.1%</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Últimas Notícias (Google News)")
    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"[{n['titulo']}]({n['link']})")
