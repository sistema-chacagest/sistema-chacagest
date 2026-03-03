import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import base64
import plotly.graph_objects as go
import plotly.express as px
import calendar as cal_module

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="CHACAGEST - GESTIÓN TOTAL", page_icon="🚛", layout="wide")

COL_CLIENTES    = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
COL_VIAJES      = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
COL_PRESUPUESTOS= ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
COL_TESORERIA   = ["Fecha", "Tipo", "Caja/Banco", "Forma", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
COL_PROVEEDORES = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA", "CBU", "Alias"]
COL_COMPRAS     = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]

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
    try:
        sh = conectar_google()
        if sh is None: return None, None, None, None, None, None

        ws_c   = sh.worksheet("clientes")
        datos_c = ws_c.get_all_records()
        df_c   = pd.DataFrame(datos_c) if datos_c else pd.DataFrame(columns=COL_CLIENTES)

        ws_v   = sh.worksheet("viajes")
        datos_v = ws_v.get_all_records()
        df_v   = pd.DataFrame(datos_v) if datos_v else pd.DataFrame(columns=COL_VIAJES)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        try:
            ws_p   = sh.worksheet("presupuestos")
            datos_p = ws_p.get_all_records()
            df_p   = pd.DataFrame(datos_p) if datos_p else pd.DataFrame(columns=COL_PRESUPUESTOS)
            df_p['Importe'] = pd.to_numeric(df_p['Importe'], errors='coerce').fillna(0)
        except:
            df_p = pd.DataFrame(columns=COL_PRESUPUESTOS)

        try:
            ws_t   = sh.worksheet("tesoreria")
            datos_t = ws_t.get_all_records()
            df_t   = pd.DataFrame(datos_t) if datos_t else pd.DataFrame(columns=COL_TESORERIA)
            df_t['Monto'] = pd.to_numeric(df_t['Monto'], errors='coerce').fillna(0)
            # Compatibilidad: si la hoja existente no tiene columna "Forma", la agrega vacía
            if 'Forma' not in df_t.columns:
                df_t.insert(3, 'Forma', '-')
        except:
            df_t = pd.DataFrame(columns=COL_TESORERIA)

        try:
            ws_prov   = sh.worksheet("proveedores")
            datos_prov = ws_prov.get_all_records()
            df_prov   = pd.DataFrame(datos_prov) if datos_prov else pd.DataFrame(columns=COL_PROVEEDORES)
            for col in ["CBU", "Alias"]:
                if col not in df_prov.columns:
                    df_prov[col] = "-"
        except:
            df_prov = pd.DataFrame(columns=COL_PROVEEDORES)

        try:
            ws_com   = sh.worksheet("compras")
            datos_com = ws_com.get_all_records()
            df_com   = pd.DataFrame(datos_com) if datos_com else pd.DataFrame(columns=COL_COMPRAS)
            for c in ["Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]:
                df_com[c] = pd.to_numeric(df_com[c], errors='coerce').fillna(0)
        except:
            df_com = pd.DataFrame(columns=COL_COMPRAS)

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
        datos   = [df_save.columns.values.tolist()] + df_save.astype(str).values.tolist()
        ws.update(datos)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# =========================================================
# --- FUNCIONES PARA REPORTES HTML PROFESIONALES ---
# =========================================================

def generar_html_resumen(cliente, df, saldo):
    tabla_html = df.to_html(index=False, classes='tabla')
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; padding: 20px; }}
            .header-table {{ width: 100%; border-bottom: 4px solid #5e2d61; margin-bottom: 20px; }}
            .empresa-name {{ color: #5e2d61; font-size: 26px; font-weight: bold; margin: 0; }}
            .sub-title {{ color: #666; font-size: 14px; margin-top: 5px; }}
            .tabla {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: white; }}
            .tabla th {{ background-color: #f8f9fa; color: #5e2d61; border-bottom: 2px solid #5e2d61; padding: 12px; text-align: left; font-size: 13px; }}
            .tabla td {{ border-bottom: 1px solid #eee; padding: 10px; font-size: 12px; }}
            .footer-resumen {{ margin-top: 30px; padding: 15px; background: #5e2d61; color: white; border-radius: 8px; text-align: right; }}
            .total-label {{ font-size: 14px; opacity: 0.9; }}
            .total-monto {{ font-size: 22px; font-weight: bold; display: block; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td>
                    <p class="empresa-name">CHACABUCO NOROESTE TOUR S.R.L.</p>
                    <p class="sub-title">Desde 1996 viajando con vos | CHACAGEST Software System</p>
                </td>
                <td style="text-align: right;">
                    <p><b>ESTADO DE CUENTA</b><br>Emisión: {date.today()}</p>
                </td>
            </tr>
        </table>
        <div style="margin-bottom: 20px;">
            <p><b>CLIENTE:</b> {cliente}</p>
        </div>
        {tabla_html}
        <div class="footer-resumen">
            <span class="total-label">SALDO TOTAL PENDIENTE</span>
            <span class="total-monto">$ {saldo:,.2f}</span>
        </div>
    </body>
    </html>
    """

def generar_html_recibo(data):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .recibo-box {{ border: 3px double #5e2d61; padding: 30px; position: relative; }}
            .header-recibo {{ display: flex; justify-content: space-between; border-bottom: 1px solid #ccc; padding-bottom: 15px; }}
            .monto-destacado {{ font-size: 28px; color: #5e2d61; font-weight: bold; background: #f0f2f6; padding: 10px 20px; border-radius: 5px; }}
            .cuerpo {{ margin-top: 30px; line-height: 2.0; font-size: 16px; }}
            .firma-box {{ margin-top: 60px; border-top: 1px solid #333; width: 200px; text-align: center; float: right; font-size: 12px; }}
            .afip-ref {{ color: #777; font-size: 12px; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="recibo-box">
            <div class="header-recibo">
                <div>
                    <b style="font-size: 20px;">CHACABUCO NOROESTE TOUR S.R.L.</b><br>
                    <span>CUIT 30-71114824-4 - C.P. 6740 - Chacabuco, Bs. As.</span>
                </div>
                <div class="monto-destacado">$ {abs(data['Monto']):,.2f}</div>
            </div>
            <h2 style="text-align: center; text-decoration: underline;">RECIBO DE PAGO</h2>
            <div class="cuerpo">
                Recibimos de <b>{data['Cliente/Proveedor']}</b> la cantidad de pesos
                <span style="text-transform: uppercase;"><b>{abs(data['Monto']):,.2f}</b></span>
                en concepto de: <b>{data['Concepto']}</b>.<br>
                Realizado mediante: <b>{data['Caja/Banco']}</b>.<br>
                <span class="afip-ref">En Concepto de: {data['Ref AFIP']}</span>
            </div>
            <div style="margin-top: 40px;"><b>FECHA:</b> {data['Fecha']}</div>
            <div class="firma-box">Firma y Sello Responsable</div>
            <div style="clear: both;"></div>
            <p style="text-align: center; font-size: 9px; color: #aaa; margin-top: 50px;">Generado por CHACAGEST.</p>
        </div>
    </body>
    </html>
    """

def generar_html_orden_pago(data):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #333; }}
            .op-container {{ border: 2px solid #d35400; border-radius: 10px; padding: 30px; background-color: #fff; }}
            .header-op {{ border-bottom: 2px solid #d35400; padding-bottom: 15px; margin-bottom: 25px; }}
            .titulo-doc {{ font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; color: #444; }}
            .monto-op {{ background: #fff4e6; border: 1px dashed #d35400; padding: 15px; font-size: 22px; font-weight: bold; text-align: center; color: #d35400; margin: 20px 0; }}
            .detalle-table {{ width: 100%; margin-top: 20px; line-height: 1.8; }}
        </style>
    </head>
    <body>
        <div class="op-container">
            <div class="header-op">
                <h2 style="margin:0; color: #d35400;">CHACABUCO NOROESTE TOUR S.R.L.</h2>
                <small>Desde 1996, viajando con vos | CHACAGEST Software System</small>
            </div>
            <div class="titulo-doc">ORDEN DE PAGO A PROVEEDOR</div>
            <table class="detalle-table">
                <tr><td><b>BENEFICIARIO:</b></td><td>{data['Proveedor']}</td></tr>
                <tr><td><b>FECHA:</b></td><td>{data['Fecha']}</td></tr>
                <tr><td><b>CONCEPTO:</b></td><td>{data['Concepto']}</td></tr>
                <tr><td><b>REFERENCIA:</b></td><td>{data['Ref AFIP']}</td></tr>
            </table>
            <div class="monto-op">TOTAL PAGADO: $ {abs(data['Monto']):,.2f}</div>
            <div style="margin-top: 60px; border-top: 1px solid #333; width: 220px; text-align: center; float: right;">Recibí conforme</div>
            <div style="clear: both;"></div>
        </div>
    </body>
    </html>
    """

def generar_html_presupuesto(p_data):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Trebuchet MS', sans-serif; padding: 30px; }}
            .main-border {{ border: 1px solid #ddd; border-top: 10px solid #f39c12; padding: 40px; box-shadow: 0 0 10px #eee; }}
            .header-p {{ display: flex; justify-content: space-between; margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
            .label-presu {{ background: #f39c12; color: white; padding: 5px 15px; font-weight: bold; border-radius: 3px; }}
            .box-detalle {{ background: #fafafa; border: 1px solid #eee; padding: 20px; margin: 20px 0; min-height: 120px; }}
            .total-p {{ font-size: 24px; text-align: right; color: #333; border-top: 2px solid #333; padding-top: 10px; margin-top: 20px; }}
            .leyenda-box {{ margin-top: 30px; padding: 15px; border: 1px solid #f39c12; border-radius: 5px; background-color: #fffaf0; font-size: 13px; color: #555; }}
            .footer-p {{ margin-top: 40px; font-size: 11px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="main-border">
            <div class="header-p">
                <div>
                    <h1 style="margin:0; color:#444;">CHACABUCO NOROESTE TOUR S.R.L.</h1>
                    <small>VIAJES ESPECIALES - TURISMO - TRASLADOS PERSONALES</small>
                </div>
                <div style="text-align: right;">
                    <span class="label-presu">PRESUPUESTO</span><br>
                    <p style="margin-top:10px;"><b>Fecha:</b> {p_data['Fecha Emisión']}</p>
                </div>
            </div>
            <p><b>CLIENTE:</b> {p_data['Cliente']}</p>
            <p><b>TIPO DE UNIDAD:</b> {p_data['Tipo Móvil']}</p>
            <div class="box-detalle">
                <b>DETALLE DEL SERVICIO:</b><br><br>
                {str(p_data['Detalle']).replace(chr(10), '<br>')}
            </div>
            <div class="total-p">
                TOTAL: <span style="color: #d35400;">$ {p_data['Importe']:,.2f}</span>
            </div>
            <div class="leyenda-box">
                • La seña para la reserva es del 30%.<br>
                • Los gastos de los choferes (hospedaje y comida) estarán a cargo del contratante. En caso de que la empresa tenga que hacerse responsable de los mismos, el presente presupuesto deberá ser reformulado.
            </div>
            <p style="margin: 20px 0; font-size: 13px;"><b>Validez de la oferta:</b> Hasta el {p_data['Vencimiento']}</p>
            <div class="footer-p">
                CHACABUCO NOROESTE TOUR S.R.L. | Chacabuco, Buenos Aires | CHACAGEST Software System
            </div>
        </div>
    </body>
    </html>
    """

# --- 2. SISTEMA DE USUARIOS Y ROLES ---
# ─────────────────────────────────────────────────────────────────────────────
# USUARIOS DEL SISTEMA
# Estructura: "usuario": {"password": "...", "rol": "admin"/"operador", "caja": "NOMBRE CAJA"}
# rol "admin"   → acceso total (Dashboard, todas las cajas, todo el sistema)
# rol "operador"→ acceso a su caja propia, carga viajes/gastos/clientes/proveedores, sin Dashboard
#
# Para agregar un nuevo usuario: copiar uno de los bloques de operador y editar.
# Las cajas de operadores deben coincidir con los nombres en opc_cajas (más abajo).
# ─────────────────────────────────────────────────────────────────────────────
USUARIOS = {
    "admin": {
        "password": "chaca2026",
        "rol": "admin",
        "caja": None,           # Admin no tiene caja asignada, ve todas
        "nombre": "Administrador"
    },
    "coti": {
        "password": "coti2026",
        "rol": "operador",
        "caja": "CAJA COTI",    # Solo puede ver y operar CAJA COTI
        "nombre": "Coti"
    },
    "tato": {
        "password": "tato2026",
        "rol": "operador",
        "caja": "CAJA TATO",    # Solo puede ver y operar CAJA TATO
        "nombre": "Tato"
    },
    # ── Para agregar más usuarios, descomentá y editá el bloque: ──
    # "nuevo_usuario": {
    #     "password": "password123",
    #     "rol": "operador",
    #     "caja": "CAJA NUEVO",
    #     "nombre": "Nombre Visible"
    # },
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None
    st.session_state.rol_actual = None
    st.session_state.caja_propia = None
    st.session_state.nombre_usuario = None

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo_path.png", width=250)
        except: st.title("🚛 CHACAGEST")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            u_lower = u.strip().lower()
            if u_lower in USUARIOS and USUARIOS[u_lower]["password"] == p.strip():
                datos_usuario = USUARIOS[u_lower]
                st.session_state.autenticado    = True
                st.session_state.usuario_actual = u_lower
                st.session_state.rol_actual     = datos_usuario["rol"]
                st.session_state.caja_propia    = datos_usuario["caja"]
                st.session_state.nombre_usuario = datos_usuario["nombre"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# Helpers de rol
es_admin    = st.session_state.rol_actual == "admin"
es_operador = st.session_state.rol_actual == "operador"
caja_propia = st.session_state.caja_propia

# --- 3. INICIALIZACIÓN ---
if 'clientes' not in st.session_state or 'viajes' not in st.session_state:
    c, v, p, t, prov, com = cargar_datos()
    st.session_state.clientes     = c    if c    is not None else pd.DataFrame(columns=COL_CLIENTES)
    st.session_state.viajes       = v    if v    is not None else pd.DataFrame(columns=COL_VIAJES)
    st.session_state.presupuestos = p    if p    is not None else pd.DataFrame(columns=COL_PRESUPUESTOS)
    st.session_state.tesoreria    = t    if t    is not None else pd.DataFrame(columns=COL_TESORERIA)
    st.session_state.proveedores  = prov if prov is not None else pd.DataFrame(columns=COL_PROVEEDORES)
    st.session_state.compras      = com  if com  is not None else pd.DataFrame(columns=COL_COMPRAS)

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
    .stDataFrame { border: 1px solid #5e2d61; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    try: st.image("logo_path.png", use_container_width=True)
    except: pass
    st.markdown("---")

    # ── Badge de usuario logueado ──
    rol_badge = "🔑 Admin" if es_admin else f"👤 {st.session_state.nombre_usuario}"
    caja_badge = "" if es_admin else f" | 🏦 {caja_propia}"
    st.markdown(f"<div style='background:#5e2d61;color:white;padding:8px 12px;border-radius:8px;font-size:13px;font-weight:bold;margin-bottom:8px;'>{rol_badge}{caja_badge}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Menú principal: Admin ve todo, Operador no ve Dashboard ──
    if es_admin:
        opciones_menu = ["CALENDARIO", "DASHBOARD", "VENTAS", "COMPRAS", "TESORERIA"]
        iconos_menu   = ["calendar3", "bar-chart-line", "cart4", "bag-check", "safe"]
    else:
        opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
        iconos_menu   = ["calendar3", "cart4", "bag-check", "safe"]

    menu_principal = option_menu(
        menu_title=None,
        options=opciones_menu,
        icons=iconos_menu,
        default_index=0,
        key="menu_p",
        styles={
            "container": {"padding": "0px", "background-color": "#f0f2f6"},
            "nav-link": {"font-size": "15px", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )

    sel_sub = None
    if menu_principal == "VENTAS":
        st.markdown("<div style='margin-left: 20px; border-left: 2px solid #f39c12; padding-left: 10px;'>", unsafe_allow_html=True)
        # Operadores no ven CTA CTE GENERAL ni COMPROBANTES (movimientos de otros)
        if es_admin:
            opciones_ventas = ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"]
            iconos_ventas   = ["people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"]
        else:
            opciones_ventas = ["CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "COMPROBANTES"]
            iconos_ventas   = ["people", "truck", "file-earmark-spreadsheet", "person-vcard", "file-text"]
        sel_sub = option_menu(
            menu_title=None,
            options=opciones_ventas,
            icons=iconos_ventas,
            default_index=0,
            key="menu_s",
            styles={
                "container": {"background-color": "transparent", "padding": "0px"},
                "nav-link": {"font-size": "13px", "text-align": "left", "margin": "2px"},
                "nav-link-selected": {"background-color": "#f39c12", "color": "white"},
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif menu_principal == "COMPRAS":
        st.markdown("<div style='margin-left: 20px; border-left: 2px solid #f39c12; padding-left: 10px;'>", unsafe_allow_html=True)
        # Operadores no ven CTA CTE GENERAL PROV (estados globales)
        if es_admin:
            opciones_compras = ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "CTA CTE GENERAL PROV", "HISTORICO COMPRAS"]
            iconos_compras   = ["person-plus", "receipt", "person-vcard", "globe", "clock-history"]
        else:
            opciones_compras = ["CARGA PROVEEDOR", "CARGA GASTOS", "CTA CTE PROVEEDOR", "HISTORICO COMPRAS"]
            iconos_compras   = ["person-plus", "receipt", "person-vcard", "clock-history"]
        sel_sub = option_menu(
            menu_title=None,
            options=opciones_compras,
            icons=iconos_compras,
            default_index=0,
            key="menu_c",
            styles={
                "container": {"background-color": "transparent", "padding": "0px"},
                "nav-link": {"font-size": "13px", "text-align": "left", "margin": "2px"},
                "nav-link-selected": {"background-color": "#f39c12", "color": "white"},
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Sincronizar"):
        with st.spinner("Sincronizando..."):
            c, v, p, t, prov, com = cargar_datos()
            st.session_state.clientes     = c    if c    is not None else pd.DataFrame(columns=COL_CLIENTES)
            st.session_state.viajes       = v    if v    is not None else pd.DataFrame(columns=COL_VIAJES)
            st.session_state.presupuestos = p    if p    is not None else pd.DataFrame(columns=COL_PRESUPUESTOS)
            st.session_state.tesoreria    = t    if t    is not None else pd.DataFrame(columns=COL_TESORERIA)
            st.session_state.proveedores  = prov if prov is not None else pd.DataFrame(columns=COL_PROVEEDORES)
            st.session_state.compras      = com  if com  is not None else pd.DataFrame(columns=COL_COMPRAS)
            st.rerun()

    if st.button("🚪 Cerrar Sesión"):
        for key in ["autenticado", "usuario_actual", "rol_actual", "caja_propia", "nombre_usuario"]:
            st.session_state[key] = False if key == "autenticado" else None
        st.rerun()

# ── Definición de sel ── SIEMPRE después del sidebar
if menu_principal in ["VENTAS", "COMPRAS"]:
    sel = sel_sub
else:
    sel = menu_principal

# ── Bloqueo de seguridad: si operador intenta acceder a DASHBOARD vía URL ──
if sel == "DASHBOARD" and es_operador:
    st.error("🚫 Acceso denegado. Solo el administrador puede ver el Dashboard.")
    st.stop()

# --- 6. MÓDULOS ---

# =============================================================
# DASHBOARD
# =============================================================
if sel == "DASHBOARD":
    st.header("📊 Dashboard de Control Financiero")

    MESES_NOMBRES = {
        1:"Enero", 2:"Febrero", 3:"Marzo",    4:"Abril",
        5:"Mayo",  6:"Junio",   7:"Julio",     8:"Agosto",
        9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
    }
    MESES_ORDEN = list(range(1, 13))
    MESES_LABEL = [cal_module.month_abbr[m] for m in MESES_ORDEN]

    # ── Preparar INGRESOS ──
    df_ing = st.session_state.viajes.copy()
    df_ing = df_ing[df_ing['Importe'] > 0].copy()
    df_ing['Fecha Viaje'] = pd.to_datetime(df_ing['Fecha Viaje'], errors='coerce')
    df_ing = df_ing.dropna(subset=['Fecha Viaje'])
    df_ing['Año'] = df_ing['Fecha Viaje'].dt.year
    df_ing['Mes'] = df_ing['Fecha Viaje'].dt.month

    # ── Preparar GASTOS ──
    df_gas = st.session_state.compras.copy()
    df_gas = df_gas[df_gas['Total'] > 0].copy()
    df_gas['Fecha'] = pd.to_datetime(df_gas['Fecha'], errors='coerce')
    df_gas = df_gas.dropna(subset=['Fecha'])
    df_gas['Año'] = df_gas['Fecha'].dt.year
    df_gas['Mes'] = df_gas['Fecha'].dt.month

    # Enriquecer gastos con Cuenta de Gastos del proveedor
    if not st.session_state.proveedores.empty:
        df_gas = df_gas.merge(
            st.session_state.proveedores[['Razón Social', 'Cuenta de Gastos']],
            left_on='Proveedor', right_on='Razón Social', how='left'
        )
        df_gas['Cuenta de Gastos'] = df_gas['Cuenta de Gastos'].fillna('SIN CATEGORÍA')
    else:
        df_gas['Cuenta de Gastos'] = 'SIN CATEGORÍA'

    # ── Años disponibles ──
    años_ing  = set(df_ing['Año'].unique()) if not df_ing.empty else set()
    años_gas  = set(df_gas['Año'].unique()) if not df_gas.empty else set()
    años_disp = sorted(años_ing | años_gas, reverse=True)
    if not años_disp:
        años_disp = [date.today().year]

    # ── Selectores ──
    col_v1, col_v2, col_v3 = st.columns([1, 1, 2])
    vista   = col_v1.radio("Vista", ["Mensual", "Anual"], horizontal=True)
    año_sel = col_v2.selectbox("Año", años_disp)

    mes_sel = None
    if vista == "Mensual":
        mes_sel = col_v3.selectbox(
            "Mes",
            options=list(MESES_NOMBRES.keys()),
            format_func=lambda x: MESES_NOMBRES[x],
            index=date.today().month - 1
        )

    # ── Filtrar ──
    if vista == "Mensual":
        df_ing_f = df_ing[(df_ing['Año'] == año_sel) & (df_ing['Mes'] == mes_sel)]
        df_gas_f = df_gas[(df_gas['Año'] == año_sel) & (df_gas['Mes'] == mes_sel)]
        titulo_periodo = f"{MESES_NOMBRES[mes_sel]} {año_sel}"
    else:
        df_ing_f = df_ing[df_ing['Año'] == año_sel]
        df_gas_f = df_gas[df_gas['Año'] == año_sel]
        titulo_periodo = f"Año {año_sel}"

    total_ing = df_ing_f['Importe'].sum()
    total_gas = df_gas_f['Total'].sum()
    resultado = total_ing - total_gas
    margen    = (resultado / total_ing * 100) if total_ing > 0 else 0

    st.markdown(f"### Período: {titulo_periodo}")
    st.markdown("---")

    # ── KPIs ──
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Ingresos", f"$ {total_ing:,.0f}")
    k2.metric("💸 Total Gastos",   f"$ {total_gas:,.0f}")
    k3.metric(
        "📈 Resultado Neto",
        f"$ {resultado:,.0f}",
        delta=f"{'▲' if resultado >= 0 else '▼'} {abs(resultado):,.0f}",
        delta_color="normal" if resultado >= 0 else "inverse"
    )
    k4.metric("📊 Margen", f"{margen:.1f} %")

    st.markdown("---")

    COLORES = ["#5e2d61", "#f39c12", "#d35400", "#2ecc71",
               "#3498db", "#e74c3c", "#9b59b6", "#1abc9c"]

    col_g1, col_g2 = st.columns(2)

    # ── Gráfico 1: Ingresos vs Gastos ──
    with col_g1:
        if vista == "Anual":
            ing_mes = df_ing_f.groupby('Mes')['Importe'].sum().reindex(MESES_ORDEN, fill_value=0)
            gas_mes = df_gas_f.groupby('Mes')['Total'].sum().reindex(MESES_ORDEN, fill_value=0)
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(name="Ingresos", x=MESES_LABEL, y=ing_mes.values,  marker_color="#5e2d61"))
            fig1.add_trace(go.Bar(name="Gastos",   x=MESES_LABEL, y=gas_mes.values,  marker_color="#f39c12"))
            fig1.update_layout(
                title=f"Ingresos vs Gastos — {año_sel}",
                barmode='group', plot_bgcolor='white',
                legend=dict(orientation="h", y=-0.2),
                yaxis_tickprefix="$", margin=dict(t=40, b=10)
            )
        else:
            dias_mes  = cal_module.monthrange(año_sel, mes_sel)[1]
            todos_dias = list(range(1, dias_mes + 1))
            df_ing_d  = df_ing_f.copy(); df_ing_d['Dia'] = df_ing_d['Fecha Viaje'].dt.day
            df_gas_d  = df_gas_f.copy(); df_gas_d['Dia'] = df_gas_d['Fecha'].dt.day
            ing_dia   = df_ing_d.groupby('Dia')['Importe'].sum().reindex(todos_dias, fill_value=0)
            gas_dia   = df_gas_d.groupby('Dia')['Total'].sum().reindex(todos_dias, fill_value=0)
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(name="Ingresos", x=todos_dias, y=ing_dia.values, marker_color="#5e2d61"))
            fig1.add_trace(go.Bar(name="Gastos",   x=todos_dias, y=gas_dia.values, marker_color="#f39c12"))
            fig1.update_layout(
                title=f"Ingresos vs Gastos por Día — {MESES_NOMBRES[mes_sel]} {año_sel}",
                barmode='group', plot_bgcolor='white',
                legend=dict(orientation="h", y=-0.2),
                xaxis_title="Día", yaxis_tickprefix="$",
                margin=dict(t=40, b=10)
            )
        st.plotly_chart(fig1, use_container_width=True)

    # ── Gráfico 2: Torta de gastos por categoría ──
    with col_g2:
        if not df_gas_f.empty:
            gas_cat = df_gas_f.groupby('Cuenta de Gastos')['Total'].sum().reset_index()
            fig2 = px.pie(
                gas_cat, values='Total', names='Cuenta de Gastos',
                title=f"Gastos por Categoría — {titulo_periodo}",
                color_discrete_sequence=COLORES, hole=0.4
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=40, b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin gastos registrados para el período seleccionado.")

    col_g3, col_g4 = st.columns(2)

    # ── Gráfico 3: Tendencia (anual) o Top clientes (mensual) ──
    with col_g3:
        if vista == "Anual":
            ing_mes   = df_ing_f.groupby('Mes')['Importe'].sum().reindex(MESES_ORDEN, fill_value=0)
            gas_mes   = df_gas_f.groupby('Mes')['Total'].sum().reindex(MESES_ORDEN, fill_value=0)
            res_mes   = ing_mes - gas_mes
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=MESES_LABEL, y=res_mes.values,
                mode='lines+markers+text',
                text=[f"${v:,.0f}" for v in res_mes.values],
                textposition="top center",
                line=dict(color="#5e2d61", width=3),
                marker=dict(size=8, color="#f39c12"),
                fill='tozeroy', fillcolor='rgba(94,45,97,0.1)',
                name="Resultado Neto"
            ))
            fig3.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
            fig3.update_layout(
                title="Tendencia del Resultado Neto",
                plot_bgcolor='white', yaxis_tickprefix="$",
                margin=dict(t=40, b=10)
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            if not df_ing_f.empty:
                top_cli = (df_ing_f.groupby('Cliente')['Importe'].sum()
                           .reset_index().sort_values('Importe').tail(5))
                fig3 = go.Figure(go.Bar(
                    x=top_cli['Importe'], y=top_cli['Cliente'],
                    orientation='h', marker_color="#5e2d61",
                    text=[f"$ {v:,.0f}" for v in top_cli['Importe']],
                    textposition='outside'
                ))
                fig3.update_layout(
                    title="Top 5 Clientes del Mes",
                    plot_bgcolor='white', xaxis_tickprefix="$",
                    margin=dict(t=40, b=10)
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Sin ingresos en el período.")

    # ── Gráfico 4: Mapa de calor (anual) o Barras categoría (mensual) ──
    with col_g4:
        if not df_gas_f.empty:
            if vista == "Anual":
                pivot = df_gas_f.pivot_table(
                    index='Cuenta de Gastos', columns='Mes',
                    values='Total', aggfunc='sum', fill_value=0
                )
                pivot.columns = [cal_module.month_abbr[m] for m in pivot.columns]
                fig4 = px.imshow(
                    pivot,
                    color_continuous_scale=[[0,"#fff4e6"],[0.5,"#f39c12"],[1,"#d35400"]],
                    title="Mapa de Gastos por Categoría y Mes",
                    text_auto=True, aspect="auto"
                )
                fig4.update_layout(margin=dict(t=40, b=10))
            else:
                gas_c = (df_gas_f.groupby('Cuenta de Gastos')['Total'].sum()
                         .reset_index().sort_values('Total'))
                fig4 = go.Figure(go.Bar(
                    x=gas_c['Total'], y=gas_c['Cuenta de Gastos'],
                    orientation='h', marker_color="#f39c12",
                    text=[f"$ {v:,.0f}" for v in gas_c['Total']],
                    textposition='outside'
                ))
                fig4.update_layout(
                    title="Gastos por Categoría del Mes",
                    plot_bgcolor='white', xaxis_tickprefix="$",
                    margin=dict(t=40, b=10)
                )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Sin gastos registrados en el período.")

    # ── Tabla resumen ──
    st.markdown("---")
    st.subheader("📋 Resumen por Categoría de Gasto")
    if not df_gas_f.empty:
        res_cat = df_gas_f.groupby('Cuenta de Gastos')['Total'].agg(
            Total='sum', Comprobantes='count'
        ).reset_index().sort_values('Total', ascending=False)
        res_cat['% del Total'] = (res_cat['Total'] / res_cat['Total'].sum() * 100).round(1).astype(str) + " %"
        res_cat['Total']       = res_cat['Total'].apply(lambda x: f"$ {x:,.2f}")
        res_cat.columns        = ['Categoría', 'Total Gastado', 'N° Comprobantes', '% del Total']
        st.dataframe(res_cat, use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de gastos para el período.")

    st.caption(f"Última actualización: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} hs")

# =============================================================
# CALENDARIO
# =============================================================
elif sel == "CALENDARIO":
    st.header("📅 Agenda de Viajes")
    if "viaje_ver" not in st.session_state:
        st.session_state.viaje_ver = None
    eventos = []
    df_solo_viajes = st.session_state.viajes[st.session_state.viajes['Importe'] > 0]
    for i, row in df_solo_viajes.iterrows():
        if str(row['Fecha Viaje']) != "-" and row['Origen'] != "AJUSTE":
            eventos.append({
                "id": str(i), "title": f"🚛 {row['Cliente']}", "start": str(row['Fecha Viaje']),
                "allDay": True, "backgroundColor": "#f39c12", "borderColor": "#d35400"
            })
    cal_options  = {"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "locale": "es", "height": 600}
    custom_css   = ".fc-button-primary { background-color: #5e2d61 !important; border-color: #5e2d61 !important; } .fc-event { background-color: #f39c12 !important; } .fc-toolbar-title { color: #5e2d61 !important; }"
    res_cal      = calendar(events=eventos, options=cal_options, custom_css=custom_css, key="cal_final")
    if res_cal.get("eventClick"):
        st.session_state.viaje_ver = int(res_cal["eventClick"]["event"]["id"])
    if st.session_state.viaje_ver is not None:
        idx = st.session_state.viaje_ver
        if idx in st.session_state.viajes.index:
            v_det = st.session_state.viajes.loc[idx]
            if st.button("❌ Cerrar"): st.session_state.viaje_ver = None; st.rerun()
            st.markdown(f"""<div style="background-color: #f0f2f6; padding: 15px; border-left: 5px solid #f39c12; border-radius: 5px; margin-top: 20px;">
                <h4 style="color: #5e2d61; margin: 0;">Detalles</h4><p><b>Cliente:</b> {v_det['Cliente']}</p>
                <p><b>Ruta:</b> {v_det['Origen']} ➔ {v_det['Destino']}</p>
                <p><b>Importe:</b> $ {v_det['Importe']}</p></div>""", unsafe_allow_html=True)

elif sel == "CLIENTES":
    st.header("👤 Gestión de Clientes")
    if st.session_state.get("msg_cliente"):
        st.success(st.session_state.msg_cliente)
        st.session_state.msg_cliente = None
    with st.expander("➕ ALTA DE NUEVO CLIENTE", expanded=False):
        with st.form("f_cli", clear_on_submit=True):
            c1, c2 = st.columns(2)
            r      = c1.text_input("Razón Social *")
            cuit   = c2.text_input("CUIT *")
            mail   = c1.text_input("Email")
            tel    = c2.text_input("Teléfono")
            dir_f  = c1.text_input("Dirección Fiscal")
            loc    = c2.text_input("Localidad")
            prov   = c1.text_input("Provincia")
            c_iva  = c2.selectbox("Condición IVA", ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"])
            c_vta  = c1.selectbox("Condición de Venta", ["Cuenta Corriente", "Contado"])
            if st.form_submit_button("REGISTRAR CLIENTE"):
                if r and cuit:
                    nueva_fila = pd.DataFrame([[r, cuit, mail, tel, dir_f, loc, prov, c_iva, c_vta]], columns=COL_CLIENTES)
                    st.session_state.clientes = pd.concat([st.session_state.clientes, nueva_fila], ignore_index=True)
                    guardar_datos("clientes", st.session_state.clientes)
                    st.session_state.msg_cliente = f"✅ Cliente '{r}' registrado correctamente."
                    st.rerun()
                else:
                    st.warning("Completá Razón Social y CUIT para continuar.")
    st.subheader("📋 Base de Clientes")
    if not st.session_state.clientes.empty:
        for i, row in st.session_state.clientes.iterrows():
            with st.container():
                c_inf, c_ed, c_el = st.columns([0.7, 0.15, 0.15])
                c_inf.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT / CUIL / DNI *']}")
                c_inf.caption(f"📍 {row['Localidad']} - {row['Provincia']} | 📞 {row['Teléfono']}")
                if c_ed.button("📝 Editar", key=f"edit_{i}"): st.session_state[f"edit_mode_{i}"] = True
                if c_el.button("🗑️", key=f"del_cli_{i}"):
                    tiene_viajes = not st.session_state.viajes[st.session_state.viajes['Cliente'] == row['Razón Social']].empty
                    if tiene_viajes: st.error("No se puede eliminar: tiene viajes asociados.")
                    else:
                        st.session_state.clientes = st.session_state.clientes.drop(i).reset_index(drop=True)
                        guardar_datos("clientes", st.session_state.clientes)
                        st.rerun()
                if st.session_state.get(f"edit_mode_{i}", False):
                    with st.form(f"f_edit_{i}"):
                        ce1, ce2 = st.columns(2)
                        n_rs   = ce1.text_input("Razón Social", value=row['Razón Social'])
                        n_cuit = ce2.text_input("CUIT", value=row['CUIT / CUIL / DNI *'])
                        n_mail = ce1.text_input("Email", value=row['Email'])
                        n_tel  = ce2.text_input("Teléfono", value=row['Teléfono'])
                        n_loc  = ce1.text_input("Localidad", value=row['Localidad'])
                        n_prov = ce2.text_input("Provincia", value=row['Provincia'])
                        be1, be2 = st.columns(2)
                        if be1.form_submit_button("✅ Guardar"):
                            st.session_state.clientes.loc[i] = [n_rs, n_cuit, n_mail, n_tel, row['Dirección Fiscal'], n_loc, n_prov, row['Condición IVA'], row['Condición de Venta']]
                            guardar_datos("clientes", st.session_state.clientes)
                            st.session_state[f"edit_mode_{i}"] = False
                            st.rerun()
                        if be2.form_submit_button("❌ Cancelar"): st.session_state[f"edit_mode_{i}"] = False; st.rerun()
                st.divider()
    else: st.info("No hay clientes registrados.")

elif sel == "CARGA VIAJE":
    st.header("🚛 Registro de Viaje")
    if st.session_state.get("msg_viaje"):
        st.success(st.session_state.msg_viaje)
        st.session_state.msg_viaje = None
    with st.form("f_v", clear_on_submit=True):
        cli  = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
        c1, c2 = st.columns(2)
        f_v  = c1.date_input("Fecha")
        pat  = c2.text_input("Patente")
        orig = st.text_input("Origen")
        dest = st.text_input("Destino")
        imp  = st.number_input("Importe Neto $", min_value=0.0)
        cond = st.selectbox("Tipo de Pago", ["Cuenta Corriente", "Contado"])
        if st.form_submit_button("GUARDAR VIAJE"):
            if cli and imp > 0:
                nv = pd.DataFrame([[date.today(), cli, f_v, orig, dest, pat, imp, f"Factura ({cond})", "-"]], columns=COL_VIAJES)
                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                guardar_datos("viajes", st.session_state.viajes)
                st.session_state.msg_viaje = f"✅ Viaje de '{cli}' registrado correctamente por $ {imp:,.2f}."
                st.rerun()
            else:
                st.warning("Seleccioná un cliente y completá el importe.")

elif sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    tab_crear, tab_historial = st.tabs(["🆕 Crear Presupuesto", "📂 Historial y Descargas"])
    with tab_crear:
        if st.session_state.get("msg_presupuesto"):
            st.success(st.session_state.msg_presupuesto)
            st.session_state.msg_presupuesto = None
        with st.form("f_presu", clear_on_submit=True):
            c1, c2   = st.columns(2)
            p_cli    = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            p_f_emi  = c2.date_input("Fecha Emisión", date.today())
            c3, c4   = st.columns(2)
            p_f_venc = c3.date_input("Fecha Vencimiento", date.today() + timedelta(days=7))
            p_movil  = c4.selectbox("Tipo de Móvil", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            p_det    = st.text_area("Detalle del Presupuesto (Servicio, Ruta, Horarios...)")
            p_imp    = st.number_input("Importe Total $", min_value=0.0)
            if st.form_submit_button("GENERAR PRESUPUESTO"):
                if p_cli and p_imp > 0:
                    nuevo_p = pd.DataFrame([[p_f_emi, p_cli, p_f_venc, p_det, p_movil, p_imp]], columns=COL_PRESUPUESTOS)
                    st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, nuevo_p], ignore_index=True)
                    guardar_datos("presupuestos", st.session_state.presupuestos)
                    st.session_state.msg_presupuesto = f"✅ Presupuesto para '{p_cli}' guardado por $ {p_imp:,.2f}."
                    st.rerun()
                else:
                    st.warning("Seleccioná cliente y completá el importe.")
    with tab_historial:
        if not st.session_state.presupuestos.empty:
            for i in reversed(st.session_state.presupuestos.index):
                row_p = st.session_state.presupuestos.loc[i]
                with st.container():
                    c_a, c_b, c_c = st.columns([0.6, 0.2, 0.2])
                    c_a.markdown(f"**{row_p['Cliente']}** | {row_p['Tipo Móvil']}")
                    c_a.caption(f"Emisión: {row_p['Fecha Emisión']} - Vence: {row_p['Vencimiento']}")
                    c_b.markdown(f"**$ {row_p['Importe']:,.2f}**")
                    html_p = generar_html_presupuesto(row_p)
                    c_c.download_button(label="📄 Descargar", data=html_p, file_name=f"Presupuesto_{row_p['Cliente']}_{row_p['Fecha Emisión']}.html", mime="text/html", key=f"dl_p_{i}")
                    if c_c.button("🗑️", key=f"del_presu_{i}"):
                        st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
                        guardar_datos("presupuestos", st.session_state.presupuestos)
                        st.rerun()
                    st.divider()
        else: st.info("No hay presupuestos registrados.")

elif sel == "TESORERIA":
    st.header("💰 Tesorería")

    # ── Cajas disponibles según rol ──
    # Admin ve todas. Operador solo ve su caja asignada.
    TODAS_CAJAS = ["CAJA COTI", "CAJA TATO", "BANCO GALICIA", "BANCO PROVINCIA", "TARJETA DE CREDITO", "BANCO SUPERVIELLE", "DOLAR CAJA COTI", "DOLAR CAJA TATO"]

    if es_admin:
        opc_cajas = TODAS_CAJAS
        FORMAS_PAGO = ["EFECTIVO", "TRANSFERENCIA", "TARJETA DE CREDITO", "DÓLARES"]
    else:
        opc_cajas   = [caja_propia]
        FORMAS_PAGO = ["EFECTIVO", "TRANSFERENCIA", "TARJETA DE CREDITO", "DÓLARES"]
        st.info(f"🏦 Operando en: **{caja_propia}**")

    # ── Tabs: Admin ve todos, Operador no ve Traspaso ni Orden de Pago
    #         pero SÍ ve "Pase de Efectivo" (puede pasar efectivo a otra caja) ──
    if es_admin:
        tab_ing, tab_egr, tab_cob, tab_ver, tab_pase, tab_tras, tab_op = st.tabs(
            ["📥 INGRESOS VARIOS", "📤 EGRESOS VARIOS", "🧾 COBRANZA VIAJE", "📊 VER MOVIMIENTOS", "💱 PASE DE EFECTIVO", "🔄 TRASPASO", "💸 ORDEN DE PAGO"]
        )
    else:
        tab_ing, tab_egr, tab_cob, tab_ver, tab_pase = st.tabs(
            ["📥 INGRESOS VARIOS", "📤 EGRESOS VARIOS", "🧾 COBRANZA VIAJE", "📊 MIS MOVIMIENTOS", "💱 PASE DE EFECTIVO"]
        )
        tab_tras = None
        tab_op   = None

    with tab_ing:
        if st.session_state.get("msg_ingreso"):
            st.success(st.session_state.msg_ingreso)
            st.session_state.msg_ingreso = None
        with st.form("f_ing_var", clear_on_submit=True):
            f   = st.date_input("Fecha", date.today())
            # Admin elige caja; operador tiene la suya fija
            if es_admin:
                cj  = st.selectbox("Caja Destino", opc_cajas)
            else:
                st.markdown(f"**Caja:** {caja_propia}")
                cj = caja_propia
            forma = st.selectbox("Forma de Ingreso", FORMAS_PAGO)
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR INGRESO"):
                if mon > 0:
                    concepto_completo = con if con else "-"
                    nt = pd.DataFrame([[f, "INGRESO VARIO", cj, forma, concepto_completo, "Varios", mon, "-"]], columns=COL_TESORERIA)
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                    guardar_datos("tesoreria", st.session_state.tesoreria)
                    st.session_state.msg_ingreso = f"✅ Ingreso de $ {mon:,.2f} ({forma}) registrado en {cj}."
                    st.rerun()
                else:
                    st.warning("Ingresá un monto mayor a cero.")

    with tab_egr:
        if st.session_state.get("msg_egreso"):
            st.success(st.session_state.msg_egreso)
            st.session_state.msg_egreso = None
        with st.form("f_egr_var", clear_on_submit=True):
            f   = st.date_input("Fecha", date.today())
            if es_admin:
                cj  = st.selectbox("Caja Origen", opc_cajas)
            else:
                st.markdown(f"**Caja:** {caja_propia}")
                cj = caja_propia
            forma = st.selectbox("Forma de Egreso", FORMAS_PAGO)
            con = st.text_input("Concepto")
            mon = st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("REGISTRAR EGRESO"):
                if mon > 0:
                    concepto_completo = con if con else "-"
                    nt = pd.DataFrame([[f, "EGRESO VARIO", cj, forma, concepto_completo, "Varios", -mon, "-"]], columns=COL_TESORERIA)
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                    guardar_datos("tesoreria", st.session_state.tesoreria)
                    st.session_state.msg_egreso = f"✅ Egreso de $ {mon:,.2f} ({forma}) registrado desde {cj}."
                    st.rerun()
                else:
                    st.warning("Ingresá un monto mayor a cero.")

    with tab_cob:
        if "html_recibo_ready" not in st.session_state: st.session_state.html_recibo_ready = None
        with st.form("f_cob", clear_on_submit=True):
            c_sel = st.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            if es_admin:
                cj       = st.selectbox("Caja Destino", opc_cajas)
                forma_cob = st.selectbox("Forma de Cobro", FORMAS_PAGO + ["OTROS"])
            else:
                cj        = caja_propia
                forma_cob = st.selectbox("Forma de Cobro", FORMAS_PAGO + ["OTROS"])
            mon   = st.number_input("Monto $", min_value=0.0)
            afip  = st.text_input("Comprobante Asociado (AFIP/Recibo)")
            if st.form_submit_button("GENERAR COBRANZA"):
                if c_sel and mon > 0:
                    nt = pd.DataFrame([[date.today(), "COBRANZA", cj, forma_cob, "Cobro Viaje", c_sel, mon, afip]], columns=COL_TESORERIA)
                    nv = pd.DataFrame([[date.today(), c_sel, date.today(), "PAGO", "TESORERIA", "-", -mon, "RECIBO", afip]], columns=COL_VIAJES)
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                    st.session_state.viajes    = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                    guardar_datos("tesoreria", st.session_state.tesoreria)
                    guardar_datos("viajes", st.session_state.viajes)
                    st.session_state.html_recibo_ready = generar_html_recibo({
                        "Fecha": date.today(), "Cliente/Proveedor": c_sel,
                        "Concepto": "Cobro de Viaje", "Caja/Banco": f"{cj} - {forma_cob}",
                        "Monto": mon, "Ref AFIP": afip
                    })
                    st.session_state.cli_ready = c_sel
                    st.rerun()
                else:
                    st.warning("Completá el cliente y el monto antes de continuar.")
        if st.session_state.html_recibo_ready:
            st.success(f"✅ Cobranza de '{st.session_state.cli_ready}' registrada con éxito.")
            st.download_button("🖨️ IMPRIMIR RECIBO PDF/HTML", st.session_state.html_recibo_ready, file_name=f"Recibo_{st.session_state.cli_ready}.html", mime="text/html")
            if st.button("Limpiar"): st.session_state.html_recibo_ready = None; st.rerun()

    with tab_ver:
        # Admin puede elegir cualquier caja. Operador solo ve la suya.
        if es_admin:
            cj_v = st.selectbox("Seleccionar Caja", opc_cajas)
        else:
            cj_v = caja_propia
            st.markdown(f"#### 🏦 {caja_propia}")

        df_ver = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj_v].copy()

        # ── Resumen desglosado por Forma ──
        FORMAS_RESUMEN = ["EFECTIVO", "TRANSFERENCIA", "TARJETA DE CREDITO", "DÓLARES", "OTROS"]
        ICONOS_FORMA   = {"EFECTIVO": "💵", "TRANSFERENCIA": "🏦", "TARJETA DE CREDITO": "💳", "DÓLARES": "💲", "OTROS": "📋"}

        cols_formas = st.columns(len(FORMAS_RESUMEN))

        for idx, forma_r in enumerate(FORMAS_RESUMEN):
            mask = df_ver['Forma'].fillna('-').str.upper().str.contains(forma_r.replace("DÓLARES", "DOLAR").replace("TARJETA DE CREDITO", "TARJETA"), na=False)
            saldo_forma = df_ver[mask]['Monto'].sum()
            icono = ICONOS_FORMA.get(forma_r, "💰")
            color = "#2ecc71" if saldo_forma >= 0 else "#e74c3c"
            cols_formas[idx].markdown(
                f"<div style='background:#f8f9fa;border-radius:10px;padding:12px;text-align:center;border-left:4px solid {color};'>"
                f"<div style='font-size:22px;'>{icono}</div>"
                f"<div style='font-size:11px;color:#666;font-weight:bold;'>{forma_r}</div>"
                f"<div style='font-size:16px;font-weight:bold;color:{color};'>$ {saldo_forma:,.2f}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("##### 📋 Detalle de Movimientos")
        st.dataframe(df_ver, use_container_width=True)

    # ── PASE DE EFECTIVO: disponible para todos (operador pasa desde su caja, admin elige) ──
    with tab_pase:
        if st.session_state.get("msg_pase"):
            st.success(st.session_state.msg_pase)
            st.session_state.msg_pase = None
        st.markdown("Registrá el pase de efectivo físico de una caja a otra. Se genera un egreso en la caja origen y un ingreso en la caja destino.")
        with st.form("f_pase", clear_on_submit=True):
            c1, c2 = st.columns(2)
            if es_admin:
                origen_pase  = c1.selectbox("Caja Origen (sale el efectivo)", TODAS_CAJAS, key="pase_orig")
                destino_pase = c2.selectbox("Caja Destino (entra el efectivo)", TODAS_CAJAS, key="pase_dest")
            else:
                st.markdown(f"**Caja Origen:** {caja_propia}")
                origen_pase  = caja_propia
                # El operador puede mandar efectivo a cualquier otra caja
                otras_cajas  = [c for c in TODAS_CAJAS if c != caja_propia]
                destino_pase = c2.selectbox("Caja Destino (entra el efectivo)", otras_cajas, key="pase_dest")
            forma_pase = st.selectbox("Tipo de valor", ["EFECTIVO", "DÓLARES"], key="pase_forma")
            monto_pase = st.number_input("Monto a pasar $", min_value=0.0, key="pase_monto")
            concepto_pase = st.text_input("Concepto (opcional)", key="pase_concepto")
            if st.form_submit_button("💱 REGISTRAR PASE"):
                if monto_pase > 0 and origen_pase != destino_pase:
                    desc = concepto_pase if concepto_pase else f"Pase a {destino_pase}"
                    desc_dest = concepto_pase if concepto_pase else f"Pase desde {origen_pase}"
                    p1 = pd.DataFrame([[date.today(), "PASE EFECTIVO", origen_pase, forma_pase, desc,       "INTERNO", -monto_pase, "-"]], columns=COL_TESORERIA)
                    p2 = pd.DataFrame([[date.today(), "PASE EFECTIVO", destino_pase, forma_pase, desc_dest, "INTERNO",  monto_pase, "-"]], columns=COL_TESORERIA)
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, p1, p2], ignore_index=True)
                    guardar_datos("tesoreria", st.session_state.tesoreria)
                    st.session_state.msg_pase = f"✅ Pase de {forma_pase} por $ {monto_pase:,.2f} de {origen_pase} → {destino_pase} registrado."
                    st.rerun()
                elif origen_pase == destino_pase:
                    st.warning("La caja origen y destino no pueden ser la misma.")
                else:
                    st.warning("Ingresá un monto mayor a cero.")

    # Traspasos y Orden de Pago: SOLO ADMIN
    if tab_tras is not None:
        with tab_tras:
            if st.session_state.get("msg_traspaso"):
                st.success(st.session_state.msg_traspaso)
                st.session_state.msg_traspaso = None
            with st.form("f_tras", clear_on_submit=True):
                o = st.selectbox("Desde", opc_cajas)
                d = st.selectbox("Hacia", opc_cajas)
                m = st.number_input("Monto a Traspasar", min_value=0.0)
                if st.form_submit_button("EJECUTAR"):
                    if m > 0:
                        tr1 = pd.DataFrame([[date.today(), "TRASPASO", o, "INTERNO", f"Hacia {d}", "INTERNO", -m, "-"]], columns=COL_TESORERIA)
                        tr2 = pd.DataFrame([[date.today(), "TRASPASO", d, "INTERNO", f"Desde {o}", "INTERNO",  m, "-"]], columns=COL_TESORERIA)
                        st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, tr1, tr2], ignore_index=True)
                        guardar_datos("tesoreria", st.session_state.tesoreria)
                        st.session_state.msg_traspaso = f"✅ Traspaso de $ {m:,.2f} de {o} hacia {d} ejecutado."
                        st.rerun()
                    else:
                        st.warning("Ingresá un monto mayor a cero.")

    if tab_op is not None:
        with tab_op:
            st.subheader("Generar Orden de Pago a Proveedor")
            if "html_op_ready" not in st.session_state: st.session_state.html_op_ready = None
            with st.form("f_op", clear_on_submit=True):
                p_sel  = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
                cj_p   = st.selectbox("Caja de Salida", opc_cajas)
                mon_p  = st.number_input("Monto $", min_value=0.0)
                afip_p = st.text_input("Referencia AFIP / Pago")
                if st.form_submit_button("GENERAR ORDEN DE PAGO"):
                    if p_sel and mon_p > 0:
                        nt = pd.DataFrame([[date.today(), "PAGO PROV", cj_p, "TRANSFERENCIA", "Orden de Pago", p_sel, -mon_p, afip_p]], columns=COL_TESORERIA)
                        nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO", 0, 0, 0, 0, 0, 0, -mon_p]], columns=COL_COMPRAS)
                        st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                        st.session_state.compras   = pd.concat([st.session_state.compras, nc], ignore_index=True)
                        guardar_datos("tesoreria", st.session_state.tesoreria)
                        guardar_datos("compras", st.session_state.compras)
                        st.session_state.html_op_ready = generar_html_orden_pago({
                            "Fecha": date.today(), "Proveedor": p_sel,
                            "Concepto": "Pago Proveedor", "Caja/Banco": cj_p,
                            "Monto": mon_p, "Ref AFIP": afip_p
                        })
                        st.session_state.prov_ready = p_sel
                        st.rerun()
                    else:
                        st.warning("Seleccioná proveedor y completá el monto.")
            if st.session_state.html_op_ready:
                st.success(f"✅ Orden de Pago para '{st.session_state.prov_ready}' registrada con éxito.")
                st.download_button("🖨️ IMPRIMIR ORDEN DE PAGO", st.session_state.html_op_ready, file_name=f"OrdenPago_{st.session_state.prov_ready}.html", mime="text/html")
                if st.button("Limpiar OP"): st.session_state.html_op_ready = None; st.rerun()

elif sel == "CTA CTE INDIVIDUAL":
    st.header("📑 Cuenta Corriente por Cliente")
    if not st.session_state.clientes.empty:
        cl     = st.selectbox("Seleccionar Cliente", st.session_state.clientes['Razón Social'].unique())
        df_ind = st.session_state.viajes[st.session_state.viajes['Cliente'] == cl].copy()
        st.metric("SALDO TOTAL", f"$ {df_ind['Importe'].sum():,.2f}")
        html_reporte = generar_html_resumen(cl, df_ind, df_ind['Importe'].sum())
        st.download_button(label="📄 DESCARGAR RESUMEN", data=html_reporte, file_name=f"Resumen_{cl}.html", mime="text/html")
        st.dataframe(df_ind, use_container_width=True)

elif sel == "CTA CTE GENERAL":
    st.header("🌎 Estado Global de Deudores")
    if not st.session_state.viajes.empty:
        res = st.session_state.viajes.groupby('Cliente')['Importe'].sum().reset_index()
        res = res[res['Importe'].round(2) != 0]
        st.table(res.style.format({"Importe": "$ {:,.2f}"}))

elif sel == "CTA CTE PROVEEDOR":
    st.header("👤 Gestión de Proveedores")
    if st.session_state.get("msg_proveedor"):
        st.success(st.session_state.msg_proveedor)
        st.session_state.msg_proveedor = None
    with st.expander("➕ ALTA DE NUEVO PROVEEDOR", expanded=False):
        with st.form("f_prov", clear_on_submit=True):
            c1, c2  = st.columns(2)
            rs      = c1.text_input("Razón Social")
            doc     = c2.text_input("CUIT o DNI")
            cuenta  = c1.selectbox("Cuenta de Gastos", ["COMBUSTIBLE", "REPARACION", "REPUESTO", "SERVICIO LUZ, GAS", "VARIOS"])
            cat_iva = c2.selectbox("Categoría IVA", ["Responsable Inscripto", "Exento en IVA", "Consumidor Final", "Monotributista", "No Inscripto"])
            c3, c4  = st.columns(2)
            cbu     = c3.text_input("CBU")
            alias   = c4.text_input("Alias")
            if st.form_submit_button("REGISTRAR PROVEEDOR"):
                if rs and doc:
                    np_row = pd.DataFrame([[rs, doc, cuenta, cat_iva, cbu, alias]], columns=COL_PROVEEDORES)
                    st.session_state.proveedores = pd.concat([st.session_state.proveedores, np_row], ignore_index=True)
                    guardar_datos("proveedores", st.session_state.proveedores)
                    st.session_state.msg_proveedor = f"✅ Proveedor '{rs}' registrado correctamente."
                    st.rerun()
                else:
                    st.warning("Completá Razón Social y CUIT/DNI para continuar.")
    st.subheader("📋 Base de Proveedores")
    if not st.session_state.proveedores.empty:
        for i, row in st.session_state.proveedores.iterrows():
            with st.container():
                c_inf, c_ed, c_el = st.columns([0.7, 0.15, 0.15])
                c_inf.markdown(f"**{row['Razón Social']}** | CUIT: {row['CUIT/DNI']}")
                c_inf.caption(f"📂 Cuenta: {row['Cuenta de Gastos']} | {row['Categoría IVA']} | 🏦 CBU: {row['CBU']} | Alias: {row['Alias']}")
                if c_ed.button("📝 Editar", key=f"edit_p_{i}"): st.session_state[f"edit_p_mode_{i}"] = True
                if c_el.button("🗑️", key=f"del_p_{i}"):
                    tiene_compras = not st.session_state.compras[st.session_state.compras['Proveedor'] == row['Razón Social']].empty
                    if tiene_compras: st.error("No se puede eliminar: tiene comprobantes asociados.")
                    else:
                        st.session_state.proveedores = st.session_state.proveedores.drop(i).reset_index(drop=True)
                        guardar_datos("proveedores", st.session_state.proveedores)
                        st.rerun()
                if st.session_state.get(f"edit_p_mode_{i}", False):
                    with st.form(f"f_edit_p_{i}"):
                        ce1, ce2 = st.columns(2)
                        n_rs    = ce1.text_input("Razón Social", value=row['Razón Social'])
                        n_doc   = ce2.text_input("CUIT/DNI", value=row['CUIT/DNI'])
                        ce3, ce4 = st.columns(2)
                        n_cbu   = ce3.text_input("CBU", value=row['CBU'])
                        n_alias = ce4.text_input("Alias", value=row['Alias'])
                        if st.form_submit_button("✅ Guardar"):
                            st.session_state.proveedores.loc[i] = [n_rs, n_doc, row['Cuenta de Gastos'], row['Categoría IVA'], n_cbu, n_alias]
                            guardar_datos("proveedores", st.session_state.proveedores)
                            st.session_state[f"edit_p_mode_{i}"] = False; st.rerun()
            st.divider()

elif sel == "CARGA GASTOS":
    st.header("💸 Carga de Gastos")
    if st.session_state.get("msg_gasto"):
        st.success(st.session_state.msg_gasto)
        st.session_state.msg_gasto = None

    # ── Inputs fuera del form para que el total se actualice en tiempo real ──
    prov_sel = st.selectbox("Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
    c1, c2   = st.columns(2)
    pv       = c1.text_input("Punto de Venta")
    tipo_f   = c2.selectbox("Tipo de Factura", ["A", "B", "C", "REMITO", "NOTA DE CREDITO", "NOTA DE DEBITO"])
    c3, c4   = st.columns(2)
    n21      = c3.number_input("Importe Neto (21%)", min_value=0.0, step=0.01, key="g_n21")
    n10      = c4.number_input("Importe Neto (10.5%)", min_value=0.0, step=0.01, key="g_n10")
    c5, c6, c7 = st.columns(3)
    r_iva    = c5.number_input("Retención IVA", min_value=0.0, step=0.01, key="g_riva")
    r_gan    = c6.number_input("Retención Ganancia", min_value=0.0, step=0.01, key="g_rgan")
    r_iibb   = c7.number_input("Retención IIBB", min_value=0.0, step=0.01, key="g_riibb")
    nograv   = st.number_input("Conceptos No Gravados", min_value=0.0, step=0.01, key="g_nograv")

    # ── Total en tiempo real ──
    total = (n21 * 1.21) + (n10 * 1.105) + r_iva + r_gan + r_iibb + nograv
    if tipo_f == "NOTA DE CREDITO": total = -total

    color_total = "#2ecc71" if total >= 0 else "#e74c3c"
    signo = "-" if total < 0 else ""
    st.markdown(
        f"<div style='background:#f0f2f6;border-radius:10px;padding:16px 24px;margin:12px 0;"
        f"border-left:5px solid {color_total};display:flex;align-items:center;gap:16px;'>"
        f"<span style='font-size:14px;color:#555;font-weight:bold;'>TOTAL DEL COMPROBANTE</span>"
        f"<span style='font-size:28px;font-weight:bold;color:{color_total};'>{signo}$ {abs(total):,.2f}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    if st.button("✅ REGISTRAR COMPROBANTE", type="primary"):
        if total != 0:
            ng = pd.DataFrame([[date.today(), prov_sel, pv, tipo_f, n21, n10, r_iva, r_gan, r_iibb, nograv, total]], columns=COL_COMPRAS)
            st.session_state.compras = pd.concat([st.session_state.compras, ng], ignore_index=True)
            guardar_datos("compras", st.session_state.compras)
            st.session_state.msg_gasto = f"✅ Comprobante de '{prov_sel}' guardado por $ {total:,.2f}."
            st.rerun()
        else:
            st.warning("Ingresá al menos un importe para registrar el comprobante.")

elif sel == "COMPROBANTES":
    st.header("📜 Historial de Viajes")

    tab_ver_comp, tab_editar = st.tabs(["📋 VER Y ELIMINAR", "✏️ EDITAR VIAJE"])

    with tab_ver_comp:
        if not st.session_state.viajes.empty:
            for i in reversed(st.session_state.viajes.index):
                row = st.session_state.viajes.loc[i]
                c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
                c1.write(f"📅 {row['Fecha Viaje']}")
                c2.write(f"👤 **{row['Cliente']}** | {row['Origen']} a {row['Destino']} | **${row['Importe']}**")
                if c3.button("🗑️", key=f"del_{i}"):
                    st.session_state.viajes = st.session_state.viajes.drop(i)
                    guardar_datos("viajes", st.session_state.viajes); st.rerun()
                st.divider()
        else:
            st.info("No hay viajes registrados.")

    with tab_editar:
        if st.session_state.viajes.empty:
            st.info("No hay viajes para editar.")
        else:
            # Filtros para encontrar el viaje rápido
            col_f1, col_f2 = st.columns(2)
            clientes_unicos = ["(Todos)"] + sorted(st.session_state.viajes['Cliente'].unique().tolist())
            filtro_cli = col_f1.selectbox("Filtrar por cliente", clientes_unicos, key="edit_filtro_cli")
            filtro_txt = col_f2.text_input("Buscar por origen / destino", key="edit_filtro_txt").strip().lower()

            df_edit = st.session_state.viajes.copy()
            if filtro_cli != "(Todos)":
                df_edit = df_edit[df_edit['Cliente'] == filtro_cli]
            if filtro_txt:
                df_edit = df_edit[
                    df_edit['Origen'].str.lower().str.contains(filtro_txt, na=False) |
                    df_edit['Destino'].str.lower().str.contains(filtro_txt, na=False)
                ]

            if df_edit.empty:
                st.info("No se encontraron viajes con ese filtro.")
            else:
                st.markdown(f"**{len(df_edit)} viaje(s) encontrado(s)**")
                for i in reversed(df_edit.index):
                    row = st.session_state.viajes.loc[i]
                    with st.container():
                        # Encabezado del viaje
                        col_info, col_btn = st.columns([0.85, 0.15])
                        col_info.markdown(
                            f"📅 `{row['Fecha Viaje']}` — **{row['Cliente']}** | "
                            f"{row['Origen']} ➔ {row['Destino']} | **$ {row['Importe']:,.2f}**"
                        )
                        if col_btn.button("✏️ Editar", key=f"abrir_edit_{i}"):
                            st.session_state[f"modo_edit_viaje_{i}"] = not st.session_state.get(f"modo_edit_viaje_{i}", False)
                            st.rerun()

                        # Formulario de edición inline
                        if st.session_state.get(f"modo_edit_viaje_{i}", False):
                            with st.form(f"form_edit_viaje_{i}"):
                                st.markdown(f"##### ✏️ Editando viaje #{i}")
                                ec1, ec2 = st.columns(2)
                                # Parsear fecha correctamente
                                try:
                                    fecha_actual = pd.to_datetime(row['Fecha Viaje']).date()
                                except:
                                    fecha_actual = date.today()
                                n_fecha  = ec1.date_input("Fecha Viaje", value=fecha_actual)
                                n_cli    = ec2.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""], index=list(st.session_state.clientes['Razón Social'].unique()).index(row['Cliente']) if row['Cliente'] in st.session_state.clientes['Razón Social'].unique() else 0)
                                ec3, ec4 = st.columns(2)
                                n_orig   = ec3.text_input("Origen", value=str(row['Origen']))
                                n_dest   = ec4.text_input("Destino", value=str(row['Destino']))
                                ec5, ec6 = st.columns(2)
                                n_pat    = ec5.text_input("Patente / Móvil", value=str(row['Patente / Móvil']))
                                n_imp    = ec6.number_input("Importe $", value=float(row['Importe']), min_value=0.0, step=0.01)
                                n_tipo   = st.selectbox("Tipo Comprobante", ["Factura (Cuenta Corriente)", "Factura (Contado)", "RECIBO", "REMITO"], index=0)
                                sb1, sb2 = st.columns(2)
                                if sb1.form_submit_button("💾 GUARDAR CAMBIOS", type="primary"):
                                    st.session_state.viajes.loc[i, 'Fecha Viaje']    = str(n_fecha)
                                    st.session_state.viajes.loc[i, 'Cliente']        = n_cli
                                    st.session_state.viajes.loc[i, 'Origen']         = n_orig
                                    st.session_state.viajes.loc[i, 'Destino']        = n_dest
                                    st.session_state.viajes.loc[i, 'Patente / Móvil']= n_pat
                                    st.session_state.viajes.loc[i, 'Importe']        = n_imp
                                    st.session_state.viajes.loc[i, 'Tipo Comp']      = n_tipo
                                    guardar_datos("viajes", st.session_state.viajes)
                                    st.session_state[f"modo_edit_viaje_{i}"] = False
                                    st.session_state.msg_viaje = f"✅ Viaje #{i} actualizado correctamente."
                                    st.rerun()
                                if sb2.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"modo_edit_viaje_{i}"] = False
                                    st.rerun()
                    st.divider()
    st.header("📊 Cuenta Corriente Individual")
    if not st.session_state.proveedores.empty:
        p_sel = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique())
        df_p  = st.session_state.compras[st.session_state.compras['Proveedor'] == p_sel]
        st.metric("SALDO PENDIENTE", f"$ {df_p['Total'].sum():,.2f}")
        st.dataframe(df_p, use_container_width=True)

elif sel == "CTA CTE GENERAL PROV":
    st.header("🌎 Estado General de Proveedores")
    if not st.session_state.compras.empty:
        res_p = st.session_state.compras.groupby('Proveedor')['Total'].sum().reset_index()
        res_p = res_p.merge(
            st.session_state.proveedores[['Razón Social', 'CBU', 'Alias']],
            left_on='Proveedor', right_on='Razón Social', how='left'
        ).drop(columns='Razón Social')
        res_p = res_p[['Proveedor', 'CBU', 'Alias', 'Total']]
        st.dataframe(res_p.style.format({"Total": "$ {:,.2f}"}), use_container_width=True)

elif sel == "HISTORICO COMPRAS":
    st.header("📜 Comprobantes Cargados")
    if not st.session_state.compras.empty:
        for i in reversed(st.session_state.compras.index):
            row = st.session_state.compras.loc[i]
            c1, c2, c3 = st.columns([0.2, 0.6, 0.1])
            c1.write(f"📅 {row['Fecha']}")
            c2.write(f"👤 **{row['Proveedor']}** | {row['Tipo Factura']} {row['Punto Venta']} | **${row['Total']:,.2f}**")
            if c3.button("🗑️", key=f"del_comp_{i}"):
                st.session_state.compras = st.session_state.compras.drop(i)
                guardar_datos("compras", st.session_state.compras); st.rerun()
            st.divider()
