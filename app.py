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

# Estilo Rosa Studio Miss
st.markdown("<style>.stApp { background-color: #FCE4EC; } .stButton>button { background-color: black; color: white; border-radius: 20px; }</style>", unsafe_allow_html=True)

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
                    st.success("Conta criada! Mude para 'Login'.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": email_i, "password": senha_i})
                    st.session_state.user = res.user
                    st.rerun()
            except: st.error("Erro no acesso.")
    else:
        st.write(f"Conectado: **{st.session_state.user.email}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

if not st.session_state.user:
    st.warning("Efetue o login para aceder.")
    st.stop()

# --- REGRAS ADMIN ---
LISTA_ADMINS = ["tercio.souza.moreira@gmail.com", "michelle@studiomiss.com"]
st.session_state.is_admin = st.session_state.user.email in LISTA_ADMINS

# --- FUNÇÕES ---
def ler_dados():
    res = supabase.table("agendamentos").select("*").execute()
    return pd.DataFrame(res.data)

# --- INTERFACE ---
tabs = st.tabs(["📅 Agenda", "📝 Registar Serviço", "📊 Relatórios", "⚙️ Admin"])

with tabs[0]: # Agenda
    df = ler_dados()
    if not df.empty:
        evs = [{"title": f"{r['cliente']} ({r['colab']}) - {r['hora']}", "start": r['data_hora']} for _, r in df.iterrows()]
        calendar(events=evs, options={"headerToolbar": {"right": "dayGridMonth,timeGridWeek"}})

with tabs[1]: # Registar
    with st.form("reg"):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome da Cliente")
        colaborador = c2.text_input("Nome do Colaborador")
        
        c3, c4 = st.columns(2)
        data_atend = c3.date_input("Data")
        hora_atend = c4.text_input("Hora (Ex: 14:30)") # Campo de texto para hora
        
        valor_total = st.number_input("Valor do Serviço (€)", min_value=0.0, step=0.50)
        
        if st.form_submit_button("Guardar Registro"):
            # CÁLCULO CONTABILÍSTICO (70% Colaborador)
            comissao = round(valor_total * 0.70, 2)
            liquido = round(valor_total - comissao, 2)
            
            supabase.table("agendamentos").insert({
                "cliente": cliente, "colab": colaborador, "valor": valor_total,
                "comissao": comissao, "liquido": liquido, "data_hora": str(data_atend),
                "hora": hora_atend, "criado_por": st.session_state.user.email
            }).execute()
            st.success(f"Registado! Comissão: {comissao}€ | Caixa: {liquido}€")

with tabs[2]: # Relatórios (Visão do Colaborador)
    df_col = ler_dados()
    if not df_col.empty:
        if not st.session_state.is_admin:
            df_col = df_col[df_col['criado_por'] == st.session_state.user.email]
        
        st.write("### Meus Ganhos")
        st.dataframe(df_col[['data_hora', 'hora', 'cliente', 'valor', 'comissao']], use_container_width=True)
        st.metric("Minha Comissão Total", f"{df_col['comissao'].sum():.2f}€")

with tabs[3]: # Admin (Visão Contabilística)
    if st.session_state.is_admin:
        df_adm = ler_dados()
        if not df_adm.empty:
            st.write("### 👑 Fechamento de Caixa - Contabilidade")
            st.dataframe(df_adm, use_container_width=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Faturação Bruta", f"{df_adm['valor'].sum():.2f}€")
            c2.metric("Total Comissões (70%)", f"{df_adm['comissao'].sum():.2f}€")
            c3.metric("Total Líquido Caixa", f"{df_adm['liquido'].sum():.2f}€")
            
            csv = df_adm.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Planilha para Contabilidade", data=csv, file_name="fechamento_studio_miss.csv", mime="text/csv")
