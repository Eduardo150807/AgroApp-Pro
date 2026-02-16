import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import io

# --- CONFIGURAÇÃO AGROMIND OS ---
st.set_page_config(page_title="AgroMind Pro", page_icon="🚜", layout="wide", initial_sidebar_state="expanded")

# --- CSS PROFISSIONAL (AGROMIND OS) ---
st.markdown("""
    <style>
    /* Geral */
    .stApp { background-color: #0E1117; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Cards de Ferramentas */
    .tool-card { 
        background-color: #1f2937; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #374151; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .tool-title { color: #58a6ff; font-size: 1.2em; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    
    /* Resultado em Destaque */
    .result-box {
        background-color: #0d4429;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00a86b;
        margin-top: 15px;
        font-weight: bold;
    }

    /* Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Mercado */
    .market-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #8b949e; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px; }
    .market-price { color: #f0f6fc; font-size: 1.4em; font-weight: 800; margin: 5px 0; }
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
            for item in root.findall('./channel/item')[:5]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

def conectar_ia_segura():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None, "Erro: Configure a GOOGLE_API_KEY no Secrets."
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        lista = genai.list_models()
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
    Você é o AgroMind, consultor técnico.
    DIRETRIZES:
    1. Se for áudio, entenda e responda.
    2. Calagem: Use NC = (CTC x (V2 - V1)) / PRNT.
    3. Seja direto.
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
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind OS</h1>", unsafe_allow_html=True)
    c_login = st.container()
    with c_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema", use_container_width=True):
            if usuario in CREDENCIAIS and CREDENCIAIS[usuario] == senha:
                st.session_state['logado'] = True
                st.rerun()
            else: st.error("Acesso Negado")
    st.stop()

# --- MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("🚜 AgroMind")
    st.markdown("---")
    menu = st.radio(
        "Navegação:",
        ["💬 Chat IA", "🌱 Plantio & Sementes", "🌾 Adubação & Solo", "🧪 Pulverização", "📊 Conversões", "📈 Mercado", "💧 Irrigação", "🐄 Pecuária", "🚜 Máquinas", "💰 Custos"]
    )
    st.markdown("---")
    st.info("Versão Pro 22.0")

# --- LÓGICA DAS PÁGINAS ---

# 1. CHAT IA
if menu == "💬 Chat IA":
    st.header("💬 Consultor Inteligente")
    
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
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
    
    prompt = st.chat_input("Pergunte ao AgroMind...")
    
    if prompt or arquivo:
        txt = prompt if prompt else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": txt})
        
        midia_proc = arquivo
        # Tratamento de Áudio e Mídia
        if arquivo and hasattr(arquivo, 'type'):
            if "pdf" in arquivo.type: txt += f"\nPDF: {ler_pdf(arquivo)}"; midia_proc = None
            elif "image" in arquivo.type: midia_proc = Image.open(arquivo)
            elif "audio" in arquivo.type:
                midia_proc = {"mime_type": arquivo.type, "data": arquivo.getvalue()}
                txt = "Áudio enviado. Transcreva e responda."

        res = gerar_resposta_inteligente(txt, str(st.session_state["messages"][-5:]), midia_proc)
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

# 2. PLANTIO
elif menu == "🌱 Plantio & Sementes":
    st.header("🌱 Planejamento de Plantio")
    
    st.markdown('<div class="tool-card"><div class="tool-title">🌽 Sementes por Hectare</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: pop = st.number_input("População (mil plantas/ha):", value=300)
    with c2: germ = st.number_input("Germinação (%):", value=90)
    with c3: pureza = st.number_input("Pureza (%):", value=98)
    
    pms = st.number_input("PMS (Peso de 1000 sementes - g):", value=180.0)
    margem = st.slider("Margem de Segurança (%)", 0, 20, 10)
    
    if st.button("Calcular Sementes"):
        # Fator de valor cultural
        vc = (germ * pureza) / 100
        # Plantas necessárias reais
        pop_real = (pop * 1000) / (vc / 100)
        # Adiciona margem
        pop_real = pop_real * (1 + margem/100)
        
        kg_ha = (pop_real * pms) / 1000000
        
        st.markdown(f"""
        <div class="result-box">
        📦 Necessidade Estimada: {kg_ha:.2f} kg/ha<br>
        🌱 Sementes Totais (com {margem}% margem): {int(pop_real):,} unidades/ha
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 3. ADUBAÇÃO
elif menu == "🌾 Adubação & Solo":
    st.header("🌾 Correção e Fertilidade")
    
    aba_cal, aba_npk = st.tabs(["Calagem", "Adubação NPK"])
    
    with aba_cal:
        st.markdown('<div class="tool-card"><div class="tool-title">⚪ Calagem (Sat. Bases)</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            ctc = st.number_input("CTC (cmolc/dm³):", value=10.0)
            v1 = st.number_input("V% Atual:", value=40.0)
        with c2:
            v2 = st.number_input("V% Desejado (Meta):", value=70.0)
            prnt = st.number_input("PRNT Calcário (%):", value=80.0)
            
        if st.button("Calcular Calagem"):
            nc = (ctc * (v2 - v1)) / prnt
            st.markdown(f"""
            <div class="result-box">
            🚜 Aplicar: {nc:.2f} toneladas/ha
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with aba_npk:
        st.info("⚠️ Módulo NPK em desenvolvimento (Próxima atualização)")

# 4. PULVERIZAÇÃO
elif menu == "🧪 Pulverização":
    st.header("🧪 Tecnologia de Aplicação")
    st.markdown('<div class="tool-card"><div class="tool-title">💧 Volume de Calda</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        tanque = st.number_input("Tanque (Litros):", value=2000)
        vazao = st.number_input("Taxa de Aplicação (L/ha):", value=150)
    with col2:
        dose = st.number_input("Dose Produto (L ou Kg / ha):", value=0.5)
        
    if st.button("Calcular Tanque"):
        area = tanque / vazao
        prod_total = area * dose
        st.markdown(f"""
        <div class="result-box">
        🚜 1 Tanque cobre: {area:.1f} hectares<br>
        🧪 Colocar no tanque: {prod_total:.2f} L (ou Kg) do produto
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 5. CONVERSÕES
elif menu == "📊 Conversões":
    st.header("📊 Conversor Agrícola")
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    val = st.number_input("Valor:", value=1.0)
    tipo = st.selectbox("Converter:", [
        "Alqueire Paulista -> Hectare",
        "Alqueire Goiano -> Hectare",
        "Alqueire Baiano -> Hectare",
        "Saca (60kg) -> Tonelada",
        "Hectare -> Metros Quadrados"
    ])
    
    res = 0
    if tipo == "Alqueire Paulista -> Hectare": res = val * 2.42
    elif tipo == "Alqueire Goiano -> Hectare": res = val * 4.84
    elif tipo == "Alqueire Baiano -> Hectare": res = val * 9.68
    elif tipo == "Saca (60kg) -> Tonelada": res = (val * 60) / 1000
    elif tipo == "Hectare -> Metros Quadrados": res = val * 10000
    
    st.markdown(f"<div class='result-box'>Resultado: {res:.2f}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 6. MERCADO
elif menu == "📈 Mercado":
    st.header("📈 Cotações & Notícias")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div></div>""", unsafe_allow_html=True)
    
    st.subheader("📰 Feed de Notícias")
    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"""<a href="{n['link']}" target="_blank" style="text-decoration:none;"><div class="tool-card" style="padding:10px; margin-bottom:10px;"><span style="color:#58a6ff; font-weight:bold;">{n['titulo']}</span><br><span style="color:#8b949e; font-size:0.8em;">{n['data']}</span></div></a>""", unsafe_allow_html=True)

# MÓDULOS EM BREVE
else:
    st.header(f"🚧 {menu}")
    st.warning("Este módulo está no roadmap e será liberado na próxima atualização do AgroMind OS.")
    st.markdown("""
    **Funcionalidades previstas:**
    * Cálculos detalhados da categoria
    * Geração de relatórios PDF
    * Histórico de operações
    """)
