import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import time

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS VISUAL (DARK MODE + SEM BARRAS) ---
st.markdown("""
    <style>
    /* Esconde elementos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* Fundo Escuro */
    .stApp { background-color: #0E1117; }
    
    /* Balões de Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; border: 1px solid #004d3d;}
    .chat-ai { background-color: #202c33; color: #e9edef; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Inputs e Botões */
    .stTextInput input { background-color: #2a3942 !important; color: white !important; border-radius: 20px !important; }
    .stPopover button { border-radius: 50% !important; width: 45px !important; height: 45px !important; background-color: #2a3942 !important; border: none !important; color: #8696a0 !important;}
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

def gerar_resposta_inteligente(prompt, historico, midia=None):
    # Configura API
    if "GOOGLE_API_KEY" in st.secrets:
        chave = st.secrets["GOOGLE_API_KEY"]
    else:
        return "⚠️ Erro: Chave de API não configurada no Secrets."

    genai.configure(api_key=chave)
    
    # 🌍 CONFIGURAÇÃO DE FERRAMENTAS (BUSCA GOOGLE)
    tools = [
        {"google_search_retrieval": {
            "dynamic_retrieval_config": {
                "mode": "dynamic",
                "dynamic_threshold": 0.3,
            }
        }}
    ]
    
    # --- MUDANÇA: FORÇANDO O MODELO FLASH DIRETO ---
    # Não tentamos mais listar modelos. Vamos direto no certo.
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
    except:
        # Fallback de segurança se o flash falhar
        model = genai.GenerativeModel('gemini-1.5-pro', tools=tools)
    
    # 🧠 O CÉREBRO
    prompt_sistema = f"""
    Você é o AgroMind, consultor agronômico sênior.
    
    DIRETRIZES:
    1. 🌦️ CLIMA: Se perguntarem de clima, peça a cidade. Use o Google Search para ver a previsão. Cite a fonte.
    2. 🔎 ATUALIDADES: Use o Google Search para notícias, cotações e pessoas (Ex: "Primos Agro").
    3. 🚜 TÉCNICO: Responda seco e direto para perguntas técnicas curtas.
    
    HISTÓRICO:
    {historico}
    
    PERGUNTA: {prompt}
    """
    
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        else:
            return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"⚠️ Erro de conexão com a IA: {e}. Tente novamente em alguns segundos."

# --- TELA DE LOGIN ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind</h1>", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("Acessar", use_container_width=True):
        if senha == "f2025" or senha == "Eduardo2007":
            st.session_state['logado'] = True
            st.rerun()
        else: st.error("Senha incorreta")
    st.stop()

# --- APP PRINCIPAL ---
st.markdown("### 🧠 AgroMind")

# Chat
for m in st.session_state["messages"]:
    classe = "chat-user" if m["role"] == "user" else "chat-ai"
    st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

# Área de Input
col1, col2 = st.columns([1, 5])
arquivo = None

with col1:
    with st.popover("➕"):
        tipo = st.radio("Anexar:", ["📸 Câmera", "🖼️ Galeria", "📄 PDF"])
        if tipo == "📸 Câmera": arquivo = st.camera_input("Foto")
        elif tipo == "🖼️ Galeria": arquivo = st.file_uploader("Img", type=["jpg", "png"])
        else: arquivo = st.file_uploader("Doc", type=["pdf"])

with col2:
    texto = st.chat_input("Pergunte sobre manejo, pragas, clima...")

if texto or arquivo:
    msg_usuario = texto if texto else "Analise este anexo."
    st.session_state["messages"].append({"role": "user", "content": msg_usuario})
    
    with st.spinner("AgroMind consultando..."):
        # Prepara histórico curto (últimas 4 mensagens para economizar tokens e evitar erro)
        historico_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state["messages"][-4:]])
        
        # Chama a inteligência
        resp = gerar_resposta_inteligente(msg_usuario, historico_txt, arquivo)
        
        st.session_state["messages"].append({"role": "assistant", "content": resp})
        st.rerun()
