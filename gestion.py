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
            [cite_start]creds = Credentials.from_service_account_file("llave_google.json", scopes=scope) [cite: 1, 2]
        client = gspread.authorize(creds)
        return client.open(nombre_planilla)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def cargar_datos():
    [cite_start]col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"] [cite: 3]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"] # Nueva col tesorería
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None
        
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        [cite_start]df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c) [cite: 4]
        
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        try:
            ws_p = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            [cite_start]df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p) [cite: 5]
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=col_p)

        # Nueva carga para Tesorería
        try:
            ws_t = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)
            
        return df_c, df_v, df_p, df_t
    except:
        return None, None, None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        [cite_start]ws = sh.worksheet(nombre_hoja) [cite: 6]
        ws.clear()
        df_save = df.fillna("-").copy()
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos) 
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- FUNCIONES PARA REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    [cite_start]tabla_html = df.to_html(index=False, classes='tabla') [cite: 7]
    html = f"""
    <html>
    <head>
        <style>
            [cite_start]body {{ font-family: Arial, sans-serif; color: #333; }} [cite: 8]
            .header {{ background-color: #5e2d61; color: white; padding: 20px; text-align: center; border-radius: 10px; [cite_start]}} [cite: 9]
            .info {{ margin: 20px 0; font-size: 14px; [cite_start]}} [cite: 10]
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; [cite_start]}} [cite: 11]
            .tabla th {{ background-color: #f39c12; color: white; padding: 10px; text-align: left; [cite_start]}} [cite: 12]
            .tabla td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; [cite_start]}} [cite: 13]
            .total {{ text-align: right; font-size: 18px; color: #5e2d61; font-weight: bold; margin-top: 20px; [cite_start]}} [cite: 14]
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CHACAGEST - Resumen de Cuenta</h1>
            <p>Fecha de emisión: {date.today()}</p>
        </div>
        <div class="info">
            <p><b>Cliente:</b> {cliente}</p>
        [cite_start]</div> [cite: 15]
        {tabla_html}
        <div class="total"> SALDO TOTAL A LA FECHA: $ {saldo:,.2f} </div>
    </body>
    </html>
    """
    return html

