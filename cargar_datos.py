import database

database.init_db()

MESES = {
    "2026-01": [
        ("Arriendo",             "fijo",     3183616, 1591808, 1591808),
        ("Agua",                 "fijo",      340000,  170000,  170000),
        ("Luz",                  "fijo",      250000,  125000,  125000),
        ("Gas",                  "fijo",       88000,   44000,   44000),
        ("ETB",                  "fijo",      200000,  100000,  100000),
        ("Empleada",             "fijo",     2800000, 1400000, 1400000),
        ("Mercado",              "fijo",     1800000,  900000,  900000),
        ("Club",                 "variable", 1750000,  875000,  875000),
        ("Fondo comun mensual",  "variable", 2000000, 1000000, 1000000),
        ("Enfermera Isabella",   "variable",  960000,  480000,  480000),
        ("Otros",                "variable",  815000,  407500,  407500),
    ],
    "2026-02": [
        ("Arriendo",             "fijo",     3505616, 1752808, 1752808),
        ("Agua",                 "fijo",      380000,  190000,  190000),
        ("Luz",                  "fijo",      280000,  140000,  140000),
        ("Gas",                  "fijo",       88000,   44000,   44000),
        ("ETB",                  "fijo",      200000,  100000,  100000),
        ("Empleada",             "fijo",     3000000, 1500000, 1500000),
        ("Mercado",              "fijo",     2000000, 1000000, 1000000),
        ("Club",                 "variable", 2000000, 1000000, 1000000),
        ("Fondo comun mensual",  "variable", 2000000, 1000000, 1000000),
        ("Vacunas Isabella",     "variable",  815000,  407500,  407500),
    ],
    "2026-03": [
        ("Arriendo",             "fijo",     3344616, 1672308, 1672308),
        ("Agua",                 "fijo",      380000,  190000,  190000),
        ("Luz",                  "fijo",      280000,  140000,  140000),
        ("Gas",                  "fijo",       99640,   49820,   49820),
        ("ETB",                  "fijo",      200000,  100000,  100000),
        ("Empleada",             "fijo",     3200000, 1600000, 1600000),
        ("Mercado",              "fijo",     2000000, 1000000, 1000000),
        ("Club",                 "variable", 2000000, 1000000, 1000000),
        ("Fondo comun mensual",  "variable", 2000000, 1000000, 1000000),
        ("Ahorro USD",           "ahorro",   1000000,  500000,  500000),
        ("Pañales y leche",      "variable",  610000,  305000,  305000),
    ],
    "2026-04": [
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
    ],
    "2026-05": [
        ("Arriendo",             "fijo",     3344616, 1672308, 1672308),
        ("Agua",                 "fijo",      380000,  190000,  190000),
        ("Luz",                  "fijo",      280000,  140000,  140000),
        ("Gas",                  "fijo",       99640,   49820,   49820),
        ("ETB",                  "fijo",      200000,  100000,  100000),
        ("Empleada",             "fijo",     3200000, 1600000, 1600000),
        ("Mercado",              "fijo",     2000000, 1000000, 1000000),
        ("Club",                 "variable", 1000000,  500000,  500000),
        ("Fondo comun mensual",  "variable", 2000000, 1000000, 1000000),
        ("Pañales y leche",      "variable",  610000,  305000,  305000),
        ("Empleada refuerzo",    "variable", 1500000,  750000,  750000),
    ],
}

for mes, gastos in MESES.items():
    database.ejecutar("DELETE FROM gastos_casa WHERE mes = %s", (mes,))
    for nombre, tipo, total, julio, paula in gastos:
        database.ejecutar(
            "INSERT INTO gastos_casa (mes, nombre, tipo, monto_total, aporte_julio, aporte_paula) VALUES (%s,%s,%s,%s,%s,%s)",
            (mes, nombre, tipo, total, julio, paula)
        )
    print(f"✅ {mes} cargado — Total: ${sum(g[2] for g in gastos):,.0f}")

print("\nTodos los meses cargados en Supabase.")
