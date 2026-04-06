import streamlit as st
import pandas as pd
import sqlite3
import json
import math
import uuid
from datetime import datetime
from database import get_db_connection
from fpdf import FPDF

# Importações dos novos módulos
from constants import *
from pdf_utils import gerar_pdf_proposta

st.set_page_config(page_title="Simulador - SEOP", page_icon="🚢", layout="wide")

# ==========================================
# INICIALIZAÇÃO DA SESSÃO
# ==========================================
if 'step' not in st.session_state: 
    st.session_state.step = 1
if 'sim_dados' not in st.session_state: 
    st.session_state.sim_dados = {'nome': '', 'empresa': '', 'email': '', 'telefone': '', 'op_nome': '', 'mod_nome': '', 'peso': 0.0, 'dias': 0, 'servicos_selecionados': {}}
if 'simulacao_salva' not in st.session_state: 
    st.session_state.simulacao_salva = False
if 'codigo_simulacao' not in st.session_state: 
    st.session_state.codigo_simulacao = None
if 'pdf_bytes_gerado' not in st.session_state: 
    st.session_state.pdf_bytes_gerado = None
if 'df_conteineres' not in st.session_state: 
    st.session_state.df_conteineres = pd.DataFrame([{
        "Tamanho": TAMANHO_20, "Tipo": TIPO_DRY, "Valor CIF (R$)": 0.0, 
        CARAC_IMO: False, CARAC_OOG: False, CARAC_ANUENCIA: False
    }])

def next_step(): 
    st.session_state.step += 1
def prev_step(): 
    st.session_state.step -= 1
def restart():
    st.session_state.step = 1
    st.session_state.simulacao_salva = False
    st.session_state.codigo_simulacao = None
    st.session_state.pdf_bytes_gerado = None
    st.session_state.df_conteineres = pd.DataFrame([{
        "Tamanho": TAMANHO_20, "Tipo": TIPO_DRY, "Valor CIF (R$)": 0.0, 
        CARAC_IMO: False, CARAC_OOG: False, CARAC_ANUENCIA: False
    }])

st.title("🚢 Simulador de Tarifas Portuárias")
st.progress(st.session_state.step / 4)
st.divider()

if st.session_state.step == 1:
    st.subheader("👤 Identificação (Opcional)")
    c1, c2 = st.columns(2)
    st.session_state.sim_dados['nome'] = c1.text_input("Nome da Pessoa", value=st.session_state.sim_dados.get('nome', ''))
    st.session_state.sim_dados['empresa'] = c2.text_input("Empresa", value=st.session_state.sim_dados.get('empresa', ''))
    
    c3, c4 = st.columns(2)
    st.session_state.sim_dados['email'] = c3.text_input("E-mail", value=st.session_state.sim_dados.get('email', ''))
    st.session_state.sim_dados['telefone'] = c4.text_input("Telefone", value=st.session_state.sim_dados.get('telefone', ''))
    
    st.write("")
    if st.button("Avançar ➡️", type="primary"): 
        next_step()
        st.rerun()

