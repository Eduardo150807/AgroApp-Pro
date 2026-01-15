import streamlit as st
import google.generativeai as genai
import os
import tempfile
import urllib.parse
from PIL import Image
from fpdf import FPDF
import datetime
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import PyPDF2

# --- Configuração Visual (TEM QUE SER O PRIMEIRO COMANDO ST) ---
st.set_page_config(page_title="AgroReport Pro", page_icon="🚜", layout="wide")

# --- CSS POWER: CORREÇÃO MOBILE + MODO QUIOSQUE + CHAT ---
st.markdown("""
    <style>
    /* 1. ESCONDER MENU DE 3 PONTINHOS E RODAPÉ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. ESCONDER BARRA COLORIDA DO TOPO (Mas deixar botão visível) */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
    
    /* 3. FORÇAR O BOTÃO DE ABRIR A BARRA LATERAL A APARECER (MOBILE) */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        color: #2E7D32 !important;
        display: block !important;
    }

    /* AJUSTE PARA O CONTEÚDO NÃO FICAR COLADO NO TOPO */
    .block-container {
        padding-top: 2rem;
    }

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
    
    /* Notícias */
    .news-card {
        background-color: #1a1a1a;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #4CAF50;
    }
    .news-title { font-weight: bold; color: #fff; text-decoration: none; font-size: 1.1em; }
    .news-date { font-size: 0.8em; color: #aaa; margin-top: 5px; }
    a:hover { color: #81c784; }

    /* Outros */
    .feno-box { background-color: #1E3F20; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 6px solid #4CAF50; color: white !important; }
    .feno-title { font-size: 1.2em; font-weight: bold; color: #A5D6A7 !important; display: block; margin-bottom: 5px; }
    .feno-desc { font-size: 1.0em; color: #FFFFFF !important; font-weight: 500; }
    .id-box { background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; border-radius: 5px; color: #E65100; margin-bottom: 20px; }
    
    /* CHAT CORRIGIDO (LETRA PRETA) */
    .chat-user { 
        text-align: right; 
        background-color: #BBDEFB; 
        color: #000000 !important; 
        padding: 12px; 
        border-radius: 15px 15px 0 15px; 
        display: inline-block; 
        margin: 5px 0 5px auto;
        float: right;
        clear: both;
        max-width: 80%;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .chat-ai { 
        text-align: left;
        background-color: #DCEDC8; 
        color: #000000 !important; 
        padding: 12px; 
        border-radius: 15px 15px 15px 0; 
        display: inline-block; 
        margin: 5px auto 5px 0;
        float: left;
        clear: both;
        max-width: 80%;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .chat-container { display: flex; flex-direction: column; }
    
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🧠 FUNÇÕES GERAIS
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

def ler_pdf(arquivo):
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro ao ler PDF: {e}"

def carregar_noticias_agro():
    url = "https://news.google.com/rss/search?q=agronegocio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        with urlopen(url) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            noticias = []
            for item in root.findall('./channel/item')[:8]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

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
    try:
        resp = model.generate_content([prompt, *arquivos_api])
        texto_limpo = forcar_termos_tecnicos(resp.text)
        try: os.unlink(path)
        except: pass
        return texto_limpo
    except Exception as e:
        if "429" in str(e): return "⚠️ **ERRO DE COTA:** A IA está 'cansada'. Aguarde 30 segundos."
        else: raise e

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
# 📊 DADOS ESTÁTICOS
# ==========================================
FENOLOGIA_TEXTOS = {
    "🌱 Soja": {"VE/VC": "Emergência.", "V1-V4": "Vegetativo.", "R1": "Início Flor.", "R3": "Canivete.", "R5": "Enchimento.", "R7": "Maturação.", "R8": "Maduro."},
    "🌽 Milho": {"VE": "Emergência.", "V3": "3 folhas.", "VT": "Pendoamento.", "R1": "Embonecamento.", "R6": "Maturidade."},
    "☁️ Algodão": {"B1": "Botão Floral.", "F1": "Primeira Flor.", "C1": "Primeira Maçã.", "M": "Capulho Aberto."},
    "🌾 Trigo": {"Perfilhamento": "Perfilhos.", "Emborrachamento": "Alongamento.", "Espigamento": "Espiga.", "Antese": "Floração."},
    "🫘 Feijão": {"V3": "Trifólio.", "R6": "Flor.", "R7": "Vagem."}
}
MAPA_IMAGENS = {
    "🌱 Soja": "regua_soja.jpg", "🌽 Milho": "regua_milho.jpg", "☁️ Algodão": "regua_algodao.jpg", 
    "🌾 Trigo": "regua_trigo.jpg", "🫘 Feijão": "regua_feijao.jpg"
}

# ==========================================
# 🔐 LOGIN
# ==========================================
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_atual' not in st.session_state: st.session_state['usuario_atual'] = ""
if 'tipo_usuario' not in st.session_state: st.session_state['tipo_usuario'] = ""

CREDENCIAIS = {
    "Eduardo Dev": {"senha": "Eduardo2007", "tipo": "admin"},
    "felpz":       {"senha": "f2025",       "tipo": "admin"} 
}

def fazer_login():
    u = st.session_state.get('w_u', '')
    s = st.session_state.get('w_p', '')
    if u in CREDENCIAIS and CREDENCIAIS[u]["senha"] == s:
        st.session_state['logado'] = True
        st.session_state['usuario_atual'] = u
        st.session_state['tipo_usuario'] = CREDENCIAIS[u]["tipo"]
        st.rerun()
    else: st.error("Erro.")

if not st.session_state['logado']:
    st.title("🔐 AgroReport Login")
    st.text_input("Usuário", key="w_u")
    st.text_input("Senha", type="password", key="w_p")
    st.button("Entrar", on_click=fazer_login)
    st.stop()

# --- MENU ---
with st.sidebar:
    st.header(f"Olá, {st.session_state['usuario_atual']}")
    st.caption("Versão PRO 3.9 (Mobile Fixed)")
    
    if st.session_state['tipo_usuario'] == 'admin':
        opcoes = [
            "📝 Gerador de Laudo", "📊 Mercado & Notícias", "🔍 Identificador + Debate", 
            "🤖 AgroChat (Com Fotos)", "🧪 Análise de Solo", "💰 Finanças (Leitor NF)",
            "🇺🇸 Inglês Agro", "📚 Resumo Acadêmico (PDF)", "📏 Régua Fenológica"
        ]
    else:
        opcoes = ["📊 Mercado & Notícias", "🤖 AgroChat (Com Fotos)", "🔍 Identificador + Debate", "📏 Régua Fenológica"]
        
    opcao = st.radio("Ferramentas:", opcoes)
    st.markdown("---")
    if st.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()
    
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: 
        st.markdown("---")
        api_key = st.text_input("Chave Google:", type="password")


# 1. GERADOR
if opcao == "📝 Gerador de Laudo":
    st.title("📝 Gerador de Laudo")
    t1, t2 = st.tabs(["🎙️ Gravar", "📂 Importar"])
    aud = None
    with t1: a = st.audio_input("Gravar Relato"); aud = a if a else None
    with t2: a = st.file_uploader("Arquivo Áudio", type=['ogg','mp3']); aud = a if a else None
    fotos = st.file_uploader("Fotos", type=["jpg","png"], accept_multiple_files=True)
    if aud and st.button("Gerar PDF"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Analisando..."):
                try:
                    aud.seek(0)
                    res = processar_laudo(aud, fotos, api_key)
                    if "ERRO DE COTA" in res: st.error(res)
                    else:
                        st.success("Pronto!")
                        res_ed = st.text_area("Texto:", res, height=300)
                        pdf = gerar_pdf(res_ed, st.session_state['usuario_atual'], fotos)
                        c1, c2 = st.columns(2)
                        with c1: st.download_button("📄 PDF", pdf, "Laudo.pdf", "application/pdf")
                        with c2: st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(res_ed)}" target="_blank" class="whatsapp-btn">Zap</a>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Erro: {e}")

# 2. MERCADO
elif opcao == "📊 Mercado & Notícias":
    st.title("📊 Mercado & Notícias")
    c1, c2 = st.columns(2); c1.metric("Soja", "R$ 128,50", "-1.2"); c2.metric("Milho", "R$ 58,90", "0.5")
    c3, c4 = st.columns(2); c3.metric("Dólar", "R$ 5,04", "0.02"); c4.metric("Boi", "R$ 235", "-2.0")
    st.markdown("---")
    st.subheader("📰 Manchetes do Agro")
    if st.button("🔄 Atualizar"): st.rerun()
    noticias = carregar_noticias_agro()
    if noticias:
        col1, col2 = st.columns(2)
        for i, news in enumerate(noticias):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""<div class="news-card"><a href="{news['link']}" target="_blank" class="news-title">{news['titulo']}</a><div class="news-date">🕒 {news['data']}</div></div>""", unsafe_allow_html=True)
    else: st.info("Sem notícias no momento.")

