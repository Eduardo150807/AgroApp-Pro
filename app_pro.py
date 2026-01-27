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

# --- CSS PREMIUM (ZAP STYLE) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background-color: transparent;}
    
    /* Campos de texto escuros */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { 
        background-color: #1E1E1E !important; 
        color: white !important; 
        border-radius: 10px; 
    }
    
    /* ABAS MINIMALISTAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #121212;
        border-radius: 20px;
        color: #888;
        padding: 0 20px;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E7D32;
        color: white;
        border: none;
    }

    /* MERCADO CARD */
    .market-card { background-color: #121212; border: 1px solid #333; border-radius: 12px; padding: 15px; text-align: center; transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .market-card:hover { border-color: #4CAF50; transform: translateY(-2px); }
    .market-symbol { color: #888; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; }
    .market-price { color: #fff; font-size: 1.8em; font-weight: 700; margin: 5px 0; }
    .market-change-up { color: #00E676; font-weight: bold; font-size: 0.9em; }
    .market-change-down { color: #FF5252; font-weight: bold; font-size: 0.9em; }

    /* CHAT BUBBLES */
    .chat-user { text-align: right; background-color: #005c4b; color: white; padding: 10px 15px; border-radius: 10px 0 10px 10px; display: inline-block; margin: 5px 0 5px auto; max-width: 85%; }
    .chat-ai { text-align: left; background-color: #202c33; color: #ECEFF1; padding: 10px 15px; border-radius: 0 10px 10px 10px; display: inline-block; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #37474F; }
    .chat-container { display: flex; flex-direction: column; margin-bottom: 20px;}
    
    /* ESCONDER O LABEL DO UPLOAD PARA FICAR LIMPO */
    [data-testid="stFileUploader"] label {display: none;}
    [data-testid="stCameraInput"] label {display: none;}
    
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNÇÕES
# ==========================================
def descobrir_modelo_disponivel(key):
    genai.configure(api_key=key)
    try:
        modelos = list(genai.list_models())
        # Prioriza modelos que aceitam multimidia
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
            for item in root.findall('./channel/item')[:6]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

# ==========================================
# 🔄 LOGIN & SETUP
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

# --- SIDEBAR LIMPA ---
with st.sidebar:
    st.title("🧠 Config")
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
aba_chat, aba_mercado = st.tabs(["💬 AgroMind Chat", "📈 Mercado"])

# --- ABA 1: CHAT WHATSAPP STYLE ---
with aba_chat:
    
    # 1. MOSTRAR MENSAGENS ANTERIORES
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state["messages"]:
        role = "chat-user" if msg["role"] == "user" else "chat-ai"
        icon = "🧑‍🌾" if role == "chat-user" else "🧠"
        st.markdown(f"<div class='{role}'>{icon} {msg['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. BARRA DE FERRAMENTAS (ACIMA DO CHAT)
    # Criamos colunas para os botões ficarem alinhados
    col_tools1, col_tools2, col_spacer = st.columns([1, 4, 15])
    
    midia_enviada = None
    tipo_midia = None # 'imagem', 'pdf', 'audio'

    with col_tools1:
        # MENU FLUTUANTE (POPOVER) - O "Clips" do WhatsApp
        with st.popover("📎", help="Anexar Foto ou Documento"):
            st.markdown("**Selecione uma opção:**")
            
            tab_foto, tab_cam, tab_doc = st.tabs(["🖼️ Galeria", "📸 Câmera", "📄 Documento"])
            
            with tab_foto:
                upl_img = st.file_uploader("Escolher foto", type=["jpg","png","jpeg"], key=f"img_{st.session_state['uploader_key']}")
                if upl_img: 
                    midia_enviada = upl_img
                    tipo_midia = 'imagem'
            
            with tab_cam:
                cam_img = st.camera_input("Tirar foto")
                if cam_img: 
                    midia_enviada = cam_img
                    tipo_midia = 'imagem'

            with tab_doc:
                upl_doc = st.file_uploader("PDF/Word", type=["pdf", "docx", "txt"], key=f"doc_{st.session_state['uploader_key']}")
                if upl_doc:
                    midia_enviada = upl_doc
                    tipo_midia = 'pdf'

    with col_tools2:
        # GRAVADOR DE ÁUDIO
        audio_rec = st.audio_input("🎙️")
        if audio_rec:
            midia_enviada = audio_rec
            tipo_midia = 'audio'

    # Aviso visual se algo estiver anexado
    if midia_enviada:
        st.info(f"📎 {tipo_midia.upper()} anexado! Digite sua mensagem abaixo para enviar tudo.")

    # 3. CAMPO DE DIGITAÇÃO (FIXO EMBAIXO)
    prompt = st.chat_input("Digite sua mensagem...")

    # LÓGICA DE ENVIO
    if prompt or (midia_enviada and tipo_midia == 'audio'):
        if not api_key: st.error("Falta API Key"); st.stop()
        
        # Se for áudio, o prompt pode ser "Analise este áudio" se o usuário não digitou nada
        texto_usuario = prompt if prompt else "Analise este arquivo/áudio."
        
        # Mostra na tela
        st.session_state["messages"].append({"role": "user", "content": texto_usuario})
        
        # Configura IA
        nome_modelo = descobrir_modelo_disponivel(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(nome_modelo)
        resposta = ""

        with st.spinner("AgroMind analisando..."):
            try:
                # --- PROCESSAMENTO POR TIPO ---
                
                # 1. IMAGEM (Fitopatologista)
                if tipo_midia == 'imagem':
                    img = Image.open(midia_enviada)
                    prompt_final = f"Atue como Fitopatologista. Usuário: '{texto_usuario}'. Identifique e recomende."
                    resposta = model.generate_content([prompt_final, img]).text
                
                # 2. PDF/DOC (Resumo)
                elif tipo_midia == 'pdf':
                    if midia_enviada.type == "application/pdf":
                        texto_extraido = ler_pdf(midia_enviada)
                        prompt_final = f"Resuma/Analise este documento. Contexto: '{texto_usuario}'. Texto: {texto_extraido[:30000]}"
                        resposta = model.generate_content(prompt_final).text
                    else:
                        resposta = "Ainda não leio DOCX, apenas PDF por enquanto."

                # 3. ÁUDIO (Transcrever e Responder)
                elif tipo_midia == 'audio':
                    # O Gemini processa áudio direto
                    prompt_final = "Ouça o áudio do produtor rural e responda/aja conforme solicitado."
                    # Upload temporário para API
                    resposta = model.generate_content([prompt_final,  {
                        "mime_type": "audio/mp3",
                        "data": midia_enviada.read()
                    }]).text

                # 4. SÓ TEXTO (Camaleão com Memória)
                else:
                    historico = ""
                    for m in st.session_state["messages"]:
                        h_role = "User" if m["role"] == "user" else "AI"
                        historico += f"{h_role}: {m['content']}\n"

                    prompt_sistema = f"""
                    Você é o AgroMind.
                    DIRETRIZ:
                    1. Pergunta curta/técnica -> Resposta seca e direta.
                    2. Conversa/Dúvida -> Resposta consultiva, didática e parceira.
                    
                    Histórico:
                    {historico}
                    
                    Atual: {texto_usuario}
                    """
                    resposta = model.generate_content(prompt_sistema).text

                st.session_state["messages"].append({"role": "assistant", "content": resposta})
                
                # Limpa o anexo forçando rerun (incrementa chave)
                if midia_enviada:
                    st.session_state["uploader_key"] += 1
                
                st.rerun()

            except Exception as e:
                st.error(f"Erro: {e}")


# --- ABA 2: MERCADO MINIMALISTA ---
with aba_mercado:
    st.markdown("#### 💹 Painel de Cotações")
    
    # Cards menores e mais limpos
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div><div class="market-change-down">▼ -1.2%</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div><div class="market-change-up">▲ +0.5%</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div><div class="market-change-down">▼ -0.8%</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div><div class="market-change-up">▲ +0.1%</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_btn, col_title = st.columns([1, 5])
    with col_btn: 
        if st.button("🔄"): st.rerun()
    with col_title:
        st.caption("Últimas Notícias")

    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"**[{n['titulo']}]({n['link']})** \n<span style='color:#666; font-size:0.8em'>{n['data']}</span>", unsafe_allow_html=True)
            st.divider()
