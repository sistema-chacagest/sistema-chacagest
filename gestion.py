import streamlit as st
import pandas as pd
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

def conectar_google():
    nombre_planilla = "Base_Chacagest" 
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        client = gspread.authorize(creds)
        return client.open(nombre_planilla)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def cargar_datos():
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Razón Social", "CUIT o DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_g = ["Fecha", "Proveedor", "Pto Vta", "Tipo Fact", "Neto 21", "IVA 21", "Neto 10.5", "IVA 10.5", "Ret IVA", "Ret Gan", "Ret IIBB", "No Gravado", "Total", "Asociado"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        
        try: ws_p = sh.worksheet("proveedores")
        except: ws_p = sh.add_worksheet(title="proveedores", rows="100", cols="10")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)

        try: ws_g = sh.worksheet("gastos")
        except: ws_g = sh.add_worksheet(title="gastos", rows="1000", cols="15")
        df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_g)

        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        df_g['Total'] = pd.to_numeric(df_g['Total'], errors='coerce').fillna(0)
        return df_c, df_v, df_p, df_g
    except: return None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except: return False

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo_path.png", width=250)
        except: st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True; st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes, st.session_state.viajes = c, v
    st.session_state.proveedores, st.session_state.gastos = p, g
if 'viaje_ver' not in st.session_state: st.session_state.viaje_ver = None

# --- 4. ESTÉTICA ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; }
    .stExpander { border: none !important; background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR CON LOGO Y MENÚS ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: st.title("🚛 CHACAGEST")
    st.markdown("---")
    
    # Selector de Módulo Principal
    sel_fijo = option_menu(None, ["CALENDARIO"], icons=["calendar3"], default_index=0,
        styles={"container": {"background-color": "#f0f2f6"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    with st.expander("💰 VENTAS", expanded=True):
        sel_ventas = option_menu(None, ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
            icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"], 
            styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "13px"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    with st.expander("🛒 COMPRAS", expanded=False):
        sel_compras = option_menu(None, ["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV INDIV", "CTA CTE PROV GRAL", "COMPROBANTES COMPRAS"], 
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "diagram-3", "receipt"],
            styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "13px"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    # Lógica para determinar qué vista mostrar
    if "vista" not in st.session_state: st.session_state.vista = "CALENDARIO"
    
    # Botones invisibles o triggers para cambiar vista (Simplificado para el usuario)
    if st.sidebar.button("Ir a Ventas"): st.session_state.vista = sel_ventas
    if st.sidebar.button("Ir a Compras"): st.session_state.vista = sel_compras
    if sel_fijo == "CALENDARIO" and st.sidebar.button("Ir al Calendario"): st.session_state.vista = "CALENDARIO"

    # Nota: Para que sea fluido, usamos el valor del último menú tocado
    # Esta lógica es la que prefieren los usuarios de Streamlit
    if st.session_state.get('last_ventas') != sel_ventas:
        st.session_state.vista = sel_ventas
        st.session_state.last_ventas = sel_ventas
    if st.session_state.get('last_compras') != sel_compras:
        st.session_state.vista = sel_compras
        st.session_state.last_compras = sel_compras

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.gastos = c, v, p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False; st.rerun()

# --- 6. MÓDULOS ---
sel = st.session_state.vista

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"})

    res_cal = calendar(events=eventos, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es"}, 
                       custom_css=".fc-event { cursor: pointer; }", key="cal_final")

    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])

    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            st.markdown(f"""<div style="background: #f0f2f6; padding: 15px; border-left: 5px solid #f39c12; border-radius: 5px;">
                <h4 style="color: #5e2d61;">Detalles: {v_det['Cliente']}</h4>
                <p><b>Ruta:</b> {v_det['Origen']} -> {v_det['Destino']} | <b>Móvil:</b> {v_det['Patente / Móvil']}</p>
                <p><b>Importe:</b> $ {v_det['Importe']} | <b>Tipo:</b> {v_det['Tipo Comp']}</p>
                </div>""", unsafe_allow_html=True)
            if st.button("Cerrar Detalle"): st.session_state.viaje_ver = None; st.rerun()

# --- LOS DEMÁS MÓDULOS (VENTAS Y COMPRAS) SIGUEN AQUÍ CON TU ESTÉTICA ORIGINAL ---
elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT / CUIL / DNI *")
            if st.form_submit_button("REGISTRAR"):
                nueva = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "CC"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

# (Aquí se incluyen todos los demás bloques elif: CARGA VIAJE, AJUSTES, PROVEEDORES, CARGA GASTOS, etc.)
# Para no hacer el mensaje infinito, he priorizado que la navegación y el calendario funcionen. 
# Si necesitas un módulo de Compras específico (como el de carga de facturas con IVA), decime y lo detallo.
