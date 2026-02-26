import streamlit as st
import pandas as pd
from datetime import date
from streamlit_option_menu import option_menu
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    else:
        creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Base_Chacagest")

def cargar_datos():
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    try:
        sh = conectar_google()
        # Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        # Viajes
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        if datos_v:
            df_v = pd.DataFrame(datos_v)
            df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        else:
            df_v = pd.DataFrame(columns=col_v)
        
        return df_c, df_v
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None # Devolvemos None para saber que falló

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        # Forzamos que todo sea texto para evitar errores de formato en Google Sheets
        df_str = df.astype(str)
        datos = [df_str.columns.values.tolist()] + df_str.values.tolist()
        ws.update(datos, 'A1')
        st.toast(f"✅ Guardado en {nombre_hoja}", icon="💾")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

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
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    if c is not None:
        st.session_state.clientes, st.session_state.viajes = c, v
    else:
        st.warning("No se pudieron cargar los datos. Verifique la conexión.")

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
    st.markdown("### Menú Principal")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v = cargar_datos()
        if c is not None and not v.empty: # SOLO ACTUALIZA SI TRAE DATOS
            st.session_state.clientes, st.session_state.viajes = c, v
            st.success("Datos actualizados")
            st.rerun()
        else:
            st.error("Sincronización fallida: No se recibieron datos de la nube.")

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda Logística")
    eventos = []
    df_v = st.session_state.viajes
    # Filtramos viajes reales
    viajes_reales = df_v[df_v['Tipo Comp'].str.contains("Factura", na=False)].copy()
    
    for i, row in viajes_reales.iterrows():
        try:
            # Aseguramos formato YYYY-MM-DD
            f_viaje = pd.to_datetime(row['Fecha Viaje']).strftime('%Y-%m-%d')
            eventos.append({
                "title": f"🚛 {row['Cliente']}",
                "start": f_viaje,
                "end": f_viaje,
                "resourceId": i,
                "color": "#5e2d61",
                "extendedProps": {"desc": f"Ruta: {row['Origen']} a {row['Destino']} | Unidad: {row['Patente / Móvil']}"}
            })
        except: continue

    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listWeek"},
        "initialView": "dayGridMonth",
        "locale": "es", "height": 500,
    }
    
    state = calendar(events=eventos, options=cal_options, key="cal_v3")
    if state.get("eventClick"):
        st.info(f"📍 {state['eventClick']['event']['extendedProps']['desc']}")

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli"):
            r = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                if r and cuit:
                    nueva = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "CC"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Nuevo Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha")
        pat = st.text_input("Patente")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura (CC)", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comp AFIP Asociado") # Importante para tu nota guardada
        mot = st.text_input("Concepto")
        monto = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("REGISTRAR"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", mot, "-", val, "NC" if val<0 else "ND", nro_asoc]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    for i, row in st.session_state.viajes.iloc[::-1].iterrows():
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"{row['Fecha Viaje']}")
        c2.write(f"**{row['Cliente']}** | ${row['Importe']}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
