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
    col_p = ["Cliente", "Fecha Viaje", "Origen", "Destino", "Tipo Vehículo", "Importe", "Vencimiento"]
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

# --- FUNCIÓN REPORTE (PDF/HTML) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
            .info {{ margin: 20px 0; font-size: 14px; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tabla th {{ background-color: #f39c12; color: white; padding: 10px; text-align: left; }}
            .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
            .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CHACAGEST - Resumen de Cuenta</h1>
            <p>Fecha de emisión: {date.today()}</p>
        </div>
        <div class="info"><p><b>Cliente:</b> {cliente}</p></div>
        {tabla_html}
        <div class="total">SALDO TOTAL A LA FECHA: $ {saldo:,.2f}</div>
    </body>
    </html>
    """
    return html

# --- 2. LOGIN ---
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

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()

# --- 4. DISEÑO ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### CHACAGEST")
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "PRESUPUESTOS", "CARGA VIAJE", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "file-earmark-spreadsheet", "truck", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"container": {"background-color": "#f0f2f6"}, "nav-link-selected": {"background-color": "#5e2d61"}}
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
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    eventos = [{"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"} 
               for i, row in st.session_state.viajes.iterrows() if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE"]
    
    res_cal = calendar(events=eventos, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es", "height": 600}, custom_css=".fc-event { cursor: pointer; }", key="cal_final")
    
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])
    
    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar Información"):
                st.session_state.viaje_ver = None
                st.rerun()
            st.info(f"**Detalles:** {v_det['Cliente']} | {v_det['Origen']} -> {v_det['Destino']} | ${v_det['Importe']}")

elif sel == "PRESUPUESTOS":
    st.header("📄 Presupuestos")
    with st.form("f_presu"):
        cli_p = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v_p = c1.date_input("Fecha Viaje")
        f_venc = c2.date_input("Vencimiento", value=date.today() + timedelta(days=7))
        orig_p = st.text_input("Origen"); dest_p = st.text_input("Destino")
        c3, c4 = st.columns(2)
        tipo_v = c3.selectbox("Vehículo", ["Camioneta", "Chasis", "Balancín", "Semi", "Acoplado"])
        monto_p = c4.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR PRESUPUESTO"):
            np = pd.DataFrame([[cli_p, f_v_p, orig_p, dest_p, tipo_v, monto_p, f_venc]], columns=st.session_state.presupuestos.columns)
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
            guardar_datos("presupuestos", st.session_state.presupuestos)
            st.rerun()
    st.dataframe(st.session_state.presupuestos, use_container_width=True)

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
        saldo_total = df_ind['Importe'].sum()
        st.metric("SALDO TOTAL", f"$ {saldo_total:,.2f}")
        
        # --- RESTAURADO: BOTÓN DE DESCARGA PDF/HTML ---
        html_reporte = generar_html_resumen(cl, df_ind, saldo_total)
        st.download_button(label="📄 DESCARGAR RESUMEN (PARA IMPRIMIR)", data=html_reporte, file_name=f"Resumen_{cl}_{date.today()}.html", mime="text/html")
        st.dataframe(df_ind, use_container_width=True)

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha Viaje']}")
        c2.write(f"👤 **{row['Cliente']}** | ${row['Importe']}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
        st.divider()
