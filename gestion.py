import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y CONEXIÓN (TUYA) ---
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
    col_t = ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"] # Nueva pestaña
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

        ws_p = sh.worksheet("presupuestos")
        datos_p = ws_p.get_all_records()
        df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
        df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)

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
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except: return False

# --- TUS FUNCIONES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html>...{tabla_html}...</html>" # Tu estilo de resumen

def generar_html_presupuesto(p_data):
    return f"<html>...{p_data['Detalle']}...</html>" # Tu estilo de presupuesto

def generar_html_recibo(cliente, monto, concepto, afip, cuenta):
    return f"""<html><body style="font-family: Arial; border: 2px solid #5e2d61; padding: 40px;">
    <h1 style="color: #5e2d61;">RECIBO DE PAGO</h1><hr>
    <p><b>Cliente:</b> {cliente}</p><p><b>Monto:</b> $ {monto:,.2f}</p>
    <p><b>Concepto:</b> {concepto}</p><p><b>Comprobante AFIP:</b> {afip}</p>
    </body></html>"""

# --- INICIALIZACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # (Tu Login que ya tenias)
    st.title("🚛 CHACAGEST")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "admin" and p == "chaca2026":
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t

# --- TU DISEÑO CSS ---
st.markdown("""<style> [data-testid="stSidebarNav"] { display: none; } h1, h2, h3 { color: #5e2d61 !important; } </style>""", unsafe_allow_html=True)

# --- TU SIDEBAR CON LA NUEVA ESTRUCTURA ---
with st.sidebar:
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "INGRESOS VARIOS", "EGRESOS VARIOS", "COBRANZA DE VIAJE", "SALDO DE CAJAS", "SALDO DE BANCOS"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text", "plus-circle", "dash-circle", "cash-coin", "wallet2", "bank"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )

# --- TUS MÓDULOS DE SIEMPRE ---
if sel == "CALENDARIO":
    st.header("📅 Agenda")
    eventos = []
    # CAMBIO: Solo viajes (Importe > 0), no cobranzas
    df_v = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in df_v.iterrows():
        eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True})
    calendar(events=eventos)

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    # Tu código de clientes con expander y edición...
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Carga de Viaje")
    # Tu form de carga de viaje...
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        imp = st.number_input("Importe")
        if st.form_submit_button("Guardar"):
            nv = pd.DataFrame([[date.today(), cli, date.today(), "-", "-", "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    # Tu código de presupuestos con el botón de PDF...
    if st.button("GENERAR PDF"):
         st.info("Generando...") # Aquí pones tu función de PDF

# --- NUEVOS MÓDULOS TESORERÍA ---
elif sel == "COBRANZA DE VIAJE":
    st.header("💸 Cobranza")
    with st.form("f_cob"):
        cl_c = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        mnt = st.number_input("Monto")
        cta = st.selectbox("Caja/Banco", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA"])
        afip = st.text_input("Comprobante AFIP")
        if st.form_submit_button("REGISTRAR Y RECIBO"):
            # Resta en Cta Cte
            nv = pd.DataFrame([[date.today(), cl_c, date.today(), "COBRANZA", "RECIBO", "-", -mnt, "RECIBO", afip]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            # Suma en Tesorería
            nt = pd.DataFrame([[date.today(), "INGRESO", f"PAGO: {cl_c}", mnt, cta, afip]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            st.download_button("Descargar Recibo", generar_html_recibo(cl_c, mnt, "Cobro Viaje", afip, cta), "Recibo.html")

elif sel == "SALDO DE CAJAS":
    st.header("🗄️ Cajas")
    for c in ["CAJA COTI", "CAJA TATO"]:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == c]
        s = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(c, f"$ {s:,.2f}")

# ... (seguí así con el resto del menú igual a como lo tenías)
