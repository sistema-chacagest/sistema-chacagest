import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CHACAGEST", page_icon="🚛", layout="wide")

def conectar_google():
    nombre_planilla = "Base_Chacagest" 
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        return gspread.authorize(creds).open(nombre_planilla)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def cargar_todo():
    sh = conectar_google()
    if not sh: return None
    
    # Función interna para leer cada hoja con seguridad
    def leer(nombre):
        try:
            data = sh.worksheet(nombre).get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()

    return leer("clientes"), leer("viajes"), leer("proveedores"), leer("gastos")

def guardar(nombre_hoja, df):
    sh = conectar_google()
    if sh:
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        df_save = df.fillna("-").astype(str)
        ws.update([df_save.columns.values.tolist()] + df_save.values.tolist())

# --- INICIO DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "chaca2026": 
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- CARGA INICIAL ---
if "df_c" not in st.session_state:
    st.session_state.df_c, st.session_state.df_v, st.session_state.df_p, st.session_state.df_g = cargar_todo()

# --- MENÚ ---
with st.sidebar:
    sel = option_menu("MENÚ", ["VENTAS", "COMPRAS", "CTA CTE", "HISTORIAL"], 
                     icons=["truck", "cart", "cash", "archive"], menu_icon="cast", default_index=0)
    if st.button("🔄 Sincronizar"):
        st.session_state.df_c, st.session_state.df_v, st.session_state.df_p, st.session_state.df_g = cargar_todo()
        st.rerun()

# --- LÓGICA DE MÓDULOS ---

if sel == "VENTAS":
    st.header("Gestión de Ventas / Viajes")
    # Formulario simplificado de Viaje (Tu lógica original)
    with st.form("viaje"):
        cli = st.selectbox("Cliente", st.session_state.df_c["Razón Social"].unique() if not st.session_state.df_c.empty else [""])
        imp = st.number_input("Importe", min_value=0.0)
        if st.form_submit_button("Guardar Viaje"):
            nuevo = pd.DataFrame([[date.today(), cli, date.today(), "-", "-", "-", imp, "Factura", "-"]], columns=st.session_state.df_v.columns)
            st.session_state.df_v = pd.concat([st.session_state.df_v, nuevo], ignore_index=True)
            guardar("viajes", st.session_state.df_v)
            st.success("Viaje Guardado")

elif sel == "COMPRAS":
    st.header("Módulo de Compras")
    m_compras = st.tabs(["Carga Proveedor", "Carga Gasto", "NC/ND Proveedor"])
    
    with m_compras[0]:
        with st.form("p"):
            rz = st.text_input("Razón Social")
            cuit = st.text_input("CUIT")
            cta = st.selectbox("Cuenta", ["Combustible", "Reparación", "Repuesto"])
            iva = st.selectbox("IVA", ["RI", "Monotributo", "Exento"])
            if st.form_submit_button("Guardar Proveedor"):
                np = pd.DataFrame([[rz, cuit, cta, iva]], columns=["Razón Social", "CUIT", "Cuenta de Gastos", "Categoría IVA"])
                st.session_state.df_p = pd.concat([st.session_state.df_p, np], ignore_index=True)
                guardar("proveedores", st.session_state.df_p)
                st.success("Proveedor Creado")

    with m_compras[1]:
        with st.form("g"):
            prov = st.selectbox("Proveedor", st.session_state.df_p["Razón Social"].unique() if not st.session_state.df_p.empty else [""])
            c1, c2 = st.columns(2)
            n21 = c1.number_input("Neto 21%", min_value=0.0)
            n10 = c2.number_input("Neto 10.5%", min_value=0.0)
            ret = st.number_input("Otras Retenciones / Impuestos", min_value=0.0)
            total = (n21 * 1.21) + (n10 * 1.105) + ret
            st.warning(f"Total a pagar: ${total:,.2f}")
            if st.form_submit_button("Cargar Factura"):
                ng = pd.DataFrame([[date.today(), prov, "000", "Factura", total, "Factura", "-"]], columns=st.session_state.df_g.columns)
                st.session_state.df_g = pd.concat([st.session_state.df_g, ng], ignore_index=True)
                guardar("gastos", st.session_state.df_g)
                st.success("Gasto Cargado")

    with m_compras[2]:
        with st.form("nc_p"):
            p_sel = st.selectbox("Proveedor ", st.session_state.df_p["Razón Social"].unique() if not st.session_state.df_p.empty else [""])
            tipo = st.radio("Tipo", ["NC (Descuenta)", "ND (Suma)"])
            monto = st.number_input("Monto", min_value=0.0)
            asoc = st.text_input("Comprobante AFIP Asociado")
            if st.form_submit_button("Registrar Nota"):
                val = -monto if "NC" in tipo else monto
                n_nc = pd.DataFrame([[date.today(), p_sel, "-", "-", val, tipo, asoc]], columns=st.session_state.df_g.columns)
                st.session_state.df_g = pd.concat([st.session_state.df_g, n_nc], ignore_index=True)
                guardar("gastos", st.session_state.df_g)
                st.success("Ajuste de Proveedor guardado")

elif sel == "CTA CTE":
    tipo = st.radio("Ver:", ["Deudores (Clientes)", "Acreedores (Proveedores)"])
    if tipo == "Deudores (Clientes)":
        res = st.session_state.df_v.groupby("Cliente")["Importe"].sum().reset_index()
        st.table(res)
    else:
        res = st.session_state.df_g.groupby("Proveedor")["Total"].sum().reset_index()
        st.table(res)

elif sel == "HISTORIAL":
    t1, t2 = st.tabs(["Ventas", "Compras"])
    with t1:
        st.dataframe(st.session_state.df_v)
    with t2:
        st.dataframe(st.session_state.df_g)
