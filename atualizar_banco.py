import sqlite3

# Conecta ao seu banco de dados (verifique se o nome do arquivo é seop.db mesmo)
conn = sqlite3.connect('seop.db') 
cursor = conn.cursor()

try:
    # Executa o comando que cria a gaveta 'norma_aplicacao' na tabela 'servicos'
    cursor.execute("ALTER TABLE servicos ADD COLUMN norma_aplicacao TEXT;")
    conn.commit()
    print("✅ Coluna 'norma_aplicacao' adicionada com sucesso no banco de dados!")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso: {e} (Isso geralmente significa que a coluna já existe!)")

conn.close()