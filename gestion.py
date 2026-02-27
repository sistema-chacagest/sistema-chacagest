import streamlit as st
import pandas as pd
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

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
    # Definición de columnas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        ws_p = sh.worksheet("presupuestos")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
        
        ws_t = sh.worksheet("tesoreria")
        df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
        df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
            
        return df_c, df_v, df_p, df_t
    except:
        return pd.DataFrame(columns=col_c), pd.DataFrame(columns=col_v), pd.DataFrame(columns=col_p), pd.DataFrame(columns=col_t)

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except: return False

# --- 2. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t

# --- 3. SIDEBAR (MENÚ ESTRUCTURADO) ---
with st.sidebar:
    st.title("🚛 CHACAGEST")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA DE VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "INGRESOS VARIOS", "EGRESOS VARIOS", "COBRANZA DE VIAJES", "SALDO DE CAJAS", "SALDO DE BANCOS"],
        icons=["calendar", "people", "truck", "file-text", "person-badge", "globe", "files", "plus-circle", "dash-circle", "cash-coin", "wallet2", "bank"],
        menu_icon="cast", default_index=0,
        styles={"nav-link": {"font-size": "13px", "text-align": "left"}}
    )

# --- 4. LÓGICA DE MÓDULOS ---

# --- VENTAS ---
if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    # (Aquí va tu código de calendario original)
    st.info("Calendario activo sincronizado con viajes.")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    # (Aquí va tu código de clientes original)
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA DE VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_viaje"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "-", imp, "FACTURA", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje cargado en Cuenta Corriente")

# --- TESORERIA ---
elif sel in ["INGRESOS VARIOS", "EGRESOS VARIOS"]:
    st.header(f"💰 {sel}")
    tipo = "INGRESO" if sel == "INGRESOS VARIOS" else "EGRESO"
    with st.form("f_teso_v"):
        cta = st.selectbox("Cuenta / Caja", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"])
        conc = st.text_input("Concepto / Detalle")
        monto = st.number_input("Monto $", min_value=0.0)
        afip = st.text_input("Asociar AFIP (NC/ND)")
        if st.form_submit_button("REGISTRAR"):
            nt = pd.DataFrame([[date.today(), tipo, conc, monto, cta, afip]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            st.success("Movimiento registrado")

elif sel == "COBRANZA DE VIAJES":
    st.header("💸 Cobranza de Viajes (Descuento de Cta Cte)")
    with st.form("f_cobro"):
        cli_pago = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        monto_pago = st.number_input("Monto Cobrado $", min_value=0.0)
        cta_destino = st.selectbox("Ingresa a:", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"])
        ref_afip = st.text_input("Nro Recibo / Comprobante AFIP")
        
        if st.form_submit_button("REGISTRAR COBRO"):
            # 1. Impacto en Tesorería (Entra dinero)
            nt = pd.DataFrame([[date.today(), "INGRESO", f"COBRANZA: {cli_pago}", monto_pago, cta_destino, ref_afip]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            
            # 2. Impacto en Cuenta Corriente (Descuenta del debe)
            # Registramos un viaje con importe NEGATIVO o tipo RECIBO para que reste en la suma
            nv = pd.DataFrame([[date.today(), cli_pago, date.today(), "PAGO", "RECIBO", "-", -monto_pago, "RECIBO", ref_afip]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            
            st.success(f"Cobro registrado. Se descontaron $ {monto_pago} de la cuenta de {cli_pago}")

elif sel == "SALDO DE CAJAS":
    st.header("🗄️ Saldo en Cajas")
    cajas = ["CAJA COTI", "CAJA TATO"]
    for c in cajas:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == c]
        saldo = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(label=c, value=f"$ {saldo:,.2f}")

elif sel == "SALDO DE BANCOS":
    st.header("🏛️ Saldo en Bancos")
    bancos = ["BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    for b in bancos:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == b]
        saldo = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(label=b, value=f"$ {saldo:,.2f}")

# (Mantener el resto de los módulos de CTA CTE igual)
