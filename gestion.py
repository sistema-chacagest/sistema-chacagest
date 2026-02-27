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
    try:
        sh = conectar_google()
        if sh is None: return None, None, None
        
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
            
        return df_c, df_v, df_p
    except:
        return None, None, None

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

# --- REPORTE CTA CTE ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .tabla th {{ background-color: #f39c12; color: white; padding: 10px; }}
            .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
            .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>CHACAGEST - Resumen de Cuenta</h1><p>Emisión: {date.today()}</p></div>
        <p><b>Cliente:</b> {cliente}</p>
        {tabla_html}
        <div class="total">SALDO TOTAL: $ {saldo:,.2f}</div>
    </body>
    </html>
    """

# --- REPORTE PRESUPUESTO ---
def generar_html_presupuesto(p_data):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; border: 2px solid #5e2d61; }}
            .header {{ border-bottom: 3px solid #f39c12; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ color: #5e2d61; font-size: 24px; font-weight: bold; }}
            .monto {{ font-size: 22px; color: #d35400; font-weight: bold; text-align: right; }}
        </style>
    </head>
    <body>
        <div class="header"><span class="title">🚛 CHACAGEST - PRESUPUESTO</span></div>
        <p><b>Cliente:</b> {p_data['Cliente']}</p>
        <p><b>Válido hasta:</b> {p_data['Vencimiento']} | <b>Unidad:</b> {p_data['Tipo Móvil']}</p>
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 100px; border: 1px solid #ddd;">
            <b>Detalle del Servicio:</b><br>{p_data['Detalle']}
        </div>
        <div class="monto">TOTAL: $ {p_data['Importe']:,.2f}</div>
    </body>
    </html>
    """

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
if 'clientes' not in st.session_state or 'viajes' not in st.session_state or 'presupuestos' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()

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
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        c, v, p = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos = c, v, p
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
    calendar(events=eventos, options={"locale": "es", "height": 600}, key="cal")

elif sel == "CLIENTES":
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
    st.dataframe(st.session_state.clientes, use_container_width=True)
    
    # --- RESTAURADO: ELIMINAR CLIENTE ---
    with st.expander("🗑️ ELIMINAR CLIENTE"):
        if not st.session_state.clientes.empty:
            elim_c = st.selectbox("Seleccione cliente a borrar:", ["-"] + list(st.session_state.clientes['Razón Social'].unique()))
            if st.button("BORRAR PERMANENTEMENTE") and elim_c != "-":
                st.session_state.clientes = st.session_state.clientes[st.session_state.clientes['Razón Social'] != elim_c]
                guardar_datos("clientes", st.session_state.clientes)
                st.success(f"Cliente {elim_c} eliminado"); st.rerun()

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2); f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Viaje registrado"); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    t_c, t_h = st.tabs(["🆕 Crear", "📂 Historial"])
    with t_c:
        with st.form("f_p", clear_on_submit=True):
            c1, c2 = st.columns(2)
            p_cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            p_f_venc = c2.date_input("Vencimiento", date.today() + timedelta(days=7))
            p_movil = st.selectbox("Tipo de Móvil", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            p_det = st.text_area("Detalle")
            p_imp = st.number_input("Importe Total $", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                np = pd.DataFrame([[date.today(), p_cli, p_f_venc, p_det, p_movil, p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    with t_h:
        for i in reversed(st.session_state.presupuestos.index):
            row = st.session_state.presupuestos.loc[i]
            c_a, c_b = st.columns([0.8, 0.2])
            c_a.write(f"**{row['Cliente']}** | {row['Tipo Móvil']} | ${row['Importe']}")
            h_p = generar_html_presupuesto(row)
            c_b.download_button("📄 PDF", data=h_p, file_name=f"Presu_{i}.html", mime="text/html", key=f"dl_{i}")
            if c_b.button("🗑️", key=f"del_p_{i}"):
                st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
            st.divider()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
        st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
        h_r = generar_html_resumen(cl, df_ind, df_ind['Importe'].sum())
        st.download_button("📄 DESCARGAR RESUMEN", data=h_r, file_name=f"Resumen_{cl}.html", mime="text/html")
        st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    for i in reversed(st.session_state.viajes.index):
        row = st.session_state.viajes.loc[i]
        c1, c2, c3 = st.columns([0.2, 0.7, 0.1])
        c1.write(f"{row['Fecha Viaje']}")
        c2.write(f"**{row['Cliente']}** | {row['Origen']} a {row['Destino']} | **${row['Importe']}**")
        if c3.button("🗑️", key=f"d_v_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()
        st.divider()
