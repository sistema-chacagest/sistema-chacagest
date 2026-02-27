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
    # Estructuras de columnas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_prov = ["Razón Social", "CUIT / DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_gastos = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "IVA 21", "Neto 10.5", "IVA 10.5", "Ret IVA", "Ret Gan", "Ret IIBB", "No Gravados", "Total"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # VENTAS
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # COMPRAS
        try:
            ws_p = sh.worksheet("proveedores")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_prov)
        except: df_p = pd.DataFrame(columns=col_prov)
        try:
            ws_g = sh.worksheet("gastos")
            df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_gastos)
            df_g['Total'] = pd.to_numeric(df_g['Total'], errors='coerce').fillna(0)
        except: df_g = pd.DataFrame(columns=col_gastos)

        return df_c, df_v, df_p, df_g
    except:
        return None, None, None, None

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
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.proveedores = p
    st.session_state.gastos = g

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

# --- 5. SIDEBAR Y NAVEGACIÓN ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    
    # Botón independiente de Calendario
    if st.button("📅 CALENDARIO", use_container_width=True):
        st.session_state.menu_opcion = "CALENDARIO"

    # Acordeón de Ventas
    with st.expander("💰 MODULO VENTAS", expanded=False):
        sel_v = option_menu(
            menu_title=None,
            options=["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
            icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
            default_index=0, key="menu_v",
            styles={"nav-link-selected": {"background-color": "#5e2d61"}}
        )
        if st.session_state.get("menu_opcion") != "CALENDARIO":
            st.session_state.menu_opcion = sel_v

    # Acordeón de Compras
    with st.expander("🛒 MODULO COMPRAS", expanded=False):
        sel_c = option_menu(
            menu_title=None,
            options=["CARGA PROVEEDOR", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV IND", "CTA CTE PROV GEN", "HISTORICO COMPRAS"],
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "diagram-3", "archive"],
            default_index=0, key="menu_c",
            styles={"nav-link-selected": {"background-color": "#d35400"}}
        )
        if st.session_state.get("menu_opcion") not in ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"]:
            st.session_state.menu_opcion = sel_c

    sel = st.session_state.get("menu_opcion", "CALENDARIO")

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.gastos = c, v, p, g
        st.rerun()

# --- 6. MÓDULOS DE VENTAS (TU ESTRUCTURA ORIGINAL) ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"})
    
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, key="cal_final")
    
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
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
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
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", "", "-", val, "NC", nro]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente Cliente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial y Eliminación")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha Viaje']}")
        c2.write(f"👤 **{row['Cliente']}** | **${row['Importe']}**")
        if c3.button("🗑️", key=f"del_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()
        st.divider()

# --- 7. MÓDULOS DE COMPRAS (REQUISITOS SOLICITADOS) ---

elif sel == "CARGA PROVEEDOR":
    st.header("🏢 Carga de Proveedor")
    with st.form("f_prov"):
        c1, c2 = st.columns(2)
        rz = c1.text_input("Razón Social")
        cuit = c2.text_input("CUIT o DNI")
        cuenta = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Otros"])
        cat_iva = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
        if st.form_submit_button("GUARDAR PROVEEDOR"):
            np = pd.DataFrame([[rz, cuit, cuenta, cat_iva]], columns=st.session_state.proveedores.columns)
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
            guardar_datos("proveedores", st.session_state.proveedores); st.success("Proveedor Guardado"); st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("🧾 Carga de Gastos")
    with st.form("f_gasto"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2, c3 = st.columns(3)
        pv = c1.text_input("Punto de Venta"); tf = c2.selectbox("Tipo Factura", ["A", "B", "C", "Remito"])
        n21 = c1.number_input("Neto 21%"); n10 = c2.number_input("Neto 10.5%")
        r_iva = c1.number_input("Retención IVA"); r_gan = c2.number_input("Retención Ganancia"); r_iibb = c3.number_input("Retención IIBB")
        no_gr = st.number_input("Conceptos No Gravados")
        # Cálculos automáticos
        iva21 = n21 * 0.21; iva10 = n10 * 0.105
        total = n21 + iva21 + n10 + iva10 + r_iva + r_gan + r_iibb + no_gr
        st.subheader(f"IMPORTE TOTAL: $ {total:,.2f}")
        if st.form_submit_button("REGISTRAR COMPRA"):
            ng = pd.DataFrame([[date.today(), prov, pv, tf, n21, iva21, n10, iva10, r_iva, r_gan, r_iibb, no_gr, total]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "AJUSTES COMPRAS":
    st.header("📉 Notas de Crédito y Débito (Proveedores)")
    p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
    t = st.radio("Tipo de Ajuste", ["Nota de Crédito", "Nota de Débito"])
    monto = st.number_input("Monto $")
    if st.button("CARGAR AJUSTE COMPRA"):
        v = -monto if "Crédito" in t else monto
        adj = pd.DataFrame([[date.today(), p, "-", t, 0, 0, 0, 0, 0, 0, 0, 0, v]], columns=st.session_state.gastos.columns)
        st.session_state.gastos = pd.concat([st.session_state.gastos, adj], ignore_index=True)
        guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "CTA CTE PROV IND":
    st.header("📖 Cuenta Corriente Proveedor")
    p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.gastos[st.session_state.gastos['Proveedor'] == p]
    st.metric("DEUDA", f"$ {df_p['Total'].sum():,.2f}")
    st.dataframe(df_p)

elif sel == "CTA CTE PROV GEN":
    st.header("📊 Saldo General Proveedores")
    st.table(st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index())

elif sel == "HISTORICO COMPRAS":
    st.header("📂 Historial de Gastos")
    for i in reversed(st.session_state.gastos.index):
        row = st.session_state.gastos.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha']}")
        c2.write(f"🏢 **{row['Proveedor']}** | **Total: ${row['Total']}**")
        if c3.button("🗑️", key=f"del_g_{i}"):
            st.session_state.gastos = st.session_state.gastos.drop(i)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()
        st.divider()
