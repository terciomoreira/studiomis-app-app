import streamlit as st
import pandas as pd
from PIL import Image
from supabase import create_client, Client
from streamlit_calendar import calendar

# --- CONFIGURAÇÃO ---
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdXJzaHJ5bHVsdWpicnhyaHZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwOTIzMTEsImV4cCI6MjA5MzY2ODMxMX0.mzy4S9b3H-PUt7nKLoH4k8ipUsXjj5CVWJbB8ZEiPJ0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Studio Miss SaaS", layout="wide")

# Estilo Rosa
st.markdown("<style>.stApp { background-color: #FCE4EC; } .stButton>button { background-color: black; color: white; border-radius: 20px; }</style>", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- SIDEBAR LOGIN ---
with st.sidebar:
    try: st.image('banner.png')
    except: st.title("STUDIO MISS")
    
    if not st.session_state.user:
        opcao = st.radio("Acesso", ["Login", "Criar Conta"])
        email = st.text_input("E-mail")
        senha = st.text_input("Senha (mín. 6 carateres)", type="password")
        if st.button("Confirmar"):
            try:
                if opcao == "Criar Conta":
                    supabase.auth.sign_up({"email": email, "password": senha})
                    st.success("Conta criada! Mude para 'Login' e entre.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    st.session_state.user = res.user
                    st.rerun()
            except: st.error("E-mail ou senha incorretos.")
    else:
        st.write(f"Olá, **{st.session_state.user.email}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

if not st.session_state.user:
    st.warning("Aguardando login...")
    st.stop()

# --- REGRAS DE GESTOR ---
LISTA_ADMINS = ["tercio.souza.moreira@gmail.com", "cliente_gestor@gmail.com"] # Adiciona aqui o email do teu cliente
st.session_state.is_admin = st.session_state.user.email in LISTA_ADMINS

# --- FUNÇÕES ---
def ler_dados():
    res = supabase.table("agendamentos").select("*").execute()
    return pd.DataFrame(res.data)

# --- INTERFACE ---
titulos = ["📅 Agenda", "📝 Registar", "📊 Relatórios"]
if st.session_state.is_admin: titulos.append("⚙️ Administração")
tabs = st.tabs(titulos)

with tabs[0]: # Agenda
    df = ler_dados()
    if not df.empty:
        evs = [{"title": f"{r['cliente']} ({r['colab']})", "start": r['data_hora']} for _, r in df.iterrows()]
        calendar(events=evs, options={"headerToolbar": {"right": "dayGridMonth,timeGridWeek"}})

with tabs[1]: # Registar
    with st.form("reg"):
        c1, c2 = st.columns(2); cli = c1.text_input("Cliente"); fun = c2.text_input("Colaborador")
        val = st.number_input("Valor (€)", min_value=0.0); dat = st.date_input("Data")
        if st.form_submit_button("Guardar"):
            com = val * 0.40
            supabase.table("agendamentos").insert({
                "cliente": cli, "colab": fun, "valor": val, "comissao": com, 
                "liquido": val-com, "data_hora": str(dat), "criado_por": st.session_state.user.email
            }).execute()
            st.success("Registado!")

with tabs[2]: # Relatórios
    df_rel = ler_dados()
    if not df_rel.empty:
        if not st.session_state.is_admin:
            df_rel = df_rel[df_rel['criado_por'] == st.session_state.user.email]
        st.dataframe(df_rel, use_container_width=True)
        st.metric("Total Faturado", f"{df_rel['valor'].sum():.2f}€")

if st.session_state.is_admin:
    with tabs[3]: # Admin
        st.subheader("Painel do Gestor")
        df_adm = ler_dados()
        st.write("Visão Geral de todos os colaboradores:")
        st.dataframe(df_adm)
        id_del = st.number_input("ID para eliminar", min_value=0)
        if st.button("Eliminar"):
            supabase.table("agendamentos").delete().eq("id", id_del).execute()
            st.rerun()
