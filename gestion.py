import streamlit as st
import pandas as pd
import os
from datetime import date
from streamlit_option_menu import option_menu
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials

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
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        
        return df_c, df_v
    except Exception:
        return pd.DataFrame(columns=col_c), pd.DataFrame(columns=col_v)

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        datos = [df.columns.values.tolist()] + df.astype(str).values.tolist()
        ws.update(datos)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- 2. INICIALIZACIÓN ---
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    st.session_state.clientes, st.session_state.viajes = cargar_datos()

# --- 3. DISEÑO VISUAL ---
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

# --- 4. SIDEBAR CON LOGO ---
with st.sidebar:
    # --- AQUÍ CARGAMOS TU LOGO ---
    # Reemplaza 'logo_path.jpg' por el nombre de tu archivo en GitHub
    try:
        st.image("logo_path.jpg", use_container_width=True)
    except:
        st.info("Logo no encontrado en GitHub")
    
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()

# --- 5. LÓGICA DE MÓDULOS ---

if sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                if r and cuit:
                    nuevo = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "Cta Cte"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Registrado"); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Nuevo Viaje")
    if not st.session_state.clientes.empty:
        with st.form("f_v"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            f = st.date_input("Fecha")
            orig = st.text_input("Origen")
            dest = st.text_input("Destino")
            imp = st.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("GUARDAR"):
                nv = pd.DataFrame([[date.today(), cli, f, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Viaje guardado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito y Débito")
    st.info("Recuerde que estos movimientos deben asociarse a un comprobante AFIP.")
    tipo = st.radio("Tipo de Ajuste:", ["Nota de Crédito (Resta)", "Nota de Débito (Suma)"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante AFIP Asociado *")
        motivo = st.text_input("Motivo / Concepto")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR EN AFIP / SISTEMA"):
            if nro_asoc:
                es_nc = "Crédito" in tipo
                final = -monto if es_nc else monto
                t_comp = "NC" if es_nc else "ND"
                nc_row = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", motivo, "-", final, t_comp, nro_asoc]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nc_row], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success(f"{t_comp} registrada correctamente y asociada al comp. {nro_asoc}")
                st.rerun()
            else:
                st.warning("Debe ingresar el comprobante asociado.")

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO ACTUAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Resumen de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    st.dataframe(st.session_state.viajes.iloc[::-1], use_container_width=True)
