import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import time

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# --- CSS AGRESSIVO (DARK MODE + SEM BARRAS) ---
st.markdown("""
    <style>
    /* Esconder Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* Forçar Dark Mode */
    .stApp { background-color: #0E1117; }
    
    /* Chat Style */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; border: 1px solid #004d3d;}
    .chat-ai { background-color: #202c33; color: #e9edef; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Inputs */
    .stTextInput input { background-color: #2a3942 !important; color: white !important; border-radius: 20px !important; }
    
    /* Botões Ferramentas */
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
    # Configura a API
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # --- O PULO DO GATO: ATIVANDO A BUSCA DO GOOGLE ---
    # Isso permite que a IA pesquise na internet coisas atuais
    tools = [
        {"google_search_retrieval": {
            "dynamic_retrieval_config": {
                "mode": "dynamic",
                "dynamic_threshold": 0.3,
            }
        }}
    ]
    
    # Cria o modelo com as ferramentas de busca
    model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
    
    # Instrução de Personalidade
    prompt_sistema = f"""
    Você é o AgroMind, um consultor agronômico sênior.
    
    DIRETRIZES:
    1. USE A BUSCA DO GOOGLE se o usuário perguntar sobre pessoas, notícias atuais, cotações ou eventos recentes (ex: "Quem são Primos Agro?", "Preço da soja hoje").
    2. Se a pergunta for técnica e direta (ex: "Fórmula calagem"), responda seco e matematicamente.
    3. Se for conversa, seja parceiro ("meu amigo", "companheiro").
    
    HISTÓRICO RECENTE:
    {historico}
    
    PERGUNTA DO USUÁRIO: {prompt}
    """
    
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        else:
            return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"Erro de conexão: {e}"

# --- APP ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False

# TELA DE LOGIN (SIMPLES)
if not st.session_state['logado']:
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind</h1>", unsafe_allow_html=True)
    senha = st.text_input("Senha de Acesso", type="password")
    if st.button("Entrar", use_container_width=True):
        if senha == "f2025" or senha == "Eduardo2007": # Suas senhas
            st.session_state['logado'] = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# TELA PRINCIPAL
st.markdown("### 🧠 AgroMind")

# Histórico
for m in st.session_state["messages"]:
    classe = "chat-user" if m["role"] == "user" else "chat-ai"
    st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

# Área de Input (Fixo embaixo visualmente pelo Streamlit)
col_ferramentas, col_input = st.columns([1, 5])
arquivo = None

with col_ferramentas:
    with st.popover("➕"):
        opcao = st.radio("Anexar:", ["📸 Câmera", "🖼️ Galeria", "📄 PDF"])
        if opcao == "📸 Câmera": arquivo = st.camera_input("Foto")
        elif opcao == "🖼️ Galeria": arquivo = st.file_uploader("Upload", type=["jpg", "png"])
        else: arquivo = st.file_uploader("Doc", type=["pdf"])

with col_input:
    prompt = st.chat_input("Digite sua pergunta...")

if prompt or arquivo:
    texto_envio = prompt if prompt else "Analise este anexo."
    
    # Adiciona ao chat visual
    st.session_state["messages"].append({"role": "user", "content": texto_envio})
    
    with st.spinner("AgroMind pesquisando..."):
        # Converte histórico para texto simples
        hist_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state["messages"][-5:]])
        
        # Chama a IA
        resposta = gerar_resposta_inteligente(texto_envio, hist_txt, arquivo)
        
        st.session_state["messages"].append({"role": "assistant", "content": resposta})
        st.rerun()
