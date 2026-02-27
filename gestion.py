import streamlit as st
import pandas as pd
import os
from datetime import date
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
    try:
        sh = conectar_google()
        if sh is None: return [None]*4
        
        # Carga Ventas
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records())
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records())
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        
        # Carga Compras (NUEVO)
        ws_p = sh.worksheet("proveedores")
        df_p = pd.DataFrame(ws_p.get_all_records())
        
        ws_g = sh.worksheet("gastos")
        df_g = pd.DataFrame(ws_g.get_all_records())
        # Convertir columnas numéricas de gastos
        cols_num = ['Neto 21', 'Neto 10', 'Ret IVA', 'Ret Gan', 'Ret IIBB', 'No Gravados', 'Total']
        for col in cols_num:
            if col in df_g.columns:
                df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0)
        
        return df_c, df_v, df_p, df_g
    except:
        return None, None, None, None

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
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 2. LOGIN (Mantenido igual) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # ... (Tu código de login original aquí)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
    st.stop()

# --- 3. INICIALIZACIÓN DE DATOS ---
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.proveedores = p if p is not None else pd.DataFrame()
    st.session_state.gastos = g if g is not None else pd.DataFrame()

# --- 4. SIDEBAR CON DIVISION COMPRAS/VENTAS ---
with st.sidebar:
    st.header("MENU PRINCIPAL")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "VIAJES (VENTAS)", "PROVEEDORES", "GASTOS (COMPRAS)", "CTA CTE", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "person-badge", "cart4", "cash-stack", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    
    if st.button("🔄 Sincronizar Todo"):
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.gastos = cargar_datos()
        st.rerun()

# --- 5. MÓDULOS DE COMPRAS (NUEVOS) ---

if sel == "PROVEEDORES":
    st.header("🏢 Gestión de Proveedores")
    with st.expander("➕ ALTA DE PROVEEDOR"):
        with st.form("f_prov", clear_on_submit=True):
            rz = st.text_input("Razón Social *")
            cuit_p = st.text_input("CUIT / DNI *")
            cta = st.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Otros"])
            cat_iva = st.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento", "Consumidor Final", "Monotributista", "No Inscripto"])
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                new_p = pd.DataFrame([[rz, cuit_p, cta, cat_iva]], columns=["Razón Social", "CUIT", "Cuenta de Gastos", "Categoría IVA"])
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, new_p], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores)
                st.success("Proveedor registrado")
    st.dataframe(st.session_state.proveedores, use_container_width=True)

