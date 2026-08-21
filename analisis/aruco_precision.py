# ─────────────────────────────────────────────────────────────────────────────
# ¿Qué precisión da un ArUco visto por la cámara de uñas?
# El requisito es ±4.5 cm lateral (lo que deja la bahía).
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
CAMS = [("USB 5 MP nivel Ingenio", 1280, 120), ("Global shutter GMSL2",1440,120),
        ("Basler dart 5 MP",       2592,  90)]
ERR_ESQ = 0.4          # error de detección de esquina, en píxeles (típico subpíxel)
DIST    = [0.8, 1.5, 2.5]
MARCAS  = [0.10, 0.15, 0.20]

print(f"error de esquina asumido: {ERR_ESQ} px\n")
for nom, W, fov in CAMS:
    f = W / (2*np.tan(np.radians(fov/2)))
    print(f"{nom}  ·  {W} px, {fov}° → f = {f:.0f} px")
    print(f"   {'marca':>7} {'dist':>6} {'lateral':>10} {'ángulo':>9}")
    for m in MARCAS:
        for d in DIST:
            lat = d * ERR_ESQ / f * 1000                    # mm
            px_marca = m * f / d                            # tamaño de la marca en px
            ang = np.degrees(ERR_ESQ / max(px_marca,1) * 2) # grados, dos esquinas opuestas
            print(f"   {m*100:>5.0f}cm {d:>5.1f}m {lat:>8.1f} mm {ang:>8.2f}°")
    print()
print("Requisito lateral: ±45 mm. Todas las combinaciones lo cumplen por uno o dos órdenes.\n")

# ── profundidad: sale del tamaño aparente, es la que de verdad manda ─────────
print("Precisión EN PROFUNDIDAD — la que dice dónde parar el chasis\n")
print(f"{'cámara':>22} {'marca':>7} {'dist':>6} {'profundidad':>13}")
for nom, W, fov in CAMS:
    if 'Global' in nom: continue
    f = W / (2*np.tan(np.radians(fov/2)))
    for m in (0.15, 0.20):
        for d in (0.8, 1.2, 1.6):
            print(f"{nom:>22} {m*100:>5.0f}cm {d:>5.1f}m {d*d*ERR_ESQ/(f*m)*1000:>11.1f} mm")
print("""
NO hace falta empujar contra nada ni medir presión:
  · el pantógrafo siempre va a SU PROPIO tope, así que el recorrido es fijo
  · la profundidad final la decide DÓNDE SE PARA EL CHASIS
  · la marca da esa distancia con precisión de milímetros
  · el riel es respaldo mecánico, no la referencia de trabajo

Y el maxicubo nunca se desliza: se entra en alto, se baja sobre la viga, se recoge.
Ese es el origen del 'error de empuje' — desaparece si no se empuja.""")
