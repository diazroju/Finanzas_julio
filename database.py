import psycopg2
import os

def get_url():
    # En la nube lee de los secrets de Streamlit, localmente de config.py
    try:
        import streamlit as st
        return st.secrets["DATABASE_URL"]
    except Exception:
        from config import DATABASE_URL
        return DATABASE_URL

def con():
    return psycopg2.connect(get_url())

def init_db():
    c = con()
    cur = c.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id        SERIAL PRIMARY KEY,
            fecha     TEXT,
            tipo      TEXT,
            monto     REAL,
            categoria TEXT,
            nota      TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos_casa (
            id           SERIAL PRIMARY KEY,
            mes          TEXT,
            nombre       TEXT,
            tipo         TEXT,
            monto_total  REAL,
            aporte_julio REAL,
            aporte_paula REAL,
            activo       INTEGER DEFAULT 1
        )
    """)
    c.commit()
    cur.close()
    c.close()

def ejecutar(sql, params=()):
    c = con()
    cur = c.cursor()
    cur.execute(sql.replace("?", "%s"), params)
    c.commit()
    cur.close()
    c.close()

def consultar(sql, params=()):
    c = con()
    cur = c.cursor()
    cur.execute(sql.replace("?", "%s"), params)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    c.close()
    return rows, cols
