import streamlit as st
import pandas as pd
import os
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
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Cliente", "Fecha Viaje", "Origen", "Destino", "Tipo Vehículo", "Importe", "Fecha Vencimiento"]
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
        except:
            df_p = pd.DataFrame(columns=col_p)
            
        return df_c, df_v, df_p
    except: return None, None, None

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
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- FUNCIONES DE REPORTE ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>body {{ font-family: Arial; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }} .total {{ text-align: right; font-size: 20px; color: #5e2d61; font-weight: bold; }}</style></head><body><div class='header'><h1>Resumen de Cuenta</h1><p>{cliente}</p></div>{tabla_html}<div class='total'>SALDO: $ {saldo:,.2f}</div></body></html>"

def generar_html_presupuesto(row):
    return f"<html><head><style>body {{ font-family: Arial; padding: 30px; border: 2px solid #5e2d61; }} h1 {{ color: #5e2d61; border-bottom: 2px solid #f39c12; }} .dato {{ font-weight: bold; }}</style></head><body><h1>PRESUPUESTO DE VIAJE</h1><p>Cliente: <span class='dato'>{row['Cliente']}</span></p><p>Fecha Viaje: <span class='dato'>{row['Fecha Viaje']}</span></p><p>Origen: <span class='dato'>{row['Origen']}</span></p><p>Destino: <span class='dato'>{row['Destino']}</span></p><p>Vehículo: <span class='dato'>{row['Tipo Vehículo']}</span></p><p>Importe: <span class='dato'>$ {row['Importe']}</span></p><p>Vencimiento: <span class='dato'>{row['Fecha Vencimiento']}</span></p></body></html>"

# --- LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
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

# --- INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos = c, v, p

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### CHACAGEST")
    sel = option_menu(None, ["CALENDARIO", "CLIENTES", "PRESUPUESTOS", "CARGA VIAJE", "CTA CTE INDIVIDUAL", "COMPROBANTES"], 
                      icons=["calendar3", "people", "file-earmark-text", "truck", "person-vcard", "file-text"], default_index=0)
    if st.button("🔄 Sincronizar"):
        c, v, p = cargar_datos(); st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos = c, v, p; st.rerun()

# --- MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    eventos = [{"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"} 
               for i, row in st.session_state.viajes.iterrows() if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE"]
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, custom_css=".fc-event { cursor: pointer; }", key="cal_chaca")
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])
    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar Información"): st.session_state.viaje_ver = None; st.rerun()
            st.info(f"**Cliente:** {v['Cliente']} | **Ruta:** {v['Origen']} ➔ {v['Destino']} | **Móvil:** {v['Patente / Móvil']} | **Importe:** ${v['Importe']}")

elif sel == "PRESUPUESTOS":
    st.header("📄 Menú de Presupuestos")
    with st.expander("📝 NUEVO PRESUPUESTO", expanded=True):
        with st.form("f_p"):
            cliente_p = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            c1, c2 = st.columns(2)
            f_viaje = c1.date_input("Fecha Viaje")
            f_venc = c2.date_input("Fecha Vencimiento de Presupuesto", value=date.today()+timedelta(days=15))
            orig_p = st.text_input("Origen")
            dest_p = st.text_input("Destino")
            c3, c4 = st.columns(2)
            tipo_vh = c3.selectbox("Tipo de Vehículo", ["Camioneta", "Chasis", "Balancín", "Semi", "Acoplado"])
            monto_p = c4.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("GUARDAR PRESUPUESTO"):
                np = pd.DataFrame([[cliente_p, f_viaje, orig_p, dest_p, tipo_vh, monto_p, f_venc]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    
    st.subheader("📋 Presupuestos Emitidos")
    for i, row in st.session_state.presupuestos.iterrows():
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        col1.write(f"**{row['Cliente']}** | {row['Origen']} a {row['Destino']} | ${row['Importe']}")
        col2.download_button("📄 PDF", data=generar_html_presupuesto(row), file_name=f"Presu_{row['Cliente']}.html", mime="text/html", key=f"dl_p_{i}")
        if col3.button("🗑️", key=f"del_p_{i}"):
            st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
            guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
        st.divider()

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    with st.expander("➕ ALTA DE CLIENTE"):
        with st.form("f_c"):
            r = st.text_input("Razón Social"); cuit = st.text_input("CUIT")
            if st.form_submit_button("REGISTRAR"):
                nc = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "-", "-"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nc], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)
    with st.expander("🗑️ ELIMINAR CLIENTE"):
        el = st.selectbox("Seleccione para eliminar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
        if st.button("ELIMINAR PERMANENTEMENTE") and el != "-":
            st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != el]
            guardar_datos("clientes", st.session_state.clientes); st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Cargar Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_i = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    sal = df_i['Importe'].sum()
    st.metric("SALDO TOTAL", f"$ {sal:,.2f}")
    st.download_button("📄 DESCARGAR RESUMEN", data=generar_html_resumen(cl, df_i, sal), file_name=f"Resumen_{cl}.html", mime="text/html")
    st.dataframe(df_i, use_container_width=True)

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Viajes")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6
