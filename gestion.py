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
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None
        
        # Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        # Viajes (Cta Cte)
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Presupuestos (Nueva Hoja)
        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)
            
        return df_c, df_v, df_p
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
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
    except Exception as e:
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 2. FUNCIONES DE REPORTE ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tabla th {{ background-color: #f39c12; color: white; padding: 10px; }}
            .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
            .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Emisión: {date.today()}</p></div>
        <p><b>Cliente:</b> {cliente}</p>
        {tabla_html}
        <div class="total">SALDO TOTAL: $ {saldo:,.2f}</div>
    </body>
    </html>
    """

def generar_html_presupuesto(p):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 30px; border: 2px solid #5e2d61; }}
            .header {{ border-bottom: 2px solid #f39c12; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ color: #5e2d61; font-size: 24px; font-weight: bold; }}
            .info {{ margin-bottom: 20px; }}
            .monto {{ font-size: 20px; font-weight: bold; color: #d35400; text-align: right; }}
        </style>
    </head>
    <body>
        <div class="header"><span class="title">🚛 CHACAGEST - PRESUPUESTO</span></div>
        <div class="info">
            <p><b>Cliente:</b> {p['Cliente']}</p>
            <p><b>Fecha Emisión:</b> {p['Fecha Emisión']} | <b>Válido hasta:</b> {p['Vencimiento']}</p>
            <p><b>Unidad:</b> {p['Tipo Móvil']}</p>
        </div>
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 100px;">
            <b>Detalle del Servicio:</b><br>{p['Detalle']}
        </div>
        <div class="monto">TOTAL: $ {float(p['Importe']):,.2f}</div>
    </body>
    </html>
    """

# --- 3. LOGIN ---
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

# --- 4. INICIALIZACIÓN DE DATOS ---
if 'clientes' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()

# Estilos CSS
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
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True})
    calendar(events=eventos, options={"locale": "es", "headerToolbar": {"right": "dayGridMonth"}}, key="cal")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                new_c = pd.DataFrame([[r, cuit, "", "", "", "", "", "", ""]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, new_c], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes)
                st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje guardado"); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    t1, t2 = st.tabs(["Crear", "Historial"])
    with t1:
        with st.form("f_p"):
            c1, c2 = st.columns(2)
            p_cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            p_venc = c2.date_input("Vencimiento", date.today() + timedelta(days=7))
            p_movil = st.selectbox("Tipo de Móvil", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            p_det = st.text_area("Detalle")
            p_imp = st.number_input("Importe Total $", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                np = pd.DataFrame([[date.today(), p_cli, p_venc, p_det, p_movil, p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos)
                st.rerun()
    with t2:
        for i, row in st.session_state.presupuestos.iterrows():
            col_a, col_b = st.columns([0.8, 0.2])
            col_a.write(f"**{row['Cliente']}** | {row['Tipo Móvil']} | ${row['Importe']}")
            html_p = generar_html_presupuesto(row)
            col_b.download_button("🖨️ PDF", data=html_p, file_name="Presupuesto.html", mime="text/html", key=f"p_{i}")
            st.divider()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_i = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_i['Importe'].sum():,.2f}")
    st.dataframe(df_i, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Global")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i, row in st.session_state.viajes.iloc[::-1].iterrows():
        c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
        c1.write(row['Fecha Viaje'])
        c2.write(f"{row['Cliente']} - {row['Origen']} a {row['Destino']} (${row['Importe']})")
        if c3.button("🗑️", key=f"d_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
