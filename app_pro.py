import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS VISUAL (DARK & LIMPO) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stApp { background-color: #0E1117; }

    /* Estilo de Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 10px; border-radius: 10px; margin: 5px 0 5px auto; max-width: 80%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 10px; border-radius: 10px; margin: 5px auto 5px 0; max-width: 80%; border: 1px solid #333; }
    
    /* Botões Ferramentas */
    .stPopover button { border-radius: 50% !important; width: 50px !important; height: 50px !important; background-color: #262730 !important; border: none !important; }

    /* Mercado */
    .market-card { background-color: #121212; border: 1px solid #333; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #888; font-size: 0.8em; text-transform: uppercase; }
    .market-price { color: #fff; font-size: 1.5em; font-weight: 700; }
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
            for item in root.findall('./channel/item')[:5]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

# --- AQUI ESTÁ A CORREÇÃO: DESCOBRIR O MODELO AUTOMATICAMENTE ---
def conectar_ia_segura():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None, "Erro: Falta GOOGLE_API_KEY no Secrets."
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Tenta listar os modelos que o servidor conhece
    try:
        lista_modelos = genai.list_models()
        modelo_escolhido = None
        
        # 1. Tenta achar o Flash (Prioridade)
        for m in lista_modelos:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name:
                    return genai.GenerativeModel(m.name), None
        
        # 2. Se não achar, pega o Pro
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                if 'pro' in m.name:
                    return genai.GenerativeModel(m.name), None

        # 3. Se não achar nada específico, pega o 'gemini-pro' padrão
        return genai.GenerativeModel('gemini-pro'), None
        
    except Exception as e:
        # Se listar falhar, tenta forçar o gemini-pro na marra
        try:
            return genai.GenerativeModel('gemini-pro'), None
        except:
            return None, f"Erro crítico na IA: {e}"

def gerar_resposta_inteligente(prompt, historico, midia=None):
    # Conecta usando a função segura acima
    model, erro = conectar_ia_segura()
    if erro: return erro
    
    prompt_sistema = f"""
    Você é o AgroMind. 
    REGRA: Responda tecnicamente se for pergunta curta. Seja amigável se for conversa.
    Histórico: {historico}
    Pergunta: {prompt}
    """
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"⚠️ O servidor não conseguiu processar. Tente atualizar a página. (Erro: {e})"

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
                st.error("Dados incorretos")
    st.stop()

# --- APP PRINCIPAL ---
st.title("🧠 AgroMind Chat")

aba1, aba2 = st.tabs(["💬 Conversa", "📊 Mercado"])

with aba1:
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 6])
    arquivo = None
    
    with col1:
        with st.popover("📎"):
            tipo = st.radio("Tipo:", ["Foto", "Câmera", "Documento"])
            if tipo == "Foto": arquivo = st.file_uploader("Galeria", type=["jpg", "png"])
            elif tipo == "Câmera": arquivo = st.camera_input("Foto")
            else: arquivo = st.file_uploader("PDF", type=["pdf"])

    with col2:
        audio = st.audio_input("🎙️")
        if audio: arquivo = audio

    prompt_usuario = st.chat_input("Digite sua pergunta...")

    if prompt_usuario or arquivo:
        texto = prompt_usuario if prompt_usuario else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": texto})
        
        # Prepara a Mídia
        midia_processada = arquivo
        if arquivo and hasattr(arquivo, 'type'):
            if arquivo.type == "application/pdf":
                texto += f"\nPDF: {ler_pdf(arquivo)}"
                midia_processada = None
            elif "image" in arquivo.type:
                midia_processada = Image.open(arquivo)

        # Chama a IA
        res = gerar_resposta_inteligente(texto, str(st.session_state["messages"][-5:]), midia_processada)
        
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

with aba2:
    st.markdown("### 💹 Cotações")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Notícias")
    noticias = carregar_noticias()
    if noticias:
        for n in noticias:
            st.markdown(f"[{n['titulo']}]({n['link']})")
