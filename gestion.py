import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# ---------------- CONFIG ----------------

st.set_page_config(page_title="CHACAGEST", page_icon="🚛", layout="wide")

# Estilo personalizado para mantener tu estética
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    h1, h2, h3 { color: #5e2d61; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- GOOGLE ----------------

def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file("llave_google.json", scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Base_Chacagest")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# ---------------- LOAD / SAVE ----------------

def cargar_datos():
    sh = conectar_google()
    if not sh: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def obtener_df(nombre):
        try:
            return pd.DataFrame(sh.worksheet(nombre).get_all_records())
        except:
            return pd.DataFrame()

    clientes = obtener_df("clientes")
    viajes = obtener_df("viajes")
    proveedores = obtener_df("proveedores")
    compras = obtener_df("compras")

    # Conversión segura de números
    if not viajes.empty and "Importe" in viajes.columns:
        viajes["Importe"] = pd.to_numeric(viajes["Importe"], errors="coerce").fillna(0)
    
    if not compras.empty and "Total" in compras.columns:
        compras["Total"] = pd.to_numeric(compras["Total"], errors="coerce").fillna(0)

    return clientes, viajes, proveedores, compras

def guardar(nombre, df):
    sh = conectar_google()
    if not sh: return
    try:
        ws = sh.worksheet(nombre)
        ws.clear()
        df = df.fillna("-").astype(str)
        data = [df.columns.tolist()] + df.values.tolist()
        ws.update(data)
    except Exception as e:
        st.error(f"Error al guardar {nombre}: {e}")

# ---------------- LOGIN ----------------

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🚛 CHACAGEST")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u == "admin" and p == "chaca2026":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Acceso denegado")
    st.stop()

# ---------------- INIT ----------------

if "init" not in st.session_state:
    c, v, p, co = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.proveedores = p
    st.session_state.compras = co
    st.session_state.init = True

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("CHACAGEST")
    menu = option_menu(
        None,
        ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)", 
         "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "COMPRAS"],
        icons=["calendar3", "people", "truck", "file-earmark-minus", 
               "person", "globe", "file-text", "cart"],
        menu_icon="cast", default_index=0,
        styles={"nav-link-selected": {"background-color": "#5e2d61"}}
    )

    if st.button("🔄 Sincronizar"):
        st.session_state.clientes, st.session_state.viajes, st.session_state.proveedores, st.session_state.compras = cargar_datos()
        st.rerun()

    if st.button("Salir"):
        st.session_state.login = False
        st.rerun()

# ---------------- MODULOS ----------------

if menu == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    eventos = []
    for i, r in st.session_state.viajes.iterrows():
        if "Fecha Viaje" in r and str(r["Fecha Viaje"]) != "-":
            eventos.append({"id": i, "title": str(r["Cliente"]), "start": str(r["Fecha Viaje"]), "allDay": True})
    calendar(events=eventos)

elif menu == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    with st.expander("Añadir Cliente"):
        with st.form("cli"):
            r = st.text_input("Razón Social")
            c = st.text_input("CUIT")
            if st.form_submit_button("Guardar"):
                df = st.session_state.clientes
                # Asegurar que tenga las columnas correctas
                new_row = [r, c] + [""] * (len(df.columns) - 2)
                df.loc[len(df)] = new_row
                guardar("clientes", df)
                st.success("Cliente guardado")
                st.rerun()
    st.dataframe(st.session_state.clientes, use_container_width=True)

elif menu == "CARGA VIAJE":
    st.header("🚛 Registro de Viajes")
    with st.form("via"):
        cli = st.selectbox("Seleccionar Cliente", st.session_state.clientes["Razón Social"] if not st.session_state.clientes.empty else [""])
        f = st.date_input("Fecha Viaje")
        o = st.text_input("Origen")
        d = st.text_input("Destino")
        i = st.number_input("Importe Neto", min_value=0.0)
        if st.form_submit_button("Registrar Viaje"):
            df = st.session_state.viajes
            df.loc[len(df)] = [date.today(), cli, f, o, d, "-", i, "Factura", "-"]
            guardar("viajes", df)
            st.success("Viaje registrado con éxito")
            st.rerun()