# 3. IDENTIFICADOR
elif opcao == "🔍 Identificador + Debate":
    st.title("🔍 Detector Fitossanitário")
    st.markdown("""<div class="id-box">⚠️ <b>Aviso:</b> Ferramenta de triagem.</div>""", unsafe_allow_html=True)
    if "id_historico" not in st.session_state: st.session_state["id_historico"] = []
    if "id_imagem_atual" not in st.session_state: st.session_state["id_imagem_atual"] = None
    col_img, col_chat = st.columns([1, 1])
    with col_img:
        cultura_id = st.selectbox("Cultura:", ["🌱 Soja", "🌽 Milho", "☁️ Algodão", "Outra"])
        arquivo = st.camera_input("📸 Foto") or st.file_uploader("Upload", type=["jpg","png"])
        if arquivo:
            st.session_state["id_imagem_atual"] = Image.open(arquivo)
            st.image(st.session_state["id_imagem_atual"], width=300)
            if st.button("🔎 Analisar"):
                if not api_key: st.error("Falta API")
                else:
                    with st.spinner("Analisando..."):
                        try:
                            model = genai.GenerativeModel(descobrir_modelo(api_key))
                            prompt = f"Atue como Fitopatologista. Cultura: {cultura_id}. Analise imagem. Responda: Diagnóstico, Evidências e Recomendação."
                            res = model.generate_content([prompt, st.session_state["id_imagem_atual"]]).text
                            st.session_state["id_historico"] = [{"role": "assistant", "content": res}]
                        except Exception as e: st.error(f"Erro: {e}")
    with col_chat:
        st.subheader("💬 Debate")
        for msg in st.session_state["id_historico"]:
            role_class = "chat-ai" if msg["role"] == "assistant" else "chat-user"
            st.markdown(f"<div class='{role_class}'>{msg['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)
        correcao = st.chat_input("Discorda? Comente aqui.")
        if correcao:
            if not api_key: st.error("API?")
            elif not st.session_state["id_imagem_atual"]: st.error("Falta Imagem")
            else:
                st.session_state["id_historico"].append({"role": "user", "content": correcao})
                with st.spinner("Reavaliando..."):
                    try:
                        model = genai.GenerativeModel(descobrir_modelo(api_key))
                        res = model.generate_content([f"Usuário disse: '{correcao}'. Reanalise.", st.session_state["id_imagem_atual"]]).text
                        st.session_state["id_historico"].append({"role": "assistant", "content": res})
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# 4. AGROCHAT
elif opcao == "🤖 AgroChat (Com Fotos)":
    st.title("🤖 AgroChat")
    if "msgs" not in st.session_state: st.session_state["msgs"] = []
    with st.expander("📸 Enviar foto"): foto_chat = st.file_uploader("Anexar", type=["jpg","png"], key="chat_img")
    
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for m in st.session_state["msgs"]: 
        role_class = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{role_class}'>{m['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if p := st.chat_input("Pergunta?"):
        if not api_key: st.error("API?")
        else:
            st.session_state["msgs"].append({"role": "user", "content": p})
            try:
                model = genai.GenerativeModel(descobrir_modelo(api_key))
                cont = [p, Image.open(foto_chat)] if foto_chat else [p]
                res = model.generate_content(cont).text
                st.session_state["msgs"].append({"role": "assistant", "content": res})
                st.rerun()
            except Exception as e: st.warning("🚦 Aguarde.")

# 5. RESUMO ACADÊMICO
elif opcao == "📚 Resumo Acadêmico (PDF)":
    st.title("📚 Resumo de Estudos")
    aba1, aba2 = st.tabs(["📄 PDF", "📸 Foto"])
    with aba1: 
        arq_pdf = st.file_uploader("PDF", type=["pdf"])
        if arq_pdf: 
            txt = ler_pdf(arq_pdf)
            if "Erro" in txt: st.error(txt + " (Atualize requirements.txt!)")
            else: st.info(f"PDF Lido. {len(txt)} caracteres.")
    with aba2: arq_foto = st.file_uploader("Foto", type=["jpg","png"])
    if st.button("Resumir"):
        if not api_key: st.error("API?")
        else:
            with st.spinner("Lendo..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    prompt = "Resuma para um agrônomo de campo."
                    cont = [prompt, Image.open(arq_foto)] if arq_foto else f"{prompt}\nTexto: {txt[:30000]}"
                    st.write(model.generate_content(cont).text)
                except Exception as e: st.error(f"Erro: {e}")

# 6. ANÁLISE SOLO
elif opcao == "🧪 Análise de Solo":
    st.title("🧪 Leitor de Solo")
    arquivo = st.camera_input("Foto Laudo") or st.file_uploader("Upload", type=["jpg","png"])
    if arquivo and st.button("Ler"):
        if not api_key: st.error("API?")
        else:
            with st.spinner("Lendo..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    st.write(model.generate_content(["Analise solo. pH, V%, Correção.", Image.open(arquivo)]).text)
                except Exception as e: st.error(f"Erro: {e}")

# 7. FINANÇAS
elif opcao == "💰 Finanças (Leitor NF)":
    st.title("💰 Leitor de Notas")
    arquivo = st.camera_input("Foto NF") or st.file_uploader("Upload", type=["jpg","png"])
    if arquivo and st.button("Ler"):
        if not api_key: st.error("API?")
        else:
            with st.spinner("Lendo..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    st.write(model.generate_content(["Extraia dados da NF em tabela.", Image.open(arquivo)]).text)
                except Exception as e: st.error(f"Erro: {e}")

# 8. INGLÊS
elif opcao == "🇺🇸 Inglês Agro":
    st.title("🇺🇸 Tradutor")
    txt = st.text_area("Texto em Inglês")
    if txt and st.button("Traduzir"):
        if not api_key: st.error("API?")
        else:
            try:
                model = genai.GenerativeModel(descobrir_modelo(api_key))
                st.success(model.generate_content(f"Traduza tecnicamente: {txt}").text)
            except Exception as e: st.error(f"Erro: {e}")

# 9. RÉGUA
elif opcao == "📏 Régua Fenológica":
    st.title("📏 Fenologia")
    c = st.selectbox("Cultura", list(FENOLOGIA_TEXTOS.keys()))
    for n,d in FENOLOGIA_TEXTOS[c].items(): st.markdown(f"<div class='feno-box'><b>{n}</b><br>{d}</div>", unsafe_allow_html=True)
    img = os.path.join("img_fenologia", MAPA_IMAGENS.get(c))
    if os.path.exists(img): st.image(img, use_container_width=True)