elif st.session_state.step == 2:
    with get_db_connection() as conn:
        df_op = pd.read_sql_query("SELECT id, nome FROM operacoes WHERE ativo = 1", conn)
        df_mod = pd.read_sql_query("SELECT id, nome FROM modalidades WHERE ativo = 1", conn)
        df_tipos = pd.read_sql_query("SELECT nome, is_oog FROM tipos_conteiner WHERE ativo = 1", conn)
    
    tipos_conteiner_lista = df_tipos['nome'].tolist() if not df_tipos.empty else [TIPO_DRY]
    dict_oog = dict(zip(df_tipos['nome'], df_tipos['is_oog']))
    
    c1, c2 = st.columns(2)
    op_dict = dict(zip(df_op['nome'], df_op['id']))
    mod_dict = dict(zip(df_mod['nome'], df_mod['id']))
    sel_op = c1.selectbox("Tipo de Operação", options=list(op_dict.keys()))
    sel_mod = c2.selectbox("Modalidade", options=list(mod_dict.keys()))
    
    c3, c4 = st.columns(2)
    st.session_state.sim_dados['dias'] = c3.number_input("Dias de Armazenagem Previstos", min_value=0, value=max(0, st.session_state.sim_dados['dias']))
    st.session_state.sim_dados['peso'] = c4.number_input("Peso Bruto Total (Ton)", min_value=0.0, value=max(0.0, st.session_state.sim_dados['peso']))
    
    st.divider()
    st.subheader("📦 Lista de Contenteineres")
    
    config_colunas = {
        "Tamanho": st.column_config.SelectboxColumn("Tamanho", options=TAMANHOS_PERMITIDOS, required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=tipos_conteiner_lista, required=True),
        "Valor CIF (R$)": st.column_config.NumberColumn("Valor CIF (R$)", min_value=0.0, format="%.2f"),
        CARAC_IMO: st.column_config.CheckboxColumn(CARAC_IMO),
        CARAC_OOG: st.column_config.CheckboxColumn(CARAC_OOG),
        CARAC_ANUENCIA: st.column_config.CheckboxColumn(CARAC_ANUENCIA)
    }
    
    df_editado = st.data_editor(st.session_state.df_conteineres, num_rows="dynamic", column_config=config_colunas, use_container_width=True, key="editor_cnts")
    
    st.write("")
    col_btn1, col_btn2 = st.columns([1, 4])
    
    if col_btn1.button("⬅️ Voltar"): 
        prev_step()
        st.rerun()
        
    if col_btn2.button("Avançar para Serviços ➡️", type="primary"):
        for i in df_editado.index:
            tipo_selecionado = df_editado.at[i, 'Tipo']
            if dict_oog.get(tipo_selecionado, 0) == 1:
                df_editado.at[i, CARAC_OOG] = True
        
        st.session_state.df_conteineres = df_editado
        
        if st.session_state.df_conteineres.empty or (st.session_state.df_conteineres['Valor CIF (R$)'] <= 0).any():
            st.error("❌ Adicione pelo menos 1 contentor e garanta que todos tenham Valor CIF maior que zero.")
        else:
            st.session_state.sim_dados['operacao_id'] = op_dict[sel_op]
            st.session_state.sim_dados['modalidade_id'] = mod_dict[sel_mod]
            st.session_state.sim_dados['op_nome'] = sel_op
            st.session_state.sim_dados['mod_nome'] = sel_mod
            next_step()
            st.rerun()

