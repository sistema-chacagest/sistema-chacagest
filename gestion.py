import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="CHACAGEST", page_icon="🚛", layout="wide")

# Estilos originales (Botones naranja y títulos púrpura)
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
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN Y DATOS ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        return gspread.authorize(creds).open("Base_Chacagest")
    except: return None

def cargar_datos():
    sh = conectar_google()
    if not sh: return [pd.DataFrame() for _ in range(4)]
    
    def leer(nombre):
        try: return pd.DataFrame(sh.worksheet(nombre).get_all_records())
        except: return pd.DataFrame()

    c = leer("clientes")
    v = leer("viajes")
    p = leer("proveedores")
    g = leer("gastos")
    return c, v, p, g

# --- 3. INICIALIZACIÓN DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and pw == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
    st.stop()

if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes, st.session_state.viajes = c, v
    st.session_state.proveedores, st.session_state.gastos = p, g

# --- 4. SIDEBAR CON ESTRUCTURA SEPARADA ---
with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>CONTROL DE GESTIÓN</h3>", unsafe_allow_html=True)
    
    # 1. CALENDARIO (Botón principal)
    if st.button("📅 CALENDARIO", use_container_width=True):
        st.session_state.seccion = "CALENDARIO"

    st.markdown("---")
    
    # 2. MÓDULO VENTAS
    with st.expander("💰 VENTAS", expanded=True):
        sel_v = option_menu(
            None, ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE CLI", "HISTORIAL VENTA"],
            icons=["people", "truck", "file-diff", "person-vcard", "archive"],
            default_index=0, key="v_menu",
            styles={"nav-link-selected": {"background-color": "#5e2d61"}}
        )
        # Si se toca este menú, actualizamos la sección
        if st.session_state.get('last_v') != sel_v:
            st.session_state.seccion = sel_v
            st.session_state.last_v = sel_v

    # 3. MÓDULO COMPRAS
    with st.expander("🛒 COMPRAS", expanded=False):
        sel_c = option_menu(
            None, ["PROVEEDORES", "CARGA GASTO", "AJUSTES PROV", "CTA CTE PROV", "HISTORIAL GASTO"],
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "archive-fill"],
            default_index=0, key="c_menu",
            styles={"nav-link-selected": {"background-color": "#d35400"}}
        )
        if st.session_state.get('last_c') != sel_c:
            st.session_state.seccion = sel_c
            st.session_state.last_c = sel_c

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.session_state.clear()
        st.rerun()

# --- 5. LÓGICA DE NAVEGACIÓN ---
seccion = st.session_state.get("seccion", "CALENDARIO")

# --- MÓDULO CALENDARIO ---
if seccion == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    if not st.session_state.viajes.empty:
        for _, row in st.session_state.viajes.iterrows():
            if str(row.get('Fecha Viaje')) != "-":
                eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

# --- MÓDULOS VENTAS ---
elif seccion == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif seccion == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_viaje"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f = st.date_input("Fecha"); imp = st.number_input("Importe Neto")
        if st.form_submit_button("GUARDAR"): st.success("Registrado")

elif seccion == "AJUSTES (NC/ND)":
    st.header("💳 NC/ND de Ventas")
    st.info("Asociado a comprobante AFIP")

elif seccion == "CTA CTE CLI":
    st.header("📑 Cuenta Corriente Clientes")
    if not st.session_state.viajes.empty:
        st.dataframe(st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index())

# --- MÓDULOS COMPRAS ---
elif seccion == "PROVEEDORES":
    st.header("🏢 Registro de Proveedores")
    with st.form("f_prov"):
        rz = st.text_input("Razón Social"); cuit = st.text_input("CUIT/DNI")
        gto = st.selectbox("Cuenta", ["Combustible", "Reparación", "Seguro"])
        iva = st.selectbox("IVA", ["RI", "Monotributo", "Exento"])
        if st.form_submit_button("REGISTRAR PROVEEDOR"): st.success("Guardado")

elif seccion == "CARGA GASTO":
    st.header("🧾 Carga de Gastos")
    with st.form("f_gasto"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        n21 = st.number_input("Neto 21%"); n10 = st.number_input("Neto 10.5%")
        iva21 = n21 * 0.21; iva10 = n10 * 0.105
        total = n21 + iva21 + n10 + iva10
        st.subheader(f"Total Calculado: $ {total:,.2f}")
        if st.form_submit_button("REGISTRAR GASTO"): st.success("Gasto cargado")

elif seccion == "AJUSTES PROV":
    st.header("📉 NC/ND Proveedores")
    st.write("Carga de notas recibidas.")

elif seccion == "CTA CTE PROV":
    st.header("📖 Cta Cte Proveedores")
    if not st.session_state.gastos.empty:
        st.dataframe(st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index())

elif seccion == "HISTORIAL VENTA" or seccion == "HISTORIAL GASTO":
    st.header("📂 Historial de Comprobantes")
    df = st.session_state.viajes if seccion == "HISTORIAL VENTA" else st.session_state.gastos
    st.dataframe(df, use_container_width=True)
