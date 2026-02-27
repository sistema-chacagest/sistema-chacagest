import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y CONEXIÓN (TU LÓGICA ORIGINAL) ---
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
    # Mantenemos tus columnas originales exactas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    # Columnas nuevas para compras (sin tocar las anteriores)
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_comp = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None
        
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
        except: df_p = pd.DataFrame(columns=col_p)

        try:
            ws_prov = sh.worksheet("proveedores")
            df_prov = pd.DataFrame(ws_prov.get_all_records())
        except: df_prov = pd.DataFrame(columns=col_prov)

        try:
            ws_comp = sh.worksheet("compras")
            df_comp = pd.DataFrame(ws_comp.get_all_records())
        except: df_comp = pd.DataFrame(columns=col_comp)
            
        return df_c, df_v, df_p, df_prov, df_comp
    except:
        return None, None, None, None, None

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
    except: return False

# --- FUNCIONES DE REPORTES HTML (TU CÓDIGO ORIGINAL RECUPERADO) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""<html><head><style>body {{ font-family: Arial; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }} .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }} .tabla th {{ background: #f39c12; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }} .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; }}</style></head><body><div class="header"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Cliente: {cliente}</p></div>{tabla_html}<div class="total">SALDO TOTAL: $ {saldo:,.2f}</div></body></html>"""

def generar_html_presupuesto(p_data):
    return f"""<html><head><style>body {{ font-family: Arial; padding: 40px; }} .header {{ border-bottom: 3px solid #5e2d61; }} .title {{ color: #5e2d61; font-size: 24px; font-weight: bold; }} .box {{ border: 1px solid #ddd; padding: 15px; background: #f9f9f9; }} .monto {{ font-size: 22px; color: #d35400; font-weight: bold; text-align: right; }}</style></head><body><div class="header"><span class="title">🚛 CHACAGEST - PRESUPUESTO</span></div><p><b>Señores:</b> {p_data['Cliente']}</p><p><b>Unidad:</b> {p_data['Tipo Móvil']}</p><div class="box"><b>Detalle:</b><br>{p_data['Detalle']}</div><div class="monto">TOTAL: $ {float(p_data['Importe']):,.2f}</div></body></html>"""

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo_path.png", width=250)
        except: st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026": st.session_state.autenticado = True; st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, prov, comp = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = c, v, p, prov, comp

# --- 4. DISEÑO Y ESTÉTICA (TUYA ORIGINAL) ---
st.markdown("<style>[data-testid='stSidebarNav'] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "MODULO VENTAS", "MODULO COMPRAS"],
        icons=["calendar3", "cash-stack", "cart-check"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = cargar_datos()
        st.rerun()
    if st.button("🚪 Cerrar Sesión"): st.session_state.autenticado = False; st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = [{"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"} for i, row in st.session_state.viajes.iterrows() if str(row['Fecha Viaje']) != "-"]
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, custom_css=".fc-event { cursor: pointer; }")
    if res_cal.get("eventClick"):
        idx = int(res_cal["eventClick"]["event"]["id"])
        v = st.session_state.viajes.loc[idx]
        st.info(f"**Detalle:** {v['Cliente']} | {v['Origen']} -> {v['Destino']} | $ {v['Importe']}")

elif sel == "MODULO VENTAS":
    st.header("💰 Gestión de Ventas")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Clientes", "🚛 Carga Viaje", "📝 Presupuestos", "📑 Cta Cte Individual", "🌎 Cta Cte General"])
    
    with tab1: # TU GESTIÓN DE CLIENTES COMPLETA
        with st.expander("➕ ALTA DE NUEVO CLIENTE"):
            with st.form("f_cli", clear_on_submit=True):
                c1, c2 = st.columns(2); r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT *")
                mail = c1.text_input("Email"); tel = c2.text_input("Teléfono")
                dir_f = c1.text_input("Dirección Fiscal"); loc = c2.text_input("Localidad")
                prov = c1.text_input("Provincia"); c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
                c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
                if st.form_submit_button("REGISTRAR CLIENTE"):
                    nf = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()
        st.dataframe(st.session_state.clientes, use_container_width=True)

    with tab2: # TU CARGA DE VIAJE ORIGINAL
        with st.form("f_v"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
            orig = st.text_input("Origen"); dest = st.text_input("Destino")
            imp = st.number_input("Importe Neto $", min_value=0.0)
            if st.form_submit_button("GUARDAR VIAJE"):
                nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

    with tab3: # TUS PRESUPUESTOS CON DESCARGA
        for i, row in st.session_state.presupuestos.iterrows():
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            c1.write(f"**{row['Cliente']}** | {row['Tipo Móvil']} | {row['Fecha Emisión']}")
            html = generar_html_presupuesto(row)
            c2.download_button("📄 PDF", data=html, file_name=f"Presu_{i}.html", mime="text/html", key=f"p_{i}")
            if c3.button("🗑️", key=f"dp_{i}"):
                st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()

    with tab4: # TU CTA CTE INDIVIDUAL CON REPORTE
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
        st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
        html_r = generar_html_resumen(cl, df_ind, df_ind['Importe'].sum())
        st.download_button("📄 DESCARGAR RESUMEN", data=html_r, file_name=f"Resumen_{cl}.html", mime="text/html")
        st.dataframe(df_ind)

elif sel == "MODULO COMPRAS":
    st.header("🛒 Gestión de Compras")
    tc1, tc2 = st.tabs(["👥 Proveedores", "🧾 Carga de Gastos"])
    with tc1:
        with st.form("f_p"):
            c1, c2 = st.columns(2)
            pr_rs = c1.text_input("Razón Social"); pr_ct = c2.text_input("CUIT")
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                nf = pd.DataFrame([[pr_rs, pr_ct, "-", "-"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, nf], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
        st.dataframe(st.session_state.proveedores)
    
    with tc2: # Lógica de Notas de Crédito y AFIP
        with st.form("f_g"):
            c1, c2, c3 = st.columns(3)
            cp_f = c1.date_input("Fecha"); cp_p = c2.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cp_t = c3.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Nota de Crédito", "Nota de Débito"])
            n21 = c1.number_input("Neto 21%"); n10 = c2.number_input("Neto 10.5%"); no_g = c3.number_input("No Gravados")
            r_iv = c1.number_input("Ret. IVA"); r_ga = c2.number_input("Ret. Ganancias"); r_ib = c3.number_input("Ret. IIBB")
            i21 = n21 * 0.21; i10 = n10 * 0.105
            total = n21 + i21 + n10 + i10 + r_iv + r_ga + r_ib + no_g
            if "Nota de Crédito" in cp_t: total = -abs(total)
            st.subheader(f"Total: $ {total:,.2f}")
            if st.form_submit_button("GUARDAR COMPRA"):
                nf = pd.DataFrame([[cp_f, cp_p, "-", cp_t, n21, i21, n10, i10, r_iv, r_ga, r_ib, no_g, total]], columns=st.session_state.compras.columns)
                st.session_state.compras = pd.concat([st.session_state.compras, nf], ignore_index=True)
                guardar_datos("compras", st.session_state.compras); st.rerun()
