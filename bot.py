import sqlite3
import re
import os
from datetime import datetime, date
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN

DB = os.path.join(os.path.dirname(__file__), "finanzas.db")

# ── BASE DE DATOS ─────────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT,
            tipo      TEXT,  -- ingreso / gasto
            monto     REAL,
            categoria TEXT,
            nota      TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS presupuestos (
            categoria TEXT PRIMARY KEY,
            limite    REAL
        )
    """)
    con.commit()
    con.close()

def guardar(tipo, monto, categoria, nota):
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO movimientos (fecha, tipo, monto, categoria, nota) VALUES (?,?,?,?,?)",
        (date.today().isoformat(), tipo, monto, categoria, nota)
    )
    con.commit()
    con.close()

def resumen_mes():
    con = sqlite3.connect(DB)
    hoy = date.today()
    mes = f"{hoy.year}-{hoy.month:02d}"
    rows = con.execute(
        "SELECT tipo, categoria, SUM(monto) FROM movimientos WHERE fecha LIKE ? GROUP BY tipo, categoria",
        (f"{mes}%",)
    ).fetchall()
    con.close()
    return rows

def total_mes():
    con = sqlite3.connect(DB)
    hoy = date.today()
    mes = f"{hoy.year}-{hoy.month:02d}"
    ingresos = con.execute(
        "SELECT COALESCE(SUM(monto),0) FROM movimientos WHERE fecha LIKE ? AND tipo='ingreso'",
        (f"{mes}%",)
    ).fetchone()[0]
    gastos = con.execute(
        "SELECT COALESCE(SUM(monto),0) FROM movimientos WHERE fecha LIKE ? AND tipo='gasto'",
        (f"{mes}%",)
    ).fetchone()[0]
    con.close()
    return ingresos, gastos

def ultimo_movimiento():
    con = sqlite3.connect(DB)
    row = con.execute(
        "SELECT tipo, monto, categoria, nota, fecha FROM movimientos ORDER BY id DESC LIMIT 1"
    ).fetchone()
    con.close()
    return row

def borrar_ultimo():
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM movimientos WHERE id = (SELECT MAX(id) FROM movimientos)")
    con.commit()
    con.close()

# ── PARSER DE LENGUAJE NATURAL ────────────────────────────────────────────────

CATEGORIAS_GASTO = {
    "mercado":      ["mercado", "supermercado", "compras", "viveres", "drogueria", "farmacia", "medicamento"],
    "restaurante":  ["restaurante", "almuerzo", "comida", "domicilio", "rappi", "ifood", "cena", "desayuno", "cafe"],
    "transporte":   ["uber", "taxi", "bus", "transporte", "gasolina", "parqueadero", "peaje"],
    "servicios":    ["luz", "agua", "gas", "internet", "telefono", "celular", "servicio"],
    "arriendo":     ["arriendo", "renta", "administracion"],
    "salud":        ["medico", "doctor", "clinica", "salud", "consulta", "examen"],
    "educacion":    ["colegio", "universidad", "curso", "libro", "educacion"],
    "ocio":         ["cine", "teatro", "entretenimiento", "viaje", "hotel", "vacaciones", "ropa", "zapatos"],
    "otros":        []
}

CATEGORIAS_INGRESO = {
    "sueldo":       ["sueldo", "salario", "nomina", "quincena"],
    "consultoria":  ["consultoria", "honorarios", "factura", "cliente"],
    "otros":        []
}

PALABRAS_GASTO   = ["gaste", "gasté", "pague", "pagué", "compre", "compré", "costo", "costó", "vale", "valio", "valió"]
PALABRAS_INGRESO = ["recibi", "recibí", "me pagaron", "ingreso", "ingresó", "gane", "gané", "pago de"]

def parsear_monto(texto):
    texto = texto.lower().replace(".", "").replace(",", "")
    patrones = [
        (r"(\d+(?:\.\d+)?)\s*millon(?:es)?", lambda m: float(m.group(1)) * 1_000_000),
        (r"(\d+(?:\.\d+)?)\s*m\b",           lambda m: float(m.group(1)) * 1_000_000),
        (r"(\d+(?:\.\d+)?)\s*mil(?:es)?",    lambda m: float(m.group(1)) * 1_000),
        (r"(\d+(?:\.\d+)?)\s*k\b",           lambda m: float(m.group(1)) * 1_000),
        (r"\$\s*(\d+(?:\.\d+)?)",            lambda m: float(m.group(1))),
        (r"(\d{4,})",                         lambda m: float(m.group(1))),
        (r"(\d+)",                            lambda m: float(m.group(1))),
    ]
    for patron, conv in patrones:
        m = re.search(patron, texto)
        if m:
            return conv(m)
    return None

def detectar_categoria(texto, categorias):
    texto = texto.lower()
    for cat, palabras in categorias.items():
        for p in palabras:
            if p in texto:
                return cat
    return "otros"

def parsear_mensaje(texto):
    texto_lower = texto.lower()

    es_ingreso = any(p in texto_lower for p in PALABRAS_INGRESO)
    es_gasto   = any(p in texto_lower for p in PALABRAS_GASTO)

    if not es_ingreso and not es_gasto:
        return None

    monto = parsear_monto(texto)
    if not monto:
        return None

    if es_ingreso:
        categoria = detectar_categoria(texto, CATEGORIAS_INGRESO)
        return {"tipo": "ingreso", "monto": monto, "categoria": categoria, "nota": texto}
    else:
        categoria = detectar_categoria(texto, CATEGORIAS_GASTO)
        return {"tipo": "gasto", "monto": monto, "categoria": categoria, "nota": texto}

def fmt(n):
    return f"${n:,.0f}".replace(",", ".")

# ── COMANDOS ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola Julio! Soy tu asistente de finanzas.\n\n"
        "Puedes escribirme en lenguaje natural:\n"
        "  • _'Gasté 80mil en mercado'_\n"
        "  • _'Pagué 1.5 millones de arriendo'_\n"
        "  • _'Me pagaron 3 millones'_\n\n"
        "Comandos disponibles:\n"
        "  /resumen — ver el mes actual\n"
        "  /hoy — movimientos de hoy\n"
        "  /borrar — eliminar el último registro\n"
        "  /ayuda — ver todos los comandos",
        parse_mode="Markdown"
    )

async def cmd_resumen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ingresos, gastos = total_mes()
    saldo = ingresos - gastos
    rows  = resumen_mes()

    hoy  = date.today()
    msg  = f"📊 *Resumen {hoy.strftime('%B %Y')}*\n\n"
    msg += f"💰 Ingresos:  {fmt(ingresos)}\n"
    msg += f"💸 Gastos:    {fmt(gastos)}\n"
    msg += f"{'✅' if saldo >= 0 else '🔴'} Saldo:     {fmt(saldo)}\n\n"

    gastos_cat = [(cat, tot) for tipo, cat, tot in rows if tipo == "gasto"]
    if gastos_cat:
        msg += "*Gastos por categoría:*\n"
        for cat, tot in sorted(gastos_cat, key=lambda x: -x[1]):
            msg += f"  • {cat.capitalize()}: {fmt(tot)}\n"

    ingresos_cat = [(cat, tot) for tipo, cat, tot in rows if tipo == "ingreso"]
    if ingresos_cat:
        msg += "\n*Ingresos por categoría:*\n"
        for cat, tot in sorted(ingresos_cat, key=lambda x: -x[1]):
            msg += f"  • {cat.capitalize()}: {fmt(tot)}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_hoy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT tipo, monto, categoria, nota FROM movimientos WHERE fecha = ? ORDER BY id DESC",
        (date.today().isoformat(),)
    ).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text("No hay movimientos registrados hoy.")
        return

    msg = f"📅 *Hoy {date.today().strftime('%d/%m/%Y')}*\n\n"
    for tipo, monto, cat, nota in rows:
        emoji = "💰" if tipo == "ingreso" else "💸"
        msg += f"{emoji} {fmt(monto)} — {cat.capitalize()}\n   _{nota}_\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_borrar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ultimo = ultimo_movimiento()
    if not ultimo:
        await update.message.reply_text("No hay movimientos para borrar.")
        return
    tipo, monto, cat, nota, fecha = ultimo
    borrar_ultimo()
    await update.message.reply_text(
        f"🗑 Borrado: {fmt(monto)} en {cat} ({fecha})\n_{nota}_",
        parse_mode="Markdown"
    )

async def cmd_ayuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Cómo usarme:*\n\n"
        "*Registrar gasto:*\n"
        "  'Gasté 50mil en mercado'\n"
        "  'Pagué 200000 de luz'\n"
        "  'Compré ropa por 300mil'\n\n"
        "*Registrar ingreso:*\n"
        "  'Me pagaron 5 millones'\n"
        "  'Recibí 800mil de consultoría'\n\n"
        "*Comandos:*\n"
        "  /resumen — resumen del mes\n"
        "  /hoy — movimientos de hoy\n"
        "  /borrar — borrar último registro\n"
        "  /ayuda — esta ayuda",
        parse_mode="Markdown"
    )

async def manejar_mensaje(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    resultado = parsear_mensaje(texto)

    if not resultado:
        await update.message.reply_text(
            "No entendí bien. Intenta así:\n"
            "• _'Gasté 80mil en mercado'_\n"
            "• _'Me pagaron 3 millones'_",
            parse_mode="Markdown"
        )
        return

    guardar(resultado["tipo"], resultado["monto"], resultado["categoria"], resultado["nota"])

    _, gastos = total_mes()
    emoji = "💰" if resultado["tipo"] == "ingreso" else "💸"

    msg = (
        f"{emoji} *Registrado*\n"
        f"  Tipo:      {resultado['tipo'].capitalize()}\n"
        f"  Monto:     {fmt(resultado['monto'])}\n"
        f"  Categoría: {resultado['categoria'].capitalize()}\n\n"
    )
    if resultado["tipo"] == "gasto":
        msg += f"Total gastado este mes: {fmt(gastos)}"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("Bot de finanzas iniciado...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(CommandHandler("hoy",     cmd_hoy))
    app.add_handler(CommandHandler("borrar",  cmd_borrar))
    app.add_handler(CommandHandler("ayuda",   cmd_ayuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    app.run_polling()
