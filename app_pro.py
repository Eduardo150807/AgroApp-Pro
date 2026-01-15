# --- CSS POWER: CORREÇÃO MOBILE + MODO QUIOSQUE ---
st.markdown("""
    <style>
    /* 1. ESCONDER O MENU DE 3 PONTINHOS (Canto superior direito) */
    #MainMenu {visibility: hidden;}
    
    /* 2. ESCONDER O RODAPÉ (Onde aparece 'Manage App' e 'Made with Streamlit') */
    footer {visibility: hidden;}
    
    /* 3. ESCONDER A BARRA COLORIDA DO TOPO (Mas manter o botão de abrir a sidebar) */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
    /* Esconde a decoração colorida do topo, mas deixa os botões clicáveis */
    header[data-testid="stHeader"] > .stAppHeader {
        background-color: transparent;
    }
    
    /* 4. GARANTIR QUE O BOTÃO DE ABRIR A SIDEBAR ESTEJA VISÍVEL NO MOBILE */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        color: #2E7D32 !important; /* Deixa o ícone verde para destacar */
    }

    /* AJUSTE PARA O CONTEÚDO SUBIR */
    .block-container {
        padding-top: 2rem; /* Um pouco mais de espaço para não ficar colado no topo */
    }

    /* (Mantenha o resto do seu CSS de botões, notícias e chat aqui...) */
    
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
    /* ... (O resto do seu CSS continua igual) */
    .whatsapp-btn { display: inline-block; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; text-align: center; width: 100%; margin-top: 10px; }
    .news-card { background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4CAF50; }
    .news-title { font-weight: bold; color: #fff; text-decoration: none; font-size: 1.1em; }
    .news-date { font-size: 0.8em; color: #aaa; margin-top: 5px; }
    a:hover { color: #81c784; }
    .feno-box { background-color: #1E3F20; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 6px solid #4CAF50; color: white !important; }
    .feno-title { font-size: 1.2em; font-weight: bold; color: #A5D6A7 !important; display: block; margin-bottom: 5px; }
    .feno-desc { font-size: 1.0em; color: #FFFFFF !important; font-weight: 500; }
    .id-box { background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; border-radius: 5px; color: #E65100; margin-bottom: 20px; }
    
    /* CHAT CORRIGIDO */
    .chat-user { text-align: right; background-color: #BBDEFB; color: #000000 !important; padding: 12px; border-radius: 15px 15px 0 15px; display: inline-block; margin: 5px 0 5px auto; float: right; clear: both; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .chat-ai { text-align: left; background-color: #DCEDC8; color: #000000 !important; padding: 12px; border-radius: 15px 15px 15px 0; display: inline-block; margin: 5px auto 5px 0; float: left; clear: both; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .chat-container { display: flex; flex-direction: column; }
    
    </style>
    """, unsafe_allow_html=True)
