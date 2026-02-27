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
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_comp = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]

    try:
        sh = conectar_google()
        if sh is None: return [None]*5
        
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        try:
            ws_pres = sh.worksheet("presupuestos")
            df_pres = pd.DataFrame(ws_pres.get_all_records()) if ws_pres.get_all_records() else pd.DataFrame(columns=col_p)
        except: df_pres = pd.DataFrame(columns=col_p)
        
        try:
            ws_prov = sh.worksheet("proveedores")
            df_prov = pd.DataFrame(ws_prov.get_all_records()) if ws_prov.get_all_records() else pd.DataFrame(columns=col_prov)
        except: df_prov = pd.DataFrame(columns=col_prov)

        try:
            ws_comp = sh.worksheet("compras")
            df_comp = pd.DataFrame(ws_comp.get_all_records()) if ws_comp.get_all_records() else pd.DataFrame(columns=col_comp)
            for col in ["Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]:
                df_comp[col] = pd.to_numeric(df_comp[col], errors='coerce').fillna(0)
        except: df_comp = pd.DataFrame(columns=col_comp)

        return df_c, df_v, df_pres, df_prov, df_comp
    except:
        return [None]*5

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

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False

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
if 'clientes' not in st.session_state:
    c, v, p, pr, co = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.proveedores = pr if pr is not None else pd.DataFrame()
    st.session_state.compras = co if co is not None else pd.DataFrame()

# --- 4. DISEÑO ESTÉTICO ORIGINAL ---
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
    .card-cliente { background-color: #f0f2f6; padding: 15px; border-left: 5px solid #5e2d61; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "COMPRAS", "CTA CTE", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "cart-check", "wallet2", "file-text"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, pr, co = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = c, v, p, pr, co
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"})
    custom_css = ".fc-button-primary { background-color: #5e2d61 !important; border-color: #5e2d61 !important; } .fc-event { background-color: #f39c12 !important; } .fc-toolbar-title { color: #5e2d61 !important; }"
    calendar(events=eventos, options={"locale": "es", "height": 600}, custom_css=custom_css)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2); r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT *")
            mail = c1.text_input("Email"); tel = c2.text_input("Teléfono")
            loc = c2.text_input("Localidad"); prov = c1.text_input("Provincia")
            c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nf = pd.DataFrame([[r, cuit, mail, tel, "", loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()

    st.subheader("📋 Base de Clientes")
    for i, row in st.session_state.clientes.iterrows():
        with st.container():
            c_inf, c_ed, c_el = st.columns([0.7, 0.15, 0.15])
            c_inf.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT / CUIL / DNI *']}")
            c_inf.caption(f"📍 {row['Localidad']}, {row['Provincia']} | 📞 {row['Teléfono']}")
            if c_ed.button("📝 Editar", key=f"edc_{i}"): st.session_state[f"edcl_mode_{i}"] = True
            if c_el.button("🗑️", key=f"delc_{i}"):
                st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
            
            if st.session_state.get(f"edcl_mode_{i}", False):
                with st.form(f"fe_{i}"):
                    n_rs = st.text_input("Razón Social", value=row['Razón Social'])
                    n_ct = st.text_input("CUIT", value=row['CUIT / CUIL / DNI *'])
                    if st.form_submit_button("Guardar"):
                        st.session_state.clientes.at[i, 'Razón Social'] = n_rs
                        st.session_state.clientes.at[i, 'CUIT / CUIL / DNI *'] = n_ct
                        guardar_datos("clientes", st.session_state.clientes)
                        st.session_state[f"edcl_mode_{i}"] = False
                        st.rerun()
            st.divider()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

elif sel == "COMPRAS":
    st.header("🛒 Módulo de Compras")
    t1, t2 = st.tabs(["👥 Carga Proveedor", "🧾 Carga Gastos"])
    with t1:
        with st.form("f_pr", clear_on_submit=True):
            c1, c2 = st.columns(2)
            pr_rs = c1.text_input("Razón Social *")
            pr_ct = c2.text_input("CUIT o DNI *")
            pr_gs = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Otros"])
            pr_iv = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento", "Consumidor Final", "Monotributista"])
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                if pr_rs and pr_ct:
                    n_pr = pd.DataFrame([[pr_rs, pr_ct, pr_gs, pr_iv]], columns=st.session_state.proveedores.columns)
                    st.session_state.proveedores = pd.concat([st.session_state.proveedores, n_pr], ignore_index=True)
                    guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
        st.dataframe(st.session_state.proveedores, use_container_width=True)

    with t2:
        with st.form("f_gas", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            cp_f = c1.date_input("Fecha", date.today())
            cp_p = c2.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cp_v = c3.text_input("Punto Venta")
            cp_t = c1.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Remito", "Nota de Crédito", "Nota de Débito"])
            
            n21 = c1.number_input("Neto 21% $", min_value=0.0)
            n10 = c2.number_input("Neto 10.5% $", min_value=0.0)
            no_g = c3.number_input("No Gravados $", min_value=0.0)
            
            r_iv = c1.number_input("Ret. IVA $", min_value=0.0)
            r_ga = c2.number_input("Ret. Ganancias $", min_value=0.0)
            r_ib = c3.number_input("Ret. IIBB $", min_value=0.0)
            
            i21 = n21 * 0.21; i10 = n10 * 0.105
            total = n21 + i21 + n10 + i10 + r_iv + r_ga + r_ib + no_g
            if "Nota de Crédito" in cp_t: total = -abs(total)
            
            st.markdown(f"### TOTAL: $ {total:,.2f}")
            if st.form_submit_button("GUARDAR COMPROBANTE"):
                n_cp = pd.DataFrame([[cp_f, cp_p, cp_v, cp_t, n21, i21, n10, i10, r_iv, r_ga, r_ib, no_g, total]], columns=st.session_state.compras.columns)
                st.session_state.compras = pd.concat([st.session_state.compras, n_cp], ignore_index=True)
                guardar_datos("compras", st.session_state.compras); st.success("Registrado"); st.rerun()

elif sel == "CTA CTE":
    st.header("💰 Cuentas Corrientes")
    p_cl, p_pr = st.tabs(["Clientes", "Proveedores"])
    with p_cl:
        if not st.session_state.clientes.empty:
            cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
            st.metric("Saldo", f"$ {df_cl['Importe'].sum():,.2f}")
            st.dataframe(df_cl, use_container_width=True)
    with p_pr:
        if not st.session_state.proveedores.empty:
            pr = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
            df_pr = st.session_state.compras[st.session_state.compras['Proveedor'] == pr]
            st.metric("Saldo", f"$ {df_pr['Total'].sum():,.2f}")
            st.dataframe(df_pr, use_container_width=True)

elif sel == "COMPROBANTES":
    st.header("📜 Historial General")
    v_v, v_c = st.tabs(["Ventas/Viajes", "Compras/Gastos"])
    with v_v:
        for i in reversed(st.session_state.viajes.index):
            row = st.session_state.viajes.loc[i]
            with st.container():
                c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
                c1.write(row['Fecha Viaje'])
                c2.markdown(f"**{row['Cliente']}** | ${row['Importe']}")
                if c3.button("🗑️", key=f"dv_{i}"):
                    st.session_state.viajes = st.session_state.viajes.drop(i); guardar_datos("viajes", st.session_state.viajes); st.rerun()
                st.divider()
    with v_c:
        for i in reversed(st.session_state.compras.index):
            row = st.session_state.compras.loc[i]
            with st.container():
                c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
                c1.write(row['Fecha'])
                c2.markdown(f"**{row['Proveedor']}** | {row['Tipo']} | **${row['Total']}**")
                if c3.button("🗑️", key=f"dc_{i}"):
                    st.session_state.compras = st.session_state.compras.drop(i); guardar_datos("compras", st.session_state.compras); st.rerun()
                st.divider()

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    st.dataframe(st.session_state.presupuestos, use_container_width=True)
