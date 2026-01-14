import streamlit as st
import google.generativeai as genai
import os
import tempfile
import urllib.parse
from PIL import Image
from fpdf import FPDF
import datetime
import time

# --- Configuração Visual ---
st.set_page_config(page_title="AgroReport Pro", page_icon="🚜", layout="centered")

st.markdown("""
    <style>
    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        background-color: #2E7D32;
        color: white;
        border: none;
    }
    .whatsapp-btn {
        display: inline-block;
        background-color: #25D366;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
        width: 100%;
        margin-top: 10px;
    }
    
    /* RÉGUA FENOLÓGICA (VISUAL DARK) */
    .feno-box {
        background-color: #1E3F20; 
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 6px solid #4CAF50; 
    }
    .feno-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #A5D6A7 !important;
        display: block;
        margin-bottom: 5px;
    }
    .feno-desc {
        font-size: 1.0em;
        color: #FFFFFF !important; 
        font-weight: 500;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNÇÕES IA (COM PROTEÇÃO CONTRA ERRO 429)
# ==========================================
def descobrir_modelo(key):
    genai.configure(api_key=key)
    try:
        lista = list(genai.list_models())
        for m in lista:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods: return m.name
        return lista[0].name if lista else "gemini-1.5-flash"
    except: return "gemini-1.5-flash"

def forcar_termos_tecnicos(texto):
    dic = {
        " download": " baixeiro", " Download": " Baixeiro", " baixar": " baixeiro",
        " baixou": " atingiu o baixeiro", " pressao": " alta severidade", " pressão": " alta severidade",
        " segurou": " controlou", " nao segurou": " falha de controle", " mato": " planta daninha",
        " auros": " Áureo", " aureo": " Áureo"
    }
    for e, c in dic.items(): texto = texto.replace(e, c)
    return texto

def processar_laudo(audio_file, lista_imagens, key):
    modelo_nome = descobrir_modelo(key)
    genai.configure(api_key=key)
    model = genai.GenerativeModel(modelo_nome)
    
    arquivos_api = []
    
    nome = audio_file.name if hasattr(audio_file, 'name') else "audio.mp3"
    ext = os.path.splitext(nome)[1] or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(audio_file.read())
        path = tmp.name
    audio_up = genai.upload_file(path, mime_type="audio/mp3")
    arquivos_api.append(audio_up)
    
    if lista_imagens:
        for img_file in lista_imagens:
            img_file.seek(0)
            img = Image.open(img_file)
            arquivos_api.append(img)

    prompt = f"""
    Engenheiro Agrônomo redigindo RELATÓRIO TÉCNICO. Contexto: Áudio + Fotos.
    Modelo: {modelo_nome}
    OBJETIVO: Relatório fiel ao ditado.
    ESTRUTURA: 1. RESUMO, 2. DIAGNÓSTICO, 3. PRESCRIÇÃO (Manter nomes comerciais), 4. OBSERVAÇÕES.
    REGRAS: "Baixeiro" NÃO É "Download". "Pressão" É "Alta Severidade".
    """
    
    # TENTATIVA COM PROTEÇÃO DE COTA (RETRY)
    try:
        resp = model.generate_content([prompt, *arquivos_api])
        texto_limpo = forcar_termos_tecnicos(resp.text)
        try: os.unlink(path)
        except: pass
        return texto_limpo
        
    except Exception as e:
        # Se der erro 429 (Cota excedida)
        if "429" in str(e) or "ResourceExhausted" in str(e):
            return "⚠️ **ERRO DE COTA:** A IA está 'cansada' (Muitos pedidos em pouco tempo). Aguarde 30 segundos e tente novamente. Isso é uma limitação da chave gratuita do Google."
        else:
            raise e # Se for outro erro, mostra normal

# ==========================================
# 📄 PDF
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_fill_color(46, 125, 50)
        self.rect(0, 0, 210, 20, 'F')
        if os.path.exists("logo.png"): self.image("logo.png", 10, 2, 16)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, 'RELATÓRIO TÉCNICO DE CAMPO', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'AgroReport AI - Pág {self.page_no()}', align='C')

def limpar_texto_pdf(texto):
    lixo = ["**", "##", "🐛", "🚜", "📸", "⚠️", "✅"]
    for item in lixo: texto = texto.replace(item, "")
    return texto.encode('latin-1', 'replace').decode('latin-1')

def gerar_pdf(texto, usuario, lista_imagens):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    data = datetime.datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 6, f"Responsável: {usuario} | Data: {data}", ln=True)
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, limpar_texto_pdf(texto))
    if lista_imagens:
        for i, img_file in enumerate(lista_imagens):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, f"ANEXO #{i+1}", ln=True, align='C')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(img_file.getvalue())
                path = tmp.name
            try: pdf.image(path, x=15, w=180) 
            except: pass
            os.unlink(path)
    return bytes(pdf.output())

# ==========================================
# 📊 DADOS FENOLÓGICOS
# ==========================================
FENOLOGIA_TEXTOS = {
    "🌱 Soja": {
        "VE/VC": "Emergência e Cotilédones abertos.",
        "V1-V4": "Vegetativo (nós com trifólios abertos).",
        "R1 (Início Flor)": "Uma flor aberta em qualquer nó.",
        "R3 (Canivete)": "Vagem de 5mm nos 4 nós superiores.",
        "R5 (Enchimento)": "Semente de 3mm na vagem (Crítico).",
        "R7 (Maturação)": "Uma vagem marrom/madura.",
        "R8": "95% das vagens maduras."
    },
    "🌽 Milho": {
        "VE": "Emergência.",
        "V3": "3 folhas (Definição de estande).",
        "V6": "Ponto de crescimento sai do solo.",
        "VT (Pendoamento)": "Último ramo do pendão visível.",
        "R1 (Embonecamento)": "Estigmas (cabelo) visíveis.",
        "R6 (Maturidade)": "Camada negra na base."
    },
    "☁️ Algodão": {
        "B1": "Botão Floral visível.",
        "F1": "Primeira Flor Branca.",
        "C1": "Primeira Maçã.",
        "M": "Primeiro Capulho Aberto."
    },
    "🌾 Trigo": {
        "Perfilhamento": "Surgimento dos perfilhos.",
        "Emborrachamento": "Alongamento do colmo.",
        "Espigamento": "Emergência da espiga.",
        "Antese": "Floração."
    },
    "🫘 Feijão": {
        "V3": "Primeira folha trifoliolada.",
        "R6": "Abertura da flor.",
        "R7": "Formação das vagens."
    }
}
MAPA_IMAGENS = {
    "🌱 Soja": "regua_soja.jpg",
    "🌽 Milho": "regua_milho.jpg",
    "☁️ Algodão": "regua_algodao.jpg",
    "🌾 Trigo": "regua_trigo.jpg",
    "🫘 Feijão": "regua_feijao.jpg"
}

# ==========================================
# 🔐 LOGIN
# ==========================================
USUARIOS = {"admin": "agro123", "teste": "123"}
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_atual' not in st.session_state: st.session_state['usuario_atual'] = ""

def fazer_login():
    u = st.session_state.get('w_u', '')
    s = st.session_state.get('w_p', '')
    if u in USUARIOS and USUARIOS[u] == s:
        st.session_state['logado'] = True
        st.session_state['usuario_atual'] = u
        st.rerun()
    else: st.error("Erro.")

if not st.session_state['logado']:
    st.title("🔐 AgroReport Login")
    st.text_input("Usuário", key="w_u")
    st.text_input("Senha", type="password", key="w_p")
    st.button("Entrar", on_click=fazer_login)
    st.stop()

# --- MENU LATERAL ---
with st.sidebar:
    st.header(f"Olá, {st.session_state['usuario_atual']}")
    st.caption("Versão PRO 2.4")
    
    opcao = st.radio("Ferramentas:", [
        "📝 Gerador de Laudo",
        "📊 Mercado & Cotações",
        "📏 Régua Fenológica",
        "🤖 Chatbot Técnico"
    ])
    
    st.markdown("---")
    if st.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()
    st.markdown("---")
    api_key = st.text_input("Chave Google:", type="password")


# --- 1. GERADOR DE LAUDO ---
if opcao == "📝 Gerador de Laudo":
    st.title("📝 Gerador de Laudo")
    
    t1, t2 = st.tabs(["🎙️ Gravar", "📂 Importar"])
    aud = None
    with t1: 
        a = st.audio_input("Gravar Relato")
        if a: aud = a
    with t2:
        a = st.file_uploader("Arquivo de Áudio", type=['ogg','mp3','m4a'])
        if a: 
            st.audio(a)
            aud = a
            
    fotos = st.file_uploader("Fotos da Vistoria", type=["jpg","png"], accept_multiple_files=True)
    if fotos: st.write(f"{len(fotos)} fotos selecionadas.")

    if aud:
        st.warning("⚠️ **Revisão:** Confira se nomes comerciais (Ex: 'Áureo', 'Fox') foram transcritos corretamente antes de gerar o PDF.")

    if aud and st.button("Gerar PDF"):
        if not api_key: st.error("Falta Chave API")
        else:
            with st.spinner("Analisando..."):
                try:
                    aud.seek(0)
                    res = processar_laudo(aud, fotos, api_key)
                    
                    if "ERRO DE COTA" in res:
                        st.error(res) # Mostra o erro amigável se estourou a cota
                    else:
                        st.success("Pronto!")
                        res_editavel = st.text_area("Texto do Laudo (Editável):", res, height=300)
                        pdf_bytes = gerar_pdf(res_editavel, st.session_state['usuario_atual'], fotos)
                        
                        c1, c2 = st.columns(2)
                        with c1: st.download_button("📄 Baixar PDF", pdf_bytes, "Laudo.pdf", "application/pdf")
                        with c2: 
                            txt = urllib.parse.quote(res_editavel)
                            st.markdown(f'<a href="https://wa.me/?text={txt}" target="_blank" class="whatsapp-btn">Zap</a>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Erro: {e}")


# --- 2. MERCADO (AGORA COMPLETO) ---
elif opcao == "📊 Mercado & Cotações":
    st.title("📊 Painel de Mercado")
    
    # Linha 1: Soja e Milho
    c1, c2 = st.columns(2)
    with c1: st.metric("Soja (60kg)", "R$ 128,50", "-1.20 R$")
    with c2: st.metric("Milho (60kg)", "R$ 58,90", "0.50 R$")
    
    # Linha 2: Dólar e Boi (RESTAURADOS!)
    c3, c4 = st.columns(2)
    with c3: st.metric("Dólar (USD)", "R$ 5,04", "0.02 R$")
    with c4: st.metric("Boi Gordo (@)", "R$ 235,00", "-2.00 R$")
    
    st.line_chart([132, 131, 130, 128, 129, 130, 128, 127, 128, 129])


# --- 3. RÉGUA FENOLÓGICA ---
elif opcao == "📏 Régua Fenológica":
    st.title("📏 Régua de Estádios")
    cultura = st.selectbox("Selecione a Cultura:", list(FENOLOGIA_TEXTOS.keys()))
    st.divider()
    
    estadios = FENOLOGIA_TEXTOS[cultura]
    for nome, descricao in estadios.items():
        st.markdown(f"""
        <div class="feno-box">
            <span class="feno-title">{nome}</span>
            <span class="feno-desc">{descricao}</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    nome_arquivo = MAPA_IMAGENS.get(cultura)
    caminho_foto = os.path.join("img_fenologia", nome_arquivo)
    
    st.subheader("📸 Escala Visual Completa")
    if os.path.exists(caminho_foto):
        st.image(caminho_foto, use_container_width=True)
    else:
        st.info(f"Salve a imagem '{nome_arquivo}' na pasta 'img_fenologia' para vê-la aqui.")


# --- 4. CHATBOT TÉCNICO (COM PROTEÇÃO 429) ---
elif opcao == "🤖 Chatbot Técnico":
    st.title("🤖 Consultor IA")
    if "msgs" not in st.session_state: st.session_state["msgs"] = []
    
    for m in st.session_state["msgs"]: st.chat_message(m["role"]).write(m["content"])
    
    if p := st.chat_input("Dúvida técnica?"):
        if not api_key: st.error("Falta API Key")
        else:
            st.session_state["msgs"].append({"role": "user", "content": p})
            st.chat_message("user").write(p)
            
            nome_modelo_chat = descobrir_modelo(api_key) 
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(nome_modelo_chat)
            
            try:
                res = model.generate_content(f"Agrônomo Sênior respondendo curto: {p}").text
                st.session_state["msgs"].append({"role": "assistant", "content": res})
                st.chat_message("assistant").write(res)
            except Exception as e:
                # Tratamento amigável do erro 429 no Chat
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    msg_erro = "🚦 Tráfego intenso! A IA está no limite gratuito. Aguarde uns 10 segundos."
                    st.session_state["msgs"].append({"role": "assistant", "content": msg_erro})
                    st.chat_message("assistant").write(msg_erro)
                else:
                    st.error(f"Erro: {e}")