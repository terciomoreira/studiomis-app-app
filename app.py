import streamlit as st
import pandas as pd
from PIL import Image
from supabase import create_client, Client
from streamlit_calendar import calendar

# --- CONFIGURAÇÃO DO SUPABASE ---
SUPABASE_URL = "https://supabase.co"
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

# --- LOGIN ---
if 'user' not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    try: st.image('banner.png')
    except: st.title("STUDIO MISS")
    
    if not st.session_state.user:
        opcao = st.radio("Acesso", ["Login", "Criar Conta"])
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Confirmar"):
            try:
                if opcao == "Criar Conta":
                    supabase.auth.sign_up({"email": email, "password": senha})
                    st.success("Conta criada! Já pode fazer Login.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    st.session_state.user = res.user
                    st.rerun()
            except: st.error("Erro no acesso.")
    else:
        st.write(f"Conectado: **{st.session_state.user.email}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

if not st.session_state.user:
    st.warning("Aguardando login...")
    st.stop()

# --- DEFINIÇÃO DE GESTOR ---
# Aqui você define o e-mail do seu cliente que será o "Dono"
LISTA_GESTORES = ["tercio.souza.moreira@gmail.com", "cliente_gestor@gmail.com"]
st.session_state.is_admin = st.session_state.user.email in LISTA_GESTORES

# --- FUNÇÕES ---
def salvar_servico(d): supabase.table("agendamentos").insert(d).execute()
def ler_servicos(): 
    res = supabase.table("agendamentos").select("*").execute()
    return pd.DataFrame(res.data)

# --- TABS ---
menu = ["📅 Agenda", "📝 Registar", "📊 Relatórios"]
if st.session_state.is_admin: menu.append("⚙️ Admin")
tabs = st.tabs(menu)

with tabs[0]: # Agenda
    df = ler_servicos()
    if not df.empty:
        evs = [{"title": f"{r['cliente']} ({r['colab']})", "start": r['data_hora']} for _, r in df.iterrows()]
        calendar(events=evs, options={"headerToolbar": {"right": "dayGridMonth,timeGridWeek"}})

with tabs[1]: # Registar
    with st.form("reg"):
        c1, c2 = st.columns(2)
        cli = c1.text_input("Cliente")
        colab = c2.text_input("Colaborador") # Pode ser selectbox no futuro
        val = st.number_input("Valor (€)", min_value=0.0)
        dat = st.date_input("Data")
        if st.form_submit_button("Salvar"):
            com = val * 0.40
            salvar_servico({
                "cliente": cli, "colab": colab, "valor": val, 
                "comissao": com, "liquido": val-com, 
                "data_hora": str(dat), "criado_por": st.session_state.user.email
            })
            st.success("Salvo!")

with tabs[2]: # Relatórios
    df_rel = ler_servicos()
    if not df_rel.empty:
        # Se não for gestor, vê apenas o que ele próprio registou
        if not st.session_state.is_admin:
            df_rel = df_rel[df_rel['criado_por'] == st.session_state.user.email]
        
        st.dataframe(df_rel, use_container_width=True)
        st.metric("Total Faturado", f"{df_rel['valor'].sum():.2f}€")

if st.session_state.is_admin:
    with tabs[3]: # Admin
        st.subheader("Painel de Controle do Gestor")
        st.info("Aqui você pode visualizar a produção de todos os colaboradores.")
        # No futuro, aqui podemos adicionar a gestão de senhas e novos membros
