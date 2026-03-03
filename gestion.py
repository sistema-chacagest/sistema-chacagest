# ============================================================
# PASO 1: Agregar "DASHBOARD" al menú principal del sidebar
# ============================================================
# Buscá estas líneas en tu código (sección --- 5. SIDEBAR ---):
#
#   opciones_menu = ["CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
#   iconos_menu   = ["calendar3", "cart4", "bag-check", "safe"]
#
# Reemplazalas por:

opciones_menu = ["DASHBOARD", "CALENDARIO", "VENTAS", "COMPRAS", "TESORERIA"]
iconos_menu   = ["bar-chart-line", "calendar3", "cart4", "bag-check", "safe"]


# ============================================================
# PASO 2: Pegar este bloque completo en la sección --- 6. MÓDULOS ---
# Pegalo ANTES del bloque:  if sel == "CALENDARIO":
# ============================================================

if sel == "DASHBOARD":
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import calendar as cal_module

    st.header("📊 Dashboard de Control Financiero")

    # ── Preparar datos de INGRESOS (viajes con importe > 0) ──
    df_ing = st.session_state.viajes.copy()
    df_ing = df_ing[df_ing['Importe'] > 0].copy()
    df_ing['Fecha Viaje'] = pd.to_datetime(df_ing['Fecha Viaje'], errors='coerce')
    df_ing = df_ing.dropna(subset=['Fecha Viaje'])
    df_ing['Año']  = df_ing['Fecha Viaje'].dt.year
    df_ing['Mes']  = df_ing['Fecha Viaje'].dt.month
    df_ing['NombreMes'] = df_ing['Fecha Viaje'].dt.strftime('%b')

    # ── Preparar datos de GASTOS (compras con total > 0) ──
    df_gas = st.session_state.compras.copy()
    df_gas = df_gas[df_gas['Total'] > 0].copy()
    df_gas['Fecha'] = pd.to_datetime(df_gas['Fecha'], errors='coerce')
    df_gas = df_gas.dropna(subset=['Fecha'])
    df_gas['Año']  = df_gas['Fecha'].dt.year
    df_gas['Mes']  = df_gas['Fecha'].dt.month
    df_gas['NombreMes'] = df_gas['Fecha'].dt.strftime('%b')

    # Enriquecer gastos con la Cuenta de Gastos del proveedor
    df_gas = df_gas.merge(
        st.session_state.proveedores[['Razón Social', 'Cuenta de Gastos']],
        left_on='Proveedor', right_on='Razón Social', how='left'
    )
    df_gas['Cuenta de Gastos'] = df_gas['Cuenta de Gastos'].fillna('SIN CATEGORÍA')

    # ── Obtener años disponibles ──
    años_ing = set(df_ing['Año'].unique()) if not df_ing.empty else set()
    años_gas = set(df_gas['Año'].unique()) if not df_gas.empty else set()
    años_disp = sorted(años_ing | años_gas, reverse=True)
    if not años_disp:
        años_disp = [date.today().year]

    # ── Selector de Vista ──
    col_v1, col_v2, col_v3 = st.columns([1, 1, 2])
    vista = col_v1.radio("Vista", ["Mensual", "Anual"], horizontal=True)
    año_sel = col_v2.selectbox("Año", años_disp)

    mes_sel = None
    if vista == "Mensual":
        meses_nombres = {
            1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",
            5:"Mayo",6:"Junio",7:"Julio",8:"Agosto",
            9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
        }
        mes_sel = col_v3.selectbox(
            "Mes",
            options=list(meses_nombres.keys()),
            format_func=lambda x: meses_nombres[x],
            index=date.today().month - 1
        )

    # ── Filtrar según vista ──
    if vista == "Mensual":
        df_ing_f = df_ing[(df_ing['Año'] == año_sel) & (df_ing['Mes'] == mes_sel)]
        df_gas_f = df_gas[(df_gas['Año'] == año_sel) & (df_gas['Mes'] == mes_sel)]
        titulo_periodo = f"{meses_nombres[mes_sel]} {año_sel}"
    else:
        df_ing_f = df_ing[df_ing['Año'] == año_sel]
        df_gas_f = df_gas[df_gas['Año'] == año_sel]
        titulo_periodo = f"Año {año_sel}"

    total_ing = df_ing_f['Importe'].sum()
    total_gas = df_gas_f['Total'].sum()
    resultado = total_ing - total_gas

    st.markdown(f"### Período: {titulo_periodo}")
    st.markdown("---")

    # ── KPIs principales ──
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Ingresos",  f"$ {total_ing:,.0f}")
    k2.metric("💸 Total Gastos",    f"$ {total_gas:,.0f}")
    color_res = "normal" if resultado >= 0 else "inverse"
    k3.metric("📈 Resultado Neto",  f"$ {resultado:,.0f}", delta=f"{'▲' if resultado >= 0 else '▼'} {abs(resultado):,.0f}", delta_color=color_res)
    margen = (resultado / total_ing * 100) if total_ing > 0 else 0
    k4.metric("📊 Margen",          f"{margen:.1f} %")

    st.markdown("---")

    # =============================================================
    # GRÁFICO 1: Ingresos vs Gastos (barras por mes si Anual,
    #            o por semana si Mensual)
    # =============================================================
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        if vista == "Anual":
            # Agrupar por mes
            MESES_ORDEN = list(range(1, 13))
            MESES_LABEL = [cal_module.month_abbr[m] for m in MESES_ORDEN]

            ing_por_mes = df_ing_f.groupby('Mes')['Importe'].sum().reindex(MESES_ORDEN, fill_value=0)
            gas_por_mes = df_gas_f.groupby('Mes')['Total'].sum().reindex(MESES_ORDEN, fill_value=0)

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(name="Ingresos", x=MESES_LABEL, y=ing_por_mes.values,
                                  marker_color="#5e2d61", opacity=0.9))
            fig1.add_trace(go.Bar(name="Gastos",   x=MESES_LABEL, y=gas_por_mes.values,
                                  marker_color="#f39c12", opacity=0.9))
            fig1.update_layout(
                title=f"Ingresos vs Gastos — {año_sel}",
                barmode='group', plot_bgcolor='white',
                legend=dict(orientation="h", y=-0.2),
                yaxis_tickprefix="$", margin=dict(t=40, b=10)
            )
        else:
            # Agrupar por día dentro del mes
            df_ing_f2 = df_ing_f.copy()
            df_gas_f2 = df_gas_f.copy()
            df_ing_f2['Dia'] = df_ing_f2['Fecha Viaje'].dt.day
            df_gas_f2['Dia'] = df_gas_f2['Fecha'].dt.day

            dias_mes = cal_module.monthrange(año_sel, mes_sel)[1]
            todos_dias = list(range(1, dias_mes + 1))

            ing_por_dia = df_ing_f2.groupby('Dia')['Importe'].sum().reindex(todos_dias, fill_value=0)
            gas_por_dia = df_gas_f2.groupby('Dia')['Total'].sum().reindex(todos_dias, fill_value=0)

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(name="Ingresos", x=todos_dias, y=ing_por_dia.values,
                                  marker_color="#5e2d61", opacity=0.9))
            fig1.add_trace(go.Bar(name="Gastos",   x=todos_dias, y=gas_por_dia.values,
                                  marker_color="#f39c12", opacity=0.9))
            fig1.update_layout(
                title=f"Ingresos vs Gastos — {meses_nombres[mes_sel]} {año_sel}",
                barmode='group', plot_bgcolor='white',
                legend=dict(orientation="h", y=-0.2),
                xaxis_title="Día", yaxis_tickprefix="$",
                margin=dict(t=40, b=10)
            )

        st.plotly_chart(fig1, use_container_width=True)

    # =============================================================
    # GRÁFICO 2: Torta de Gastos por Cuenta de Gastos
    # =============================================================
    with col_g2:
        if not df_gas_f.empty:
            gas_por_cuenta = df_gas_f.groupby('Cuenta de Gastos')['Total'].sum().reset_index()
            gas_por_cuenta = gas_por_cuenta.sort_values('Total', ascending=False)

            COLORES_TORTA = [
                "#5e2d61", "#f39c12", "#d35400", "#2ecc71",
                "#3498db", "#e74c3c", "#9b59b6", "#1abc9c"
            ]

            fig2 = px.pie(
                gas_por_cuenta,
                values='Total',
                names='Cuenta de Gastos',
                title=f"Gastos por Categoría — {titulo_periodo}",
                color_discrete_sequence=COLORES_TORTA,
                hole=0.4
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(
                legend=dict(orientation="h", y=-0.2),
                margin=dict(t=40, b=10)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin gastos registrados para el período seleccionado.")

    # =============================================================
    # GRÁFICO 3 (Anual): Línea de tendencia de resultado neto
    # GRÁFICO 3 (Mensual): Top 5 clientes por ingreso
    # =============================================================
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        if vista == "Anual":
            ing_mes = df_ing_f.groupby('Mes')['Importe'].sum().reindex(MESES_ORDEN, fill_value=0)
            gas_mes = df_gas_f.groupby('Mes')['Total'].sum().reindex(MESES_ORDEN, fill_value=0)
            resultado_mes = ing_mes - gas_mes

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=MESES_LABEL, y=resultado_mes.values,
                mode='lines+markers+text',
                text=[f"${v:,.0f}" for v in resultado_mes.values],
                textposition="top center",
                line=dict(color="#5e2d61", width=3),
                marker=dict(size=8, color="#f39c12"),
                fill='tozeroy',
                fillcolor='rgba(94,45,97,0.1)',
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
            # Top clientes del mes
            if not df_ing_f.empty:
                top_cli = df_ing_f.groupby('Cliente')['Importe'].sum().reset_index()
                top_cli = top_cli.sort_values('Importe', ascending=True).tail(5)
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

    # =============================================================
    # GRÁFICO 4: Detalle de gastos por categoría (barras horizontales)
    # =============================================================
    with col_g4:
        if not df_gas_f.empty:
            if vista == "Anual":
                # Mapa de calor: categoría vs mes
                pivot = df_gas_f.pivot_table(
                    index='Cuenta de Gastos', columns='Mes',
                    values='Total', aggfunc='sum', fill_value=0
                )
                pivot.columns = [cal_module.month_abbr[m] for m in pivot.columns]
                fig4 = px.imshow(
                    pivot,
                    color_continuous_scale=[[0, "#fff4e6"], [0.5, "#f39c12"], [1, "#d35400"]],
                    title="Mapa de Gastos por Categoría y Mes",
                    text_auto=True,
                    aspect="auto"
                )
                fig4.update_layout(margin=dict(t=40, b=10))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                gas_cuenta = df_gas_f.groupby('Cuenta de Gastos')['Total'].sum().reset_index()
                gas_cuenta = gas_cuenta.sort_values('Total', ascending=True)
                fig4 = go.Figure(go.Bar(
                    x=gas_cuenta['Total'], y=gas_cuenta['Cuenta de Gastos'],
                    orientation='h', marker_color="#f39c12",
                    text=[f"$ {v:,.0f}" for v in gas_cuenta['Total']],
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

    # =============================================================
    # TABLA RESUMEN al pie
    # =============================================================
    st.markdown("---")
    st.subheader("📋 Resumen Detallado por Categoría de Gasto")

    if not df_gas_f.empty:
        resumen_cat = df_gas_f.groupby('Cuenta de Gastos')['Total'].agg(
            Total='sum', Cantidad='count'
        ).reset_index()
        resumen_cat['% del Total'] = (resumen_cat['Total'] / resumen_cat['Total'].sum() * 100).round(1)
        resumen_cat = resumen_cat.sort_values('Total', ascending=False)
        resumen_cat['Total'] = resumen_cat['Total'].apply(lambda x: f"$ {x:,.2f}")
        resumen_cat['% del Total'] = resumen_cat['% del Total'].apply(lambda x: f"{x} %")
        resumen_cat.columns = ['Cuenta de Gastos', 'Total Gastado', 'N° Comprobantes', '% del Total']
        st.dataframe(resumen_cat, use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de gastos para el período.")

    # ── Pie de página con fecha de actualización ──
    st.caption(f"Última actualización: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} hs")
