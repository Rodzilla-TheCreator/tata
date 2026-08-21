# ─────────────────────────────────────────────────────────────────────────────
# EDR18N2 en pasillo de 3.00 m — geometría del giro de 90°
#
# CORRECCIÓN: 2.91 m (culo a punta de uñas) es con el pantógrafo RECOGIDO.
# Extendido son 2.91 + 0.61 = 3.52 m.
#
# El pivote NO se deriva del radio de giro: es el eje de las ruedas de carga.
# Entre ejes de ficha 1.562 m + rueda motriz a ~0.35 m del culo = 1.91 m.
# ─────────────────────────────────────────────────────────────────────────────
L_RECOG = 2.91      # culo a punta de uñas, pantógrafo recogido — MEDIDO EN SITIO
FLEN    = 1.21      # uña = largo del maxicubo
REACH   = 0.61      # recorrido del pantógrafo
L_EXT   = L_RECOG + REACH
ANCHO   = 1.054
CARGA_W = 1.20
Wa      = 1.797     # radio de giro exterior, de ficha
WB      = 1.562     # entre ejes
XPIV    = 1.91      # eje de ruedas de carga ≈ 0.35 + WB
PAS     = 3.00
CLR     = 0.20      # holgura de norma

def ast(tip):
    return Wa + (tip - XPIV) + CLR

print(f"Pivote (eje de ruedas de carga) a {XPIV:.2f} m del culo\n")
print(f"{'configuración':>14} {'punta':>7} {'delante del pivote':>19} {'Ast':>8} {'en 3.00 m':>11}")
for nom, tip in (('recogido', L_RECOG), ('extendido', L_EXT)):
    A = ast(tip)
    print(f"{nom:>14} {tip:>7.2f} {tip-XPIV:>19.2f} {A:>8.2f} {PAS-A:>+11.2f}")

print(f"\nOjo con leer mal el Ast: ya trae adentro la holgura de norma ({CLR:.2f} m).")
print(f"{'':14} {'barrido':>9} {'sobra en 3.00 m':>17}")
for nom, tip in (('recogido', L_RECOG), ('extendido', L_EXT)):
    barr = Wa + (tip - XPIV)
    print(f"{nom:>14} {barr:>9.2f} {PAS-barr:>+17.2f}")
print(f"\nRecogido: el barrido ocupa 2.80 m y quedan 20 cm — que es justo la holgura")
print("que pide la norma. No es margen cero: es margen normal, sin extra.\n")

print("Comprobación cruzada del pivote:")
print(f"  para que quepa en {PAS:.2f} m, el pivote tiene que estar a ≥ "
      f"{Wa + L_RECOG + CLR - PAS:.3f} m del culo")
print(f"  entre ejes de ficha + rueda motriz a 0.35 m da {0.35+WB:.2f} m")
print("  los dos caminos coinciden, así que el modelo ya es consistente con lo observado\n")

print(f"Baoli KBE 20 (contrabalanceado): Ast 3.82 m → {PAS-3.82:+.2f} m. No entra de ninguna forma.")
print("\n── Dónde está la tolerancia ──")
BAY = 1.29
print(f"  pasillo: sobran {(PAS-CARGA_W)/2*100:.0f} cm por lado del maxicubo")
print(f"  bahía {BAY:.2f} m: quedan {(BAY-CARGA_W)/2*100:.1f} cm por lado  ← el requisito real")
print(f"  desplazador ±12 cm: cubre ese error {0.12/((BAY-CARGA_W)/2):.1f} veces")
