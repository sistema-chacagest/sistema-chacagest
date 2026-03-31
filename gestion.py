import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
import uuid
import calendar

# ═══════════════════════════════════════════════════════════════
# CHACAGEST — Sistema de Gestión Total
# Interfaz idéntica a la versión web React
# Paleta: Rojo (#C8102E), Negro (#141414), Gris (#8C8C8C)
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="CHACAGEST", page_icon="🚌", layout="wide", initial_sidebar_state="expanded")

# ─── PALETA ───
RED = "#C8102E"
RED_LIGHT = "#F8D7DA"
RED_HOVER = "#A30D24"
BLACK = "#141414"
DARK = "#1A1A1A"
DARK2 = "#242424"
GRAY = "#8C8C8C"
LIGHT_GRAY = "#F5F5F5"
WHITE = "#FFFFFF"
CARD_BG = "#FFFFFF"
BORDER = "#E0E0E0"
SUCCESS = "#16A34A"
WARNING = "#EAB308"
DANGER = "#DC2626"

# ─── CSS GLOBAL ───
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Global */
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif;
    background-color: {LIGHT_GRAY};
    color: {BLACK};
}}
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: {BLACK} !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: {BLACK} !important;
    border-right: 1px solid {DARK2} !important;
}}
[data-testid="stSidebar"] * {{
    color: #EAEAEA !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background-color: {DARK2} !important;
}}
[data-testid="stSidebar"] .stRadio label[data-checked="true"],
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {{
    background-color: {RED} !important;
    color: white !important;
    font-weight: 600 !important;
}}

