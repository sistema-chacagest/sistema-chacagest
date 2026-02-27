import streamlit as st
import pandas as pd
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

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
    # Definición de columnas por hoja
    cols = {
        "clientes": ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"],
        "viajes": ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"],
        "presupuestos": ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"],
        "tesoreria": ["Fecha", "Tipo", "Concepto", "Monto", "Cuenta", "AFIP_Asoc"] # Nueva Hoja
    }
    
    try:
        sh = conectar_google()
        if sh is None: return None
        
        dfs = {}
        for hoja, columnas in cols.items():
            try:
                ws = sh.worksheet(hoja)
                datos = ws.get_all_records()
                df = pd.DataFrame(datos) if datos else pd.DataFrame(columns=columnas)
                # Limpieza de numéricos
                if 'Importe' in df.columns: df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce').fillna(0)
                if 'Monto' in df.columns: df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
                dfs[hoja] = df
            except:
                dfs[hoja] = pd.DataFrame(columns=columnas)
        return dfs
    except:
        return None

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

# --- 2. LOGIN (Simplificado para el ejemplo) ---
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
    st.stop()

# --- 3. INICIALIZACIÓN DE DATOS ---
if 'datos' not in st.session_state:
    st.session_state.datos = cargar_datos()

# --- 4. SIDEBAR Y MENÚ ---
with st.sidebar:
    st.markdown("### Menú Principal")
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "TESORERÍA", "CTA CTE", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "cash-stack", "person-vcard", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    if st.button("🔄 Sincronizar"):
        st.session_state.datos = cargar_datos()
        st.rerun()

# --- 5. MÓDULO DE TESORERÍA (NUEVO) ---
if sel == "TESORERÍA":
    st.header("💰 Módulo de Tesorería")
    
    df_teso = st.session_state.datos['tesoreria']
    cuentas = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE"]
    
    # --- RESUMEN DE SALDOS ---
    cols_saldos = st.columns(len(cuentas))
    for i, cta in enumerate(cuentas):
        ingresos = df_teso[(df_teso['Cuenta'] == cta) & (df_teso['Tipo'] == 'INGRESO')]['Monto'].sum()
        egresos = df_teso[(df_teso['Cuenta'] == cta) & (df_teso['Tipo'] == 'EGRESO')]['Monto'].sum()
        saldo = ingresos - egresos
        cols_saldos[i].metric(cta, f"$ {saldo:,.0f}")

    st.divider()

    tab1, tab2 = st.tabs(["➕ Nuevo Movimiento", "📜 Historial de Caja"])

    with tab1:
        with st.form("f_teso", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            tipo_mov = col_a.selectbox("Tipo de Movimiento", ["INGRESO", "EGRESO"])
            cuenta_sel = col_b.selectbox("Cuenta / Caja", cuentas)
            
            concepto = st.selectbox("Concepto", ["COBRANZA DE VIAJE", "INGRESOS VARIOS", "EGRESOS VARIOS", "NOTA DE CRÉDITO", "NOTA DE DÉBITO"])
            monto = st.number_input("Importe $", min_value=0.0, step=100.0)
            
            # Nota de AFIP (obligatorio si es NC/ND según tus instrucciones)
            afip_ref = st.text_input("Comprobante AFIP Asociado (Opcional)", placeholder="Ej: NC-0001-00001234")
            
            if st.form_submit_button("REGISTRAR EN TESORERÍA"):
                nuevo_mov = pd.DataFrame([[date.today().strftime("%Y-%m-%d"), tipo_mov, concepto, monto, cuenta_sel, afip_ref]], 
                                        columns=df_teso.columns)
                st.session_state.datos['tesoreria'] = pd.concat([df_teso, nuevo_mov], ignore_index=True)
                guardar_datos("tesoreria", st.session_state.datos['tesoreria'])
                st.success(f"Movimiento registrado en {cuenta_sel}")
                st.rerun()

    with tab2:
        st.subheader("Últimos Movimientos")
        if not df_teso.empty:
            st.dataframe(df_teso.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("No hay movimientos registrados.")

# --- 6. (OTROS MÓDULOS SE MANTIENEN IGUAL PERO ACCEDIENDO A st.session_state.datos) ---
elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    # ... (Tu código de clientes usando st.session_state.datos['clientes'])
    st.dataframe(st.session_state.datos['clientes'])

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    # ... (Tu código de viajes)
