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
        
        # Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        # Viajes (Cuenta Corriente)
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Presupuestos
        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)

        # Tesoreria
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
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 2. REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""<html><head><style>body {{ font-family: Arial; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }} .total {{ text-align: right; font-size: 20px; color: #5e2d61; font-weight: bold; }}</style></head>
    <body><div class="header"><h1>CHACAGEST - Estado de Cuenta</h1></div><p><b>Cliente:</b> {cliente}</p>{tabla_html}<div class="total">SALDO: $ {saldo:,.2f}</div></body></html>"""

def generar_html_recibo(data):
    return f"""<html><head><style>body {{ font-family: Arial; padding: 30px; border: 5px solid #5e2d61; }} .monto {{ background: #f0f2f6; padding: 20px; font-size: 24px; font-weight: bold; text-align: center; border: 2px dashed #5e2d61; }}</style></head>
    <body><h2 style="text-align:center;">RECIBO DE PAGO - CHACAGEST</h2><hr>
    <p><b>Fecha:</b> {data['Fecha']}</p><p><b>Cliente:</b> {data['Cliente/Proveedor']}</p><p><b>Concepto:</b> {data['Concepto']}</p><p><b>Medio:</b> {data['Caja/Banco']}</p><p><b>Asoc. AFIP:</b> {data['Ref AFIP']}</p>
    <div class="monto">TOTAL: $ {abs(data['Monto']):,.2f}</div></body></html>"""

# --- 3. LOGIN ---
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

# --- 4. CARGA DE ESTADO ---
if 'clientes' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t

st.markdown("""<style>[data-testid="stSidebarNav"] { display: none; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; }</style>""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    sel = option_menu(None, ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERIA", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "safe", "person-vcard", "globe", "file-text"], default_index=0)
    if st.button("🔄 Sincronizar"):
        c, v, p, t = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    # FILTRO: Solo viajes (Importe > 0)
    df_v = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in df_v.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        # FILTRO: No mostrar saldos 0
        res = res[res['Importe'].round(2) != 0]
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))
        st.metric("DEUDA TOTAL", f"$ {res['Importe'].sum():,.2f}")

elif sel == "TESORERIA":
    st.header("💰 Tesorería y Cobranzas")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2, t3, t4 = st.tabs(["📥 COBRANZA CLIENTE", "💸 GASTOS/INGRESOS", "📊 MOVIMIENTOS", "🔄 TRASPASO"])
    
    with t1:
        with st.form("f_cob", clear_on_submit=True):
            c_sel = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
            cj = st.selectbox("Caja/Banco", opc_cajas)
            mon = st.number_input("Monto Cobrado $", min_value=0.0)
            afip = st.text_input("Nro Recibo / Ref AFIP")
            btn_cobrar = st.form_submit_button("REGISTRAR PAGO")
        
        if btn_cobrar:
            # 1. Registro en Tesorería
            nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
            # 2. Registro en Cuenta Corriente (Negativo para restar deuda)
            nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
            
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            
            if guardar_datos("tesoreria", st.session_state.tesoreria) and guardar_datos("viajes", st.session_state.viajes):
                st.success("Cobro registrado exitosamente.")
                rec_html = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Concepto": "Cobro de Viaje", "Caja/Banco": cj, "Monto": mon, "Ref AFIP": afip})
                st.download_button("🖨️ DESCARGAR RECIBO", rec_html, file_name=f"Recibo_{c_sel}.html", mime="text/html")

    with t2:
        with st.form("f_mov"):
            tipo = st.selectbox("Tipo", ["INGRESO VARIO", "EGRESO VARIO"])
            cj_m = st.selectbox("Caja", opc_cajas)
            con_m = st.text_input("Concepto")
            mon_m = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("GUARDAR MOVIMIENTO"):
                m_final = mon_m if "INGRESO" in tipo else -mon_m
                nt = pd.DataFrame([[date.today(), tipo, cj_m, con_m, "Varios", m_final, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                st.success("Movimiento guardado")
                st.rerun()

    with t3:
        cj_ver = st.selectbox("Filtrar por Caja", opc_cajas)
        df_caja = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj_ver]
        st.metric(f"Saldo {cj_ver}", f"$ {df_caja['Monto'].sum():,.2f}")
        st.dataframe(df_caja, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha Viaje")
        pat = c2.text_input("Patente")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje guardado")
            st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Historial del Cliente")
    cl_sel = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl_sel]
    saldo = df_cl['Importe'].sum()
    st.metric("SALDO ACTUAL", f"$ {saldo:,.2f}")
    st.dataframe(df_cl, use_container_width=True)
    if st.button("Generar Reporte PDF"):
        h = generar_html_resumen(cl_sel, df_cl, saldo)
        st.download_button("Descargar Reporte", h, file_name=f"CtaCte_{cl_sel}.html")

elif sel == "COMPROBANTES":
    st.header("📜 Historial General")
    st.dataframe(st.session_state.viajes, use_container_width=True)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.form("f_cli"):
        rs = st.text_input("Razón Social")
        cuit = st.text_input("CUIT")
        if st.form_submit_button("AGREGAR CLIENTE"):
            nc = pd.DataFrame([[rs, cuit, "-", "-", "-", "-", "-", "-", "-"]], columns=st.session_state.clientes.columns)
            st.session_state.clientes = pd.concat([st.session_state.clientes, nc], ignore_index=True)
            guardar_datos("clientes", st.session_state.clientes)
            st.rerun()
