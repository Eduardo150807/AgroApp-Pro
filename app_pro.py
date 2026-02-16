import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind Pro", page_icon="🚜", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM (VISUAL LIMPO) ---
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
        white-space: pre-wrap;
        background-color: #161b22;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #fff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
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

# --- FUNÇÕES ---
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
    if "GOOGLE_API_KEY" not in st.secrets: return None, "Erro: Configure API KEY"
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        lista = genai.list_models()
        for m in lista:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), None
        return genai.GenerativeModel('gemini-pro'), None
    except: return genai.GenerativeModel('gemini-pro'), None

def gerar_resposta_inteligente(prompt, historico, midia=None):
    model, erro = conectar_ia_segura()
    if erro: return erro
    prompt_sistema = f"""
    Você é o AgroMind. 
    Diretrizes: Responda curto e técnico.
    Histórico: {historico}
    Input: {prompt}
    """
    try:
        if midia: return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e: return f"⚠️ Erro IA: {str(e)}"

# --- LOGIN ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
CREDENCIAIS = {"Eduardo Dev": "Eduardo2007", "felpz": "f2025"}

if not st.session_state['logado']:
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind Pro</h1>", unsafe_allow_html=True)
    c_login = st.container()
    with c_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if usuario in CREDENCIAIS and CREDENCIAIS[usuario] == senha:
                st.session_state['logado'] = True
                st.rerun()
            else: st.error("Acesso Negado")
    st.stop()

# --- APP PRINCIPAL (ABAS) ---
st.title("🚜 AgroMind")

# AS 3 ABAS SAGRADAS
aba1, aba2, aba3 = st.tabs(["💬 Chat IA", "📈 Mercado", "🧰 Ferramentas"])

# --- ABA 1: CHAT ---
with aba1:
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
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
    
    prompt = st.chat_input("Digite sua pergunta...")
    if prompt or arquivo:
        txt = prompt if prompt else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": txt})
        midia_proc = arquivo
        if arquivo and hasattr(arquivo, 'type'):
            if "pdf" in arquivo.type: txt += f"\nPDF: {ler_pdf(arquivo)}"; midia_proc = None
            elif "image" in arquivo.type: midia_proc = Image.open(arquivo)
            elif "audio" in arquivo.type:
                midia_proc = {"mime_type": arquivo.type, "data": arquivo.getvalue()}
                txt = "Áudio recebido. Responda."
        res = gerar_resposta_inteligente(txt, str(st.session_state["messages"][-5:]), midia_proc)
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

# --- ABA 2: MERCADO ---
with aba2:
    st.markdown("### 💹 Cotações do Dia")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div></div>""", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📰 Notícias")
    news = carregar_noticias()
    if news:
        for n in news:
            st.markdown(f"""<div style="background:#161b22; padding:10px; margin-bottom:5px; border-radius:5px;"><a href="{n['link']}" target="_blank" style="text-decoration:none; color:#58a6ff; font-weight:bold;">{n['titulo']}</a></div>""", unsafe_allow_html=True)

# --- ABA 3: FERRAMENTAS (Organizadas) ---
with aba3:
    st.markdown("### 🚜 Caixa de Ferramentas")
    
    # 1. PLANTIO (Dentro de um Expander para ficar limpo)
    with st.expander("🌱 Plantio & Sementes", expanded=True):
        c1, c2 = st.columns(2)
        with c1: 
            pop = st.number_input("População (mil/ha):", value=300)
            germ = st.number_input("Germinação (%):", value=90)
        with c2: 
            pms = st.number_input("PMS (g):", value=180.0)
            margem = st.slider("Margem Seg. (%)", 0, 20, 10)
        
        if st.button("Calcular Sementes"):
            pop_real = (pop * 1000) / (germ / 100) * (1 + margem/100)
            kg_ha = (pop_real * pms) / 1000000
            st.markdown(f"<div class='result-box'>📦 Comprar: {kg_ha:.2f} kg/ha<br>🌱 Total: {int(pop_real):,} sementes/ha</div>", unsafe_allow_html=True)

    # 2. ADUBAÇÃO
    with st.expander("🌾 Adubação & Calagem"):
        c1, c2 = st.columns(2)
        with c1:
            ctc = st.number_input("CTC (cmolc):", value=10.0)
            v1 = st.number_input("V% Atual:", value=40.0)
        with c2:
            v2 = st.number_input("V% Meta:", value=70.0)
            prnt = st.number_input("PRNT (%):", value=80.0)
        
        if st.button("Calcular Calagem"):
            nc = (ctc * (v2 - v1)) / prnt
            st.markdown(f"<div class='result-box'>🚜 Aplicar: {nc:.2f} toneladas/ha</div>", unsafe_allow_html=True)

    # 3. PULVERIZAÇÃO
    with st.expander("🧪 Pulverização (Tanque)"):
        c1, c2 = st.columns(2)
        with c1:
            tanque = st.number_input("Tanque (L):", value=2000)
            vazao = st.number_input("Vazão (L/ha):", value=150)
        with c2: dose = st.number_input("Dose (L ou Kg / ha):", value=0.5)
        
        if st.button("Calcular Calda"):
            area = tanque / vazao
            total = area * dose
            st.markdown(f"<div class='result-box'>🚜 Cobre: {area:.1f} ha<br>🧪 Pôr no Tanque: {total:.2f} L (ou Kg)</div>", unsafe_allow_html=True)

    # 4. CONVERSÕES
    with st.expander("📊 Conversor de Medidas"):
        c1, c2 = st.columns(2)
        with c1: val = st.number_input("Valor:", value=1.0)
        with c2: tipo = st.selectbox("Converter:", ["Alqueire SP -> ha", "Alqueire GO -> ha", "Alqueire BA -> ha", "Saca -> Ton"])
        
        res = 0
        if "SP" in tipo: res = val * 2.42
        elif "GO" in tipo: res = val * 4.84
        elif "BA" in tipo: res = val * 9.68
        elif "Saca" in tipo: res = (val * 60) / 1000
        st.metric("Resultado", f"{res:.2f}")