/* Cards */
[data-testid="stMetric"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
[data-testid="stMetricValue"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: {BLACK} !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 12px !important;
    color: {GRAY} !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}

/* Buttons */
.stButton > button {{
    background-color: {RED} !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.5px !important;
    padding: 10px 24px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 12px rgba(200,16,46,0.2) !important;
}}
.stButton > button:hover {{
    background-color: {RED_HOVER} !important;
    box-shadow: 0 6px 16px rgba(200,16,46,0.3) !important;
    transform: translateY(-1px) !important;
}}

/* Inputs */
.stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select,
[data-testid="stTextInput"] input, [data-baseweb="input"] input {{
    border-radius: 12px !important;
    border: 1px solid {BORDER} !important;
    background: {CARD_BG} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: {RED} !important;
    box-shadow: 0 0 0 2px rgba(200,16,46,0.15) !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
.stTabs [aria-selected="true"] {{
    background-color: {RED} !important;
    color: white !important;
}}

/* Expander */
.streamlit-expanderHeader {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: {BLACK} !important;
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
}}

/* Dataframe */
.stDataFrame {{
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}}

/* Custom scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {LIGHT_GRAY}; }}
::-webkit-scrollbar-thumb {{ background: {GRAY}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {RED}; }}

/* Hide Streamlit chrome */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}

/* Top gradient bar */
[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, {RED}, {RED}, {BLACK});
    z-index: 9999;
}}
</style>
""", unsafe_allow_html=True)

# ─── PERSISTENCE ───
DATA_FILE = "chacagest_data.json"

def load_data():
    default = {"clientes": [], "viajes": [], "presupuestos": [], "tesoreria": [],
               "proveedores": [], "compras": [], "cheques_emitidos": [], "cheques_cartera": [], "facturas": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return default

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

if "data" not in st.session_state:
    st.session_state.data = load_data()

def get_data():
    return st.session_state.data

def persist():
    save_data(st.session_state.data)

# ─── AUTH ───
USUARIOS = {
    "admin": {"password": "chaca2026", "rol": "admin", "caja": None, "nombre": "Administrador"},
    "coti":  {"password": "coti2026",  "rol": "operador", "caja": "CAJA COTI",  "nombre": "Coti"},
    "tato":  {"password": "tato2026",  "rol": "operador", "caja": "CAJA TATO",  "nombre": "Tato"},
    "mel":   {"password": "congo2026", "rol": "operador", "caja": "CAJA JUNIN", "nombre": "Mel"},
}

def login_page():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background:{BLACK}; height:100vh; display:flex; align-items:center; justify-content:center;
                     margin:-6rem -1rem -6rem -1rem; padding:3rem; position:relative; overflow:hidden;">
            <div style="position:absolute;inset:0;background:linear-gradient(135deg,{BLACK},{BLACK},rgba(200,16,46,0.1));"></div>
            <div style="position:absolute;top:-100px;right:-80px;width:400px;height:400px;border-radius:50%;background:rgba(200,16,46,0.04);"></div>
            <div style="position:absolute;bottom:-120px;left:-80px;width:350px;height:350px;border-radius:50%;background:rgba(200,16,46,0.04);"></div>
            <div style="position:relative;z-index:1;text-align:center;">
                <div style="width:120px;height:120px;margin:0 auto 2rem;background:rgba(255,255,255,0.06);
                            backdrop-filter:blur(8px);border-radius:24px;display:flex;align-items:center;
                            justify-content:center;border:1px solid rgba(255,255,255,0.08);
                            box-shadow:0 20px 40px rgba(0,0,0,0.3);">
                    <span style="font-size:56px;">🚌</span>
                </div>
                <h1 style="color:white;font-family:'Space Grotesk',sans-serif;font-size:2.5rem;
                           font-weight:700;letter-spacing:-0.5px;margin:0;">CHACAGEST</h1>
                <div style="width:60px;height:4px;background:{RED};margin:1rem auto;border-radius:2px;"></div>
                <p style="color:rgba(255,255,255,0.5);font-size:14px;margin:0;">Sistema de Gestión Total</p>
                <p style="color:rgba(255,255,255,0.3);font-size:11px;margin-top:3rem;">
                    Chacabuco Noroeste Tour S.R.L.<br>Desde 1996 viajando con vos</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='height:30vh'></div>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='font-family:Space Grotesk,sans-serif;font-weight:700;color:{BLACK};font-size:1.6rem;'>Iniciar Sesión</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{GRAY};font-size:13px;margin-top:-10px;'>Ingresá tus credenciales para continuar</p>", unsafe_allow_html=True)
        
        st.markdown(f"<label style='font-size:11px;font-weight:600;color:{GRAY};text-transform:uppercase;letter-spacing:1px;'>Usuario</label>", unsafe_allow_html=True)
        username = st.text_input("", key="login_user", placeholder="Ingrese su usuario", label_visibility="collapsed")
        
        st.markdown(f"<label style='font-size:11px;font-weight:600;color:{GRAY};text-transform:uppercase;letter-spacing:1px;'>Contraseña</label>", unsafe_allow_html=True)
        password = st.text_input("", type="password", key="login_pass", placeholder="Ingrese su contraseña", label_visibility="collapsed")
        
        if st.button("INGRESAR", use_container_width=True):
            u = username.strip().lower()
            if u in USUARIOS and USUARIOS[u]["password"] == password.strip():
                st.session_state.user = USUARIOS[u]
                st.session_state.user["username"] = u
                st.rerun()
            else:
                st.error("⚠ Usuario o contraseña incorrectos")
        
        st.markdown(f"<p style='text-align:center;color:{GRAY};font-size:11px;margin-top:3rem;'>© {datetime.now().year} Chacabuco Noroeste Tour S.R.L.</p>", unsafe_allow_html=True)

# ─── SIDEBAR ───
def render_sidebar():
    user = st.session_state.user
    is_admin = user["rol"] == "admin"
    
    st.sidebar.markdown(f"""
    <div style="padding:12px 8px 12px 8px;border-bottom:1px solid {DARK2};margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:40px;height:40px;background:{CARD_BG};border-radius:10px;
                        display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                <span style="font-size:22px;">🚌</span>
            </div>
            <div>
                <p style="margin:0;font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:13px;color:white;">CHACAGEST</p>
                <p style="margin:0;font-size:10px;color:{GRAY};">Gestión Total</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # User badge
    badge_text = f"🔑 Admin" if is_admin else f"👤 {user['nombre']}"
    extra = "" if is_admin else (f" | {user['caja']}" if user.get('caja') else "")
    st.sidebar.markdown(f"""
    <div style="background:{DARK2};border-radius:10px;padding:8px 12px;margin:0 4px 16px 4px;">
        <span style="color:{RED};font-weight:700;font-size:12px;">{badge_text}</span>
        <span style="color:{GRAY};font-size:11px;">{extra}</span>
    </div>
    """, unsafe_allow_html=True)

    # Menu
    menu_items = ["📅 Calendario"]
    if is_admin:
        menu_items.append("📊 Dashboard")
    menu_items += [
        "🛒 Ventas › Clientes",
        "🛒 Ventas › Carga Viaje",
        "🛒 Ventas › Presupuestos",
        "🛒 Ventas › Cta Cte Individual",
        "🛒 Ventas › Cta Cte General",
        "🛒 Ventas › Comprobantes",
        "🛍️ Compras › Carga Proveedor",
        "🛍️ Compras › Carga Gastos",
        "🛍️ Compras › Cta Cte Proveedor",
        "🛍️ Compras › Cta Cte General",
        "🛍️ Compras › Histórico",
        "🛍️ Compras › Mayor de Cuentas",
        "🧾 Facturación",
        "🏦 Tesorería",
        "🏛️ Cheques",
    ]

    default_idx = 1 if is_admin else 0
    choice = st.sidebar.radio("Menú", menu_items, index=default_idx, label_visibility="collapsed")

    st.sidebar.markdown(f"<div style='border-top:1px solid {DARK2};margin-top:1rem;padding-top:0.8rem;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        del st.session_state.user
        st.rerun()

    return choice

# ─── MODULES ───

def mod_dashboard():
    st.markdown(f"<h1 style='font-size:1.6rem;'>Dashboard de Control Financiero</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{GRAY};font-size:13px;margin-top:-12px;'>Resumen del período actual</p>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Ingresos", "$5.740.000", "+12%")
    c2.metric("Total Gastos", "$2.960.000", "-3%")
    c3.metric("Resultado Neto", "$2.780.000", "+18%")
    c4.metric("Margen", "48.4%", "+2.1%")

    col1, col2 = st.columns(2)
    with col1:
        months = ["Ene","Feb","Mar","Abr","May","Jun"]
        ingresos = [850000,920000,780000,1050000,1180000,960000]
        gastos = [420000,510000,380000,620000,550000,480000]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ingresos", x=months, y=ingresos, marker_color=RED, marker_cornerradius=4))
        fig.add_trace(go.Bar(name="Gastos", x=months, y=gastos, marker_color=DARK2, marker_cornerradius=4))
        fig.update_layout(title="Ingresos vs Gastos", title_font=dict(family="Space Grotesk", size=14),
                          barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                          font=dict(family="Inter", size=12), height=320,
                          margin=dict(t=40,b=30,l=50,r=20),
                          legend=dict(orientation="h", y=-0.15))
        fig.update_yaxes(gridcolor="#F0F0F0", tickprefix="$", tickformat=",.")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cats = ["Combustible","Reparaciones","Alquileres","Honorarios","Varios"]
        vals = [320000,180000,150000,120000,90000]
        colors = [RED, DARK2, GRAY, WARNING, "#BFBFBF"]
        fig2 = px.pie(names=cats, values=vals, hole=0.55, color_discrete_sequence=colors)
        fig2.update_layout(title="Gastos por Categoría", title_font=dict(family="Space Grotesk", size=14),
                           plot_bgcolor="white", paper_bgcolor="white",
                           font=dict(family="Inter", size=12), height=320,
                           margin=dict(t=40,b=30,l=20,r=20),
                           legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig2, use_container_width=True)


def mod_clientes():
    data = get_data()
    st.markdown("<h1 style='font-size:1.6rem;'>Gestión de Clientes</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{GRAY};font-size:13px;margin-top:-12px;'>{len(data['clientes'])} clientes registrados</p>", unsafe_allow_html=True)

    with st.expander("➕ Nuevo Cliente", expanded=False):
        c1, c2 = st.columns(2)
        razon = c1.text_input("Razón Social *", key="cli_razon")
        cuit = c2.text_input("CUIT *", key="cli_cuit")
        c3, c4 = st.columns(2)
        email = c3.text_input("Email", key="cli_email")
        tel = c4.text_input("Teléfono", key="cli_tel")
        c5, c6 = st.columns(2)
        direc = c5.text_input("Dirección Fiscal", key="cli_dir")
        loc = c6.text_input("Localidad", key="cli_loc")
        c7, c8 = st.columns(2)
        prov = c7.text_input("Provincia", key="cli_prov")
        iva = c8.selectbox("Condición IVA", ["Responsable Inscripto","Monotributo","Exento","Consumidor Final"], key="cli_iva")
        cond_venta = st.selectbox("Condición de Venta", ["Cuenta Corriente","Contado"], key="cli_venta")
        if st.button("GUARDAR CLIENTE", key="cli_save"):
            if razon and cuit:
                data["clientes"].append({"id": str(uuid.uuid4()), "razonSocial": razon, "cuit": cuit,
                    "email": email, "telefono": tel, "direccionFiscal": direc, "localidad": loc,
                    "provincia": prov, "condicionIVA": iva, "condicionVenta": cond_venta})
                persist()
                st.success(f"Cliente '{razon}' registrado")
                st.rerun()
            else:
                st.error("Completá Razón Social y CUIT")

    search = st.text_input("🔍 Buscar por nombre o CUIT...", key="cli_search")
    filtered = [c for c in data["clientes"] if search.lower() in c["razonSocial"].lower() or search in c.get("cuit","")]
    
    for c in filtered:
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{c['razonSocial']}**")
                st.markdown(f"<span style='font-size:12px;color:{GRAY};'>CUIT: {c['cuit']} | {c.get('localidad','')} - {c.get('provincia','')} | {c.get('telefono','')}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:12px;color:{GRAY};'>{c.get('condicionIVA','')} | {c.get('condicionVenta','')}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_cli_{c['id']}"):
                    has_viajes = any(v["cliente"] == c["razonSocial"] for v in data["viajes"])
                    if has_viajes:
                        st.error("No se puede eliminar: tiene viajes asociados")
                    else:
                        data["clientes"] = [x for x in data["clientes"] if x["id"] != c["id"]]
                        persist()
                        st.rerun()
            st.divider()
    
    if not filtered:
        st.markdown(f"<p style='text-align:center;color:{GRAY};padding:2rem;'>No hay clientes registrados.</p>", unsafe_allow_html=True)


def mod_carga_viaje():
    data = get_data()
    st.markdown("<h1 style='font-size:1.6rem;'>Registro de Viaje</h1>", unsafe_allow_html=True)
    
    clientes_nombres = [c["razonSocial"] for c in data["clientes"]]
    cliente = st.selectbox("Seleccionar Cliente", [""] + clientes_nombres, key="vj_cli")
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", value=date.today(), key="vj_fecha")
    patente = c2.text_input("Patente", placeholder="ABC 123", key="vj_pat")
    origen = st.text_input("Origen", key="vj_orig")
    destino = st.text_input("Destino", key="vj_dest")
    importe = st.number_input("Importe Neto $", min_value=0.0, step=1000.0, key="vj_imp")
    tipo_pago = st.selectbox("Tipo de Pago", ["Cuenta Corriente","Contado"], key="vj_pago")
    
    if st.button("GUARDAR VIAJE", use_container_width=True, key="vj_save"):
        if cliente and importe > 0:
            data["viajes"].append({"id": str(uuid.uuid4()), "fechaCarga": str(date.today()),
                "cliente": cliente, "fechaViaje": str(fecha), "origen": origen, "destino": destino,
                "patente": patente, "importe": importe, "tipoComp": f"Factura ({tipo_pago})", "nroCompAsoc": "-"})
            persist()
            st.success(f"Viaje de '{cliente}' registrado por ${importe:,.0f}")
            st.rerun()
        else:
            st.error("Seleccioná cliente y completá el importe")


def mod_presupuestos():
    data = get_data()
    st.markdown("<h1 style='font-size:1.6rem;'>Gestión de Presupuestos</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Crear", "Historial"])
    
    with tab1:
        clientes_nombres = [c["razonSocial"] for c in data["clientes"]]
        c1, c2 = st.columns(2)
        cliente = c1.selectbox("Cliente", [""] + clientes_nombres, key="pres_cli")
        fecha_em = c2.date_input("Fecha Emisión", value=date.today(), key="pres_fecha")
        c3, c4 = st.columns(2)
        venc = c3.date_input("Vencimiento", value=date.today() + timedelta(days=15), key="pres_venc")
        movil = c4.selectbox("Tipo Móvil", ["Combi 19 asientos","Minibus 24 asientos","Micro 45 asientos","Micro 60 asientos","Remis"], key="pres_mov")
        detalle = st.text_area("Detalle del presupuesto...", key="pres_det")
        importe = st.number_input("Importe Total $", min_value=0.0, step=1000.0, key="pres_imp")
        if st.button("GENERAR PRESUPUESTO", use_container_width=True, key="pres_save"):
            if cliente and importe > 0:
                data["presupuestos"].append({"id": str(uuid.uuid4()), "fechaEmision": str(fecha_em),
                    "cliente": cliente, "vencimiento": str(venc), "detalle": detalle,
                    "tipoMovil": movil, "importe": importe})
                persist()
                st.success(f"Presupuesto para '{cliente}' guardado")
                st.rerun()
            else:
                st.error("Seleccioná cliente y completá el importe")
    
    with tab2:
        for p in reversed(data["presupuestos"]):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{p['cliente']}** — {p['tipoMovil']}")
                st.markdown(f"<span style='font-size:12px;color:{GRAY};'>Emisión: {p['fechaEmision']} | Vence: {p['vencimiento']}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:700;color:{RED};'>$ {p['importe']:,.0f}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_pres_{p['id']}"):
                    data["presupuestos"] = [x for x in data["presupuestos"] if x["id"] != p["id"]]
                    persist()
                    st.rerun()
            st.divider()
        if not data["presupuestos"]:
            st.markdown(f"<p style='text-align:center;color:{GRAY};padding:2rem;'>No hay presupuestos.</p>", unsafe_allow_html=True)


