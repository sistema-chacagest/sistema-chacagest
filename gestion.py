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
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
    
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

# --- 2. LOGIN Y ESTILOS ---
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

if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t

st.markdown("""<style>
    [data-testid="stSidebarNav"] { display: none; }
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; }
    </style>""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    sel = option_menu(None, ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERIA", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "safe", "person-vcard", "globe", "file-text"], default_index=0)
    
    if st.button("🔄 Sincronizar"):
        c, v, p, t = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
        st.rerun()

# --- 4. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    # FILTRO: Solo registros que sean viajes (Importe > 0) y que tengan fecha válida
    df_solo_viajes = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    
    for i, row in df_solo_viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({
                "id": str(i),
                "title": f"🚛 {row['Cliente']} ({row['Origen']})",
                "start": str(row['Fecha Viaje']),
                "allDay": True,
                "backgroundColor": "#f39c12",
                "borderColor": "#d35400"
            })
    
    cal_options = {"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es", "height": 600}
    calendar(events=eventos, options=cal_options, key="cal_viajes")

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    if not st.session_state.viajes.empty:
        # Agrupamos por cliente y sumamos
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        
        # FILTRO: Solo los que NO están en cero (Redondeamos por seguridad en decimales)
        res = res[res['Importe'].round(2) != 0]
        
        if not res.empty:
            st.table(res.style.format({"Importe": "$ {:,.2f}"}))
            st.metric("DEUDA TOTAL EN CALLE", f"$ {res['Importe'].sum():,.2f}")
        else:
            st.success("🎉 Todas las cuentas están al día (Saldo 0).")

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha")
        pat = c2.text_input("Patente")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        # Nota: Aquí guardamos como positivo porque es una deuda generada
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje registrado")
            st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Tesorería y Cobranzas")
    t1, t2 = st.tabs(["📥 COBRANZA CLIENTE", "📊 VER MOVIMIENTOS"])
    with t1:
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            mon = st.number_input("Monto Cobrado $", min_value=0.0)
            afip = st.text_input("Referencia / Nro Recibo (Asociar AFIP)")
            if st.form_submit_button("REGISTRAR PAGO"):
                # El pago entra como NEGATIVO en la cuenta corriente del viaje para restar deuda
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Pago impactado en Cuenta Corriente")
                st.rerun()

# --- EL RESTO DE MÓDULOS SE MANTIENEN IGUAL QUE TU LÓGICA ORIGINAL ---
# (Clientes, Presupuestos, Cta Cte Individual, Comprobantes...)
