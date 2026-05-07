import streamlit as st
import pandas as pd
from PIL import Image
from supabase import create_client, Client

# --- CONFIGURAÇÃO DO SUPABASE ---
# A URL deve ser algo como: https://supabase.co
SUPABASE_URL = "https://aqurshrylulujbrxrhvn.supabase.co//"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdXJzaHJ5bHVsdWpicnhyaHZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwOTIzMTEsImV4cCI6MjA5MzY2ODMxMX0.mzy4S9b3H-PUt7nKLoH4k8ipUsXjj5CVWJbB8ZEiPJ0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Studio Miss SaaS", layout="wide")

# Estilo Rosa Studio Miss
st.markdown("""
    <style>
    .stApp { background-color: #FCE4EC; }
    .stButton>button { background-color: black; color: white; border-radius: 20px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE LOGIN ---
if 'user' not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    try:
        st.image('banner.png')
    except:
        st.title("STUDIO MISS")

    if not st.session_state.user:
        tipo = st.radio("Acesso", ["Login", "Cadastro"])
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Confirmar"):
            try:
                if tipo == "Cadastro":
                    supabase.auth.sign_up({"email": email, "password": senha})
                    st.success("Conta criada! Confirme no seu e-mail.")
                else:
                    res = supabase.auth.sign_in_with_password(
                        {"email": email, "password": senha})
                    st.session_state.user = res.user
                    st.rerun()
            except:
                st.error("Erro na autenticação. Verifique os dados.")
    else:
        st.write(f"Utilizador: {st.session_state.user.email}")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

if not st.session_state.user:
    st.warning("Por favor, faça login para aceder ao sistema.")
    st.stop()

# --- FUNÇÕES DE DADOS ---


def salvar_dados(dic):
    supabase.table("agendamentos").insert(dic).execute()


def carregar_dados():
    res = supabase.table("agendamentos").select("*").execute()
    return pd.DataFrame(res.data)


# --- INTERFACE PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📅 Agenda", "📝 Registar Serviço", "📊 Relatórios"])

with tab1:
    st.info("O calendário visual será ativado assim que as bibliotecas estiverem sincronizadas.")
    df_ag = carregar_dados()
    if not df_ag.empty:
        st.write("Próximas marcações:")
        st.table(df_ag[['cliente', 'colab', 'data_hora']].head())

with tab2:
    with st.form("add_servico"):
        c1, c2 = st.columns(2)
        cli = c1.text_input("Nome da Cliente")
        fun = c2.text_input("Colaborador")
        val = st.number_input("Valor (€)", min_value=0.0)
        dat = st.date_input("Data do Serviço")
        if st.form_submit_button("Guardar no Sistema"):
            com = val * 0.40  # Comissão de 40%
            dados_servico = {
                "cliente": cli,
                "colab": fun,
                "valor": val,
                "comissao": com,
                "liquido": val - com,
                "data_hora": str(dat),
                "criado_por": st.session_state.user.email
            }
            salvar_dados(dados_servico)
            st.success("Serviço registado com sucesso!")

with tab3:
    st.subheader("Relatórios de Produção")
    df_rel = carregar_dados()
    if not df_rel.empty:
        # Se for o dono (ex: admin@studiomiss.com), vê tudo. Se não, filtra por ele.
        is_admin = st.session_state.user.email == "emilygisto@gmail.com"

        if not is_admin:
            df_rel = df_rel[df_rel['criado_por']
                            == st.session_state.user.email]

        st.dataframe(df_rel, use_container_width=True)
        st.metric("Total Faturado", f"{df_rel['valor'].sum():.2f}€")
