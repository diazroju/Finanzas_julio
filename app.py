import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import database

st.set_page_config(page_title="Finanzas Julio", page_icon="💰", layout="centered")

def fmt(n):
    if not n:
        return "$0"
    return f"${float(n):,.0f}".replace(",", ".")

def get_df(sql, params=()):
    rows, cols = database.consultar(sql, params)
    return pd.DataFrame(rows, columns=cols)

def meses():
    rows, _ = database.consultar("SELECT DISTINCT mes FROM gastos_casa ORDER BY mes DESC")
    return [r[0] for r in rows] or [date.today().strftime("%Y-%m")]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("💰 Finanzas Julio")
mes_lista = meses()
mes_sel   = st.sidebar.selectbox("Mes", mes_lista)
pagina    = st.sidebar.radio("Sección", ["📊 Resumen", "📈 Comparación", "🏠 Gastos Casa", "➕ Agregar"])

# ═══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Resumen":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("📊 Resumen del mes")

    df_casa = get_df("SELECT * FROM gastos_casa WHERE mes=%s AND activo=1", (mes_sel,))
    df_mov  = get_df("SELECT * FROM movimientos WHERE fecha LIKE %s", (f"{mes_sel}%",))

    if df_casa.empty and df_mov.empty:
        st.info("No hay datos. Ve a '🏠 Gastos Casa' para agregar.")
        st.stop()

    total_casa = df_casa["monto_total"].sum() if not df_casa.empty else 0
    julio_casa = df_casa["aporte_julio"].sum() if not df_casa.empty else 0
    paula_casa = df_casa["aporte_paula"].sum() if not df_casa.empty else 0

    gastos_personal = df_mov[df_mov["tipo"] == "gasto"]["monto"].sum() if not df_mov.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Total Casa",   fmt(total_casa))
    col2.metric("👤 Julio aporta", fmt(julio_casa))
    col3.metric("👩 Paula aporta", fmt(paula_casa))

    st.divider()

    fig = go.Figure(go.Pie(
        labels=["Julio", "Paula"],
        values=[julio_casa, paula_casa],
        hole=0.5,
        marker_colors=["#3498db", "#e91e8c"]
    ))
    fig.update_layout(title="Distribución de aportes", height=280, margin=dict(t=40,b=0,l=0,r=0))
    st.plotly_chart(fig, use_container_width=True)

    if not df_casa.empty:
        st.subheader("Por categoría")
        tipo_df = df_casa.groupby("tipo")["monto_total"].sum().reset_index()
        tipo_df.columns = ["Tipo", "Total"]
        tipo_df["Tipo"] = tipo_df["Tipo"].str.capitalize()
        tipo_df["Pct"] = (tipo_df["Total"] / tipo_df["Total"].sum() * 100).round(1)
        tipo_df["Label"] = tipo_df.apply(lambda r: f"${r['Total']:,.0f}<br>{r['Pct']}%".replace(",", "."), axis=1)
        fig2 = px.bar(tipo_df, x="Tipo", y="Total", color="Tipo",
                      color_discrete_sequence=["#3498db","#2ecc71","#e74c3c"],
                      text="Label")
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False, margin=dict(t=40, b=0),
                           yaxis=dict(range=[0, tipo_df["Total"].max() * 1.2]))
        st.plotly_chart(fig2, use_container_width=True)

    if not df_mov.empty:
        st.subheader("Mis gastos personales")
        ingresos = df_mov[df_mov["tipo"]=="ingreso"]["monto"].sum()
        col1, col2 = st.columns(2)
        col1.metric("Ingresos", fmt(ingresos))
        col2.metric("Gastos",   fmt(gastos_personal))

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "📈 Comparación":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("📈 Comparación por mes")

    df_todo = get_df("SELECT mes, nombre, monto_total FROM gastos_casa WHERE activo=1 ORDER BY mes")

    if df_todo.empty or df_todo["mes"].nunique() < 2:
        st.info("Necesitas al menos 2 meses de datos para ver comparaciones. Agrega los gastos del mes siguiente en '🏠 Gastos Casa'.")
        st.stop()

    # Gráfica total por mes
    total_mes = df_todo.groupby("mes")["monto_total"].sum().reset_index()
    total_mes.columns = ["Mes", "Total"]
    total_mes["Variación"] = total_mes["Total"].diff().fillna(0)
    total_mes["Color"] = total_mes["Variación"].apply(lambda x: "Subió" if x > 0 else ("Bajó" if x < 0 else "Igual"))

    st.subheader("Total gastos por mes")
    fig1 = px.bar(total_mes, x="Mes", y="Total", color="Color",
                  color_discrete_map={"Subió": "#e74c3c", "Bajó": "#2ecc71", "Igual": "#95a5a6"},
                  text_auto=False)
    fig1.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
    fig1.update_layout(showlegend=True, margin=dict(t=20, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    # Tabla de variación
    if len(total_mes) >= 2:
        ultimo  = total_mes.iloc[-1]
        penult  = total_mes.iloc[-2]
        delta   = ultimo["Total"] - penult["Total"]
        st.metric(
            label=f"Cambio vs {penult['Mes']}",
            value=fmt(ultimo["Total"]),
            delta=f"{'+'if delta>0 else ''}{fmt(delta)}",
            delta_color="inverse"
        )

    st.divider()

    # Comparación por categoría entre los últimos 2 meses
    st.subheader("Por categoría — últimos 2 meses")
    meses_disp = sorted(df_todo["mes"].unique())
    if len(meses_disp) >= 2:
        m1, m2 = meses_disp[-2], meses_disp[-1]
        df_m1 = df_todo[df_todo["mes"] == m1].set_index("nombre")["monto_total"]
        df_m2 = df_todo[df_todo["mes"] == m2].set_index("nombre")["monto_total"]
        comp  = pd.DataFrame({"Anterior": df_m1, "Actual": df_m2}).fillna(0).reset_index()
        comp.columns = ["Concepto", m1, m2]
        comp["Δ"] = comp[m2] - comp[m1]
        comp["Cambio"] = comp["Δ"].apply(lambda x: f"+{fmt(x)}" if x > 0 else fmt(x))

        fig2 = px.bar(comp.melt(id_vars="Concepto", value_vars=[m1, m2], var_name="Mes", value_name="Monto"),
                      x="Concepto", y="Monto", color="Mes", barmode="group",
                      color_discrete_sequence=["#95a5a6", "#3498db"])
        fig2.update_layout(margin=dict(t=20, b=0), xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Detalle de cambios")
        tabla = comp[["Concepto", m1, m2, "Cambio"]].copy()
        tabla[m1] = tabla[m1].apply(fmt)
        tabla[m2] = tabla[m2].apply(fmt)
        st.dataframe(tabla, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "🏠 Gastos Casa":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("🏠 Gastos CASITA MADRIGAL")
    st.subheader(f"Mes: {mes_sel}")

    df = get_df("SELECT * FROM gastos_casa WHERE mes=%s AND activo=1 ORDER BY tipo, id", (mes_sel,))

    if df.empty:
        st.info("No hay gastos para este mes.")
    else:
        for tipo in ["fijo", "variable", "ahorro"]:
            sub = df[df["tipo"] == tipo].copy()
            if sub.empty:
                continue
            titulo = {"fijo": "📌 Gastos Fijos", "variable": "📊 Gastos Variables", "ahorro": "💾 Ahorros"}
            st.subheader(titulo[tipo])

            col_cfg = {
                "Total": st.column_config.NumberColumn("Total ($)", format="$ %d"),
                "Julio": st.column_config.NumberColumn("Julio ($)", format="$ %d"),
                "Paula": st.column_config.NumberColumn("Paula ($)", format="$ %d"),
            }
            edited = st.data_editor(
                sub[["id","nombre","monto_total","aporte_julio","aporte_paula"]].rename(columns={
                    "nombre":"Concepto","monto_total":"Total","aporte_julio":"Julio","aporte_paula":"Paula"
                }),
                hide_index=True, use_container_width=True, disabled=["id"],
                column_config=col_cfg,
                key=f"ed_{tipo}_{mes_sel}"
            )

            if st.button(f"💾 Guardar {tipo}s", key=f"sv_{tipo}"):
                for _, r in edited.iterrows():
                    database.ejecutar(
                        "UPDATE gastos_casa SET nombre=%s, monto_total=%s, aporte_julio=%s, aporte_paula=%s WHERE id=%s",
                        (r["Concepto"], r["Total"], r["Julio"], r["Paula"], r["id"])
                    )
                st.success("Guardado.")
                st.rerun()

            j = sub["aporte_julio"].sum()
            p = sub["aporte_paula"].sum()
            st.caption(f"Total: {fmt(sub['monto_total'].sum())} | Julio: {fmt(j)} | Paula: {fmt(p)}")
            st.divider()

        total = df["monto_total"].sum()
        j_tot = df["aporte_julio"].sum()
        p_tot = df["aporte_paula"].sum()
        st.markdown(f"**TOTAL MES: {fmt(total)}** | Julio: {fmt(j_tot)} ({round(j_tot/total*100)}%) | Paula: {fmt(p_tot)} ({round(p_tot/total*100)}%)")

    st.divider()
    st.subheader("➕ Agregar gasto")
    with st.form("nuevo"):
        col1, col2 = st.columns(2)
        nombre  = col1.text_input("Concepto")
        tipo_g  = col2.selectbox("Tipo", ["fijo","variable","ahorro"])
        total_g = st.number_input("Monto total ($)", min_value=0, step=10000)
        col3, col4 = st.columns(2)
        julio_g = col3.number_input("Aporte Julio", min_value=0, step=10000, value=int(total_g//2))
        paula_g = col4.number_input("Aporte Paula", min_value=0, step=10000, value=int(total_g//2))
        if st.form_submit_button("Agregar") and nombre:
            database.ejecutar(
                "INSERT INTO gastos_casa (mes,nombre,tipo,monto_total,aporte_julio,aporte_paula) VALUES (%s,%s,%s,%s,%s,%s)",
                (mes_sel, nombre, tipo_g, total_g, julio_g, paula_g)
            )
            st.success(f"'{nombre}' agregado.")
            st.rerun()

    if not df.empty:
        st.subheader("🗑 Eliminar gasto")
        a_borrar = st.selectbox("Selecciona", df["nombre"].tolist())
        if st.button("Eliminar"):
            database.ejecutar("UPDATE gastos_casa SET activo=0 WHERE mes=%s AND nombre=%s", (mes_sel, a_borrar))
            st.success(f"'{a_borrar}' eliminado.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "➕ Agregar":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("➕ Registrar movimiento")
    st.info("También puedes escribirle al bot en Telegram.")

    with st.form("mov"):
        tipo  = st.radio("Tipo", ["gasto","ingreso"], horizontal=True)
        monto = st.number_input("Monto ($)", min_value=0, step=10000)
        cat   = st.selectbox("Categoría", ["mercado","restaurante","transporte","servicios","arriendo","salud","educacion","ocio","otros"])
        nota  = st.text_input("Nota (opcional)")
        fecha = st.date_input("Fecha", value=date.today())
        if st.form_submit_button("Registrar") and monto > 0:
            database.ejecutar(
                "INSERT INTO movimientos (fecha,tipo,monto,categoria,nota) VALUES (%s,%s,%s,%s,%s)",
                (fecha.isoformat(), tipo, monto, cat, nota)
            )
            st.success(f"Registrado: {fmt(monto)} en {cat}")
