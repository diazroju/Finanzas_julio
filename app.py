import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import database

st.set_page_config(page_title="Finanzas Julio", page_icon="💎", layout="centered")

st.markdown("""
<style>
/* Sidebar limpia */
[data-testid="stSidebar"] { background: #f8fafc; border-right: 1px solid #e2e8f0; }
/* Métricas con tarjeta */
[data-testid="stMetric"] {
    background: #f8fafc; border-radius: 12px;
    padding: 16px 20px; border: 1px solid #e2e8f0;
}
/* Títulos más limpios */
h1 { font-weight: 700; letter-spacing: -0.5px; }
h2 { font-weight: 600; color: #475569; font-size: 1.1rem !important; text-transform: uppercase; letter-spacing: 0.5px; }
/* Tablas */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
/* Botones */
.stButton > button { border-radius: 8px; font-weight: 500; }
/* Expander */
[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 10px; }
/* Divider más sutil */
hr { border-color: #f1f5f9 !important; }
</style>
""", unsafe_allow_html=True)

def fmt(n):
    if not n:
        return "$0"
    return f"${float(n):,.0f}".replace(",", ".")

def parse_monto(s):
    try:
        return int(str(s).replace("$","").replace(".","").replace(",","").strip())
    except Exception:
        return 0

def get_df(sql, params=()):
    rows, cols = database.consultar(sql, params)
    return pd.DataFrame(rows, columns=cols)

MESES_ES = {
    "01":"Enero","02":"Febrero","03":"Marzo","04":"Abril",
    "05":"Mayo","06":"Junio","07":"Julio","08":"Agosto",
    "09":"Septiembre","10":"Octubre","11":"Noviembre","12":"Diciembre"
}

def fmt_mes(m):
    partes = m.split("-")
    return f"{MESES_ES.get(partes[1], partes[1])}-{partes[0]}"

def meses():
    rows, _ = database.consultar("SELECT DISTINCT mes FROM gastos_casa ORDER BY mes DESC")
    return [r[0] for r in rows] or [date.today().strftime("%Y-%m")]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("💎 Finanzas Julio")
mes_lista = meses()
mes_sel   = st.sidebar.selectbox("Mes", mes_lista, format_func=fmt_mes)
pagina    = st.sidebar.radio("Vista", ["Resumen", "Comparación", "Casa Madrigal", "Registrar"])

