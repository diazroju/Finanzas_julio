import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os

DB = os.path.join(os.path.dirname(__file__), "finanzas.db")

st.set_page_config(page_title="Finanzas Julio", page_icon="💰", layout="centered")

def con():
    return sqlite3.connect(DB)

def fmt(n):
    if n is None or n == "":
        return "$0"
    return f"${float(n):,.0f}".replace(",", ".")

def meses():
    c = con()
    rows = c.execute(
        "SELECT DISTINCT mes FROM gastos_casa ORDER BY mes DESC"
    ).fetchall()
    c.close()
    return [r[0] for r in rows] or [date.today().strftime("%Y-%m")]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("💰 Finanzas Julio")
mes_lista = meses()
mes_sel   = st.sidebar.selectbox("Mes", mes_lista)
pagina    = st.sidebar.radio("", ["📊 Resumen", "🏠 Gastos Casa", "➕ Agregar Gasto"])

# ── CARGAR DATOS ──────────────────────────────────────────────────────────────
def get_gastos_casa(mes):
    c = con()
    df = pd.read_sql(
        "SELECT * FROM gastos_casa WHERE mes=? AND activo=1 ORDER BY tipo, id",
        c, params=(mes,)
    )
    c.close()
    return df

def get_movimientos(mes):
    c = con()
    df = pd.read_sql(
        "SELECT * FROM movimientos WHERE fecha LIKE ? ORDER BY fecha DESC",
        c, params=(f"{mes}%",)
    )
    c.close()
    return df

