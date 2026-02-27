import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
# ... (mantenemos el resto de imports igual)

# --- 1. CONFIGURACIÓN Y CONEXIÓN (ACTUALIZADO) ---
# Se agrega la carga de la hoja de presupuestos
def cargar_datos():
    col_c = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
    col_v = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
    col_p = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
    
    try:
        sh = conectar_google()
        if sh is None: return None, None, None
        
        ws_c = sh.worksheet("clientes")
        df_c = pd.DataFrame(ws_c.get_all_records()) if ws_c.get_all_records() else pd.DataFrame(columns=col_c)
        
        ws_v = sh.worksheet("viajes")
        df_v = pd.DataFrame(ws_v.get_all_records()) if ws_v.get_all_records() else pd.DataFrame(columns=col_v)
        df_v['Importe'] = pd.to_numeric(df_v['Importe'], errors='coerce').fillna(0)

        # Carga de Presupuestos
        try:
            ws_p = sh.worksheet("presupuestos")
            df_p = pd.DataFrame(ws_p.get_all_records())
        except:
            df_p = pd.DataFrame(columns=col_p)
        
        return df_c, df_v, df_p
    except:
        return None, None, None

# --- FUNCIÓN ESPECÍFICA PARA IMPRIMIR PRESUPUESTO ---
def generar_html_presupuesto(p_data):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; }}
            .header {{ border-bottom: 3px solid #5e2d61; padding-bottom: 10px; margin-bottom: 20px; }}
            .logo-text {{ font-size: 28px; color: #5e2d61; font-weight: bold; }}
            .presu-titulo {{ background: #f39c12; color: white; padding: 10px; text-align: center; border-radius: 5px; }}
            .info-box {{ margin: 20px 0; line-height: 1.6; }}
            .detalle-box {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .detalle-box th {{ background: #eee; padding: 10px; border: 1px solid #ddd; }}
            .detalle-box td {{ padding: 15px; border: 1px solid #ddd; }}
            .monto {{ font-size: 24px; color: #5e2d61; text-align: right; margin-top: 30px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <span class="logo-text">🚛 CHACAGEST</span>
            <div style="float: right; text-align: right;">
                <p>Fecha: {p_data['Fecha Emisión']}<br>Vence: {p_data['Vencimiento']}</p>
            </div>
        </div>
        <div class="presu-titulo">PRESUPUESTO DE SERVICIO</div>
        <div class="info-box">
            <p><b>Señores:</b> {p_data['Cliente']}</p>
            <p><b>Unidad solicitada:</b> {p_data['Tipo Móvil']}</p>
        </div>
        <table class="detalle-box">
            <tr><th>Descripción del Servicio</th></tr>
            <tr><td>{p_data['Detalle']}</td></tr>
        </table>
        <div class="monto">TOTAL PRESUPUESTADO: $ {p_data['Importe']:,.2f}</div>
        <div style="margin-top: 50px; font-size: 12px; color: gray;">
            * Los precios están sujetos a cambios sin previo aviso según disponibilidad.
        </div>
    </body>
    </html>
    """
    return html

# --- (INICIALIZACIÓN DE SESSION STATE) ---
if 'presupuestos' not in st.session_state:
    c, v, p = cargar_datos()
    st.session_state.clientes = c
    st.session_state.viajes = v
    st.session_state.presupuestos = p

# --- SIDEBAR (ACTUALIZADO) ---
with st.sidebar:
    # ... (mismo estilo anterior)
    sel = option_menu(
        menu_title=None,
        options=["CALENDARIO", "CLIENTES", "CARGA VIAJE", "PRESUPUESTOS", "CTA CTE INDIVIDUAL", "CTA CTE GENERAL", "COMPROBANTES"],
        icons=["calendar3", "people", "truck", "file-earmark-spreadsheet", "person-vcard", "globe", "file-text"],
        default_index=0,
        styles={
            "container": {"background-color": "#f0f2f6"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#5e2d61"},
        }
    )

# --- MÓDULO NUEVO: PRESUPUESTOS ---
if sel == "PRESUPUESTOS":
    st.header("📝 Gestión de Presupuestos")
    
    tab1, tab2 = st.tabs(["🆕 Crear Presupuesto", "📂 Historial de Presupuestos"])
    
    with tab1:
        with st.form("f_presu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cli = c1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""])
            f_emi = c2.date_input("Fecha Emisión", date.today())
            
            c3, c4 = st.columns(2)
            f_venc = c3.date_input("Fecha Vencimiento", date.today() + timedelta(days=7))
            t_movil = c4.selectbox("Tipo de Móvil", ["Combi 19 asientos", "Minibus 24 asientos", "Micro 45 asientos", "Micro 60 asientos"])
            
            det = st.text_area("Detalle del Presupuesto (Ruta, horarios, paradas...)")
            imp = st.number_input("Importe Total $", min_value=0.0)
            
            if st.form_submit_button("GENERAR Y GUARDAR"):
                if cli and imp > 0:
                    np = pd.DataFrame([[str(f_emi), cli, str(f_venc), det, t_movil, imp]], columns=st.session_state.presupuestos.columns)
                    st.session_state.presupuestos = pd.concat([st.session_state.presupuestos, np], ignore_index=True)
                    guardar_datos("presupuestos", st.session_state.presupuestos)
                    st.success("Presupuesto guardado con éxito.")
                    st.rerun()

    with tab2:
        if not st.session_state.presupuestos.empty:
            for i in reversed(st.session_state.presupuestos.index):
                p = st.session_state.presupuestos.loc[i]
                with st.container():
                    col_a, col_b, col_c = st.columns([0.6, 0.2, 0.2])
                    col_a.markdown(f"**{p['Cliente']}** - {p['Tipo Móvil']}")
                    col_a.caption(f"Detalle: {p['Detalle'][:100]}...")
                    
                    col_b.write(f"**$ {p['Importe']:,.2f}**")
                    
                    # Generar PDF/HTML para este presupuesto específico
                    html_p = generar_html_presupuesto(p)
                    col_c.download_button(
                        label="🖨️ PDF",
                        data=html_p,
                        file_name=f"Presupuesto_{p['Cliente']}_{p['Fecha Emisión']}.html",
                        mime="text/html",
                        key=f"dl_{i}"
                    )
                    
                    if st.button("Eliminar", key=f"delp_{i}"):
                        st.session_state.presupuestos = st.session_state.presupuestos.drop(i)
                        guardar_datos("presupuestos", st.session_state.presupuestos)
                        st.rerun()
                    st.divider()
        else:
            st.info("No hay presupuestos cargados.")

# --- (EL RESTO DEL CÓDIGO SE MANTIENE IGUAL) ---
