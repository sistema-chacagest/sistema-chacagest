import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="CHACAGEST", page_icon="🚛", layout="wide")

# Estilos originales
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE DATOS (Optimizadas para velocidad) ---
@st.cache_resource
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        return gspread.authorize(creds).open("Base_Chacagest")
    except: return None

def cargar_todo():
    sh = conectar_google()
    if not sh: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def get_df(name, cols):
        try:
            data = sh.worksheet(name).get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame(columns=cols)
        except: return pd.DataFrame(columns=cols)

    c = get_df("clientes", ["Razón Social", "CUIT / CUIL / DNI *", "Condición IVA"])
    v = get_df("viajes", ["Fecha Carga", "Cliente", "Fecha Viaje", "Importe", "Tipo Comp", "Nro Comp Asoc"])
    p = get_df("proveedores", ["Razón Social", "CUIT / DNI", "Cuenta de Gastos", "Categoría IVA"])
    g = get_df("gastos", ["Fecha", "Proveedor", "Total", "Tipo Factura"])
    
    if not v.empty: v['Importe'] = pd.to_numeric(v['Importe'], errors='coerce').fillna(0)
    if not g.empty: g['Total'] = pd.to_numeric(g['Total'], errors='coerce').fillna(0)
    
    return c, v, p, g

# --- 3. LOGICA DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
    st.stop()

# Carga inicial única
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_todo()
    st.session_state.clientes, st.session_state.viajes = c, v
    st.session_state.proveedores, st.session_state.gastos = p, g

# --- 4. SIDEBAR UNIFICADO (Sin trabas de navegación) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>MENU</h2>", unsafe_allow_html=True)
    
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "VENTAS NC/ND", "CTA CTE CLI", "PROVEEDORES", "CARGA GASTOS", "COMPRAS NC/ND", "CTA CTE PROV", "HISTORIAL"],
        icons=["calendar3", "people", "truck", "file-diff", "person-vcard", "person-badge", "cart-plus", "patch-minus", "journal-text", "archive"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    
    st.markdown("---")
    if st.button("🔄 Sincronizar Datos"):
        st.cache_resource.clear()
        c, v, p, g = cargar_todo()
        st.session_state.clientes, st.session_state.viajes = c, v
        st.session_state.proveedores, st.session_state.gastos = p, g
        st.rerun()

# --- 5. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if not st.session_state.viajes.empty and str(row.get('Fecha Viaje', '-')) != "-":
            eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)
    # Aquí iría el form de alta...

elif sel == "CARGA VIAJE":
    st.header("🚛 Nuevo Viaje")
    with st.form("v_form"):
        c1, c2 = st.columns(2)
        cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = c2.date_input("Fecha")
        imp = c1.number_input("Importe Neto $")
        if st.form_submit_button("GUARDAR"):
            st.success("Viaje Registrado (Simulado)")

elif sel == "CARGA GASTOS":
    st.header("🧾 Carga de Gastos")
    with st.form("g_form"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2 = st.columns(2)
        n21 = c1.number_input("Neto 21%")
        r_iva = c2.number_input("Retenciones")
        total = (n21 * 1.21) + r_iva
        st.subheader(f"Total: $ {total:,.2f}")
        if st.form_submit_button("REGISTRAR"):
            st.success("Gasto Guardado")

elif sel == "CTA CTE CLI":
    st.header("📑 Cta Cte Clientes")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        st.table(res)

elif sel == "CTA CTE PROV":
    st.header("📖 Cta Cte Proveedores")
    if not st.session_state.gastos.empty:
        res_p = st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index()
        st.table(res_p)

elif sel == "HISTORIAL":
    st.header("📂 Historial General")
    tab1, tab2 = st.tabs(["Ventas", "Compras"])
    with tab1: st.dataframe(st.session_state.viajes)
    with tab2: st.dataframe(st.session_state.gastos)
