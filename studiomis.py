import streamlit as st
import pandas as pd
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="Studio Miss - Gestão", page_icon="✨")

# Estilo para as cores do Studio (Rosa e Preto)
st.markdown("""
    <style>
    .stApp { background-color: #FCE4EC; }
    .stButton>button { background-color: black; color: white; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Banner do Studio
try:
    image = Image.open('banner.png')
    st.image(image, use_container_width=True)
except:
    st.title("STUDIO MISS")

st.subheader("Agenda e Cálculo de Colaboradores")

# Criar ou carregar banco de dados simples (em memória para este exemplo)
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=["Cliente", "Colaborador", "Valor", "Comissão", "Líquido"])

# Formulário de entrada
with st.form("agendamento"):
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("Nome do Cliente")
        valor = st.number_input("Valor do Serviço (R$)", min_value=0.0, step=10.0)
    with col2:
        colab = st.text_input("Nome do Colaborador")
        pct = st.slider("Comissão (%)", 0, 100, 40)
    
    submit = st.form_submit_button("Registrar na Agenda")

if submit:
    comissao = valor * (pct / 100)
    liquido = valor - comissao
    nova_linha = {"Cliente": cliente, "Colaborador": colab, "Valor": valor, "Comissão": comissao, "Líquido": liquido}
    st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova_linha])], ignore_index=True)
    st.success("Registrado com sucesso!")

# Exibição da Tabela
st.write("### Relatório Atual")
st.dataframe(st.session_state.dados, use_container_width=True)

# Botão para baixar a planilha (O que você pediu!)
if not st.session_state.dados.empty:
    csv = st.session_state.dados.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Relatório em Excel (CSV)",
        data=csv,
        file_name='relatorio_studio_miss.csv',
        mime='text/csv',
    )


