import streamlit as st
from database import init_db

# Garante que o banco de dados e as tabelas existam logo ao abrir o app
init_db()

# Configuração global da página
st.set_page_config(
    page_title="SEOP - Simulador Portuário",
    page_icon="🚢",
    layout="wide"
)

st.title("🚢 Sistema Eletrônico de Operações Portuárias (SEOP)")
st.write("Bem-vindo ao simulador de preços do terminal de acordo com as normas da ANTAQ.")

st.info("⬅️ Utilize o menu lateral para navegar entre o **Simulador** (área do cliente) e o **Painel Admin** (área restrita).")