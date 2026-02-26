import streamlit as st
import pandas as pd
import os
from datetime import date
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
    # Columnas Ventas
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    # Columnas Compras
    col_p = ["Razón Social", "CUIT o DNI", "Cuenta de Gastos", "Categoría IVA"]
    col_g = ["Fecha", "Proveedor", "Pto Vta", "Tipo Fact", "Neto 21", "IVA 21", "Neto 10.5", "IVA 10.5", "Ret IVA", "Ret Gan", "Ret IIBB", "No Gravado", "Total", "Nro Comp Asoc"]

    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Hojas de Ventas
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        
        # Hojas de Compras (crear si no existen)
        try: ws_p = sh.worksheet("proveedores")
        except: ws_p = sh.add_worksheet(title="proveedores", rows="100", cols="10")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_p)

        try: ws_g = sh.worksheet("gastos")
        except: ws_g = sh.add_worksheet(title="gastos", rows="1000", cols="15")
        df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_g)

        # Limpieza de datos
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        df_g['Total'] = pd.to_numeric(df_g['Total'], errors='coerce').fillna(0)
        
        return df_c, df_v, df_p, df_g
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

def generar_html_resumen(entidad, df, saldo, es_cliente=True):
    tipo = "Cliente" if es_cliente else "Proveedor"
    tabla_html = df.to_html(index=False, classes='tabla')
    html = f"""
    <html><head><style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
        .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .tabla th {{ background-color: #f39c12; color: white; padding: 10px; }}
        .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
        .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }}
    </style></head><body>
        <div class="header"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Emisión: {date.today()}</p></div>
        <p><b>{tipo}:</b> {entidad}</p>
        {tabla_html}
        <div class="total">SALDO TOTAL: $ {saldo:,.2f}</div>
    </body></html>
    """
    return html

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
                st.session_state.autenticado = True; st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, g = cargar_datos()
    st.session_state.clientes, st.session_state.viajes = c, v
    st.session_state.proveedores, st.session_state.gastos = p, g

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
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; }
    .stExpander { border: none !important; background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🚛 CHACAGEST")
    st.markdown("---")
    
    sel_fijo = option_menu(None, ["CALENDARIO"], icons=["calendar3"], default_index=0,
        styles={"container": {"background-color": "#f0f2f6", "padding": "0px"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    with st.expander("💰 VENTAS", expanded=True):
        sel_v = option_menu(None, ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], 
            icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"], default_index=0,
            styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "13px"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    with st.expander("🛒 COMPRAS", expanded=False):
        sel_c = option_menu(None, ["PROVEEDORES", "CARGA GASTOS", "AJUSTES COMPRAS", "CTA CTE PROV INDIV", "CTA CTE PROV GRAL", "COMPROBANTES COMPRAS"], 
            icons=["person-badge", "cart-plus", "patch-minus", "journal-text", "diagram-3", "receipt"], default_index=0,
            styles={"container": {"background-color": "transparent"}, "nav-link": {"font-size": "13px"}, "nav-link-selected": {"background-color": "#5e2d61"}})

    # Lógica de navegación
    if sel_fijo == "CALENDARIO":
        if "prev_sel_v" not in st.session_state: st.session_state.prev_sel_v = sel_v
        if "prev_sel_c" not in st.session_state: st.session_state.prev_sel_c = sel_c
        
        if sel_v != st.session_state.prev_sel_v:
            st.session_state.modulo = sel_v; st.session_state.prev_sel_v = sel_v
        elif sel_c != st.session_state.prev_sel_c:
            st.session_state.modulo = sel_c; st.session_state.prev_sel_c = sel_c
        else:
            st.session_state.modulo = "CALENDARIO"

    sel = st.session_state.modulo

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.gastos = c, v, p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False; st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600}, key="cal_final")

# --- MÓDULOS VENTAS ---
elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT / CUIL / DNI *")
            mail = c1.text_input("Email"); tel = c2.text_input("Teléfono")
            c_iva = c1.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c2.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, "-", "-", "-", c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.success("Guardado"); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha Viaje"); pat = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (Ventas)")
    st.info("Debe asociarse a un comprobante AFIP.")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante AFIP Asociado *")
        mot = st.text_input("Motivo / Concepto")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", mot, "-", val, "NC" if val<0 else "ND", nro_asoc]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Ajuste cargado"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
    saldo = df_ind['Importe'].sum()
    st.metric("SALDO TOTAL", f"$ {saldo:,.2f}")
    html = generar_html_resumen(cl, df_ind, saldo)
    st.download_button("📄 DESCARGAR RESUMEN", data=html, file_name=f"CtaCte_{cl}.html", mime="text/html")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"📅 {row['Fecha Viaje']}")
        c2.write(f"👤 **{row['Cliente']}** | {row['Origen']} a {row['Destino']} | **${row['Importe']}**")
        if c3.button("🗑️", key=f"del_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i); guardar_datos("viajes", st.session_state.viajes); st.rerun()
        st.divider()

# --- MÓDULOS COMPRAS ---
elif sel == "PROVEEDORES":
    st.header("👤 Gestión de Proveedores")
    with st.expander("➕ ALTA DE PROVEEDOR"):
        with st.form("f_prov", clear_on_submit=True):
            c1, c2 = st.columns(2)
            razon = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT o DNI *")
            gasto = c1.selectbox("Cuenta de Gastos", ["Combustible", "Reparación", "Repuesto", "Seguros", "Viáticos", "Peajes", "Otros"])
            iva = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                if razon and cuit:
                    new_p = pd.DataFrame([[razon, cuit, gasto, iva]], columns=st.session_state.proveedores.columns)
                    st.session_state.proveedores = pd.concat([st.session_state.proveedores, new_p], ignore_index=True)
                    guardar_datos("proveedores", st.session_state.proveedores); st.success("Proveedor Guardado"); st.rerun()
    st.dataframe(st.session_state.proveedores, use_container_width=True)

elif sel == "CARGA GASTOS":
    st.header("📥 Carga de Gastos")
    with st.form("f_gasto"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        c1, c2, c3 = st.columns(3)
        ptov = c1.text_input("Punto de Venta"); tfact = c2.selectbox("Tipo Factura", ["A", "B", "C", "Remito"]); f_g = c3.date_input("Fecha")
        
        st.subheader("Importes")
        col1, col2 = st.columns(2)
        n21 = col1.number_input("Neto 21% $", min_value=0.0); n10 = col2.number_input("Neto 10.5% $", min_value=0.0)
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        r_iva = col_r1.number_input("Retención IVA $", min_value=0.0)
        r_gan = col_r2.number_input("Retención Ganancia $", min_value=0.0)
        r_iibb = col_r3.number_input("Retención IIBB $", min_value=0.0)
        no_gr = col_r4.number_input("No Gravados $", min_value=0.0)
        
        iva21 = n21 * 0.21; iva10 = n10 * 0.105
        total = n21 + iva21 + n10 + iva10 + r_iva + r_gan + r_iibb + no_gr
        st.metric("TOTAL A PAGAR", f"$ {total:,.2f}")
        
        if st.form_submit_button("GUARDAR GASTO"):
            ng = pd.DataFrame([[f_g, prov, ptov, tfact, n21, iva21, n10, iva10, r_iva, r_gan, r_iibb, no_gr, total, "-"]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.success("Gasto Cargado"); st.rerun()

elif sel == "AJUSTES COMPRAS":
    st.header("💳 Notas de Crédito / Débito (Compras)")
    st.info("Cargue aquí los comprobantes de ajuste emitidos por proveedores.")
    tipo = st.radio("Acción:", ["Nota de Crédito Prov.", "Nota de Débito Prov."], horizontal=True)
    with st.form("f_nc_p"):
        pr = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante Asociado *")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), pr, "-", "AJUSTE", 0, 0, 0, 0, 0, 0, 0, 0, val, nro_asoc]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, nc], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.success("Ajuste cargado"); st.rerun()

elif sel == "CTA CTE PROV INDIV":
    st.header("📑 Cta Cte Proveedor")
    p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.gastos[st.session_state.gastos['Proveedor'] == p_sel].copy()
    saldo = df_p['Total'].sum()
    st.metric("DEUDA TOTAL", f"$ {saldo:,.2f}")
    st.dataframe(df_p, use_container_width=True)

elif sel == "CTA CTE PROV GRAL":
    st.header("🌎 Saldos Generales Proveedores")
    res_p = st.session_state.gastos.groupby('Proveedor')['Total'].sum().reset_index()
    st.table(res_p.style.format({"Total": "$ {:,.2f}"}))

elif sel == "COMPROBANTES COMPRAS":
    st.header("📜 Historial de Gastos")
    for i in reversed(st.session_state.gastos.index):
        r = st.session_state.gastos.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(f"{r['Fecha']}"); c2.write(f"**{r['Proveedor']}** | {r['Tipo Fact']} {r['Pto Vta']} | **Total: ${r['Total']}**")
        if c3.button("🗑️", key=f"del_g_{i}"):
            st.session_state.gastos = st.session_state.gastos.drop(i); guardar_datos("gastos", st.session_state.gastos); st.rerun()
        st.divider()