elif st.session_state.step == 3:
    with get_db_connection() as conn:
        df_serv_vinc = pd.read_sql_query(
            "SELECT s.id, s.codigo_rubrica, s.nome, oms.is_obrigatorio, s.regras_calculo "
            "FROM op_mod_servicos oms "
            "JOIN servicos s ON oms.servico_id = s.id "
            "WHERE oms.operacao_id = ? AND oms.modalidade_id = ? AND s.ativo = 1", 
            conn, params=(st.session_state.sim_dados['operacao_id'], st.session_state.sim_dados['modalidade_id'])
        )
    
    df_cnts = st.session_state.df_conteineres
    
    tem_reefer = df_cnts['Tipo'].astype(str).str.contains(TIPO_REEFER, case=False).any() if 'Tipo' in df_cnts.columns else False
    tem_imo = df_cnts[CARAC_IMO].any() if CARAC_IMO in df_cnts.columns else False
    tem_oog = df_cnts[CARAC_OOG].any() if CARAC_OOG in df_cnts.columns else False
    tem_anuencia = df_cnts[CARAC_ANUENCIA].any() if CARAC_ANUENCIA in df_cnts.columns else False
    
    st.subheader("🛠️ Seleção de Serviços")
    
    servicos_obrigatorios = []
    servicos_opcionais = []
    
    for _, row in df_serv_vinc.iterrows():
        is_obrig = bool(row['is_obrigatorio'])
        gatilho = GATILHO_NENHUM
        if row['regras_calculo']:
            try:
                regras = json.loads(row['regras_calculo'])
                gatilho = regras.get('gatilho_automatico', GATILHO_NENHUM)
            except:
                pass
        
        hide_service = False

        if gatilho == GATILHO_REEFER and not tem_reefer: hide_service = True
        elif gatilho == GATILHO_IMO and not tem_imo: hide_service = True
        elif gatilho == GATILHO_OOG and not tem_oog: hide_service = True
        elif gatilho == GATILHO_ANUENCIA and not tem_anuencia: hide_service = True

        if hide_service:
            continue 
            
        if is_obrig:
            servicos_obrigatorios.append(row)
        else:
            servicos_opcionais.append(row)

    st.session_state.temp_serv_map = {} 
    
    c_obrig, c_opc = st.columns(2)
    
    with c_obrig:
        st.markdown("### 🔒 Obrigatórios e Vinculados")
        st.caption("Base do processo e acionados automaticamente por gatilho da carga.")
        if not servicos_obrigatorios:
            st.info("Nenhum serviço obrigatório identificado para esta carga.")
        for row in servicos_obrigatorios:
            st.success(f"**{row['codigo_rubrica']}** - {row['nome']}")
            st.session_state.temp_serv_map[row['id']] = 'all'

    with c_opc:
        st.markdown("### ➕ Serviços Opcionais")
        st.caption("Marque o serviço e selecione em quais unidades aplicar.")
        if not servicos_opcionais:
            st.info("Nenhum serviço opcional disponível para esta carga.")
            
        for row in servicos_opcionais:
            # Identificar o gatilho deste serviço
            regras = json.loads(row['regras_calculo']) if row['regras_calculo'] else {}
            gatilho_serv = regras.get('gatilho_automatico', GATILHO_NENHUM)
            
            # ✨ NOVO: Filtrar as opções de contentores para mostrar apenas os compatíveis com o gatilho
            opcoes_cnts_filtradas = []
            for i, cnt in df_cnts.iterrows():
                match = False
                if gatilho_serv == GATILHO_NENHUM: match = True
                elif gatilho_serv == GATILHO_REEFER and TIPO_REEFER in str(cnt['Tipo']): match = True
                elif gatilho_serv == GATILHO_IMO and cnt.get(CARAC_IMO, False): match = True
                elif gatilho_serv == GATILHO_OOG and cnt.get(CARAC_OOG, False): match = True
                elif gatilho_serv == GATILHO_ANUENCIA and cnt.get(CARAC_ANUENCIA, False): match = True
                
                if match:
                    opcoes_cnts_filtradas.append(f"Unid {i+1} ({cnt['Tamanho']} {cnt['Tipo']})")

            chk = st.checkbox(f"**{row['codigo_rubrica']}** - {row['nome']}", key=f"chk_serv_{row['id']}")
            if chk:
                alvo = st.multiselect(
                    "Aplicar em quais contentores?", 
                    options=["Todos"] + opcoes_cnts_filtradas, 
                    default=["Todos"], 
                    key=f"sel_serv_{row['id']}"
                )
                if "Todos" in alvo:
                    st.session_state.temp_serv_map[row['id']] = 'all'
                else:
                    indices = []
                    for a in alvo:
                        idx_str = a.split(" ")[1]
                        indices.append(int(idx_str) - 1)
                    if indices:
                        st.session_state.temp_serv_map[row['id']] = indices
                    else:
                        st.session_state.temp_serv_map[row['id']] = [] 

    st.write("")
    col_btn1, col_btn2 = st.columns([1, 4])
    if col_btn1.button("⬅️ Voltar"): 
        prev_step()
        st.rerun()
        
    if col_btn2.button("Calcular Cotação Final 🚀", type="primary"):
        final_map = {k: v for k, v in st.session_state.temp_serv_map.items() if v == 'all' or (isinstance(v, list) and len(v) > 0)}
        st.session_state.sim_dados['servicos_selecionados'] = final_map
        next_step()
        st.rerun()

