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
    col_prov = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA", "Alias", "CBU"]
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
            # PROTECCIÓN: Si las columnas nuevas no existen en el Excel, las agregamos al DataFrame
            for col in ["Alias", "CBU"]:
                if col not in df_prov.columns:
                    df_prov[col] = "-"
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

# --- REPORTEADORES HTML ---

def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""<html><head><style>body {{ font-family: sans-serif; padding: 20px; }} .tabla {{ width: 100%; border-collapse: collapse; }} .tabla th {{ background: #5e2d61; color: white; padding: 10px; }} .tabla td {{ border: 1px solid #ddd; padding: 8px; }}</style></head><body><h2>Estado de Cuenta: {cliente}</h2>{tabla_html}<h3>Saldo Pendiente: $ {saldo:,.2f}</h3></body></html>"""

def generar_html_recibo(data):
    return f"""<html><body style='font-family:sans-serif; border:2px solid #5e2d61; padding:20px;'><h1>RECIBO DE PAGO</h1><p><b>Cliente:</b> {data['Cliente/Proveedor']}</p><p><b>Monto:</b> $ {abs(data['Monto']):,.2f}</p><p><b>Concepto:</b> {data['Concepto']}</p><p><b>Ref AFIP:</b> {data['Ref AFIP']}</p></body></html>"""

def generar_html_orden_pago(data):
    return f"""<html><body style='font-family:sans-serif; border:2px solid #d35400; padding:20px;'><h1>ORDEN DE PAGO</h1><p><b>Proveedor:</b> {data['Proveedor']}</p><p><b>Monto:</b> $ {abs(data['Monto']):,.2f}</p><p><b>Concepto:</b> {data['Concepto']}</p></body></html>"""

def generar_html_presupuesto(p_data):
    return f"""<html><body style='font-family:sans-serif; padding:30px;'><h1>PRESUPUESTO</h1><p><b>Cliente:</b> {p_data['Cliente']}</p><p><b>Móvil:</b> {p_data['Tipo Móvil']}</p><p><b>Detalle:</b> {p_data['Detalle']}</p><h2>TOTAL: $ {p_data['Importe']:,.2f}</h2></body></html>"""

# --- LOGIN ---
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

# --- INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t
    st.session_state.proveedores = prov
    st.session_state.compras = com

# --- SIDEBAR ---
with st.sidebar:
    st.header("MENU")
    menu_principal = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], icons=["calendar", "cart", "bag", "safe"], default_index=0)
    sel_sub = None
    if menu_principal == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"], icons=["people", "truck", "file", "person", "globe", "list"])
    elif menu_principal == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"], icons=["person-plus", "receipt", "person-vcard", "globe", "clock"])
    
    if st.button("🔄 Sincronizar"):
        c, v, p, t, prov, com = cargar_datos()
        st.session_state.clientes, st.session_state.viajes, st.session_state.presupuestos, st.session_state.tesoreria, st.session_state.proveedores, st.session_state.compras = c, v, p, t, prov, com
        st.rerun()
    if st.button("🚪 Salir"):
        st.session_state.autenticado = False; st.rerun()

sel = sel_sub if menu_principal in ["VENTAS", "COMPRAS"] else menu_principal

# --- MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda")
    eventos = []
    for i, row in st.session_state.viajes.iterrows():
        if row['Importe'] > 0 and str(row['Fecha Viaje']) != "-":
            eventos.append({"title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje'])})
    calendar(events=eventos, options={"locale": "es"})

elif sel == "CLIENTES":
    st.header("👤 Clientes")
    with st.expander("➕ Nuevo Cliente"):
        with st.form("f_cli"):
            r = st.text_input("Razón Social")
            cuit = st.text_input("CUIT")
            if st.form_submit_button("Guardar"):
                if r and cuit:
                    nc = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "Consumidor Final", "Cuenta Corriente"]], columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nc], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes); st.rerun()
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Cargar Viaje")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        f = st.date_input("Fecha")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe", min_value=0.0)
        if st.form_submit_button("Registrar"):
            nv = pd.DataFrame([[date.today(), cli, f, orig, dest, "-", imp, "Factura", "-"]], columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes); st.rerun()

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Proveedores")
    with st.expander("➕ Nuevo Proveedor"):
        with st.form("f_prov"):
            rs = st.text_input("Razón Social")
            doc = st.text_input("CUIT")
            cat = st.selectbox("IVA", ["Monotributo", "Responsable Inscripto"])
            # NUEVOS CAMPOS
            ali = st.text_input("Alias")
            cbu = st.text_input("CBU")
            if st.form_submit_button("Registrar"):
                np = pd.DataFrame([[rs, doc, "VARIOS", cat, ali, cbu]], columns=st.session_state.proveedores.columns)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores); st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("💸 Cargar Gastos")
    prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique())
    tipo = st.selectbox("Tipo", ["A", "B", "C", "NOTA DE CREDITO", "NOTA DE DEBITO"])
    total = st.number_input("Total $", min_value=0.0)
    if st.button("Guardar Gasto"):
        val = -total if tipo == "NOTA DE CREDITO" else total
        ng = pd.DataFrame([[date.today(), prov, "0001", tipo, 0, 0, 0, 0, 0, 0, val]], columns=st.session_state.compras.columns)
        st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
        guardar_datos("compras", st.session_state.compras); st.rerun()

elif sel == "CTA CTE GENERAL PROV":
    st.header("🌎 Estado General de Proveedores")
    if not st.session_state.compras.empty:
        # 1. Agrupar totales
        res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
        
        # 2. Intentar unir con info bancaria (con protección por si las columnas no cargaron bien)
        prov_info = st.session_state.proveedores.copy()
        for col in ['Alias', 'CBU']:
            if col not in prov_info.columns: prov_info[col] = "-"
            
        res_p = res_p.merge(prov_info[['Razón Social', 'Alias', 'CBU']], left_on='Proveedor', right_on='Razón Social', how='left')
        
        if 'Razón Social' in res_p.columns: res_p = res_p.drop(columns=['Razón Social'])
        
        st.table(res_p.style.format({"Total": "$ {:,.2f}"}))
    else:
        st.info("Sin movimientos.")

elif sel == "TESORERIA":
    st.header("💰 Tesorería")
    # Versión simplificada para el ejemplo, pero funcional con tus datos
    caja = st.selectbox("Caja", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA"])
    saldo = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == caja]['Monto'].sum()
    st.metric(f"Saldo {caja}", f"$ {saldo:,.2f}")
    st.dataframe(st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == caja])

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Cliente")
    cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
    st.metric("Deuda", f"$ {df['Importe'].sum():,.2f}")
    st.dataframe(df)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Deudores Global")
    res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
    st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Comprobantes")
    st.dataframe(st.session_state.compras)

elif sel == "COMPROBANTES":
    st.header("📜 Viajes Registrados")
    st.dataframe(st.session_state.viajes)

elif sel == "PRESUPUESTOS":
    st.header("📝 Presupuestos")
    st.dataframe(st.session_state.presupuestos)
