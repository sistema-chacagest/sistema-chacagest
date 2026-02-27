import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y CONEXIÓN (Mantenemos tu lógica intacta) ---
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
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_comp = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None
        
        def get_df(name, cols):
            try:
                ws = sh.worksheet(name)
                data = ws.get_all_records()
                df = pd.DataFrame(data) if data else pd.DataFrame(columns=cols)
                if 'Importe' in df.columns: df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce').fillna(0)
                if 'Total' in df.columns: df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
                return df
            except: return pd.DataFrame(columns=cols)

        return get_df("clientes", col_c), get_df("viajes", col_v), get_df("presupuestos", col_p), get_df("proveedores", col_prov), get_df("compras", col_comp)
    except:
        return None, None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except: return False

# --- FUNCIONES DE REPORTES (Tus funciones originales) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>body {{ font-family: Arial; }} .header {{ background: #5e2d61; color: white; padding: 20px; text-align: center; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #f39c12; color: white; }} .total {{ text-align: right; font-size: 20px; color: #5e2d61; }}</style></head><body><div class='header'><h1>Resumen de Cuenta: {cliente}</h1></div>{tabla_html}<div class='total'>SALDO: $ {saldo:,.2f}</div></body></html>"

def generar_html_presupuesto(p_data):
    return f"<html><body style='font-family: Arial; padding: 40px;'><h1 style='color: #5e2d61;'>🚛 CHACAGEST - PRESUPUESTO</h1><hr><p><b>Cliente:</b> {p_data['Cliente']}</p><p><b>Detalle:</b> {p_data['Detalle']}</p><h2>TOTAL: $ {float(p_data['Importe']):,.2f}</h2></body></html>"

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

# --- 4. DISEÑO Y SIDEBAR ---
st.markdown("<style>[data-testid='stSidebarNav'] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

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
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. MÓDULOS SEPARADOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda Global de Viajes")
    eventos = [{"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"} for i, row in st.session_state.viajes.iterrows() if str(row['Fecha Viaje']) != "-"]
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, custom_css=".fc-event { cursor: pointer; }")
    if res_cal.get("eventClick"):
        idx = int(res_cal["eventClick"]["event"]["id"])
        v = st.session_state.viajes.loc[idx]
        st.info(f"**Detalle:** {v['Cliente']} | {v['Origen']} -> {v['Destino']} | $ {v['Importe']}")

elif sel == "MODULO VENTAS":
    st.header("💰 Gestión de Ventas (Ingresos)")
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Clientes", "🚛 Carga Viaje", "📝 Presupuestos", "📑 Cta Cte Clientes"])
    
    with tab1: # CLIENTES (Tu código original de edición y alta)
        with st.expander("➕ NUEVO CLIENTE"):
            with st.form("f_cli"):
                r = st.text_input("Razón Social"); cuit = st.text_input("CUIT")
                if st.form_submit_button("GUARDAR"):
                    nf = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "-", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()
        st.dataframe(st.session_state.clientes, use_container_width=True)

    with tab2: # CARGA VIAJE
        with st.form("f_v"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
            orig = st.text_input("Origen"); dest = st.text_input("Destino")
            imp = st.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("GUARDAR VIAJE"):
                nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes); st.success("Guardado"); st.rerun()

    with tab3: # PRESUPUESTOS (Con tu descarga original)
        st.subheader("Historial de Presupuestos")
        for i, row in st.session_state.presupuestos.iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"**{row['Cliente']}** - ${row['Importe']}")
            html = generar_html_presupuesto(row)
            c2.download_button("📄 Descargar", data=html, file_name=f"Presu_{i}.html", mime="text/html", key=f"p_{i}")

    with tab4: # CTA CTE CLIENTES
        if not st.session_state.clientes.empty:
            cl = st.selectbox("Cta Cte Individual", st.session_state.clientes['Razón Social'].unique())
            df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
            st.metric("Total a Cobrar", f"$ {df_cl['Importe'].sum():,.2f}")
            st.dataframe(df_cl, use_container_width=True)

elif sel == "MODULO COMPRAS":
    st.header("🛒 Gestión de Compras (Gastos)")
    tab_p, tab_g, tab_cc = st.tabs(["👥 Proveedores", "🧾 Carga de Gastos", "📑 Cta Cte Proveedores"])
    
    with tab_p:
        with st.form("f_prov"):
            c1, c2 = st.columns(2)
            pr_rs = c1.text_input("Proveedor"); pr_ct = c2.text_input("CUIT")
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                nf = pd.DataFrame([[pr_rs, pr_ct, "-", "-"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, nf], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
        st.dataframe(st.session_state.proveedores, use_container_width=True)

    with tab_g:
        with st.form("f_compra"):
            c1, c2, c3 = st.columns(3)
            cp_f = c1.date_input("Fecha"); cp_p = c2.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cp_t = c3.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Nota de Crédito", "Nota de Débito"])
            n21 = c1.number_input("Neto 21%"); n10 = c2.number_input("Neto 10.5%"); no_g = c3.number_input("No Gravados")
            r_iv = c1.number_input("Ret. IVA"); r_ga = c2.number_input("Ret. Ganancias"); r_ib = c3.number_input("Ret. IIBB")
            i21 = n21 * 0.21; i10 = n10 * 0.105
            total = n21 + i21 + n10 + i10 + r_iv + r_ga + r_ib + no_g
            if "Nota de Crédito" in cp_t: total = -abs(total) # Nota de crédito resta
            st.subheader(f"Total Comprobante: $ {total:,.2f}")
            if st.form_submit_button("GUARDAR COMPRA"):
                nf = pd.DataFrame([[cp_f, cp_p, "-", cp_t, n21, i21, n10, i10, r_iv, r_ga, r_ib, no_g, total]], columns=st.session_state.compras.columns)
                st.session_state.compras = pd.concat([st.session_state.compras, nf], ignore_index=True)
                guardar_datos("compras", st.session_state.compras); st.rerun()

    with tab_cc:
        if not st.session_state.compras.empty:
            res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
            st.table(res_p.style.format({"Total": "$ {:,.2f}"}))
