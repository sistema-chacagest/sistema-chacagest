
# CHACAGEST - SISTEMA COMPLETO CON MODULO COMPRAS
# Archivo unificado

import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar

# ---------------- CONFIG ----------------

st.set_page_config(page_title="CHACAGEST", page_icon="🚛", layout="wide")

# ---------------- GOOGLE ----------------

def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scope)
        else:
            creds = Credentials.from_service_account_file(
                "llave_google.json", scopes=scope)

        client = gspread.authorize(creds)
        return client.open("Base_Chacagest")

    except Exception as e:
        st.error(e)
        return None


# ---------------- LOAD ----------------

def cargar_datos():
    sh = conectar_google()

    clientes = pd.DataFrame(sh.worksheet("clientes").get_all_records())
    viajes = pd.DataFrame(sh.worksheet("viajes").get_all_records())

    proveedores = pd.DataFrame(sh.worksheet("proveedores").get_all_records())
    compras = pd.DataFrame(sh.worksheet("compras").get_all_records())

    if not viajes.empty:
        viajes["Importe"] = pd.to_numeric(viajes["Importe"], errors="coerce").fillna(0)

    if not compras.empty:
        compras["Total"] = pd.to_numeric(compras["Total"], errors="coerce").fillna(0)

    return clientes, viajes, proveedores, compras


def guardar(nombre, df):

    sh = conectar_google()
    ws = sh.worksheet(nombre)

    ws.clear()

    df = df.fillna("-").astype(str)

    data = [df.columns.tolist()] + df.values.tolist()

    ws.update(data)


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

    menu = option_menu(
        None,
        ["CALENDARIO", "CLIENTES", "CARGA VIAJE", "AJUSTES (NC/ND)",
         "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES", "COMPRAS"],
        icons=["calendar3", "people", "truck", "file-earmark-minus",
               "person", "globe", "file-text", "cart"]
    )

    if st.button("🔄 Sincronizar"):

        c, v, p, co = cargar_datos()

        st.session_state.clientes = c
        st.session_state.viajes = v
        st.session_state.proveedores = p
        st.session_state.compras = co

        st.rerun()

    if st.button("Salir"):
        st.session_state.login = False
        st.rerun()


# ---------------- CALENDARIO ----------------

if menu == "CALENDARIO":

    st.header("Agenda")

    eventos = []

    for i, r in st.session_state.viajes.iterrows():

        if str(r["Fecha Viaje"]) != "-":

            eventos.append({
                "id": i,
                "title": r["Cliente"],
                "start": str(r["Fecha Viaje"]),
                "allDay": True
            })

    calendar(events=eventos)


# ---------------- CLIENTES ----------------

elif menu == "CLIENTES":

    st.header("Clientes")

    with st.form("cli"):

        r = st.text_input("Razón Social")
        c = st.text_input("CUIT")

        if st.form_submit_button("Guardar"):

            df = st.session_state.clientes

            df.loc[len(df)] = [r, c, "", "", "", "", "", "", ""]

            guardar("clientes", df)

            st.success("Guardado")
            st.rerun()

    st.dataframe(st.session_state.clientes)


# ---------------- VIAJES ----------------

elif menu == "CARGA VIAJE":

    st.header("Viajes")

    with st.form("via"):

        cli = st.selectbox("Cliente", st.session_state.clientes["Razón Social"])

        f = st.date_input("Fecha")
        o = st.text_input("Origen")
        d = st.text_input("Destino")
        i = st.number_input("Importe")

        if st.form_submit_button("Guardar"):

            df = st.session_state.viajes

            df.loc[len(df)] = [
                date.today(), cli, f, o, d, "-", i, "Factura", "-"
            ]

            guardar("viajes", df)

            st.success("Guardado")
            st.rerun()


# ---------------- COMPRAS ----------------

elif menu == "COMPRAS":

    st.header("🛒 Compras")

    sub = st.selectbox("Módulo", [
        "Proveedores",
        "Carga Gastos",
        "NC / ND",
        "Cuenta Corriente",
        "General",
        "Comprobantes"
    ])


    # -------- PROVEEDORES --------

    if sub == "Proveedores":

        with st.form("prov"):

            r = st.text_input("Razón Social")
            c = st.text_input("CUIT")

            g = st.selectbox("Cuenta Gasto",
                             ["Combustible", "Reparación", "Repuesto", "Otros"])

            iva = st.selectbox("IVA",
                               ["Resp. Inscripto", "Exento",
                                "CF", "Mono", "No Inscripto"])

            if st.form_submit_button("Guardar"):

                df = st.session_state.proveedores

                df.loc[len(df)] = [r, c, g, iva]

                guardar("proveedores", df)

                st.success("Guardado")
                st.rerun()

        st.dataframe(st.session_state.proveedores)


    # -------- GASTOS --------

    if sub == "Carga Gastos":

        with st.form("gas"):

            p = st.selectbox("Proveedor",
                             st.session_state.proveedores["Razon Social"])

            pv = st.text_input("Punto Venta")

            tf = st.selectbox("Factura", ["A", "B", "C", "Remito"])

            n21 = st.number_input("Neto 21", 0.0)
            n10 = st.number_input("Neto 10", 0.0)

            riva = st.number_input("Ret IVA", 0.0)
            rgan = st.number_input("Ret Gan", 0.0)
            riibb = st.number_input("Ret IIBB", 0.0)

            ng = st.number_input("No Gravado", 0.0)

            total = n21*1.21 + n10*1.105 - riva - rgan - riibb + ng

            st.metric("TOTAL", f"$ {total:,.2f}")

            if st.form_submit_button("Guardar"):

                df = st.session_state.compras

                df.loc[len(df)] = [
                    date.today(), p, pv, tf,
                    n21, n10, riva, rgan, riibb,
                    ng, total, "FACT", "-"
                ]

                guardar("compras", df)

                st.success("Guardado")
                st.rerun()


    # -------- NC ND --------

    if sub == "NC / ND":

        with st.form("nc"):

            p = st.selectbox("Proveedor",
                             st.session_state.proveedores["Razon Social"])

            tipo = st.radio("Tipo", ["NC", "ND"])

            n = st.number_input("Monto")

            asoc = st.text_input("Nro Asociado")

            if st.form_submit_button("Guardar"):

                val = -n if tipo == "NC" else n

                df = st.session_state.compras

                df.loc[len(df)] = [
                    date.today(), p, "-", "-",
                    0, 0, 0, 0, 0,
                    0, val, tipo, asoc
                ]

                guardar("compras", df)

                st.success("Guardado")
                st.rerun()


    # -------- CTA CTE --------

    if sub == "Cuenta Corriente":

        p = st.selectbox("Proveedor",
                         st.session_state.proveedores["Razon Social"])

        df = st.session_state.compras

        f = df[df["Proveedor"] == p]

        st.dataframe(f)

        st.metric("Saldo", f["Total"].sum())


    # -------- GENERAL --------

    if sub == "General":

        df = st.session_state.compras

        g = df.groupby("Proveedor")["Total"].sum().reset_index()

        st.dataframe(g)


    # -------- HISTORIAL --------

    if sub == "Comprobantes":

        df = st.session_state.compras

        for i in reversed(df.index):

            r = df.loc[i]

            c1, c2 = st.columns([0.8, 0.2])

            c1.write(f"{r['Fecha']} | {r['Proveedor']} | $ {r['Total']}")

            if c2.button("🗑️", key=f"d{i}"):

                df = df.drop(i)

                st.session_state.compras = df

                guardar("compras", df)

                st.rerun()
