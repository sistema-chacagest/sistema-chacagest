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
        # Cargar Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        # Cargar Viajes
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        
        return df_c, df_v
    except Exception as e:
        st.error(f"Error de conexión: {e}")
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

# --- 3. DISEÑO VISUAL ORIGINAL ---
st.markdown(f"""
    <style>
    [data-testid="stSidebarNav"] {{ display: none; }}
    header {{ visibility: hidden; }} 
    [data-testid="stSidebarUserContent"] {{ padding-top: 0rem !important; margin-top: -85px !important; }}
    h1, h2, h3 {{ color: #5e2d61 !important; }}
    div.stButton > button {{
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCIONES PDF ---
def generar_pdf_ctacte(cliente, df_cliente):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(94, 45, 97)
    pdf.cell(0, 10, f"RESUMEN DE CUENTA CORRIENTE", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True, align="L")
    pdf.cell(0, 10, f"Fecha: {date.today().strftime('%d/%m/%Y')}", ln=True, align="L")
    pdf.ln(5)
    pdf.set_fill_color(243, 156, 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(25, 10, "Fecha", 1, 0, "C", True)
    pdf.cell(115, 10, "Detalle / Concepto", 1, 0, "C", True)
    pdf.cell(35, 10, "Importe", 1, 1, "C", True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    total = 0
    for _, fila in df_cliente.iterrows():
        detalle = str(fila['Destino']) if fila['Origen'] == "AJUSTE" else f"{fila['Origen']} a {fila['Destino']}"
        pdf.cell(25, 8, str(fila['Fecha Viaje']), 1, 0, "C")
        pdf.cell(115, 8, detalle[:65], 1, 0, "L")
        pdf.cell(35, 8, f"$ {fila['Importe']:,.2f}", 1, 1, "R")
        total += fila['Importe']
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(140, 10, "SALDO TOTAL:", 0, 0, "R")
    pdf.cell(35, 10, f"$ {total:,.2f}", 1, 1, "R")
    return pdf.output(dest='S').encode('latin-1')

# --- 5. SIDEBAR CON TU MENÚ ---
with st.sidebar:
    st.markdown("### 💰 MÓDULO VENTAS")
    sel = option_menu(
        menu_title=None,
        options=["CLIENTES", "CARGA VIAJE", "NOTA DE CRÉDITO", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes = cargar_datos()
        st.rerun()
    st.caption(f"CHACAGEST v4.0 (Cloud) | {date.today().strftime('%d/%m/%Y')}")

# --- 6. LÓGICA DE MÓDULOS ---
if sel == "CLIENTES":
    st.header("👤 Gestión Integral de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cliente_full", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                r = st.text_input("Razón Social / Nombre Completo *")
                cuit = st.text_input("CUIT / CUIL / DNI *")
                cond_iva = st.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
                e = st.text_input("Email")
                tel = st.text_input("Teléfono")
            with c2:
                dir_f = st.text_input("Dirección Fiscal")
                loc = st.text_input("Localidad")
                prov = st.text_input("Provincia")
                cond_v = st.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado", "7 días", "15 días"])
            
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nuevo = pd.DataFrame([[r, cuit, e, tel, dir_f, loc, prov, cond_iva, cond_v]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Cliente guardado!"); st.rerun()

    st.subheader("📋 Lista de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)
    
    elim_c = st.selectbox("Eliminar Cliente:", ["Seleccione..."] + list(st.session_state.clientes['Razón Social'].unique()))
    if st.button("ELIMINAR CLIENTE") and elim_c != "Seleccione...":
        st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim_c]
        guardar_datos("clientes", st.session_state.clientes)
        st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_viaje"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha de Viaje")
        movil = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, movil, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje guardado!"); st.rerun()

elif sel == "NOTA DE CRÉDITO":
    st.header("💳 Notas de Crédito / Débito")
    t_ajuste = st.radio("Tipo:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'])
        c1, c2 = st.columns(2)
        nro_afip = c1.text_input("Nro Comprobante AFIP")
        asoc = c2.text_input("Factura Asociada")
        mot = st.text_input("Motivo")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            es_nc = "Crédito" in t_ajuste
            final = -monto if es_nc else monto
            tipo_txt = "NC" if es_nc else "ND"
            nc_row = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", f"{tipo_txt}: {mot}", "-", final, tipo_txt, asoc]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc_row], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Ajuste registrado!"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'])
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    if not df_ind.empty:
        st.download_button("📥 PDF", generar_pdf_ctacte(cl, df_ind), f"CtaCte_{cl}.pdf")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    for i, row in st.session_state.viajes.iloc[::-1].iterrows():
        with st.container():
            col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
            color = "red" if float(row['Importe']) < 0 else "green"
            col1.write(f"**{row['Fecha Viaje']}**")
            col2.markdown(f"**{row['Cliente']}** | {row['Tipo Comp']} | <span style='color:{color}; font-weight:bold;'>$ {float(row['Importe']):,.2f}</span>", unsafe_allow_html=True)
            if col3.button("🗑️", key=f"del_{i}"):
                st.session_state.viajes = st.session_state.viajes.drop(i).reset_index(drop=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.rerun()
            st.divider()
