import streamlit as st
import pandas as pd
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CHACAGEST - SISTEMA DE GESTIÓN", page_icon="🚛", layout="wide")

# Colores institucionales
COLOR_PRINCIPAL = "#5e2d61"  # El violeta de tu menú
COLOR_CONTRASTE = "#f39c12"  # Naranja para resaltar botones y eventos

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google():
    nombre_planilla = "Base_Chacagest"
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # Intenta usar Secrets de Streamlit o archivo local
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
    try:
        sh = conectar_google()
        if sh is None: return None, None
        
        # Cargar Clientes
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records())
        
        # Cargar Viajes
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records())
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        return df_c, df_v
    except:
        return pd.DataFrame(), pd.DataFrame()

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

# --- 3. INICIALIZACIÓN DE ESTADO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v

# --- 4. CSS PARA DISEÑO MIMETIZADO ---
st.markdown(f"""
    <style>
    /* Ocultar elementos de Streamlit */
    header {{ visibility: hidden; }}
    
    /* Estilo del Calendario para que combine con el Menú */
    .fc {{ 
        background-color: {COLOR_PRINCIPAL} !important; 
        color: white !important;
        border-radius: 15px;
        padding: 15px;
        border: none !important;
    }}
    .fc-toolbar-title {{ color: white !important; font-size: 1.2rem !important; }}
    .fc-button {{ 
        background-color: rgba(255,255,255,0.1) !important; 
        border: 1px solid rgba(255,255,255,0.3) !important; 
        color: white !important; 
    }}
    .fc-button:hover {{ background-color: {COLOR_CONTRASTE} !important; }}
    .fc-daygrid-day-number {{ color: white !important; padding: 5px !important; }}
    .fc-col-header-cell-cushion {{ color: white !important; }}
    
    /* Eventos */
    .fc-event {{
        background-color: {COLOR_CONTRASTE} !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        padding: 2px 5px !important;
        cursor: pointer !important;
    }}
    
    /* Botones generales */
    div.stButton > button {{
        background-color: {COLOR_CONTRASTE} !important;
        color: white !important;
        border-radius: 5px;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🚛 LOGIN")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
    st.stop()

# --- 6. SIDEBAR (MENÚ) ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: {COLOR_PRINCIPAL};'>CHACAGEST</h2>", unsafe_allow_html=True)
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "COMPROBANTES", "AJUSTES (NC/ND)", "ESTADÍSTICAS"],
        icons=["calendar3", "people", "truck", "file-earmark-text", "file-diff", "graph-up"],
        default_index=0,
        styles={
            "nav-link-selected": {"background-color": COLOR_PRINCIPAL},
        }
    )
    if st.button("🔄 Sincronizar Google Sheets"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()

# --- 7. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    
    eventos = []
    # Generar eventos para el calendario
    for i, row in st.session_state.viajes.iterrows():
        if row['Origen'] != "AJUSTE" and row['Fecha Viaje'] != "-":
            eventos.append({
                "id": str(i),
                "title": f"🚛 {row['Cliente']}",
                "start": str(row['Fecha Viaje']),
                "end": str(row['Fecha Viaje']),
                "allDay": True
            })

    opciones_cal = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialView": "dayGridMonth",
        "locale": "es",
        "height": 550,
    }

    # Mostrar calendario y capturar clic
    res_cal = calendar(events=eventos, options=opciones_cal, key="cal_v2")

    # Mostrar Info si se hace clic
    if res_cal.get("eventClick"):
        id_evento = int(res_cal["eventClick"]["event"]["id"])
        viaje_info = st.session_state.viajes.loc[id_evento]
        st.markdown("---")
        with st.container():
            st.subheader(f"🔍 Detalle: {viaje_info['Cliente']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ruta", f"{viaje_info['Origen']} ➔ {viaje_info['Destino']}")
            c2.metric("Móvil / Patente", viaje_info['Patente / Móvil'])
            c3.metric("Importe", f"$ {viaje_info['Importe']:,.2f}")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    
    # Formulario de alta
    with st.expander("➕ AGREGAR NUEVO CLIENTE"):
        with st.form("nuevo_cli", clear_on_submit=True):
            r_soc = st.text_input("Razón Social")
            cuit = st.text_input("CUIT/DNI")
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([[r_soc, cuit, "-", "-", "-", "-", "-", "-", "Cuenta Corriente"]], 
                                     columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes)
                st.rerun()

    # Listado con opción de BORRAR
    st.subheader("Lista de Clientes")
    for idx, row in st.session_state.clientes.iterrows():
        col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
        col1.write(f"**{row['Razón Social']}**")
        col2.write(f"ID: {row['CUIT / CUIL / DNI *']}")
        if col3.button("🗑️", key=f"del_cli_{idx}"):
            st.session_state.clientes = st.session_state.clientes.drop(idx).reset_index(drop=True)
            guardar_datos("clientes", st.session_state.clientes)
            st.rerun()
        st.divider()

elif sel == "CARGA VIAJE":
    st.header("🚛 Nuevo Viaje")
    with st.form("v_form"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].tolist())
        f_v = st.date_input("Fecha Viaje")
        ori = st.text_input("Origen")
        des = st.text_input("Destino")
        pat = st.text_input("Patente")
        imp = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR"):
            nv = pd.DataFrame([[date.today(), cl, f_v, ori, des, pat, imp, "Factura", "-"]], 
                              columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje Guardado")

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    # Listado con opción de BORRAR
    for idx, row in reversed(list(st.session_state.viajes.iterrows())):
        col1, col2, col3 = st.columns([0.2, 0.6, 0.1])
        col1.write(row['Fecha Viaje'])
        col2.write(f"**{row['Cliente']}** - {row['Origen']} a {row['Destino']} (**${row['Importe']}**)")
        if col3.button("🗑️", key=f"del_viaje_{idx}"):
            st.session_state.viajes = st.session_state.viajes.drop(idx).reset_index(drop=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
        st.divider()

elif sel == "AJUSTES (NC/ND)":
    st.header("📝 Notas de Crédito y Débito")
    st.warning("Recuerda: estos movimientos deben estar asociados a un CUIT y factura AFIP.")
    # (Aquí iría el formulario de NC/ND similar al de viajes pero con signo invertido)
