import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import time

# --- CONFIGURAÇÃO INICIAL (SEGURA) ---
st.set_page_config(
    page_title="AgroMind", 
    page_icon="🧠", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS VISUAL (DARK MODE + SEM BARRAS + PROTEÇÃO DE DOM) ---
st.markdown("""
    <style>
    /* Esconde elementos do Streamlit de forma segura */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    /* Forçar Dark Mode */
    .stApp { 
        background-color: #0E1117; 
    }
    
    /* Balões de Chat */
    .chat-user { 
        background-color: #005c4b; 
        color: white; 
        padding: 12px; 
        border-radius: 12px 0 12px 12px; 
        margin: 5px 0 5px auto; 
        max-width: 85%; 
        text-align: right; 
        border: 1px solid #004d3d;
    }
    .chat-ai { 
        background-color: #202c33; 
        color: #e9edef; 
        padding: 12px; 
        border-radius: 0 12px 12px 12px; 
        margin: 5px auto 5px 0; 
        max-width: 85%; 
        border: 1px solid #333; 
    }
    
    /* Inputs e Botões */
    .stTextInput input { 
        background-color: #2a3942 !important; 
        color: white !important; 
        border-radius: 20px !important; 
    }
    /* Proteção para evitar erro de tradutor no botão */
    .stPopover button span {
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def ler_pdf(arquivo):
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for p in leitor.pages: 
            extract = p.extract_text()
            if extract: texto += extract + "\n"
        return texto
    except: return "Erro ao ler PDF."

# --- SELEÇÃO DE MODELO COM FALLBACK (ANTI-CRASH) ---
def obter_modelo_seguro(api_key, tools_config=None):
    # Tenta Flash (Rápido)
    try:
        return genai.GenerativeModel('gemini-1.5-flash', tools=tools_config)
    except:
        pass
    
    # Tenta Pro (Estável)
    try:
        return genai.GenerativeModel('gemini-1.5-pro', tools=tools_config)
    except:
        pass

    # Último recurso (Básico)
    return genai.GenerativeModel('gemini-pro')

def gerar_resposta_inteligente(prompt, historico, midia=None):
    # Verifica API Key
    if "GOOGLE_API_KEY" in st.secrets:
        chave = st.secrets["GOOGLE_API_KEY"]
    else:
        return "⚠️ Erro: Chave de API não configurada. Verifique os Secrets do Streamlit."

    genai.configure(api_key=chave)
    
    # Configura Ferramenta de Busca
    tools = [
        {"google_search_retrieval": {
            "dynamic_retrieval_config": {
                "mode": "dynamic",
                "dynamic_threshold": 0.3,
            }
        }}
    ]
    
    # Obtém modelo seguro
    model = obter_modelo_seguro(chave, tools)
    
    prompt_sistema = f"""
    Você é o AgroMind, consultor agronômico sênior.
    
    DIRETRIZES:
    1. CLIMA/ATUALIDADES: Use o Google Search para dados em tempo real. Sempre cite a fonte.
    2. TÉCNICO: Responda seco e direto para perguntas técnicas (cálculos, dosagens).
    3. CONVERSA: Seja parceiro e didático.
    
    HISTÓRICO: {historico}
    PERGUNTA: {prompt}
    """
    
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        else:
            return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"⚠️ Erro técnico na IA: {str(e)}. Tente novamente."

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
        else: 
            st.error("Senha incorreta")
    st.stop()

# --- APP PRINCIPAL ---
st.markdown("### 🧠 AgroMind")

# Renderiza Chat (Sem usar containers complexos para evitar erro de DOM)
for m in st.session_state["messages"]:
    classe = "chat-user" if m["role"] == "user" else "chat-ai"
    # Usando st.markdown direto evita aninhamento que confunde o React
    st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

# Espaçador para o chat não ficar escondido atrás do input
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

# Área de Input Fixa (Estratégia mais estável)
arquivo = None

# Criação das colunas para input
col1, col2 = st.columns([1, 6])

with col1:
    with st.popover("➕"):
        tipo = st.radio("Anexar:", ["📸 Câmera", "🖼️ Galeria", "📄 PDF"])
        if tipo == "📸 Câmera": 
            arquivo = st.camera_input("Foto")
        elif tipo == "🖼️ Galeria": 
            arquivo = st.file_uploader("Img", type=["jpg", "png"])
        else: 
            arquivo = st.file_uploader("Doc", type=["pdf"])

with col2:
    texto = st.chat_input("Pergunte sobre manejo, pragas, clima...")

# Processamento da mensagem
if texto or arquivo:
    msg_usuario = texto if texto else "Analise este anexo."
    
    # Adiciona mensagem do usuário
    st.session_state["messages"].append({"role": "user", "content": msg_usuario})
    
    # Spinner nativo do Streamlit (mais seguro que containers customizados)
    with st.spinner("AgroMind processando..."):
        # Limita histórico para evitar estouro de memória (últimas 4 msgs)
        historico_recente = st.session_state["messages"][-4:]
        historico_txt = "\n".join([f"{m['role']}: {m['content']}" for m in historico_recente])
        
        # Chama IA
        resp = gerar_resposta_inteligente(msg_usuario, historico_txt, arquivo)
        
        # Adiciona resposta
        st.session_state["messages"].append({"role": "assistant", "content": resp})
        
        # Rerun seguro (apenas se necessário)
        st.rerun()
