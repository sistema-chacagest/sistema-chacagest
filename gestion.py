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
    except:
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

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo_path.png", width=200)
        except: st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Incorrecto")
    st.stop()

# --- 3. INICIALIZACIÓN Y DISEÑO ---
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    st.session_state.clientes, st.session_state.viajes = cargar_datos()

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    sel = option_menu(None, ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
                      icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"], default_index=0)
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 5. MÓDULOS ---

if sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            razon = c1.text_input("Razón Social / Nombre *")
            cuit = c2.text_input("CUIT / DNI *")
            mail = c1.text_input("Email")
            tel = c2.text_input("Teléfono")
            dire = c1.text_input("Dirección Fiscal")
            loc = c2.text_input("Localidad")
            prov = c1.selectbox("Provincia", ["Buenos Aires", "CABA", "Santa Fe", "Córdoba", "La Pampa", "Otra"])
            c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if razon and cuit:
                    nueva_fila = [razon, cuit, mail, tel, dire, loc, prov, c_iva, c_vta]
                    nuevo_df = pd.DataFrame([nueva_fila], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo_df], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Guardado"); st.rerun()

    st.subheader("Lista de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)
    
    elim_c = st.selectbox("Seleccione cliente para eliminar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
    if st.button("❌ ELIMINAR CLIENTE PERMANENTEMENTE") and elim_c != "-":
        st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim_c]
        guardar_datos("clientes", st.session_state.clientes)
        st.success("Cliente eliminado"); st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    if st.session_state.clientes.empty:
        st.warning("Primero cargue un cliente.")
    else:
        with st.form("f_v"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            c1, c2 = st.columns(2)
            f_viaje = c1.date_input("Fecha del Viaje")
            movil = c2.text_input("Patente / Móvil")
            orig = st.text_input("Origen")
            dest = st.text_input("Destino")
            imp = st.number_input("Importe $", min_value=0.0)
            tipo_v = st.selectbox("Tipo de Operación", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("GUARDAR VIAJE"):
                nv = [date.today(), cli, f_viaje, orig, dest, movil, imp, f"Factura ({tipo_v})", "-"]
                nv_df = pd.DataFrame([nv], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv_df], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Viaje guardado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito")
    tipo = st.radio("Acción:", ["Nota de Crédito (Resta)", "Nota de Débito (Suma)"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_afip = st.text_input("Nro Comprobante AFIP Asociado *")
        mot = st.text_input("Concepto / Motivo")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR"):
            final = -monto if "Crédito" in tipo else monto
            t_comp = "NC" if "Crédito" in tipo else "ND"
            nc_row = [date.today(), cl, date.today(), "AJUSTE", mot, "-", final, t_comp, nro_afip]
            nc_df = pd.DataFrame([nc_row], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc_df], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Ajuste registrado"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial y Edición")
    st.write("Haga clic en el botón 🗑️ para eliminar una carga errónea.")
    for i, row in st.session_state.viajes.iloc[::-1].iterrows():
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"**{row['Fecha Viaje']}**")
        c2.write(f"**{row['Cliente']}** | {row['Origen']} -> {row['Destino']} | ${row['Importe']}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
        st.divider()
