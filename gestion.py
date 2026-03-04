elif sel == "FACTURAS":
    import json as _json

    st.header("🧾 Facturación de Ventas")

    TIPOS_COMP_VENTA = [
        "Factura A", "Factura B", "Factura C",
        "Nota de Crédito A", "Nota de Crédito B", "Nota de Crédito C",
        "Nota de Débito A",  "Nota de Débito B",  "Nota de Débito C",
        "Remito"
    ]
    ALICUOTAS = ["21%", "10.5%", "Exento / No Gravado"]

    if "fv_items" not in st.session_state:
        st.session_state.fv_items = [{"descripcion":"","cantidad":1.0,"precio_unit":0.0,"alicuota":"21%"}]
    if "fv_html_ready" not in st.session_state:
        st.session_state.fv_html_ready    = None
        st.session_state.fv_cliente_ready = None
    if 'facturas_ventas' not in st.session_state:
        st.session_state.facturas_ventas = pd.DataFrame(columns=COL_FACTURAS_VENTAS)

    tab_nueva, tab_hist = st.tabs(["🆕 Nueva Factura", "📂 Historial de Facturas"])

    with tab_nueva:

        if st.session_state.fv_html_ready:
            st.success(f"✅ Factura emitida para **{st.session_state.fv_cliente_ready}** registrada correctamente.")
            st.download_button(
                "🖨️ IMPRIMIR / DESCARGAR FACTURA",
                st.session_state.fv_html_ready,
                file_name=f"Factura_{st.session_state.fv_cliente_ready}_{date.today()}.html",
                mime="text/html"
            )
            if st.button("➕ Nueva Factura"):
                st.session_state.fv_html_ready    = None
                st.session_state.fv_cliente_ready = None
                st.session_state.fv_items = [{"descripcion":"","cantidad":1.0,"precio_unit":0.0,"alicuota":"21%"}]
                st.rerun()
        else:
            st.markdown("#### 📋 Datos del Comprobante")
            fv_c1, fv_c2, fv_c3, fv_c4 = st.columns([1.4, 0.7, 0.9, 1.0])
            fv_tipo  = fv_c1.selectbox("Tipo de Comprobante", TIPOS_COMP_VENTA, key="fv_tipo")
            fv_pv    = fv_c2.text_input("Punto de Venta", value="0001", key="fv_pv")
            fv_nro   = fv_c3.text_input("Número", value="00000001", key="fv_nro")
            fv_fecha = fv_c4.date_input("Fecha de Emisión", value=date.today(), key="fv_fecha")

            st.markdown("---")
            st.markdown("#### 👤 Datos del Cliente")
            fv_cc1, fv_cc2 = st.columns(2)

            clientes_lista = st.session_state.clientes['Razón Social'].unique().tolist() if not st.session_state.clientes.empty else [""]
            fv_cliente = fv_cc1.selectbox("Cliente", clientes_lista, key="fv_cliente")
            fv_cond_pago = fv_cc2.selectbox("Condición de Pago", ["Contado","Cuenta Corriente","30 días","60 días","90 días"], key="fv_cond_pago")

            # Autocompletar datos del cliente
            cuit_cli = "-"; cond_iva_cli = "-"; dom_cli = "-"
            if not st.session_state.clientes.empty and fv_cliente in st.session_state.clientes['Razón Social'].values:
                cr = st.session_state.clientes[st.session_state.clientes['Razón Social'] == fv_cliente].iloc[0]
                cuit_cli     = cr.get('CUIT / CUIL / DNI *', '-')
                cond_iva_cli = cr.get('Condición IVA', '-')
                dom_cli      = f"{cr.get('Dirección Fiscal','')} - {cr.get('Localidad','')}, {cr.get('Provincia','')}"

            st.caption(f"CUIT: **{cuit_cli}** &nbsp;·&nbsp; IVA: **{cond_iva_cli}** &nbsp;·&nbsp; {dom_cli}")

            st.markdown("---")
            st.markdown("#### 📦 Ítems del Comprobante")

            col_add, col_del, _ = st.columns([0.18, 0.18, 0.64])
            if col_add.button("➕ Agregar ítem"):
                st.session_state.fv_items.append({"descripcion":"","cantidad":1.0,"precio_unit":0.0,"alicuota":"21%"})
                st.rerun()
            if len(st.session_state.fv_items) > 1:
                if col_del.button("➖ Quitar último"):
                    st.session_state.fv_items.pop()
                    st.rerun()

            # Encabezados de columnas
            hd1, hd2, hd3, hd4 = st.columns([2.5, 0.6, 1.1, 0.8])
            hd1.markdown("**Descripción**")
            hd2.markdown("**Cantidad**")
            hd3.markdown("**Precio Unit.**")
            hd4.markdown("**Alíc. IVA**")

            for idx, item in enumerate(st.session_state.fv_items):
                ic1, ic2, ic3, ic4 = st.columns([2.5, 0.6, 1.1, 0.8])
                item['descripcion'] = ic1.text_input(f"desc_{idx}", value=item['descripcion'],        key=f"fv_desc_{idx}", label_visibility="collapsed")
                item['cantidad']    = ic2.number_input(f"cant_{idx}", value=float(item['cantidad']),  min_value=0.0, step=1.0,  key=f"fv_cant_{idx}", label_visibility="collapsed")
                item['precio_unit'] = ic3.number_input(f"pu_{idx}",   value=float(item['precio_unit']), min_value=0.0, step=0.01, key=f"fv_pu_{idx}",   label_visibility="collapsed")
                item['alicuota']    = ic4.selectbox(f"ali_{idx}", ALICUOTAS, index=ALICUOTAS.index(item.get('alicuota','21%')), key=f"fv_ali_{idx}", label_visibility="collapsed")

            st.markdown("---")

            # Totales en tiempo real
            neto_21  = sum(float(it['cantidad']) * float(it['precio_unit']) for it in st.session_state.fv_items if it['alicuota'] == "21%")
            neto_105 = sum(float(it['cantidad']) * float(it['precio_unit']) for it in st.session_state.fv_items if it['alicuota'] == "10.5%")
            exento   = sum(float(it['cantidad']) * float(it['precio_unit']) for it in st.session_state.fv_items if it['alicuota'] == "Exento / No Gravado")
            iva_21   = neto_21  * 0.21
            iva_105  = neto_105 * 0.105
            total_fv = neto_21 + neto_105 + exento + iva_21 + iva_105
            if "Nota de Crédito" in fv_tipo:
                total_fv = -abs(total_fv)

            kt1, kt2, kt3, kt4 = st.columns(4)
            kt1.metric("Neto 21%",   f"$ {neto_21:,.2f}")
            kt2.metric("Neto 10.5%", f"$ {neto_105:,.2f}")
            kt3.metric("IVA Total",  f"$ {iva_21+iva_105:,.2f}")
            kt4.metric("TOTAL",      f"$ {abs(total_fv):,.2f}")

            fv_obs = st.text_area("Observaciones (opcional)", key="fv_obs", height=60)

            st.markdown("---")
            if st.button("✅ EMITIR FACTURA", type="primary"):
                if not fv_cliente:
                    st.warning("Seleccioná un cliente.")
                elif total_fv == 0:
                    st.warning("El total no puede ser cero.")
                else:
                    data_fv = {
                        "Fecha": str(fv_fecha), "Tipo Comp": fv_tipo,
                        "Punto Venta": fv_pv, "Nro Factura": fv_nro,
                        "Cliente": fv_cliente, "CUIT Cliente": cuit_cli,
                        "Condicion IVA Cliente": cond_iva_cli,
                        "Condicion Pago": fv_cond_pago,
                        "Items": _json.dumps(st.session_state.fv_items, ensure_ascii=False),
                        "Neto Gravado 21": round(neto_21, 2),
                        "Neto Gravado 105": round(neto_105, 2),
                        "Exento": round(exento, 2),
                        "IVA 21": round(iva_21, 2),
                        "IVA 105": round(iva_105, 2),
                        "Total": round(total_fv, 2),
                        "Estado": "EMITIDA",
                        "Observaciones": fv_obs,
                        "domicilio_cliente": dom_cli,
                    }
                    nueva_fv = pd.DataFrame([[
                        data_fv["Fecha"], data_fv["Tipo Comp"], data_fv["Punto Venta"], data_fv["Nro Factura"],
                        data_fv["Cliente"], data_fv["CUIT Cliente"], data_fv["Condicion IVA Cliente"],
                        data_fv["Condicion Pago"], data_fv["Items"],
                        data_fv["Neto Gravado 21"], data_fv["Neto Gravado 105"], data_fv["Exento"],
                        data_fv["IVA 21"], data_fv["IVA 105"], data_fv["Total"],
                        "EMITIDA", fv_obs
                    ]], columns=COL_FACTURAS_VENTAS)
                    st.session_state.facturas_ventas = pd.concat([st.session_state.facturas_ventas, nueva_fv], ignore_index=True)
                    guardar_datos("facturas_ventas", st.session_state.facturas_ventas)

                    # Impactar en cuenta corriente del cliente (si no es Remito ni NC)
                    if fv_tipo not in ["Remito"] and "Nota de Crédito" not in fv_tipo:
                        nv_fv = pd.DataFrame([[
                            date.today(), fv_cliente, fv_fecha,
                            f"Factura {fv_pv}-{fv_nro}", "FACTURACION",
                            fv_pv, total_fv, fv_tipo, f"{fv_pv}-{fv_nro}"
                        ]], columns=COL_VIAJES)
                        st.session_state.viajes = pd.concat([st.session_state.viajes, nv_fv], ignore_index=True)
                        guardar_datos("viajes", st.session_state.viajes)

                    st.session_state.fv_html_ready    = generar_html_factura(data_fv, st.session_state.fv_items)
                    st.session_state.fv_cliente_ready = fv_cliente
                    st.session_state.fv_items = [{"descripcion":"","cantidad":1.0,"precio_unit":0.0,"alicuota":"21%"}]
                    st.rerun()

    # ── TAB HISTORIAL ──
    with tab_hist:
        if st.session_state.facturas_ventas.empty:
            st.info("No hay facturas emitidas aún.")
        else:
            df_fh = st.session_state.facturas_ventas.copy()

            hf1, hf2, hf3 = st.columns(3)
            f_cli  = hf1.selectbox("Cliente",  ["(Todos)"] + sorted(df_fh['Cliente'].unique().tolist()),   key="fv_f_cli")
            f_tipo = hf2.selectbox("Tipo",     ["(Todos)"] + TIPOS_COMP_VENTA,                             key="fv_f_tipo")
            f_est  = hf3.selectbox("Estado",   ["(Todos)", "EMITIDA", "COBRADA", "ANULADA"],               key="fv_f_est")

            if f_cli  != "(Todos)": df_fh = df_fh[df_fh['Cliente']   == f_cli]
            if f_tipo != "(Todos)": df_fh = df_fh[df_fh['Tipo Comp'] == f_tipo]
            if f_est  != "(Todos)": df_fh = df_fh[df_fh['Estado']    == f_est]

            hm1, hm2, hm3 = st.columns(3)
            hm1.metric("Comprobantes", len(df_fh))
            hm2.metric("Total Facturado", f"$ {df_fh['Total'].sum():,.2f}")
            hm3.metric("IVA Total", f"$ {(df_fh['IVA 21'] + df_fh['IVA 105']).sum():,.2f}")
            st.markdown("---")

            COLOR_EST = {"EMITIDA":"#3498db","COBRADA":"#2ecc71","ANULADA":"#e74c3c"}
            for idx in reversed(df_fh.index):
                row_fv = st.session_state.facturas_ventas.loc[idx]
                est    = row_fv['Estado']
                c_est  = COLOR_EST.get(est, "#888")
                try:
                    items_h = _json.loads(row_fv['Items']) if str(row_fv['Items']) not in ['-','','None'] else []
                except:
                    items_h = []
                data_h = dict(row_fv)
                data_h['domicilio_cliente'] = '-'

                with st.container():
                    hc1, hc2, hc3 = st.columns([0.55, 0.25, 0.20])
                    hc1.markdown(
                        f"**{row_fv['Tipo Comp']}** &nbsp; "
                        f"N° {str(row_fv['Punto Venta']).zfill(4)}-{str(row_fv['Nro Factura']).zfill(8)} "
                        f"&nbsp;·&nbsp; {row_fv['Fecha']}<br>"
                        f"👤 {row_fv['Cliente']} &nbsp;·&nbsp; {row_fv['Condicion Pago']}",
                        unsafe_allow_html=True
                    )
                    hc2.markdown(
                        f"**$ {float(row_fv['Total']):,.2f}**<br>"
                        f"<span style='background:{c_est};color:white;padding:2px 9px;"
                        f"border-radius:10px;font-size:11px;font-weight:bold;'>{est}</span>",
                        unsafe_allow_html=True
                    )
                    with hc3:
                        html_h = generar_html_factura(data_h, items_h)
                        st.download_button("📄 Descargar", html_h,
                            file_name=f"{row_fv['Tipo Comp']}_{row_fv['Cliente']}_{row_fv['Fecha']}.html",
                            mime="text/html", key=f"dl_fv_{idx}")
                        if est == "EMITIDA":
                            if st.button("✅ Cobrada", key=f"cobrar_fv_{idx}"):
                                st.session_state.facturas_ventas.loc[idx,'Estado'] = 'COBRADA'
                                guardar_datos("facturas_ventas", st.session_state.facturas_ventas)
                                st.rerun()
                            if st.button("🗑️ Anular", key=f"anu_fv_{idx}"):
                                st.session_state.facturas_ventas.loc[idx,'Estado'] = 'ANULADA'
                                guardar_datos("facturas_ventas", st.session_state.facturas_ventas)
                                st.rerun()
                    st.divider()
