# ─────────────────────────────────────────────────────────────────────────────
# Ingeniería por nivel de madurez · kit TaTa sobre EDR18N2
# Horas estimadas. Son estimaciones de ingeniero, no cotizaciones.
# ─────────────────────────────────────────────────────────────────────────────
NIV = ['Ingenio', 'Piloto', 'Serie', 'Flota', 'Homologado']

TAREAS = {
'Ingenio': [
  ("Simulador: escena, cotas y cinemática del EDR",      70, "maje"),
  ("LiDAR: integración y SLAM en pasillo",              120, "Pato"),
  ("Cámaras: tubería de visión y marcadores",            80, "maje"),
  ("Placa de intercepción: ingeniería inversa",         140, "maje"),
  ("Placa de intercepción: diseño y validación",         70, "maje"),
  ("Teleoperación y cadena de paro",                     60, "maje"),
  ("Integración y pruebas en taller",                   100, "maje + Pato"),
],
'Piloto': [
  ("Evasión de obstáculos y control de velocidad",      120, "maje"),
  ("Seguimiento de trayectoria en pasillo de 3 m",      150, "Pato"),
  ("Toma y dejada asistida con desplazador",            120, "maje"),
  ("Modos de falla y recuperación",                     100, "maje + Pato"),
  ("Iteraciones de prueba en piso real",                160, "equipo"),
],
'Serie': [
  ("Integración con el WMS del cliente",                200, "maje"),
  ("Tablero de flota y reportes",                       150, "maje"),
  ("Herramientas de instalación y calibración",         180, "equipo"),
  ("Documentación, manuales y capacitación",            120, "equipo"),
  ("Endurecimiento y suite de regresión",               200, "maje"),
  ("Migración a sensores propios",                      100, "equipo"),
],
'Flota': [
  ("Arquitectura de seguridad e integración PL d",      300, "externo"),
  ("Expediente de seguridad funcional ISO 3691-4",      250, "externo"),
  ("Diagnóstico, OTA y soporte remoto",                 250, "maje"),
  ("Gestión de tráfico multivehículo",                  300, "maje + Pato"),
  ("Ingeniería de confiabilidad y MTBF",                200, "equipo"),
],
'Homologado': [
  ("Verificación y validación IEC 61508 / ISO 13849",   600, "externo"),
  ("Arquitectura redundante y su verificación",         500, "externo"),
  ("Proceso de certificación con tercero",              400, "externo"),
  ("Sistema de calidad de manufactura",                 300, "equipo"),
],
}
# tarifas: lo interno no se cobra; lo externo sí es efectivo
TARIFA_MERCADO = 55      # USD/h a precio de mercado regional para ingeniería de robótica
TARIFA_EXTERNA = 95      # USD/h de un consultor de seguridad funcional
FEES = {'Ingenio': 0, 'Piloto': 0, 'Serie': 0, 'Flota': 8000, 'Homologado': 55000}

print(f"{'NIVEL':12} {'horas':>7} {'sem-pers':>9} {'acum h':>8} "
      f"{'valor mercado':>14} {'EFECTIVO':>10}")
acum = 0
tot = {}
for n in NIV:
    h = sum(t[1] for t in TAREAS[n])
    hExt = sum(t[1] for t in TAREAS[n] if t[2] == 'externo')
    acum += h
    valor = h * TARIFA_MERCADO
    efectivo = hExt * TARIFA_EXTERNA + FEES[n]
    tot[n] = dict(h=h, hExt=hExt, acum=acum, valor=valor, efectivo=efectivo)
    print(f"{n:12} {h:>7} {h/40:>9.1f} {acum:>8} {valor:>14,} {efectivo:>10,}")

print(f"\n{'ACUMULADO al Homologado':24} {acum:>6} h = {acum/40:.0f} semanas-persona = {acum/2000:.1f} años-persona")
print(f"{'Valor de mercado total':24} ${acum*TARIFA_MERCADO:>9,}")
print(f"{'Efectivo total a Montasa':24} ${sum(t['efectivo'] for t in tot.values()):>9,}")
print(f"{'Aportado sin cobrar':24} ${acum*TARIFA_MERCADO - sum(t['hExt']*TARIFA_MERCADO for t in tot.values()):>9,}")

print("\n── El comparable de fábrica ──")
# Third Wave Automation construye un reach truck autónomo: el mismo formato que el EDR
TWA_USD, TWA_ANIOS = 97_000_000, 8
ing = TWA_USD * 0.60                      # parte que se va a nómina de ingeniería
anios_persona = ing / 200_000             # costo cargado por ingeniero-año en la bahía
print(f"Third Wave Automation · reach truck autónomo · fundada 2018")
print(f"  levantado: ${TWA_USD:,} en {TWA_ANIOS} años")
print(f"  si 60% va a ingeniería: ${ing:,.0f} ≈ {anios_persona:.0f} años-persona")
print(f"  TaTa al nivel Homologado: {acum/2000:.1f} años-persona = {acum/2000/anios_persona*100:.1f}% de eso")
print("\n  La diferencia no es que seamos más rápidos: es que no estamos construyendo")
print("  la máquina. El mástil, la hidráulica, la tracción y la homologación del")
print("  vehículo base ya existen y ya las pagó Mitsubishi.")
import json; json.dump({n:tot[n] for n in NIV}, open('ing_niveles.json','w'))
