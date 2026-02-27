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

# --- FUNCIONES PARA REPORTES (HTML) ---
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
        <div class="header">
            <h1>CHACAGEST - Resumen de Cuenta</h1>
            <p>Fecha de emisión: {date.today()}</p>
        </div>
        <div class="info">
            <p><b>Cliente:</b> {cliente}</p>
        </div>
        {tabla_html}
        <div class="total"> SALDO TOTAL A LA FECHA: $ {saldo:,.2f} </div>
    </body>
    </html>
    """
    return html

def generar_html_presupuesto(cliente, detalles, total):
    filas_items = "".join([f"<tr><td>{i['Cant']}</td><td>{i['Descripción']}</td><td>$ {i['Precio U.']:,.2f}</td><td>$ {i['Subtotal']:,.2f}</td></tr>" for i in detalles])
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
        <div class="header">
            <span class="logo">🚛 CHACAGEST</span>
            <div style="float: right; text-align: right;"><b>PRESUPUESTO</b><br>Fecha: {date.today()}</div>
        </div>
        <p><b>CLIENTE:</b> {cliente}</p>
        <table class="tabla">
            <thead><tr><th>Cant.</th><th>Descripción</th><th>Precio Unit.</th><th>Subtotal</th></tr></thead>
            <tbody>{filas_items}</tbody>
        </table>
        <div class="total"> TOTAL ESTIMADO: $ {total:,.2f} </div>
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
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame(columns=["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"])
    st.session_state.viajes = v if v is not None else pd.DataFrame(columns=["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"])

# --- 4. DISEÑO ORIGINAL ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "PRESUPUESTOS"],
        icons=["calendar3", "people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text", "file-earmark-spreadsheet"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        with st.spinner("Sincronizando..."):
            c, v = cargar_datos()
            if c is not None:
                st.session_state.clientes, st.session_state.viajes = c, v
                st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state: st.session_state.viaje_ver = None
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({
                "id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']),
                "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"
            })
    res_cal = calendar(events=eventos, options={"locale": "es", "height": 600}, key="cal_final")
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])
    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar Información"):
                st.session_state.viaje_ver = None
                st.rerun()
            st.info(f"Viaje: {v_det['Cliente']} - {v_det['Origen']} a {v_det['Destino']} - $ {v_det['Importe']}")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT *")
            mail = c1.text_input("Email"); tel = c2.text_input("Teléfono")
            dir_f = c1.text_input("Dirección Fiscal"); loc = c2.text_input("Localidad")
            prov = c1.text_input("Provincia")
            c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.success("Cliente guardado"); st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v = c1.date_input("Fecha del Viaje"); pat = c2.text_input("Patente / Móvil")
        orig = st.text_input("Origen"); dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje registrado"); st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito")
    st.info("Nota: Las Notas de Crédito y Débito deben estar asociadas a un comprobante AFIP.")
    tipo = st.radio("Acción:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        nro_asoc = st.text_input("Nro Comprobante AFIP Asociado *")
        mot = st.text_input("Motivo / Concepto"); monto = st.number_input("Monto $", min_value=0.0)
        if st.form_submit_button("REGISTRAR AJUSTE"):
            if nro_asoc:
                val = -monto if "Crédito" in tipo else monto
                t_txt = "NC" if "Crédito" in tipo else "ND"
                nc = pd.DataFrame([[date.today(), cl, date.today(), "AJUSTE", mot, "-", val, t_txt, nro_asoc]], columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Ajuste cargado correctamente"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
    saldo_total = df_ind['Importe'].sum()
    st.metric("SALDO TOTAL", f"$ {saldo_total:,.2f}")
    st.download_button("📄 DESCARGAR RESUMEN", generar_html_resumen(cl, df_ind, saldo_total), f"Resumen_{cl}.html", "text/html")
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
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.viajes = st.session_state.viajes.drop(i)
            guardar_datos("viajes", st.session_state.viajes)
            st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Generador de Presupuestos")
    if "ppto_items" not in st.session_state: st.session_state.ppto_items = []
    
    cl_p = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else ["Particular"])
    col1, col2, col3 = st.columns([1, 3, 1])
    cant = col1.number_input("Cant", 1)
    desc = col2.text_input("Descripción")
    prec = col3.number_input("Precio Unit. $", 0.0)
    
    if st.button("➕ Agregar"):
        if desc:
            st.session_state.ppto_items.append({"Cant": cant, "Descripción": desc, "Precio U.": prec, "Subtotal": cant * prec})
            st.rerun()
            
    if st.session_state.ppto_items:
        df_p = pd.DataFrame(st.session_state.ppto_items)
        st.table(df_p)
        total_p = df_p['Subtotal'].sum()
        st.subheader(f"Total: $ {total_p:,.2f}")
        st.download_button("📄 DESCARGAR PDF (HTML)", generar_html_presupuesto(cl_p, st.session_state.ppto_items, total_p), f"Presupuesto_{cl_p}.html", "text/html")
        if st.button("🗑️ Limpiar"):
            st.session_state.ppto_items = []; st.rerun()
