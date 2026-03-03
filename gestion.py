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


LOGO_B64 = "data:image/jpeg;base64,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"
COL_CLIENTES         = ["Razón Social", "CUIT / CUIL / DNI *", "Email", "Teléfono", "Dirección Fiscal", "Localidad", "Provincia", "Condición IVA", "Condición de Venta"]
COL_VIAJES           = ["Fecha Carga", "Cliente", "Fecha Viaje", "Origen", "Destino", "Patente / Móvil", "Importe", "Tipo Comp", "Nro Comp Asoc"]
COL_PRESUPUESTOS     = ["Fecha Emisión", "Cliente", "Vencimiento", "Detalle", "Tipo Móvil", "Importe"]
COL_TESORERIA        = ["Fecha", "Tipo", "Caja/Banco", "Forma", "Concepto", "Cliente/Proveedor", "Monto", "Ref AFIP"]
COL_PROVEEDORES      = ["Razón Social", "CUIT/DNI", "Cuenta de Gastos", "Categoría IVA", "CBU", "Alias"]
COL_COMPRAS          = ["Fecha", "Proveedor", "Punto Venta", "Tipo Factura", "Neto 21", "Neto 10.5", "Ret IVA", "Ret Ganancia", "Ret IIBB", "No Gravados", "Total"]
# Cheques emitidos por la empresa (pagos con cheque propio)
COL_CHEQ_EMITIDOS    = ["Fecha Emisión", "Nro Cheque", "Tipo", "Banco", "Beneficiario", "Importe", "Fecha Vencimiento", "Estado", "Fecha Conciliación", "Observaciones"]
# Cheques de terceros recibidos en cobranzas (cartera)
COL_CHEQ_CARTERA     = ["Fecha Recepción", "Nro Cheque", "Tipo", "Banco Librador", "Librador", "Importe", "Fecha Vencimiento", "Estado", "Destino", "Fecha Aplicación", "Observaciones"]

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

        try:
            ws_ce    = sh.worksheet("cheques_emitidos")
            datos_ce = ws_ce.get_all_records()
            df_ce    = pd.DataFrame(datos_ce) if datos_ce else pd.DataFrame(columns=COL_CHEQ_EMITIDOS)
            df_ce['Importe'] = pd.to_numeric(df_ce['Importe'], errors='coerce').fillna(0)
        except:
            df_ce = pd.DataFrame(columns=COL_CHEQ_EMITIDOS)

        try:
            ws_cc    = sh.worksheet("cheques_cartera")
            datos_cc = ws_cc.get_all_records()
            df_cc    = pd.DataFrame(datos_cc) if datos_cc else pd.DataFrame(columns=COL_CHEQ_CARTERA)
            df_cc['Importe'] = pd.to_numeric(df_cc['Importe'], errors='coerce').fillna(0)
        except:
            df_cc = pd.DataFrame(columns=COL_CHEQ_CARTERA)

        return df_c, df_v, df_p, df_t, df_prov, df_com, df_ce, df_cc
    except:
        return None, None, None, None, None, None, None, None

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
                <td style="vertical-align:middle;">
                    <img src="{LOGO_B64}" style="height:60px; margin-right:15px; vertical-align:middle;">
                    <span style="vertical-align:middle;">
                        <p class="empresa-name">CHACABUCO NOROESTE TOUR S.R.L.</p>
                        <p class="sub-title">Desde 1996 viajando con vos | CHACAGEST Software System</p>
                    </span>
                </td>
                <td style="text-align: right; vertical-align:middle;">
                    <p><b>ESTADO DE CUENTA</b><br>Emisión: {{date.today()}}</p>
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
                <div style="display:flex;align-items:center;gap:12px;">
                    <img src="data:image/jpeg;base64,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" style="height:65px;vertical-align:middle;margin-right:12px;">
                    <div>
                        <b style="font-size: 20px;">CHACABUCO NOROESTE TOUR S.R.L.</b><br>
                        <span>CUIT 30-71114824-4 - C.P. 6740 - Chacabuco, Bs. As.</span>
                    </div>
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
            <div class="header-op" style="display:flex;align-items:center;gap:14px;">
                <img src="data:image/jpeg;base64,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" style="height:65px;vertical-align:middle;margin-right:12px;">
                <div>
                    <h2 style="margin:0; color: #d35400;">CHACABUCO NOROESTE TOUR S.R.L.</h2>
                    <small>Desde 1996, viajando con vos | CHACAGEST Software System</small>
                </div>
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
                <div style="display:flex;align-items:center;gap:14px;">
                    <img src="data:image/jpeg;base64,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" style="height:65px;vertical-align:middle;margin-right:12px;">
                    <div>
                        <h1 style="margin:0; color:#444;">CHACABUCO NOROESTE TOUR S.R.L.</h1>
                        <small>VIAJES ESPECIALES - TURISMO - TRASLADOS PERSONALES</small>
                    </div>
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

