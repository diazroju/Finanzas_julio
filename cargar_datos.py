import database

database.init_db()
database.ejecutar("DELETE FROM gastos_casa WHERE mes = %s", ("2026-04",))

gastos = [
    ("Arriendo",                 "fijo",     3344616, 1672308, 1672308),
    ("Agua",                     "fijo",      380000,  190000,  190000),
    ("Luz",                      "fijo",      280000,  140000,  140000),
    ("Gas",                      "fijo",       99640,   49820,   49820),
    ("ETB",                      "fijo",      200000,  100000,  100000),
    ("Empleada",                 "fijo",     3200000, 1600000, 1600000),
    ("Mercado",                  "fijo",     2000000, 1000000, 1000000),
    ("Club",                     "variable", 1000000,  500000,  500000),
    ("Fondo comun mensual",      "variable", 2000000, 1000000, 1000000),
    ("Ahorro USD",               "ahorro",   1100000,  550000,  550000),
    ("Ahorro COP Contingencias", "ahorro",   1000000,  500000,  500000),
    ("Pañales y leche",          "variable",  610000,  305000,  305000),
    ("Empleada refuerzo",        "variable", 1500000,  750000,  750000),
]

for nombre, tipo, total, julio, paula in gastos:
    database.ejecutar(
        "INSERT INTO gastos_casa (mes, nombre, tipo, monto_total, aporte_julio, aporte_paula) VALUES (%s,%s,%s,%s,%s,%s)",
        ("2026-04", nombre, tipo, total, julio, paula)
    )

print("✅ Datos de Abril 2026 cargados en Supabase.")
print("   Total: $16.714.256 | Julio: $6.714.256 | Paula: $10.000.000")
