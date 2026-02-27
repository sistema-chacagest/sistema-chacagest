import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu

# --- CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="Chacagest", layout="wide")

# Definición de Cuentas solicitadas
CUENTAS_TESORERIA = [
    "Caja Tato", 
    "Caja Coti", 
    "Banco Galicia", 
    "Banco Provincia", 
    "Banco Supervielle"
]

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
    # Estructura de columnas según tu código
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_t = ["Fecha", "Tipo", "Origen", "Destino", "Detalle", "Monto", "Cliente/Proveedor"]
    
    sh = conectar_google()
    if sh:
        # Clientes
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        # Viajes (Cta Cte / AFIP)
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
        # Tesorería
        try:
            ws_t = sh.worksheet("tesoreria")
            df_t = pd.DataFrame(ws_t.get_all_records()) if ws_t.get_all_records() else pd.DataFrame(columns=col_t)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
        except:
            df_t = pd.DataFrame(columns=col_t)
            
        return df_c, df_v, df_t
    return None, None, None

def guardar_datos(nombre_hoja, df):
    sh = conectar_google()
    if sh:
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        datos = [df.columns.values.tolist()] + df.fillna("-").astype(str).values.tolist()
        ws.update(datos)
        return True
    return False

# --- INICIALIZACIÓN ---
if 'clientes' not in st.session_state:
    c, v, t = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.tesoreria = t

# --- SIDEBAR ---
with st.sidebar:
    sel = option_menu("Menú", ["CLIENTES", "CARGA VIAJE", "TESORERÍA", "CTA CTE INDIVIDUAL"], 
        icons=['people', 'truck', 'cash-stack', 'file-person'], menu_icon="cast", default_index=1)

# --- MÓDULO CLIENTES ---
if sel == "CLIENTES":
    st.header("Gestión de Clientes")
    st.dataframe(st.session_state.clientes)

# --- MÓDULO CARGA VIAJE (Facturación / Notas de Crédito / Débito) ---
elif sel == "CARGA VIAJE":
    st.header("Carga de Comprobantes")
    with st.form("f_viaje", clear_on_submit=True):
        f_viaje = st.date_input("Fecha Viaje")
        cli = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        tipo_c = st.selectbox("Tipo Comprobante", ["Factura", "Nota de Débito", "Nota de Crédito"])
        imp = st.number_input("Importe $", min_value=0.0)
        asoc = st.text_input("Nro Comprobante / Asoc AFIP")
        
        if st.form_submit_button("Guardar Comprobante"):
            # Lógica de impacto en Cta Cte: Nota de Crédito resta saldo
            valor_final = -imp if tipo_c == "Nota de Crédito" else imp
            
            nuevo_v = pd.DataFrame([[date.today(), cli, f_viaje, "-", "-", "-", valor_final, tipo_c, asoc]], 
                                   columns=st.session_state.viajes.columns)
            st.session_state.viajes = pd.concat([st.session_state.viajes, nuevo_v], ignore_index=True)
            guardar_datos("viajes", st.session_state.viajes)
            st.success(f"{tipo_c} registrada correctamente")

# --- MÓDULO TESORERÍA (NUEVO) ---
elif sel == "TESORERÍA":
    st.header("💰 Módulo de Tesorería")
    
    # 1. Mostrar Saldos de Cajas y Bancos
    st.subheader("Saldos en Cajas y Bancos")
    cols = st.columns(len(CUENTAS_TESORERIA))
    for i, cuenta in enumerate(CUENTAS_TESORERIA):
        ingresos = st.session_state.tesoreria[st.session_state.tesoreria['Destino'] == cuenta]['Monto'].sum()
        egresos = st.session_state.tesoreria[st.session_state.tesoreria['Origen'] == cuenta]['Monto'].sum()
        saldo = ingresos - egresos
        cols[i].metric(cuenta, f"$ {saldo:,.2f}")

    st.divider()

    # 2. Formulario de Movimientos
    st.subheader("Registrar Movimiento")
    with st.form("f_teso", clear_on_submit=True):
        tipo_m = st.selectbox("Operación", ["Cobranza de Viaje", "Ingreso Vario", "Egreso Vario", "Pase entre Cajas"])
        monto_m = st.number_input("Monto $", min_value=0.0)
        detalle_m = st.text_input("Detalle / Observaciones")
        
        c1, c2 = st.columns(2)
        if tipo_m == "Cobranza de Viaje":
            cliente_m = c1.selectbox("Cliente que Paga", st.session_state.clientes['Razón Social'].unique())
            destino_m = c2.selectbox("Ingresa a", CUENTAS_TESORERIA)
            origen_m = "CLIENTE"
        elif tipo_m == "Ingreso Vario":
            origen_m = "VARIOS"
            destino_m = st.selectbox("Caja Destino", CUENTAS_TESORERIA)
            cliente_m = "-"
        elif tipo_m == "Egreso Vario":
            origen_m = st.selectbox("Caja/Banco Origen", CUENTAS_TESORERIA)
            destino_m = "GASTO / VARIOS"
            cliente_m = "-"
        elif tipo_m == "Pase entre Cajas":
            origen_m = st.selectbox("Desde (Origen)", CUENTAS_TESORERIA)
            destino_m = st.selectbox("Hacia (Destino)", CUENTAS_TESORERIA)
            cliente_m = "-"

        if st.form_submit_button("Ejecutar Movimiento"):
            # A. Registrar en hoja de Tesorería
            nuevo_mov = pd.DataFrame([[date.today(), tipo_m, origen_m, destino_m, detalle_m, monto_m, cliente_m]], 
                                     columns=st.session_state.tesoreria.columns)
            st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nuevo_mov], ignore_index=True)
            guardar_datos("tesoreria", st.session_state.tesoreria)

            # B. Si es COBRANZA, impactar en la Cta Cte del Cliente (restar deuda)
            if tipo_m == "Cobranza de Viaje":
                nuevo_pago = pd.DataFrame([[date.today(), cliente_m, date.today(), "COBRANZA", "-", "-", -monto_m, "RECIBO CAJA", detalle_m]], 
                                          columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nuevo_pago], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)

            st.success("Movimiento registrado y saldos actualizados")
            st.rerun()

    st.subheader("Historial de Tesorería")
    st.dataframe(st.session_state.tesoreria.sort_index(ascending=False))

# --- CTA CTE INDIVIDUAL ---
elif sel == "CTA CTE INDIVIDUAL":
    st.header("Cuenta Corriente por Cliente")
    cli_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
    df_cli = st.session_state.viajes[st.session_state.viajes['Cliente'] == cli_sel]
    st.metric("Saldo Pendiente", f"$ {df_cli['Importe'].sum():,.2f}")
    st.dataframe(df_cli)
