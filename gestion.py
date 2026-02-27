import streamlit as st
import pandas as pd
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

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
    # Estructura de columnas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_comp = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]

    try:
        sh = conectar_google()
        if sh is None: return [pd.DataFrame(columns=c) for c in [col_c, col_v, col_p, col_prov, col_comp]]
        
        def get_df(name, cols):
            try:
                ws = sh.worksheet(name)
                data = ws.get_all_records()
                return pd.DataFrame(data) if data else pd.DataFrame(columns=cols)
            except: return pd.DataFrame(columns=cols)

        df_c = get_df("clientes", col_c)
        df_v = get_df("viajes", col_v)
        df_p = get_df("presupuestos", col_p)
        df_prov = get_df("proveedores", col_prov)
        df_comp = get_df("compras", col_comp)

        # Formateo de números
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        for col in ["Neto 21%", "IVA 21%", "Neto 10.5%", "IVA 10.5%", "Ret. IVA", "Ret. Ganancias", "Ret. IIBB", "No Gravados", "Total"]:
            if col in df_comp.columns:
                df_comp[col] = pd.to_numeric(df_comp[col], errors='coerce').fillna(0)

        return df_c, df_v, df_p, df_prov, df_comp
    except:
        return [pd.DataFrame() for _ in range(5)]

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
    c, v, p, pr, co = cargar_datos()
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = c, v, p, pr, co

# --- 4. ESTÉTICA ORIGINAL ---
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

# --- 5. SIDEBAR ORGANIZADO ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #5e2d61;'>CHACAGEST</h2>", unsafe_allow_html=True)
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "MODULO VENTAS", "MODULO COMPRAS", "REPORTES GENERALES"],
        icons=["calendar3", "cash-stack", "cart-check", "graph-up"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, pr, co = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.proveedores, st.session_state.compras = c, v, p, pr, co
        st.rerun()
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. LÓGICA DE MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda Global de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "MODULO VENTAS":
    st.header("💰 Gestión de Ventas")
    v_tab1, v_tab2, v_tab3, v_tab4 = st.tabs(["👥 Clientes", "🚛 Carga de Viaje", "📝 Presupuestos", "📑 Cta. Cte. Clientes"])
    
    with v_tab1:
        st.subheader("Administración de Clientes")
        # Aquí va la lógica de Clientes (Alta/Baja/Edición) que ya teníamos...
        with st.expander("➕ Alta de Cliente"):
             with st.form("f_cli_v"):
                r = st.text_input("Razón Social"); cuit = st.text_input("CUIT")
                if st.form_submit_button("Guardar"):
                    nf = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "-", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()
        st.dataframe(st.session_state.clientes, use_container_width=True)

    with v_tab2:
        st.subheader("Nuevo Viaje / Servicio")
        with st.form("f_viaje_v"):
            c1, c2 = st.columns(2)
            cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            f_v = c2.date_input("Fecha")
            orig = c1.text_input("Origen"); dest = c2.text_input("Destino")
            imp = st.number_input("Importe $", min_value=0.0)
            if st.form_submit_button("Registrar Viaje"):
                nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes); st.success("Viaje guardado"); st.rerun()

    with v_tab3:
        st.subheader("Presupuestos Enviados")
        st.dataframe(st.session_state.presupuestos, use_container_width=True)

    with v_tab4:
        st.subheader("Estado de Cuenta de Clientes")
        if not st.session_state.clientes.empty:
            cl_sel = st.selectbox("Seleccionar Cliente para Ver Saldo", st.session_state.clientes['Razón Social'].unique())
            res = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl_sel]
            st.metric("Deuda Pendiente", f"$ {res['Importe'].sum():,.2f}")
            st.dataframe(res, use_container_width=True)

elif sel == "MODULO COMPRAS":
    st.header("🛒 Gestión de Compras y Gastos")
    c_tab1, c_tab2, c_tab3, c_tab4 = st.tabs(["👥 Proveedores", "🧾 Carga de Gastos", "📉 Cta. Cte. Proveedores", "📜 Histórico Comprobantes"])
    
    with c_tab1:
        st.subheader("Administración de Proveedores")
        with st.form("f_prov_c", clear_on_submit=True):
            c1, c2 = st.columns(2)
            pr_rs = c1.text_input("Razón Social *")
            pr_ct = c2.text_input("CUIT o DNI *")
            pr_gs = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Sueldos", "Otros"])
            pr_iv = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
            if st.form_submit_button("Registrar Proveedor"):
                n_pr = pd.DataFrame([[pr_rs, pr_ct, pr_gs, pr_iv]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, n_pr], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
        st.dataframe(st.session_state.proveedores, use_container_width=True)

    with c_tab2:
        st.subheader("Carga de Comprobante / Gasto")
        with st.form("f_gasto_c", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            cp_f = col1.date_input("Fecha", date.today())
            cp_p = col2.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            cp_t = col3.selectbox("Tipo", ["Factura A", "Factura B", "Factura C", "Remito", "Nota de Crédito", "Nota de Débito"])
            
            n21 = col1.number_input("Neto 21% $", min_value=0.0)
            n10 = col2.number_input("Neto 10.5% $", min_value=0.0)
            no_g = col3.number_input("No Gravados $", min_value=0.0)
            
            r_iv = col1.number_input("Ret. IVA $", min_value=0.0)
            r_ga = col2.number_input("Ret. Ganancias $", min_value=0.0)
            r_ib = col3.number_input("Ret. IIBB $", min_value=0.0)
            
            i21 = n21 * 0.21; i10 = n10 * 0.105
            total = n21 + i21 + n10 + i10 + r_iv + r_ga + r_ib + no_g
            if "Nota de Crédito" in cp_t: total = -abs(total)
            
            st.markdown(f"### TOTAL A PAGAR: $ {total:,.2f}")
            if st.form_submit_button("Guardar Gasto"):
                n_cp = pd.DataFrame([[cp_f, cp_p, "-", cp_t, n21, i21, n10, i10, r_iv, r_ga, r_ib, no_g, total]], columns=st.session_state.compras.columns)
                st.session_state.compras = pd.concat([st.session_state.compras, n_cp], ignore_index=True)
                guardar_datos("compras", st.session_state.compras); st.success("Gasto registrado"); st.rerun()

    with c_tab3:
        st.subheader("Saldos con Proveedores")
        if not st.session_state.compras.empty:
            res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
            st.table(res_p.style.format({"Total": "$ {:,.2f}"}))

    with c_tab4:
        st.subheader("Histórico de Compras")
        for i in reversed(st.session_state.compras.index):
            r = st.session_state.compras.loc[i]
            c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
            c1.write(r['Fecha'])
            c2.write(f"**{r['Proveedor']}** | {r['Tipo Factura']} | **${r['Total']}**")
            if c3.button("🗑️", key=f"del_cp_{i}"):
                st.session_state.compras = st.session_state.compras.drop(i)
                guardar_datos("compras", st.session_state.compras); st.rerun()
            st.divider()

elif sel == "REPORTES GENERALES":
    st.header("📊 Resumen de Situación")
    col1, col2 = st.columns(2)
    tot_v = st.session_state.viajes['Importe'].sum()
    tot_c = st.session_state.compras['Total'].sum()
    col1.metric("Total Ventas (Cobra)", f"$ {tot_v:,.2f}")
    col2.metric("Total Compras (Paga)", f"$ {tot_c:,.2f}")
    st.subheader("Resultado Estimado")
    st.title(f"$ {tot_v - tot_c:,.2f}")
