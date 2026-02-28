import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, timedelta
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

# Estilos Globales
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

# --- 2. MOTOR DE CONEXIÓN ---
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
        st.error(f"❌ Error de Conexión: {e}")
        return None

def cargar_datos():
    # Definición estricta de columnas para evitar desajustes
    cols = {
        "clientes": ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"],
        "viajes": ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"],
        "presupuestos": ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"],
        "tesoreria": ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"],
        "proveedores": ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"],
        "compras": ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]
    }
    
    sh = conectar_google()
    if not sh: return [pd.DataFrame(columns=c) for c in cols.values()]
    
    resultados = []
    for nombre, columnas in cols.items():
        try:
            ws = sh.worksheet(nombre)
            df = pd.DataFrame(ws.get_all_records())
            if df.empty: df = pd.DataFrame(columns=columnas)
            # Asegurar que los montos sean numéricos
            for col_num in ["Importe", "Monto", "Total", "Neto 21"]:
                if col_num in df.columns:
                    df[col_num] = pd.to_numeric(df[col_num], errors='coerce').fillna(0)
            resultados.append(df)
        except:
            resultados.append(pd.DataFrame(columns=columnas))
    return resultados

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if not sh: return False
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        # Convertir todo a String para Google Sheets y manejar NaN
        df_save = df.copy().fillna("-")
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos)
        return True
    except Exception as e:
        st.error(f"⚠️ Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 3. FUNCIONES DE IMPRESIÓN (HTML) ---
def generar_html_recibo(data):
    return f"""<html><body style='font-family:sans-serif; border:2px solid #5e2d61; padding:20px;'>
    <h2 style='color:#5e2d61; text-align:center;'>RECIBO DE PAGO - CHACAGEST</h2>
    <hr><p><b>Fecha:</b> {data['Fecha']}</p><p><b>Cliente:</b> {data['Cliente/Proveedor']}</p>
    <p><b>Concepto:</b> {data['Concepto']}</p><p><b>Medio:</b> {data['Caja/Banco']}</p>
    <div style='background:#f0f2f6; padding:10px; font-size:20px;'><b>MONTO: $ {abs(data['Monto']):,.2f}</b></div>
    <p style='font-size:10px;'>Asoc. AFIP: {data['Ref AFIP']}</p></body></html>"""

def generar_html_orden_pago(data):
    return f"""<html><body style='font-family:sans-serif; border:2px solid #d35400; padding:20px;'>
    <h2 style='color:#d35400; text-align:center;'>ORDEN DE PAGO - CHACAGEST</h2>
    <hr><p><b>Fecha:</b> {data['Fecha']}</p><p><b>Proveedor:</b> {data['Proveedor']}</p>
    <p><b>Caja:</b> {data['Caja/Banco']}</p><div style='background:#fff4e6; padding:10px; font-size:20px;'>
    <b>TOTAL PAGADO: $ {abs(data['Monto']):,.2f}</b></div></body></html>"""

# --- 4. AUTENTICACIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

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

# --- 5. CARGA DE ESTADO (SESSION STATE) ---
if 'clientes' not in st.session_state:
    dfs = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, \
    st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = dfs

# --- 6. MENÚ LATERAL ---
with st.sidebar:
    st.header("MENÚ PRINCIPAL")
    menu_p = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], 
                         icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0)
    
    sel_sub = None
    if menu_p == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL"], 
                              icons=["people", "truck", "file-text", "person-vcard"], default_index=0)
    elif menu_p == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR"], 
                              icons=["person-plus", "receipt", "person-vcard"], default_index=0)
    
    st.markdown("---")
    if st.button("🔄 Sincronizar Nube"):
        st.session_state.clear()
        st.rerun()

sel = sel_sub if sel_sub else menu_p

