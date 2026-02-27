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
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    try:
        sh = conectar_google()
        if sh is None: return None, None
        
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        return df_c, df_v
    except:
        return None, None

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

# --- FUNCIONES DE REPORTE ---
def generar_html_resumen(cliente, df, saldo):
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
        <div class="header"><h1>CHACAGEST - Resumen</h1><p>Emisión: {date.today()}</p></div>
        <div class="info"><p><b>Cliente:</b> {cliente}</p></div>
        {tabla_html}
        <div class="total">SALDO TOTAL: $ {saldo:,.2f}</div>
    </body>
    </html>
    """
    return html

def generar_html_presupuesto(cliente, detalles, total):
    filas = "".join([f"<tr><td>{i['Cant']}</td><td>{i['Descripción']}</td><td>$ {i['Precio U.']:,.2f}</td><td>$ {i['Subtotal']:,.2f}</td></tr>" for i in detalles])
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .header {{ border-bottom: 3px solid #5e2d61; padding-bottom: 10px; margin-bottom: 20px; }}
            .logo {{ color: #5e2d61; font-size: 28px; font-weight: bold; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tabla th {{ background-color: #5e2d61; color: white; padding: 10px; text-align: left; }}
            .tabla td {{ border-bottom: 1px solid #ddd; padding: 10px; }}
            .total {{ text-align: right; margin-top: 30px; font-size: 22px; color: #d35400; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header"><span class="logo">🚛 CHACAGEST</span><div style="float:right"><b>PRESUPUESTO</b><br>{date.today()}</div></div>
        <p><b>CLIENTE:</b> {cliente}</p>
        <table class="tabla">
            <thead><tr><th>Cant.</th><th>Descripción</th><th>Precio Unit.</th><th>Subtotal</th></tr></thead>
            <tbody>{filas}</tbody>
        </table>
        <div class="total">TOTAL ESTIMADO: $ {total:,.2f}</div>
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
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame(columns=["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"])
    st.session_state.viajes = v if v is not None else pd.DataFrame(columns=["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"])

# --- 4. DISEÑO ---
st.markdown("<style>[data-testid='stSidebarNav'] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; }</style>", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### PANEL CHACAGEST")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v = cargar_datos()
        st.session_state.clientes, st.session_state.viajes = c, v
        st.rerun()
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = [{"title": f"🚛 {r['Cliente']}", "start": str(r['Fecha Viaje']), "allDay": True} for i, r in st.session_state.viajes.iterrows() if str(r['Fecha Viaje']) != "-"]
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *"); cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                if r and cuit:
                    nuevo = pd.DataFrame([[r, cuit, "", "", "", "", "", "Monotributo", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Guardado"); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha"); pat = st.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Registrado"); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Generador de Presupuestos")
    if "items_p" not in st.session_state: st.session_state.items_p = []
    
    cl_p = st.selectbox("Para el cliente:", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else ["Particular"])
    col1, col2, col3 = st.columns([1, 3, 1])
    c_p = col1.number_input("Cant", 1); d_p = col2.text_input("Detalle"); p_p = col3.number_input("Precio U.", 0.0)
    
    if st.button("➕ Añadir"):
        if d_p:
            st.session_state.items_p.append({"Cant": c_p, "Descripción": d_p, "Precio U.": p_p, "Subtotal": c_p * p_p})
            st.rerun()

    if st.session_state.items_p:
        df_p = pd.DataFrame(st.session_state.items_p)
        st.table(df_p)
        tot = df_p['Subtotal'].sum()
        st.subheader(f"Total: $ {tot:,.2f}")
        
        st.download_button("📄 DESCARGAR PDF (HTML)", generar_html_presupuesto(cl_p, st.session_state.items_p, tot), f"Ppto_{cl_p}.html", "text/html")
        if st.button("🗑️ Limpiar"):
            st.session_state.items_p = []; st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_i = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_i['Importe'].sum():,.2f}")
    st.dataframe(df_i, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i in reversed(st.session_state.viajes.index):
        r = st.session_state.viajes.loc[i]
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"**{r['Cliente']}** | {r['Fecha Viaje']} | ${r['Importe']}")
        if c2.button("🗑️", key=f"d_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()
