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
    try:
        sh = conectar_google()
        if sh is None: return None, None, None
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        try:
            ws_p = sh.worksheet("presupuestos")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)
        return df_c, df_v, df_p
    except:
        return None, None, None

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
    except:
        return False

# --- REPORTE CTA CTE ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>body {{ font-family: Arial; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }}</style></head><body><div class='header'><h1>Resumen {cliente}</h1></div>{tabla_html}<h3>Saldo: $ {saldo:,.2f}</h3></body></html>"

# --- REPORTE PRESUPUESTO ---
def generar_html_presupuesto(p_data):
    return f"<html><head><style>body {{ font-family: Arial; padding: 40px; border: 2px solid #5e2d61; }} .header {{ border-bottom: 3px solid #f39c12; }} .monto {{ font-size: 22px; color: #d35400; font-weight: bold; }}</style></head><body><div class='header'><h2 style='color:#5e2d61'>CHACAGEST - PRESUPUESTO</h2></div><p><b>Cliente:</b> {p_data['Cliente']}</p><p><b>Unidad:</b> {p_data['Tipo Móvil']}</p><div style='background:#f9f9f9; padding:15px;'>{p_data['Detalle']}</div><p class='monto'>TOTAL: $ {float(p_data['Importe']):,.2f}</p></body></html>"

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
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos = c, v, p

# --- 4. DISEÑO ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### PANEL DE CONTROL")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v, p = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos = c, v, p
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False; st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True})
            
    # --- ESTILO ESPECIFICO DEL CALENDARIO ---
    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "locale": "es", "height": 600,
    }
    custom_css = """
        .fc-button-primary { background-color: #5e2d61 !important; border-color: #5e2d61 !important; }
        .fc-event { background-color: #f39c12 !important; border: none !important; cursor: pointer; }
        .fc-toolbar-title { color: #5e2d61 !important; font-weight: bold; }
    """
    
    res_cal = calendar(events=eventos, options=cal_options, custom_css=custom_css, key="cal_final")

    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])

    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            st.markdown(f"<div style='background:#f0f2f6; padding:15px; border-left:5px solid #f39c12; border-radius:5px;'><h4>Detalles del Viaje</h4><b>Cliente:</b> {v_det['Cliente']}<br><b>Ruta:</b> {v_det['Origen']} ➔ {v_det['Destino']}<br><b>Móvil:</b> {v_det['Patente / Móvil']}<br><b>Importe:</b> $ {v_det['Importe']}</div>", unsafe_allow_html=True)
            if st.button("Cerrar Detalles"): st.session_state.viaje_ver = None; st.rerun()

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                new_c = pd.DataFrame([[r, cuit, "", "", "", "", "", "", ""]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, new_c], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)
    with st.expander("🗑️ ELIMINAR CLIENTE"):
        elim_c = st.selectbox("Cliente a borrar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
        if st.button("BORRAR") and elim_c != "-":
            st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim_c]
            guardar_datos("clientes", st.session_state.clientes); st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); pat = st.text_input("Móvil")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    t_c, t_h = st.tabs(["Crear", "Historial"])
    with t_c:
        with st.form("f_p", clear_on_submit=True):
            p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            p_venc = st.date_input("Vencimiento", date.today() + timedelta(days=7))
            p_movil = st.selectbox("Unidad", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            p_det = st.text_area("Detalle")
            p_imp = st.number_input("Total $", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                np = pd.DataFrame([[date.today(), p_cli, p_f_venc, p_det, p_movil, p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    with t_h:
        for i in reversed(st.session_state.presupuestos.index):
            row = st.session_state.presupuestos.loc[i]
            c_a, c_b = st.columns([0.8, 0.2])
            c_a.write(f"**{row['Cliente']}** | {row['Tipo Móvil']} | ${row['Importe']}")
            h_p = generar_html_presupuesto(row)
            c_b.download_button("Descargar", data=h_p, file_name=f"Presu_{i}.html", mime="text/html", key=f"dl_{i}")

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
        st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
        st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
        c1.write(f"{row['Fecha Viaje']}")
        c2.write(f"**{row['Cliente']}** | ${row['Importe']}")
        if c3.button("🗑️", key=f"d_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()
