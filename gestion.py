import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64
from io import BytesIO
from xhtml2pdf import pisa # Nueva librería para PDF

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide") [cite: 1]

def exportar_a_pdf(html_content):
    """Convierte un string HTML a bytes de PDF para descarga."""
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def conectar_google():
    nombre_planilla = "Base_Chacagest" [cite: 2]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"] [cite: 2]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope) [cite: 2]
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope) [cite: 2]
        client = gspread.authorize(creds) [cite: 2]
        return client.open(nombre_planilla) [cite: 2]
    except Exception as e:
        st.error(f"Error de conexión: {e}") [cite: 2]
        return None

def cargar_datos():
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"] [cite: 2]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"] [cite: 2]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"] [cite: 2, 3]
    col_t = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"] [cite: 3]
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"] [cite: 3]
    col_compras = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"] [cite: 3]

    try:
        sh = conectar_google() [cite: 4]
        if sh is None: return None, None, None, None, None, None [cite: 4]
        
        ws_c = sh.worksheet("clientes") [cite: 4]
        datos_c = ws_c.get_all_records() [cite: 4]
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c) [cite: 4]
        
        ws_v = sh.worksheet("viajes") [cite: 4]
        datos_v = ws_v.get_all_records() [cite: 4]
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v) [cite: 4]
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0) [cite: 4]

        try:
            ws_p = sh.worksheet("presupuestos") [cite: 5]
            datos_p = ws_p.get_all_records() [cite: 5]
            df_p = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=col_p) [cite: 5]
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0) [cite: 5]
        except:
            df_p = pd.DataFrame(columns=col_p) [cite: 5]

        try:
            ws_t = sh.worksheet("tesoreria") [cite: 5]
            datos_t = ws_t.get_all_records() [cite: 6]
            df_t = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=col_t) [cite: 6]
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0) [cite: 6]
        except:
            df_t = pd.DataFrame(columns=col_t) [cite: 6]

        try:
            ws_prov = sh.worksheet("proveedores") [cite: 6]
            datos_prov = ws_prov.get_all_records() [cite: 7]
            df_prov = pd.DataFrame(datos_prov) if datos_prov else pd.DataFrame(columns=col_prov) [cite: 7]
        except:
            df_prov = pd.DataFrame(columns=col_prov) [cite: 7]

        try:
            ws_com = sh.worksheet("compras") [cite: 7]
            datos_com = ws_com.get_all_records() [cite: 7]
            df_com = pd.DataFrame(datos_com) if datos_com else pd.DataFrame(columns=col_compras) [cite: 7]
            for c in ["Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]: [cite: 8]
                df_com[c] = pd.to_numeric(df_com[c], errors='coerce').fillna(0) [cite: 8]
        except:
            df_com = pd.DataFrame(columns=col_compras) [cite: 8]
            
        return df_c, df_v, df_p, df_t, df_prov, df_com [cite: 8]
    except:
        return None, None, None, None, None, None [cite: 9]

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google() [cite: 9]
        if sh is None: return False [cite: 9]
        ws = sh.worksheet(nombre_hoja) [cite: 9]
        ws.clear() [cite: 9]
        df_save = df.fillna("-").copy() [cite: 9]
        datos = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist() [cite: 9]
        ws.update(datos) [cite: 9]
        return True [cite: 9]
    except Exception as e:
        st.error(f"Error al guardar: {e}") [cite: 10]
        return False [cite: 10]

# --- FUNCIONES PARA REPORTES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla') [cite: 10]
    return f"""
    <html><head><style>
    body {{ font-family: Helvetica; color: #333; padding: 20px; }}
    .header-table {{ width: 100%; border-bottom: 4px solid #5e2d61; margin-bottom: 20px; }}
    .empresa-name {{ color: #5e2d61; font-size: 22px; font-weight: bold; }}
    .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    .tabla th {{ background-color: #f8f9fa; color: #5e2d61; border-bottom: 2px solid #5e2d61; padding: 8px; text-align: left; }}
    .tabla td {{ border-bottom: 1px solid #eee; padding: 8px; font-size: 10px; }}
    .footer-resumen {{ margin-top: 30px; padding: 15px; background: #5e2d61; color: white; text-align: right; }}
    </style></head><body>
    <table class="header-table"><tr><td><p class="empresa-name">CHACABUCO NOROESTE TOUR S.R.L.</p></td><td style="text-align: right;"><b>ESTADO DE CUENTA</b><br>Emisión: {date.today()}</td></tr></table>
    <p><b>CLIENTE:</b> {cliente}</p>{tabla_html}
    <div class="footer-resumen">SALDO TOTAL PENDIENTE: <b>$ {saldo:,.2f}</b></div>
    </body></html>""" [cite: 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

def generar_html_recibo(data):
    return f"""
    <html><head><style>
    body {{ font-family: Helvetica; padding: 20px; }}
    .recibo-box {{ border: 2px solid #5e2d61; padding: 20px; }}
    .header {{ border-bottom: 1px solid #ccc; padding-bottom: 10px; }}
    .monto {{ font-size: 24px; color: #5e2d61; font-weight: bold; text-align: right; }}
    </style></head><body>
    <div class="recibo-box">
        <div class="header"><b>CHACABUCO NOROESTE TOUR S.R.L.</b><br>CUIT 30-71114824-4</div>
        <div class="monto">$ {abs(data['Monto']):,.2f}</div>
        <h2 style="text-align: center;">RECIBO DE PAGO</h2>
        <p>Recibimos de <b>{data['Cliente/Proveedor']}</b> la cantidad de pesos <b>{abs(data['Monto']):,.2f}</b> en concepto de: {data['Concepto']}.</p>
        <p>Medio: {data['Caja/Banco']} | Ref AFIP: {data['Ref AFIP']}</p>
        <p><b>FECHA:</b> {data['Fecha']}</p>
    </div></body></html>""" [cite: 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]

def generar_html_orden_pago(data):
    return f"""
    <html><head><style>body {{ font-family: Helvetica; padding: 20px; }} .op-box {{ border: 2px solid #d35400; padding: 20px; }}</style></head><body>
    <div class="op-box">
        <h2 style="color: #d35400;">ORDEN DE PAGO</h2>
        <p><b>PROVEEDOR:</b> {data['Proveedor']}</p>
        <p><b>CONCEPTO:</b> {data['Concepto']} | <b>FECHA:</b> {data['Fecha']}</p>
        <p><b>REFERENCIA AFIP:</b> {data['Ref AFIP']}</p>
        <h3 style="background: #fff4e6; padding: 10px;">TOTAL PAGADO: $ {abs(data['Monto']):,.2f}</h3>
    </div></body></html>""" [cite: 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

def generar_html_presupuesto(p_data):
    return f"""
    <html><head><style>body {{ font-family: Helvetica; padding: 30px; }} .border {{ border: 1px solid #ddd; padding: 20px; }} .total {{ color: #d35400; font-size: 20px; }}</style></head><body>
    <div class="border">
        <h1>CHACABUCO NOROESTE TOUR S.R.L.</h1>
        <p><b>PRESUPUESTO PARA:</b> {p_data['Cliente']}</p>
        <p><b>UNIDAD:</b> {p_data['Tipo Móvil']} | <b>VENCE:</b> {p_data['Vencimiento']}</p>
        <div style="background: #f9f9f9; padding: 15px; margin: 10px 0;">{str(p_data['Detalle']).replace('\n', '<br>')}</div>
        <p class="total">TOTAL: $ {p_data['Importe']:,.2f}</p>
    </div></body></html>""" [cite: 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]

# --- 2. LOGIN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario") [cite: 67]
        p = st.text_input("Contraseña", type="password") [cite: 67]
        if st.button("INGRESAR"): [cite: 67]
            if u == "admin" and p == "chaca2026": [cite: 67]
                st.session_state.autenticado = True [cite: 67]
                st.rerun() [cite: 67]
            else: st.error("Acceso denegado") [cite: 67]
    st.stop() [cite: 68]

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos() [cite: 68]
    st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com [cite: 68, 69]

# --- 4. DISEÑO ---
st.markdown("""<style>[data-testid="stSidebarNav"] { display: none; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; font-weight: bold !important; }</style>""", unsafe_allow_html=True) [cite: 70, 71, 72, 73]

# --- 5. SIDEBAR ---
with st.sidebar:
    menu_principal = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0) [cite: 74, 75]
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"], default_index=0) [cite: 76, 77]
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"], default_index=0) [cite: 78, 79]
    if st.button("🔄 Sincronizar"): [cite: 80]
        c, v, p, t, prov, com = cargar_datos(); st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com; st.rerun() [cite: 80]
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun() [cite: 80]

sel = sel_sub if menu_principal in ["VENTAS", "COMPRAS"] else menu_principal [cite: 81]

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    df_v = st.session_state.viajes
    for i, row in df_v[df_v['Importe'] > 0].iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "allDay": True, "backgroundColor": "#f39c12"}) [cite: 81, 82]
    calendar(events=eventos, options={"locale": "es"}, key="cal_final") [cite: 83, 84]

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *") [cite: 86]
            cuit = st.text_input("CUIT *") [cite: 86]
            if st.form_submit_button("REGISTRAR"):
                if r and cuit:
                    nf = pd.DataFrame([[r, cuit, "", "", "", "", "", "Monotributo", "Cuenta Corriente"]], columns=st.session_state.clientes.columns) [cite: 87, 88]
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nf], ignore_index=True); guardar_datos("clientes", st.session_state.clientes); st.rerun() [cite: 88]
    st.dataframe(st.session_state.clientes, use_container_width=True) [cite: 89]

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique()) [cite: 97]
        f_v = st.date_input("Fecha") [cite: 98]
        imp = st.number_input("Importe Neto $", min_value=0.0) [cite: 98]
        if st.form_submit_button("GUARDAR"):
            nv = pd.DataFrame([[date.today(), cli, f_v, "Origen", "Destino", "Patente", imp, "Factura", "-"]], columns=st.session_state.viajes.columns) [cite: 98, 99]
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True); guardar_datos("viajes", st.session_state.viajes); st.success("Registrado"); st.rerun() [cite: 99, 100]