# ═══════════════════════════════════════════════════════════════════════════════
if pagina == "Resumen":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("Resumen del mes")

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
        marker_colors=["#94a3b8", "#6366f1"],
        textfont=dict(color="white")
    ))
    fig.update_layout(title="Distribución de aportes", height=280, margin=dict(t=40,b=0,l=0,r=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    if not df_casa.empty:
        st.subheader("Por categoría")
        tipo_df = df_casa.groupby("tipo")["monto_total"].sum().reset_index()
        tipo_df.columns = ["Tipo", "Total"]
        tipo_df["Tipo"] = tipo_df["Tipo"].str.capitalize()
        tipo_df["Pct"] = (tipo_df["Total"] / tipo_df["Total"].sum() * 100).round(1)
        tipo_df["Label"] = tipo_df.apply(lambda r: f"${r['Total']:,.0f}<br>{r['Pct']}%".replace(",", "."), axis=1)
        fig2 = px.bar(tipo_df, x="Tipo", y="Total", color="Tipo",
                      color_discrete_sequence=["#1e3a5f", "#6366f1", "#cbd5e1"],
                      text="Label")
        fig2.update_traces(textposition="outside", textfont=dict(color="#1e293b"))
        fig2.update_layout(showlegend=False, margin=dict(t=40, b=0),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(range=[0, tipo_df["Total"].max() * 1.25], showgrid=True, gridcolor="#f1f5f9"))
        st.plotly_chart(fig2, use_container_width=True)

    if not df_mov.empty:
        st.subheader("Mis gastos personales")
        ingresos = df_mov[df_mov["tipo"]=="ingreso"]["monto"].sum()
        col1, col2 = st.columns(2)
        col1.metric("Ingresos", fmt(ingresos))
        col2.metric("Gastos",   fmt(gastos_personal))

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "Comparación":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("Comparación por mes")

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
                  color_discrete_map={"Subió": "#6366f1", "Bajó": "#1e3a5f", "Igual": "#cbd5e1"},
                  text_auto=False)
    fig1.update_traces(texttemplate="$%{y:,.0f}", textposition="outside", textfont=dict(color="#1e293b"))
    fig1.update_layout(showlegend=True, margin=dict(t=20, b=0),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       yaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
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
                      color_discrete_sequence=["#cbd5e1", "#6366f1"])
        fig2.update_layout(margin=dict(t=20, b=0), xaxis_tickangle=-45,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           yaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Detalle de cambios")
        tabla = comp[["Concepto", m1, m2, "Cambio"]].copy()
        tabla[m1] = tabla[m1].apply(fmt)
        tabla[m2] = tabla[m2].apply(fmt)
        st.dataframe(tabla, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "Casa Madrigal":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("Casa Madrigal")
    st.subheader(fmt_mes(mes_sel))

    df = get_df("SELECT * FROM gastos_casa WHERE mes=%s AND activo=1 ORDER BY tipo, id", (mes_sel,))

    if df.empty:
        st.info("No hay gastos para este mes.")
    else:
        for tipo in ["fijo", "variable", "ahorro"]:
            sub = df[df["tipo"] == tipo].copy()
            if sub.empty:
                continue
            titulo = {"fijo": "Gastos Fijos", "variable": "Gastos Variables", "ahorro": "Ahorros"}
            st.subheader(titulo[tipo])

            disp = sub[["nombre","monto_total","aporte_julio","aporte_paula"]].copy()
            disp.columns = ["Concepto","Total","Julio","Paula"]
            disp["Total"] = disp["Total"].apply(fmt)
            disp["Julio"] = disp["Julio"].apply(fmt)
            disp["Paula"] = disp["Paula"].apply(fmt)
            st.dataframe(disp, hide_index=True, use_container_width=True)

            with st.expander("✏️ Editar valores"):
                edit_df = sub[["id","nombre","monto_total","aporte_julio","aporte_paula"]].copy()
                edit_df["monto_total"]  = edit_df["monto_total"].apply(fmt)
                edit_df["aporte_julio"] = edit_df["aporte_julio"].apply(fmt)
                edit_df["aporte_paula"] = edit_df["aporte_paula"].apply(fmt)
                edit_df = edit_df.rename(columns={"nombre":"Concepto","monto_total":"Total","aporte_julio":"Julio","aporte_paula":"Paula"})
                edited = st.data_editor(
                    edit_df,
                    hide_index=True, use_container_width=True, disabled=["id"],
                    key=f"ed_{tipo}_{mes_sel}"
                )
                if st.button(f"💾 Guardar {tipo}s", key=f"sv_{tipo}"):
                    for _, r in edited.iterrows():
                        database.ejecutar(
                            "UPDATE gastos_casa SET nombre=%s, monto_total=%s, aporte_julio=%s, aporte_paula=%s WHERE id=%s",
                            (r["Concepto"], parse_monto(r["Total"]), parse_monto(r["Julio"]), parse_monto(r["Paula"]), r["id"])
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

    # ── DISTRIBUIR APORTES ────────────────────────────────────────────────────
    st.subheader("Distribuir aportes del mes")
    col_a, col_b = st.columns(2)
    julio_pct = col_a.number_input("% Julio", min_value=0, max_value=100, value=50, step=1)
    paula_pct = col_b.number_input("% Paula", min_value=0, max_value=100, value=50, step=1)
    suma = julio_pct + paula_pct
    if suma != 100:
        st.warning(f"Los porcentajes suman {suma}% — deben sumar 100%.")
    else:
        if st.button("Aplicar a todos los gastos del mes"):
            rows, _ = database.consultar("SELECT id, monto_total FROM gastos_casa WHERE mes=%s AND activo=1", (mes_sel,))
            for rid, monto_t in rows:
                j = round(monto_t * julio_pct / 100)
                p = monto_t - j
                database.ejecutar("UPDATE gastos_casa SET aporte_julio=%s, aporte_paula=%s WHERE id=%s", (j, p, rid))
            st.success(f"Aportes actualizados: Julio {julio_pct}% / Paula {paula_pct}%")
            st.rerun()

    st.divider()
    st.subheader("Agregar gasto")
    with st.form("nuevo"):
        col1, col2 = st.columns(2)
        nombre  = col1.text_input("Concepto")
        tipo_g  = col2.selectbox("Tipo", ["fijo","variable","ahorro"])
        total_g_str = st.text_input("Monto total ($)", placeholder="Ej: $1.200.000")
        if st.form_submit_button("Agregar") and nombre:
            total_g = parse_monto(total_g_str)
            j_g = round(total_g * julio_pct / 100)
            p_g = total_g - j_g
            p_g = total_g - j_g
            database.ejecutar(
                "INSERT INTO gastos_casa (mes,nombre,tipo,monto_total,aporte_julio,aporte_paula) VALUES (%s,%s,%s,%s,%s,%s)",
                (mes_sel, nombre, tipo_g, total_g, j_g, p_g)
            )
            st.success(f"'{nombre}' agregado ({julio_pct}% Julio / {paula_pct}% Paula).")
            st.rerun()

    if not df.empty:
        st.subheader("Eliminar gasto")
        a_borrar = st.selectbox("Selecciona", df["nombre"].tolist())
        if st.button("Eliminar"):
            database.ejecutar("UPDATE gastos_casa SET activo=0 WHERE mes=%s AND nombre=%s", (mes_sel, a_borrar))
            st.success(f"'{a_borrar}' eliminado.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "Registrar":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("Registrar movimiento")
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
