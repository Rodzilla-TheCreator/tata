# ─────────────────────────────────────────────────────────────────────────────
# ¿Cuánto cuesta REALMENTE emular las señales del EDR?
# Una sola placa cubre dirección, tracción e hidráulica. Esto es BOM de piezas,
# no ingeniería.
# ─────────────────────────────────────────────────────────────────────────────
PIEZAS = [
 ("MCU con CAN-FD y timers",            "STM32G474 o similar",        1,  6.50),
 ("Transceptores CAN aislados",         "ISO1042, 2 buses",           2,  3.80),
 ("Aislador digital de 6 canales",      "ISO7761",                    2,  2.90),
 ("DAC de 16 bits, 4 canales",          "DAC8564 — emula el mando",   1,  9.20),
 ("ADC de 16 bits, 8 canales",          "ADS8688 — lee al operador",  1, 11.40),
 ("Multiplexor analógico de potencia",  "conmuta operador ↔ robot",   4,  1.60),
 ("Relés de seguridad de doble contacto","corte físico del mando",    2,  4.20),
 ("Drivers de válvula proporcional",    "medio puente con lazo de corriente", 6, 3.40),
 ("Sensado de corriente por canal",     "INA240",                     6,  2.10),
 ("Regulador buck 24/48 V → 5 V",       "aislado",                    1,  7.80),
 ("Supresión y protección de entrada",  "TVS, fusibles, ferritas",    1,  9.00),
 ("Conectores automotrices sellados",   "Deutsch DT, 4 posiciones",   6,  5.50),
 ("PCB 4 capas, lote de 10",            "fabricación y ensamble",     1, 42.00),
 ("Gabinete y prensaestopas",           "IP65 pequeño",               1, 18.00),
]
tot = sum(c*p for _,_,c,p in PIEZAS)
print(f"{'PIEZA':38} {'CANT':>5} {'UNIT':>8} {'SUBTOT':>9}")
for n,d,c,p in PIEZAS:
    print(f"{n:38} {c:>5} {p:>8.2f} {c*p:>9.2f}")
print(f"{'':38} {'':>5} {'BOM':>8} {tot:>9.2f}")
print(f"\nCon 35% de margen de ensamble y prueba: ${tot*1.35:,.0f}")
print(f"Redondeado para la lista: ${round(tot*1.35/10)*10:,.0f}")

print("\n── Ingeniería, que es lo que de verdad cuesta ──")
NRE = [
 ("Ingeniería inversa del bus de dirección", 60),
 ("Ingeniería inversa de tracción y hidráulica", 80),
 ("Diseño y validación de la placa", 70),
 ("Pruebas de seguridad y modos de falla", 50),
]
h = sum(x[1] for x in NRE)
for n,x in NRE: print(f"  {n:44} {x:>4} h")
print(f"  {'TOTAL':44} {h:>4} h  ≈ {h/40:.1f} semanas-persona")
print(f"\nEs UNA sola vez para todo el modelo EDR18N2, no por unidad.")
for u in (1, 3, 10, 30):
    print(f"  repartida entre {u:>2} unidades: {h*25/u:>8,.0f} USD/unidad  (a $25/hora interna)")
