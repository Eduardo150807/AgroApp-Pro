import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2

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
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False

# --- LÓGICA DE PERSONALIDADE (CAMALEÃO) ---
def gerar_resposta_inteligente(prompt, historico, midia=None):
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Instrução para ser seco ou social
    prompt_sistema = f"""
    Você é o AgroMind. 
    REGRA DE OURO: 
    1. Se o usuário mandar uma mensagem curta/seca (ex: "Fórmula calagem"), responda APENAS o dado técnico, sem saudações ou firulas.
    2. Se o usuário conversar ou pedir explicação, seja amigável e use um tom de consultor do campo.
    
    Histórico: {historico}
    Pergunta: {prompt}
    """
    
    if midia:
        return model.generate_content([prompt_sistema, midia]).text
    return model.generate_content(prompt_sistema).text

# --- INTERFACE ---
st.title("🧠 AgroMind Chat")

aba1, aba2 = st.tabs(["💬 Conversa", "📊 Mercado"])

with aba1:
    # Exibir chat
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    # BARRA DE FERRAMENTAS (ESTILO WHATSAPP)
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
        
        # Gera resposta usando a lógica camaleão
        res = gerar_resposta_inteligente(texto, st.session_state["messages"], arquivo)
        
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

with aba2:
    st.write("Cotações em tempo real...")
    # Aqui entra sua tabela de mercado minimalista
