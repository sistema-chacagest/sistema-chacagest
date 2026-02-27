import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
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
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    # NUEVA COLUMNA TESORERIA
    col_t = ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)

        # CARGA DE TESORERIA
        try:
            ws_t = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)
            
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

# --- (Las funciones de HTML se mantienen igual...) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html>...{tabla_html}...</html>" # Simplificado para brevedad

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
if 'clientes' not in st.session_state or 'tesoreria' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t

# --- 4. DISEÑO ---
st.markdown("""<style>
    [data-testid="stSidebarNav"] { display: none; }
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; }
    </style>""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERIA", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "cash-stack", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v, p, t = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
        st.rerun()

# --- 6. MÓDULOS ---

# [Tus módulos CALENDARIO, CLIENTES, CARGA VIAJE, PRESUPUESTOS se mantienen idénticos]

if sel == "TESORERIA":
    st.header("💰 Gestión de Tesorería")
    
    cuentas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    df_t = st.session_state.tesoreria

    # Dashboard de saldos
    cols = st.columns(5)
    for i, cta in enumerate(cuentas):
        ing = df_t[(df_t['Cuenta'] == cta) & (df_t['Tipo'] == 'INGRESO')]['Monto'].sum()
        egr = df_t[(df_t['Cuenta'] == cta) & (df_t['Tipo'] == 'EGRESO')]['Monto'].sum()
        cols[i].metric(cta, f"$ {ing - egr:,.2f}")

    st.divider()

    t_registro, t_historial = st.tabs(["📝 Registrar Movimiento", "📜 Historial de Movimientos"])

    with t_registro:
        with st.form("form_teso", clear_on_submit=True):
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo", ["INGRESO", "EGRESO"])
            cta_destino = c2.selectbox("Cuenta / Caja", cuentas)
            
            concep = st.selectbox("Concepto", ["COBRANZA DE VIAJE", "INGRESOS VARIOS", "EGRESOS VARIOS", "NOTA DE CRÉDITO", "NOTA DE DÉBITO"])
            monto_t = st.number_input("Importe $", min_value=0.0)
            
            # Recordatorio Nota de Crédito/Débito AFIP
            asoc_afip = st.text_input("Comprobante AFIP (Requerido para NC/ND)")
            
            if st.form_submit_button("GUARDAR MOVIMIENTO"):
                nueva_fila = pd.DataFrame([[date.today(), tipo, concep, monto_t, cta_destino, asoc_afip]], columns=df_t.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nueva_fila], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                st.success("Movimiento registrado con éxito")
                st.rerun()

    with t_historial:
        if not df_t.empty:
            st.dataframe(df_t.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("No hay movimientos en el historial.")

# [El resto de tus módulos CTA CTE y COMPROBANTES se mantienen iguales]
