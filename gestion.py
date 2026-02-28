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

        try:
            ws_p = sh.worksheet("presupuestos")
            df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except: df_p = pd.DataFrame(columns=col_p)

        try:
            ws_t = sh.worksheet("tesoreria")
            df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
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

# --- FUNCIONES PARA REPORTES HTML ---
def generar_html_recibo(data):
    tipo_titulo = "ORDEN DE PAGO" if data['Monto'] < 0 else "RECIBO DE PAGO"
    monto_mostrar = abs(data['Monto'])
    html = f"""
    <html><head><style>
    body {{ font-family: Arial, sans-serif; padding: 30px; border: 2px solid #5e2d61; }}
    .header {{ text-align: center; border-bottom: 2px solid #5e2d61; margin-bottom: 20px; }}
    .monto-box {{ background: #f0f2f6; padding: 15px; font-size: 20px; font-weight: bold; text-align: center; border: 1px dashed #5e2d61; }}
    </style></head><body>
    <div class="header"><h2>{tipo_titulo} - CHACAGEST</h2></div>
    <p><b>Fecha:</b> {data['Fecha']}</p>
    <p><b>A favor de / Recibido de:</b> {data['Cliente/Proveedor']}</p>
    <p><b>Concepto:</b> {data['Concepto']}</p>
    <p><b>Medio:</b> {data['Caja/Banco']}</p>
    <p><b>Referencia:</b> {data['Ref AFIP']}</p>
    <div class="monto-box">IMPORTE TOTAL: $ {monto_mostrar:,.2f}</div>
    </body></html>
    """
    return html

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

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

if "op_lista" not in st.session_state:
    st.session_state.op_lista = None

