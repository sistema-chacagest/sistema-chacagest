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
        
        def leer_h(n, cols):
            try:
                ws = sh.worksheet(n)
                d = ws.get_all_records()
                df = pd.DataFrame(d) if d else pd.DataFrame(columns=cols)
                return df
            except: return pd.DataFrame(columns=cols)

        df_c = leer_h("clientes", col_c)
        df_v = leer_h("viajes", col_v)
        df_p = leer_h("presupuestos", col_p)
        df_t = leer_h("tesoreria", col_t)
        df_prov = leer_h("proveedores", col_prov)
        df_com = leer_h("compras", col_compras)

        # Formateo numérico estricto
        for df, col in [(df_v, 'Importe'), (df_p, 'Importe'), (df_t, 'Monto'), (df_com, 'Total')]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
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

# --- 2. REPORTES HTML (TU ESTÉTICA) ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>body{{font-family:Arial;}}.header{{background:#5e2d61;color:white;padding:20px;text-align:center;}}.tabla{{width:100%;border-collapse:collapse;}}.tabla th{{background:#f39c12;color:white;padding:10px;}}.tabla td{{border:1px solid #ddd;padding:8px;}}</style></head><body><div class='header'><h1>Resumen: {cliente}</h1></div>{tabla_html}<h3>SALDO: $ {saldo:,.2f}</h3></body></html>"

def generar_html_presupuesto(p_data):
    return f"<html><body style='font-family:Arial;padding:40px;'><h1 style='color:#5e2d61'>PRESUPUESTO</h1><p><b>Cliente:</b> {p_data['Cliente']}</p><p><b>Detalle:</b> {p_data['Detalle']}</p><h2>TOTAL: $ {p_data['Importe']:,.2f}</h2></body></html>"

# --- 3. LOGIN ---
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

# --- 4. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c; st.session_state.viajes = v; st.session_state.presupuestos = p
    st.session_state.tesoreria = t; st.session_state.proveedores = prov; st.session_state.compras = com

# --- 5. ESTILO CSS ORIGINAL ---
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

# --- 6. SIDEBAR (ESTÉTICA RECUPERADA) ---
with st.sidebar:
    st.markdown("### 🚛 CHACAGEST")
    st.markdown("---")
    menu_principal = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], 
        icons=["calendar3", "cart4", "bag-check", "safe"], 
        default_index=0,
        styles={
            "container": {"padding": "0px", "background-color": "#f0f2f6"},
            "nav-link": {"font-size": "15px", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    
    sel_sub = None
    if menu_principal == "VENTAS":
        st.markdown("<div style='margin-left: 20px; border-left: 2px solid #f39c12; padding-left: 10px;'>", unsafe_allow_html=True)
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
            icons=["people", "truck", "file-text", "person-vcard", "globe", "file-text"],
            styles={"nav-link-selected": {"background-color": "#f39c12", "color": "white"}})
        st.markdown("</div>", unsafe_allow_html=True)
    elif menu_principal == "COMPRAS":
        st.markdown("<div style='margin-left: 20px; border-left: 2px solid #f39c12; padding-left: 10px;'>", unsafe_allow_html=True)
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"],
            icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"],
            styles={"nav-link-selected": {"background-color": "#f39c12", "color": "white"}})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Sincronizar"): st.session_state.clear(); st.rerun()
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

sel = sel_sub if sel_sub else menu_principal

# --- 7. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Importe'] > 0:
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es"})

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "CC"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()

    st.subheader("📋 Base de Clientes")
    for i, row in st.session_state.clientes.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
            c1.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT / CUIL / DNI *']}")
            if c2.button("📝 Editar", key=f"ed_cl_{i}"): st.session_state[f"edit_cl_{i}"] = True
            if c3.button("🗑️", key=f"del_cl_{i}"):
                st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
            
            if st.session_state.get(f"edit_cl_{i}", False):
                with st.form(f"f_ed_cl_{i}"):
                    n_rs = st.text_input("Nueva Razón Social", value=row['Razón Social'])
                    if st.form_submit_button("✅ Actualizar"):
                        st.session_state.clientes.at[i, 'Razón Social'] = n_rs
                        guardar_datos("clientes", st.session_state.clientes); st.session_state[f"edit_cl_{i}"] = False; st.rerun()
        st.divider()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); pat = st.text_input("Patente")
        imp = st.number_input("Importe $", min_value=0.0)
        
        # ASOCIACIÓN AFIP
        t_comp = st.selectbox("Tipo Comprobante", ["Factura", "Nota de Débito", "Nota de Crédito"])
        ref_afip = st.text_input("Nro Comprobante Asociado (AFIP)")
        
        if st.form_submit_button("GUARDAR VIAJE"):
            valor = -imp if t_comp == "Nota de Crédito" else imp
            nv = pd.DataFrame([[date.today(), cli, f_v, "", "", pat, valor, t_comp, ref_afip]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Guardado"); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    with st.form("f_p", clear_on_submit=True):
        p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        p_det = st.text_area("Detalle"); p_imp = st.number_input("Total", min_value=0.0)
        if st.form_submit_button("GENERAR"):
            np = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(7), p_det, "Bus", p_imp]], columns=st.session_state.presupuestos.columns)
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
            guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    
    for i, row in st.session_state.presupuestos.iterrows():
        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
        c1.write(f"**{row['Cliente']}** - ${row['Importe']}")
        html = generar_html_presupuesto(row)
        c2.download_button("📄 PDF", data=html, file_name=f"Presu_{i}.html", mime="text/html", key=f"dl_{i}")
        if c3.button("🗑️", key=f"del_p_{i}"):
            st.session_state.presupuestos = st.session_state.presupuestos.drop(i); guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2 = st.tabs(["🧾 COBRANZA", "📊 SALDOS"])
    with t1:
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            cj = st.selectbox("Caja", opc_cajas); mon = st.number_input("Monto", min_value=0.0)
            afip = st.text_input("Ref AFIP")
            if st.form_submit_button("REGISTRAR COBRO"):
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESO", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); guardar_datos("viajes", st.session_state.viajes); st.rerun()
    with t2:
        for caja in opc_cajas:
            s = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == caja]['Monto'].sum()
            st.metric(caja, f"$ {s:,.2f}")

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
        c1.write(f"{row['Fecha Viaje']}")
        c2.write(f"**{row['Cliente']}** | {row['Tipo Comp']} | **${row['Importe']}**")
        if c3.button("🗑️", key=f"del_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i); guardar_datos("viajes", st.session_state.viajes); st.rerun()
        st.divider()

# --- Módulos de Compras (Repitiendo estética y lógica de edición) ---
elif sel == "CARGA PROVEEDOR":
    st.header("👤 Proveedores")
    with st.expander("➕ NUEVO PROVEEDOR"):
        with st.form("f_prov"):
            rs = st.text_input("Razón Social"); doc = st.text_input("CUIT")
            if st.form_submit_button("REGISTRAR"):
                np = pd.DataFrame([[rs, doc, "Varios", "RI"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    
    for i, row in st.session_state.proveedores.iterrows():
        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
        c1.write(f"**{row['Razón Social']}** | CUIT: {row['CUIT/DNI']}")
        if c2.button("📝", key=f"ed_pr_{i}"): st.session_state[f"edit_pr_{i}"] = True
        if c3.button("🗑️", key=f"del_pr_{i}"):
            st.session_state.proveedores = st.session_state.proveedores.drop(i); guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
