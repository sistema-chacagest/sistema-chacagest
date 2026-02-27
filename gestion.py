import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y CONEXIÓN (TU CÓDIGO) ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="LOGOCHACA.png", layout="wide")

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
    col_t = ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"] # Nueva para Tesorería
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)

        try:
            ws_t = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)
            
        return df_c, df_v, df_p, df_t
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
        st.error(f"Error al guardar: {e}")
        return False

# --- TUS FUNCIONES PARA REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    html = f"<html><head><style>body {{ font-family: Arial, sans-serif; color: #333; }} .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }} .info {{ margin: 20px 0; font-size: 14px; }} .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }} .tabla th {{ background-color: #f39c12; color: white; padding: 10px; text-align: left; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }} .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }} </style></head><body><div class=\"header\"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Fecha de emisión: {date.today()}</p></div><div class=\"info\"><p><b>Cliente:</b> {cliente}</p></div>{tabla_html}<div class=\"total\"> SALDO TOTAL A LA FECHA: $ {saldo:,.2f} </div></body></html>"
    return html

def generar_html_presupuesto(p_data):
    html = f"<html><head><style>body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }} .header {{ border-bottom: 3px solid #5e2d61; padding-bottom: 10px; margin-bottom: 20px; }} .title {{ color: #5e2d61; font-size: 24px; font-weight: bold; }} .box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-top: 20px; background-color: #f9f9f9; }} .monto {{ font-size: 22px; color: #d35400; font-weight: bold; text-align: right; margin-top: 20px; }} .footer {{ margin-top: 50px; font-size: 11px; color: #777; text-align: center; }} </style></head><body><div class=\"header\"><span class=\"title\">🚛 CHACAGEST - PRESUPUESTO</span><div style=\"float: right; text-align: right; font-size: 12px;\">Emisión: {p_data['Fecha Emisión']}<br>Válido hasta: {p_data['Vencimiento']}</div></div><p><b>Señores:</b> {p_data['Cliente']}</p><p><b>Unidad solicitada:</b> {p_data['Tipo Móvil']}</p><div class=\"box\"><b>Detalle del Servicio:</b><br>{p_data['Detalle']}</div><div class=\"monto\">TOTAL PRESUPUESTADO: $ {p_data['Importe']:,.2f}</div><div class=\"footer\">Este documento es un presupuesto estimativo y no representa una factura ni afecta el estado de cuenta corriente.</div></body></html>"
    return html

def generar_html_recibo(cliente, monto, concepto, afip, cuenta):
    html = f"<html><body style=\"font-family: Arial; border: 2px solid #5e2d61; padding: 40px; width: 600px; margin: auto;\"><h1 style=\"text-align: center; color: #5e2d61;\">RECIBO DE PAGO</h1><p style=\"text-align: right;\"><b>Fecha:</b> {date.today()}</p><hr><p><b>Recibimos de:</b> {cliente}</p><p><b>La cantidad de:</b> $ {monto:,.2f}</p><p><b>En concepto de:</b> {concepto}</p><p><b>Forma de pago:</b> {cuenta}</p><p><b>Comprobante Asociado AFIP:</b> {afip}</p><br><br><div style=\"text-align: center;\"><p>_______________________</p><p>Firma y Sello CHACAGEST</p></div></body></html>"
    return html

# --- 2. LOGIN (TU CÓDIGO) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("LOGOCHACA.png", width=250)
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
if 'clientes' not in st.session_state or 'viajes' not in st.session_state or 'tesoreria' not in st.session_state:
    c, v, p, t = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame(columns=["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"])
    st.session_state.viajes = v if v is not None else pd.DataFrame(columns=["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"])
    st.session_state.presupuestos = p if p is not None else pd.DataFrame(columns=["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"])
    st.session_state.tesoreria = t if t is not None else pd.DataFrame(columns=["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"])

# --- 4. DISEÑO ORIGINAL (TU CÓDIGO) ---
st.markdown("""<style>[data-testid="stSidebarNav"] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; } .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; } </style>""", unsafe_allow_html=True)

