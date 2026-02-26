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
    columnas_clientes = ["Razón Social", "CUIT/DNI", "Email", "Teléfono", "Dirección", "Localidad", "Provincia", "Condición IVA", "Condición Venta"]
    columnas_viajes = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    
    try:
        sh = conectar_google()
        # Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=columnas_clientes)
        
        # Viajes
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=columnas_viajes)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        
        # Si por algún motivo faltan columnas, las forzamos
        for col in columnas_clientes:
            if col not in df_c.columns: df_c[col] = ""
        for col in columnas_viajes:
            if col not in df_v.columns: df_v[col] = ""
            
        return df_c, df_v
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(columns=columnas_clientes), pd.DataFrame(columns=columnas_viajes)

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

# --- 3. DISEÑO ---
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

# --- 4. FUNCIONES ---
def generar_pdf_ctacte(cliente, df_cliente):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"RESUMEN DE CUENTA - {cliente}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Fecha", 1); pdf.cell(120, 10, "Detalle", 1); pdf.cell(40, 10, "Importe", 1, ln=True)
    pdf.set_font("Arial", "", 9)
    for _, fila in df_cliente.iterrows():
        pdf.cell(30, 8, str(fila['Fecha Viaje']), 1)
        pdf.cell(120, 8, f"{fila['Origen']} a {fila['Destino']}"[:60], 1)
        pdf.cell(40, 8, f"$ {fila['Importe']:.2f}", 1, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 💰 MÓDULO VENTAS")
    sel = option_menu(None, ["CLIENTES", "CARGA VIAJE", "NOTA DE CRÉDITO", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
                      icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"], default_index=0)
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()

# --- 6. MÓDULOS ---
if sel == "CLIENTES":
    st.header("👤 Clientes")
    with st.form("f_cli", clear_on_submit=True):
        r = st.text_input("Razón Social *")
        cuit = st.text_input("CUIT *")
        if st.form_submit_button("REGISTRAR"):
            if r and cuit:
                nuevo = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "Cta Cte"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes)
                st.success("Guardado!"); st.rerun()

    st.dataframe(st.session_state.clientes, use_container_width=True)
    elim = st.selectbox("Borrar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
    if st.button("ELIMINAR") and elim != "-":
        st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim]
        guardar_datos("clientes", st.session_state.clientes)
        st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Carga de Viaje")
    if not st.session_state.clientes.empty:
        with st.form("f_v"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'])
            f = st.date_input("Fecha")
            orig = st.text_input("Origen")
            dest = st.text_input("Destino")
            imp = st.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("GUARDAR"):
                nv = pd.DataFrame([[date.today(), cli, f, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Viaje guardado!"); st.rerun()

elif sel == "NOTA DE CRÉDITO":
    st.header("💳 Ajustes (NC/ND)")
    tipo = st.radio("Tipo:", ["Crédito (Resta)", "Débito (Suma)"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'])
        asoc = st.text_input("Nro Comprobante AFIP Asociado")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            final = -monto if "Crédito" in tipo else monto
            nc_row = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", "Nota de Ajuste", "-", final, "NC/ND", asoc]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc_row], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Ajuste registrado!"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'])
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)
    if not df_ind.empty:
        st.download_button("📥 Descargar PDF", generar_pdf_ctacte(cl, df_ind), f"CtaCte_{cl}.pdf")

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Resumen Global de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    st.dataframe(st.session_state.viajes.iloc[::-1], use_container_width=True)
