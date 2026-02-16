import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import time  # <--- IMPORTANTE: Adicionei isso para o efeito de carregamento

# --- CONFIGURAÇÃO AGROMIND ---
st.set_page_config(page_title="AgroMind Pro", page_icon="🚜", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM (VISUAL LIMPO E MODERNO) ---
st.markdown("""
    <style>
    /* Esconde menu padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    
    .stApp { background-color: #0E1117; }

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161b22;
        border-radius: 4px 4px 0px 0px;
        color: #fff;
        border: 1px solid #30363d;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
        border-color: #2ea043;
    }

    /* Chat */
    .chat-user { background-color: #005c4b; color: white; padding: 12px; border-radius: 12px 0 12px 12px; margin: 5px 0 5px auto; max-width: 85%; text-align: right; }
    .chat-ai { background-color: #202c33; color: white; padding: 12px; border-radius: 0 12px 12px 12px; margin: 5px auto 5px 0; max-width: 85%; border: 1px solid #333; }
    
    /* Mercado */
    .market-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .market-symbol { color: #8b949e; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px; }
    .market-price { color: #f0f6fc; font-size: 1.4em; font-weight: 800; margin: 5px 0; }
    
    /* Resultados Calculadoras */
    .result-box {
        background-color: #0d4429;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00a86b;
        margin-top: 10px;
        font-weight: bold;
    }
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
            for item in root.findall('./channel/item')[:6]:
                noticias.append({'titulo': item.find('title').text, 'link': item.find('link').text, 'data': item.find('pubDate').text})
            return noticias
    except: return []

def conectar_ia_segura():
    if "GOOGLE_API_KEY" not in st.secrets: return None, "Erro: Configure API KEY"
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    try:
        lista = genai.list_models()
        for m in lista:
            if 'flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), None
        return genai.GenerativeModel('gemini-pro'), None
    except: return genai.GenerativeModel('gemini-pro'), None

def gerar_resposta_inteligente(prompt, historico, midia=None):
    model, erro = conectar_ia_segura()
    if erro: return erro
    
    prompt_sistema = f"""
    Você é o AgroMind, consultor agronômico avançado. 
    Diretrizes: 
    1. Responda de forma curta, técnica e direta.
    2. Se receber áudio, transcreva mentalmente e responda a dúvida.
    Histórico: {historico}
    Input: {prompt}
    """
    try:
        if midia: return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e: return f"⚠️ Erro IA: {str(e)}"

# --- TELA DE LOGIN (ATUALIZADA COM EFEITO) ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
CREDENCIAIS = {"Eduardo Dev": "Eduardo2007", "felpz": "f2025", "Lhara": "L2026"}

if not st.session_state['logado']:
    st.markdown("<br><h1 style='text-align:center'>🔐 AgroMind Pro</h1>", unsafe_allow_html=True)
    c_login = st.container()
    with c_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            if usuario in CREDENCIAIS and CREDENCIAIS[usuario] == senha:
                # --- EFEITO DE LOGIN AQUI ---
                st.success(f"👋 Bem-vindo, {usuario}!")
                with st.spinner("Carregando sistema AgroMind..."):
                    time.sleep(2) # Espera 2 segundos para o efeito visual
                # ----------------------------
                
                st.session_state['logado'] = True
                st.rerun()
            else: 
                st.error("❌ Acesso Negado")
    st.stop()

# --- APP PRINCIPAL ---
st.title("🚜 AgroMind")

aba1, aba2, aba3 = st.tabs(["💬 Chat IA", "📈 Mercado", "🧰 Ferramentas"])

# --- ABA 1: CHAT ---
with aba1:
    for m in st.session_state["messages"]:
        classe = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f"<div class='{classe}'>{m['content']}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 6])
    arquivo = None
    with c1:
        with st.popover("📎"):
            tipo = st.radio("Anexar:", ["Galeria", "Câmera", "PDF"])
            if tipo == "Galeria": arquivo = st.file_uploader("Img", type=["jpg", "png"])
            elif tipo == "Câmera": arquivo = st.camera_input("Foto")
            else: arquivo = st.file_uploader("Doc", type=["pdf"])
    with c2:
        audio = st.audio_input("🎙️")
        if audio: arquivo = audio
    
    prompt = st.chat_input("Digite ou fale sua dúvida...")

    if prompt or arquivo:
        txt = prompt if prompt else "Analise este anexo."
        st.session_state["messages"].append({"role": "user", "content": txt})
        
        midia_proc = arquivo
        if arquivo and hasattr(arquivo, 'type'):
            if "pdf" in arquivo.type: 
                txt += f"\nPDF: {ler_pdf(arquivo)}"
                midia_proc = None
            elif "image" in arquivo.type: 
                midia_proc = Image.open(arquivo)
            elif "audio" in arquivo.type:
                midia_proc = {"mime_type": arquivo.type, "data": arquivo.getvalue()}
                txt = "Áudio recebido do produtor. Responda a dúvida falada."

        res = gerar_resposta_inteligente(txt, str(st.session_state["messages"][-5:]), midia_proc)
        st.session_state["messages"].append({"role": "assistant", "content": res})
        st.rerun()

# --- ABA 2: MERCADO ---
with aba2:
    st.markdown("### 💹 Cotações do Dia")
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="market-card"><div class="market-symbol">SOJA</div><div class="market-price">R$ 128,50</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="market-card"><div class="market-symbol">MILHO</div><div class="market-price">R$ 58,90</div></div>""", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3: st.markdown("""<div class="market-card"><div class="market-symbol">BOI</div><div class="market-price">R$ 235,00</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="market-card"><div class="market-symbol">DÓLAR</div><div class="market-price">R$ 5,04</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📰 Notícias")
    news = carregar_noticias()
    if news:
        for n in news:
            st.markdown(f"""<div style="background:#161b22; padding:10px; margin-bottom:5px; border-radius:5px;"><a href="{n['link']}" target="_blank" style="text-decoration:none; color:#58a6ff; font-weight:bold;">{n['titulo']}</a></div>""", unsafe_allow_html=True)
    else:
        st.info("Carregando notícias...")

# --- ABA 3: FERRAMENTAS ---
with aba3:
    st.markdown("### 🚜 Ferramentas Técnicas")
    
    # 1. PLANTIO (COMPLETO)
    with st.expander("🌱 Plantio (Cálculo Flexível)", expanded=True):
        modo_avancado = st.checkbox("🛠️ Modo Avançado (Qualidade e Perdas)")
        c_pop, c_esp = st.columns(2)
        with c_pop: pop = st.number_input("População Desejada (mil/ha):", value=300.0)
        with c_esp: espacamento = st.number_input("Espaçamento (cm) [Opcional]:", value=0.0)

        germ = 100.0; pureza = 100.0; pms = 0.0; perda = 0.0

        if modo_avancado:
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1: germ = st.number_input("Germinação (%):", value=100.0, max_value=100.0)
            with c2: pureza = st.number_input("Pureza (%):", value=100.0, max_value=100.0)
            with c3: perda = st.number_input("Perda (%):", value=0.0, max_value=90.0)
            with c4: pms = st.number_input("PMS (g):", value=0.0)

        if st.button("Calcular Plantio"):
            vc = (germ * pureza) / 100
            fator_perda = 1 - (perda / 100)
            
            if fator_perda <= 0:
                st.error("Erro: Perda excessiva.")
            else:
                pop_necessaria = (pop * 1000) / ((vc / 100) * fator_perda)
                
                html_res = f"""<div class="result-box">🎯 População Alvo: {int(pop*1000):,} plantas/ha<br>🌱 <b>Sementes para Plantar: {int(pop_necessaria):,} /ha</b>"""
                
                if espacamento > 0:
                    metros_lineares = 10000 / (espacamento / 100)
                    sem_metro = pop_necessaria / metros_lineares
                    html_res += f"<br><br>📏 <b>Metros Lineares: {int(metros_lineares):,} m/ha</b>"
                    html_res += f"<br>🚜 <b>Regular Máquina: {sem_metro:.1f} sementes/metro</b>"
                
                if vc < 100 or perda > 0: html_res += f"<br><br><span style='font-size:0.8em; color:#bbb'>(VC: {vc:.1f}% | Perda: {perda}%)</span>"
                html_res += "</div>"
                st.markdown(html_res, unsafe_allow_html=True)
                
                if pms > 0:
                    kg_ha = (pop_necessaria * pms) / 1000000
                    st.info(f"📦 Comprar: **{kg_ha:.1f} kg/ha**")
                elif modo_avancado:
                    st.caption("ℹ️ Preencha o PMS para saber quantos Kg comprar.")

    # 2. ADUBAÇÃO
    with st.expander("🌾 Adubação & Calagem"):
        c1, c2 = st.columns(2)
        with c1:
            ctc = st.number_input("CTC (cmolc):", value=10.0)
            v1 = st.number_input("V% Atual:", value=40.0)
        with c2:
            v2 = st.number_input("V% Meta:", value=70.0)
            prnt = st.number_input("PRNT (%):", value=80.0)
        
        if st.button("Calcular Calagem"):
            if prnt > 0:
                nc = (ctc * (v2 - v1)) / prnt
                st.markdown(f"<div class='result-box'>🚜 Aplicar: {nc:.2f} toneladas/ha</div>", unsafe_allow_html=True)

    # 3. PULVERIZAÇÃO (COMPLETA)
    with st.expander("🧪 Pulverização (Planejamento)"):
        st.write("Dados Obrigatórios:")
        c1, c2 = st.columns(2)
        with c1: tanque = st.number_input("Capacidade do Tanque (L):", value=2000.0)
        with c2: vazao = st.number_input("Volume de Calda (L/ha):", value=150.0)

        st.write("Dados Opcionais:")
        c3, c4 = st.columns(2)
        with c3: dose = st.number_input("Dose do Produto (L ou Kg/ha):", value=0.0)
        with c4: area_total = st.number_input("Área Total (ha):", value=0.0)
        
        if st.button("Calcular Pulverização"):
            if vazao > 0 and tanque > 0:
                area_tanque = tanque / vazao
                html_res = f"""<div class="result-box">🚜 <b>Um tanque cobre: {area_tanque:.2f} ha</b>"""

                if dose > 0:
                    prod_tanque = area_tanque * dose
                    html_res += f"<br>🧪 <b>Colocar no Tanque: {prod_tanque:.2f} (L ou Kg)</b>"
                else: html_res += "<br><i>(Preencha a Dose para ver qtd de produto)</i>"

                if area_total > 0:
                    num_tanques = area_total / area_tanque
                    vol_total = area_total * vazao
                    html_res += f"<br><br>📋 <b>Logística ({area_total} ha):</b>"
                    html_res += f"<br>💧 Calda Total: {vol_total:,.0f} L"
                    html_res += f"<br>🔄 Tanques: {num_tanques:.1f} viagens"
                    if dose > 0:
                        prod_total = area_total * dose
                        html_res += f"<br>📦 Produto Total: {prod_total:.1f} (L ou Kg)"
                else: html_res += "<br><i>(Preencha Área Total para ver logística)</i>"
                
                html_res += "</div>"
                st.markdown(html_res, unsafe_allow_html=True)
            else: st.error("Tanque e Vazão devem ser maiores que 0.")

    # 4. CONVERSÕES
    with st.expander("📊 Conversor de Medidas"):
        c1, c2 = st.columns(2)
        with c1: val = st.number_input("Valor:", value=1.0)
        with c2: tipo = st.selectbox("Converter:", ["Alqueire SP -> ha", "Alqueire GO -> ha", "Alqueire BA -> ha", "Saca -> Ton"])
        
        res = 0
        if "SP" in tipo: res = val * 2.42
        elif "GO" in tipo: res = val * 4.84
        elif "BA" in tipo: res = val * 9.68
        elif "Saca" in tipo: res = (val * 60) / 1000
        st.metric("Resultado", f"{res:.2f}")

