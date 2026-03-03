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

# --- FUNCIONES HTML ---
def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"<html><head><style>body {{ font-family: 'Segoe UI'; color: #333; padding: 20px; }}.header-table {{ width: 100%; border-bottom: 4px solid #5e2d61; }}.empresa-name {{ color: #5e2d61; font-size: 26px; font-weight: bold; }}.tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}.tabla th {{ background-color: #f8f9fa; color: #5e2d61; border-bottom: 2px solid #5e2d61; padding: 12px; }}.tabla td {{ border-bottom: 1px solid #eee; padding: 10px; }}.footer-resumen {{ margin-top: 30px; padding: 15px; background: #5e2d61; color: white; border-radius: 8px; text-align: right; }}</style></head><body><table class=\"header-table\"><tr><td><p class=\"empresa-name\">CHACABUCO NOROESTE TOUR S.R.L.</p></td><td style=\"text-align: right;\"><p><b>ESTADO DE CUENTA</b><br>Emisión: {date.today()}</p></td></tr></table><p><b>CLIENTE:</b> {cliente}</p>{tabla_html}<div class=\"footer-resumen\">SALDO TOTAL PENDIENTE: $ {saldo:,.2f}</div></body></html>"

def generar_html_recibo(data):
    return f"<html><head><style>body {{ font-family: Arial; padding: 20px; }}.recibo-box {{ border: 3px double #5e2d61; padding: 30px; }}.monto-destacado {{ font-size: 28px; color: #5e2d61; background: #f0f2f6; padding: 10px; }}</style></head><body><div class=\"recibo-box\"><h2>CHACABUCO NOROESTE TOUR S.R.L.</h2><div class=\"monto-destacado\">$ {abs(data['Monto']):,.2f}</div><p>Recibimos de <b>{data['Cliente/Proveedor']}</b> el importe por <b>{data['Concepto']}</b>.</p><p>Ref AFIP: {data['Ref AFIP']}</p><p>Fecha: {data['Fecha']}</p></div></body></html>"

def generar_html_orden_pago(data):
    return f"<html><head><style>body {{ font-family: Arial; padding: 20px; }}.op-container {{ border: 2px solid #d35400; padding: 30px; }}</style></head><body><div class=\"op-container\"><h2>ORDEN DE PAGO</h2><p>Proveedor: {data['Proveedor']}</p><p>Monto: $ {abs(data['Monto']):,.2f}</p></div></body></html>"

def generar_html_presupuesto(p_data):
    return f"<html><head><style>body {{ font-family: sans-serif; padding: 30px; }}.main-border {{ border-top: 10px solid #f39c12; padding: 20px; }}</style></head><body><div class=\"main-border\"><h1>PRESUPUESTO</h1><p>Cliente: {p_data['Cliente']}</p><p>Detalle: {p_data['Detalle']}</p><h3>Total: $ {p_data['Importe']:,.2f}</h3></div></body></html>"

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
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c if c is not None else pd.DataFrame()
    st.session_state.viajes = v if v is not None else pd.DataFrame()
    st.session_state.presupuestos = p if p is not None else pd.DataFrame()
    st.session_state.tesoreria = t if t is not None else pd.DataFrame()
    st.session_state.proveedores = prov if prov is not None else pd.DataFrame()
    st.session_state.compras = com if com is not None else pd.DataFrame()

