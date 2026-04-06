# Adicione este import no topo do database.py
import contextlib
import sqlite3
import os

DB_NAME = "seop.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ADICIONE ESTA NOVA FUNÇÃO
@contextlib.contextmanager
def get_db_connection():
    """Gerenciador de contexto para garantir fechamento seguro da conexão."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Cria as tabelas do banco de dados caso elas não existam."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Configurações do Terminal (Norma VIII: a, g)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes_terminal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        razao_social TEXT NOT NULL,
        cnpj TEXT NOT NULL,
        condicoes_cobranca TEXT,
        prazo_pagamento TEXT,
        imposto_percentual REAL DEFAULT 0.0
    )
    """)

    # 2. Operações (Ex: Importação, Exportação)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        ativo BOOLEAN DEFAULT 1
    )
    """)

    # 3. Modalidades (Ex: DI, DUIMP, DSA)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS modalidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        ativo BOOLEAN DEFAULT 1
    )
    """)

    # 4. Serviços (Tarifas Base)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_rubrica TEXT NOT NULL UNIQUE,
        nome TEXT NOT NULL,
        norma_aplicacao TEXT,  -- ✨ NOVA COLUNA ADICIONADA AQUI
        tipo_cobranca TEXT NOT NULL,
        valor_base REAL NOT NULL,
        regras_calculo TEXT,
        gatilho_tipo TEXT DEFAULT 'Nenhum',
        gatilho_carac TEXT DEFAULT 'Nenhuma',
        ativo BOOLEAN DEFAULT 1
    )
    """)

    # 5. Tabela de Relacionamento (Operação x Modalidade x Serviço)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS op_mod_servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operacao_id INTEGER NOT NULL,
        modalidade_id INTEGER NOT NULL,
        servico_id INTEGER NOT NULL,
        is_obrigatorio BOOLEAN DEFAULT 0,
        FOREIGN KEY (operacao_id) REFERENCES operacoes(id),
        FOREIGN KEY (modalidade_id) REFERENCES modalidades(id),
        FOREIGN KEY (servico_id) REFERENCES servicos(id),
        UNIQUE(operacao_id, modalidade_id, servico_id)
    )
    """)

    # 6. Tipos de Contêiner (Para a Tab 5 do Admin)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipos_conteiner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        is_oog BOOLEAN DEFAULT 0,
        ativo BOOLEAN DEFAULT 1
    )
    """)

    # 7. Simulações (ATUALIZADO DEFINITIVAMENTE)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_simulacao TEXT,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        nome TEXT,
        empresa TEXT,
        email TEXT,
        telefone TEXT,
        operacao TEXT,
        modalidade TEXT,
        qtd_conteineres INTEGER,
        valor_cif REAL,
        valor_total REAL,
        detalhes_conteineres TEXT,
        pdf_arquivo BLOB
    )
    """)

    # 8. Itens da Simulação (Norma VIII: d - Rubricas itemizadas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulacao_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulacao_id INTEGER NOT NULL,
        servico_codigo TEXT NOT NULL, 
        servico_nome TEXT NOT NULL,
        quantidade REAL NOT NULL,
        valor_unitario REAL NOT NULL,
        valor_total_item REAL NOT NULL,
        FOREIGN KEY (simulacao_id) REFERENCES simulacoes(id) ON DELETE CASCADE
    )
    """)

    # 9. Adicionais de Carga (IMO, Anuência, etc)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adicionais_carga (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        caracteristica TEXT NOT NULL, 
        tipo_calculo TEXT NOT NULL, 
        valor REAL NOT NULL,
        servico_base_id INTEGER, 
        dias_periodo INTEGER DEFAULT 7,
        ativo BOOLEAN DEFAULT 1,
        FOREIGN KEY(servico_base_id) REFERENCES servicos(id)
    )
    """)

    # Inserir dados padrão do Terminal se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM configuracoes_terminal")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO configuracoes_terminal (razao_social, cnpj, condicoes_cobranca, prazo_pagamento, imposto_percentual)
        VALUES ('Terminal Portuário Exemplo S/A', '00.000.000/0001-00', 'Pagamento Faturado', '15 dias após emissão da NF', 14.25)
        """)

    conn.commit()
    conn.close()
    print("Banco de dados 'seop.db' inicializado com sucesso!")

# Se você rodar este arquivo diretamente, ele cria o banco
if __name__ == "__main__":
    init_db()