def generar_html_recibo(data):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 30px; border: 2px solid #5e2d61; }}
            .header {{ text-align: center; border-bottom: 2px solid #5e2d61; margin-bottom: 20px; }}
            .monto-box {{ background: #f0f2f6; padding: 15px; font-size: 20px; font-weight: bold; text-align: center; border: 1px dashed #5e2d61; }}
        </style>
    </head>
    <body>
        <div class="header"><h2>RECIBO DE PAGO - CHACAGEST</h2></div>
        <p><b>Fecha:</b> {data['Fecha']}</p>
        <p><b>Recibimos de:</b> {data['Cliente/Proveedor']}</p>
        <p><b>Concepto:</b> {data['Concepto']}</p>
        <p><b>Medio:</b> {data['Caja/Banco']}</p>
        <p><b>Asoc. AFIP:</b> {data['Ref AFIP']}</p>
        <div class="monto-box">SON PESOS: $ {abs(data['Monto']):,.2f}</div>
    </body>
    </html>
    """
    return html

def generar_html_presupuesto(p_data):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; [cite_start]}} [cite: 16]
            .header {{ border-bottom: 3px solid #5e2d61; padding-bottom: 10px; margin-bottom: 20px; [cite_start]}} [cite: 17]
            .title {{ color: #5e2d61; font-size: 24px; font-weight: bold; [cite_start]}} [cite: 18]
            .box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-top: 20px; background-color: #f9f9f9; [cite_start]}} [cite: 19]
            .monto {{ font-size: 22px; color: #d35400; font-weight: bold; text-align: right; margin-top: 20px; [cite_start]}} [cite: 20]
            .footer {{ margin-top: 50px; font-size: 11px; color: #777; text-align: center; [cite_start]}} [cite: 21]
        </style>
    </head>
    <body>
        <div class="header">
            <span class="title">🚛 CHACAGEST - PRESUPUESTO</span>
            <div style="float: right; text-align: right; font-size: 12px;">
                Emisión: {p_data['Fecha Emisión']}<br>Válido hasta: {p_data['Vencimiento']}
            </div>
        [cite_start]</div> [cite: 22]
        <p><b>Señores:</b> {p_data['Cliente']}</p>
        <p><b>Unidad solicitada:</b> {p_data['Tipo Móvil']}</p>
        <div class="box">
            <b>Detalle del Servicio:</b><br>
            {p_data['Detalle']}
        </div>
        <div class="monto">TOTAL PRESUPUESTADO: $ {p_data['Importe']:,.2f}</div>
        [cite_start]<div class="footer">Este documento es un presupuesto estimativo y no representa una factura ni afecta el estado de cuenta corriente.</div> [cite: 23]
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
        [cite_start]p = st.text_input("Contraseña", type="password") [cite: 24]
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    [cite_start]c, v, p, t = cargar_datos() [cite: 25]
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.tesoreria = t if t is not None else pd.DataFrame()

# --- 4. DISEÑO ORIGINAL ---
st.markdown("""
    <style>
    [cite_start][data-testid="stSidebarNav"] { display: none; } [cite: 26]
    header { visibility: hidden; [cite_start]} [cite: 27] 
    h1, h2, h3 { color: #5e2d61 !important; [cite_start]} [cite: 28]
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        [cite_start]color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; [cite: 29, 30]
    }
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; [cite_start]} [cite: 31]
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERIA", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "safe", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={
            [cite_start]"container": {"background-color": "#f0f2f6"}, [cite: 32]
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )
    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        with st.spinner("Sincronizando..."):
            c, v, p, t = cargar_datos()
            [cite_start]if c is not None: [cite: 33]
                st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria = c, v, p, t
                st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state:
        st.session_state.viaje_ver = None
    [cite_start]eventos = [] [cite: 34]
    for i, row in st.session_state.viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({
                "id": str(i),
                "title": f"🚛 {row['Cliente']}",
                "start": str(row['Fecha Viaje']),
                [cite_start]"allDay": True, [cite: 35]
                "backgroundColor": "#f39c12",
                "borderColor": "#d35400"
            })
    cal_options = {"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es", "height": 600}
    [cite_start]custom_css = ".fc-button-primary { background-color: #5e2d61 !important; border-color: #5e2d61 !important; } .fc-event { background-color: #f39c12 !important; } .fc-toolbar-title { color: #5e2d61 !important; }" [cite: 36, 37]
    res_cal = calendar(events=eventos, options=cal_options, custom_css=custom_css, key="cal_final")
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])
    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar"): st.session_state.viaje_ver = None; st.rerun()
            [cite_start]st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-left: 5px solid #f39c12; border-radius: 5px; margin-top: 20px;"> [cite: 38]
                <h4 style="color: #5e2d61; margin: 0;">Detalles</h4><p><b>Cliente:</b> {v_det['Cliente']}</p><p><b>Ruta:</b> {v_det['Origen']} ➔ {v_det['Destino']}</p>
                <p><b>Importe:</b> $ {v_det['Importe']}</p></div>""", unsafe_allow_html=True)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            [cite_start]c1, c2 = st.columns(2); [cite: 39]
            r = c1.text_input("Razón Social *"); cuit = c2.text_input("CUIT *")
            [cite_start]mail = c1.text_input("Email"); tel = c2.text_input("Teléfono") [cite: 40]
            [cite_start]dir_f = c1.text_input("Dirección Fiscal"); loc = c2.text_input("Localidad") [cite: 41]
            [cite_start]prov = c1.text_input("Provincia"); c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"]) [cite: 42]
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=st.session_state.clientes.columns)
                    [cite_start]st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True) [cite: 43]
                    [cite_start]guardar_datos("clientes", st.session_state.clientes); st.success("Cliente guardado"); st.rerun() [cite: 44]
    
    st.subheader("📋 Base de Clientes")
    if not st.session_state.clientes.empty:
        for i, row in st.session_state.clientes.iterrows():
            with st.container():
                c_inf, c_ed, c_el = st.columns([0.7, 0.15, 0.15])
                c_inf.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT / CUIL / DNI *']}")
                [cite_start]c_inf.caption(f"📍 {row['Localidad']} - {row['Provincia']} | 📞 {row['Teléfono']}") [cite: 45]
                if c_ed.button("📝 Editar", key=f"edit_{i}"):
                    st.session_state[f"edit_mode_{i}"] = True
                [cite_start]if c_el.button("🗑️", key=f"del_cli_{i}"): [cite: 46]
                    tiene_viajes = not st.session_state.viajes[st.session_state.viajes['Cliente'] == row['Razón Social']].empty
                    [cite_start]if tiene_viajes: [cite: 47]
                        st.error("No se puede eliminar: tiene viajes asociados.")
                    else:
                        st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True)
                        [cite_start]guardar_datos("clientes", st.session_state.clientes) [cite: 48]
                        st.rerun()
                [cite_start]if st.session_state.get(f"edit_mode_{i}", False): [cite: 49]
                    with st.form(f"f_edit_{i}"):
                        ce1, ce2 = st.columns(2)
                        n_rs = ce1.text_input("Razón Social", value=row['Razón Social'])
                        n_cuit = ce2.text_input("CUIT", value=row['CUIT / CUIL / DNI *'])
                        [cite_start]n_mail = ce1.text_input("Email", value=row['Email']) [cite: 50]
                        n_tel = ce2.text_input("Teléfono", value=row['Teléfono'])
                        n_loc = ce1.text_input("Localidad", value=row['Localidad'])
                        [cite_start]n_prov = ce2.text_input("Provincia", value=row['Provincia']) [cite: 51]
                        be1, be2 = st.columns(2)
                        [cite_start]if be1.form_submit_button("✅ Guardar"): [cite: 52]
                            st.session_state.clientes.loc[i] = [n_rs, n_cuit, n_mail, n_tel, row['Dirección Fiscal'], n_loc, n_prov, row['Condición IVA'], row['Condición de Venta']]
                            guardar_datos("clientes", st.session_state.clientes)
                            st.session_state[f"edit_mode_{i}"] = False
                            [cite_start]st.rerun() [cite: 53]
                        if be2.form_submit_button("❌ Cancelar"):
                            st.session_state[f"edit_mode_{i}"] = False
                            st.rerun()
                [cite_start]st.divider() [cite: 54]
    else:
        st.info("No hay clientes registrados.")

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        [cite_start]c1, c2 = st.columns(2); [cite: 55]
        f_v = c1.date_input("Fecha"); pat = c2.text_input("Patente")
        [cite_start]orig = st.text_input("Origen"); dest = st.text_input("Destino") [cite: 56]
        imp = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            [cite_start]guardar_datos("viajes", st.session_state.viajes); st.success("Viaje registrado"); st.rerun() [cite: 57]

elif sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    tab_crear, tab_historial = st.tabs(["🆕 Crear Presupuesto", "📂 Historial y Descargas"])
    with tab_crear:
        with st.form("f_presu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            p_cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            [cite_start]p_f_emi = c2.date_input("Fecha Emisión", date.today()) [cite: 58]
            c3, c4 = st.columns(2)
            p_f_venc = c3.date_input("Fecha Vencimiento", date.today() + timedelta(days=7))
            p_movil = c4.selectbox("Tipo de Móvil", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            [cite_start]p_det = st.text_area("Detalle del Presupuesto (Servicio, Ruta, Horarios...)") [cite: 59]
            p_imp = st.number_input("Importe Total $", min_value=0.0)
            if st.form_submit_button("GENERAR PRESUPUESTO"):
                if p_cli and p_imp > 0:
                    nuevo_p = pd.DataFrame([[p_f_emi, p_cli, p_f_venc, p_det, p_movil, p_imp]], columns=st.session_state.presupuestos.columns)
                    [cite_start]st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, nuevo_p], ignore_index=True) [cite: 60]
                    guardar_datos("presupuestos", st.session_state.presupuestos)
                    st.success("Presupuesto guardado con éxito")
                    st.rerun()
    with tab_historial:
        [cite_start]if not st.session_state.presupuestos.empty: [cite: 61]
            for i in reversed(st.session_state.presupuestos.index):
                row_p = st.session_state.presupuestos.loc[i]
                with st.container():
                    c_a, c_b, c_c = st.columns([0.6, 0.2, 0.2])
                    [cite_start]c_a.markdown(f"**{row_p['Cliente']}** | {row_p['Tipo Móvil']}") [cite: 62]
                    c_a.caption(f"Emisión: {row_p['Fecha Emisión']} - Vence: {row_p['Vencimiento']}")
                    c_b.markdown(f"**$ {row_p['Importe']:,.2f}**")
                    [cite_start]html_p = generar_html_presupuesto(row_p) [cite: 63]
                    [cite_start]c_c.download_button(label="📄 Descargar", data=html_p, file_name=f"Presupuesto_{row_p['Cliente']}_{row_p['Fecha Emisión']}.html", mime="text/html", key=f"dl_p_{i}") [cite: 64]
                    [cite_start]if c_c.button("🗑️", key=f"del_p_{i}"): [cite: 65]
                        st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
                        guardar_datos("presupuestos", st.session_state.presupuestos)
                        st.rerun()
                    [cite_start]st.divider() [cite: 66]
        else: st.info("No hay presupuestos registrados.")

# --- NUEVO MÓDULO TESORERIA ---
elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    t1, t2, t3, t4, t5 = st.tabs(["📥 INGRESOS VARIOS", "📤 EGRESOS VARIOS", "🧾 COBRANZA VIAJE", "📊 VER MOVIMIENTOS", "🔄 TRASPASO"])

    with t1:
        with st.form("f_ing_var"):
            f = st.date_input("Fecha", date.today())
            cj = st.selectbox("Caja Destino", opc_cajas)
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR INGRESO"):
                nt = pd.DataFrame([[f, "INGRESO VARIO", cj, con, "Varios", mon, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); st.success("Registrado"); st.rerun()

    with t2:
        with st.form("f_egr_var"):
            f = st.date_input("Fecha", date.today())
            cj = st.selectbox("Caja Origen", opc_cajas)
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR EGRESO"):
                nt = pd.DataFrame([[f, "EGRESO VARIO", cj, con, "Varios", -mon, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); st.success("Registrado"); st.rerun()

    with t3:
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            cj = st.selectbox("Forma de Cobro", opc_cajas + ["OTROS"])
            mon = st.number_input("Monto $", min_value=0.0)
            afip = st.text_input("Comprobante Asociado (AFIP/Recibo)")
            if st.form_submit_button("GENERAR COBRANZA"):
                # Impacto Tesorería
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                # Impacto CTA CTE (negativo para restar deuda)
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Cobranza realizada")
                rec_html = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Concepto": "Cobro de Viaje", "Caja/Banco": cj, "Monto": mon, "Ref AFIP": afip})
                st.download_button("🖨️ IMPRIMIR RECIBO PDF/HTML", rec_html, file_name=f"Recibo_{c_sel}.html", mime="text/html")

    with t4:
        cj_v = st.selectbox("Seleccionar Caja", opc_cajas)
        df_ver = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj_v]
        st.metric(f"Saldo en {cj_v}", f"$ {df_ver['Monto'].sum():,.2f}")
        st.dataframe(df_ver, use_container_width=True)

    with t5:
        with st.form("f_tras"):
            o = st.selectbox("Desde", opc_cajas); d = st.selectbox("Hacia", opc_cajas)
            m = st.number_input("Monto a Traspasar", min_value=0.0)
            if st.form_submit_button("EJECUTAR"):
                t1 = pd.DataFrame([[date.today(), "TRASPASO", o, f"Hacia {d}", "INTERNO", -m, "-"]], columns=st.session_state.tesoreria.columns)
                t2 = pd.DataFrame([[date.today(), "TRASPASO", d, f"Desde {o}", "INTERNO", m, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, t1, t2], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
        [cite_start]st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}") [cite: 66]
        html_reporte = generar_html_resumen(cl, df_ind, df_ind['Importe'].sum())
        st.download_button(label="📄 DESCARGAR RESUMEN", data=html_reporte, file_name=f"Resumen_{cl}.html", mime="text/html")
        [cite_start]st.dataframe(df_ind, use_container_width=True) [cite: 67]

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Comprobantes")
    if not st.session_state.viajes.empty:
        for i in reversed(st.session_state.viajes.index):
            row = st.session_state.viajes.loc[i]
            [cite_start]c1, c2, c3 = st.columns([0.2, 0.6, 0.1]) [cite: 68]
            c1.write(f"📅 {row['Fecha Viaje']}")
            [cite_start]c2.write(f"👤 **{row['Cliente']}** | {row['Origen']} a {row['Destino']} | **${row['Importe']}**") [cite: 69]
            if c3.button("🗑️", key=f"del_{i}"):
                st.session_state.viajes = st.session_state.viajes.drop(i)
                guardar_datos("viajes", st.session_state.viajes); st.rerun()
            st.divider()