# --- 4. DISEÑO ---
st.markdown("""<style>[data-testid="stSidebarNav"] { display: none; } header { visibility: hidden; } h1, h2, h3 { color: #5e2d61 !important; } div.stButton > button { background: linear-gradient(to right, #f39c12, #d35400) !important; color: white !important; border-radius: 8px !important; font-weight: bold !important; }</style>""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")
    opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
    menu_principal = option_menu(None, opciones_menu, icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0, styles={"nav-link-selected": {"background-color": "#5e2d61"}})
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"], default_index=0)
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock-history"], default_index=0)
    
    if st.button("🔄 Sincronizar"):
        c, v, p, t, prov, com = cargar_datos()
        st.session_state.update({"clientes": c, "viajes": v, "presupuestos": p, "tesoreria": t, "proveedores": prov, "compras": com})
        st.rerun()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

sel = sel_sub if menu_principal in ["VENTAS", "COMPRAS"] else menu_principal

# --- 6. MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    df_solo_viajes = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in df_solo_viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({"id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']), "backgroundColor": "#f39c12"})
    calendar(events=eventos, options={"locale": "es", "height": 600})

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE"):
        with st.form("f_cli", clear_on_submit=True):
            r = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *")
            if st.form_submit_button("REGISTRAR CLIENTE") and r and cuit:
                nueva_fila = pd.DataFrame([[r, cuit, "", "", "", "", "", "Monotributo", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes)
                st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        f_v = st.date_input("Fecha")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe $", min_value=0.0)
        if st.form_submit_button("GUARDAR VIAJE"):
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Viaje registrado"); st.rerun()

elif sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    with st.form("f_presu", clear_on_submit=True):
        p_cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        p_det = st.text_area("Detalle")
        p_imp = st.number_input("Importe Total $", min_value=0.0)
        if st.form_submit_button("GENERAR"):
            nuevo_p = pd.DataFrame([[date.today(), p_cli, date.today()+timedelta(7), p_det, "Combi", p_imp]], columns=st.session_state.presupuestos.columns)
            st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, nuevo_p], ignore_index=True)
            guardar_datos("presupuestos", st.session_state.presupuestos)
            st.rerun()
    st.dataframe(st.session_state.presupuestos)

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    opc_cajas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "TARJETA DE CREDITO", "BANCO SUPERVIELLE", "DOLAR CAJA COTI", "DOLAR CAJA TATO"]
    t1, t2, t3, t4 = st.tabs(["📥 INGRESOS/EGRESOS", "🧾 COBRANZA VIAJE", "📊 VER MOVIMIENTOS", "💸 ORDEN DE PAGO"])
   
    with t1:
        with st.form("f_var"):
            tipo = st.selectbox("Tipo", ["INGRESO VARIO", "EGRESO VARIO"])
            cj = st.selectbox("Caja", opc_cajas)
            mon = st.number_input("Monto", min_value=0.0)
            if st.form_submit_button("REGISTRAR"):
                m_final = mon if "INGRESO" in tipo else -mon
                nt = pd.DataFrame([[date.today(), tipo, cj, "Varios", "Varios", m_final, "-"]], columns=st.session_state.tesoreria.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                st.rerun()

    with t2:
        # REPARACIÓN DEL ERROR DE REGISTRO
        if "html_recibo_ready" not in st.session_state: st.session_state.html_recibo_ready = None
        with st.form("f_cob"):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            cj = st.selectbox("Caja", opc_cajas)
            mon = st.number_input("Monto $", min_value=0.0)
            afip = st.text_input("Ref AFIP")
            if st.form_submit_button("GENERAR COBRANZA"):
                if mon > 0:
                    # 1. Crear dataframes
                    nt = pd.DataFrame([[date.today(), "COBRANZA", cj, "Cobro Viaje", c_sel, mon, afip]], columns=st.session_state.tesoreria.columns)
                    nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=st.session_state.viajes.columns)
                    
                    # 2. Concatenar localmente
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                    st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                    
                    # 3. GUARDAR ANTES DEL RERUN
                    guardar_datos("tesoreria", st.session_state.tesoreria)
                    guardar_datos("viajes", st.session_state.viajes)
                    
                    st.session_state.html_recibo_ready = generar_html_recibo({"Fecha": date.today(), "Cliente/Proveedor": c_sel, "Concepto": "Cobro de Viaje", "Caja/Banco": cj, "Monto": mon, "Ref AFIP": afip})
                    st.session_state.cli_ready = c_sel
                    st.success("Cobro registrado correctamente.")
                    st.rerun() # Ahora el rerun ocurre después de asegurar el guardado

        if st.session_state.html_recibo_ready:
            st.download_button("🖨️ IMPRIMIR RECIBO", st.session_state.html_recibo_ready, file_name=f"Recibo_{st.session_state.cli_ready}.html", mime="text/html")

    with t3:
        cj_v = st.selectbox("Caja a Ver", opc_cajas)
        df_ver = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj_v]
        st.metric(f"Saldo {cj_v}", f"$ {df_ver['Monto'].sum():,.2f}")
        st.dataframe(df_ver, use_container_width=True)

    with t4:
        with st.form("f_op"):
            p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
            mon_p = st.number_input("Monto $ ", min_value=0.0)
            if st.form_submit_button("GENERAR"):
                nt = pd.DataFrame([[date.today(), "PAGO PROV", "CAJA", "OP", p_sel, -mon_p, "-"]], columns=st.session_state.tesoreria.columns)
                nc = pd.DataFrame([[date.today(), p_sel, "-", "OP", 0, 0, 0, 0, 0, 0, -mon_p]], columns=st.session_state.compras.columns)
                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                st.session_state.compras = pd.concat([st.session_state.compras, nc], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.tesoreria)
                guardar_datos("compras", st.session_state.compras)
                st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente")
    cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
    df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("SALDO", f"$ {df_ind['Importe'].sum():,.2f}")
    st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Deudores")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res)

elif sel == "COMPROBANTES":
    st.header("📜 Historial")
    st.dataframe(st.session_state.viajes)

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Proveedores")
    with st.form("f_prov"):
        rs = st.text_input("Razón Social")
        doc = st.text_input("CUIT")
        if st.form_submit_button("REGISTRAR"):
            np = pd.DataFrame([[rs, doc, "VARIOS", "R.I."]], columns=st.session_state.proveedores.columns)
            st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
            guardar_datos("proveedores", st.session_state.proveedores)
            st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("💸 Gastos")
    with st.form("f_gasto"):
        prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        tipo_f = st.selectbox("Tipo", ["A", "B", "C", "NOTA DE CREDITO", "NOTA DE DEBITO"])
        total = st.number_input("Total $", min_value=0.0)
        if st.form_submit_button("GUARDAR"):
            t_final = -total if tipo_f == "NOTA DE CREDITO" else total
            ng = pd.DataFrame([[date.today(), prov_sel, "001", tipo_f, 0, 0, 0, 0, 0, 0, t_final]], columns=st.session_state.compras.columns)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras)
            st.rerun()

elif sel == "CTA CTE PROVEEDOR":
    p_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    df_p = st.session_state.compras[st.session_state.compras['Proveedor'] == p_sel]
    st.metric("PENDIENTE", f"$ {df_p['Total'].sum():,.2f}")
    st.dataframe(df_p)

elif sel == "CTA CTE GENERAL PROV":
    res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
    st.table(res_p)

elif sel == "HISTORICO COMPRAS":
    st.dataframe(st.session_state.compras)