elif sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    with st.form("f_presu", clear_on_submit=True):
        p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique()) [cite: 101]
        p_det = st.text_area("Detalle") [cite: 102]
        p_imp = st.number_input("Importe $", min_value=0.0) [cite: 102]
        if st.form_submit_button("GENERAR"):
            np = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(7), p_det, "Combi", p_imp]], columns=st.session_state.presupuestos.columns) [cite: 102, 103]
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True); guardar_datos("presupuestos", st.session_state.presupuestos); st.rerun() [cite: 103, 104]
    
    for i in reversed(st.session_state.presupuestos.index):
        row_p = st.session_state.presupuestos.loc[i]
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"**{row_p['Cliente']}** - $ {row_p['Importe']}") [cite: 105]
        # EXPORTACIÓN PDF
        html_p = generar_html_presupuesto(row_p)
        pdf_p = exportar_a_pdf(html_p)
        if pdf_p:
            c2.download_button("📄 PDF", pdf_p, file_name=f"Presu_{row_p['Cliente']}.pdf", mime="application/pdf", key=f"dl_p_{i}") [cite: 106]
        st.divider()

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    t1, t2, t3 = st.tabs(["📥 COBRANZA VIAJE", "💸 ORDEN DE PAGO", "📊 SALDOS"])
    
    with t1:
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique()) [cite: 113]
            cj = st.selectbox("Caja", ["CAJA COTI", "BANCO GALICIA"]) [cite: 113]
            mon = st.number_input("Monto $", min_value=0.0) [cite: 113]
            afip = st.text_input("Ref AFIP") [cite: 113]
            if st.form_submit_button("GENERAR"):
                nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns) [cite: 113, 114]
                nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns) [cite: 114]
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True) [cite: 114]
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True) [cite: 114]
                guardar_datos("tesoreria", st.session_state.tesoreria); guardar_datos("viajes", st.session_state.viajes) [cite: 114]
                # EXPORTACIÓN PDF
                html_rec = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Concepto": "Cobro Viaje", "Caja/Banco": cj, "Monto": mon, "Ref AFIP": afip})
                pdf_rec = exportar_a_pdf(html_rec)
                if pdf_rec:
                    st.download_button("🖨️ DESCARGAR RECIBO PDF", pdf_rec, file_name=f"Recibo_{c_sel}.pdf", mime="application/pdf") [cite: 115]

    with t2:
        with st.form("f_op"):
            p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique()) [cite: 119]
            mon_p = st.number_input("Monto $", min_value=0.0) [cite: 119]
            afip_p = st.text_input("Ref AFIP / Pago") [cite: 119]
            if st.form_submit_button("GENERAR ORDEN PAGO"):
                nt = pd.DataFrame([[date.today(), "PAGO PROV", "CAJA", "OP", p_sel, -mon_p, afip_p]], columns=st.session_state.tesoreria.columns) [cite: 120]
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True); guardar_datos("tesoreria", st.session_state.tesoreria) [cite: 121]
                # EXPORTACIÓN PDF
                html_op = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Concepto": "Pago Proveedor", "Caja/Banco": "Caja", "Monto": mon_p, "Ref AFIP": afip_p})
                pdf_op = exportar_a_pdf(html_op)
                if pdf_op:
                    st.download_button("🖨️ DESCARGAR OP PDF", pdf_op, file_name=f"OP_{p_sel}.pdf", mime="application/pdf") [cite: 122]

    with t3:
        st.dataframe(st.session_state.tesoreria, use_container_width=True) [cite: 116]

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique()) [cite: 123]
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl] [cite: 123]
    saldo = df_ind['Importe'].sum() [cite: 123]
    st.metric("SALDO", f"$ {saldo:,.2f}") [cite: 123]
    # EXPORTACIÓN PDF
    html_res = generar_html_resumen(cl, df_ind, saldo)
    pdf_res = exportar_a_pdf(html_res)
    if pdf_res:
        st.download_button("📄 DESCARGAR RESUMEN PDF", pdf_res, file_name=f"Resumen_{cl}.pdf", mime="application/pdf") [cite: 123]
    st.dataframe(df_ind, use_container_width=True) [cite: 123]

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Proveedores")
    with st.form("f_prov"):
        rs = st.text_input("Razón Social") [cite: 127]
        doc = st.text_input("CUIT") [cite: 127]
        if st.form_submit_button("REGISTRAR"):
            np = pd.DataFrame([[rs, doc, "VARIOS", "Monotributo"]], columns=st.session_state.proveedores.columns) [cite: 128]
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True); guardar_datos("proveedores", st.session_state.proveedores); st.rerun() [cite: 129, 130]
    st.dataframe(st.session_state.proveedores, use_container_width=True) [cite: 131]

elif sel == "CARGA GASTOS":
    st.header("💸 Gastos")
    with st.form("f_gasto"):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique()) [cite: 136]
        tipo_f = st.selectbox("Tipo", ["A", "B", "C", "NOTA DE CREDITO", "NOTA DE DEBITO"]) [cite: 137]
        total = st.number_input("Total $", min_value=0.0) [cite: 138]
        if st.form_submit_button("GUARDAR"):
            if tipo_f == "NOTA DE CREDITO": total = -total [cite: 138]
            ng = pd.DataFrame([[date.today(), prov_sel, "0001", tipo_f, 0, 0, 0, 0, 0, 0, total]], columns=st.session_state.compras.columns) [cite: 138, 139]
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True); guardar_datos("compras", st.session_state.compras); st.rerun() [cite: 139, 140]

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Histórico de Gastos")
    st.dataframe(st.session_state.compras, use_container_width=True) [cite: 142]
