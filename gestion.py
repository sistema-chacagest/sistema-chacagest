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
    # Definición de columnas según tu estructura original
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Carga Clientes
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        # Carga Viajes
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Carga Presupuestos
        try:
            ws_p = sh.worksheet("presupuestos")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)

        # Carga Tesorería (Nueva Hoja)
        try:
            ws_t = sh.worksheet("tesoreria")
            df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)
            
        return df_c, df_v, df_p, df_t
    except Exception as e:
        st.error(f"Error al cargar tablas: {e}")
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
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""<html><head><style>body {{ font-family: Arial; color: #333; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }} .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; }}</style></head>
    <body><div class="header"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Cliente: {cliente}</p></div>{tabla_html}<div class="total"> SALDO: $ {saldo:,.2f} </div></body></html>"""

def generar_html_recibo(data):
    return f"""<html><head><style>body {{ font-family: Arial; padding: 30px; border: 5px solid #5e2d61; }} .monto {{ background: #f0f2f6; padding: 15px; font-size: 20px; font-weight: bold; border: 1px dashed #5e2d61; }}</style></head>
    <body><h2 style="color:#5e2d61">RECIBO DE PAGO - CHACAGEST</h2><hr><p><b>Fecha:</b> {data['Fecha']}</p><p><b>Cliente:</b> {data['Cliente/Proveedor']}</p><p><b>Concepto:</b> {data['Concepto']}</p><p><b>Medio:</b> {data['Caja/Banco']}</p><p><b>Ref AFIP:</b> {data['Ref AFIP']}</p><div class="monto">TOTAL: $ {abs(data['Monto']):,.2f}</div></body></html>"""

# --- LOGIN ---
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

# --- INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.tesoreria = t if t is not None else pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### MENU")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERIA", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "safe", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v, p, t = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
        st.rerun()

# --- MÓDULOS ---

if sel == "TESORERIA":
    st.header("💰 Tesorería")
    opc_caja = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE", "OTROS"]
    t1, t2, t3, t4, t5 = st.tabs(["📥 INGRESO", "📤 EGRESO", "🧾 COBRANZA", "📊 MOVIMIENTOS", "🔄 TRASPASO"])

    with t1:
        with st.form("f_ing"):
            f = st.date_input("Fecha", date.today())
            cj = st.selectbox("Caja", opc_caja)
            con = st.text_input("Concepto")
            cli = st.text_input("Origen")
            mon = st.number_input("Monto", min_value=0.0)
            afip = st.text_input("Asociar AFIP")
            if st.form_submit_button("GUARDAR"):
                nt = pd.DataFrame([[f, "INGRESO", cj, con, cli, mon, afip]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); st.success("Ok"); st.rerun()

    with t2:
        with st.form("f_egr"):
            f = st.date_input("Fecha", date.today())
            cj = st.selectbox("Caja", opc_caja)
            con = st.text_input("Concepto")
            cli = st.text_input("Destino")
            mon = st.number_input("Monto", min_value=0.0)
            afip = st.text_input("Asociar AFIP")
            if st.form_submit_button("GUARDAR"):
                nt = pd.DataFrame([[f, "EGRESO", cj, con, cli, -mon, afip]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); st.success("Ok"); st.rerun()

    with t3:
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            cj = st.selectbox("Cobro vía", opc_caja)
            mon = st.number_input("Monto", min_value=0.0)
            afip = st.text_input("Nro Recibo / AFIP")
            if st.form_submit_button("COBRAR"):
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Pago Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                st.
