import streamlit as st
import pandas as pd
import os
from datetime import date
from streamlit_option_menu import option_menu
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar  # LIBRERÍA NUEVA PARA EL CALENDARIO

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

# --- 2. LOGIN (CON TU DISEÑO) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo_path.png", width=250)
        except: st.title("🚛 CHACAGEST")
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
    st.session_state.clientes, st.session_state.viajes = cargar_datos()

# --- 4. DISEÑO ESTILO CHACAGEST (VIOLETA Y NARANJA) ---
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
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CLIENTES", "CARGA VIAJE", "CALENDARIO", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["people", "truck", "calendar3", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social / Nombre Completo *")
            cuit = c2.text_input("CUIT / CUIL / DNI *")
            mail = c1.text_input("Email")
            tel = c2.text_input("Teléfono")
            dir_f = c1.text_input("Dirección Fiscal")
            loc = c2.text_input("Localidad")
            prov = c1.text_input("Provincia")
            c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Cliente guardado con éxito"); st.rerun()

    st.subheader("📋 Base de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)
    
    with st.expander("🗑️ ELIMINAR CLIENTE"):
        elim_c = st.selectbox("Seleccione cliente a borrar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
        if st.button("BORRAR PERMANENTEMENTE") and elim_c != "-":
            st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim_c]
            guardar_datos("clientes", st.session_state.clientes)
            st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha del Viaje")
        pat = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje registrado correctamente"); st.rerun()

elif sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes Disponibles")
    
    # Preparar eventos para el calendario
    eventos = []
    # Filtrar solo lo que sea 'Factura' para no mezclar con NC/ND en el calendario visual
    df_eventos = st.session_state.viajes[st.session_state.viajes['Tipo Comp'].str.contains("Factura", na=False)]
    
    for i, row in df_eventos.iterrows():
        eventos.append({
            "title": f"🚛 {row['Cliente']} | {row['Origen']}-{row['Destino']}",
            "start": str(row['Fecha Viaje']),
            "end": str(row['Fecha Viaje']),
            "resourceId": i,
            "color": "#5e2d61",
        })

    cal_options = {
        "editable": False,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,dayGridWeek,listWeek",
        },
        "initialView": "dayGridMonth",
        "locale": "es",
    }
    
    state = calendar(events=eventos, options=cal_options, key="viajes_cal")
    
    if state.get("eventClick"):
        st.info(f"Detalle del Viaje: {state['eventClick']['event']['title']}")

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante AFIP Asociado *")
        mot = st.text_input("Motivo / Concepto")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            if nro_asoc:
                val = -monto if "Crédito" in tipo else monto
                t_txt = "NC" if "Crédito" in tipo else "ND"
                nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", mot, "-", val, t_txt, nro_asoc]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Ajuste cargado correctamente"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    st.info("Desde aquí puede revisar y eliminar cargas erróneas.")
    for i, row in st.session_state.viajes.iloc[::-1].iterrows():
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha Viaje']}")
        c2.write(f"👤 **{row['Cliente']}** | {row['Origen']} a {row['Destino']} | **${row['Importe']}**")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
        st.divider()
