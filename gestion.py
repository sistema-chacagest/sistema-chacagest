import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64

# --- 1. CONFIGURACIÓN Y ESTRUCTURA DE DATOS (CONSTANTES) ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

# Definimos las columnas exactas para evitar errores de desajuste (ValueError)
COL_CLIENTES = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
COL_VIAJES = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
COL_PRESUPUESTOS = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
COL_TESORERIA = ["Fecha", "Tipo", "Caja/Banco", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
COL_PROVEEDORES = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA"]
COL_COMPRAS = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]

# --- 2. FUNCIONES DE CONEXIÓN Y PERSISTENCIA ---

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
        st.error(f"Error de conexión con Google: {e}")
        return None

def cargar_datos():
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None, None
        
        def leer_hoja(nombre, columnas_modelo):
            try:
                ws = sh.worksheet(nombre)
                datos = ws.get_all_records()
                df = pd.DataFrame(datos)
                if df.empty:
                    return pd.DataFrame(columns=columnas_modelo)
                # Forzamos a que el DF tenga solo las columnas del modelo para evitar errores
                for col in columnas_modelo:
                    if col not in df.columns: df[col] = "-"
                return df[columnas_modelo]
            except:
                return pd.DataFrame(columns=columnas_modelo)

        df_c = leer_hoja("clientes", COL_CLIENTES)
        df_v = leer_hoja("viajes", COL_VIAJES)
        df_p = leer_hoja("presupuestos", COL_PRESUPUESTOS)
        df_t = leer_hoja("tesoreria", COL_TESORERIA)
        df_prov = leer_hoja("proveedores", COL_PROVEEDORES)
        df_com = leer_hoja("compras", COL_COMPRAS)

        # Formateo de tipos de datos numéricos
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        df_com['Total'] = pd.to_numeric(df_com['Total'], errors='coerce').fillna(0)
        df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
            
        return df_c, df_v, df_p, df_t, df_prov, df_com
    except Exception as e:
        st.error(f"Error al procesar datos: {e}")
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
        st.error(f"Error al guardar en {nombre_hoja}: {e}")
        return False

# --- 3. SISTEMA DE LOGIN ---
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
            else: st.error("Acceso incorrecto")
    st.stop()

# --- 4. CARGA INICIAL DE SESIÓN ---
if 'clientes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p
    st.session_state.tesoreria = t
    st.session_state.proveedores = prov
    st.session_state.compras = com

# --- 5. NAVEGACIÓN (SIDEBAR) ---
with st.sidebar:
    st.header("NAVEGACIÓN")
    menu_p = option_menu(None, ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"], 
        icons=["calendar3", "cart4", "bag-check", "safe"], default_index=0)
    
    sel_sub = None
    if menu_p == "VENTAS":
        sel_sub = option_menu(None, ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "COMPROBANTES"], 
                              icons=["people", "truck", "file-text", "person", "receipt"])
    elif menu_p == "COMPRAS":
        sel_sub = option_menu(None, ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "HISTORICO COMPRAS"], 
                              icons=["person-plus", "receipt", "person", "clock"])
    
    if st.button("🔄 Sincronizar Todo"):
        st.session_state.clear()
        st.rerun()

sel = sel_sub if sel_sub else menu_p

# --- 6. LÓGICA DE MÓDULOS ---

if sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = [{"title": str(r['Cliente']), "start": str(r['Fecha Viaje']), "allDay": True} 
               for _, r in st.session_state.viajes.iterrows() if str(r['Fecha Viaje']) != "-" and r['Importe'] > 0]
    calendar(events=eventos)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.form("f_cli", clear_on_submit=True):
        r = st.text_input("Razón Social")
        cuit = st.text_input("CUIT/CUIL")
        if st.form_submit_button("REGISTRAR"):
            if r and cuit:
                # Creación segura usando la constante global
                nc = pd.DataFrame([[r, cuit, "-", "-", "-", "-", "-", "Monotributo", "Cuenta Corriente"]], columns=COL_CLIENTES)
                st.session_state.clientes = pd.concat([st.session_state.clientes, nc], ignore_index=True)
                guardar_datos("clientes", st.session_state.clientes)
                st.success("Cliente guardado correctamente"); st.rerun()
    st.dataframe(st.session_state.clientes)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Comprobante Venta (AFIP)")
    with st.form("f_v"):
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        tipo_c = st.selectbox("Tipo de Comprobante", ["Factura", "Nota de Crédito", "Nota de Débito"])
        f_v = st.date_input("Fecha Viaje")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp = st.number_input("Importe Neto $", min_value=0.0)
        ref_afip = st.text_input("Nro. Comprobante AFIP (Asociado)")
        if st.form_submit_button("GUARDAR COMPROBANTE"):
            # Si es Nota de Crédito, el valor debe ser negativo para restar en Cta Cte
            valor = -abs(imp) if tipo_c == "Nota de Crédito" else abs(imp)
            # Creación segura con constante
            nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, "-", valor, tipo_c, ref_afip]], columns=COL_VIAJES)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success("Venta/Crédito registrado con éxito"); st.rerun()

