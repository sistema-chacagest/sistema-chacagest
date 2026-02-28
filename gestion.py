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
    # Estructura de columnas fija para evitar errores de desajuste
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_compras = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]

    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None, None
        
        # Carga de cada hoja con fallback a DF vacío si no existe
        def leer_hoja(nombre, columnas):
            try:
                ws = sh.worksheet(nombre)
                datos = ws.get_all_records()
                df = pd.DataFrame(datos)
                return df if not df.empty else pd.DataFrame(columns=columnas)
            except:
                return pd.DataFrame(columns=columnas)

        df_c = leer_hoja("clientes", col_c)
        df_v = leer_hoja("viajes", col_v)
        df_p = leer_hoja("presupuestos", col_p)
        df_t = leer_hoja("tesoreria", col_t)
        df_prov = leer_hoja("proveedores", col_prov)
        df_com = leer_hoja("compras", col_compras)

        # Limpieza de datos numéricos para que no fallen las operaciones
        for df, col_num in [(df_v, 'Importe'), (df_p, 'Importe'), (df_t, 'Monto'), (df_com, 'Total')]:
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors='coerce').fillna(0)
            
        return df_c, df_v, df_p, df_t, df_prov, df_com
    except:
        return None, None, None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        # IMPORTANTE: Convertimos todo a String para que Google Sheets no rechace formatos
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except Exception as e:
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- FUNCIONES PARA REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>.header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background-color: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }}</style></head><body><div class='header'><h1>Resumen: {cliente}</h1></div>{tabla_html}<h3>SALDO: $ {saldo:,.2f}</h3></body></html>"

def generar_html_recibo(data):
    return f"<html><body style='font-family: Arial; border: 2px solid #5e2d61; padding: 20px;'><h2 style='color:#5e2d61'>RECIBO - CHACAGEST</h2><p><b>Fecha:</b> {data['Fecha']}</p><p><b>Cliente:</b> {data['Cliente/Proveedor']}</p><p><b>Monto:</b> $ {abs(data['Monto']):,.2f}</p><p>Ref: {data['Ref AFIP']}</p></body></html>"

def generar_html_orden_pago(data):
    return f"<html><body style='font-family: Arial; border: 2px solid #d35400; padding: 20px;'><h2 style='color:#d35400'>ORDEN DE PAGO</h2><p><b>Fecha:</b> {data['Fecha']}</p><p><b>Proveedor:</b> {data['Proveedor']}</p><p><b>Monto:</b> $ {abs(data['Monto']):,.2f}</p></body></html>"

def generar_html_presupuesto(p_data):
    return f"<html><body style='font-family: Arial; padding: 40px;'><h1 style='color:#5e2d61'>PRESUPUESTO</h1><hr><p><b>Cliente:</b> {p_data['Cliente']}</p><p><b>Detalle:</b> {p_data['Detalle']}</p><h2>TOTAL: $ {p_data['Importe']:,.2f}</h2></body></html>"

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t
    st.session_state.proveedores = prov
    st.session_state.compras = com

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
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("MENÚ")
    menu_principal = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0)
    
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-text", "person-vcard", "globe", "file-text"], default_index=0)
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"], default_index=0)

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.session_state.clear()
        st.rerun()
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.rerun()

