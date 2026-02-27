import streamlit as st
import pandas as pd
from datetime import date
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
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"]
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        ws_c = sh.worksheet("clientes"); df_c = pd.DataFrame(ws_c.get_all_records())
        ws_v = sh.worksheet("viajes"); df_v = pd.DataFrame(ws_v.get_all_records())
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        ws_p = sh.worksheet("presupuestos"); df_p = pd.DataFrame(ws_p.get_all_records())
        ws_t = sh.worksheet("tesoreria"); df_t = pd.DataFrame(ws_t.get_all_records())
        return df_c, df_v, df_p, df_t
    except: return pd.DataFrame(columns=col_c), pd.DataFrame(columns=col_v), pd.DataFrame(columns=col_p), pd.DataFrame(columns=col_t)

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

# --- FUNCIONES DE REPORTES (PRESUPUESTO Y RECIBO) ---
def generar_html_presupuesto(p_data):
    return f"""<html><body style="font-family: Arial; padding: 30px;">
    <h2 style="color: #5e2d61;">🚛 CHACAGEST - PRESUPUESTO</h2>
    <hr>
    <p><b>Cliente:</b> {p_data['Cliente']}</p>
    <p><b>Fecha:</b> {p_data['Fecha Emisión']}</p>
    <p><b>Detalle:</b> {p_data['Detalle']}</p>
    <h3 style="color: #d35400;">Total: $ {float(p_data['Importe']):,.2f}</h3>
    </body></html>"""

def generar_html_recibo(cliente, monto, concepto, afip, cuenta):
    return f"""<html><body style="font-family: Arial; border: 2px solid #5e2d61; padding: 40px; width: 600px; margin: auto;">
    <h1 style="text-align: center; color: #5e2d61;">RECIBO DE PAGO</h1>
    <p style="text-align: right;"><b>Fecha:</b> {date.today()}</p>
    <hr>
    <p><b>Recibimos de:</b> {cliente}</p>
    <p><b>La cantidad de:</b> $ {monto:,.2f}</p>
    <p><b>En concepto de:</b> {concepto}</p>
    <p><b>Forma de pago:</b> {cuenta}</p>
    <p><b>Comprobante Asociado:</b> {afip}</p>
    <br><br>
    <div style="text-align: center;"><p>_______________________</p><p>Firma y Sello CHACAGEST</p></div>
    </body></html>"""

# --- INICIALIZACIÓN Y DISEÑO ---
if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t

st.markdown("""<style> [data-testid="stSidebarNav"] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; } </style>""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚛 CHACAGEST")
    sel = option_menu(None, ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "INGRESOS VARIOS", "EGRESOS VARIOS", "COBRANZA DE VIAJE", "SALDO DE CAJAS", "SALDO DE BANCOS"], 
    icons=["calendar3", "people", "truck", "file-text", "person-vcard", "globe", "file-text", "plus-circle", "dash-circle", "cash-coin", "wallet2", "bank"], default_index=0)

# --- MODULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    # FILTRO: Solo viajes con importe positivo (No pagos/recibos)
    df_viajes_solo = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in df_viajes_solo.iterrows():
        eventos.append({ "id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12" })
    calendar(events=eventos, options={"locale": "es"})

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Nuevo Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Viaje Cargado")

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    with st.form("f_p"):
        p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        p_det = st.text_area("Detalle")
        p_imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GENERAR"):
            nuevo_p = {"Fecha Emisión": str(date.today()), "Cliente": p_cli, "Vencimiento": str(date.today()+timedelta(days=15)), "Detalle": p_det, "Tipo Móvil": "Bus", "Importe": p_imp}
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, pd.DataFrame([nuevo_p])], ignore_index=True)
            guardar_datos("presupuestos", st.session_state.presupuestos)
            st.download_button("Descargar PDF Presupuesto", generar_html_presupuesto(nuevo_p), f"Presupuesto_{p_cli}.html", "text/html")

elif sel == "COBRANZA DE VIAJE":
    st.header("💸 Registrar Cobranza")
    with st.form("f_cob", clear_on_submit=True):
        cl_cob = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        monto_cob = st.number_input("Monto $", min_value=0.0)
        cta_cob = st.selectbox("Cuenta", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"])
        afip_cob = st.text_input("Comprobante AFIP")
        submitted = st.form_submit_button("REGISTRAR Y GENERAR RECIBO")
        
        if submitted:
            # Impacto Cta Cte (Importe Negativo)
            nv = pd.DataFrame([[date.today(), cl_cob, date.today(), "COBRANZA", "RECIBO", "-", -monto_cob, "RECIBO", afip_cob]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            # Impacto Tesoreria
            nt = pd.DataFrame([[date.today(), "INGRESO", f"COBRANZA: {cl_cob}", monto_cob, cta_cob, afip_cob]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            
            st.success("Cobro registrado con éxito.")
            html_recibo = generar_html_recibo(cl_cob, monto_cob, "Cobranza de Viajes", afip_cob, cta_cob)
            st.download_button("📄 DESCARGAR RECIBO PDF", html_recibo, f"Recibo_{cl_cob}_{afip_cob}.html", "text/html")

elif sel == "SALDO DE CAJAS":
    st.header("🗄️ Cajas")
    for c in ["CAJA COTI", "CAJA TATO"]:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == c]
        saldo = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(c, f"$ {saldo:,.2f}")

# (Los demas modulos de Cta Cte y Bancos siguen igual a tu version anterior)
