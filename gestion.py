import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

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
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_compras = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]

    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        ws_p = sh.worksheet("presupuestos")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
        
        ws_t = sh.worksheet("tesoreria")
        df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
        df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)

        ws_prov = sh.worksheet("proveedores")
        df_prov = pd.DataFrame(ws_prov.get_all_records()) if ws_prov.get_all_records() else pd.DataFrame(columns=col_prov)

        ws_com = sh.worksheet("compras")
        df_com = pd.DataFrame(ws_com.get_all_records()) if ws_com.get_all_records() else pd.DataFrame(columns=col_compras)
        
        # Corrección de tipos numéricos para Compras
        for col in ["Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]:
            if col in df_com.columns:
                df_com[col] = pd.to_numeric(df_com[col], errors='coerce').fillna(0)
            
        return df_c, df_v, df_p, df_t, df_prov, df_com
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None, None, None, None, None, None

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

# --- 2. LOGIN Y SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t
    st.session_state.proveedores = prov
    st.session_state.compras = com

# --- 3. SIDEBAR ---
with st.sidebar:
    menu_principal = option_menu(
        menu_title="CHACAGEST",
        options=["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"],
        icons=["calendar3", "cart4", "bag-check", "safe"],
        default_index=0
    )
    
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "CTA CTE INDIVIDUAL"], icons=["people", "truck", "person-vcard"])
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "clock-history"])

    if st.button("🔄 Sincronizar"):
        st.session_state.clear()
        st.rerun()

sel = sel_sub if sel_sub else menu_principal

# --- 4. MÓDULOS ---

if sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v", clear_on_submit=True):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha")
        pat = st.text_input("Patente")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje registrado")
            st.rerun()

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gasto (Total Automático)")
    with st.form("f_gasto", clear_on_submit=True):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        c1, c2 = st.columns(2)
        pv = c1.text_input("Punto de Venta")
        tipo_f = c2.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Nota de Crédito", "Nota de Débito"])
        
        st.subheader("Importes")
        g1, g2 = st.columns(2)
        n21 = g1.number_input("Neto 21% $", min_value=0.0)
        n10 = g2.number_input("Neto 10.5% $", min_value=0.0)
        
        r1, r2, r3 = st.columns(3)
        r_iva = r1.number_input("Ret. IVA $", min_value=0.0)
        r_gan = r2.number_input("Ret. Ganancias $", min_value=0.0)
        r_iibb = r3.number_input("Ret. IIBB $", min_value=0.0)
        nograv = st.number_input("No Gravados / Otros $", min_value=0.0)

        # CÁLCULO DEL TOTAL (Neto + IVA + Retenciones + No Gravados)
        total = (n21 * 1.21) + (n10 * 1.105) + r_iva + r_gan + r_iibb + nograv
        if "Nota de Crédito" in tipo_f: total = -total

        st.markdown(f"### **TOTAL A REGISTRAR: $ {total:,.2f}**")
        
        if st.form_submit_button("REGISTRAR COMPROBANTE"):
            ng = pd.DataFrame([[date.today(), prov_sel, pv, tipo_f, n21, n10, r_iva, r_gan, r_iibb, nograv, total]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras)
            st.success(f"Gasto guardado por $ {total:,.2f}")
            st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    t1, t2 = st.tabs(["📥 INGRESO", "📤 EGRESO"])
    with t1:
        with st.form("f_ing", clear_on_submit=True):
            f = st.date_input("Fecha", date.today())
            cj = st.selectbox("Caja", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA"])
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR INGRESO"):
                nt = pd.DataFrame([[f, "INGRESO VARIO", cj, con, "Varios", mon, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                st.success("Ingreso registrado")
                st.rerun()

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Historial de Compras")
    st.dataframe(st.session_state.compras, use_container_width=True)

elif sel == "CLIENTES":
    st.header("👥 Gestión de Clientes")
    with st.form("f_nuevo_cli", clear_on_submit=True):
        rs = st.text_input("Razón Social")
        cuit = st.text_input("CUIT")
        if st.form_submit_button("Agregar Cliente"):
            nc = pd.DataFrame([[rs, cuit, "-", "-", "-", "-", "-", "-", "-"]], columns=st.session_state.clientes.columns)
            st.session_state.clientes = pd.concat([st.session_state.clientes, nc], ignore_index=True)
            guardar_datos("clientes", st.session_state.clientes)
            st.rerun()
    st.table(st.session_state.clientes[["Razón Social", "CUIT / CUIL / DNI *"]])
