import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64
from fpdf import FPDF # Importación de la librería para PDF

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

        try:
            ws_t = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)

        try:
            ws_prov = sh.worksheet("proveedores")
            datos_prov = ws_prov.get_all_records()
            df_prov = pd.DataFrame(datos_prov) if datos_prov else pd.DataFrame(columns=col_prov)
        except:
            df_prov = pd.DataFrame(columns=col_prov)

        try:
            ws_com = sh.worksheet("compras")
            datos_com = ws_com.get_all_records()
            df_com = pd.DataFrame(datos_com) if datos_com else pd.DataFrame(columns=col_compras)
            for c in ["Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]:
                df_com[c] = pd.to_numeric(df_com[c], errors='coerce').fillna(0)
        except:
            df_com = pd.DataFrame(columns=col_compras)
            
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

# =========================================================
# --- FUNCIÓN GENERADORA DE PDF ---
# =========================================================
def generar_pdf_chacagest(tipo_doc, entidad, detalle, monto, referencia="", fecha_venc=""):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Morado
    pdf.set_fill_color(94, 45, 97)
    pdf.rect(0, 0, 210, 40, 'F')
    
    # Logo / Nombre Empresa
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, "CHACABUCO NOROESTE TOUR S.R.L.", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "VIAJES ESPECIALES - TURISMO - TRASLADOS", ln=True)
    
    # Cuadro de Tipo de Comprobante
    pdf.set_xy(150, 10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, tipo_doc.upper(), border=1, ln=True, align='C')
    pdf.set_xy(150, 22)
    pdf.set_font("Arial", "", 9)
    pdf.cell(50, 5, f"Fecha: {date.today()}", ln=True, align='R')
    
    # Cuerpo
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(50)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"DESTINATARIO: {entidad}", ln=True)
    if referencia:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 7, f"Ref: {referencia}", ln=True)
    if fecha_venc:
        pdf.cell(0, 7, f"Vencimiento: {fecha_venc}", ln=True)
        
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "DETALLE:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, str(detalle), border=1)
    
    # Importe Total
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(211, 84, 0) # Naranja
    pdf.cell(130, 10, "", ln=0)
    pdf.cell(60, 12, f"TOTAL: $ {abs(monto):,.2f}", border=1, ln=True, align='C')
    
    # Pie de página
    pdf.set_y(-40)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(120, 120, 120)
    if tipo_doc == "Presupuesto":
        pdf.multi_cell(0, 4, "Condiciones: Seña del 30% para reserva. Gastos de choferes a cargo del contratante.")
    
    pdf.set_y(-20)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 10, "Sistema de Gestión CHACAGEST - Chacabuco, Buenos Aires.", ln=True, align='C')
    
    return pdf.output()

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
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.tesoreria = t if t is not None else pd.DataFrame()
    st.session_state.proveedores = prov if prov is not None else pd.DataFrame()
    st.session_state.compras = com if com is not None else pd.DataFrame()