elif st.session_state.step == 4:
    dados = st.session_state.sim_dados
    df_cnts = st.session_state.df_conteineres
    
    st.subheader("📑 Resumo Detalhado da Simulação")
    st.divider()

    with st.expander("🔍 Visualizar Premissas da Simulação (Embarque e Contentores)", expanded=True):
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown(f"**Operação:** {dados.get('op_nome', '')}")
            st.markdown(f"**Modalidade:** {dados.get('mod_nome', '')}")
            st.markdown(f"**Cliente/Empresa:** {dados.get('nome', '')} / {dados.get('empresa', '')}")

        with col_res2:
            st.markdown(f"**Dias de Armazenagem:** {dados.get('dias', 0)}")
            st.markdown(f"**Peso Bruto Total (Tons):** {dados.get('peso', 0.0):,.3f}")
            st.markdown(f"**Quantidade Contentores:** {len(df_cnts)}")
            
        st.divider()
        st.caption("Contentores")
        
        df_view_cnts = df_cnts.copy()
        
        def f_sn_tela(val): return "Sim" if val else "Não"
        
        df_view_cnts["IMO"] = df_view_cnts.get("IMO (Perigosa)", False).apply(f_sn_tela)
        df_view_cnts["OOG"] = df_view_cnts.get("OOG (Excesso)", False).apply(f_sn_tela)
        df_view_cnts["Anuência"] = df_view_cnts.get("Anuência", False).apply(f_sn_tela)
        
        st.dataframe(
            df_view_cnts[["Tamanho", "Tipo", "Valor CIF (R$)", "IMO", "OOG", "Anuência"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor CIF (R$)": st.column_config.NumberColumn(format="R$ {:,.2f}")
            }
        )
    st.write("")
    st.divider()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT imposto_percentual, condicoes_cobranca, prazo_pagamento FROM configuracoes_terminal LIMIT 1")
        config_term = cursor.fetchone()
        imposto_perc = config_term[0] if config_term else 0.0
        condicoes = config_term[1] if config_term else "Padrão"
        prazo = config_term[2] if config_term else "Imediato"
        
        serv_map = dados.get('servicos_selecionados', {})
        servicos_ids = tuple(serv_map.keys())
        
        if servicos_ids:
            placeholders = ','.join('?' for _ in servicos_ids)
            df_calc = pd.read_sql_query(f"SELECT * FROM servicos WHERE id IN ({placeholders})", conn, params=servicos_ids)
            df_regras_add = pd.read_sql_query("SELECT * FROM adicionais_carga WHERE ativo = 1", conn)
            
            linhas_tabela = []
            total_sem_imposto = 0.0
            total_com_imposto = 0.0
            valor_impostos_total = 0.0
            
            def calc_imposto(valor):
                if imposto_perc > 0:
                    fator = 1 - (imposto_perc / 100)
                    t_com = valor / fator
                    return (t_com - valor), t_com
                return 0.0, valor

            for index, cnt in df_cnts.iterrows():
                cif_cnt = float(cnt['Valor CIF (R$)'])
                tam_cnt = cnt['Tamanho']
                
                caracteristicas_cnt = []
                if cnt.get(CARAC_IMO, False): caracteristicas_cnt.append('IMO (Perigosa)')
                if cnt.get(CARAC_OOG, False): caracteristicas_cnt.append('OOG (Excesso de Dimensão)')
                if cnt.get(CARAC_ANUENCIA, False): caracteristicas_cnt.append('Anuência')

                for _, serv in df_calc.iterrows():
                    serv_id = serv['id']
                    alvos_unidades = serv_map.get(serv_id, [])
                    
                    if alvos_unidades != 'all' and index not in alvos_unidades:
                        continue 
                        
                    val_base = 0.0
                    tipo = serv['tipo_cobranca']
                    vb = float(serv['valor_base'])
                    
                    gatilho_serv = GATILHO_NENHUM
                    if serv['regras_calculo']:
                        try:
                            regras = json.loads(serv['regras_calculo'])
                            gatilho_serv = regras.get('gatilho_automatico', GATILHO_NENHUM)
                        except:
                            pass
                            
                    if gatilho_serv == GATILHO_REEFER and TIPO_REEFER not in str(cnt['Tipo']):
                        continue 
                    if gatilho_serv == GATILHO_IMO and not cnt.get(CARAC_IMO, False):
                        continue
                    if gatilho_serv == GATILHO_OOG and not cnt.get(CARAC_OOG, False):
                        continue
                    if gatilho_serv == GATILHO_ANUENCIA and not cnt.get(CARAC_ANUENCIA, False):
                        continue
                    
                    if tipo == "Fixo": 
                        val_base = vb / len(df_cnts)
                    elif tipo == "Por Dia": 
                        val_base = vb * dados['dias']
                    elif tipo == "Por Tonelada": 
                        val_base = (vb * dados['peso']) / len(df_cnts)
                    elif tipo == "Por Contêiner": 
                        val_base = vb
                    elif tipo == "Percentual CIF": 
                        val_base = cif_cnt * (vb / 100)
                    elif tipo == "Por Período":
                        try: regras = json.loads(serv['regras_calculo']) if serv['regras_calculo'] else {}
                        except: regras = {}
                        dias_p = int(regras.get('dias_por_periodo', 7))
                        periodos = math.ceil(dados['dias'] / dias_p) if dados['dias'] > 0 else 0
                        val_base = vb * periodos
                    elif tipo == "Fixo por Período e Tamanho":
                        try: regras = json.loads(serv['regras_calculo']) if serv['regras_calculo'] else {}
                        except: regras = {}
                        dias_p = int(regras.get('dias_por_periodo', 7))
                        periodos = math.ceil(dados['dias'] / dias_p) if dados['dias'] > 0 else 0
                        val_20 = float(regras.get('valor_20', vb))
                        val_40 = float(regras.get('valor_40', vb))
                        valor_aplicado = val_20 if tam_cnt == TAMANHO_20 else val_40
                        val_base = valor_aplicado * periodos
                    elif tipo == "Armazenagem Escalonada" and dados['dias'] > 0:
                        try: regras = json.loads(serv['regras_calculo']) if serv['regras_calculo'] else {}
                        except: regras = {}
                        if 'periodos' in regras:
                            periodos_totais = math.ceil(dados['dias'] / regras.get('dias_por_periodo', 4))
                            for p in range(1, periodos_totais + 1):
                                cfg = regras['periodos']['1'] if p == 1 else (regras['periodos']['2'] if p == 2 else regras['periodos']['demais'])
                                val_perc = cif_cnt * (float(cfg['percentual']) / 100)
                                val_minimo = float(cfg['min_20']) if tam_cnt == TAMANHO_20 else float(cfg['min_40'])
                                val_base += max(val_perc, val_minimo)
                    
                    if val_base > 0:
                        val_add = 0.0
                        nomes_adds = []
                        
                        try: regras_serv = json.loads(serv['regras_calculo']) if serv['regras_calculo'] else {}
                        except: regras_serv = {}
                        adds_vinculados = regras_serv.get('adicionais_vinculados', [])

                        for caract in caracteristicas_cnt:
                            regras_aplicaveis = df_regras_add[df_regras_add['caracteristica'] == caract]
                            for _, regra in regras_aplicaveis.iterrows():
                                regra_id = int(regra['id'])
                                if regra['tipo_calculo'] == "Percentual sobre o Serviço (%)" and regra_id in adds_vinculados:
                                    adic = val_base * (float(regra['valor']) / 100)
                                    val_add += adic
                                    nomes_adds.append(f"{regra['nome']} ({regra['valor']}%)")

                        subtotal = val_base + val_add
                        imp_linha, tot_linha = calc_imposto(subtotal)

                        linhas_tabela.append({
                            "código": serv['codigo_rubrica'],
                            "serviço": f"{serv['nome']} (Unid {index+1})",
                            "valor_base": val_base,
                            "adicionais": val_add,
                            "desc_adds": ", ".join(nomes_adds) if nomes_adds else "-",
                            "impostos": imp_linha,
                            "valor_total": tot_linha
                        })
                        
                        total_sem_imposto += subtotal
                        valor_impostos_total += imp_linha
                        total_com_imposto += tot_linha

                for caract in caracteristicas_cnt:
                    regras_aplicaveis = df_regras_add[df_regras_add['caracteristica'] == caract]
                    for _, regra in regras_aplicaveis.iterrows():
                        val_add_indep = 0.0
                        if regra['tipo_calculo'] == "Valor Fixo Extra (R$)":
                            val_add_indep = float(regra['valor'])
                        elif regra['tipo_calculo'] == "Por Período (R$)":
                            dias_p = int(regra.get('dias_periodo', 7))
                            periodos = math.ceil(dados['dias'] / dias_p) if dados['dias'] > 0 else 0
                            val_add_indep = float(regra['valor']) * periodos

                        if val_add_indep > 0:
                            imp_indep, tot_indep = calc_imposto(val_add_indep)
                            linhas_tabela.append({
                                "código": "ADD",
                                "serviço": f"{regra['nome']} (Unid {index+1})",
                                "valor_base": 0.0,
                                "adicionais": val_add_indep,
                                "desc_adds": regra['nome'],
                                "impostos": imp_indep,
                                "valor_total": tot_indep
                            })
                            total_sem_imposto += val_add_indep
                            valor_impostos_total += imp_indep
                            total_com_imposto += tot_indep

            if linhas_tabela:
                df_res = pd.DataFrame(linhas_tabela)
                
                df_view = df_res.rename(columns={
                    "código": "Código",
                    "serviço": "Serviço",
                    "valor_base": "Valor Base (R$)",
                    "adicionais": "Adicionais (R$)",
                    "desc_adds": "Motivo Adicional",
                    "impostos": "Impostos (R$)",
                    "valor_total": "Total (R$)"
                })
                
                colunas_moeda = ["Valor Base (R$)", "Adicionais (R$)", "Impostos (R$)", "Total (R$)"]
                st.dataframe(df_view.style.format({col: "R$ {:,.2f}" for col in colunas_moeda}), hide_index=True, use_container_width=True)
                
                st.divider()
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Subtotal (Sem Impostos)", f"R$ {total_sem_imposto:,.2f}")
                col_res2.metric(f"Impostos Estimados ({imposto_perc}%)", f"R$ {valor_impostos_total:,.2f}")
                st.success(f"### Valor Total Estimado: R$ {total_com_imposto:,.2f}")
                
                if not st.session_state.simulacao_salva:
                    codigo_sim = f"SIM-{uuid.uuid4().hex[:6].upper()}"
                    st.session_state.codigo_simulacao = codigo_sim
                    
                    pdf_bytes = gerar_pdf_proposta(dados, df_cnts, linhas_tabela, total_sem_imposto, valor_impostos_total, total_com_imposto, condicoes, prazo, codigo_sim)
                    st.session_state.pdf_bytes_gerado = pdf_bytes
                    
                    json_cnts = df_cnts.to_json(orient="records")

                    cursor.execute("""
                        INSERT INTO simulacoes (
                            codigo_simulacao, nome, empresa, email, telefone, 
                            operacao, modalidade, qtd_conteineres, valor_cif, valor_total, pdf_arquivo, detalhes_conteineres
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        codigo_sim, dados['nome'], dados['empresa'], dados['email'], dados['telefone'], 
                        dados['op_nome'], dados['mod_nome'], len(df_cnts), df_cnts['Valor CIF (R$)'].sum(), total_com_imposto, pdf_bytes, json_cnts
                    ))
                    conn.commit()
                    st.session_state.simulacao_salva = True
                
                st.download_button(
                    "📥 Baixar Proposta PDF", 
                    data=st.session_state.pdf_bytes_gerado, 
                    file_name=f"Proposta_{st.session_state.codigo_simulacao}.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )
            
    if st.button("🔄 Nova Simulação"): 
        restart()
        st.rerun()
