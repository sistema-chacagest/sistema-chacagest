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
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # ... (resto de las cargas igual a tu código original)
        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except: df_p = pd.DataFrame(columns=col_p)

        try:
            ws_t = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except: df_t = pd.DataFrame(columns=col_t)

        try:
            ws_prov = sh.worksheet("proveedores")
            df_prov = pd.DataFrame(ws_prov.get_all_records()) if ws_prov.get_all_records() else pd.DataFrame(columns=col_prov)
        except: df_prov = pd.DataFrame(columns=col_prov)

        try:
            ws_com = sh.worksheet("compras")
            df_com = pd.DataFrame(ws_com.get_all_records()) if ws_com.get_all_records() else pd.DataFrame(columns=col_compras)
            for c in ["Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]:
                df_com[c] = pd.to_numeric(df_com[c], errors='coerce').fillna(0)
        except: df_com = pd.DataFrame(columns=col_compras)
            
        return df_c, df_v, df_p, df_t, df_prov, df_com
    except:
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

# --- (GENERACIÓN DE HTML: SE MANTIENE IGUAL A TU CÓDIGO) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    html = f"<html>...</html>" # (Simplificado para brevedad, mantener tu código original aquí)
    return html

def generar_html_recibo(data):
    html = f"<html>...</html>" # (Mantener tu código original aquí)
    return html

def generar_html_presupuesto(p_data):
    html = f"<html>...</html>" # (Mantener tu código original aquí)
    return html

# --- 2. LOGIN ---
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
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.tesoreria = t if t is not None else pd.DataFrame()
    st.session_state.proveedores = prov if prov is not None else pd.DataFrame()
    st.session_state.compras = com if com is not None else pd.DataFrame()

# --- 4. DISEÑO ORIGINAL ---
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # (Mantener tus estilos)

# --- 5. SIDEBAR (MENÚ) ---
# (Se mantiene exactamente igual a tu código original)
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
    iconos_menu = ["calendar3", "cart4", "bag-check", "safe"]
    menu_principal = option_menu(menu_title=None, options=opciones_menu, icons=iconos_menu, default_index=0, key="menu_p", 
                                 styles={"nav-link-selected": {"background-color": "#5e2d61"}})
    
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(menu_title=None, options=["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"], key="menu_s")
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(menu_title=None, options=["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"], key="menu_c")

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, t, prov, com = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

sel = sel_sub if menu_principal in ["VENTAS", "COMPRAS"] else menu_principal

# --- 6. MÓDULOS ---

# (CALENDARIO, CLIENTES: IGUAL A TU CÓDIGO)

if sel == "CARGA VIAJE":
    st.header("🚛 Registro de Comprobante de Venta")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha")
        pat = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        
        c3, c4 = st.columns(2)
        imp = c3.number_input("Importe Neto $", min_value=0.0)
        # AJUSTE: Selección de tipo de comprobante para asociar
        tipo_c = c4.selectbox("Tipo de Comprobante", ["Factura", "Nota de Crédito", "Nota de Débito"])
        
        # AJUSTE: Referencia a comprobante original
        ref_afip = st.text_input("Nro. Comprobante / Ref. AFIP")
        
        if st.form_submit_button("GUARDAR"):
            # Lógica de signos: Nota de crédito resta
            final_imp = -imp if tipo_c == "Nota de Crédito" else imp
            
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, final_imp, tipo_c, ref_afip]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success(f"{tipo_c} registrada correctamente")
            st.rerun()

# (PRESUPUESTOS, TESORERIA, CTA CTE: SE MANTIENEN IGUAL)
# Solo asegúrate que en TESORERIA -> COBRANZA VIAJE, el campo "Ref AFIP" siga pidiendo el número.

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gastos (Compras)")
    with st.form("f_gasto", clear_on_submit=True):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2 = st.columns(2)
        pv = c1.text_input("Punto de Venta / Nro")
        tipo_f = c2.selectbox("Tipo de Factura", ["A", "B", "C", "REMITO", "NOTA DE CREDITO", "NOTA DE DEBITO"])
        c3, c4 = st.columns(2)
        n21 = c3.number_input("Importe Neto (21%)", min_value=0.0)
        n10 = c4.number_input("Importe Neto (10.5%)", min_value=0.0)
        c5, c6, c7 = st.columns(3)
        r_iva = c5.number_input("Retención IVA", min_value=0.0)
        r_gan = c6.number_input("Retención Ganancia", min_value=0.0)
        r_iibb = c7.number_input("Retención IIBB", min_value=0.0)
        nograv = st.number_input("Conceptos No Gravados", min_value=0.0)
        
        total = (n21 * 1.21) + (n10 * 1.105) + r_iva + r_gan + r_iibb + nograv
        
        # AJUSTE: Nota de Crédito en Compras también resta
        if tipo_f == "NOTA DE CREDITO":
            total = -abs(total)
        
        if st.form_submit_button("REGISTRAR COMPROBANTE"):
            ng = pd.DataFrame([[date.today(), prov_sel, pv, tipo_f, n21, n10, r_iva, r_gan, r_iibb, nograv, total]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras)
            st.success(f"Gasto guardado por total de $ {total:,.2f}")
            st.rerun()

# (RESTO DE LOS MÓDULOS CTA CTE PROV, HISTORICO: IGUAL A TU CÓDIGO)
