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

# --- Configuração Visual ---
st.set_page_config(page_title="AgroReport Pro", page_icon="🚜", layout="wide")

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
    
    /* Boxes Coloridos */
    .feno-box { background-color: #1E3F20; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 6px solid #4CAF50; }
    .feno-title { font-size: 1.2em; font-weight: bold; color: #A5D6A7 !important; display: block; margin-bottom: 5px; }
    .feno-desc { font-size: 1.0em; color: #FFFFFF !important; font-weight: 500; }
    
    .id-box { background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; border-radius: 5px; color: #E65100; margin-bottom: 20px; }
    .solo-box { background-color: #E0F2F1; border-left: 5px solid #009688; padding: 15px; border-radius: 5px; color: #004D40; margin-bottom: 20px; }
    .fin-box { background-color: #FFEBEE; border-left: 5px solid #D32F2F; padding: 15px; border-radius: 5px; color: #B71C1C; margin-bottom: 20px; }
    .ing-box { background-color: #E8EAF6; border-left: 5px solid #3F51B5; padding: 15px; border-radius: 5px; color: #1A237E; margin-bottom: 20px; }
    .calc-box { background-color: #ECEFF1; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #CFD8DC; }
    
    /* Estilo das Notícias */
    .news-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
        border-left: 5px solid #2E7D32;
    }
    .news-title { font-weight: bold; font-size: 1.1em; color: #333; }
    .news-date { font-size: 0.8em; color: #666; }
    a { text-decoration: none; color: #2E7D32; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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

def carregar_noticias_agro():
    """Busca notícias reais do Google News (RSS)"""
    url = "https://news.google.com/rss/search?q=agronegocio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        with urlopen(url) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            noticias = []
            # Pega as 5 primeiras notícias
            for item in root.findall('./channel/item')[:6]:
                noticias.append({
                    'titulo': item.find('title').text,
                    'link': item.find('link').text,
                    'data': item.find('pubDate').text
                })
            return noticias
    except:
        return [] # Retorna vazio se der erro na internet

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
        if "429" in str(e) or "ResourceExhausted" in str(e):
            return "⚠️ **ERRO DE COTA:** A IA está 'cansada'. Aguarde 30 segundos."
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
    st.caption("Versão PRO 3.0 (Com Notícias)")
    opcao = st.radio("Ferramentas:", [
        "📝 Gerador de Laudo",
        "📊 Mercado & Notícias", # MUDOU O NOME AQUI
        "🔍 Identificador de Pragas", 
        "🧪 Análise de Solo",
        "💰 Finanças (Leitor NF)",
        "🇺🇸 Inglês Agro",
        "📚 Resumo Acadêmico",
        "🧮 Calculadoras Agro",
        "📏 Régua Fenológica",
        "🤖 Chatbot Técnico"
    ])
    st.markdown("---")
    if st.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()
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

# 2. MERCADO & NOTÍCIAS (ATUALIZADO)
elif opcao == "📊 Mercado & Notícias":
    st.title("📊 Mercado & Notícias")
    
    # Cotações (Parte Superior)
    st.subheader("💰 Cotações do Dia")
    c1, c2 = st.columns(2); c1.metric("Soja (60kg)", "R$ 128,50", "-1.2"); c2.metric("Milho (60kg)", "R$ 58,90", "0.5")
    c3, c4 = st.columns(2); c3.metric("Dólar (USD)", "R$ 5,04", "0.02"); c4.metric("Boi Gordo (@)", "R$ 235", "-2.0")
    
    st.markdown("---")
    
    # Notícias (Parte Inferior)
    st.subheader("📰 Últimas do Agronegócio")
    
    if st.button("🔄 Atualizar Notícias"):
        st.rerun()
        
    noticias = carregar_noticias_agro()
    
    if noticias:
        col_news1, col_news2 = st.columns(2)
        for i, news in enumerate(noticias):
            # Alterna entre as colunas
            coluna_atual = col_news1 if i % 2 == 0 else col_news2
            with coluna_atual:
                st.markdown(f"""
                <div class="news-card">
                    <div class="news-title"><a href="{news['link']}" target="_blank">{news['titulo']}</a></div>
                    <div class="news-date">🕒 {news['data']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Não foi possível carregar as notícias agora (Verifique sua internet).")

# 3. IDENTIFICADOR
elif opcao == "🔍 Identificador de Pragas":
    st.title("🔍 Detector Fitossanitário")
    st.markdown("""<div class="id-box">⚠️ <b>Aviso:</b> Ferramenta de triagem. Use o <b>Pano Branco</b> para confirmar Ferrugem.</div>""", unsafe_allow_html=True)
    cultura_id = st.selectbox("Cultura:", ["🌱 Soja", "🌽 Milho", "☁️ Algodão", "Outra"])
    arquivo = st.camera_input("📸 Foto") or st.file_uploader("Ou upload", type=["jpg","png"])
    if arquivo and st.button("Analise"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Sherlock Holmes analisando..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    prompt = f"""Atue como Fitopatologista. Cultura: {cultura_id}. Se Soja: Diferencie Ferrugem de Mancha Parda. Responda: 1. Diagnóstico, 2. Evidências, 3. Recomendação."""
                    st.write(model.generate_content([prompt, Image.open(arquivo)]).text)
                except Exception as e: st.error(f"Erro: {e}")

# 4. ANÁLISE DE SOLO
elif opcao == "🧪 Análise de Solo":
    st.title("🧪 Leitor de Análise de Solo")
    st.markdown("""<div class="solo-box">📸 Tire foto do laudo laboratorial.</div>""", unsafe_allow_html=True)
    arquivo = st.camera_input("📸 Foto") or st.file_uploader("Ou upload", type=["jpg","png"])
    if arquivo and st.button("Interpretar"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Lendo..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    st.write(model.generate_content(["Analise este laudo de solo. Extraia pH, V%, P, K e sugira correção.", Image.open(arquivo)]).text)
                except Exception as e: st.error(f"Erro: {e}")

# 5. FINANÇAS
elif opcao == "💰 Finanças (Leitor NF)":
    st.title("💰 Leitor de Notas Fiscais")
    st.markdown("""<div class="fin-box">📸 Tire foto da Nota Fiscal de insumos. A IA extrai os dados para seu controle.</div>""", unsafe_allow_html=True)
    arquivo = st.camera_input("📸 Foto da NF") or st.file_uploader("Upload NF", type=["jpg","png"])
    if arquivo and st.button("Ler Nota"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Extraindo valores..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    prompt = """Analise esta Nota Fiscal Agro. Extraia: Data, Fornecedor, Valor Total e Produtos."""
                    st.write(model.generate_content([prompt, Image.open(arquivo)]).text)
                except Exception as e: st.error(f"Erro: {e}")

# 6. INGLÊS AGRO
elif opcao == "🇺🇸 Inglês Agro":
    st.title("🇺🇸 Tradutor Técnico")
    st.markdown("""<div class="ing-box">Tradutor especializado em termos agronômicos.</div>""", unsafe_allow_html=True)
    texto_ing = st.text_area("Cole o texto em inglês:")
    if texto_ing and st.button("Traduzir"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Traduzindo..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    st.success(model.generate_content(f"Traduza para português do Brasil, contexto agronômico: '{texto_ing}'").text)
                except Exception as e: st.error(f"Erro: {e}")

# 7. RESUMO ACADÊMICO
elif opcao == "📚 Resumo Acadêmico":
    st.title("📚 Resumo de Artigos/Livros")
    aba1, aba2 = st.tabs(["📸 Foto de Página", "📝 Colar Texto"])
    with aba1: arquivo = st.camera_input("Foto Página") or st.file_uploader("Upload Página", type=["jpg","png"])
    with aba2: texto_artigo = st.text_area("Cole o texto aqui")
    if st.button("Resumir"):
        if not api_key: st.error("Falta API")
        else:
            with st.spinner("Estudando..."):
                try:
                    model = genai.GenerativeModel(descobrir_modelo(api_key))
                    prompt = "Faça um resumo prático para um agrônomo de campo."
                    conteudo = [prompt, Image.open(arquivo)] if arquivo else f"{prompt}\nTexto: {texto_artigo}"
                    st.write(model.generate_content(conteudo).text)
                except Exception as e: st.error(f"Erro: {e}")

# 8. CALCULADORAS
elif opcao == "🧮 Calculadoras Agro":
    st.title("🧮 Calculadoras")
    tipo = st.selectbox("Tipo:", ["Plantabilidade", "Pulverização"])
    if tipo == "Plantabilidade":
        pop = st.number_input("População (pl/ha)", value=300000)
        esp = st.number_input("Espaçamento (cm)", value=45.0)
        germ = st.number_input("Germinação (%)", value=90)
        if st.button("Calcular"):
            st.metric("Sementes/metro", f"{(pop / (10000/(esp/100)) / (germ/100)):.1f}")
    else:
        tnq = st.number_input("Tanque (L)", value=2000)
        vaz = st.number_input("Vazão (L/ha)", value=150)
        dose = st.number_input("Dose (L/ha)", value=0.5)
        if st.button("Calcular"):
            st.metric("Prod. no Tanque", f"{(tnq/vaz)*dose:.2f} L")

# 9. RÉGUA
elif opcao == "📏 Régua Fenológica":
    st.title("📏 Fenologia")
    cult = st.selectbox("Cultura:", list(FENOLOGIA_TEXTOS.keys()))
    for n, d in FENOLOGIA_TEXTOS[cult].items(): st.markdown(f"<div class='feno-box'><b>{n}</b><br>{d}</div>", unsafe_allow_html=True)
    img = os.path.join("img_fenologia", MAPA_IMAGENS.get(cult))
    if os.path.exists(img): st.image(img, use_container_width=True)

# 10. CHATBOT
elif opcao == "🤖 Chatbot Técnico":
    st.title("🤖 Chatbot")
    if "msgs" not in st.session_state: st.session_state["msgs"] = []
    for m in st.session_state["msgs"]: st.chat_message(m["role"]).write(m["content"])
    if p := st.chat_input("?"):
        if not api_key: st.error("API?")
        else:
            st.session_state["msgs"].append({"role": "user", "content": p})
            st.chat_message("user").write(p)
            try:
                res = genai.GenerativeModel(descobrir_modelo(api_key)).generate_content(f"Agrônomo curto: {p}").text
                st.session_state["msgs"].append({"role": "assistant", "content": res})
                st.chat_message("assistant").write(res)
            except Exception as e: st.warning("🚦 Aguarde.")
