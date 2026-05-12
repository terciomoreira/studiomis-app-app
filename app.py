import streamlit as st
import pandas as pd
from PIL import Image
from supabase import create_client, Client
from streamlit_calendar import calendar

# --- CONFIGURAÇÃO ---
SUPABASE_URL = "https://aqurshrylulujbrxrhvn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdXJzaHJ5bHVsdWpicnhyaHZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwOTIzMTEsImV4cCI6MjA5MzY2ODMxMX0.mzy4S9b3H-PUt7nKLoH4k8ipUsXjj5CVWJbB8ZEiPJ0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Studio Miss SaaS", layout="wide")

# Estilo SaaS
st.markdown("<style>.stApp { background-color: #FCE4EC; } .stButton>button { background-color: black; color: white; border-radius: 20px; }</style>", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN ---
with st.sidebar:
    try: st.image('banner.png')
    except: st.title("STUDIO MISS")
    if not st.session_state.user:
        opcao = st.radio("Acesso", ["Login", "Criar Conta"])
        em, se = st.text_input("E-mail"), st.text_input("Senha", type="password")
        if st.button("Confirmar"):
            try:
                if opcao == "Criar Conta":
                    supabase.auth.sign_up({"email": em, "password": se})
                    st.success("Conta criada! Mude para 'Login'.")
                else:
                    res = supabase.auth.sign_in_with_password({"email": em, "password": se})
                    if res.user: st.session_state.user = res.user; st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
    else:
        st.write(f"Conectado: **{st.session_state.user.email}**")
        if st.button("Sair"): st.session_state.user = None; st.rerun()

if not st.session_state.user: st.warning("Efetue o login."); st.stop()

# --- REGRAS ADMIN ---
LISTA_ADMINS = ["tercio.souza.moreira@gmail.com", "michelle@studiomiss.com"]
st.session_state.is_admin = st.session_state.user.email in LISTA_ADMINS

# --- FUNÇÕES ---
def ler_dados():
    try:
        res = supabase.table("agendamentos").select("*").execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def buscar_cores():
    try:
        res = supabase.table("configuracoes_cores").select("*").execute()
        return {item['colab']: f"background-color: {item['cor_hex']}" for item in res.data}
    except: return {}

def aplicar_estilo_dinamico(row):
    mapa = buscar_cores()
    return [mapa.get(row['colab'], '')] * len(row)

# --- INTERFACE ---
titulos = ["📅 Agenda", "📝 Registar", "📊 Relatórios", "👤 Perfil"]
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
        cli, fun = c1.text_input("Cliente"), c2.text_input("Colaborador")
        dat, hor = st.date_input("Data"), st.text_input("Hora (Ex: 14:30)")
        val = st.number_input("Valor (€)", min_value=0.0)
        if st.form_submit_button("Guardar"):
            com = round(val * 0.70, 2)
            supabase.table("agendamentos").insert({
                "cliente": cli, "colab": fun, "valor": val, "comissao": com,
                "liquido": val-com, "data_hora": str(dat), "hora": hor,
                "criado_por": st.session_state.user.email
            }).execute()
            st.success("Registado!")

with tabs[2]: # Relatórios
    df_rel = ler_dados()
    if not df_rel.empty:
        if not st.session_state.is_admin:
            df_rel = df_rel[df_rel['criado_por'] == st.session_state.user.email]
        st.dataframe(df_rel.style.apply(aplicar_estilo_dinamico, axis=1), use_container_width=True)

with tabs[3]: # Perfil
    st.subheader("Configurações")
    nova_senha = st.text_input("Nova Senha", type="password")
    if st.button("Atualizar Senha"):
        supabase.auth.update_user({"password": nova_senha}); st.success("Atualizado!")

if st.session_state.is_admin:
    with tabs[4]: # Admin
        st.subheader("👑 Painel de Gestão Master")
        
        with st.expander("🎨 Gestão da Tabela de Cores"):
            nome_c = st.text_input("Nome da Colaboradora (Exato)")
            
            st.write("Cores Sugeridas (Clique num quadrado para selecionar):")
            # PALETA DE CORES RÁPIDA
            paleta = ["#F8BBD0", "#B3E5FC", "#C8E6C9", "#FFF9C4", "#D1C4E9", "#FFCCBC", "#E0E0E0"]
            col_cores = st.columns(len(paleta))
            
            # Escolha manual ou rápida
            if 'cor_temp' not in st.session_state: st.session_state.cor_temp = "#F8BBD0"
            
            for i, cor_hex in enumerate(paleta):
                if col_cores[i].button(" ", key=f"btn_{i}", help=cor_hex):
                    st.session_state.cor_temp = cor_hex
            
            cor_final = st.color_picker("Cor Selecionada (Pode ajustar aqui)", st.session_state.cor_temp)
            
            if st.button("Gravar Cor na Tabela"):
                if nome_c:
                    supabase.table("configuracoes_cores").upsert({"colab": nome_c, "cor_hex": cor_final}).execute()
                    st.success(f"Cor de {nome_c} definida!")
                    st.rerun()
                else: st.error("Insira o nome!")

        df_adm = ler_dados()
        if not df_adm.empty:
            st.dataframe(df_adm.style.apply(aplicar_estilo_dinamico, axis=1), use_container_width=True)
            id_del = st.number_input("ID para eliminar", min_value=0, step=1)
            if st.button("Eliminar"):
                supabase.table("agendamentos").delete().eq("id", id_del).execute(); st.rerun()

