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
    col_prov = ["Razón Social", "CUIT / DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_gastos = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "IVA 21", "Neto 10.5", "IVA 10.5", "Ret IVA", "Ret Gan", "Ret IIBB", "No Gravados", "Total"]
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        ws_c = sh.worksheet("clientes"); datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        ws_v = sh.worksheet("viajes"); datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        try:
            ws_p = sh.worksheet("proveedores"); df_p = pd.DataFrame(ws_p.get_all_records())
        except: df_p = pd.DataFrame(columns=col_prov)
        try:
            ws_g = sh.worksheet("gastos"); df_g = pd.DataFrame(ws_g.get_all_records())
            df_g['Total'] = pd.to_numeric(df_g['Total'], errors='coerce').fillna(0)
        except: df_g = pd.DataFrame(columns=col_gastos)
        return df_c, df_v, df_p, df_g
    except: return None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        try: ws = sh.worksheet(nombre_hoja)
        except: ws = sh.add_worksheet(title=nombre_hoja, rows="100", cols="20")
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except: return False

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

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
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.proveedores = p if p is not None else pd.DataFrame()
    st.session_state.gastos = g if g is not None else pd.DataFrame()

# --- 4. DISEÑO ORIGINAL ---
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
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR (ESTRUCTURA SOLICITADA) ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    
    # Manejo de navegación
    if 'menu_sel' not in st.session_state:
        st.session_state.menu_sel = "CALENDARIO"

    # 1. Calendario Independiente
    if st.button("📅 CALENDARIO", use_container_width=True):
        st.session_state.menu_sel = "CALENDARIO"

    # 2. Acordeón VENTA
    with st.expander("💰 VENTA", expanded=(st.session_state.menu_sel in ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"])):
        sel_v = option_menu(
            menu_title=None,
            options=["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
            icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#5e2d61"}},
            key="v_menu"
        )
        if st.session_state.menu_sel != "CALENDARIO":
            st.session_state.menu_sel = sel_v

    # 3. Acordeón COMPRAS
    with st.expander("🛒 COMPRAS", expanded=(st.session_state.menu_sel in ["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV IND", "CTA CTE PROV GEN", "HISTORICO GASTOS"])):
        sel_c = option_menu(
            menu_title=None,
            options=["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV IND", "CTA CTE PROV GEN", "HISTORICO GASTOS"],
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "diagram-3", "archive"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#5e2d61"}},
            key="c_menu"
        )
        if st.session_state.menu_sel not in ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"]:
            st.session_state.menu_sel = sel_c

    sel = st.session_state.menu_sel
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.gastos = c, v, p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"})
    
    res_cal = calendar(events=eventos, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es", "height": 600}, key="cal_final")
    
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])

    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar Información"):
                st.session_state.viaje_ver = None
                st.rerun()
            st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-left: 5px solid #f39c12; border-radius: 5px;">
                <h4 style="color: #5e2d61;">Detalles del Viaje</h4>
                <p><b>Cliente:</b> {v_det['Cliente']}<br><b>Ruta:</b> {v_det['Origen']} ➔ {v_det['Destino']}<br><b>Importe:</b> $ {v_det['Importe']}</p>
            </div>""", unsafe_allow_html=True)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli"):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT / CUIL / DNI *")
            iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            if st.form_submit_button("REGISTRAR"):
                nf = pd.DataFrame([[r, cuit, "", "", "", "", "", iva, "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, "", "", "", imp, "Factura (CC)", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Guardado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (Ventas)")
    st.info("Asociar ajuste a comprobante AFIP.")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        nro = st.text_input("Nro Comprobante Asociado"); monto = st.number_input("Monto $")
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", "", "-", val, "NC" if "Crédito" in tipo else "ND", nro]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente Cliente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Ventas")
    st.dataframe(st.session_state.viajes, use_container_width=True)

# --- MÓDULOS COMPRAS ---

elif sel == "PROVEEDORES":
    st.header("🏢 Carga de Proveedores")
    with st.form("f_prov"):
        c1, c2 = st.columns(2)
        rz = c1.text_input("Razón Social *"); doc = c2.text_input("CUIT o DNI *")
        gto = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Otros"])
        iva_p = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
        if st.form_submit_button("GUARDAR"):
            np = pd.DataFrame([[rz, doc, gto, iva_p]], columns=["Razón Social", "CUIT / DNI", "Cuenta de Gastos", "Categoría IVA"])
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
            guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("🧾 Carga de Gastos")
    with st.form("f_gasto"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2, c3 = st.columns(3)
        tfac = c2.selectbox("Tipo", ["A", "B", "C", "Remito"])
        n21 = c1.number_input("Neto 21%"); n10 = c2.number_input("Neto 10.5%")
        r_iva = c3.number_input("Ret. IVA"); no_g = c1.number_input("No Gravados")
        total = (n21*1.21) + (n10*1.105) + r_iva + no_g
        st.subheader(f"Total: $ {total:,.2f}")
        if st.form_submit_button("REGISTRAR COMPRA"):
            ng = pd.DataFrame([[date.today(), prov, "", tfac, n21, n21*0.21, n10, n10*0.105, r_iva, 0, 0, no_g, total]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "AJUSTES COMPRAS":
    st.header("📉 NC/ND Proveedores")
    with st.form("f_adj_p"):
        p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        t = st.radio("Tipo", ["Nota de Crédito", "Nota de Débito"])
        monto = st.number_input("Monto")
        if st.form_submit_button("CARGAR"):
            v = -monto if "Crédito" in t else monto
            adj = pd.DataFrame([[date.today(), p, "", t, 0, 0, 0, 0, 0, 0, 0, 0, v]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, adj], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "CTA CTE PROV IND":
    st.header("📖 Cta Cte Proveedor")
    p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.gastos[st.session_state.gastos['Proveedor'] == p]
    st.metric("DEUDA", f"$ {df_p['Total'].sum():,.2f}")
    st.dataframe(df_p)

elif sel == "CTA CTE PROV GEN":
    st.header("📊 Saldo General Proveedores")
    st.table(st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index())

elif sel == "HISTORICO GASTOS":
    st.header("📂 Histórico Compras")
    st.dataframe(st.session_state.gastos)