# --- 5. SIDEBAR (CON TU ESTRUCTURA PEDIDA) ---
with st.sidebar:
    try: st.image("LOGOCHACA.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "INGRESOS VARIOS", "EGRESOS VARIOS", "COBRANZA DE VIAJE", "SALDO DE CAJAS", "SALDO DE BANCOS"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text", "plus-circle", "dash-circle", "cash-coin", "wallet2", "bank"],
        default_index=0,
        styles={"container": {"background-color": "#f0f2f6"}, "nav-link": {"font-size": "13px", "text-align": "left", "margin":"0px"}, "nav-link-selected": {"background-color": "#5e2d61"}}
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        with st.spinner("Sincronizando..."):
            c, v, p, t = cargar_datos()
            st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
            st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    # CAMBIO: Solo viajes reales (No cobranzas con importe negativo)
    solo_viajes = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in solo_viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "CLIENTES":
    # --- TU CÓDIGO DE CLIENTES (EXPANDER, FORM, TABLA) ---
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2); r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT *")
            mail = c1.text_input("Email"); tel = c2.text_input("Teléfono")
            dir_f = c1.text_input("Dirección Fiscal"); loc = c2.text_input("Localidad")
            prov = c1.text_input("Provincia"); c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.success("Cliente guardado"); st.rerun()
    
    st.subheader("📋 Base de Clientes")
    if not st.session_state.clientes.empty:
        for i, row in st.session_state.clientes.iterrows():
            with st.container():
                c_inf, c_ed, c_el = st.columns([0.7, 0.15, 0.15])
                c_inf.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT / CUIL / DNI *']}")
                if c_el.button("🗑️", key=f"del_cli_{i}"):
                    st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True); guardar_datos("clientes", st.session_state.clientes); st.rerun()
                st.divider()

elif sel == "CARGA VIAJE":
    # --- TU CÓDIGO DE CARGA DE VIAJE ---
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Viaje registrado"); st.rerun()

elif sel == "PRESUPUESTOS":
    # --- TU CÓDIGO DE PRESUPUESTOS (RESTABLECIDO) ---
    st.header("📝 Gestión de Presupuestos")
    tab_crear, tab_historial = st.tabs(["🆕 Crear Presupuesto", "📂 Historial"])
    with tab_crear:
        with st.form("f_presu"):
            p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            p_det = st.text_area("Detalle")
            p_imp = st.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                nuevo_p = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(days=7), p_det, "Minibus", p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, nuevo_p], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    with tab_historial:
        for i, row_p in st.session_state.presupuestos.iterrows():
            st.write(f"**{row_p['Cliente']}** - $ {row_p['Importe']}")
            st.download_button("📄 Descargar PDF", generar_html_presupuesto(row_p), f"Presu_{i}.html", "text/html", key=f"dl_{i}")

elif sel == "CTA CTE INDIVIDUAL":
    # --- TU CÓDIGO DE CTA CTE INDIVIDUAL ---
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind)

elif sel in ["INGRESOS VARIOS", "EGRESOS VARIOS"]:
    st.header(f"💰 {sel}")
    tipo = "INGRESO" if sel == "INGRESOS VARIOS" else "EGRESO"
    with st.form("f_teso"):
        cta = st.selectbox("Caja/Banco", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"])
        conc = st.text_input("Concepto")
        monto = st.number_input("Monto $", min_value=0.0)
        afip = st.text_input("Comprobante AFIP (NC/ND)")
        if st.form_submit_button("REGISTRAR"):
            nt = pd.DataFrame([[date.today(), tipo, conc, monto, cta, afip]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria); st.success("Registrado"); st.rerun()

elif sel == "COBRANZA DE VIAJE":
    st.header("💸 Cobranza de Viaje")
    with st.form("f_cob"):
        cl_c = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        mnt = st.number_input("Monto Cobrado $", min_value=0.0)
        cta = st.selectbox("Destino", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"])
        afip = st.text_input("Comprobante AFIP")
        if st.form_submit_button("REGISTRAR PAGO Y RECIBO"):
            # 1. Descuenta de Cta Cte (Viaje negativo)
            nv = pd.DataFrame([[date.today(), cl_c, date.today(), "COBRANZA", "RECIBO", "-", -mnt, "RECIBO", afip]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            # 2. Entra en Tesorería
            nt = pd.DataFrame([[date.today(), "INGRESO", f"COBRANZA: {cl_c}", mnt, cta, afip]], columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)
            st.success("Cobro realizado.")
            st.download_button("📄 DESCARGAR RECIBO", generar_html_recibo(cl_c, mnt, "Cobranza de Viaje", afip, cta), f"Recibo_{cl_c}.html", "text/html")

elif sel == "SALDO DE CAJAS":
    st.header("🗄️ Saldo de Cajas")
    for c in ["CAJA COTI", "CAJA TATO"]:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == c]
        saldo = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(c, f"$ {saldo:,.2f}")

elif sel == "SALDO DE BANCOS":
    st.header("🏛️ Saldo de Bancos")
    for b in ["BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]:
        df = st.session_state.tesoreria[st.session_state.tesoreria['Cuenta'] == b]
        saldo = df[df['Tipo'] == 'INGRESO']['Monto'].sum() - df[df['Tipo'] == 'EGRESO']['Monto'].sum()
        st.metric(b, f"$ {saldo:,.2f}")