# --- 7. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, r in st.session_state.viajes.iterrows():
        if str(r['Fecha Viaje']) != "-" and r['Importe'] > 0:
            eventos.append({"title": f"🚛 {r['Cliente']}", "start": str(r['Fecha Viaje']), "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es"})

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.form("f_cli", clear_on_submit=True):
        c1, c2 = st.columns(2)
        r = c1.text_input("Razón Social *")
        cuit = c2.text_input("CUIT *")
        mail = c1.text_input("Email")
        tel = c2.text_input("Teléfono")
        if st.form_submit_button("REGISTRAR CLIENTE"):
            if r and cuit:
                nueva = pd.DataFrame([[r, cuit, mail, tel, "-", "-", "-", "RI", "CC"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                if guardar_datos("clientes", st.session_state.clientes):
                    st.success("✅ Cliente guardado"); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v", clear_on_submit=True):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha Viaje")
        pat = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            if guardar_datos("viajes", st.session_state.viajes):
                st.success("✅ Viaje registrado"); st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Gestión de Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2, t3, t4 = st.tabs(["🧾 COBRANZA", "💸 ORDEN PAGO", "📥/📤 VARIOS", "📊 SALDOS"])

    with t1:
        if "recibo_html" not in st.session_state: st.session_state.recibo_html = None
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            cj = st.selectbox("Caja", opc_cajas)
            mon = st.number_input("Monto $", min_value=0.0)
            afip = st.text_input("Referencia / Recibo")
            if st.form_submit_button("REGISTRAR COBRANZA"):
                # Registro en Tesorería
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                # Registro en Viajes (Ajuste saldo)
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                
                if guardar_datos("tesoreria", st.session_state.tesoreria) and guardar_datos("viajes", st.session_state.viajes):
                    st.session_state.recibo_html = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Concepto": "Cobro Viaje", "Caja/Banco": cj, "Monto": mon, "Ref AFIP": afip})
                    st.rerun()
        if st.session_state.recibo_html:
            st.success("✅ Cobranza Guardada")
            st.download_button("🖨️ Descargar Recibo", st.session_state.recibo_html, "Recibo.html", "text/html")

    with t2:
        if "op_html" not in st.session_state: st.session_state.op_html = None
        with st.form("f_op"):
            p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cj_p = st.selectbox("Caja Salida", opc_cajas)
            mon_p = st.number_input("Monto Pago $", min_value=0.0)
            if st.form_submit_button("GENERAR ORDEN DE PAGO"):
                nt = pd.DataFrame([[date.today(), "PAGO PROV", cj_p, "Orden Pago", p_sel, -mon_p, "-"]], columns=st.session_state.tesoreria.columns)
                nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO", 0,0,0,0,0,0, -mon_p]], columns=st.session_state.compras.columns)
                
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.compras = pd.concat([st.session_state.compras, nc], ignore_index=True)
                
                if guardar_datos("tesoreria", st.session_state.tesoreria) and guardar_datos("compras", st.session_state.compras):
                    st.session_state.op_html = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Caja/Banco": cj_p, "Monto": mon_p})
                    st.rerun()
        if st.session_state.op_html:
            st.success("✅ Pago Guardado")
            st.download_button("🖨️ Descargar Orden Pago", st.session_state.op_html, "OrdenPago.html", "text/html")

    with t3:
        with st.form("f_var"):
            tipo = st.selectbox("Tipo", ["INGRESO VARIO", "EGRESO VARIO"])
            cj_v = st.selectbox("Caja Movimiento", opc_cajas)
            con_v = st.text_input("Concepto")
            mon_v = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR MOVIMIENTO"):
                m_final = mon_v if "INGRESO" in tipo else -mon_v
                nv = pd.DataFrame([[date.today(), tipo, cj_v, con_v, "Varios", m_final, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nv], ignore_index=True)
                if guardar_datos("tesoreria", st.session_state.tesoreria):
                    st.success("✅ Movimiento registrado"); st.rerun()

    with t4:
        st.subheader("Saldos por Cuenta")
        for cj in opc_cajas:
            saldo = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj]['Monto'].sum()
            st.metric(cj, f"$ {saldo:,.2f}")

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
    st.header("💸 Carga de Gastos (Compras)")
    with st.form("f_com", clear_on_submit=True):
        p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        tipo_f = st.selectbox("Tipo Factura", ["A", "B", "C", "NC", "ND"])
        total = st.number_input("Total Factura $", min_value=0.0)
        if st.form_submit_button("REGISTRAR GASTO"):
            m_final = -total if tipo_f == "NC" else total
            ng = pd.DataFrame([[date.today(), p_sel, "0001", tipo_f, 0, 0, 0, 0, 0, 0, m_final]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            if guardar_datos("compras", st.session_state.compras):
                st.success("✅ Gasto registrado"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Estado de Cuenta Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO PENDIENTE", f"$ {df_cl['Importe'].sum():,.2f}")
    st.dataframe(df_cl, use_container_width=True)

elif sel == "CTA CTE PROVEEDOR":
    st.header("📑 Estado de Cuenta Proveedor")
    pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_pr = st.session_state.compras[st.session_state.compras['Proveedor'] == pr]
    st.metric("SALDO PENDIENTE", f"$ {df_pr['Total'].sum():,.2f}")
    st.dataframe(df_pr, use_container_width=True)
