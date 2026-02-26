import streamlit as st
import pandas as pd
import os
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
    try:
        sh = conectar_google()
        if sh is None: return None, None
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records())
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records())
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        return df_c, df_v
    except:
        return None, None

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
    except: return False

# --- 2. INICIALIZACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()

# --- 3. CSS (AQUÍ ESTÁ EL ARREGLO DEL COLOR Y TAMAÑO) ---
st.markdown("""
    <style>
    header { visibility: hidden; }
    /* Ajuste del Calendario para que combine con el menú #5e2d61 */
    .fc { 
        background-color: #5e2d61 !important; 
        color: white !important; 
        max-width: 850px !important; /* Tamaño controlado, no gigante */
        margin: 0 auto !important;
        border-radius: 10px;
        padding: 10px;
    }
    .fc-toolbar-title { color: white !important; font-size: 1.1rem !important; }
    .fc-button { background-color: rgba(255,255,255,0.2) !important; border: none !important; color: white !important; }
    .fc-daygrid-day-number { color: white !important; }
    .fc-col-header-cell-cushion { color: white !important; }
    .fc-event { background-color: #f39c12 !important; border: none !important; color: white !important; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR (LOGO Y MENÚ ORIGINAL) ---
with st.sidebar:
    # Intento de cargar logo (ajustá la ruta si es necesario)
    try: st.image("logo.png", use_container_width=True)
    except: st.markdown("<h2 style='text-align:center;'>🚛 CHACAGEST</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )

# --- 5. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if row['Origen'] != "AJUSTE" and str(row['Fecha Viaje']) != "-":
            eventos.append({
                "id": str(i),
                "title": f"{row['Cliente']}",
                "start": str(row['Fecha Viaje']),
                "allDay": True,
            })

    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "locale": "es",
        "height": 450, # Altura reducida para que no sea gigante
    }

    # Mostrar calendario
    state = calendar(events=eventos, options=cal_options, key="cal_final")

    # MOSTRAR INFORMACIÓN DEL VIAJE (Aparece abajo al hacer clic)
    if state.get("eventClick"):
        idx = int(state["eventClick"]["event"]["id"])
        v = st.session_state.viajes.loc[idx]
        st.info(f"""
        **DATOS DEL VIAJE SELECCIONADO:**
        * **Cliente:** {v['Cliente']}
        * **Desde/Hacia:** {v['Origen']} a {v['Destino']}
        * **Móvil/Patente:** {v['Patente / Móvil']}
        * **Importe:** ${v['Importe']}
        """)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    # Tabla con botón de borrar
    for i, row in st.session_state.clientes.iterrows():
        c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
        c1.write(row['Razón Social'])
        c2.write(row['CUIT / CUIL / DNI *'])
        if c3.button("🗑️", key=f"cli_{i}"):
            st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True)
            guardar_datos("clientes", st.session_state.clientes)
            st.rerun()
    st.divider()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viajes")
    with st.form("form_viaje"):
        # Tu lógica de carga de viaje...
        st.form_submit_button("Guardar Viaje")

elif sel == "AJUSTES (NC/ND)":
    st.header("📝 Notas de Crédito y Débito")
    st.info("Asociar a factura AFIP")
    # Lógica de ajustes...

elif sel == "COMPROBANTES":
    st.header("📜 Historial y Eliminación")
    for i, row in reversed(list(st.session_state.viajes.iterrows())):
        c1, c2, c3 = st.columns([0.2, 0.6, 0.2])
        c1.write(row['Fecha Viaje'])
        c2.write(f"{row['Cliente']} | {row['Origen']} - {row['Destino']}")
        if c3.button("🗑️ Eliminar", key=f"via_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i).reset_index(drop=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()

# (Agregá aquí las secciones de CTA CTE INDIVIDUAL y GENERAL que ya tenías)