sel = sel_sub if sel_sub else menu_principal

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Importe'] > 0:
            eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es"})

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE", expanded=True):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *")
            cuit = c2.text_input("CUIT *")
            mail = c1.text_input("Email")
            tel = c2.text_input("Teléfono")
            loc = c1.text_input("Localidad")
            prov = c2.text_input("Provincia")
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, "-", loc, prov, "RI", "CC"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    if guardar_datos("clientes", st.session_state.clientes):
                        st.success("✅ Guardado correctamente")
                        st.rerun()
    st.subheader("📋 Base de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            if guardar_datos("viajes", st.session_state.viajes):
                st.success("✅ Viaje guardado"); st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Gestión de Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2, t3, t4 = st.tabs(["📥 INGRESOS/EGRESOS", "🧾 COBRANZA", "📊 SALDOS", "💸 ORDEN PAGO"])
    
    with t1:
        with st.form("f_teso_var", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["INGRESO VARIO", "EGRESO VARIO"])
            cj = st.selectbox("Caja", opc_cajas)
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR"):
                m_final = mon if "INGRESO" in tipo else -mon
                nt = pd.DataFrame([[date.today(), tipo, cj, con, "Varios", m_final, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                if guardar_datos("tesoreria", st.session_state.tesoreria):
                    st.success("✅ Movimiento guardado"); st.rerun()

    with t2:
        if "recibo_html" not in st.session_state: st.session_state.recibo_html = None
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            cj = st.selectbox("Caja Destino", opc_cajas)
            mon = st.number_input("Importe Recibido $", min_value=0.0)
            afip = st.text_input("Ref AFIP / Comprobante")
            if st.form_submit_button("GENERAR COBRANZA"):
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                if guardar_datos("tesoreria", st.session_state.tesoreria) and guardar_datos("viajes", st.session_state.viajes):
                    st.session_state.recibo_html = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Monto": mon, "Ref AFIP": afip})
                    st.rerun()
        if st.session_state.recibo_html:
            st.download_button("🖨️ Imprimir Recibo", st.session_state.recibo_html, "Recibo.html", "text/html")

    with t3:
        for caja in opc_cajas:
            s = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == caja]['Monto'].sum()
            st.metric(caja, f"$ {s:,.2f}")

    with t4:
        if "op_html" not in st.session_state: st.session_state.op_html = None
        with st.form("f_op"):
            p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cj_p = st.selectbox("Caja Pago", opc_cajas)
            mon_p = st.number_input("Monto Pago $", min_value=0.0)
            if st.form_submit_button("GENERAR ORDEN DE PAGO"):
                nt = pd.DataFrame([[date.today(), "PAGO PROV", cj_p, "Orden Pago", p_sel, -mon_p, "-"]], columns=st.session_state.tesoreria.columns)
                nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO", 0,0,0,0,0,0, -mon_p]], columns=st.session_state.compras.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.compras = pd.concat([st.session_state.compras, nc], ignore_index=True)
                if guardar_datos("tesoreria", st.session_state.tesoreria) and guardar_datos("compras", st.session_state.compras):
                    st.session_state.op_html = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Monto": mon_p})
                    st.rerun()
        if st.session_state.op_html:
            st.download_button("🖨️ Descargar Orden de Pago", st.session_state.op_html, "OP.html", "text/html")

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Gestión de Proveedores")
    with st.form("f_prov", clear_on_submit=True):
        rs = st.text_input("Razón Social")
        doc = st.text_input("CUIT/DNI")
        if st.form_submit_button("REGISTRAR PROVEEDOR"):
            np = pd.DataFrame([[rs, doc, "VARIOS", "RI"]], columns=st.session_state.proveedores.columns)
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
            if guardar_datos("proveedores", st.session_state.proveedores):
                st.success("✅ Proveedor registrado"); st.rerun()

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gastos")
    with st.form("f_gasto", clear_on_submit=True):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        c1, c2 = st.columns(2)
        tipo_f = c1.selectbox("Tipo Factura", ["A", "B", "C", "NC", "ND"])
        total = c2.number_input("Total $", min_value=0.0)
        if st.form_submit_button("REGISTRAR GASTO"):
            m_final = -total if tipo_f == "NC" else total
            ng = pd.DataFrame([[date.today(), prov_sel, "0001", tipo_f, 0, 0, 0, 0, 0, 0, m_final]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            if guardar_datos("compras", st.session_state.compras):
                st.success("✅ Gasto guardado"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO PENDIENTE", f"$ {df_cl['Importe'].sum():,.2f}")
    st.dataframe(df_cl, use_container_width=True)

elif sel == "CTA CTE PROVEEDOR":
    st.header("📑 Cuenta Corriente Proveedor")
    pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_pr = st.session_state.compras[st.session_state.compras['Proveedor'] == pr]
    st.metric("SALDO PENDIENTE", f"$ {df_pr['Total'].sum():,.2f}")
    st.dataframe(df_pr, use_container_width=True)

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    with st.form("f_pre"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        det = st.text_area("Detalle")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR PRESUPUESTO"):
            np = pd.DataFrame([[date.today(), cli, date.today() + timedelta(days=7), det, "Combi", imp]], columns=st.session_state.presupuestos.columns)
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
            if guardar_datos("presupuestos", st.session_state.presupuestos):
                st.success("✅ Presupuesto registrado"); st.rerun()

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Viajes/Comprobantes")
    st.dataframe(st.session_state.viajes, use_container_width=True)

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Historial de Compras")
    st.dataframe(st.session_state.compras, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.dataframe(res, use_container_width=True)

elif sel == "CTA CTE GENERAL PROV":
    st.header("🌎 Estado Global Proveedores")
    res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
    st.dataframe(res_p, use_container_width=True)
