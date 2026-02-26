import streamlit as st
import pandas as pd
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64 # Para la descarga del PDF

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
    col_g = ["Fecha Carga", "Proveedor", "Fecha Gasto", "Concepto", "Referencia", "Móvil/Sucursal", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        # Carga Clientes y Ventas (Viajes)
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Carga Proveedores y Compras (Gastos)
        ws_p = sh.worksheet("proveedores")
        df_p = pd.DataFrame(ws_p.get_all_records()) if ws_p.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_g = sh.worksheet("gastos")
        df_g = pd.DataFrame(ws_g.get_all_records()) if ws_g.get_all_records() else pd.DataFrame(columns=col_g)
        df_g['Importe'] = pd.to_numeric(df_g['Importe'], errors='coerce').fillna(0)
        
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
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- FUNCIÓN PARA GENERAR REPORTE ---
def generar_html_resumen(entidad, df, saldo, tipo="Cliente"):
    tabla_html = df.to_html(index=False, classes='tabla')
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
            .info {{ margin: 20px 0; font-size: 14px; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tabla th {{ background-color: #f39c12; color: white; padding: 10px; text-align: left; }}
            .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
            .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CHACAGEST - Resumen de Cuenta</h1>
            <p>Fecha de emisión: {date.today()}</p>
        </div>
        <div class="info">
            <p><b>{tipo}:</b> {entidad}</p>
        </div>
        {tabla_html}
        <div class="total"> SALDO TOTAL A LA FECHA: $ {saldo:,.2f} </div>
    </body>
    </html>
    """
    return html

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

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
    c, v, p, g = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.proveedores = p if p is not None else pd.DataFrame()
    st.session_state.gastos = g if g is not None else pd.DataFrame()

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
    .stExpander { border: none !important; background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    
    sel_fijo = option_menu(None, ["CALENDARIO"], icons=["calendar3"], default_index=0,
                         styles={"nav-link-selected": {"background-color": "#5e2d61"}})

    with st.expander("💰 VENTAS", expanded=False):
        sel_ventas = option_menu(None, ["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
                                icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"], key='menu_v')
    
    with st.expander("🛒 COMPRAS", expanded=False):
        sel_compras = option_menu(None, ["PROVEEDORES", "CARGA COMPRA", "AJUSTES COMPRA (NC/ND)", "CTA CTE PROV INDIV", "CTA CTE PROV GRAL", "COMPROBANTES COMPRA"],
                                 icons=["shop", "cart-plus", "file-earmark-plus", "person-badge", "geo", "receipt"], key='menu_c')

    # Lógica de navegación simple
    if "menu_activo" not in st.session_state: st.session_state.menu_activo = "CALENDARIO"
    
    # Actualizar según interacción
    if sel_fijo == "CALENDARIO": sel = "CALENDARIO"
    # El usuario debe expandir y clickear para cambiar el 'sel'
    # Priorizamos el último menú tocado usando un callback o chequeo de cambio
    if 'menu_v' in st.context.keys: sel = sel_ventas
    
    # Manejo manual de la navegación
    query_params = st.query_params
    sel = sel_fijo
    if st.session_state.get('menu_v'): sel = sel_ventas
    if st.session_state.get('menu_c'): sel = sel_compras

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, g = cargar_datos()
        st.session_state.clientes, st.session_state.viajes = c, v
        st.session_state.proveedores, st.session_state.gastos = p, g
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

# --- CALENDARIO (IGUAL) ---
if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, custom_css=".fc-event { background-color: #f39c12; }")
    if res_cal.get("eventClick"):
        idx = int(res_cal["eventClick"]["event"]["id"])
        v_det = st.session_state.viajes.loc[idx]
        st.info(f"**Viaje de {v_det['Cliente']}**: {v_det['Origen']} -> {v_det['Destino']} | Importe: ${v_det['Importe']}")

# --- VENTAS (MODULOS ORIGINALES) ---
elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR CLIENTE"):
                nueva = pd.DataFrame([[r, cuit, "", "", "", "", "", "Monotributo", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f_v = st.date_input("Fecha"); pat = st.text_input("Patente"); orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (Ventas)")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro = st.text_input("Nro Comprobante AFIP Asociado *")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            val = -monto if "Crédito" in tipo else monto
            nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", "Ajuste Saldo", "-", val, "NC" if val<0 else "ND", nro]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    for i, row in st.session_state.viajes.iterrows():
        c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
        c1.write(row['Fecha Viaje'])
        c2.write(f"**{row['Cliente']}** | ${row['Importe']}")
        if c3.button("🗑️", key=f"del_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

# --- COMPRAS (NUEVO MÓDULO ESPEJO) ---
elif sel == "PROVEEDORES":
    st.header("🏢 Gestión de Proveedores")
    with st.expander("➕ ALTA DE NUEVO PROVEEDOR"):
        with st.form("f_prov", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                nueva = pd.DataFrame([[r, cuit, "", "", "", "", "", "Responsable Inscripto", "Cuenta Corriente"]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, nueva], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    st.dataframe(st.session_state.proveedores, use_container_width=True)

elif sel == "CARGA COMPRA":
    st.header("🛒 Registro de Gasto / Compra")
    with st.form("f_g"):
        prov = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        f_g = st.date_input("Fecha de Factura")
        conc = st.text_input("Concepto (Combustible, Repuestos, etc.)")
        ref = st.text_input("Nro Factura")
        movil = st.text_input("Móvil / Sucursal")
        imp = st.number_input("Importe Total $", min_value=0.0)
        if st.form_submit_button("GUARDAR COMPRA"):
            # En compras, el importe suma a nuestra deuda (valor positivo)
            ng = pd.DataFrame([[date.today(), prov, f_g, conc, ref, movil, imp, "Factura Compra", "-"]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, ng], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.success("Compra cargada"); st.rerun()

elif sel == "AJUSTES COMPRA (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (Compras)")
    st.info("Asocie la nota de crédito del proveedor a una factura existente.")
    tipo = st.radio("Acción:", ["Nota de Crédito (Baja Deuda)", "Nota de Débito (Sube Deuda)"], horizontal=True)
    with st.form("f_nc_p"):
        pr = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante Asociado *")
        monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE COMPRA"):
            val = -monto if "Crédito" in tipo else monto
            t_txt = "NC Proveedor" if "Crédito" in tipo else "ND Proveedor"
            nc = pd.DataFrame([[date.today(), pr, date.today(), "AJUSTE", "Ajuste de Cuenta", "-", val, t_txt, nro_asoc]], columns=st.session_state.gastos.columns)
            st.session_state.gastos = pd.concat([st.session_state.gastos, nc], ignore_index=True)
            guardar_datos("gastos", st.session_state.gastos); st.rerun()

elif sel == "CTA CTE PROV INDIV":
    st.header("📑 Cuenta Corriente con Proveedor")
    if not st.session_state.proveedores.empty:
        pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
        df_ind = st.session_state.gastos[st.session_state.gastos['Proveedor'] == pr]
        saldo = df_ind['Importe'].sum()
        st.metric("DEUDA CON PROVEEDOR", f"$ {saldo:,.2f}")
        st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE PROV GRAL":
    st.header("🌎 Resumen de Cuentas a Pagar")
    if not st.session_state.gastos.empty:
        res = st.session_state.gastos.groupby('Proveedor')['Importe'].sum().reset_index()
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES COMPRA":
    st.header("📜 Historial de Gastos")
    if not st.session_state.gastos.empty:
        for i, row in st.session_state.gastos.iterrows():
            c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
            c1.write(f"📅 {row['Fecha Gasto']}")
            c2.write(f"🏢 **{row['Proveedor']}** | {row['Concepto']} | **${row['Importe']}**")
            if c3.button("🗑️", key=f"del_g_{i}"):
                st.session_state.gastos = st.session_state.gastos.drop(i)
                guardar_datos("gastos", st.session_state.gastos); st.rerun()