# --- 4. DISEÑO ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
    header { visibility: hidden; } 
    h1, h2, h3 { color: #5e2d61 !important; }
    div.stButton > button {
        background: linear-gradient(to right, #f39c12, #d35400) !important;
        color: white !important; 
        border-radius: 8px !important; 
        border: none !important; 
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    
    opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
    menu_principal = option_menu(None, opciones_menu, icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0, styles={"nav-link-selected": {"background-color": "#5e2d61"}})

    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-earmark", "person-vcard", "globe", "file-text"], key="v")
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"], key="c")

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        c, v, p, t, prov, com = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com
        st.rerun()
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False; st.rerun()

sel = sel_sub if sel_sub else menu_principal

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, row in st.session_state.viajes[st.session_state.viajes['Importe'] > 0].iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es"}, key="cal")

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR"):
                nueva = pd.DataFrame([[r, cuit, "", "", "", "", "", "RI", "CC"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.success("Guardado")

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    tab1, tab2 = st.tabs(["Crear", "Historial"])
    with tab1:
        with st.form("f_p", clear_on_submit=True):
            p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            p_movil = st.selectbox("Móvil", ["Combi 19", "Minibus 24", "Micro 45", "Micro 60"])
            p_det = st.text_area("Detalle del Viaje")
            p_imp = st.number_input("Importe Total $", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                nuevo = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(7), p_det, p_movil, p_imp]], columns=st.session_state.presupuestos.columns)
                st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, nuevo], ignore_index=True)
                guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun()
    with tab2:
        for i, row in st.session_state.presupuestos.iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"**{row['Cliente']}** - {row['Tipo Móvil']} - ${row['Importe']}")
            pdf_bytes = generar_pdf_chacagest("Presupuesto", row['Cliente'], row['Detalle'], row['Importe'], row['Tipo Móvil'], row['Vencimiento'])
            c2.download_button("📄 PDF", pdf_bytes, f"Presupuesto_{row['Cliente']}.pdf", "application/pdf", key=f"p_{i}")

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    t1, t2, t3 = st.tabs(["COBRANZA", "PAGO PROVEEDOR", "MOVIMIENTOS"])
    
    with t1:
        with st.form("f_cob"):
            cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
            mon = st.number_input("Monto $", min_value=0.0)
            ref = st.text_input("Ref AFIP")
            if st.form_submit_button("REGISTRAR COBRO"):
                nt = pd.DataFrame([[date.today(), "COBRANZA", "CAJA", "Cobro", cli, mon, ref]], columns=st.session_state.tesoreria.columns)
                nv = pd.DataFrame([[date.today(), cli, date.today(), "PAGO", "TESO", "-", -mon, "RECIBO", ref]], columns=st.session_state.viajes.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                guardar_datos("viajes", st.session_state.viajes)
                st.success("Cobro registrado")
                
                pdf_recibo = generar_pdf_chacagest("Recibo de Pago", cli, "Cobro por servicios de transporte varios.", mon, ref)
                st.download_button("📩 Descargar Recibo PDF", pdf_recibo, f"Recibo_{cli}.pdf", "application/pdf")

    with t2:
        with st.form("f_op"):
            prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            mon = st.number_input("Monto a Pagar $", min_value=0.0)
            ref_p = st.text_input("Referencia")
            if st.form_submit_button("GENERAR ORDEN DE PAGO"):
                nt = pd.DataFrame([[date.today(), "PAGO PROV", "CAJA", "Pago", prov, -mon, ref_p]], columns=st.session_state.tesoreria.columns)
                nc = pd.DataFrame([[date.today(), prov, "-", "PAGO", 0, 0, 0, 0, 0, 0, -mon]], columns=st.session_state.compras.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.compras = pd.concat([st.session_state.compras, nc], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                guardar_datos("compras", st.session_state.compras)
                st.success("Pago registrado")
                
                pdf_op = generar_pdf_chacagest("Orden de Pago", prov, "Pago de facturas / gastos varios.", mon, ref_p)
                st.download_button("📩 Descargar OP PDF", pdf_op, f"OrdenPago_{prov}.pdf", "application/pdf")

    with t3:
        st.dataframe(st.session_state.tesoreria)

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cta Cte Cliente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_c = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_c['Importe'].sum():,.2f}")
    st.dataframe(df_c)

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Proveedores")
    with st.form("f_prov"):
        rs = st.text_input("Razón Social")
        cuit = st.text_input("CUIT")
        if st.form_submit_button("REGISTRAR"):
            np = pd.DataFrame([[rs, cuit, "VARIOS", "RI"]], columns=st.session_state.proveedores.columns)
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
            guardar_datos("proveedores", st.session_state.proveedores); st.rerun()

elif sel == "CARGA GASTOS":
    st.header("💸 Carga Gastos")
    with st.form("f_g"):
        p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
        t_f = st.selectbox("Tipo", ["A", "B", "C", "NOTA DE CREDITO", "NOTA DE DEBITO"])
        neto = st.number_input("Neto $", min_value=0.0)
        total = neto * 1.21 if t_f == "A" else neto
        if t_f == "NOTA DE CREDITO": total = -total
        if st.form_submit_button("REGISTRAR"):
            # Nota de débito y crédito asociadas según requerimiento
            ng = pd.DataFrame([[date.today(), p, "001", t_f, neto, 0, 0, 0, 0, 0, total]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras); st.success("Cargado")

elif sel == "CTA CTE PROVEEDOR":
    st.header("📊 Cta Cte Proveedor")
    p = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.compras[st.session_state.compras['Proveedor'] == p]
    st.metric("SALDO", f"$ {df_p['Total'].sum():,.2f}")
    st.dataframe(df_p)
