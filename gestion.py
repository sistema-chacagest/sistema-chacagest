import streamlit as st
import pandas as pd
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

# Constantes de Tesorería
CUENTAS = ["Caja Tato", "Caja Coti", "Banco Galicia", "Banco Provincia", "Banco Supervielle"]

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
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Origen", "Destino", "Detalle", "Monto", "Cliente/Proveedor"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Clientes
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        # Viajes / Cta Cte
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Presupuestos
        try:
            ws_p = sh.worksheet("presupuestos")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except: df_p = pd.DataFrame(columns=col_p)

        # Tesorería
        try:
            ws_t = sh.worksheet("tesoreria")
            df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except: df_t = pd.DataFrame(columns=col_t)
            
        return df_c, df_v, df_p, df_t
    except:
        return None, None, None, None

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
        st.error(f"Error al guardar: {e}")
        return False

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🚛 CHACAGEST")
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
    c, v, p, t = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t

# --- 4. DISEÑO Y SIDEBAR ---
st.markdown("<style>header {visibility: hidden;} h1, h2, h3 {color: #5e2d61 !important;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.header("MENÚ")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERÍA", "CTA CTE INDIVIDUAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "cash-coin", "person-vcard", "file-text"],
        default_index=0
    )
    if st.button("🔄 Sincronizar Todo"):
        st.cache_data.clear()
        st.rerun()

# --- 5. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and "Factura" in str(row['Tipo Comp']):
            eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True})
    calendar(events=eventos, options={"locale": "es"}, key="cal")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli"):
            r = st.text_input("Razón Social"); cuit = st.text_input("CUIT")
            if st.form_submit_button("REGISTRAR"):
                new_c = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, new_c], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.success("Guardado"); st.rerun()
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Comprobantes (Ventas)")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        t_comp = st.selectbox("Tipo de Comprobante", ["Factura (Cuenta Corriente)", "Factura (Contado)", "Nota de Crédito", "Nota de Débito"])
        c1, c2 = st.columns(2); f_v = c1.date_input("Fecha Viaje"); pat = c2.text_input("Móvil")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        asoc = st.text_input("Comp. Asociado (Para Notas de Crédito/Débito)")
        
        if st.form_submit_button("GUARDAR EN CTA CTE"):
            # Lógica AFIP: Nota de Crédito resta del saldo
            valor_final = -imp if t_comp == "Nota de Crédito" else imp
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, valor_final, t_comp, asoc]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

elif sel == "TESORERÍA":
    st.header("💰 Tesorería - Movimientos de Caja")
    
    # Mostrar Saldos
    df_t = st.session_state.tesoreria
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    for i, cta in enumerate(CUENTAS):
        ing = df_t[(df_t['Destino'] == cta)]['Monto'].sum()
        egr = df_t[(df_t['Origen'] == cta)]['Monto'].sum()
        with [sc1, sc2, sc3, sc4, sc5][i]:
            st.metric(cta, f"$ {ing - egr:,.2f}")

    st.divider()
    t_mov = st.selectbox("Tipo", ["Cobranza de Viaje", "Ingreso Vario", "Egreso Vario", "Pase entre Cajas"])
    
    with st.form("f_teso", clear_on_submit=True):
        col1, col2 = st.columns(2)
        f_m = col1.date_input("Fecha", date.today())
        mto = col2.number_input("Monto $", min_value=0.0)
        det = st.text_input("Detalle / Concepto")
        
        orig_m, dest_m, cli_m = "-", "-", "-"
        
        if t_mov == "Cobranza de Viaje":
            cli_m = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            dest_m = st.selectbox("Caja Destino", CUENTAS)
            orig_m = "CLIENTE"
        elif t_mov == "Ingreso Vario":
            dest_m = st.selectbox("Caja Destino", CUENTAS); orig_m = "VARIOS"
        elif t_mov == "Egreso Vario":
            orig_m = st.selectbox("Caja Origen", CUENTAS); dest_m = "GASTO"
        elif t_mov == "Pase entre Cajas":
            orig_m = st.selectbox("Desde", CUENTAS); dest_m = st.selectbox("Hacia", CUENTAS)

        if st.form_submit_button("REGISTRAR"):
            # 1. Guardar en Tesorería
            new_t = pd.DataFrame([[f_m, t_mov, orig_m, dest_m, det, mto, cli_m]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, new_t], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            
            # 2. Si es Cobranza, impactar en Cuenta Corriente (restar deuda)
            if t_mov == "Cobranza de Viaje":
                nv = pd.DataFrame([[date.today(), cli_m, f_m, "COBRANZA", "-", "-", -mto, "Recibo Caja", det]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
            
            st.success("Movimiento Procesado"); st.rerun()

    st.subheader("Últimos Movimientos")
    st.dataframe(st.session_state.tesoreria.sort_index(ascending=False), use_container_width=True)

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
    st.metric("SALDO PENDIENTE", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind)

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Facturación")
    st.dataframe(st.session_state.viajes.sort_index(ascending=False))
