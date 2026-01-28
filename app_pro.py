def gerar_resposta_inteligente(prompt, historico, midia=None):
    model, erro = conectar_ia_segura()
    if erro: return erro
    
    # Prompt Blindado com a Matemática Correta
    prompt_sistema = f"""
    Você é o AgroMind, o melhor consultor de agronomia do Brasil.
    
    DIRETRIZES TÉCNICAS (MATEMÁTICA):
    1. FÓRMULA DE CALAGEM (Método Saturação por Bases):
       - A fórmula OBRIGATÓRIA é: NC (ton/ha) = (CTC x (V2 - V1)) / PRNT
       - Onde: CTC em cmolc/dm³, V2 e V1 em %, PRNT em %.
       - JAMAIS divida por 10 ou 100 se a CTC for em cmolc.
       - Se o usuário não der o PRNT, assuma 80% mas avise.
    
    DIRETRIZES DE COMPORTAMENTO:
    1. Se a pergunta for curta (ex: "Calcule calagem: CTC 10, V1 50, V2 70, PRNT 80"), dê APENAS o resultado e a conta.
    2. Se for conversa, seja parceiro.
    
    Histórico: {historico}
    Pergunta: {prompt}
    """
    try:
        if midia:
            return model.generate_content([prompt_sistema, midia]).text
        return model.generate_content(prompt_sistema).text
    except Exception as e:
        return f"⚠️ Erro de conexão (Tente novamente): {e}"
