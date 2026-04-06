from fpdf import FPDF
from datetime import datetime

def gerar_pdf_proposta(dados, df_cnts, itens, total_sem, impostos, total_com, condicoes, prazo, codigo_sim):
    # Removido o orientation="L", regressando ao padrão Retrato (Portrait)
    pdf = FPDF()
    
    # [OPCIONAL] Se for usar a fonte Pilat, descomente a linha abaixo e mude os 'helvetica' para 'Pilat'
    # pdf.add_font("Pilat", style="", fname="pilat-light.ttf")
    
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    # ==========================================
    # CABEÇALHO
    # ==========================================
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "PROPOSTA COMERCIAL - SERVIÇOS PORTUÁRIOS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Simulação ID: {codigo_sim} | Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # ==========================================
    # 1. DADOS DO CLIENTE
    # ==========================================
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "1. DADOS DO CLIENTE", border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"Nome/Contato: {dados.get('nome', 'Não informado')} | Empresa: {dados.get('empresa', 'Não informada')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"E-mail: {dados.get('email', 'Não informado')} | Telefone: {dados.get('telefone', 'Não informado')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ==========================================
    # 2. INFORMAÇÕES DO EMBARQUE
    # ==========================================
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "2. INFORMAÇÕES DO EMBARQUE (PREMISSAS)", border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    largura_rotulo = 60
    largura_valor = 120 # Ajustado para o total de 180mm do formato retrato

    def adicionar_linha_quadro(rotulo, valor):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(largura_rotulo, 8, f"{rotulo}:", border=1, align="R")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(largura_valor, 8, str(valor), border=1, new_x="LMARGIN", new_y="NEXT")

    adicionar_linha_quadro("Tipo de Operação", dados.get('op_nome', ''))
    adicionar_linha_quadro("Modalidade", dados.get('mod_nome', ''))
    adicionar_linha_quadro("Dias de Armazenagem Previstos", f"{dados.get('dias', 0)} dias")
    adicionar_linha_quadro("Peso Bruto Total (Premissa)", f"{dados.get('peso', 0.0):,.3f} Ton")
    pdf.ln(5)

    # ==========================================
    # 3. DETALHAMENTO DOS CONTENTORES
    # ==========================================
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "3. DETALHAMENTO DOS CONTENTORES", border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("helvetica", "B", 9)
    alt = 8
    # Larguras para formato Retrato (Total = 180)
    pdf.cell(10, alt, "Idx", border=1, align="C")
    pdf.cell(20, alt, "Tamanho", border=1, align="C")
    pdf.cell(30, alt, "Tipo", border=1, align="C")
    pdf.cell(40, alt, "Valor CIF (R$)", border=1, align="C")
    pdf.cell(20, alt, "IMO", border=1, align="C")
    pdf.cell(20, alt, "OOG", border=1, align="C")
    pdf.cell(40, alt, "Anuência MAPA/ANV", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 8) 
    for idx, row in df_cnts.iterrows():
        def f_sn(bool_val): return "Sim" if bool_val else "Não"
        cif_f = f"{row['Valor CIF (R$)']:,.2f}"
        
        pdf.cell(10, alt, str(idx+1), border=1, align="C")
        pdf.cell(20, alt, str(row['Tamanho']), border=1, align="C")
        pdf.cell(30, alt, str(row['Tipo']), border=1)
        pdf.cell(40, alt, cif_f, border=1, align="R")
        pdf.cell(20, alt, f_sn(row.get('IMO (Perigosa)', False)), border=1, align="C")
        pdf.cell(20, alt, f_sn(row.get('OOG (Excesso)', False)), border=1, align="C")
        pdf.cell(40, alt, f_sn(row.get('Anuência', False)), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ==========================================
    # 4. RESUMO DE CUSTOS ESTIMADOS
    # ==========================================
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "4. RESUMO DE CUSTOS ESTIMADOS", border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Larguras para formato Retrato (Total = 180)
    pdf.set_font("helvetica", "B", 7)
    pdf.cell(12, 8, "Cód.", border=1, align="C")
    pdf.cell(48, 8, "Serviço / Rubrica", border=1, align="C")
    pdf.cell(21, 8, "V. Base (R$)", border=1, align="C")
    pdf.cell(21, 8, "Adicional (R$)", border=1, align="C")
    pdf.cell(34, 8, "Motivo Adic.", border=1, align="C")
    pdf.cell(21, 8, "Impostos (R$)", border=1, align="C")
    pdf.cell(23, 8, "Total (R$)", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 7)
    for item in itens:
        nome_servico = item['serviço']
        # Corte ajustado para a largura reduzida da coluna
        if len(nome_servico) > 35:
            nome_servico = nome_servico[:32] + "..."
            
        motivo = item['desc_adds']
        if len(motivo) > 23:
            motivo = motivo[:20] + "..."

        pdf.cell(12, 8, str(item['código']), border=1, align="C")
        pdf.cell(48, 8, nome_servico, border=1)
        pdf.cell(21, 8, f"{item['valor_base']:,.2f}", border=1, align="R")
        pdf.cell(21, 8, f"{item['adicionais']:,.2f}", border=1, align="R")
        pdf.cell(34, 8, motivo, border=1, align="C")
        pdf.cell(21, 8, f"{item['impostos']:,.2f}", border=1, align="R")
        pdf.cell(23, 8, f"{item['valor_total']:,.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)

    # ==========================================
    # RESUMO FINANCEIRO
    # ==========================================
    pdf.set_font("helvetica", "B", 11)
    # Empurra os quadros para a direita (180 - 40 - 40 = 100)
    pdf.cell(100, 8, "", align="R") 
    pdf.cell(40, 8, "Subtotal:", border=1, align="R")
    pdf.cell(40, 8, f"R$ {total_sem:,.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(100, 8, "", align="R")
    pdf.cell(40, 8, "Impostos:", border=1, align="R")
    pdf.cell(40, 8, f"R$ {impostos:,.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(100, 8, "", align="R")
    pdf.cell(40, 8, "TOTAL ESTIMADO:", border=1, align="R", fill=False)
    pdf.cell(40, 8, f"R$ {total_com:,.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # ==========================================
    # 5. CONDIÇÕES COMERCIAIS E NOTAS EXPLICATIVAS
    # ==========================================
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "Condições Comerciais e Notas Explicativas:", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 9)
    
    notas = [
        "1. Prazo de Pagamento: À vista (pagamento antecipado à liberação da carga).",
        "2. Validade da Proposta: 15 dias a partir da data de emissão desta simulação.",
        "3. Esta é uma simulação estimativa baseada nas variáveis informadas pelo usuário.",
        "4. Os valores estão sujeitos a alteração caso as características físicas da carga (peso, dimensões, tipo) divirjam do que foi declarado.",
        "5. O período de armazenagem é contabilizado a partir do registro de entrada da carga (Gate In) no terminal."
    ]
    
    for nota in notas:
        pdf.multi_cell(0, 5, nota)
        pdf.ln(1)
    
    return bytes(pdf.output())