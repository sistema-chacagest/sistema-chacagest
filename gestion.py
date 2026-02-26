import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as fgo # Para el calendario visual
from streamlit_option_menu import option_menu
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - CALENDARIO", page_icon="📅", layout="wide")

def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        return gspread.authorize(creds).open("Base_Chacagest")
    except Exception as e:
        return None

def cargar_datos():
    sh = conectar_google()
    if not sh: return pd.DataFrame(), pd.DataFrame()
    try:
        df_c = pd.DataFrame(sh.worksheet("clientes").get_all_records())
        df_v = pd.DataFrame(sh.worksheet("viajes").get_all_records())
        # Blindaje de fechas e importes
        df_v['Fecha Viaje'] = pd.to_datetime(df_v['Fecha Viaje'], errors='coerce')
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        return df_c, df_v
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # ... (Tu código de login se mantiene igual)
    st.title("🚛 CHACAGEST")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR"):
        if u == "admin" and p == "chaca2026":
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

# Carga inicial
if 'clientes' not in st.session_state:
    st.session_state.clientes, st.session_state.viajes = cargar_datos()

# --- SIDEBAR CON TU MENÚ DESPLEGABLE ---
with st.sidebar:
    st.markdown("### 🗄️ PANEL DE CONTROL")
    
    with st.expander("💰 VENTAS", expanded=True):
        accion = option_menu(
            menu_title=None,
            options=["Calendario de Viajes", "Clientes", "Carga de Viaje", "Cta Cte Individual", "Comprobantes"],
            icons=["calendar3", "people", "truck", "person-vcard", "file-text"],
            default_index=0,
            key="menu_v"
        )
    
    with st.expander("🛒 COMPRAS", expanded=False):
        st.write("Próximamente...")

# --- MÓDULO CALENDARIO REAL ---
if accion == "Calendario de Viajes":
    st.header("📅 Calendario Operativo de Viajes")
    
    df = st.session_state.viajes.copy()
    if df.empty:
        st.warning("No hay viajes cargados para mostrar en el calendario.")
    else:
        # Agrupamos por fecha para ver cuántos viajes hay por día
        df['dia'] = df['Fecha Viaje'].dt.day
        df['mes'] = df['Fecha Viaje'].dt.month
        df['año'] = df['Fecha Viaje'].dt.year
        
        # Filtro de Mes y Año
        c1, c2 = st.columns(2)
        mes_sel = c1.selectbox("Mes", range(1, 13), index=date.today().month - 1)
        año_sel = c2.selectbox("Año", [2025, 2026], index=1)
        
        filtro = df[(df['mes'] == mes_sel) & (df['año'] == año_sel)]
        
        # Crear una matriz de calendario visual
        import calendar
        cal = calendar.monthcalendar(año_sel, mes_sel)
        
        st.subheader(f"Viajes de {calendar.month_name[mes_sel]} {año_sel}")
        
        # Dibujamos el calendario con columnas
        cols = st.columns(7)
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, d in enumerate(dias_semana):
            cols[i].markdown(f"**{d}**")
            
        for semana in cal:
            cols = st.columns(7)
            for i, dia in enumerate(semana):
                if dia == 0:
                    cols[i].write("")
                else:
                    # Buscamos si hay viajes este día
                    viajes_dia = filtro[filtro['dia'] == dia]
                    if not viajes_dia.empty:
                        # Si hay viajes, ponemos el número en naranja y el cliente
                        cols[i].markdown(f"""
                            <div style="background-color:#fdf2e9; border-left: 5px solid #d35400; padding:5px; border-radius:5px;">
                            <span style="color:#d35400; font-weight:bold;">{dia}</span><br>
                            <small>{viajes_dia['Cliente'].iloc[0][:10]}...</small><br>
                            <b style="font-size:10px;">${viajes_dia['Importe'].sum():.0f}</b>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f"<div style='color:gray;'>{dia}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.write("📌 *El calendario muestra el primer cliente del día y el monto total acumulado.*")

# --- RESTO DE TUS MÓDULOS (Clientes, Carga, etc.) ---
elif accion == "Clientes":
    st.header("👤 Gestión de Clientes")
    # ... (Aquí sigue tu código de Clientes)
    st.dataframe(st.session_state.clientes)

elif accion == "Carga de Viaje":
    st.header("🚛 Registro de Viaje")
    # ... (Aquí sigue tu código de Carga)