elif sel == "GASTOS (COMPRAS)":
    st.header("💸 Carga de Gastos / Compras")
    
    tab1, tab2 = st.tabs(["Cargar Factura/Remito", "Notas de Crédito/Débito Prov."])
    
    with tab1:
        with st.form("f_gasto", clear_on_submit=True):
            prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            c1, c2, c3 = st.columns(3)
            ptovta = c1.text_input("Punto de Venta")
            tipo_f = c2.selectbox("Tipo de Factura", ["A", "B", "C", "Remito"])
            f_gasto = c3.date_input("Fecha", date.today())
            
            st.markdown("---")
            col_a, col_b = st.columns(2)
            n21 = col_a.number_input("Neto + 21% IVA (Subtotal)", min_value=0.0)
            n10 = col_b.number_input("Neto + 10.5% IVA (Subtotal)", min_value=0.0)
            
            col_x, col_y, col_z = st.columns(3)
            r_iva = col_x.number_input("Retención IVA", min_value=0.0)
            r_gan = col_y.number_input("Retención Ganancia", min_value=0.0)
            r_iibb = col_z.number_input("Retención IIBB", min_value=0.0)
            no_grav = st.number_input("Conceptos No Gravados", min_value=0.0)
            
            total_g = (n21 * 1.21) + (n10 * 1.105) + r_iva + r_gan + r_iibb + no_grav
            st.metric("TOTAL CALCULADO", f"$ {total_g:,.2f}")
            
            if st.form_submit_button("GUARDAR GASTO"):
                new_g = pd.DataFrame([[f_gasto, prov_sel, ptovta, tipo_f, n21, n10, r_iva, r_gan, r_iibb, no_grav, total_g, "Factura", "-"]], 
                                     columns=st.session_state.gastos.columns)
                st.session_state.gastos = pd.concat([st.session_state.gastos, new_g], ignore_index=True)
                guardar_datos("gastos", st.session_state.gastos)
                st.success("Gasto guardado correctamente")

    with tab2:
        st.subheader("Ajustes de Proveedores")
        with st.form("f_ajuste_p"):
            p_aj = st.selectbox("Proveedor ", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            tipo_aj = st.radio("Tipo", ["Nota de Crédito (Baja Deuda)", "Nota de Débito (Sube Deuda)"], horizontal=True)
            nro_ref = st.text_input("Nro Comprobante AFIP Asociado *")
            monto_aj = st.number_input("Monto Total $", min_value=0.0)
            if st.form_submit_button("REGISTRAR AJUSTE PROVEEDOR"):
                real_monto = -monto_aj if "Crédito" in tipo_aj else monto_aj
                t_comp = "NC" if "Crédito" in tipo_aj else "ND"
                new_aj = pd.DataFrame([[date.today(), p_aj, "0000", tipo_aj, 0, 0, 0, 0, 0, 0, real_monto, t_comp, nro_ref]], 
                                      columns=st.session_state.gastos.columns)
                st.session_state.gastos = pd.concat([st.session_state.gastos, new_aj], ignore_index=True)
                guardar_datos("gastos", st.session_state.gastos)
                st.success("Ajuste de proveedor registrado")

elif sel == "CTA CTE":
    tipo_cta = st.radio("Ver Cuenta Corriente de:", ["Clientes (Ventas)", "Proveedores (Compras)"], horizontal=True)
    
    if tipo_cta == "Clientes (Ventas)":
        # ... (Mantener tu lógica de CTA CTE INDIVIDUAL de clientes aquí)
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
        st.metric("SALDO CLIENTE", f"$ {df_ind['Importe'].sum():,.2f}")
        st.dataframe(df_ind)
        
    else:
        # Lógica para Proveedores
        pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
        df_p = st.session_state.gastos[st.session_state.gastos['Proveedor'] == pr]
        st.metric("DEUDA TOTAL CON PROVEEDOR", f"$ {df_p['Total'].sum():,.2f}")
        st.dataframe(df_p)
        
        st.subheader("Resumen General de Proveedores")
        res_p = st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index()
        st.table(res_p)

elif sel == "COMPROBANTES":
    tipo_hist = st.tabs(["Historial Ventas", "Historial Compras"])
    
    with tipo_hist[0]:
        # Tu código original de historial de viajes
        for i in reversed(st.session_state.viajes.index):
            row = st.session_state.viajes.loc[i]
            st.write(f"📅 {row['Fecha Viaje']} | **{row['Cliente']}** | ${row['Importe']}")
            if st.button("Eliminar Venta", key=f"del_v_{i}"):
                st.session_state.viajes = st.session_state.viajes.drop(i)
                guardar_datos("viajes", st.session_state.viajes)
                st.rerun()

    with tipo_hist[1]:
        # Historial de gastos
        for i in reversed(st.session_state.gastos.index):
            row = st.session_state.gastos.loc[i]
            st.write(f"📅 {row['Fecha']} | **{row['Proveedor']}** | ${row['Total']} | {row['Tipo Comp']}")
            if st.button("Eliminar Gasto", key=f"del_g_{i}"):
                st.session_state.gastos = st.session_state.gastos.drop(i)
                guardar_datos("gastos", st.session_state.gastos)
                st.rerun()

# --- Módulos originales (CALENDARIO, CLIENTES, VIAJES) se mantienen igual ---
# ... (Copiar el resto de tu lógica original de CALENDARIO y CLIENTES)