# ═══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Resumen":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("📊 Resumen del mes")

    df_casa = get_gastos_casa(mes_sel)
    df_mov  = get_movimientos(mes_sel)

    if df_casa.empty and df_mov.empty:
        st.info("No hay datos para este mes. Ve a '🏠 Gastos Casa' para agregar.")
        st.stop()

    total_casa  = df_casa["monto_total"].sum() if not df_casa.empty else 0
    julio_casa  = df_casa["aporte_julio"].sum() if not df_casa.empty else 0
    paula_casa  = df_casa["aporte_paula"].sum() if not df_casa.empty else 0

    gastos_julio_personal = df_mov[df_mov["tipo"]=="gasto"]["monto"].sum() if not df_mov.empty else 0
    total_julio = julio_casa + gastos_julio_personal

    # Métricas principales
    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Total Casa",    fmt(total_casa))
    col2.metric("👤 Julio aporta",  fmt(julio_casa))
    col3.metric("👩 Paula aporta",  fmt(paula_casa))

    st.divider()

    # Gráfica aportes
    fig_aportes = go.Figure(go.Pie(
        labels=["Julio", "Paula"],
        values=[julio_casa, paula_casa],
        hole=0.5,
        marker_colors=["#3498db", "#e91e8c"]
    ))
    fig_aportes.update_layout(
        title="Distribución de aportes",
        showlegend=True,
        margin=dict(t=40, b=0, l=0, r=0),
        height=280
    )
    st.plotly_chart(fig_aportes, use_container_width=True)

    # Gastos por tipo
    if not df_casa.empty:
        st.subheader("Gastos por categoría")
        tipo_df = df_casa.groupby("tipo")["monto_total"].sum().reset_index()
        tipo_df.columns = ["Tipo", "Total"]
        tipo_df["Tipo"] = tipo_df["Tipo"].str.capitalize()
        fig2 = px.bar(tipo_df, x="Tipo", y="Total",
                      color="Tipo",
                      color_discrete_sequence=["#3498db","#2ecc71","#e74c3c"],
                      text_auto=False)
        fig2.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
        fig2.update_layout(showlegend=False, margin=dict(t=20,b=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Gastos personales del bot
    if not df_mov.empty:
        st.subheader("Mis gastos personales (bot)")
        col1, col2 = st.columns(2)
        ingresos_bot = df_mov[df_mov["tipo"]=="ingreso"]["monto"].sum()
        col1.metric("Ingresos registrados", fmt(ingresos_bot))
        col2.metric("Gastos personales",    fmt(gastos_julio_personal))

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "🏠 Gastos Casa":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("🏠 Gastos CASITA MADRIGAL")

    df = get_gastos_casa(mes_sel)

    # Copiar mes anterior
    st.subheader(f"Mes: {mes_sel}")

    meses_list = meses()
    if len(meses_list) > 1:
        if st.button("📋 Copiar del mes anterior"):
            mes_ant = meses_list[1]
            c = con()
            c.execute("DELETE FROM gastos_casa WHERE mes=?", (mes_sel,))
            rows = c.execute("SELECT nombre,tipo,monto_total,aporte_julio,aporte_paula FROM gastos_casa WHERE mes=? AND activo=1", (mes_ant,)).fetchall()
            for r in rows:
                c.execute("INSERT INTO gastos_casa (mes,nombre,tipo,monto_total,aporte_julio,aporte_paula) VALUES (?,?,?,?,?,?)",
                          (mes_sel, r[0], r[1], r[2], r[3], r[4]))
            c.commit()
            c.close()
            st.success("Mes copiado.")
            st.rerun()

    if df.empty:
        st.info("No hay gastos para este mes.")
    else:
        for tipo in ["fijo", "variable", "ahorro"]:
            sub = df[df["tipo"] == tipo].copy()
            if sub.empty:
                continue

            titulo = {"fijo": "📌 Gastos Fijos", "variable": "📊 Gastos Variables", "ahorro": "💾 Ahorros"}
            st.subheader(titulo[tipo])

            edited = st.data_editor(
                sub[["id","nombre","monto_total","aporte_julio","aporte_paula"]].rename(columns={
                    "nombre": "Concepto", "monto_total": "Total",
                    "aporte_julio": "Julio", "aporte_paula": "Paula"
                }),
                hide_index=True,
                use_container_width=True,
                disabled=["id"],
                key=f"editor_{tipo}_{mes_sel}"
            )

            if st.button(f"💾 Guardar {tipo}s", key=f"save_{tipo}"):
                c = con()
                for _, r in edited.iterrows():
                    c.execute(
                        "UPDATE gastos_casa SET nombre=?, monto_total=?, aporte_julio=?, aporte_paula=? WHERE id=?",
                        (r["Concepto"], r["Total"], r["Julio"], r["Paula"], r["id"])
                    )
                c.commit()
                c.close()
                st.success("Guardado.")
                st.rerun()

            total_tipo = sub["monto_total"].sum()
            j = sub["aporte_julio"].sum()
            p = sub["aporte_paula"].sum()
            st.caption(f"Total: {fmt(total_tipo)} | Julio: {fmt(j)} | Paula: {fmt(p)}")
            st.divider()

        # Totales
        st.markdown(f"""
        **TOTAL GASTOS MES: {fmt(df['monto_total'].sum())}**
        | Julio: {fmt(df['aporte_julio'].sum())} ({round(df['aporte_julio'].sum()/df['monto_total'].sum()*100)}%)
        | Paula: {fmt(df['aporte_paula'].sum())} ({round(df['aporte_paula'].sum()/df['monto_total'].sum()*100)}%)
        """)

    st.divider()
    st.subheader("➕ Agregar gasto a la casa")
    with st.form("nuevo_gasto_casa"):
        col1, col2 = st.columns(2)
        nombre   = col1.text_input("Concepto")
        tipo_g   = col2.selectbox("Tipo", ["fijo", "variable", "ahorro"])
        total_g  = st.number_input("Monto total ($)", min_value=0, step=10000)
        col3, col4 = st.columns(2)
        julio_g  = col3.number_input("Aporte Julio ($)", min_value=0, step=10000, value=int(total_g//2))
        paula_g  = col4.number_input("Aporte Paula ($)", min_value=0, step=10000, value=int(total_g//2))
        submitted = st.form_submit_button("Agregar")
        if submitted and nombre:
            c = con()
            c.execute(
                "INSERT INTO gastos_casa (mes,nombre,tipo,monto_total,aporte_julio,aporte_paula) VALUES (?,?,?,?,?,?)",
                (mes_sel, nombre, tipo_g, total_g, julio_g, paula_g)
            )
            c.commit()
            c.close()
            st.success(f"'{nombre}' agregado.")
            st.rerun()

    # Eliminar gasto
    if not df.empty:
        st.subheader("🗑 Eliminar gasto")
        opciones = df["nombre"].tolist()
        a_borrar = st.selectbox("Selecciona el gasto a eliminar", opciones)
        if st.button("Eliminar"):
            c = con()
            c.execute("UPDATE gastos_casa SET activo=0 WHERE mes=? AND nombre=?", (mes_sel, a_borrar))
            c.commit()
            c.close()
            st.success(f"'{a_borrar}' eliminado.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
elif pagina == "➕ Agregar Gasto":
# ═══════════════════════════════════════════════════════════════════════════════
    st.title("➕ Registrar movimiento")
    st.info("También puedes registrar gastos escribiéndole al bot en Telegram.")

    with st.form("mov_form"):
        tipo     = st.radio("Tipo", ["gasto", "ingreso"], horizontal=True)
        monto    = st.number_input("Monto ($)", min_value=0, step=10000)
        cat      = st.selectbox("Categoría", [
            "mercado", "restaurante", "transporte", "servicios",
            "arriendo", "salud", "educacion", "ocio", "otros"
        ])
        nota     = st.text_input("Nota (opcional)")
        fecha    = st.date_input("Fecha", value=date.today())
        sub      = st.form_submit_button("Registrar")
        if sub and monto > 0:
            c = con()
            c.execute(
                "INSERT INTO movimientos (fecha, tipo, monto, categoria, nota) VALUES (?,?,?,?,?)",
                (fecha.isoformat(), tipo, monto, cat, nota)
            )
            c.commit()
            c.close()
            st.success(f"Registrado: {fmt(monto)} en {cat}")