def mod_placeholder(title, description):
    st.markdown(f"""
    <div style="text-align:center;padding:5rem 2rem;">
        <div style="width:64px;height:64px;border-radius:16px;background:rgba(200,16,46,0.08);
                    display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;">
            <span style="font-size:32px;">🚧</span>
        </div>
        <h2 style="font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;color:{BLACK};">{title}</h2>
        <p style="font-size:13px;color:{GRAY};max-width:400px;margin:0.5rem auto;">{description}</p>
        <div style="display:inline-block;margin-top:1.5rem;padding:6px 16px;background:{LIGHT_GRAY};
                    border-radius:20px;font-size:12px;color:{GRAY};font-weight:500;">
            Módulo en desarrollo
        </div>
    </div>
    """, unsafe_allow_html=True)

MODULE_INFO = {
    "📅 Calendario": ("Calendario", "Visualizá y organizá tus viajes y eventos en un calendario interactivo."),
    "🛒 Ventas › Cta Cte Individual": ("Cuenta Corriente Individual", "Consultá el estado de cuenta de cada cliente."),
    "🛒 Ventas › Cta Cte General": ("Cuenta Corriente General", "Vista general de saldos de todos los clientes."),
    "🛒 Ventas › Comprobantes": ("Comprobantes", "Generá recibos, órdenes de pago y otros comprobantes."),
    "🛍️ Compras › Carga Proveedor": ("Carga Proveedor", "Registrá nuevos proveedores con sus datos fiscales."),
    "🛍️ Compras › Carga Gastos": ("Carga de Gastos", "Registrá gastos y facturas de proveedores."),
    "🛍️ Compras › Cta Cte Proveedor": ("Cta Cte Proveedor", "Consultá el estado de cuenta de cada proveedor."),
    "🛍️ Compras › Cta Cte General": ("Cta Cte General Proveedores", "Vista general de saldos con proveedores."),
    "🛍️ Compras › Histórico": ("Histórico de Compras", "Consultá el historial completo de compras."),
    "🛍️ Compras › Mayor de Cuentas": ("Mayor de Cuentas", "Análisis de gastos por cuenta contable."),
    "🧾 Facturación": ("Facturación", "Emití facturas, notas de crédito y notas de débito."),
    "🏦 Tesorería": ("Tesorería", "Gestioná ingresos, egresos, cierres de caja y rendiciones."),
    "🏛️ Cheques": ("Cheques", "Controlá cheques emitidos y de cartera de terceros."),
}

# ─── MAIN ───
def main():
    if "user" not in st.session_state:
        login_page()
        return

    choice = render_sidebar()

    if choice == "📊 Dashboard":
        mod_dashboard()
    elif choice == "🛒 Ventas › Clientes":
        mod_clientes()
    elif choice == "🛒 Ventas › Carga Viaje":
        mod_carga_viaje()
    elif choice == "🛒 Ventas › Presupuestos":
        mod_presupuestos()
    elif choice in MODULE_INFO:
        title, desc = MODULE_INFO[choice]
        mod_placeholder(title, desc)
    else:
        mod_placeholder(choice, "Este módulo estará disponible próximamente.")

if __name__ == "__main__":
    main()