elif sel == "CARGA PROVEEDOR":
    st.header("👤 Gestión de Proveedores")
    with st.form("f_prov", clear_on_submit=True):
        rs = st.text_input("Razón Social Proveedor")
        doc = st.text_input("CUIT Proveedor")
        cuenta = st.selectbox("Cuenta de Gastos", ["COMBUSTIBLE", "REPUESTO", "MANTENIMIENTO", "VARIOS"])
        if st.form_submit_button("REGISTRAR PROVEEDOR"):
            if rs and doc:
                # Creación segura con constante
                np = pd.DataFrame([[rs, doc, cuenta, "Responsable Inscripto"]], columns=COL_PROVEEDORES)
                st.session_state.proveedores = pd.concat([st.session_state.proveedores, np], ignore_index=True)
                guardar_datos("proveedores", st.session_state.proveedores)
                st.success("Proveedor añadido"); st.rerun()
    st.dataframe(st.session_state.proveedores)

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gastos / Compras")
    with st.form("f_g"):
        prov = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
        tipo_f = st.selectbox("Tipo de Documento", ["Factura A", "Factura B", "Factura C", "NOTA DE CREDITO", "NOTA DE DEBITO"])
        n_afip = st.text_input("Nro Comprobante AFIP")
        neto = st.number_input("Importe Neto", min_value=0.0)
        iva = st.number_input("IVA", min_value=0.0)
        if st.form_submit_button("REGISTRAR GASTO"):
            # Lógica de signos: NC resta, Facturas y ND suman
            total = (neto + iva)
            if tipo_f == "NOTA DE CREDITO": total = -abs(total)
            
            # Creación segura con constante
            ng = pd.DataFrame([[date.today(), prov, n_afip, tipo_f, neto, 0, 0, 0, 0, 0, total]], columns=COL_COMPRAS)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras)
            st.success("Gasto registrado"); st.rerun()

elif sel == "TESORERIA":
    st.header("💰 Caja y Movimientos de Tesorería")
    with st.form("f_t"):
        tipo_t = st.selectbox("Tipo de Movimiento", ["COBRANZA", "PAGO PROV", "INGRESO VARIO", "EGRESO VARIO"])
        # Lista combinada para seleccionar entidad
        lista_entidades = list(st.session_state.clientes['Razón Social']) + list(st.session_state.proveedores['Razón Social'])
        entidad = st.selectbox("Entidad / Beneficiario", lista_entidades if lista_entidades else ["Varios"])
        caja = st.selectbox("Caja/Banco", ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA"])
        monto = st.number_input("Monto total de la operación $", min_value=0.0)
        ref = st.text_input("Referencia AFIP / Recibo")
        
        if st.form_submit_button("EJECUTAR MOVIMIENTO"):
            # 1. Registro en Tesorería
            monto_real = -monto if "EGRESO" in tipo_t or "PAGO" in tipo_t else monto
            nt = pd.DataFrame([[date.today(), tipo_t, caja, "Movimiento de Caja", entidad, monto_real, ref]], columns=COL_TESORERIA)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
            
            # 2. Impacto en Cuentas Corrientes según el caso
            if tipo_t == "COBRANZA":
                # Resta deuda al cliente (Importe negativo)
                nv = pd.DataFrame([[date.today(), entidad, date.today(), "PAGO RECIBIDO", "TESORERIA", "-", -abs(monto), "RECIBO", ref]], columns=COL_VIAJES)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
            
            elif tipo_t == "PAGO PROV":
                # Resta deuda al proveedor (Importe negativo)
                nc = pd.DataFrame([[date.today(), entidad, "-", "PAGO REALIZADO", 0, 0, 0, 0, 0, 0, -abs(monto)]], columns=COL_COMPRAS)
                st.session_state.compras = pd.concat([st.session_state.compras, nc], ignore_index=True)
                guardar_datos("compras", st.session_state.compras)

            guardar_datos("tesoreria", st.session_state.tesoreria)
            st.success("Operación financiera registrada"); st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente de Clientes")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_res = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
        st.metric("SALDO PENDIENTE", f"$ {df_res['Importe'].sum():,.2f}")
        st.dataframe(df_res, use_container_width=True)

elif sel == "CTA CTE PROVEEDOR":
    st.header("📊 Cuenta Corriente de Proveedores")
    if not st.session_state.proveedores.empty:
        pr = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
        df_p = st.session_state.compras[st.session_state.compras['Proveedor'] == pr]
        st.metric("DEUDA CON PROVEEDOR", f"$ {df_p['Total'].sum():,.2f}")
        st.dataframe(df_p, use_container_width=True)

elif sel == "COMPROBANTES":
    st.header("📜 Histórico de Ventas")
    st.dataframe(st.session_state.viajes)

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Histórico de Compras/Gastos")
    st.dataframe(st.session_state.compras)