# --- 4. DISEÑO ---
st.markdown("""<style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; }
    </style>""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### MENU PRINCIPAL")
    opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
    menu_principal = option_menu(None, opciones_menu, icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0)

    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-text", "person-vcard", "globe", "file-text"])
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"])

    if st.button("🔄 Sincronizar"):
        c, v, p, t, prov, com = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com
        st.rerun()

sel = sel_sub if sel_sub else menu_principal

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    df_v = st.session_state.viajes
    for i, row in df_v[df_v['Importe'] > 0].iterrows():
        if str(row['Fecha Viaje']) != "-":
            eventos.append({
                "id": str(i), 
                "title": f"{row['Cliente']} ({row['Origen']} -> {row['Destino']})", 
                "start": str(row['Fecha Viaje']), 
                "backgroundColor": "#f39c12",
                "extendedProps": {"Patente": row['Patente / Móvil'], "Importe": row['Importe']}
            })
    
    cal = calendar(events=eventos, options={"locale": "es", "selectable": True})
    if cal.get("eventClick"):
        st.info(f"**Detalles del Viaje:**\n\n- **Cliente:** {cal['eventClick']['event']['title']}\n- **Móvil:** {cal['eventClick']['event']['extendedProps']['Patente']}\n- **Importe:** $ {cal['eventClick']['event']['extendedProps']['Importe']}")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA / EDICIÓN DE CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            lista_cli = ["NUEVO"] + list(st.session_state.clientes['Razón Social'].unique())
            elegido = st.selectbox("Seleccionar para editar o dejar NUEVO", lista_cli)
            
            # Valores por defecto si es edición
            datos_prev = st.session_state.clientes[st.session_state.clientes['Razón Social'] == elegido].iloc[0] if elegido != "NUEVO" else None
            
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *", value=datos_prev['Razón Social'] if datos_prev is not None else "")
            cuit = c2.text_input("CUIT *", value=datos_prev['CUIT / CUIL / DNI *'] if datos_prev is not None else "")
            mail = c1.text_input("Email", value=datos_prev['Email'] if datos_prev is not None else "")
            tel = c2.text_input("Teléfono", value=datos_prev['Teléfono'] if datos_prev is not None else "")
            
            btn_col1, btn_col2 = st.columns(2)
            guardar = btn_col1.form_submit_button("REGISTRAR / ACTUALIZAR")
            eliminar = btn_col2.form_submit_button("❌ ELIMINAR CLIENTE")

            if guardar:
                if elegido != "NUEVO":
                    st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elegido]
                nueva_fila = pd.DataFrame([[r, cuit, mail, tel, "-", "-", "-", "RI", "CC"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
            
            if eliminar and elegido != "NUEVO":
                st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elegido]
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Gestión de Proveedores")
    with st.expander("➕ ALTA / EDICIÓN DE PROVEEDOR"):
        with st.form("f_prov", clear_on_submit=True):
            lista_prov = ["NUEVO"] + list(st.session_state.proveedores['Razón Social'].unique())
            elegido_p = st.selectbox("Seleccionar para editar o dejar NUEVO", lista_prov)
            
            datos_p_prev = st.session_state.proveedores[st.session_state.proveedores['Razón Social'] == elegido_p].iloc[0] if elegido_p != "NUEVO" else None
            
            c1, c2 = st.columns(2)
            rs = c1.text_input("Razón Social", value=datos_p_prev['Razón Social'] if datos_p_prev is not None else "")
            doc = c2.text_input("CUIT o DNI", value=datos_p_prev['CUIT/DNI'] if datos_p_prev is not None else "")
            cuenta = c1.selectbox("Cuenta de Gastos", ["COMBUSTIBLE", "REPARACION", "REPUESTO", "VARIOS"])
            
            b1, b2 = st.columns(2)
            if b1.form_submit_button("GUARDAR"):
                if elegido_p != "NUEVO":
                    st.session_state.proveedores = st.session_state.proveedores[st.session_state.proveedores['Razón Social'] != elegido_p]
                np = pd.DataFrame([[rs, doc, cuenta, "RI"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
            
            if b2.form_submit_button("❌ ELIMINAR"):
                if elegido_p != "NUEVO":
                    st.session_state.proveedores = st.session_state.proveedores[st.session_state.proveedores['Razón Social'] != elegido_p]
                    guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    st.dataframe(st.session_state.proveedores, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Viaje registrado")

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2, t3, t4, t5 = st.tabs(["📥 INGRESOS/EGRESOS", "🧾 COBRANZA", "🛡️ ORDEN DE PAGO", "📊 SALDOS", "🔄 TRASPASO"])
    
    with t3:
        st.subheader("🛡️ Nueva Orden de Pago")
        with st.form("f_op", clear_on_submit=True):
            prov_op = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
            cj_op = st.selectbox("Desde", opc_cajas); mon_op = st.number_input("Monto $", min_value=0.0)
            ref_op = st.text_input("Referencia/AFIP"); con_op = st.text_input("Concepto", value="Pago a Proveedor")
            if st.form_submit_button("REGISTRAR PAGO"):
                nt_op = pd.DataFrame([[date.today(), "ORDEN DE PAGO", cj_op, con_op, prov_op, -mon_op, ref_op]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt_op], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                st.session_state.op_lista = {
                    "html": generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": prov_op, "Concepto": con_op, "Caja/Banco": cj_op, "Monto": -mon_op, "Ref AFIP": ref_op}),
                    "nombre": f"OP_{prov_op}_{date.today()}.html"
                }
                st.rerun()
        
        if st.session_state.op_lista:
            st.download_button("🖨️ DESCARGAR ORDEN DE PAGO", st.session_state.op_lista["html"], file_name=st.session_state.op_lista["nombre"], mime="text/html")
            if st.button("Limpiar descarga"): st.session_state.op_lista = None; st.rerun()

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gastos")
    with st.form("f_gasto"):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        c1, c2 = st.columns(2); pv = c1.text_input("Punto Vta"); tipo_f = c2.selectbox("Tipo", ["A", "B", "C", "NC", "ND", "REMITO"])
        n21 = st.number_input("Neto 21"); r_iva = st.number_input("Ret IVA")
        total = (n21 * 1.21) + r_iva
        if tipo_f == "NC": total = -total
        if st.form_submit_button("REGISTRAR COMPROBANTE"):
            ng = pd.DataFrame([[date.today(), prov_sel, pv, tipo_f, n21, 0, r_iva, 0, 0, 0, total]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras); st.rerun()

# --- VISTAS GENERALES ---
elif "CTA CTE" in sel or sel == "COMPROBANTES" or sel == "HISTORICO COMPRAS":
    st.header(f"📊 {sel}")
    if "INDIVIDUAL" in sel:
        cl_f = st.selectbox("Seleccionar", st.session_state.clientes['Razón Social'].unique())
        df_res = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl_f]
        st.metric("Saldo", f"$ {df_res['Importe'].sum():,.2f}")
        st.dataframe(df_res, use_container_width=True)
    elif "GENERAL" in sel:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index() if "PROV" not in sel else st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
        st.table(res)
    else:
        st.dataframe(st.session_state.viajes if sel == "COMPROBANTES" else st.session_state.compras, use_container_width=True)
