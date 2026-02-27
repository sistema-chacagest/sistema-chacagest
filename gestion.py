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
    # Estructuras de columnas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_prov = ["Razón Social", "CUIT / DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_gastos = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "IVA 21", "Neto 10.5", "IVA 10.5", "Ret IVA", "Ret Gan", "Ret IIBB", "No Gravados", "Total"]

    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Carga Clientes y Viajes
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Carga Proveedores y Gastos (Compras)
        try:
            ws_p = sh.worksheet("proveedores")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_prov)
        except: df_p = pd.DataFrame(columns=col_prov)

        try:
            ws_g = sh.worksheet("gastos")
            df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_gastos)
            df_g['Total'] = pd.to_numeric(df_g['Total'], errors='coerce').fillna(0)
        except: df_g = pd.DataFrame(columns=col_gastos)

        return df_c, df_v, df_p, df_g
    except:
        return None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        try:
            ws = sh.worksheet(nombre_hoja)
        except:
            ws = sh.add_worksheet(title=nombre_hoja, rows="100", cols="20")
        
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except Exception as e:
        st.error(f"Error al guardar {nombre_hoja}: {e}")
        return False

# --- 2. LOGIN Y ESTADO ---
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

if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.proveedores = p
    st.session_state.gastos = g

# --- 4. DISEÑO ---
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
    
    if 'menu_actual' not in st.session_state:
        st.session_state.menu_actual = "CALENDARIO"

    if st.button("📅 CALENDARIO", use_container_width=True):
        st.session_state.menu_actual = "CALENDARIO"

    with st.expander("💰 VENTA", expanded=(st.session_state.menu_actual in ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"])):
        sel_venta = option_menu(
            menu_title=None,
            options=["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
            icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
            default_index=0, key="venta_menu"
        )
        if st.session_state.menu_actual != "CALENDARIO" and sel_venta:
            st.session_state.menu_actual = sel_venta

    with st.expander("🛒 COMPRAS", expanded=(st.session_state.menu_actual in ["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV IND", "CTA CTE PROV GEN", "HISTORICO GASTOS"])):
        sel_compra = option_menu(
            menu_title=None,
            options=["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV IND", "CTA CTE PROV GEN", "HISTORICO GASTOS"],
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "diagram-3", "archive"],
            default_index=0, key="compra_menu"
        )
        if st.session_state.menu_actual != "CALENDARIO" and sel_compra:
            st.session_state.menu_actual = sel_compra

    sel = st.session_state.menu_actual

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes = c, v
        st.session_state.proveedores, st.session_state.gastos = p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS VENTAS (ORIGINALES) ---
if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600}, key="cal_final")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.form("f_cli"):
        c1, c2 = st.columns(2)
        r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT / CUIL / DNI *")
        iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
        if st.form_submit_button("REGISTRAR CLIENTE"):
            nf = pd.DataFrame([[r, cuit, "", "", "", "", "", iva, "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
            st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
            guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("Register Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        imp = st.number_input("Importe", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, date.today(), "", "", "", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (Ventas)")
    st.info("Asociar ajuste a comprobante AFIP.")
    # (Lógica original de NC/ND de ventas)

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Ventas")
    st.dataframe(st.session_state.viajes)

# --- 7. MÓDULOS COMPRAS (NUEVOS) ---

elif sel == "PROVEEDORES":
    st.header("🏢 Carga de Proveedores")
    with st.form("f_prov"):
        c1, c2 = st.columns(2)
        rz = c1.text_input("Razón Social *")
        doc = c2.text_input("CUIT o DNI *")
        gasto_tipo = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Otros"])
        cat_iva = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
        if st.form_submit_button("GUARDAR PROVEEDOR"):
            if rz and doc:
                new_p = pd.DataFrame([[rz, doc, gasto_tipo, cat_iva]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, new_p], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.success("Proveedor Guardado"); st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("🧾 Carga de Gastos")
    with st.form("f_gasto"):
        prov = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2, c3 = st.columns(3)
        ptovta = c1.text_input("Punto de Venta")
        tfac = c2.selectbox("Tipo de Factura", ["A", "B", "C", "Remito"])
        fec = c3.date_input("Fecha")
        
        st.markdown("### Desglose de Importes")
        colA, colB = st.columns(2)
        n21 = colA.number_input("Neto al 21%", min_value=0.0)
        n10 = colB.number_input("Neto al 10.5%", min_value=0.0)
        
        r_iva = colA.number_input("Retención IVA", min_value=0.0)
        r_gan = colB.number_input("Retención Ganancia", min_value=0.0)
        r_iibb = colA.number_input("Retención IIBB", min_value=0.0)
        no_grav = colB.number_input("Conceptos No Gravados", min_value=0.0)
        
        iva21 = n21 * 0.21
        iva10 = n10 * 0.105
        total_calc = n21 + iva21 + n10 + iva10 + r_iva + r_gan + r_iibb + no_grav
        
        st.subheader(f"IMPORTE TOTAL: $ {total_calc:,.2f}")
        
        if st.form_submit_button("REGISTRAR COMPRA"):
            ng = pd.DataFrame([[fec, prov, ptovta, tfac, n21, iva21, n10, iva10, r_iva, r_gan, r_iibb, no_grav, total_calc]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.success("Gasto Cargado"); st.rerun()

elif sel == "AJUSTES COMPRAS":
    st.header("📉 Ajustes Proveedores (NC/ND)")
    with st.form("f_adj_p"):
        p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        t = st.radio("Tipo", ["Nota de Crédito (Baja Deuda)", "Nota de Débito (Sube Deuda)"])
        monto = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("CARGAR AJUSTE"):
            final_m = -monto if "Crédito" in t else monto
            adj = pd.DataFrame([[date.today(), p, "AJUSTE", t, 0, 0, 0, 0, 0, 0, 0, 0, final_m]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, adj], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "CTA CTE PROV IND":
    st.header("📖 Cuenta Corriente Individual Proveedor")
    p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.gastos[st.session_state.gastos['Proveedor'] == p]
    st.metric("DEUDA TOTAL", f"$ {df_p['Total'].sum():,.2f}")
    st.dataframe(df_p)

elif sel == "CTA CTE PROV GEN":
    st.header("📊 Saldo General de Proveedores")
    res_p = st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index()
    st.table(res_p)

elif sel == "HISTORICO GASTOS":
    st.header("📂 Histórico de Comprobantes de Compras")
    st.info("Haga clic en el botón de basura para eliminar errores.")
    for i in reversed(st.session_state.gastos.index):
        row = st.session_state.gastos.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha']}")
        c2.write(f"🏢 **{row['Proveedor']}** | Fact: {row['Tipo Factura']} | **TOTAL: ${row['Total']}**")
        if c3.button("🗑️", key=f"del_g_{i}"):
            st.session_state.gastos = st.session_state.gastos.drop(i)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()
        st.divider()
