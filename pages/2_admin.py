import streamlit as st
import pandas as pd
import sqlite3
import json
import logging
from database import get_db_connection
from constants import OPCOES_GATILHO

st.set_page_config(page_title="Painel Admin - SEOP", page_icon="⚙️", layout="wide")

st.title("⚙️ Painel Administrativo")
st.markdown("Gerencie rubricas, operações, vínculos e acompanhe o histórico de simulações.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["1. Adicionais/Taxas", "2. Serviços (Rubricas)", "3. Operações", "4. Modalidades", "5. Tipos Contêiner", "6. Vinculações", "7. Histórico"])

def salvar_edicoes(df_editado, tabela, colunas_atualizar):
    try:
        with get_db_connection() as conn:
            for index, row in df_editado.iterrows():
                valores = [row[col] for col in colunas_atualizar]
                valores.append(int(row['ativo']))
                valores.append(row['id'])
                set_clause = ", ".join([f"{col} = ?" for col in colunas_atualizar]) + ", ativo = ?"
                conn.execute(f"UPDATE {tabela} SET {set_clause} WHERE id = ?", tuple(valores))
            conn.commit()
            st.success("✅ Alterações salvas com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao salvar na tabela {tabela}: {e}")
        st.error(f"Erro no banco de dados ao salvar edições: {e}")

# ==========================================
# TAB 1: ADICIONAIS DE CARGA
# ==========================================
with tab1:
    st.header("☢️ Adicionais de Carga (IMO, OOG, Anuência)")
    with st.form("form_adicionais", clear_on_submit=True):
        nome_add = st.text_input("Nome da Taxa (ex: Posicionamento MAPA)")
        c1, c2, c3, c4 = st.columns(4)
        caracteristica = c1.selectbox("Característica", ["IMO (Perigosa)", "OOG (Excesso de Dimensão)", "Anuência", "Outros"])
        tipo_calc = c2.selectbox("Tipo de Cálculo", ["Percentual sobre o Serviço (%)", "Valor Fixo Extra (R$)", "Por Período (R$)"]) 
        valor_add = c3.number_input("Valor (% ou R$)", min_value=0.0, format="%.2f")
        
        dias_p = 7
        if tipo_calc == "Por Período (R$)":
            dias_p = c4.number_input("Dias por Período", min_value=1, value=7)
            
        if st.form_submit_button("Criar Novo Adicional"):
            if nome_add:
                try:
                    with get_db_connection() as conn:
                        conn.execute("INSERT INTO adicionais_carga (nome, caracteristica, tipo_calculo, valor, servico_base_id, dias_periodo) VALUES (?, ?, ?, ?, ?, ?)", (nome_add, caracteristica, tipo_calc, valor_add, None, dias_p))
                        conn.commit()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao criar adicional: {e}")

    try:
        with get_db_connection() as conn:
            df_add = pd.read_sql_query("SELECT id, nome, caracteristica, tipo_calculo, valor, dias_periodo, ativo FROM adicionais_carga", conn)
        
        if not df_add.empty:
            st.divider()
            df_add['ativo'] = df_add['ativo'].astype(bool)
            df_add_editado = st.data_editor(df_add, hide_index=True, use_container_width=True, disabled=["id"])
            if st.button("💾 Salvar Alterações de Adicionais"):
                salvar_edicoes(df_add_editado, "adicionais_carga", ["nome", "caracteristica", "tipo_calculo", "valor", "dias_periodo"])
                st.rerun()
    except Exception as e: 
        st.error(f"Não foi possível carregar os adicionais de carga: {e}")

# ==========================================
# TAB 2: SERVIÇOS (Rubricas)
# ==========================================
with tab2:
    st.header("Cadastro e Edição de Serviços")
    
    with get_db_connection() as conn:
        df_add_opcoes = pd.read_sql_query("SELECT id, nome FROM adicionais_carga WHERE ativo = 1", conn)
    dict_adicionais = dict(zip(df_add_opcoes['nome'], df_add_opcoes['id'])) if not df_add_opcoes.empty else {}
    dict_add_reverso = {v: k for k, v in dict_adicionais.items()}
    
    # --- BLOCO 1: CRIAR NOVO SERVIÇO ---
    with st.expander("➕ CRIAR NOVO SERVIÇO", expanded=False):
        col1, col2 = st.columns(2)
        codigo_rubrica = col1.text_input("Código da Rubrica (ex: 1.1.2)")
        nome = col2.text_input("Nome do Serviço")
        
        adicionais_selecionados = st.multiselect("Taxas adicionais que incidem sobre este serviço (IMO, OOG, etc)", options=list(dict_adicionais.keys()))
        
        norma_aplicacao = st.text_area("Texto Informativo / Norma de Aplicação (Aparecerá no PDF)")
        
        gatilho_sistema = st.selectbox("⚡ Gatilho Automático (Força a inclusão na simulação)", OPCOES_GATILHO)
        
        col3, col4 = st.columns([1, 2])
        valor_base = col3.number_input("Valor Base Padrão (R$)", min_value=0.0, format="%.2f", help="Deixe 0 se o valor for definido por regras como a Armazenagem Escalonada.")
        
        tipo_cobranca = col4.selectbox("Tipo de Cobrança", ["Fixo", "Por Dia", "Por Tonelada", "Por Contêiner", "Percentual CIF", "Armazenagem Escalonada", "Por Período", "Fixo por Período e Tamanho"])
        
        dias_p_serv = 7
        regras_dict = {}

        if tipo_cobranca == "Por Período":
            dias_p_serv = st.number_input("Dias/Período", min_value=1, value=7)
            
        elif tipo_cobranca == "Fixo por Período e Tamanho":
            st.markdown("#### ⚙️ Regras: Fixo por Período e Tamanho")
            dias_p_serv = st.number_input("Dias/Período", min_value=1, value=7)
            c_val1, c_val2 = st.columns(2)
            val_20 = c_val1.number_input("Valor para Contêiner 20'", min_value=0.0, format="%.2f", value=150.0)
            val_40 = c_val2.number_input("Valor para Contêiner 40'", min_value=0.0, format="%.2f", value=250.0)
            regras_dict["valor_20"] = val_20
            regras_dict["valor_40"] = val_40

        elif tipo_cobranca == "Armazenagem Escalonada":
            st.markdown("#### ⚙️ Regras da Armazenagem Escalonada")
            dias_p_serv = st.number_input("Dias por Período (Escalonado)", min_value=1, value=4)
            
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                st.write("**1º Período**")
                perc_1 = st.number_input("% sobre CIF (1º Período)", value=0.25, format="%.2f")
                min20_1 = st.number_input("Min 20' (1º Período)", value=100.0)
                min40_1 = st.number_input("Min 40' (1º Período)", value=150.0)
            with ce2:
                st.write("**2º Período**")
                perc_2 = st.number_input("% sobre CIF (2º Período)", value=0.50, format="%.2f")
                min20_2 = st.number_input("Min 20' (2º Período)", value=200.0)
                min40_2 = st.number_input("Min 40' (2º Período)", value=300.0)
            with ce3:
                st.write("**Demais Períodos**")
                perc_d = st.number_input("% sobre CIF (Demais)", value=1.00, format="%.2f")
                min20_d = st.number_input("Min 20' (Demais)", value=300.0)
                min40_d = st.number_input("Min 40' (Demais)", value=450.0)

            regras_dict["periodos"] = {
                "1": {"percentual": perc_1, "min_20": min20_1, "min_40": min40_1},
                "2": {"percentual": perc_2, "min_20": min20_2, "min_40": min40_2},
                "demais": {"percentual": perc_d, "min_20": min20_d, "min_40": min40_d}
            }

        if st.button("💾 Salvar Novo Serviço", type="primary"):
            if codigo_rubrica and nome:
                try:
                    regras_dict["adicionais_vinculados"] = [dict_adicionais[add_nome] for add_nome in adicionais_selecionados]
                    regras_dict["dias_por_periodo"] = dias_p_serv
                    regras_dict["gatilho_automatico"] = gatilho_sistema
                    
                    with get_db_connection() as conn:
                        conn.execute("INSERT INTO servicos (codigo_rubrica, nome, norma_aplicacao, valor_base, tipo_cobranca, regras_calculo) VALUES (?, ?, ?, ?, ?, ?)", 
                                     (codigo_rubrica, nome, norma_aplicacao, valor_base, tipo_cobranca, json.dumps(regras_dict)))
                        conn.commit()
                    st.success("Criado com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Código de Rubrica já existe.")
                except Exception as e:
                    st.error(f"Erro ao salvar serviço: {e}")
            else:
                st.warning("Preencha o Código da Rubrica e o Nome do Serviço.")
                
    # --- BLOCO 2: EDIÇÃO RÁPIDA E AVANÇADA ---
    try:
        with get_db_connection() as conn:
            df_serv = pd.read_sql_query("SELECT id, codigo_rubrica, nome, norma_aplicacao, tipo_cobranca, valor_base, regras_calculo, ativo FROM servicos", conn)
        
        if not df_serv.empty:
            st.divider()
            st.subheader("Edição Rápida (Textos, Valores e Status)")
            df_view = df_serv.copy()
            df_view['ativo'] = df_view['ativo'].astype(bool)
            
            df_serv_editado = st.data_editor(
                df_view[['id', 'codigo_rubrica', 'nome', 'norma_aplicacao', 'tipo_cobranca', 'valor_base', 'ativo']], 
                hide_index=True, 
                use_container_width=True, 
                disabled=["id", "tipo_cobranca"]
            )
            
            if st.button("💾 Salvar Edição Rápida"):
                salvar_edicoes(df_serv_editado, "servicos", ["codigo_rubrica", "nome", "norma_aplicacao", "valor_base"])
                st.rerun()
                
            st.divider()
            st.subheader("🛠️ Edição Avançada (Adicionais e Regras Específicas)")
            serv_selecionado = st.selectbox("Selecione o serviço para editar:", options=df_serv['nome'].tolist())
            
            if serv_selecionado:
                row_serv = df_serv[df_serv['nome'] == serv_selecionado].iloc[0]
                tipo_atual = row_serv['tipo_cobranca']
                
                try:
                    regras_atuais = json.loads(row_serv['regras_calculo']) if row_serv['regras_calculo'] else {}
                    ids_vinculados = regras_atuais.get("adicionais_vinculados", [])
                    nomes_vinculados_atuais = [dict_add_reverso[i] for i in ids_vinculados if i in dict_add_reverso]
                except: 
                    regras_atuais = {}
                    nomes_vinculados_atuais = []

                novos_adicionais = st.multiselect(
                    f"Adicionais que incidem sobre '{serv_selecionado}':", 
                    options=list(dict_adicionais.keys()), 
                    default=nomes_vinculados_atuais
                )
                
                gatilho_salvo = regras_atuais.get("gatilho_automatico", "Nenhum")
                index_gatilho = OPCOES_GATILHO.index(gatilho_salvo) if gatilho_salvo in OPCOES_GATILHO else 0 
                novo_gatilho = st.selectbox("⚡ Editar Gatilho Automático", OPCOES_GATILHO, index=index_gatilho)
                
                if tipo_atual == "Fixo por Período e Tamanho":
                    st.markdown("#### ⚙️ Editar Regras: Fixo por Período e Tamanho")
                    dias_p_edit = st.number_input("Dias por Período", min_value=1, value=int(regras_atuais.get("dias_por_periodo", 7)))
                    c_val1, c_val2 = st.columns(2)
                    val_20_edit = c_val1.number_input("Valor 20'", min_value=0.0, format="%.2f", value=float(regras_atuais.get("valor_20", 150.0)))
                    val_40_edit = c_val2.number_input("Valor 40'", min_value=0.0, format="%.2f", value=float(regras_atuais.get("valor_40", 250.0)))

                elif tipo_atual == "Armazenagem Escalonada":
                    st.markdown("#### ⚙️ Editar Regras da Armazenagem Escalonada")
                    
                    periodos = regras_atuais.get("periodos", {})
                    p1 = periodos.get("1", {"percentual": 0.25, "min_20": 100.0, "min_40": 150.0})
                    p2 = periodos.get("2", {"percentual": 0.50, "min_20": 200.0, "min_40": 300.0})
                    pd_demais = periodos.get("demais", {"percentual": 1.00, "min_20": 300.0, "min_40": 450.0})
                    
                    dias_p_edit = st.number_input("Dias por Período (Atualizar)", min_value=1, value=int(regras_atuais.get("dias_por_periodo", 4)))
                    
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1:
                        st.write("**1º Período**")
                        perc_1_ed = st.number_input("% sobre CIF (1º)", value=float(p1.get("percentual", 0.25)), format="%.2f")
                        min20_1_ed = st.number_input("Min 20' (1º)", value=float(p1.get("min_20", 100.0)))
                        min40_1_ed = st.number_input("Min 40' (1º)", value=float(p1.get("min_40", 150.0)))
                    with ce2:
                        st.write("**2º Período**")
                        perc_2_ed = st.number_input("% sobre CIF (2º)", value=float(p2.get("percentual", 0.50)), format="%.2f")
                        min20_2_ed = st.number_input("Min 20' (2º)", value=float(p2.get("min_20", 200.0)))
                        min40_2_ed = st.number_input("Min 40' (2º)", value=float(p2.get("min_40", 300.0)))
                    with ce3:
                        st.write("**Demais Períodos**")
                        perc_d_ed = st.number_input("% sobre CIF (Dem)", value=float(pd_demais.get("percentual", 1.00)), format="%.2f")
                        min20_d_ed = st.number_input("Min 20' (Dem)", value=float(pd_demais.get("min_20", 300.0)))
                        min40_d_ed = st.number_input("Min 40' (Dem)", value=float(pd_demais.get("min_40", 450.0)))

                if st.button("🔄 Salvar Edição Avançada", type="primary"):
                    novos_ids = [dict_adicionais[n] for n in novos_adicionais]
                    regras_atuais["adicionais_vinculados"] = novos_ids
                    regras_atuais["gatilho_automatico"] = novo_gatilho
                    
                    if tipo_atual == "Fixo por Período e Tamanho":
                        regras_atuais["dias_por_periodo"] = dias_p_edit
                        regras_atuais["valor_20"] = val_20_edit
                        regras_atuais["valor_40"] = val_40_edit

                    elif tipo_atual == "Armazenagem Escalonada":
                        regras_atuais["dias_por_periodo"] = dias_p_edit
                        regras_atuais["periodos"] = {
                            "1": {"percentual": perc_1_ed, "min_20": min20_1_ed, "min_40": min40_1_ed},
                            "2": {"percentual": perc_2_ed, "min_20": min20_2_ed, "min_40": min40_2_ed},
                            "demais": {"percentual": perc_d_ed, "min_20": min20_d_ed, "min_40": min40_d_ed}
                        }
                    
                    try:
                        with get_db_connection() as conn:
                            conn.execute("UPDATE servicos SET regras_calculo = ? WHERE id = ?", (json.dumps(regras_atuais), int(row_serv['id'])))
                            conn.commit()
                        st.success("Regras atualizadas com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar regras avançadas: {e}")
    except Exception as e:
        st.error(f"Erro ao carregar serviços: {e}")

# ==========================================
# TAB 3 e 4: OPERAÇÕES E MODALIDADES
# ==========================================
with tab3:
    st.header("Operações")
    with st.form("op_form", clear_on_submit=True):
        nome_op = st.text_input("Nome da Operação")
        if st.form_submit_button("Criar Operação") and nome_op.strip():
            try:
                with get_db_connection() as conn:
                    conn.execute("INSERT INTO operacoes (nome) VALUES (?)", (nome_op.strip(),))
                    conn.commit()
                st.rerun()
            except Exception as e: 
                st.error(f"Erro ao criar operação: {e}")

    try:
        with get_db_connection() as conn:
            df_op = pd.read_sql_query("SELECT id, nome, ativo FROM operacoes", conn)
        if not df_op.empty:
            df_op['ativo'] = df_op['ativo'].astype(bool)
            df_op_editado = st.data_editor(df_op, hide_index=True, use_container_width=True, disabled=["id"])
            if st.button("💾 Salvar Alterações de Operações"):
                salvar_edicoes(df_op_editado, "operacoes", ["nome"])
                st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar operações: {e}")

with tab4:
    st.header("Modalidades")
    with st.form("mod_form", clear_on_submit=True):
        nome_mod = st.text_input("Nome da Modalidade")
        if st.form_submit_button("Criar Modalidade") and nome_mod.strip():
            try:
                with get_db_connection() as conn:
                    conn.execute("INSERT INTO modalidades (nome) VALUES (?)", (nome_mod.strip(),))
                    conn.commit()
                st.rerun()
            except Exception as e: 
                st.error(f"Erro ao criar modalidade: {e}")

    try:
        with get_db_connection() as conn:
            df_mod = pd.read_sql_query("SELECT id, nome, ativo FROM modalidades", conn)
        if not df_mod.empty:
            df_mod['ativo'] = df_mod['ativo'].astype(bool)
            df_mod_editado = st.data_editor(df_mod, hide_index=True, use_container_width=True, disabled=["id"])
            if st.button("💾 Salvar Alterações de Modalidades"):
                salvar_edicoes(df_mod_editado, "modalidades", ["nome"])
                st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar modalidades: {e}")

# ==========================================
# TAB 5: TIPOS DE CONTÊINER
# ==========================================
with tab5:
    st.header("📦 Tipos de Contêiner")
    
    with st.form("form_tipo_conteiner", clear_on_submit=True):
        nome_tipo = st.text_input("Nome do Tipo de Contêiner (Ex: Flat Rack)")
        is_oog = st.checkbox("Este tipo é sempre OOG (Excesso)?")
        
        if st.form_submit_button("Salvar Tipo"):
            if nome_tipo:
                try:
                    with get_db_connection() as conn:
                        conn.execute("INSERT INTO tipos_conteiner (nome, is_oog) VALUES (?, ?)", (nome_tipo, is_oog))
                        conn.commit()
                    st.success(f"Tipo '{nome_tipo}' cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Erro: Este tipo de contêiner já existe.")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")
            else:
                st.warning("Por favor, informe o nome do contêiner.")
    
    st.divider()
    
    try:
        with get_db_connection() as conn:
            df_tipos = pd.read_sql_query("SELECT id, nome, is_oog, ativo FROM tipos_conteiner", conn)
        if not df_tipos.empty:
            st.subheader("Tipos Cadastrados")
            df_tipos['OOG (Excesso)'] = df_tipos['is_oog'].map({1: True, 0: False})
            df_tipos['Ativo'] = df_tipos['ativo'].map({1: True, 0: False})
            
            df_tipos_edit = st.data_editor(
                df_tipos[['id', 'nome', 'OOG (Excesso)', 'Ativo']], 
                hide_index=True, 
                disabled=['id', 'nome', 'OOG (Excesso)'],
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Erro ao carregar tipos de contêiner: {e}")
    
# ==========================================
# TAB 6: VINCULAÇÕES
# ==========================================
with tab6:
    st.header("🔗 Matriz de Cobrança (Vínculos)")
    try:
        with get_db_connection() as conn:
            df_op = pd.read_sql_query("SELECT id, nome FROM operacoes WHERE ativo = 1", conn)
            df_mod = pd.read_sql_query("SELECT id, nome FROM modalidades WHERE ativo = 1", conn)
            df_serv = pd.read_sql_query("SELECT id, codigo_rubrica, nome FROM servicos WHERE ativo = 1", conn)
            
            if not df_op.empty and not df_mod.empty and not df_serv.empty:
                with st.form("form_vinculacao", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    op_dict = dict(zip(df_op['nome'], df_op['id']))
                    mod_dict = dict(zip(df_mod['nome'], df_mod['id']))
                    serv_dict = dict(zip(df_serv['codigo_rubrica'] + " - " + df_serv['nome'], df_serv['id']))
                    
                    sel_op = c1.selectbox("Operação", options=list(op_dict.keys()))
                    sel_mod = c2.selectbox("Modalidade", options=list(mod_dict.keys()))
                    sel_serv = c3.selectbox("Serviço", options=list(serv_dict.keys()))
                    is_obrig = st.checkbox("Obrigatório?")
                    
                    sucesso = False
                    if st.form_submit_button("Criar Vinculação"):
                        try:
                            conn.execute("INSERT INTO op_mod_servicos (operacao_id, modalidade_id, servico_id, is_obrigatorio) VALUES (?, ?, ?, ?)", (op_dict[sel_op], mod_dict[sel_mod], serv_dict[sel_serv], is_obrig))
                            conn.commit()
                            sucesso = True
                        except sqlite3.IntegrityError:
                            st.error("Erro: Este vínculo já existe na matriz.")
                        except Exception as e:
                            st.error(f"Erro inesperado: {e}")
                    
                    if sucesso:
                        st.toast("✅ Vínculo criado com sucesso!")
            
            st.divider()
            st.subheader("Desvincular Serviços")
            
            df_links = pd.read_sql_query("""
                SELECT 
                    oms.operacao_id, 
                    oms.modalidade_id, 
                    oms.servico_id, 
                    o.nome as Operacao, 
                    m.nome as Modalidade, 
                    s.nome as Servico,
                    oms.is_obrigatorio as is_obrig
                FROM op_mod_servicos oms 
                JOIN operacoes o ON oms.operacao_id = o.id 
                JOIN modalidades m ON oms.modalidade_id = m.id 
                JOIN servicos s ON oms.servico_id = s.id
            """, conn)
            
            if not df_links.empty:
                df_links['Selecionar para Excluir'] = False
                df_links['Obrigatório'] = df_links['is_obrig'].map({1: 'Sim', 0: 'Não', True: 'Sim', False: 'Não'})
                
                df_links_edit = st.data_editor(
                    df_links[['Selecionar para Excluir', 'Operacao', 'Modalidade', 'Servico', 'Obrigatório']], 
                    hide_index=True,
                    use_container_width=True
                )
                
                if st.button("🗑️ Excluir Vínculos Selecionados"):
                    try:
                        for idx in df_links_edit[df_links_edit['Selecionar para Excluir'] == True].index:
                            conn.execute("DELETE FROM op_mod_servicos WHERE operacao_id=? AND modalidade_id=? AND servico_id=?", 
                                         (int(df_links.loc[idx, 'operacao_id']), int(df_links.loc[idx, 'modalidade_id']), int(df_links.loc[idx, 'servico_id'])))
                        conn.commit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir vínculos: {e}")
    except Exception as e: 
        st.error(f"Erro ao carregar matriz de vínculos: {e}")

# ==========================================
# TAB 7: HISTÓRICO DE SIMULAÇÕES
# ==========================================
with tab7:
    st.header("📊 Histórico de Simulações Realizadas")
    st.markdown("Acompanhe as cotações geradas no simulador e recupere o PDF da proposta.")
    try:
        with get_db_connection() as conn:
            tabelas = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' AND name='simulacoes'", conn)
            
            if not tabelas.empty:
                query = """
                    SELECT 
                        codigo_simulacao as ID_Simulação, 
                        data_hora as Data, 
                        COALESCE(nome, '') || ' / ' || COALESCE(empresa, '') as Cliente, 
                        operacao as Operação, 
                        modalidade as Modalidade, 
                        qtd_conteineres as Qtd_Cnt, 
                        valor_cif as Total_CIF, 
                        valor_total as Valor_Proposta 
                     FROM simulacoes 
                     ORDER BY data_hora DESC
                """
                df_hist = pd.read_sql_query(query, conn)
                
                if not df_hist.empty:
                    df_view = df_hist.copy()
                    df_view['Cliente'] = df_view['Cliente'].apply(lambda x: x.strip(' / '))
                    df_view['Total_CIF'] = df_view['Total_CIF'].apply(lambda x: f"R$ {x:,.2f}")
                    df_view['Valor_Proposta'] = df_view['Valor_Proposta'].apply(lambda x: f"R$ {x:,.2f}")

                    st.dataframe(df_view, hide_index=True, use_container_width=True)
                    
                    st.divider()
                    st.subheader("📥 Recuperar Proposta Comercial (PDF)")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    opcoes_ids = df_hist['ID_Simulação'].tolist()
                    id_selecionado = col1.selectbox("Selecione o ID da Simulação para baixar:", opcoes_ids)
                    
                    if id_selecionado:
                        cursor = conn.cursor()
                        cursor.execute("SELECT pdf_arquivo FROM simulacoes WHERE codigo_simulacao = ?", (id_selecionado,))
                        resultado = cursor.fetchone()
                        
                        if resultado and resultado[0]:
                            pdf_bytes = resultado[0]
                            
                            col2.write("") 
                            col2.write("") 
                            col2.download_button(
                                label="⬇️ Baixar Proposta PDF",
                                data=pdf_bytes,
                                file_name=f"Proposta_{id_selecionado}.pdf",
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True
                            )
                        else:
                            st.warning("O arquivo PDF desta simulação não foi encontrado no banco de dados.")
                            
                else:
                    st.info("Nenhuma simulação registada ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")