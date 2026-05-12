import streamlit as st
import pandas as pd
from PIL import Image
from supabase import create_client, Client
from streamlit_calendar import calendar

# --- CONFIGURAÇÃO ---
SUPABASE_URL = "https://aqurshrylulujbrxrhvn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdXJzaHJ5bHVsdWpicnhyaHZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwOTIzMTEsImV4cCI6MjA5MzY2ODMxMX0.mzy4S9b3H-PUt7nKLoH4k8ipUsXjj5CVWJbB8ZEiPJ0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Studio Miss SaaS", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO E CORES SaaS ---
st.markdown("""
    <style>
    .stApp { background-color: #FCE4EC; }
    .stButton>button { background-color: black; color: white; border-radius: 20px; width: 100%; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- SIDEBAR LOGIN ---
with st.sidebar:
    try: st.image('banner.png')
    except: st.title("STUDIO MISS")
    
    if not st.session_state.user:
        opcao = st.radio("Acesso", ["Login", "Criar Conta"])
        email_i = st.text_input("E-mail")
        senha_i = st.text_input("Senha", type="password")
        if st.button("Confirmar"):
            try:
                if opcao == "Criar Conta":
                    supabase.auth.sign_up({"email": email_i, "password": senha_i})
                    st.success("Conta criada! Já pode entrar.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email_i, "password": senha_i})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
    else:
        st.write(f"Olá, **{st.session_state.user.email}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

if not st.session_state.user:
    st.warning("Por favor, faça login para continuar.")
    st.stop()

# --- REGRAS ADMIN ---
LISTA_ADMINS = ["tercio.souza.moreira@gmail.com", "michelle@studiomiss.com"]
st.session_state.is_admin = st.session_state.user.email in LISTA_ADMINS

# --- FUNÇÕES ---
def ler_dados():
    try:
        res = supabase.table("agendamentos").select("*").execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

# Função para colorir a tabela por colaborador (Estilo SaaS)
def colorir_colaborador(row):
    # Pode adicionar quantos colaboradores e cores quiser aqui
    cores = {
        'Michelle': 'background-color: #F8BBD0', # Rosa
        'Ana': 'background-color: #B3E5FC',      # Azul Claro
        'Beatriz': 'background-color: #C8E6C9',   # Verde Claro
        'Carla': 'background-color: #FFF9C4'     # Amarelo Claro
    }
    return [cores.get(row['colab'], '')] * len(row)

# --- INTERFACE ---
titulos = ["📅 Agenda", "📝 Registar Serviço", "📊 Relatórios", "👤 Perfil"]
if st.session_state.is_admin: titulos.append("⚙️ Admin")
tabs = st.tabs(titulos)

with tabs[0]: # Agenda
    df = ler_dados()
    if not df.empty:
        evs = [{"title": f"{r['cliente']} ({r['colab']})", "start": r['data_hora']} for _, r in df.iterrows()]
        calendar(events=evs, options={"headerToolbar": {"right": "dayGridMonth,timeGridWeek"}})

with tabs[1]: # Registar
    with st.form("reg"):
        c1, c2 = st.columns(2)
        cli = c1.text_input("Cliente")
        colab = c2.text_input("Colaborador (Nome Exato)")
        c3, c4 = st.columns(2)
        dat = c3.date_input("Data")
        hor = c4.text_input("Hora (Ex: 15:30)")
        val = st.number_input("Valor (€)", min_value=0.0)
        if st.form_submit_button("Guardar"):
            com = round(val * 0.70, 2)
            supabase.table("agendamentos").insert({
                "cliente": cli, "colab": colab, "valor": val, "comissao": com,
                "liquido": val-com, "data_hora": str(dat), "hora": hor,
                "criado_por": st.session_state.user.email
            }).execute()
            st.success("Registado com sucesso!")

with tabs[2]: # Relatórios Colaborador
    df_rel = ler_dados()
    if not df_rel.empty:
        if not st.session_state.is_admin:
            df_rel = df_rel[df_rel['criado_por'] == st.session_state.user.email]
        st.dataframe(df_rel.style.apply(colorir_colaborador, axis=1), use_container_width=True)
        st.metric("Minha Comissão Total", f"{df_rel['comissao'].sum():.2f}€")

with tabs[3]: # Perfil (Gestão de Usuário)
    st.subheader("👤 Minhas Configurações")
    st.info("Aqui pode alterar a sua senha de acesso.")
    nova_senha = st.text_input("Nova Senha", type="password")
    if st.button("Atualizar Senha"):
        try:
            supabase.auth.update_user({"password": nova_senha})
            st.success("Senha alterada com sucesso!")
        except Exception as e: st.error(f"Erro: {e}")

if st.session_state.is_admin:
    with tabs[4]: # Admin
        st.subheader("👑 Painel de Gestão Master")
        df_adm = ler_dados()
        if not df_adm.empty:
            st.write("### Produção Detalhada por Cor")
            # Tabela Admin Colorida
            st.dataframe(df_adm.style.apply(colorir_colaborador, axis=1), use_container_width=True)
            
            st.metric("Total Líquido em Caixa", f"{df_adm['liquido'].sum():.2f}€")
            
            # Ferramenta de Eliminação
            st.divider()
            id_del = st.number_input("ID para eliminar", min_value=0, step=1)
            if st.button("Eliminar Permanentemente"):
                supabase.table("agendamentos").delete().eq("id", id_del).execute()
                st.rerun()
