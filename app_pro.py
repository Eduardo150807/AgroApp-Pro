import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stApp { background-color: #0E1117; }

    /* Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Botões */
    .stPopover button { border-radius: 50% !important; width: 50px !important; height: 50px !important; background-color: #262730 !important; border: 1px solid #444 !important; }

    /* Mercado */
    .market-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #8b949e; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px; }
    .market-price { color: #f0f6fc; font-size: 1.4em; font-weight: 800; margin: 5px 0; }
    
    /* Notícias */
    .news-card { background-color: #161b22; border-left: 4px solid #238636; padding: 15px; margin-bottom: 12px; border-radius: 4px; text-decoration: none; }
    .news-title { color: #58a6ff; font-weight: bold; text-decoration: none; font-size: 1.1em; display: block; margin-bottom: 5px;}
    .news-date { color: #8b949e; font-size: 0.8em; }

    /* Ferramentas */
    .tool-card { background-color: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 20px; }
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
    if "GOOGLE_API_KEY" not in st.secrets:
        return None, "Erro: Configure a GOOGLE_API_KEY no Secrets."
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        lista = genai.list_models()
        # Procura especificamente o Flash porque ele entende áudio bem
        for m in lista:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), None
        return genai.GenerativeModel('gemini-pro'), None
    except:
        return genai.GenerativeModel('gemini-pro'), None

def gerar_resposta_inteligente(prompt, historico, midia=None):
    model, erro = conectar_ia_segura()
    if erro: return erro
    
    prompt_sistema = f"""
    Você é o AgroMind. 
    DIRETRIZES:
    1. Se receber ÁUDIO, transcreva mentalmente e responda a dúvida.
    2. Calagem: Use NC = (CTC x (V2 - V1)) / PRNT.
    3. Responda curto e técnico para contas.
    
    Histórico: {historico}
    Pergunta (ou Audio): {prompt}
    """
    try:
        if midia: 
            return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e: 
        return f"⚠️ Erro ao processar (Tente enviar texto): {str(e)}"

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
            else: st.error("Acesso Negado")
    st.stop()

# --- APP ---
st.title("🧠 AgroMind")

# ABAS
aba1, aba2, aba3 = st.tabs(["💬 Chat", "📈 Mercado", "🧰 Ferramentas"])

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
    
    prompt_usuario = st.chat_input("Digite aqui...")

    if prompt_usuario or arquivo:
        texto = prompt_usuario if prompt_usuario else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": texto})
        
        midia_proc = arquivo
        
        # --- CORREÇÃO DO ERRO DO ÁUDIO AQUI ---
        if arquivo and hasattr(arquivo, 'type'):
            if "pdf" in arquivo.type:
                texto += f"\nPDF: {ler_pdf(arquivo)}"
                midia_proc = None
            elif "image" in arquivo.type:
                midia_proc = Image.open(arquivo)
            elif "audio" in arquivo.type:
                # O Pulo do Gato: Transforma o áudio em dados brutos para a IA
                midia_proc = {
                    "mime_type": arquivo.type,
                    "data": arquivo.getvalue()
                }
                texto = "O usuário enviou um áudio. Ouça e responda."

        res = gerar_resposta_inteligente(texto, str(st.session_state["messages"][-5:]), midia_proc)
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

# --- ABA 2: MERCADO ---
with aba2:
    st.markdown("### 💹 Cotações")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div></div>""", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📰 Notícias")
    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"""<div class="news-card"><a href="{n['link']}" target="_blank" class="news-title">{n['titulo']}</a><div class="news-date">📅 {n['data']}</div></div>""", unsafe_allow_html=True)
    else: st.info("Carregando...")

# --- ABA 3: FERRAMENTAS ---
with aba3:
    st.markdown("### 🚜 Ferramentas de Bolso")
    
    # FERRAMENTA 1: CONVERSOR
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.markdown("#### 🔄 Conversor de Área")
    col_conv1, col_conv2 = st.columns(2)
    with col_conv1:
        valor = st.number_input("Valor:", min_value=0.0, value=1.0)
        unidade_de = st.selectbox("De:", ["Alqueire Paulista (2.42)", "Alqueire Goiano/MG (4.84)", "Alqueire Baiano (9.68)", "Hectare"])
    with col_conv2:
        st.write("") 
        st.write("")
        fator = 1.0
        if "Paulista" in unidade_de: fator = 2.42
        elif "Goiano" in unidade_de: fator = 4.84
        elif "Baiano" in unidade_de: fator = 9.68
        
        resultado_ha = valor * fator
        st.metric(label="Em Hectares (ha)", value=f"{resultado_ha:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

    # FERRAMENTA 2: PLANTIO
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.markdown("#### 🌱 Sementes por Hectare")
    c_seed1, c_seed2 = st.columns(2)
    with c_seed1:
        pop_desejada = st.number_input("Plantas/ha desejadas (mil):", value=300)
        pms = st.number_input("PMS (g):", value=180.0)
    with c_seed2:
        germinacao = st.number_input("Germinação (%):", value=90)
        espacamento = st.number_input("Espaçamento (cm):", value=50)
    
    if st.button("Calcular Sementes"):
        pop_real = (pop_desejada * 1000) / (germinacao / 100)
        kg_ha = (pop_real * pms) / 1000000
        metros_lineares = 10000 / (espacamento / 100)
        sementes_metro = pop_real / metros_lineares
        
        st.success(f"📦 Você precisa de: **{kg_ha:.1f} kg/ha**")
        st.info(f"📏 Regular plantadeira para: **{sementes_metro:.1f} sementes/metro**")
    st.markdown('</div>', unsafe_allow_html=True)

    # FERRAMENTA 3: TANQUE (NOVA)
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.markdown("#### 💧 Calculadora de Tanque")
    c_tank1, c_tank2 = st.columns(2)
    with c_tank1:
        cap_tanque = st.number_input("Tamanho do Tanque (Litros):", value=2000)
        vazao_ha = st.number_input("Vazão (L/ha):", value=150)
    with c_tank2:
        dose_produto = st.number_input("Dose do Produto (L ou Kg / ha):", value=0.5)
    
    if st.button("Calcular Calda"):
        area_coberta = cap_tanque / vazao_ha
        qtd_produto = area_coberta * dose_produto
        st.success(f"🚜 Um tanque cheio cobre: **{area_coberta:.1f} hectares**")
        st.warning(f"⚠️ Colocar no tanque: **{qtd_produto:.2f} Litros (ou Kg)** do produto")
    st.markdown('</div>', unsafe_allow_html=True)