elif menu == "COMPRAS":
    st.header("🛒 Módulo de Compras")
    sub = option_menu(None, ["Proveedores", "Carga Gastos", "NC / ND", "Cuenta Corriente", "Comprobantes"], 
        icons=["people", "plus-circle", "patch-minus", "wallet2", "receipt"], 
        menu_icon="cast", default_index=0, orientation="horizontal")

    # -------- PROVEEDORES --------
    if sub == "Proveedores":
        with st.form("prov"):
            r = st.text_input("Razón Social / Nombre")
            c = st.text_input("CUIT")
            g = st.selectbox("Cuenta Gasto Principal", ["Combustible", "Reparación", "Repuesto", "Otros"])
            iva = st.selectbox("Condición IVA", ["Resp. Inscripto", "Exento", "CF", "Mono", "No Inscripto"])
            if st.form_submit_button("Guardar Proveedor"):
                df = st.session_state.proveedores
                df.loc[len(df)] = [r, c, g, iva]
                guardar("proveedores", df)
                st.success("Proveedor registrado")
                st.rerun()
        st.dataframe(st.session_state.proveedores, use_container_width=True)

    # -------- GASTOS --------
    elif sub == "Carga Gastos":
        with st.form("gas"):
            p = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores["Razón Social"] if not st.session_state.proveedores.empty else [""])
            c1, c2 = st.columns(2)
            pv = c1.text_input("Punto Venta (4 dígitos)")
            tf = c2.selectbox("Tipo Factura", ["A", "B", "C", "Remito"])
            
            st.markdown("### Desglose de Importes")
            col1, col2 = st.columns(2)
            n21 = col1.number_input("Neto Gravado 21%", min_value=0.0)
            n10 = col2.number_input("Neto Gravado 10.5%", min_value=0.0)
            
            st.markdown("### Retenciones e Impuestos")
            col3, col4, col5 = st.columns(3)
            riva = col3.number_input("Retención IVA", min_value=0.0)
            rgan = col4.number_input("Retención Ganancias", min_value=0.0)
            riibb = col5.number_input("Retención IIBB", min_value=0.0)
            ng = st.number_input("Conceptos No Gravados", min_value=0.0)

            total = (n21 * 1.21) + (n10 * 1.105) + riva + rgan + riibb + ng
            st.metric("TOTAL A PAGAR", f"$ {total:,.2f}")

            if st.form_submit_button("Cargar Comprobante"):
                df = st.session_state.compras
                df.loc[len(df)] = [date.today(), p, pv, tf, n21, n10, riva, rgan, riibb, ng, total, "FACT", "-"]
                guardar("compras", df)
                st.success("Gasto cargado correctamente")
                st.rerun()

    # -------- NC / ND --------
    elif sub == "NC / ND":
        st.info("Asocie la Nota de Crédito/Débito a un comprobante existente.")
        with st.form("nc"):
            p = st.selectbox("Proveedor", st.session_state.proveedores["Razón Social"] if not st.session_state.proveedores.empty else [""])
            tipo = st.radio("Tipo de Ajuste", ["NC", "ND"], horizontal=True)
            n = st.number_input("Monto del Ajuste", min_value=0.0)
            asoc = st.text_input("Nro Comprobante AFIP Asociado")
            if st.form_submit_button("Guardar Ajuste"):
                val = -n if tipo == "NC" else n
                df = st.session_state.compras
                # Llenamos con 0 las columnas de impuestos para mantener estructura
                df.loc[len(df)] = [date.today(), p, "-", "-", 0, 0, 0, 0, 0, 0, val, tipo, asoc]
                guardar("compras", df)
                st.success("Ajuste registrado")
                st.rerun()

    # -------- CTA CTE PROV --------
    elif sub == "Cuenta Corriente":
        p = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores["Razón Social"] if not st.session_state.proveedores.empty else [""])
        df = st.session_state.compras
        if not df.empty:
            filtro = df[df["Proveedor"] == p]
            st.dataframe(filtro, use_container_width=True)
            saldo = filtro["Total"].sum()
            st.metric(f"Saldo Pendiente con {p}", f"$ {saldo:,.2f}")

    # -------- HISTORIAL COMPRAS --------
    elif sub == "Comprobantes":
        st.subheader("Historial de Compras (Eliminación)")
        df = st.session_state.compras
        for i in reversed(df.index):
            r = df.loc[i]
            c1, c2 = st.columns([0.85, 0.15])
            c1.write(f"**{r['Fecha']}** | {r['Proveedor']} | **Total: $ {r['Total']}** | Tipo: {r['Tipo Comp']}")
            if c2.button("🗑️", key=f"del_co_{i}"):
                df = df.drop(i)
                st.session_state.compras = df
                guardar("compras", df)
                st.rerun()

# --- NOTA: Módulos de CTA CTE Clientes y Ajustes Clientes se manejan similar a CARGA VIAJE ---
