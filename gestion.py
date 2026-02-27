import streamlit as st
import pandas as pd
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

    sh = conectar_google()
    if sh is None: return [pd.DataFrame() for _ in range(5)]
    
    def get_df(name, cols):
        try:
            ws = sh.worksheet(name)
            data = ws.get_all_records()
            return pd.DataFrame(data) if data else pd.DataFrame(columns=cols)
        except: return pd.DataFrame(columns=cols)

    return get_df("clientes", col_c), get_df("viajes", col_v), get_df("presupuestos", col_p), get_df("proveedores", col_prov), get_df("compras", col_comp)

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

# --- 2. FUNCIONES DE IMPRESIÓN (PDF/HTML) ---
def generar_html_presupuesto(p_data):
    return f"""
    <html><body style="font-family: Arial; padding: 30px;">
        <h1 style="color: #5e2d61;">CHACAGEST - PRESUPUESTO</h1>
        <hr>
        <p><b>Cliente:</b> {p_data['Cliente']}</p>
        <p><b>Fecha:</b> {p_data['Fecha Emisión']} | <b>Vencimiento:</b> {p_data['Vencimiento']}</p>
        <p><b>Unidad:</b> {p_data['Tipo Móvil']}</p>
        <div style="background: #f4f4f4; padding: 15px; border-radius: 5px;">
            <b>Detalle:</b><br>{p_data['Detalle']}
        </div>
        <h2 style="text-align: right; color: #d35400;">TOTAL: $ {float(p_data['Importe']):,.2f}</h2>
    </body></html>
    """

# --- 3. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026": st.session_state.autenticado = True; st.rerun()
            else: st.error("Error")
    st.stop()

# --- 4. INICIALIZACIÓN Y ESTÉTICA ---
if 'clientes' not in st.session_state:
    c, v, p, pr, co = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = c, v, p, pr, co

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px 5px 0 0; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    # EL LOGO SE MANTIENE AQUÍ
    try: st.image("logo_path.png", use_container_width=True)
    except: st.markdown("<h2 style='text-align:center;'>🚛 CHACAGEST</h2>", unsafe_allow_html=True)
    
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "MODULO VENTAS", "MODULO COMPRAS"],
        icons=["calendar3", "cash-stack", "cart-check"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = cargar_datos()
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda Global")
    if "v_cal" not in st.session_state: st.session_state.v_cal = None
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        eventos.append({"id": str(i), "title": f"{row['Cliente']}", "start": str(row['Fecha Viaje']), "backgroundColor": "#f39c12"})
    
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 500})
    
    if res_cal.get("eventClick"):
        idx = int(res_cal["eventClick"]["event"]["id"])
        v_det = st.session_state.viajes.loc[idx]
        st.info(f"**Detalle del Viaje:** {v_det['Cliente']} | {v_det['Origen']} -> {v_det['Destino']} | $ {v_det['Importe']}")

elif sel == "MODULO VENTAS":
    st.header("💰 Gestión de Ventas")
    vt1, vt2, vt3, vt4 = st.tabs(["👥 Clientes", "🚛 Carga Viaje", "📝 Presupuestos", "📑 Cta Cte"])
    
    with vt1:
        st.subheader("Clientes")
        with st.expander("➕ Alta Cliente"):
            with st.form("f_c"):
                c1, c2 = st.columns(2)
                r = c1.text_input("Razón Social"); cuit = c2.text_input("CUIT")
                tel = c1.text_input("Teléfono"); mail = c2.text_input("Email")
                if st.form_submit_button("Guardar"):
                    # Alta completa con todas las columnas
                    nf = pd.DataFrame([[r, cuit, mail, tel, "-", "-", "-", "-", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()
        st.dataframe(st.session_state.clientes, use_container_width=True)

    with vt2:
        st.subheader("Carga de Viaje")
        with st.form("f_v"):
            c1, c2 = st.columns(2)
            cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            f_v = c2.date_input("Fecha Viaje")
            ori = c1.text_input("Origen"); des = c2.text_input("Destino")
            pat = c1.text_input("Patente"); imp = c2.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("Registrar"):
                nv = pd.DataFrame([[date.today(), cli, f_v, ori, des, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes); st.rerun()

    with vt3:
        st.subheader("Nuevo Presupuesto")
        with st.form("f_p"):
            p_cli = st.selectbox("Cliente ", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            p_det = st.text_area("Detalle del Servicio")
            p_mov = st.selectbox("Móvil", ["Combi", "Minibus", "Micro"])
            p_imp = st.number_input("Importe Total", min_value=0.0)
            if st.form_submit_button("Generar"):
                np = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(days=7), p_det, p_mov, p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
        
        st.divider()
        for i, row in st.session_state.presupuestos.iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"**{row['Cliente']}** - {row['Tipo Móvil']} - ${row['Importe']}")
            html_p = generar_html_presupuesto(row)
            c2.download_button("📄 PDF", data=html_p, file_name=f"Presu_{i}.html", mime="text/html")

    with vt4:
        if not st.session_state.clientes.empty:
            cl = st.selectbox("Cta Cte Cliente", st.session_state.clientes['Razón Social'].unique())
            df_cl = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
            st.metric("Total Deuda", f"$ {df_cl['Importe'].sum():,.2f}")
            st.dataframe(df_cl, use_container_width=True)

elif sel == "MODULO COMPRAS":
    st.header("🛒 Gestión de Compras")
    ct1, ct2, ct3 = st.tabs(["👥 Proveedores", "🧾 Carga Gastos", "📑 Cta Cte"])
    
    with ct1:
        with st.form("f_pr"):
            st.subheader("Nuevo Proveedor")
            c1, c2 = st.columns(2)
            pr_rs = c1.text_input("Razón Social"); pr_ct = c2.text_input("CUIT/DNI")
            pr_gs = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Otros"])
            pr_iv = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento", "Monotributista"])
            if st.form_submit_button("Registrar"):
                n_pr = pd.DataFrame([[pr_rs, pr_ct, pr_gs, pr_iv]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, n_pr], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
        st.dataframe(st.session_state.proveedores, use_container_width=True)

    with ct2:
        with st.form("f_g"):
            st.subheader("Carga de Gasto Completa")
            c1, c2, c3 = st.columns(3)
            cp_f = c1.date_input("Fecha"); cp_p = c2.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cp_t = c3.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Remito", "Nota de Crédito", "Nota de Débito"])
            
            n21 = c1.number_input("Neto 21%", min_value=0.0); n10 = c2.number_input("Neto 10.5%", min_value=0.0); no_g = c3.number_input("No Gravados", min_value=0.0)
            r_iv = c1.number_input("Ret. IVA", min_value=0.0); r_ga = c2.number_input("Ret. Ganancias", min_value=0.0); r_ib = c3.number_input("Ret. IIBB", min_value=0.0)
            
            i21 = n21 * 0.21; i10 = n10 * 0.105
            total = n21 + i21 + n10 + i10 + r_iv + r_ga + r_ib + no_g
            if "Nota de Crédito" in cp_t: total = -abs(total)
            
            st.markdown(f"### TOTAL: $ {total:,.2f}")
            if st.form_submit_button("Guardar Comprobante"):
                n_cp = pd.DataFrame([[cp_f, cp_p, "-", cp_t, n21, i21, n10, i10, r_iv, r_ga, r_ib, no_g, total]], columns=st.session_state.compras.columns)
                st.session_state.compras = pd.concat([st.session_state.compras, n_cp], ignore_index=True)
                guardar_datos("compras", st.session_state.compras); st.rerun()
