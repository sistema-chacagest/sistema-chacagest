import streamlit as st
import pandas as pd
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

def conectar_google():
    # El nombre debe coincidir EXACTAMENTE con tu archivo en Drive
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
        if sh is None: return None, None # Retorno nulo para evitar sobrescribir con vacío
        
        # Carga de Clientes
        ws_c = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=col_c)
        
        # Carga de Viajes
        ws_v = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=col_v)
        
        # Limpieza de datos numéricos para evitar errores en cálculos
        if not df_v.empty:
            df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)
            
        return df_c, df_v
    except Exception as e:
        st.error(f"Error crítico al leer las pestañas: {e}")
        return None, None

def guardar_datos(nombre_hoja, df):
    try:
        sh = conectar_google()
        if sh is None: return False
        ws = sh.worksheet(nombre_hoja)
        ws.clear()
        
        # Convertimos todo a texto para asegurar compatibilidad con Google Sheets
        df_save = df.copy()
        for col in df_save.columns:
            df_save[col] = df_save[col].astype(str)
            
        datos = [df_save.columns.values.tolist()] + df_save.values.tolist()
        ws.update(datos) 
        return True
    except Exception as e:
        st.error(f"Error al intentar guardar en la nube: {e}")
        return False

# --- 2. LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "chaca2026":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- 3. INICIALIZACIÓN DE DATOS (EVITA EL BORRADO ACCIDENTAL) ---
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v = cargar_datos()
    # Si la carga falló, creamos estructuras vacías pero no sobreescribimos si ya existen
    st.session_state.clientes = c if c is not None else pd.DataFrame(columns=["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"])
    st.session_state.viajes = v if v is not None else pd.DataFrame(columns=["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"])

# --- 4. DISEÑO ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }
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
    st.markdown("### PANEL DE CONTROL")
    sel = option_menu(
        menu_title=None,
        options=["CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["people", "truck", "file-earmark-minus", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )
    st.markdown("---")
    
    # REPARACIÓN DEL BOTÓN SINCRONIZAR
    if st.button("🔄 Sincronizar"):
        with st.spinner("Actualizando datos..."):
            c, v = cargar_datos()
            if c is not None and v is not None:
                st.session_state.clientes = c
                st.session_state.viajes = v
                st.success("Sincronización exitosa")
                st.rerun()
            else:
                st.error("No se pudo conectar. Se mantienen los datos actuales.")

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r = c1.text_input("Razón Social / Nombre Completo *")
            cuit = c2.text_input("CUIT / CUIL / DNI *")
            mail = c1.text_input("Email")
            tel = c2.text_input("Teléfono")
            dir_f = c1.text_input("Dirección Fiscal")
            loc = c2.text_input("Localidad")
            prov = c1.text_input("Provincia")
            c_iva = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], 
                                               columns=st.session_state.clientes.columns)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    if guardar_datos("clientes", st.session_state.clientes):
                        st.success("✅ Cliente guardado en la nube")
                        st.rerun()
                else:
                    st.warning("Complete los campos obligatorios (*)")

    st.subheader("📋 Base de Clientes")
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    if st.session_state.clientes.empty:
        st.warning("⚠️ Debe cargar clientes antes de registrar viajes.")
    else:
        with st.form("f_v"):
            cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
            c1, c2 = st.columns(2)
            f_v = c1.date_input("Fecha del Viaje")
            pat = c2.text_input("Patente / Móvil")
            orig = st.text_input("Origen")
            dest = st.text_input("Destino")
            imp = st.number_input("Importe Neto $", min_value=0.0)
            cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
            
            if st.form_submit_button("GUARDAR VIAJE"):
                nv = pd.DataFrame([[date.today().isoformat(), cli, f_v.isoformat(), orig, dest, pat, imp, f"Factura ({cond})", "-"]], 
                                  columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                if guardar_datos("viajes", st.session_state.viajes):
                    st.success("Viaje registrado correctamente")
                    st.rerun()

elif sel == "AJUSTES (NC/ND)":
    st.header("💳 Notas de Crédito / Débito (AFIP)")
    tipo = st.radio("Seleccione el ajuste:", ["Nota de Crédito", "Nota de Débito"], horizontal=True)
    
    with st.form("f_nc"):
        cl = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique())
        nro_asoc = st.text_input("Nro Comprobante AFIP Asociado *")
        mot = st.text_input("Motivo / Concepto")
        monto = st.number_input("Monto $", min_value=0.0)
        
        if st.form_submit_button("REGISTRAR AJUSTE"):
            if nro_asoc and monto > 0:
                # NC resta saldo, ND suma saldo
                val = -monto if "Crédito" in tipo else monto
                t_txt = "NC" if "Crédito" in tipo else "ND"
                
                nc = pd.DataFrame([[date.today().isoformat(), cl, date.today().isoformat(), "AJUSTE", mot, "-", val, t_txt, nro_asoc]], 
                                  columns=st.session_state.viajes.columns)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nc], ignore_index=True)
                if guardar_datos("viajes", st.session_state.viajes):
                    st.success(f"Se registró la {t_txt} asociada al comp. {nro_asoc}")
                    st.rerun()
            else:
                st.error("Debe indicar el Nro de Comprobante AFIP y el Monto.")

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    if not st.session_state.clientes.empty:
        cl = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl]
        saldo = df_ind['Importe'].sum()
        st.metric("SALDO ACTUAL", f"$ {saldo:,.2f}")
        st.dataframe(df_ind, use_container_width=True)
    else:
        st.info("No hay clientes registrados.")

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))
    else:
        st.info("Sin registros de deudas.")

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Cargas")
    if not st.session_state.viajes.empty:
        df_rev = st.session_state.viajes.copy().iloc[::-1]
        for i, row in df_rev.iterrows():
            c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
            c1.write(f"📅 {row['Fecha Viaje']}")
            c2.write(f"👤 **{row['Cliente']}** | {row['Tipo Comp']} | **${row['Importe']}**")
            if c3.button("🗑️", key=f"del_{i}"):
                st.session_state.viajes = st.session_state.viajes.drop(i)
                guardar_datos("viajes", st.session_state.viajes)
                st.rerun()
            st.divider()
