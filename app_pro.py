# --- ABA 3: FERRAMENTAS ---
with aba3:
    st.markdown("### 🚜 Ferramentas Técnicas")
    
    # 1. PLANTIO (MANTIDO IGUAL)
    with st.expander("🌱 Plantio (Cálculo Flexível)", expanded=False):
        # ... (seu código de plantio anterior continua aqui) ...
        # (Para economizar espaço na resposta, mantenha o código de Plantio da versão 29.0 aqui)
        pass 

    # 2. ADUBAÇÃO (MANTIDO IGUAL)
    with st.expander("🌾 Adubação & Calagem", expanded=False):
         # ... (seu código de adubação anterior continua aqui) ...
         pass

    # 3. PULVERIZAÇÃO (AGORA HÍBRIDA: TRATOR OU DRONE)
    with st.expander("🧪 Pulverização (Trator & Drone)", expanded=True):
        
        # CHAVE SELETORA
        tipo_equip = st.radio("Equipamento:", ["🚜 Trator", "🚁 Drone Agrícola"], horizontal=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if tipo_equip == "🚁 Drone Agrícola":
                tanque = st.number_input("Tanque do Drone (L):", value=10.0, step=1.0)
            else:
                tanque = st.number_input("Tanque do Pulverizador (L):", value=2000.0, step=100.0)
        
        with c2:
            # Drones usam volumes muito menores (UBV)
            val_padrao = 10.0 if tipo_equip == "🚁 Drone Agrícola" else 150.0
            vazao = st.number_input("Volume de Calda (L/ha):", value=val_padrao, step=1.0)

        # CAMPOS ESPECÍFICOS DE DRONE
        if tipo_equip == "🚁 Drone Agrícola":
            st.markdown("---")
            st.caption("🚁 Parâmetros de Voo (Opcional para cálculo avançado)")
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1: faixal = st.number_input("Faixa de Aplicação (m):", value=5.0)
            with c_d2: veloc = st.number_input("Velocidade (km/h):", value=20.0)
            with c_d3: bat_voo = st.number_input("Hectares por Bateria:", value=2.0) # Quantos ha 1 bateria faz

        st.markdown("---")
        st.write("📋 Planejamento:")
        c3, c4 = st.columns(2)
        with c3: dose = st.number_input("Dose Produto (L ou Kg/ha):", value=0.0)
        with c4: area_total = st.number_input("Área Total (ha):", value=0.0)
        
        if st.button("Calcular Aplicação"):
            if vazao > 0 and tanque > 0:
                # 1. CÁLCULO DE COBERTURA DO TANQUE
                area_tanque = tanque / vazao
                
                html_res = f"""<div class="result-box">
                <b>⛽ Um tanque cheio cobre: {area_tanque:.2f} ha</b>"""

                # SE FOR DRONE, MOSTRA EFICIÊNCIA OPERACIONAL
                if tipo_equip == "🚁 Drone Agrícola" and faixal > 0 and veloc > 0:
                    # Capacidade Teórica (ha/h) = (Velocidade x Faixa) / 10
                    cap_teorica = (veloc * faixal) / 10
                    html_res += f"<br>⚡ <b>Rendimento Teórico: {cap_teorica:.1f} ha/hora</b>"

                # 2. CÁLCULO DE PRODUTO
                if dose > 0:
                    prod_tanque = area_tanque * dose
                    html_res += f"<br>🧪 <b>Colocar no Tanque: {prod_tanque:.2f} (L ou Kg)</b>"

                # 3. PLANEJAMENTO TOTAL (LOGÍSTICA)
                if area_total > 0:
                    num_tanques = area_total / area_tanque
                    vol_total = area_total * vazao
                    
                    html_res += f"<br><br>📋 <b>Logística Total ({area_total} ha):</b>"
                    html_res += f"<br>💧 Calda Total: {vol_total:,.0f} L"
                    html_res += f"<br>🔄 Recargas (Tanques): {num_tanques:.1f} voos/tanques"
                    
                    # CÁLCULO DE BATERIAS (SÓ DRONE)
                    if tipo_equip == "🚁 Drone Agrícola" and bat_voo > 0:
                        num_baterias = area_total / bat_voo
                        html_res += f"<br>🔋 <b>Trocas de Bateria Estimadas: {num_baterias:.1f} un</b>"
                    
                    if dose > 0:
                        prod_total = area_total * dose
                        html_res += f"<br>📦 Produto Total: {prod_total:.1f} (L ou Kg)"
                
                html_res += "</div>"
                st.markdown(html_res, unsafe_allow_html=True)
            else:
                st.error("Tanque e Volume devem ser maiores que 0.")

    # 4. CONVERSÕES (MANTIDO IGUAL)
    with st.expander("📊 Conversor de Medidas", expanded=False):
        # ... (código de conversão mantido) ...
        pass
