import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "finanzas.db")
con = sqlite3.connect(DB)

# ── CREAR TABLAS NUEVAS ───────────────────────────────────────────────────────
con.executescript("""
    CREATE TABLE IF NOT EXISTS gastos_casa (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        mes              TEXT,
        nombre           TEXT,
        tipo             TEXT,
        monto_total      REAL,
        aporte_julio     REAL,
        aporte_paula     REAL,
        activo           INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ingresos_persona (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        mes     TEXT,
        persona TEXT,
        monto   REAL,
        nota    TEXT
    );
""")

# ── BORRAR DATA ANTERIOR DEL MES ──────────────────────────────────────────────
con.execute("DELETE FROM gastos_casa WHERE mes = '2026-04'")

# ── CARGAR GASTOS DE MAYO (de la imagen) ─────────────────────────────────────
gastos = [
    # (nombre, tipo, total, julio, paula)
    ("Arriendo",                  "fijo",     3344616, 1672308, 1672308),
    ("Agua",                      "fijo",      380000,  190000,  190000),
    ("Luz",                       "fijo",      280000,  140000,  140000),
    ("Gas",                       "fijo",       99640,   49820,   49820),
    ("ETB",                       "fijo",      200000,  100000,  100000),
    ("Empleada",                  "fijo",     3200000, 1600000, 1600000),
    ("Mercado",                   "fijo",     2000000, 1000000, 1000000),
    ("Club",                      "variable", 1000000,  500000,  500000),
    ("Fondo comun mensual",       "variable", 2000000, 1000000, 1000000),
    ("Ahorro USD",                "ahorro",   1100000,  550000,  550000),
    ("Ahorro COP Contingencias",  "ahorro",   1000000,  500000,  500000),
    ("Pañales y leche",           "variable",  610000,  305000,  305000),
    ("Empleada refuerzo",         "variable", 1500000,  750000,  750000),
]

for nombre, tipo, total, julio, paula in gastos:
    con.execute(
        "INSERT INTO gastos_casa (mes, nombre, tipo, monto_total, aporte_julio, aporte_paula) VALUES (?,?,?,?,?,?)",
        ("2026-04", nombre, tipo, total, julio, paula)
    )

con.commit()
con.close()
print("✅ Datos de Abril 2026 cargados correctamente.")
print(f"   Total gastos casa: $16.714.256")
print(f"   Aporte Julio:       $6.714.256 (40%)")
print(f"   Aporte Paula:      $10.000.000 (60%)")
