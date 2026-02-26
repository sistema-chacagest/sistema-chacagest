import streamlit as st
import pandas as pd
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN ---
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
    # Definición de columnas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_g = ["Fecha Carga", "Proveedor", "Fecha Gasto", "Concepto", "Referencia", "Móvil/Sucursal", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Carga Clientes y Ventas
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Carga Proveedores y Gastos
        ws_p = sh.worksheet("proveedores")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_g = sh.worksheet("gastos")
        df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_g)
        df_g['Importe'] = pd.to_numeric(df_g['Importe'], errors='coerce').fillna(0)
        
        return df_c, df_v, df_p, df_g
    except Exception as e:
        st.warning(f"Aviso: Algunas hojas no se encontraron o están vacías. {e}")
        return pd.DataFrame(columns=col_c), pd.DataFrame(columns=col_v), pd.DataFrame(columns=col_c), pd.DataFrame(columns=col_g)

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
    except Exception as e:
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. ESTADOS Y DATOS ---
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes, st.session_state.viajes = c, v
    st.session_state.proveedores, st.session_state.gastos = p, g

# --- 4. NAVEGACIÓN (Sidebar) ---
with st.sidebar:
    st.title("Menú Principal")
    # Usamos un solo option_menu principal para evitar conflictos
    sel = option_menu(
        menu_title="CHACAGEST",
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "VENTAS: AJUSTES", "VENTAS: CTA CTE", "VENTAS: COMPROBANTES", 
                 "PROVEEDORES", "CARGA COMPRA", "COMPRAS: AJUSTES", "COMPRAS: CTA CTE", "COMPRAS: COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-minus", "person-vcard", "file-text", 
               "shop", "cart-plus", "file-earmark-plus", "person-badge", "receipt"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "5px"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    
    st.markdown("---")
    if st.button("🔄 Sincronizar Todo"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes = c, v
        st.session_state.proveedores, st.session_state.gastos = p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 5. LÓGICA DE MÓDULOS ---

# CALENDARIO (IGUAL AL ORIGINAL)
if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    
    calendar(events=eventos, options={"locale": "es", "height": 600})

# --- MÓDULOS VENTAS ---
elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR CLIENTE"):
                nueva = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "Monotributo", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); pat = st.text_input("Patente"); orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

elif sel == "VENTAS: AJUSTES":
    st.header("💳 Notas de Crédito / Débito (Ventas)")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro = st.text_input("Nro Comprobante AFIP Asociado *")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", "Ajuste Saldo", "-", val, "NC" if val<0 else "ND", nro]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "VENTAS: CTA CTE":
    st.header("📑 Cuenta Corriente Clientes")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "VENTAS: COMPROBANTES":
    st.header("📜 Historial de Ventas")
    for i, row in st.session_state.viajes.iterrows():
        st.write(f"📅 {row['Fecha Viaje']} | **{row['Cliente']}** | ${row['Importe']}")
        if st.button("Eliminar", key=f"del_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

# --- MÓDULOS COMPRAS ---
elif sel == "PROVEEDORES":
    st.header("🏢 Gestión de Proveedores")
    with st.expander("➕ ALTA DE PROVEEDOR"):
        with st.form("f_p", clear_on_submit=True):
            r = st.text_input("Nombre/Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                np = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "Responsable Inscripto", "Cta Cte"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    st.dataframe(st.session_state.proveedores, use_container_width=True)

elif sel == "CARGA COMPRA":
    st.header("🛒 Registro de Gasto")
    with st.form("f_g"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        f_g = st.date_input("Fecha Factura")
        conc = st.text_input("Concepto")
        ref = st.text_input("Nro Factura")
        imp = st.number_input("Importe Total $", min_value=0.0)
        if st.form_submit_button("GUARDAR COMPRA"):
            ng = pd.DataFrame([[date.today(), prov, f_g, conc, ref, "-", imp, "Factura Compra", "-"]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.success("Guardado"); st.rerun()

elif sel == "COMPRAS: AJUSTES":
    st.header("💳 Notas de Crédito / Débito (Proveedores)")
    tipo = st.radio("Acción:", ["Nota de Crédito (Baja Deuda)", "Nota de Débito (Sube Deuda)"], horizontal=True)
    with st.form("f_ncp"):
        pr = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        nro = st.text_input("Factura Asociada *")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), pr, date.today(), "AJUSTE", "Ajuste Saldo", "-", val, "NC Prov", nro]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, nc], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "COMPRAS: CTA CTE":
    st.header("📑 Cuenta Corriente Proveedores")
    pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_ind = st.session_state.gastos[st.session_state.gastos['Proveedor'] == pr]
    st.metric("DEUDA TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "COMPRAS: COMPROBANTES":
    st.header("📜 Historial de Gastos")
    for i, row in st.session_state.gastos.iterrows():
        st.write(f"📅 {row['Fecha Gasto']} | **{row['Proveedor']}** | {row['Concepto']} | ${row['Importe']}")
        if st.button("Eliminar", key=f"del_g_{i}"):
            st.session_state.gastos = st.session_state.gastos.drop(i)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()