def generar_html_cierre_caja(data):
    # Construir tabla de movimientos del día
    df = data['movimientos']
    filas_html = ""
    for _, row in df.iterrows():
        color_fila = "#fff" if row['Monto'] >= 0 else "#fff8f8"
        signo = "+" if row['Monto'] >= 0 else ""
        filas_html += f"""
        <tr style="background:{color_fila};">
            <td>{row['Fecha']}</td>
            <td>{row['Tipo']}</td>
            <td>{row.get('Forma','-')}</td>
            <td>{row['Concepto']}</td>
            <td>{row['Cliente/Proveedor']}</td>
            <td style="text-align:right;font-weight:bold;color:{'#27ae60' if row['Monto']>=0 else '#e74c3c'};">{signo}$ {row['Monto']:,.2f}</td>
        </tr>"""

    # Subtotales por forma
    FORMAS = ["EFECTIVO", "TRANSFERENCIA", "TARJETA DE CREDITO", "DÓLARES", "OTROS"]
    ICONOS = {"EFECTIVO":"💵","TRANSFERENCIA":"🏦","TARJETA DE CREDITO":"💳","DÓLARES":"💲","OTROS":"📋"}
    subtotales_html = ""
    for f in FORMAS:
        mask = df['Forma'].fillna('-').str.upper().str.contains(f.replace("DÓLARES","DOLAR").replace("TARJETA DE CREDITO","TARJETA"), na=False)
        sub = df[mask]['Monto'].sum()
        if sub != 0:
            color_s = "#27ae60" if sub >= 0 else "#e74c3c"
            signo_s = "+" if sub >= 0 else ""
            subtotales_html += f"""
            <tr>
                <td style="padding:8px 12px;">{ICONOS.get(f,'💰')} {f}</td>
                <td style="text-align:right;padding:8px 12px;font-weight:bold;color:{color_s};">{signo_s}$ {sub:,.2f}</td>
            </tr>"""

    total = data['total']
    color_total = "#27ae60" if total >= 0 else "#e74c3c"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        @media print {{ .no-print {{ display: none; }} body {{ margin: 0; }} }}
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; padding: 30px; background: #fff; }}
        .header-cierre {{ display: flex; justify-content: space-between; align-items: flex-start;
                          border-bottom: 4px solid #5e2d61; padding-bottom: 20px; margin-bottom: 25px; }}
        .empresa-nombre {{ font-size: 22px; font-weight: bold; color: #5e2d61; margin: 0; }}
        .empresa-sub {{ font-size: 12px; color: #888; margin-top: 4px; }}
        .badge-cierre {{ background: #5e2d61; color: white; padding: 8px 20px; border-radius: 6px;
                         font-size: 16px; font-weight: bold; text-align: center; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 25px; }}
        .info-box {{ background: #f8f9fa; border-radius: 8px; padding: 14px; border-left: 4px solid #f39c12; }}
        .info-label {{ font-size: 11px; color: #888; font-weight: bold; text-transform: uppercase; }}
        .info-value {{ font-size: 16px; font-weight: bold; color: #333; margin-top: 4px; }}
        table.mov {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 25px; }}
        table.mov th {{ background: #5e2d61; color: white; padding: 9px 10px; text-align: left; }}
        table.mov td {{ padding: 7px 10px; border-bottom: 1px solid #eee; }}
        .subtotales-tabla {{ width: 100%; border-collapse: collapse; max-width: 380px; margin-left: auto; }}
        .subtotales-tabla td {{ border: 1px solid #ddd; }}
        .subtotales-header {{ background: #f0f2f6; font-weight: bold; font-size: 13px; padding: 10px 12px; text-transform: uppercase; letter-spacing: 1px; }}
        .total-box {{ background: {color_total}; color: white; padding: 16px 24px; border-radius: 10px;
                      text-align: right; margin-top: 20px; }}
        .total-label {{ font-size: 13px; opacity: 0.9; }}
        .total-monto {{ font-size: 32px; font-weight: bold; display: block; margin-top: 4px; }}
        .firmas {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 60px; }}
        .firma-box {{ border-top: 2px solid #333; padding-top: 10px; text-align: center; font-size: 12px; color: #555; }}
        .footer-cierre {{ margin-top: 40px; text-align: center; font-size: 10px; color: #bbb;
                           border-top: 1px solid #eee; padding-top: 12px; }}
        .btn-imprimir {{ background: #5e2d61; color: white; border: none; padding: 12px 28px;
                          font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer;
                          display: block; margin: 0 auto 24px auto; }}
        .btn-imprimir:hover {{ background: #4a2350; }}
    </style>
</head>
<body>
    <button class="btn-imprimir no-print" onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>

    <div class="header-cierre">
        <div style="display:flex;align-items:center;gap:14px;">
            <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISERUQEBMVEhUWEhUVEBYREhAXFRUXGBIWFxUVFRUYHSggGBslHxUVITEiJSkrLi4wGB8zODMsOCgtLisBCgoKDQ0NGQ8PFzcZFx8rKy0rMis3Ky0rLTcrNys3LTcrLSstLSstMC0tMDIrNystNy03LTY3Ny8rLSs3LTcrK//AABEIALcBEwMBIgACEQEDEQH/xAAcAAEAAgIDAQAAAAAAAAAAAAAABgcBBQMECAL/xABHEAACAQICBQcHCQUHBQAAAAAAAQIDEQQhBQYxQWEHEhMiUXGBMkJTVJHR0hQVFiNSk5ShwReSorHhM0NicnOC8EVjhKOz/8QAGgEBAQADAQEAAAAAAAAAAAAAAAECAwYEBf/EACQRAQACAgEDAwUAAAAAAAAAAAABAgMRBBIxUQUhIhMjQmFx/9oADAMBAAIRAxEAPwC8QAAAAAAAAAAAAAAAAAAAAAAAAcGLxcKUJVaslCEIuU5S2JJXbIsuU/RPra+6r/ABMCOaz6UcbUabae2bTat2RvxNbiuVHRag3DEqUrdVKnXze7zSHVddMFKTlKum27t8yr8IEi+WVfS1PvJ+8fLKvpKn3k/eR6GtmCbSVdXbslzal29iSXN25oli0FXtfmZWvnKCy9pYR1PllX0lT7yfvHy2r6Sp95P3nC0fVGk5yUYq7bshI3Or9OrVqXlUqOEc5deeb3LaS86mjsEqVNQj/ufa97O2RQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAjmvms8dH4Sdd2dR9TDxfnVGnbLsWbfBAVxy3623a0ZQnkmpYtx35XhSfDZJr/AClRHJXrynOVSpJynKTlOT2uTd233s4woAbLV3QtTG4mnhaPlTl1pboRWcpvglfv2ATvkW1S+UV3jq0fqqLtRT2Tq73xjFfm+BbWs2keZHoovrS8q26PZ4nawmFo4HCxpU1zYUoKMFvk7b+1t5kOxNeU5Octrbb/AEQRxko1W0bZdPJZvKF+ze/E0uh8A61RR81Zza7OzvZO4RSVlklsRZkZRkAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbA+Kskk23ZJNtvYkt7PM3KRrW9I4tzg/qad4YdXyaum6lu2TS8Eix+W3W5UqXzdRf1lWN67XmUnfq98rPwXEo0AAAoegeR7VJ4TDPE1l9fXSdms6dPbGHe/KfeuwrHkt1dp4rFqriGlQotSkpf3k79SHdezfcu0vbTOmYKnzaUlKUsuq/JW9hGq1j0j0s+ZHyIP2y3s1EYtuyzb2foYJFqvo676aSyV1BPe97A3OhcAqNNR855zfHs8DYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGajWnT1PA4WpiquyK6sd85vKEFxba8Lm2Z535XdbvlmKeHpSvQoNxVtlSp58+5eSvF70BDNK6RqYmtUxFZ86dSTlJ3duCXBKyXBHUAChzYPCyq1I0qavKclGPf/Tb4HCWNyc6C5kPldRdaatRvug9sv938gJPoTRkcNQjRhuXWe+UnnKV/y8DvgykZaR2dG4N1aigu+T7F2k9oUVCKhHJJJIjeDx2EwNPnYqvRoynm+kqQi+EUm7vwOhjOVbRUNleVX/SpVH+bSTMRNwVrV5aNHryadeXfCMfybON8teC9DX9kPeBZwKvfLZg/QV//AF+8x+2zB+r1/wCD3gWiCrHy3YT1av7afvMftvwvq1f20veBagKpfLhhvVa/71L3mHy44b1Sv+/R94Frgqd8uOH9Ur/v0fefP7csP6nW8alH3gW0DQ6E03XxNCniI4V01Ujzoxq1YqaV3ZtJO11n4gDfAAAAAAAAAAAAAAAAAxc1Gs+sNHA4eWIrvJZQj505box4gRblf1teCwvQUZWr104xtthT8+pbt81cXfceeTY6w6bq43ETxVd9abyS2Qir82EeCXtua4AAZpwcmoxTk27RS2tvYkFbnVLQrxVdQf8AZw61V8L2UfFlwxikrLJJWXYkv6Gk0Ho+ngML9ZJRdudWl/its422L+pBtZ9b6mIbp0r06Ozb1p8Zdi4FRLdO67UKF4UvrprLqvqJ8Ze4g+k9bcXW21Ojj9mkuavb5X5mjsBs0zNttybbb8pttt97ebMAEUAAAwZAAAAAAAJfyY6qPH4tc9PoKLU67z62+FK/a9/YvAiuDws6tSFKlHnTnJRgu1t5LgeodRdWoaPwkMNHrS8qtO1nOpLOT7lsS7EgjexjZWSVlkrZWW5GDlAAAxJgZBpsdrXgKNSVKvi8PSqRtzoVK9KMldJq8W7rJp+JwfTjRnr+E/E0fiAkAI/9ONGev4T8TR+IfTjRnr+E/E0fiAkAI/8ATjRnr+E/E0fiH040Z6/hPxNH4gJACP8A040Z6/hPxNH4jq4nlG0VTV3jaUrei59T/wCaYEqMc4rXSXLRgIJ9BCtXe7qKnF+M3f8AIgOsfKxj8QnCi1hIPL6q7qtf6j2eCT4gW/rnrzhdHRfSS6Sra8KNNpzff9lcWefNa9Zq+kK3TYh7LqlCN+ZTT3RvteWb2s09Sbk3KTcm3eTk2232tvNvifIUAAAnHJ9oZK+NrWjGF+icu1K0p9y2eJGdX9ESxVaNKOSunUl9mN8337Uu8kuvml4wjHAYfqwhFdLb+Gn+r8AjT626xyxdS0bqjF9SOznf45Lt7Ow0AAUAAAEl1a1Ex+OtKjS5lPfVrNwp27VleXgn4Fl6E5FMPFJ4uvOtLfGlanC/B5yftAo8xc9O4Tk40VTtbB058avOqX71NtP2Gyjqno9KywWFS4Yah8IHlC4uesfotgPUsL+GofCPotgPUsL+GofCB5OuLnrH6LYD1LC/hqHwj6LYD1LC/hqHwgeTrhtHrH6LYD1LC/hqHwj6LYD1LC/hqHwgVnyIao/9TrRzd44VP2Tq97zSff2lxJHHh6EacYwhFRjFJRjFKMYpKyUYrJLgjlCAAAMj+u2skMBhJ4idnLyaMPt1H5K7ltfBM30pJK7aSW2+482cqGtrx+Lag/qKLcKGflNPrVPHdwsBE8di51qk61WXOnObnNva2/8An5HCAFAAAAAAAAAAAAAA58DhJ1qkaVOLlKTskv5t7lxOxofRFXE1OZRi39qTuox/zMtPV7V+lgqbs+dNpupUllxaXZFAazoqeisFJq0q0978+o1kv8kezhxKyq1XJuUm5Sk7yb2tva3xNzrdpr5VXck/q4XjSW6185d79xpAgAYuFclGlKclCEXOUpKMYxTbbbskki7dQeSmnSUcRpGKq1cnCi86dPeuevPlw2LvOxyRairD0447Ew+vqK9KMl/YwezLdOS9iaRZyCMRikkkklutsPqwAAAAAAAAAAAAAAAAAFY8tGtvyagsFRlatXT6Rp506W/xlsXBMoax6D03yTUMXXqYmvisS51Jc550rRW6MVzcklZHTXIlgvWMR7aXwAUQC+FyJ4H02I9tL4T6XIpgfTYj96n8IFCgvv8AYtgPS1/34fCJcjej0rupXtxqR9wFCAvhckei/S1fvY+4z+yTRXpan30RuGXTbwoYF9rkm0T6Wp9+jK5KdEfbm/8AyBuF6Z8KDMSkltaXeeg6eoGg6OclGX+pXlJfzO/o+Wh6ErYalQ5/munSUpZf42m14sm4X6WSY3FfZ5/wGgcTWt0dGdnslKLjG3beVrruJfobk+SfPxVTnf8Abp7P909/giwsXiHUm5y3/ktyRsMLq/WqQU04JNXSk5J29jMmto8LhYUoKnTioRWxRSSIjyi6d5kPklN9aavVs9kL+Twvb8ic6zYd4HDTxVaVPmxyilKV5SeUIJc3a3+pQmNxUqtSVWbvKcnKT/52ZLwA4QARQnnJHqk8bilXqq9ChJSnfZOpthDuTzfdxIbovR9TEVoUKMedOpJRgt1+19iWbfcepdVNBU8DhaeFpZ82PXlZXnN+VN8W/wBAjbxRkAAAAAAAAAAAAAAAAAAAAAAAAAAdXSODjWpSpT2SVmdowyd1iZidwonTGBnh606M73i8nd9aPmyXgdPnPtftZafKDoHpqPTU1epTV8lnKO9d+8qo+dmpNLfp3HpvJpyMMTr5R7Szd9oMA1bfQ6Y8FiUaDwXRw50l1pbeC3LhlZ+JqtB4HpJ86Xkx28XuXh+hKacHJqKV23ZJb7ns42PfzlznrfN19ik/1sNBaP6apn5Mc5fovEm6SS4HU0VgVRpqC27ZPte8hXK/rf8AI8N8noytXrppW206eyU+Dd7Lx7GetzKtuVvW75biuhpSvQoSlGNtlSpsnPilnFdqu95AwAoASnk51UekcWqc0+gp2niGr5xv1YX7ZNNdyYFj8iWqHRU/nGvG1SrHm4dPbGk9su+WXgl2lrJGKdNRSjFJJJKKSsklkkkfQQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfM43Kg140G8NX50V9XUvKHB+dH9fEuBmq1j0VHE0JUpZO14P7MtzNWWnXXT3+ncyeNmi34z3UifdGk5SUY7W7L/nYZxNCVOcqc1aUZNSXFG+1fwPNj0stsl1eEdt/E8OPHNraddzOZTBg+pve+zY4TDqnBQjsX5ve2SvVXR39/Jdqp/rI02isC61RQ3bZvsRPKcVFKKVkkkuCPpxGo1Dhb3te02t3l1NMaSp4ajUxFZ82FOLlJ78tyW9vYu88s6yacq43EzxVbJzfVis1CK8mC7l7Xdk95bNbunrfIKL+qou9drz6u6PdH+b4Z1eGAAAr7oUpTlGEE5SlJRgltcpO0Uu92PT2oWq0dH4SNFWdST59eSt1ptbO5K0VwXErrkP1S50npOtHKLccKpLbJXU6q7s4p95dSCMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGGjJ8zkkm3kkrtgQbXnV6E6tPEJpX6tWO+Vlk1+a8ToJbku5I72mMf01Ry81ZQXDt72dKE3Fpp2azTJWsRMy25M+S9K0tO4r2TbQeA6Gmr+VLOfuNFym61rR+Dbg109VOGHXY2s6jXZFZ+w6PzrX9LP2mp0vgKWKkp4qCrSiubF1M7LsXZ/RGWmpRs5Nttttttttttt5tt9pguV6r4L1en4J+8k+geTzR7p8+thKUnLOKaeS9u8g85m71N1dnj8XTw0E1FvnVp7oU1m5d7yS4tHoT9nmivUqP7r95s9C6t4TCc54XD06LnbnuEbN22JsDuaPwcKNKFGlFQhTioQitiilZI7IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA02scqjiqdON+dnN3isuzNgARr5qrfY/ih7x81VvsfxQ95kFRj5qrfY/ih7x81VvsfxQ95kFkdvRWhZyqLpY2is3nHPPJZMmKAMVZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf/2Q==" style="height:65px;vertical-align:middle;margin-right:12px;">
            <div>
                <p class="empresa-nombre">CHACABUCO NOROESTE TOUR S.R.L.</p>
                <p class="empresa-sub">Desde 1996 viajando con vos | CHACAGEST Software System</p>
            </div>
        </div>
        <div class="badge-cierre">CIERRE DE CAJA</div>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <div class="info-label">📅 Fecha de Cierre</div>
            <div class="info-value">{data['fecha_cierre']}</div>
        </div>
        <div class="info-box">
            <div class="info-label">🏦 Caja</div>
            <div class="info-value">{data['caja']}</div>
        </div>
        <div class="info-box">
            <div class="info-label">👤 Responsable</div>
            <div class="info-value">{data['responsable']}</div>
        </div>
    </div>

    <h3 style="color:#5e2d61;border-bottom:2px solid #f39c12;padding-bottom:6px;">📋 Movimientos del Período</h3>
    <table class="mov">
        <thead>
            <tr>
                <th>Fecha</th><th>Tipo</th><th>Forma</th><th>Concepto</th><th>Cliente / Proveedor</th><th style="text-align:right;">Monto</th>
            </tr>
        </thead>
        <tbody>
            {filas_html if filas_html else '<tr><td colspan="6" style="text-align:center;padding:20px;color:#aaa;">Sin movimientos en el período</td></tr>'}
        </tbody>
    </table>

    <table class="subtotales-tabla">
        <tr><td colspan="2" class="subtotales-header">Resumen por Forma de Pago</td></tr>
        {subtotales_html if subtotales_html else '<tr><td colspan="2" style="padding:8px 12px;color:#aaa;">Sin movimientos</td></tr>'}
    </table>

    <div class="total-box">
        <span class="total-label">SALDO DEL PERÍODO</span>
        <span class="total-monto">$ {total:,.2f}</span>
    </div>

    <div style="background:#f0f2f6;border-radius:10px;padding:16px 24px;margin-top:16px;display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:12px;color:#888;font-weight:bold;">SALDO ACUMULADO ANTES DEL CIERRE</div>
            <div style="font-size:22px;font-weight:bold;color:#5e2d61;">$ {data.get('saldo_previo', total):,.2f}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:12px;color:#888;font-weight:bold;">SALDO DESPUÉS DEL CIERRE</div>
            <div style="font-size:22px;font-weight:bold;color:#27ae60;">$ 0,00 ✓</div>
        </div>
    </div>

    {"<div style='background:#fff8e1;border:1px solid #f39c12;border-radius:8px;padding:14px;margin-top:20px;font-size:13px;'><b>📝 Observaciones:</b><br><br>" + data['observaciones'] + "</div>" if data.get('observaciones') else ""}

    <div class="firmas">
        <div class="firma-box">
            <p style="margin:4px 0;">Responsable de Caja</p>
            <p style="margin:4px 0;font-weight:bold;">{data['responsable']}</p>
        </div>
        <div class="firma-box">
            <p style="margin:4px 0;">Supervisión / Administración</p>
            <p style="margin:4px 0;color:#aaa;">____________________________</p>
        </div>
    </div>

    <div class="footer-cierre">
        Generado por CHACAGEST · {data['fecha_cierre']} · Sistema de Gestión Chacabuco Noroeste Tour S.R.L.
    </div>
</body>
</html>"""

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
    c, v, p, t, prov, com, ce, cc = cargar_datos()
    st.session_state.clientes          = c    if c    is not None else pd.DataFrame(columns=COL_CLIENTES)
    st.session_state.viajes            = v    if v    is not None else pd.DataFrame(columns=COL_VIAJES)
    st.session_state.presupuestos      = p    if p    is not None else pd.DataFrame(columns=COL_PRESUPUESTOS)
    st.session_state.tesoreria         = t    if t    is not None else pd.DataFrame(columns=COL_TESORERIA)
    st.session_state.proveedores       = prov if prov is not None else pd.DataFrame(columns=COL_PROVEEDORES)
    st.session_state.compras           = com  if com  is not None else pd.DataFrame(columns=COL_COMPRAS)
    st.session_state.cheques_emitidos  = ce   if ce   is not None else pd.DataFrame(columns=COL_CHEQ_EMITIDOS)
    st.session_state.cheques_cartera   = cc   if cc   is not None else pd.DataFrame(columns=COL_CHEQ_CARTERA)

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
        opciones_menu = ["CALENDARIO", "DASHBOARD", "VENTAS", "COMPRAS", "TESORERIA", "CHEQUES"]
        iconos_menu   = ["calendar3", "bar-chart-line", "cart4", "bag-check", "safe", "bank2"]
    else:
        opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA", "CHEQUES"]
        iconos_menu   = ["calendar3", "cart4", "bag-check", "safe", "bank2"]

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
            c, v, p, t, prov, com, ce, cc = cargar_datos()
            st.session_state.clientes         = c    if c    is not None else pd.DataFrame(columns=COL_CLIENTES)
            st.session_state.viajes           = v    if v    is not None else pd.DataFrame(columns=COL_VIAJES)
            st.session_state.presupuestos     = p    if p    is not None else pd.DataFrame(columns=COL_PRESUPUESTOS)
            st.session_state.tesoreria        = t    if t    is not None else pd.DataFrame(columns=COL_TESORERIA)
            st.session_state.proveedores      = prov if prov is not None else pd.DataFrame(columns=COL_PROVEEDORES)
            st.session_state.compras          = com  if com  is not None else pd.DataFrame(columns=COL_COMPRAS)
            st.session_state.cheques_emitidos = ce   if ce   is not None else pd.DataFrame(columns=COL_CHEQ_EMITIDOS)
            st.session_state.cheques_cartera  = cc   if cc   is not None else pd.DataFrame(columns=COL_CHEQ_CARTERA)
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
        tab_ing, tab_egr, tab_cob, tab_ver, tab_pase, tab_cierre, tab_tras, tab_op = st.tabs(
            ["📥 INGRESOS VARIOS", "📤 EGRESOS VARIOS", "🧾 COBRANZA VIAJE", "📊 VER MOVIMIENTOS", "💱 PASE DE EFECTIVO", "🔒 CIERRE DE CAJA", "🔄 TRASPASO", "💸 ORDEN DE PAGO"]
        )
    else:
        tab_ing, tab_egr, tab_cob, tab_ver, tab_pase, tab_cierre, tab_op = st.tabs(
            ["📥 INGRESOS VARIOS", "📤 EGRESOS VARIOS", "🧾 COBRANZA VIAJE", "📊 MIS MOVIMIENTOS", "💱 PASE DE EFECTIVO", "🔒 CIERRE DE CAJA", "💸 ORDEN DE PAGO"]
        )
        tab_tras = None

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

        FORMAS_COBRO_VIAJE = FORMAS_PAGO + ["CHEQUE DE TERCEROS", "OTROS"]

        if not st.session_state.html_recibo_ready:
            # ── Selectbox de forma FUERA del form para mostrar campos dinámicamente ──
            cob_col1, cob_col2 = st.columns(2)
            c_sel_prev = cob_col1.selectbox("Cliente", st.session_state.clientes['Razón Social'].unique() if not st.session_state.clientes.empty else [""], key="cob_cli_sel")
            forma_cob_prev = cob_col2.selectbox("Forma de Cobro", FORMAS_COBRO_VIAJE, key="cob_forma_sel")

            es_cheque = (forma_cob_prev == "CHEQUE DE TERCEROS")

            with st.form("f_cob", clear_on_submit=True):
                # ── Datos base ──
                fb1, fb2 = st.columns(2)
                if es_admin:
                    cj = fb1.selectbox("Caja Destino", opc_cajas)
                else:
                    cj = caja_propia
                    fb1.markdown(f"**Caja:** {caja_propia}")
                mon  = fb2.number_input("Monto $", min_value=0.0)
                afip = st.text_input("Comprobante Asociado (AFIP/Recibo)")

                # ── Campos del cheque: aparecen solo si forma = CHEQUE DE TERCEROS ──
                if es_cheque:
                    st.markdown("---")
                    st.markdown("##### 🏦 Datos del Cheque Recibido")
                    ch1, ch2 = st.columns(2)
                    ch_nro       = ch1.text_input("Nro. de Cheque *")
                    ch_tipo      = ch2.selectbox("Tipo", ["COMÚN", "DIFERIDO", "ELECTRÓNICO"])
                    ch3, ch4     = st.columns(2)
                    ch_banco     = ch3.text_input("Banco Librador *")
                    ch_librador  = ch4.text_input("Librador (titular del cheque) *")
                    ch5, ch6     = st.columns(2)
                    ch_recibido  = ch5.text_input("Recibido de (quien entrega el cheque)")
                    ch_femision  = ch6.date_input("Fecha de Emisión", date.today())
                    ch7, ch8     = st.columns(2)
                    ch_fvenc     = ch7.date_input("Fecha de Vencimiento / Pago *", date.today() + timedelta(days=30))
                    ch_obs       = ch8.text_input("Observaciones")
                else:
                    ch_nro = ch_tipo = ch_banco = ch_librador = ""
                    ch_recibido = ch_obs = ""
                    ch_fvenc = date.today()
                    ch_femision = date.today()

                if st.form_submit_button("✅ GUARDAR COBRANZA"):
                    c_sel     = c_sel_prev
                    forma_cob = forma_cob_prev
                    if c_sel and mon > 0:
                        if es_cheque:
                            if not ch_nro or not ch_banco or not ch_librador:
                                st.warning("Completá Nro. de Cheque, Banco Librador y Librador para continuar.")
                            else:
                                # 1) Registrar en cheques_cartera
                                nuevo_cheq = pd.DataFrame([[
                                    str(date.today()), ch_nro, ch_tipo, ch_banco, ch_librador,
                                    mon, str(ch_fvenc), "EN CARTERA", "-", "-",
                                    f"Emisión:{ch_femision} | Recibido de:{ch_recibido if ch_recibido else ch_librador} | {ch_obs}"
                                ]], columns=COL_CHEQ_CARTERA)
                                st.session_state.cheques_cartera = pd.concat([st.session_state.cheques_cartera, nuevo_cheq], ignore_index=True)
                                guardar_datos("cheques_cartera", st.session_state.cheques_cartera)
                                # 2) Tesorería
                                nt = pd.DataFrame([[
                                    str(date.today()), "COBRANZA", cj, "CHEQUE TERCERO",
                                    f"Cobro Viaje - Cheque #{ch_nro} de {ch_librador}",
                                    c_sel, mon, afip
                                ]], columns=COL_TESORERIA)
                                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                                guardar_datos("tesoreria", st.session_state.tesoreria)
                                # 3) Viajes (cta cte cliente)
                                nv = pd.DataFrame([[
                                    date.today(), c_sel, date.today(), "PAGO", "TESORERIA",
                                    "-", -mon, "RECIBO", afip
                                ]], columns=COL_VIAJES)
                                st.session_state.viajes = pd.concat([st.session_state.viajes, nv], ignore_index=True)
                                guardar_datos("viajes", st.session_state.viajes)
                                # 4) Recibo
                                st.session_state.html_recibo_ready = generar_html_recibo({
                                    "Fecha": date.today(), "Cliente/Proveedor": c_sel,
                                    "Concepto": f"Cobro de Viaje — Cheque #{ch_nro} ({ch_tipo}) | Librador: {ch_librador} | Vence: {ch_fvenc}",
                                    "Caja/Banco": f"{cj} - CHEQUE DE TERCEROS",
                                    "Monto": mon, "Ref AFIP": afip
                                })
                                st.session_state.cli_ready = c_sel
                                st.rerun()
                        else:
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

        df_caja_full = st.session_state.tesoreria[st.session_state.tesoreria['Caja/Banco'] == cj_v].copy()

        # ── Mostrar solo movimientos DESDE el último cierre (inclusive el cierre no, post-cierre) ──
        cierres_idx = df_caja_full[df_caja_full['Tipo'] == 'CIERRE DE CAJA'].index
        if len(cierres_idx) > 0:
            ultimo_cierre_idx = cierres_idx[-1]
            df_ver = df_caja_full[df_caja_full.index > ultimo_cierre_idx].copy()
            ultimo_cierre_row = df_caja_full.loc[ultimo_cierre_idx]
            st.caption(f"📌 Último cierre: {ultimo_cierre_row['Fecha']} — mostrando movimientos posteriores al cierre.")
        else:
            df_ver = df_caja_full.copy()

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

    # ── CIERRE DE CAJA ──
    with tab_cierre:
        if "html_cierre_ready" not in st.session_state:
            st.session_state.html_cierre_ready = None

        if st.session_state.html_cierre_ready:
            st.success("✅ Cierre generado. Descargá el documento para imprimir.")
            st.download_button(
                "🖨️ DESCARGAR CIERRE DE CAJA",
                st.session_state.html_cierre_ready,
                file_name=f"Cierre_Caja_{date.today()}.html",
                mime="text/html"
            )
            if st.button("🔄 Nuevo Cierre"):
                st.session_state.html_cierre_ready = None
                st.rerun()
        else:
            st.markdown("Generá el cierre oficial de caja para el período que elijas. Se incluyen todos los movimientos y el saldo por forma de pago.")

            c_cie1, c_cie2 = st.columns(2)
            if es_admin:
                caja_cierre = c_cie1.selectbox("Caja a cerrar", TODAS_CAJAS, key="cierre_caja_sel")
            else:
                caja_cierre = caja_propia
                c_cie1.markdown(f"**Caja:** {caja_propia}")

            periodo_cierre = c_cie2.radio("Período", ["Hoy", "Esta semana", "Este mes", "Personalizado"], horizontal=True, key="cierre_periodo")

            hoy = date.today()
            if periodo_cierre == "Hoy":
                fecha_desde = hoy
                fecha_hasta = hoy
            elif periodo_cierre == "Esta semana":
                fecha_desde = hoy - timedelta(days=hoy.weekday())
                fecha_hasta = hoy
            elif periodo_cierre == "Este mes":
                fecha_desde = hoy.replace(day=1)
                fecha_hasta = hoy
            else:
                cp1, cp2 = st.columns(2)
                fecha_desde = cp1.date_input("Desde", value=hoy.replace(day=1), key="cierre_desde")
                fecha_hasta = cp2.date_input("Hasta", value=hoy, key="cierre_hasta")

            obs_cierre = st.text_area("Observaciones (opcional)", placeholder="Ej: Se entregó efectivo al supervisor. Faltante de $...", key="cierre_obs", height=80)

            st.markdown("---")

            # ── Base: solo movimientos desde el último cierre (igual que en tab_ver) ──
            df_caja_base = st.session_state.tesoreria[
                st.session_state.tesoreria['Caja/Banco'] == caja_cierre
            ].copy()
            cierres_prev = df_caja_base[df_caja_base['Tipo'] == 'CIERRE DE CAJA'].index
            if len(cierres_prev) > 0:
                df_caja_base = df_caja_base[df_caja_base.index > cierres_prev[-1]].copy()

            # Filtrar por período dentro de esa base
            df_cierre = df_caja_base.copy()
            try:
                df_cierre['Fecha_dt'] = pd.to_datetime(df_cierre['Fecha'], errors='coerce')
                df_cierre = df_cierre[
                    (df_cierre['Fecha_dt'].dt.date >= fecha_desde) &
                    (df_cierre['Fecha_dt'].dt.date <= fecha_hasta)
                ]
            except:
                pass

            # El saldo real a cerrar es el acumulado desde el último cierre (toda la base, no solo el período)
            saldo_desde_ultimo_cierre = df_caja_base['Monto'].sum()

            # Preview del resumen
            FORMAS_PREV = ["EFECTIVO", "TRANSFERENCIA", "TARJETA DE CREDITO", "DÓLARES", "OTROS"]
            ICONOS_PREV = {"EFECTIVO":"💵","TRANSFERENCIA":"🏦","TARJETA DE CREDITO":"💳","DÓLARES":"💲","OTROS":"📋"}
            st.markdown(f"##### Vista previa — {caja_cierre} | {fecha_desde} al {fecha_hasta}")
            cols_prev = st.columns(len(FORMAS_PREV))
            for idx_p, fr in enumerate(FORMAS_PREV):
                mask_p = df_cierre['Forma'].fillna('-').str.upper().str.contains(fr.replace("DÓLARES","DOLAR").replace("TARJETA DE CREDITO","TARJETA"), na=False)
                sub_p  = df_cierre[mask_p]['Monto'].sum()
                col_p  = "#2ecc71" if sub_p >= 0 else "#e74c3c"
                cols_prev[idx_p].markdown(
                    f"<div style='background:#f8f9fa;border-radius:8px;padding:10px;text-align:center;border-left:3px solid {col_p};'>"
                    f"<div>{ICONOS_PREV.get(fr,'💰')}</div>"
                    f"<div style='font-size:10px;color:#666;font-weight:bold;'>{fr}</div>"
                    f"<div style='font-size:14px;font-weight:bold;color:{col_p};'>$ {sub_p:,.2f}</div>"
                    f"</div>", unsafe_allow_html=True
                )
            st.caption(f"{len(df_cierre)} movimiento(s) en el período")
            st.markdown("---")

            if st.button("🔒 GENERAR CIERRE DE CAJA", type="primary"):
                responsable = st.session_state.nombre_usuario

                # ── Registrar movimiento de cierre que lleva la caja a CERO ──
                # Usa el saldo desde el último cierre (ya calculado arriba)
                if saldo_desde_ultimo_cierre != 0:
                    ajuste = -saldo_desde_ultimo_cierre
                    mov_cierre = pd.DataFrame([[
                        date.today(),
                        "CIERRE DE CAJA",
                        caja_cierre,
                        "CIERRE",
                        f"Cierre de caja — {responsable}",
                        "INTERNO",
                        ajuste,
                        f"Cierre {fecha_desde}/{fecha_hasta}"
                    ]], columns=COL_TESORERIA)
                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, mov_cierre], ignore_index=True)
                    guardar_datos("tesoreria", st.session_state.tesoreria)

                html_cierre = generar_html_cierre_caja({
                    "caja":          caja_cierre,
                    "fecha_cierre":  f"{fecha_desde} al {fecha_hasta}",
                    "responsable":   responsable,
                    "movimientos":   df_cierre.drop(columns=['Fecha_dt'], errors='ignore'),
                    "total":         df_cierre['Monto'].sum(),
                    "saldo_previo":  saldo_desde_ultimo_cierre,
                    "observaciones": obs_cierre.strip()
                })
                st.session_state.html_cierre_ready = html_cierre
                st.rerun()

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
            st.subheader("💸 Generar Orden de Pago a Proveedor")
            if "html_op_ready" not in st.session_state: st.session_state.html_op_ready = None

            if st.session_state.html_op_ready:
                st.success(f"✅ Orden de Pago para '{st.session_state.prov_ready}' registrada con éxito.")
                st.download_button("🖨️ IMPRIMIR ORDEN DE PAGO", st.session_state.html_op_ready, file_name=f"OrdenPago_{st.session_state.prov_ready}.html", mime="text/html")
                if st.button("Limpiar OP"): st.session_state.html_op_ready = None; st.rerun()
            else:
                # ── Proveedor y forma de pago FUERA del form para reaccionar en tiempo real ──
                p_sel   = st.selectbox("Seleccionar Proveedor", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""], key="op_prov")
                forma_op = st.selectbox("Forma de Pago", ["TRANSFERENCIA", "EFECTIVO", "CHEQUE PROPIO", "CHEQUE DE TERCERO"], key="op_forma")
                afip_p  = st.text_input("Referencia AFIP / Concepto", key="op_afip")

                # ── TRANSFERENCIA / EFECTIVO ─────────────────────────────────────────
                if forma_op in ["TRANSFERENCIA", "EFECTIVO"]:
                    with st.form("f_op_std", clear_on_submit=True):
                        cj_p  = st.selectbox("Caja de Salida", opc_cajas)
                        mon_p = st.number_input("Monto $", min_value=0.0, step=0.01)
                        if st.form_submit_button("✅ GENERAR ORDEN DE PAGO"):
                            if p_sel and mon_p > 0:
                                nt = pd.DataFrame([[date.today(), "PAGO PROV", cj_p, forma_op, "Orden de Pago", p_sel, -mon_p, afip_p]], columns=COL_TESORERIA)
                                nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO", 0, 0, 0, 0, 0, 0, -mon_p]], columns=COL_COMPRAS)
                                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                                st.session_state.compras   = pd.concat([st.session_state.compras, nc], ignore_index=True)
                                guardar_datos("tesoreria", st.session_state.tesoreria)
                                guardar_datos("compras", st.session_state.compras)
                                st.session_state.html_op_ready = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Concepto": f"Pago {forma_op}", "Caja/Banco": cj_p, "Monto": mon_p, "Ref AFIP": afip_p})
                                st.session_state.prov_ready = p_sel
                                st.rerun()
                            else:
                                st.warning("Seleccioná proveedor y completá el monto.")

                # ── CHEQUE PROPIO ────────────────────────────────────────────────────
                elif forma_op == "CHEQUE PROPIO":
                    st.markdown("##### 📝 Datos del Cheque Propio a Emitir")
                    with st.form("f_op_cheq_propio", clear_on_submit=True):
                        op1, op2, op3 = st.columns(3)
                        nro_op   = op1.text_input("Nro de Cheque")
                        tipo_op  = op2.selectbox("Tipo", ["FÍSICO", "ECHEQ"])
                        banco_op = op3.text_input("Banco Emisor")
                        op4, op5 = st.columns(2)
                        mon_op   = op4.number_input("Importe $", min_value=0.0, step=0.01)
                        f_venc_op = op5.date_input("Fecha de Vencimiento del Cheque", value=date.today() + timedelta(days=30))
                        obs_op   = st.text_input("Observaciones")
                        if st.form_submit_button("✅ EMITIR CHEQUE Y GENERAR ORDEN DE PAGO"):
                            if p_sel and nro_op and mon_op > 0:
                                # Registrar en cheques_emitidos
                                nuevo_cheq = pd.DataFrame([[
                                    str(date.today()), nro_op, tipo_op, banco_op, p_sel,
                                    mon_op, str(f_venc_op), "PENDIENTE", "-", obs_op
                                ]], columns=COL_CHEQ_EMITIDOS)
                                st.session_state.cheques_emitidos = pd.concat([st.session_state.cheques_emitidos, nuevo_cheq], ignore_index=True)
                                guardar_datos("cheques_emitidos", st.session_state.cheques_emitidos)
                                # Registrar egreso en tesorería
                                nt = pd.DataFrame([[date.today(), "PAGO PROV", f"CHEQUE {tipo_op}", f"CHEQUE PROPIO #{nro_op}", "Orden de Pago", p_sel, -mon_op, afip_p]], columns=COL_TESORERIA)
                                nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO CHEQUE", 0, 0, 0, 0, 0, 0, -mon_op]], columns=COL_COMPRAS)
                                st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                                st.session_state.compras   = pd.concat([st.session_state.compras, nc], ignore_index=True)
                                guardar_datos("tesoreria", st.session_state.tesoreria)
                                guardar_datos("compras", st.session_state.compras)
                                st.session_state.html_op_ready = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Concepto": f"Cheque {tipo_op} #{nro_op} — Vto: {f_venc_op}", "Caja/Banco": f"Cheque {banco_op}", "Monto": mon_op, "Ref AFIP": afip_p})
                                st.session_state.prov_ready = p_sel
                                st.rerun()
                            else:
                                st.warning("Completá proveedor, número de cheque e importe.")

                # ── CHEQUE DE TERCERO (de cartera) ───────────────────────────────────
                elif forma_op == "CHEQUE DE TERCERO":
                    # Filtrar cheques en cartera disponibles
                    df_cartera_disp = st.session_state.cheques_cartera[
                        st.session_state.cheques_cartera['Estado'] == 'EN CARTERA'
                    ].copy() if not st.session_state.cheques_cartera.empty else pd.DataFrame(columns=COL_CHEQ_CARTERA)

                    if df_cartera_disp.empty:
                        st.warning("⚠️ No hay cheques de terceros en cartera disponibles. Ingresá uno desde el módulo **CHEQUES → Cheques en Cartera**.")
                    else:
                        st.markdown("##### 📂 Seleccionar Cheque de Cartera")
                        # Mostrar cartera disponible con info útil
                        opciones_cartera = []
                        for idx, r in df_cartera_disp.iterrows():
                            d_v = (pd.to_datetime(r['Fecha Vencimiento']).date() - date.today()).days if r['Fecha Vencimiento'] not in ['-',''] else '?'
                            opciones_cartera.append(f"#{r['Nro Cheque']} — {r['Banco Librador']} — {r['Librador']} — $ {float(r['Importe']):,.2f} — Vto: {r['Fecha Vencimiento']} ({d_v}d)")

                        idx_map = {opc: idx for opc, idx in zip(opciones_cartera, df_cartera_disp.index)}

                        with st.form("f_op_cheq_tercero", clear_on_submit=True):
                            cheq_sel_str = st.selectbox("Cheque a utilizar", opciones_cartera)
                            if st.form_submit_button("✅ APLICAR CHEQUE Y GENERAR ORDEN DE PAGO"):
                                if p_sel and cheq_sel_str:
                                    cheq_idx = idx_map[cheq_sel_str]
                                    cheq_row = st.session_state.cheques_cartera.loc[cheq_idx]
                                    mon_ct   = float(cheq_row['Importe'])
                                    # Marcar cheque como APLICADO PAGO
                                    st.session_state.cheques_cartera.loc[cheq_idx, 'Estado']          = 'APLICADO PAGO'
                                    st.session_state.cheques_cartera.loc[cheq_idx, 'Destino']         = p_sel
                                    st.session_state.cheques_cartera.loc[cheq_idx, 'Fecha Aplicación']= str(date.today())
                                    guardar_datos("cheques_cartera", st.session_state.cheques_cartera)
                                    # Registrar en tesorería
                                    nt = pd.DataFrame([[date.today(), "PAGO PROV", "CARTERA", f"CHEQUE TERCERO #{cheq_row['Nro Cheque']}", "Orden de Pago", p_sel, -mon_ct, afip_p]], columns=COL_TESORERIA)
                                    nc = pd.DataFrame([[date.today(), p_sel, "-", "ORDEN PAGO CHEQUE TERCERO", 0, 0, 0, 0, 0, 0, -mon_ct]], columns=COL_COMPRAS)
                                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, nt], ignore_index=True)
                                    st.session_state.compras   = pd.concat([st.session_state.compras, nc], ignore_index=True)
                                    guardar_datos("tesoreria", st.session_state.tesoreria)
                                    guardar_datos("compras", st.session_state.compras)
                                    st.session_state.html_op_ready = generar_html_orden_pago({"Fecha": date.today(), "Proveedor": p_sel, "Concepto": f"Cheque de {cheq_row['Librador']} #{cheq_row['Nro Cheque']} — Vto: {cheq_row['Fecha Vencimiento']}", "Caja/Banco": f"Cheque {cheq_row['Banco Librador']}", "Monto": mon_ct, "Ref AFIP": afip_p})
                                    st.session_state.prov_ready = p_sel
                                    st.rerun()
                                else:
                                    st.warning("Seleccioná proveedor y cheque.")

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

elif sel == "CARGA PROVEEDOR":
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

elif sel == "CTA CTE PROVEEDOR":
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

# =============================================================
# CHEQUES
# =============================================================
elif sel == "CHEQUES":
    st.header("🏦 Gestión de Cheques")

    hoy = date.today()

    # ── Helper: badge de estado con color ──
    def badge_estado(estado):
        colores = {
            "PENDIENTE":    ("#fff3cd", "#856404", "⏳"),
            "CONCILIADO":   ("#d1e7dd", "#0f5132", "✅"),
            "RECHAZADO":    ("#f8d7da", "#842029", "❌"),
            "EN CARTERA":   ("#cff4fc", "#055160", "📂"),
            "DEPOSITADO":   ("#d1e7dd", "#0f5132", "🏦"),
            "APLICADO PAGO":("#e2d9f3", "#4a235a", "💸"),
            "VENCIDO":      ("#f8d7da", "#842029", "⚠️"),
        }
        bg, fg, ico = colores.get(estado, ("#f0f2f6","#333","•"))
        return f"<span style='background:{bg};color:{fg};padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;'>{ico} {estado}</span>"

    # ── Helper: días para vencer ──
    def dias_vencer(fecha_str):
        try:
            fv = pd.to_datetime(fecha_str).date()
            return (fv - hoy).days
        except:
            return None

    # ── Alertas globales: cheques próximos a vencer (≤7 días) ──
    alertas = []
    if not st.session_state.cheques_emitidos.empty:
        for _, r in st.session_state.cheques_emitidos[st.session_state.cheques_emitidos['Estado'] == 'PENDIENTE'].iterrows():
            d = dias_vencer(r['Fecha Vencimiento'])
            if d is not None and 0 <= d <= 7:
                alertas.append(f"⚠️ **Cheque emitido #{r['Nro Cheque']}** a {r['Beneficiario']} vence en **{d} día(s)** — $ {float(r['Importe']):,.2f}")
    if not st.session_state.cheques_cartera.empty:
        for _, r in st.session_state.cheques_cartera[st.session_state.cheques_cartera['Estado'] == 'EN CARTERA'].iterrows():
            d = dias_vencer(r['Fecha Vencimiento'])
            if d is not None and 0 <= d <= 7:
                alertas.append(f"📂 **Cheque en cartera #{r['Nro Cheque']}** de {r['Librador']} vence en **{d} día(s)** — $ {float(r['Importe']):,.2f}")
            if d is not None and d < 0:
                alertas.append(f"🔴 **Cheque VENCIDO #{r['Nro Cheque']}** de {r['Librador']} venció hace **{abs(d)} día(s)** — $ {float(r['Importe']):,.2f}")

    if alertas:
        with st.expander(f"🚨 {len(alertas)} alerta(s) de vencimiento", expanded=True):
            for a in alertas:
                st.warning(a)

    tab_emit, tab_cart, tab_venc = st.tabs(["📤 CHEQUES EMITIDOS", "📂 CHEQUES EN CARTERA", "📅 PRÓXIMOS VENCIMIENTOS"])

    # ══════════════════════════════════════════════════════
    # TAB 1 — CHEQUES EMITIDOS
    # ══════════════════════════════════════════════════════
    with tab_emit:
        if st.session_state.get("msg_cheq_emit"):
            st.success(st.session_state.msg_cheq_emit)
            st.session_state.msg_cheq_emit = None

        with st.expander("➕ REGISTRAR NUEVO CHEQUE EMITIDO", expanded=False):
            with st.form("f_cheq_emit", clear_on_submit=True):
                ce1, ce2, ce3 = st.columns(3)
                nro_ch   = ce1.text_input("Nro de Cheque")
                tipo_ch  = ce2.selectbox("Tipo", ["FÍSICO", "ECHEQ"])
                banco_ch = ce3.text_input("Banco Emisor")
                ce4, ce5 = st.columns(2)
                benef    = ce4.text_input("Beneficiario (Proveedor / Persona)")
                imp_ch   = ce5.number_input("Importe $", min_value=0.0, step=0.01)
                ce6, ce7 = st.columns(2)
                f_emis   = ce6.date_input("Fecha de Emisión", value=hoy)
                f_venc   = ce7.date_input("Fecha de Vencimiento", value=hoy + timedelta(days=30))
                obs_ch   = st.text_input("Observaciones (opcional)")
                if st.form_submit_button("✅ REGISTRAR CHEQUE"):
                    if nro_ch and benef and imp_ch > 0:
                        nueva_fila = pd.DataFrame([[
                            str(f_emis), nro_ch, tipo_ch, banco_ch, benef,
                            imp_ch, str(f_venc), "PENDIENTE", "-", obs_ch
                        ]], columns=COL_CHEQ_EMITIDOS)
                        st.session_state.cheques_emitidos = pd.concat([st.session_state.cheques_emitidos, nueva_fila], ignore_index=True)
                        guardar_datos("cheques_emitidos", st.session_state.cheques_emitidos)
                        # Registrar egreso en tesorería
                        mov = pd.DataFrame([[
                            str(f_emis), "CHEQUE EMITIDO", "CAJA GENERAL", f"CHEQUE {tipo_ch}",
                            f"Cheque #{nro_ch} a {benef}", benef, -imp_ch, nro_ch
                        ]], columns=COL_TESORERIA)
                        st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, mov], ignore_index=True)
                        guardar_datos("tesoreria", st.session_state.tesoreria)
                        st.session_state.msg_cheq_emit = f"✅ Cheque #{nro_ch} emitido a {benef} por $ {imp_ch:,.2f} registrado."
                        st.rerun()
                    else:
                        st.warning("Completá Nro de Cheque, Beneficiario e Importe.")

        # ── IMPORTAR eCheqs desde XLS del banco ──
        with st.expander("📥 IMPORTAR eCheqs DESDE ARCHIVO XLS DEL BANCO", expanded=False):
            st.markdown("""
            <div style='background:#fff4e6;border-left:4px solid #f39c12;padding:10px 14px;border-radius:6px;font-size:13px;'>
                📋 <b>Cómo exportar el archivo desde tu banco:</b><br>
                Ingresá a Banca Electrónica → eCheqs → Cheques Diferidos Emitidos → Exportar XLS.<br>
                El archivo debe tener las columnas: <b>Fecha | Fecha Acred | Nro Cheque | Banco Emisor | Concepto | Importe</b>
            </div>
            """, unsafe_allow_html=True)

            archivo_xls = st.file_uploader("Seleccioná el archivo XLS del banco", type=["xls", "xlsx"], key="xls_echeq_uploader")

            if archivo_xls is not None:
                try:
                    import io, struct
                    from datetime import timedelta as _td

                    # ── Helpers ────────────────────────────────────────────
                    def _fmt_fecha(v):
                        """Convierte serial Excel o string a 'YYYY-MM-DD'."""
                        if v is None or str(v).strip() in ('', '-', 'None'):
                            return '-'
                        try:
                            f = float(str(v).replace(',', '.'))
                            if 30000 < f < 60000:
                                return (date(1899, 12, 30) + _td(days=int(f))).strftime('%Y-%m-%d')
                        except:
                            pass
                        # ya es string con formato reconocible
                        s = str(v).strip()
                        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
                            try:
                                from datetime import datetime as _dt
                                return _dt.strptime(s, fmt).strftime('%Y-%m-%d')
                            except:
                                pass
                        return s

                    def _benef(concepto):
                        if concepto and ':' in str(concepto):
                            return str(concepto).split(':', 1)[1].strip()
                        return str(concepto).strip() if concepto else '-'

                    # ── Leer el archivo con openpyxl (xlsx) o parser BIFF (xls) ──
                    nombre = archivo_xls.name.lower()
                    raw    = archivo_xls.read()
                    filas_raw = []   # lista de dicts con claves = nombre columna (lower)

                    if nombre.endswith('.xlsx'):
                        import openpyxl
                        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
                        ws_xl = wb.active
                        rows_iter = list(ws_xl.iter_rows(values_only=True))
                        # buscar fila de cabecera: la primera con AL MENOS 3 keywords de columnas esperadas
                        HEADER_KW = ('fecha', 'nro', 'banco', 'importe', 'concepto', 'monto', 'acred', 'emisor')
                        header_row = 0
                        for ri, row in enumerate(rows_iter[:20]):
                            cells_str = [str(c).lower() if c is not None else '' for c in row]
                            hits = sum(1 for c in cells_str if any(kw in c for kw in HEADER_KW))
                            if hits >= 3:
                                header_row = ri; break
                        headers = [str(c).strip().lower() if c is not None else f'col{ci}'
                                   for ci, c in enumerate(rows_iter[header_row])]
                        for row in rows_iter[header_row+1:]:
                            if all(c is None for c in row): continue
                            filas_raw.append({headers[ci]: row[ci] for ci in range(len(headers))})

                    else:   # .xls — parser BIFF8
                        def _parse_biff(data):
                            start = 0
                            for i in range(len(data) - 4):
                                try:
                                    if struct.unpack_from('<H', data, i)[0] == 0x0809:
                                        if 4 <= struct.unpack_from('<H', data, i+2)[0] <= 20:
                                            start = i; break
                                except: pass
                            data = data[start:]
                            sst, cells = [], {}
                            i = 0
                            while i < len(data) - 4:
                                try:
                                    rtype = struct.unpack_from('<H', data, i)[0]
                                    rlen  = struct.unpack_from('<H', data, i+2)[0]
                                except: break
                                if rlen > 8192 or i + 4 + rlen > len(data):
                                    i += 1; continue
                                chunk = data[i+4:i+4+rlen]
                                if rtype == 0x00FC and rlen >= 8:      # SST
                                    total = struct.unpack_from('<I', chunk, 4)[0]
                                    pos = 8
                                    for _ in range(total):
                                        if pos + 3 > len(chunk): break
                                        nchars = struct.unpack_from('<H', chunk, pos)[0]
                                        flags  = chunk[pos+2]; pos += 3
                                        if flags & 0x04: pos += 2
                                        if flags & 0x08: pos += 4
                                        if flags & 0x01:
                                            s = chunk[pos:pos+nchars*2].decode('utf-16-le', errors='replace'); pos += nchars*2
                                        else:
                                            s = chunk[pos:pos+nchars].decode('latin-1', errors='replace'); pos += nchars
                                        sst.append(s)
                                elif rtype == 0x00FD and rlen >= 10:   # LabelSST
                                    r = struct.unpack_from('<H', chunk, 0)[0]
                                    c = struct.unpack_from('<H', chunk, 2)[0]
                                    cells[(r,c)] = ('sst', struct.unpack_from('<I', chunk, 6)[0])
                                elif rtype == 0x0203 and rlen >= 14:   # Number
                                    r = struct.unpack_from('<H', chunk, 0)[0]
                                    c = struct.unpack_from('<H', chunk, 2)[0]
                                    cells[(r,c)] = ('num', struct.unpack_from('<d', chunk, 6)[0])
                                elif rtype == 0x027E and rlen >= 10:   # RK
                                    r  = struct.unpack_from('<H', chunk, 0)[0]
                                    c  = struct.unpack_from('<H', chunk, 2)[0]
                                    rk = struct.unpack_from('<I', chunk, 6)[0]
                                    if rk & 2:
                                        val = (rk >> 2) / (100.0 if (rk & 1) else 1.0)
                                    else:
                                        packed = struct.pack('<Q', (rk & 0xFFFFFFFC) << 32)
                                        val = struct.unpack('<d', packed)[0]
                                        if rk & 1: val /= 100
                                    cells[(r,c)] = ('num', val)
                                elif rtype == 0x0204 and rlen >= 8:    # Label (cadena directa)
                                    r = struct.unpack_from('<H', chunk, 0)[0]
                                    c = struct.unpack_from('<H', chunk, 2)[0]
                                    slen = struct.unpack_from('<H', chunk, 6)[0]
                                    s = chunk[8:8+slen].decode('latin-1', errors='replace')
                                    cells[(r,c)] = ('str', s)
                                i += 4 + rlen
                            return sst, cells

                        sst, cells = _parse_biff(raw)

                        def _cell_val(sst, cells, row, col):
                            cell = cells.get((row, col))
                            if cell is None: return None
                            if cell[0] == 'sst': return sst[cell[1]] if cell[1] < len(sst) else None
                            if cell[0] == 'str': return cell[1]
                            return cell[1]  # num

                        max_row = max((r for r,c in cells), default=0)
                        max_col = max((c for r,c in cells), default=0)

                        # buscar fila de cabecera: la primera con AL MENOS 3 keywords de columnas esperadas
                        HEADER_KW = ('fecha', 'nro', 'banco', 'importe', 'concepto', 'monto', 'acred', 'emisor')
                        header_row = 0
                        for ri in range(min(20, max_row+1)):
                            row_vals = [str(_cell_val(sst, cells, ri, ci) or '').lower()
                                        for ci in range(max_col+1)]
                            hits = sum(1 for v in row_vals if any(kw in v for kw in HEADER_KW))
                            if hits >= 3:
                                header_row = ri; break

                        headers = [str(_cell_val(sst, cells, header_row, ci) or f'col{ci}').strip().lower()
                                   for ci in range(max_col+1)]

                        for ri in range(header_row+1, max_row+1):
                            row_d = {headers[ci]: _cell_val(sst, cells, ri, ci)
                                     for ci in range(len(headers))}
                            if any(v is not None for v in row_d.values()):
                                filas_raw.append(row_d)

                    # ── Buscar columnas por nombre ───────────────────────
                    def _find_col(row_d, *keywords):
                        for kw in keywords:
                            for k in row_d.keys():
                                if kw in k:
                                    return row_d[k]
                        return None

                    # Detectar si Fecha y Nro Cheque vienen vacíos en todas las filas
                    col_fecha_vacia = all(_find_col(r, 'fecha emis', 'fecha emisi', 'fecha ') is None for r in filas_raw)
                    col_nro_vacia   = all(_find_col(r, 'nro', 'número', 'numero', 'nro cheque') is None for r in filas_raw)

                    if col_fecha_vacia or col_nro_vacia:
                        faltantes = []
                        if col_fecha_vacia: faltantes.append('**Fecha** y **Fecha Acred**')
                        if col_nro_vacia:   faltantes.append('**Nro Cheque**')
                        st.warning(f"⚠️ El archivo tiene las columnas {' y '.join(faltantes)} vacías. El banco exporta el archivo sin esos datos.")
                        st.markdown("""
                        <div style='background:#fff3cd;border-left:4px solid #f39c12;padding:12px 16px;border-radius:6px;font-size:13px;margin-top:8px;'>
                        <b>📋 Cómo completar el archivo antes de importar:</b><br><br>
                        1. Abrí el archivo XLS en Excel<br>
                        2. Completá la columna <b>Fecha</b> con la fecha de emisión (formato DD/MM/AAAA)<br>
                        3. Completá la columna <b>Fecha Acred</b> con la fecha de vencimiento<br>
                        4. Completá la columna <b>Nro Cheque</b> con el número de cada cheque<br>
                        5. Guardá el archivo y volvé a subirlo aquí
                        </div>
                        """, unsafe_allow_html=True)
                        # Vista previa de los datos disponibles
                        datos_parciales = []
                        for r in filas_raw:
                            concepto_p = _find_col(r, 'concepto', 'descripcion', 'detalle', 'orden')
                            banco_p    = _find_col(r, 'banco')
                            importe_p  = _find_col(r, 'importe', 'monto', 'valor')
                            try:
                                imp_p = float(str(importe_p).replace('.', '').replace(',', '.')) if importe_p else 0
                            except:
                                imp_p = 0
                            if imp_p > 0:
                                datos_parciales.append({
                                    'Fecha Emisión':     '⚠️ completar',
                                    'Fecha Vencimiento': '⚠️ completar',
                                    'Nro Cheque':        '⚠️ completar',
                                    'Banco':             str(banco_p).strip() if banco_p else '-',
                                    'Beneficiario':      _benef(str(concepto_p)) if concepto_p else '-',
                                    'Importe':           imp_p,
                                })
                        if datos_parciales:
                            st.markdown(f"##### 👇 {len(datos_parciales)} registros encontrados — completá las columnas faltantes en el XLS:")
                            st.dataframe(pd.DataFrame(datos_parciales), use_container_width=True, hide_index=True)
                    else:
                        filas = []
                        for row_d in filas_raw:
                            fecha_emis = _fmt_fecha(_find_col(row_d, 'fecha emis', 'fecha emisi', 'fecha '))
                            fecha_venc = _fmt_fecha(_find_col(row_d, 'acred', 'venc', 'fecha acred'))
                            nro        = _find_col(row_d, 'nro', 'número', 'numero', 'nro cheque')
                            banco      = _find_col(row_d, 'banco')
                            concepto   = _find_col(row_d, 'concepto', 'descripcion', 'detalle', 'orden')
                            importe    = _find_col(row_d, 'importe', 'monto', 'valor')
                            try:
                                imp_f = float(str(importe).replace('.', '').replace(',', '.')) if importe else 0
                            except:
                                imp_f = 0
                            try:
                                nro_str = str(int(float(str(nro).replace('.', '').replace(',', '.')))) if nro is not None else None
                            except (ValueError, TypeError):
                                continue
                            if nro_str is None or imp_f <= 0:
                                continue
                            filas.append({
                                'fecha_emis': fecha_emis if fecha_emis != '-' else str(date.today()),
                                'fecha_venc': fecha_venc if fecha_venc != '-' else str(date.today()),
                                'nro':        nro_str,
                                'banco':      str(banco).strip() if banco else 'BANCO GALICIA',
                                'concepto':   str(concepto).strip() if concepto else '-',
                                'importe':    imp_f,
                            })
                        if not filas:
                            st.error("❌ No se encontraron datos válidos. Verificá que el archivo tenga las columnas correctas.")
                        else:
                            df_preview = pd.DataFrame([{
                                'Fecha Emisión':     f['fecha_emis'],
                                'Fecha Vencimiento': f['fecha_venc'],
                                'Nro Cheque':        f['nro'],
                                'Banco':             f['banco'],
                                'Beneficiario':      _benef(f['concepto']),
                                'Importe':           f['importe'],
                            } for f in filas])

                            st.markdown(f"##### 📋 Se encontraron **{len(df_preview)} eCheqs** para importar:")
                            st.dataframe(df_preview, use_container_width=True, hide_index=True)

                            nros_existentes = set(st.session_state.cheques_emitidos['Nro Cheque'].astype(str).tolist())
                            nuevos     = [f for f in filas if f['nro'] not in nros_existentes]
                            duplicados = len(filas) - len(nuevos)

                            if duplicados > 0:
                                st.info(f"ℹ️ {duplicados} cheque(s) ya existen en el sistema y serán omitidos.")

                            col_imp1, col_imp2 = st.columns(2)
                            if col_imp1.button(f"✅ IMPORTAR {len(nuevos)} eCheqs NUEVOS", key="btn_importar_echeq", disabled=(len(nuevos)==0)):
                                importados = 0
                                for f in nuevos:
                                    benef_val = _benef(f['concepto'])
                                    imp_val   = f['importe']
                                    nro_val   = f['nro']
                                    f_emis    = f['fecha_emis']
                                    f_venc    = f['fecha_venc']
                                    banco_val = f['banco']

                                    # 1) cheques_emitidos
                                    nueva_fila = pd.DataFrame([[
                                        f_emis, nro_val, "ECHEQ", banco_val, benef_val,
                                        imp_val, f_venc, "PENDIENTE", "-",
                                        "Importado desde XLS banco"
                                    ]], columns=COL_CHEQ_EMITIDOS)
                                    st.session_state.cheques_emitidos = pd.concat(
                                        [st.session_state.cheques_emitidos, nueva_fila], ignore_index=True)

                                    # 2) tesorería
                                    mov = pd.DataFrame([[
                                        f_emis, "CHEQUE EMITIDO", "CAJA GENERAL", "CHEQUE ECHEQ",
                                        f"eCheq #{nro_val} a {benef_val}", benef_val, -imp_val, nro_val
                                    ]], columns=COL_TESORERIA)
                                    st.session_state.tesoreria = pd.concat(
                                        [st.session_state.tesoreria, mov], ignore_index=True)
                                    importados += 1

                                guardar_datos("cheques_emitidos", st.session_state.cheques_emitidos)
                                guardar_datos("tesoreria", st.session_state.tesoreria)
                                st.session_state.msg_cheq_emit = f"✅ Se importaron {importados} eCheqs correctamente."
                                st.rerun()

                            if col_imp2.button("❌ Cancelar", key="btn_cancelar_echeq"):
                                st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al leer el archivo: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        st.markdown("---")

        # Filtro por estado
        filtro_emit = st.radio("Mostrar", ["PENDIENTES", "CONCILIADOS", "TODOS"], horizontal=True, key="filtro_emit")
        df_emit = st.session_state.cheques_emitidos.copy()
        if filtro_emit == "PENDIENTES":
            df_emit = df_emit[df_emit['Estado'] == 'PENDIENTE']
        elif filtro_emit == "CONCILIADOS":
            df_emit = df_emit[df_emit['Estado'] == 'CONCILIADO']

        if df_emit.empty:
            st.info("No hay cheques en esta categoría.")
        else:
            for i, row in df_emit.iterrows():
                d_venc = dias_vencer(row['Fecha Vencimiento'])
                alerta_color = ""
                if row['Estado'] == 'PENDIENTE' and d_venc is not None:
                    if d_venc < 0:   alerta_color = "border-left:4px solid #e74c3c;"
                    elif d_venc <= 7: alerta_color = "border-left:4px solid #f39c12;"
                    else:             alerta_color = "border-left:4px solid #2ecc71;"

                with st.container():
                    col_inf, col_acc = st.columns([0.82, 0.18])
                    col_inf.markdown(
                        f"<div style='background:#f8f9fa;border-radius:8px;padding:12px 16px;{alerta_color}'>"
                        f"<b>#{row['Nro Cheque']}</b> — {row['Tipo']} — {row['Banco']} &nbsp;|&nbsp; "
                        f"Beneficiario: <b>{row['Beneficiario']}</b><br>"
                        f"Emisión: {row['Fecha Emisión']} &nbsp;·&nbsp; Vencimiento: <b>{row['Fecha Vencimiento']}</b>"
                        f"{'&nbsp;·&nbsp; <b style=color:#e74c3c>VENCIDO</b>' if d_venc is not None and d_venc < 0 else (f'&nbsp;·&nbsp; <b style=color:#f39c12>{d_venc}d</b>' if d_venc is not None and d_venc<=7 else '')}"
                        f"&nbsp;&nbsp; {badge_estado(row['Estado'])}<br>"
                        f"<b style='font-size:17px;color:#5e2d61;'>$ {float(row['Importe']):,.2f}</b>"
                        f"{'&nbsp;&nbsp;<small>' + str(row['Observaciones']) + '</small>' if str(row['Observaciones']) not in ['-',''] else ''}"
                        f"</div>", unsafe_allow_html=True
                    )
                    if row['Estado'] == 'PENDIENTE':
                        if col_acc.button("✅ Conciliar", key=f"conc_{i}"):
                            st.session_state.cheques_emitidos.loc[i, 'Estado'] = 'CONCILIADO'
                            st.session_state.cheques_emitidos.loc[i, 'Fecha Conciliación'] = str(hoy)
                            guardar_datos("cheques_emitidos", st.session_state.cheques_emitidos)
                            st.session_state.msg_cheq_emit = f"✅ Cheque #{row['Nro Cheque']} conciliado."
                            st.rerun()
                        if col_acc.button("❌ Rechazar", key=f"rech_{i}"):
                            st.session_state.cheques_emitidos.loc[i, 'Estado'] = 'RECHAZADO'
                            guardar_datos("cheques_emitidos", st.session_state.cheques_emitidos)
                            st.rerun()
                    st.divider()

    # ══════════════════════════════════════════════════════
    # TAB 2 — CHEQUES EN CARTERA (de terceros)
    # ══════════════════════════════════════════════════════
    with tab_cart:
        if st.session_state.get("msg_cheq_cart"):
            st.success(st.session_state.msg_cheq_cart)
            st.session_state.msg_cheq_cart = None

        with st.expander("➕ INGRESAR CHEQUE DE TERCERO A CARTERA", expanded=False):
            with st.form("f_cheq_cart", clear_on_submit=True):
                cc1, cc2, cc3 = st.columns(3)
                nro_cc   = cc1.text_input("Nro de Cheque")
                tipo_cc  = cc2.selectbox("Tipo", ["FÍSICO", "ECHEQ"])
                banco_cc = cc3.text_input("Banco Librador")
                cc4, cc5 = st.columns(2)
                librador = cc4.text_input("Librador (quien entregó el cheque)")
                imp_cc   = cc5.number_input("Importe $", min_value=0.0, step=0.01)
                cc6, cc7 = st.columns(2)
                f_rec    = cc6.date_input("Fecha de Recepción", value=hoy)
                f_venc_c = cc7.date_input("Fecha de Vencimiento", value=hoy + timedelta(days=30))
                obs_cc   = st.text_input("Observaciones (opcional)")
                if st.form_submit_button("✅ AGREGAR A CARTERA"):
                    if nro_cc and librador and imp_cc > 0:
                        nueva_cc = pd.DataFrame([[
                            str(f_rec), nro_cc, tipo_cc, banco_cc, librador,
                            imp_cc, str(f_venc_c), "EN CARTERA", "-", "-", obs_cc
                        ]], columns=COL_CHEQ_CARTERA)
                        st.session_state.cheques_cartera = pd.concat([st.session_state.cheques_cartera, nueva_cc], ignore_index=True)
                        guardar_datos("cheques_cartera", st.session_state.cheques_cartera)
                        st.session_state.msg_cheq_cart = f"✅ Cheque #{nro_cc} de {librador} ingresado a cartera por $ {imp_cc:,.2f}."
                        st.rerun()
                    else:
                        st.warning("Completá Nro de Cheque, Librador e Importe.")

        st.markdown("---")

        filtro_cart = st.radio("Mostrar", ["EN CARTERA", "APLICADOS/DEPOSITADOS", "TODOS"], horizontal=True, key="filtro_cart")
        df_cart = st.session_state.cheques_cartera.copy()
        if filtro_cart == "EN CARTERA":
            df_cart = df_cart[df_cart['Estado'] == 'EN CARTERA']
        elif filtro_cart == "APLICADOS/DEPOSITADOS":
            df_cart = df_cart[df_cart['Estado'].isin(['DEPOSITADO', 'APLICADO PAGO'])]

        if df_cart.empty:
            st.info("No hay cheques en esta categoría.")
        else:
            for i, row in df_cart.iterrows():
                d_venc_c = dias_vencer(row['Fecha Vencimiento'])
                alerta_c = ""
                if row['Estado'] == 'EN CARTERA' and d_venc_c is not None:
                    if d_venc_c < 0:    alerta_c = "border-left:4px solid #e74c3c;"
                    elif d_venc_c <= 7: alerta_c = "border-left:4px solid #f39c12;"
                    else:               alerta_c = "border-left:4px solid #2ecc71;"

                with st.container():
                    col_ci, col_ca = st.columns([0.75, 0.25])
                    col_ci.markdown(
                        f"<div style='background:#f8f9fa;border-radius:8px;padding:12px 16px;{alerta_c}'>"
                        f"<b>#{row['Nro Cheque']}</b> — {row['Tipo']} — {row['Banco Librador']} &nbsp;|&nbsp; "
                        f"Librador: <b>{row['Librador']}</b><br>"
                        f"Recibido: {row['Fecha Recepción']} &nbsp;·&nbsp; Vencimiento: <b>{row['Fecha Vencimiento']}</b>"
                        f"{'&nbsp;·&nbsp; <b style=color:#e74c3c>VENCIDO</b>' if d_venc_c is not None and d_venc_c < 0 else (f'&nbsp;·&nbsp; <b style=color:#f39c12>{d_venc_c}d para vencer</b>' if d_venc_c is not None and d_venc_c<=7 else '')}"
                        f"&nbsp;&nbsp; {badge_estado(row['Estado'])}<br>"
                        f"<b style='font-size:17px;color:#5e2d61;'>$ {float(row['Importe']):,.2f}</b>"
                        f"{'&nbsp;&nbsp; → ' + str(row['Destino']) if str(row['Destino']) not in ['-',''] else ''}"
                        f"</div>", unsafe_allow_html=True
                    )
                    if row['Estado'] == 'EN CARTERA':
                        # Depositar en banco
                        if col_ca.button("🏦 Depositar", key=f"dep_{i}"):
                            st.session_state[f"accion_cart_{i}"] = "depositar"
                        # Aplicar como pago a proveedor
                        if col_ca.button("💸 Pagar c/cheque", key=f"pag_{i}"):
                            st.session_state[f"accion_cart_{i}"] = "pagar"

                        accion = st.session_state.get(f"accion_cart_{i}")
                        if accion == "depositar":
                            with st.form(f"f_dep_{i}"):
                                banco_dep = st.selectbox("Banco donde depositar", ["BANCO GALICIA", "BANCO PROVINCIA", "BANCO SUPERVIELLE", "OTRO"])
                                if st.form_submit_button("✅ CONFIRMAR DEPÓSITO"):
                                    st.session_state.cheques_cartera.loc[i, 'Estado']          = 'DEPOSITADO'
                                    st.session_state.cheques_cartera.loc[i, 'Destino']         = banco_dep
                                    st.session_state.cheques_cartera.loc[i, 'Fecha Aplicación']= str(hoy)
                                    guardar_datos("cheques_cartera", st.session_state.cheques_cartera)
                                    # Ingreso en tesorería del banco
                                    mov_dep = pd.DataFrame([[
                                        str(hoy), "DEPÓSITO CHEQUE", banco_dep, "CHEQUE TERCERO",
                                        f"Depósito cheque #{row['Nro Cheque']} de {row['Librador']}",
                                        row['Librador'], float(row['Importe']), row['Nro Cheque']
                                    ]], columns=COL_TESORERIA)
                                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, mov_dep], ignore_index=True)
                                    guardar_datos("tesoreria", st.session_state.tesoreria)
                                    st.session_state[f"accion_cart_{i}"] = None
                                    st.session_state.msg_cheq_cart = f"✅ Cheque #{row['Nro Cheque']} depositado en {banco_dep}."
                                    st.rerun()
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"accion_cart_{i}"] = None; st.rerun()

                        elif accion == "pagar":
                            with st.form(f"f_pag_{i}"):
                                prov_pag = st.selectbox("Proveedor a pagar", st.session_state.proveedores['Razón Social'].unique() if not st.session_state.proveedores.empty else [""])
                                if st.form_submit_button("✅ CONFIRMAR PAGO"):
                                    st.session_state.cheques_cartera.loc[i, 'Estado']          = 'APLICADO PAGO'
                                    st.session_state.cheques_cartera.loc[i, 'Destino']         = prov_pag
                                    st.session_state.cheques_cartera.loc[i, 'Fecha Aplicación']= str(hoy)
                                    guardar_datos("cheques_cartera", st.session_state.cheques_cartera)
                                    # Egreso en tesorería
                                    mov_pag = pd.DataFrame([[
                                        str(hoy), "PAGO CHEQUE TERCERO", "CARTERA", "CHEQUE TERCERO",
                                        f"Pago a {prov_pag} con cheque #{row['Nro Cheque']} de {row['Librador']}",
                                        prov_pag, -float(row['Importe']), row['Nro Cheque']
                                    ]], columns=COL_TESORERIA)
                                    st.session_state.tesoreria = pd.concat([st.session_state.tesoreria, mov_pag], ignore_index=True)
                                    guardar_datos("tesoreria", st.session_state.tesoreria)
                                    st.session_state[f"accion_cart_{i}"] = None
                                    st.session_state.msg_cheq_cart = f"✅ Cheque #{row['Nro Cheque']} aplicado como pago a {prov_pag}."
                                    st.rerun()
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state[f"accion_cart_{i}"] = None; st.rerun()
                    st.divider()

    # ══════════════════════════════════════════════════════
    # TAB 3 — PRÓXIMOS VENCIMIENTOS (ambos tipos)
    # ══════════════════════════════════════════════════════
    with tab_venc:
        st.markdown("##### Cheques con vencimiento en los próximos 30 días")
        dias_filtro = st.slider("Días hacia adelante", 7, 60, 30, key="dias_venc_slider")

        filas_venc = []

        if not st.session_state.cheques_emitidos.empty:
            for _, r in st.session_state.cheques_emitidos[st.session_state.cheques_emitidos['Estado'] == 'PENDIENTE'].iterrows():
                d = dias_vencer(r['Fecha Vencimiento'])
                if d is not None and d <= dias_filtro:
                    filas_venc.append({
                        "Tipo": "📤 EMITIDO",
                        "Nro Cheque": r['Nro Cheque'],
                        "Modalidad": r['Tipo'],
                        "Banco": r['Banco'],
                        "Contraparte": r['Beneficiario'],
                        "Importe": float(r['Importe']),
                        "Vencimiento": r['Fecha Vencimiento'],
                        "Días": d,
                        "Estado": r['Estado']
                    })

        if not st.session_state.cheques_cartera.empty:
            for _, r in st.session_state.cheques_cartera[st.session_state.cheques_cartera['Estado'] == 'EN CARTERA'].iterrows():
                d = dias_vencer(r['Fecha Vencimiento'])
                if d is not None and d <= dias_filtro:
                    filas_venc.append({
                        "Tipo": "📂 CARTERA",
                        "Nro Cheque": r['Nro Cheque'],
                        "Modalidad": r['Tipo'],
                        "Banco": r['Banco Librador'],
                        "Contraparte": r['Librador'],
                        "Importe": float(r['Importe']),
                        "Vencimiento": r['Fecha Vencimiento'],
                        "Días": d,
                        "Estado": r['Estado']
                    })

        if filas_venc:
            df_venc = pd.DataFrame(filas_venc).sort_values("Días")
            total_emit_pend = df_venc[df_venc['Tipo'] == '📤 EMITIDO']['Importe'].sum()
            total_cart_pend = df_venc[df_venc['Tipo'] == '📂 CARTERA']['Importe'].sum()

            kv1, kv2, kv3 = st.columns(3)
            kv1.metric("Total cheques", len(df_venc))
            kv2.metric("📤 A pagar (emitidos)", f"$ {total_emit_pend:,.2f}")
            kv3.metric("📂 A cobrar/depositar", f"$ {total_cart_pend:,.2f}")
            st.markdown("---")

            for _, r in df_venc.iterrows():
                if r['Días'] < 0:
                    color_d = "#e74c3c"; label_d = f"VENCIDO hace {abs(int(r['Días']))}d"
                elif r['Días'] == 0:
                    color_d = "#e74c3c"; label_d = "VENCE HOY"
                elif r['Días'] <= 3:
                    color_d = "#e74c3c"; label_d = f"Vence en {int(r['Días'])}d"
                elif r['Días'] <= 7:
                    color_d = "#f39c12"; label_d = f"Vence en {int(r['Días'])}d"
                else:
                    color_d = "#2ecc71"; label_d = f"Vence en {int(r['Días'])}d"

                st.markdown(
                    f"<div style='background:#f8f9fa;border-radius:8px;padding:12px 16px;margin-bottom:8px;"
                    f"border-left:5px solid {color_d};display:flex;justify-content:space-between;align-items:center;'>"
                    f"<div>{r['Tipo']} &nbsp; <b>#{r['Nro Cheque']}</b> &nbsp;·&nbsp; {r['Modalidad']} &nbsp;·&nbsp; {r['Banco']}<br>"
                    f"Contraparte: <b>{r['Contraparte']}</b> &nbsp;·&nbsp; Vence: <b>{r['Vencimiento']}</b></div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-size:18px;font-weight:bold;color:#5e2d61;'>$ {r['Importe']:,.2f}</div>"
                    f"<div style='font-size:13px;font-weight:bold;color:{color_d};'>{label_d}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
        else:
            st.success(f"✅ No hay cheques con vencimiento en los próximos {dias_filtro} días.")
