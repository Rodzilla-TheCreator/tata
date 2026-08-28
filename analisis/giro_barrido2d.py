# -*- coding: utf-8 -*-
"""
EDR18N2 en pasillo de 3.00 m — barrido REAL del giro de 90 grados.

Reemplaza el modelo 1-D de geometria_giro.py, que tenia dos fallas:

  (1) Colocaba el pivote a 1.91 m del culo y a la vez usaba Wa = 1.797 m de
      ficha. Son incompatibles: con el pivote ahi, la sola esquina trasera
      exterior barre hypot(1.91, 0.527) = 1.981 m, o sea 18 cm MAS que el Wa
      que dice la ficha. El pivote maximo que admite Wa=1.797 es 1.718 m.

  (2) Media el brazo de la carga solo en longitudinal (punta - pivote),
      ignorando que el maxicubo tiene 1.20 m de ancho. El punto critico del
      giro no es la punta de la uña: es la ESQUINA delantera exterior de la
      carga, a hypot(dy, 0.60) del pivote.

Aqui el barrido se calcula rotando los poligonos de verdad y midiendo la
envolvente, sin formula cerrada.
"""
import math

# ── maquina, tal como esta documentada en docs/02 ────────────────────────────
W_TRUCK = 1.054          # ancho de chasis, ficha
HW      = W_TRUCK / 2
Wa      = 1.797          # radio de giro exterior, ficha
WB      = 1.562          # entre ejes, ficha
TIP     = 2.91           # culo a punta de uñas, RECOGIDO, medido en sitio
FACE    = 1.70           # culo a cara de uñas, derivado
FLEN    = 1.21           # largo de uña, medido
REACH   = 0.61           # recorrido del pantografo
PAS     = 3.00           # pasillo
CLR     = 0.20           # holgura de norma (VDI/ISO), TOTAL, no por lado

# el maxicubo: datos/almacen3d.json dice w=1.20 d=1.00; docs/02 dice que la uña
# 1.21 es "igual que el maxicubo". Se modelan los dos y se reporta la diferencia.
CUBE_W  = 1.20
CUBE_D  = 1.00

P_MAX   = math.sqrt(Wa**2 - HW**2)   # pivote maximo compatible con Wa


def poly_truck(tip):
    """Chasis + carga en marco cuerpo: culo en y=0, eje longitudinal = +y."""
    face = tip - FLEN
    chasis = [(-HW, 0.0), (HW, 0.0), (HW, FACE), (-HW, FACE)]
    return chasis, face


def poly_load(tip, modo):
    """Huella de la carga sobre las uñas. modo: 'json' (1.20x1.00) o 'doc' (1.20x1.21)."""
    face = tip - FLEN
    d = CUBE_D if modo == 'json' else FLEN
    return [(-CUBE_W/2, face), (CUBE_W/2, face), (CUBE_W/2, face + d), (-CUBE_W/2, face + d)]


def envolvente(pts, piv, arco=90.0, paso=0.5):
    """Ancho de la envolvente barrida al rotar `pts` alrededor de (0, piv)."""
    xmin, xmax = float('inf'), float('-inf')
    n = int(arco / paso)
    for i in range(n + 1):
        th = math.radians(arco * i / n)
        c, s = math.cos(th), math.sin(th)
        for x, y in pts:
            dy = y - piv
            xr = x * c - dy * s
            if xr < xmin: xmin = xr
            if xr > xmax: xmax = xr
    return xmax - xmin


def radio_max(pts, piv):
    return max(math.hypot(x, y - piv) for x, y in pts)


def bloque(tip, modo, piv):
    chasis, _ = poly_truck(tip)
    carga = poly_load(tip, modo)
    uñas = [(-0.30, tip), (0.30, tip)]          # puntas de uña desnudas
    return chasis + carga + uñas


# ── 1. la inconsistencia del pivote ──────────────────────────────────────────
print("=" * 74)
print("1. EL PIVOTE Y EL Wa DE FICHA NO PUEDEN SER AMBOS CIERTOS")
print("=" * 74)
p_doc = 0.35 + WB
print(f"  docs/02 pone el pivote a 0.35 + {WB} = {p_doc:.3f} m del culo")
print(f"  con ese pivote la esquina trasera exterior barre  "
      f"hypot({p_doc:.3f}, {HW:.3f}) = {math.hypot(p_doc, HW):.3f} m")
print(f"  pero la ficha dice que el radio exterior es Wa   = {Wa:.3f} m")
print(f"  -> el modelo se pasa por {math.hypot(p_doc, HW) - Wa:+.3f} m\n")
print(f"  pivote maximo que admite Wa={Wa} con el chasis de {W_TRUCK} m: "
      f"{P_MAX:.3f} m del culo")
print(f"  eso deja el volado trasero en {P_MAX - WB:.3f} m, no en los 0.35 supuestos\n")


# ── 2. barrido real vs el numero publicado ───────────────────────────────────
print("=" * 74)
print("2. BARRIDO REAL DEL GIRO DE 90 GRADOS (envolvente rotada, no formula)")
print("=" * 74)
print(f"{'pivote':>8} {'carga':>6} {'R_max':>7} {'barrido':>8} {'+holgura':>9} "
      f"{'vs 3.00':>9}  {'':>4}")
filas = []
for piv, etq in ((P_MAX, 'coherente'), (p_doc, 'del doc')):
    for modo in ('json', 'doc'):
        pts = bloque(TIP, modo, piv)
        barr = envolvente(pts, piv)
        rmax = radio_max(pts, piv)
        ast = barr + CLR
        filas.append((piv, etq, modo, rmax, barr, ast))
        marca = 'CABE' if ast <= PAS else 'NO CABE'
        print(f"{piv:>8.3f} {modo:>6} {rmax:>7.3f} {barr:>8.3f} {ast:>9.3f} "
              f"{PAS - ast:>+9.3f}  {marca}")

print(f"\n  para comparar, lo que dice hoy docs/02: barrido 2.80, Ast 3.00, 'cabe'")
mejor = min(f[4] for f in filas)
print(f"  el barrido mas optimista de los cuatro es {mejor:.3f} m, "
      f"{mejor - 2.80:+.3f} m sobre lo publicado")


# ── 3. ¿que tendria que ser cierto para que quepa en 3.00? ───────────────────
print("\n" + "=" * 74)
print("3. QUE TENDRIA QUE SER CIERTO PARA QUE EL GIRO DE UNA SOLA VEZ QUEPA")
print("=" * 74)
pts = bloque(TIP, 'json', P_MAX)
barr = envolvente(pts, P_MAX)
print(f"  con pivote coherente y cubo 1.20x1.00 el barrido es {barr:.3f} m")
print(f"  sin NADA de holgura de norma todavia faltan {barr - PAS:+.3f} m")
print(f"  -> un giro de 90 grados en un solo movimiento NO cabe en 3.00 m\n")

# cuanto habria que recortar la punta
lo, hi = 1.5, TIP
for _ in range(60):
    mid = (lo + hi) / 2
    if envolvente(bloque(mid, 'json', min(P_MAX, mid - 0.5)), min(P_MAX, mid - 0.5)) > PAS:
        hi = mid
    else:
        lo = mid
print(f"  la punta tendria que estar a {lo:.2f} m del culo (hoy: {TIP:.2f} m) "
      f"-> sobran {TIP - lo:.2f} m")

# extendido, para dejarlo dicho
pts_e = bloque(TIP + REACH, 'json', P_MAX)
print(f"  extendido ({TIP + REACH:.2f} m) el barrido seria "
      f"{envolvente(pts_e, P_MAX):.3f} m — ni de lejos\n")

print("=" * 74)
print("LO QUE SIGUE EN PIE Y LO QUE NO")
print("=" * 74)
print("  SIGUE EN PIE: girar recogido y extender solo ya alineado. La regla es")
print("                correcta y ahora con mas razon, no menos.")
print("  SIGUE EN PIE: la tolerancia esta en la bahia (4.5 cm), no en el pasillo,")
print("                y el desplazador la cubre 2.7 veces.")
print("  SE CAE:       'cabe con margen normal'. Con la geometria bien hecha el")
print("                giro de 90 en un solo movimiento no cabe en 3.00 m.")
print("  IMPLICACION:  si la maquina hoy trabaja ahi, es porque el operador NO")
print("                gira de una sola vez. Hace vaiven. Eso hay que medirlo en")
print("                campo y el kit tiene que planificarlo, no improvisarlo.")


# ── 4. contraste con la ficha publicada del EDR18N2 ──────────────────────────
# Fuente: hoja de especificaciones Mitsubishi/Logisnext (machinemaxxusa, lectura-specs)
#   largo total (a punta de patines) ....... 1983 mm
#   largo a cara de uñas ................... 1582 mm   <-- docs/02 "deriva" 1.70 m
#   radio de giro minimo ................... 1797 mm   (coincide)
#   entre ejes ............................. 1562 mm   (coincide)
#   techo de proteccion .................... 2413 mm   (coincide)
#   capacidad .............................. 1580 kg   (coincide)
FICHA_L1   = 1.983    # tail -> punta de patines; ahi viven las ruedas de carga
FICHA_FACE = 1.582    # tail -> cara de uñas

print("\n" + "=" * 74)
print("4. CONTRA LA FICHA PUBLICADA")
print("=" * 74)
print(f"  la ficha da cara de uñas a {FICHA_FACE:.3f} m; docs/02 'deriva' {FACE:.3f} m"
      f"  ({FACE - FICHA_FACE:+.3f} m)")
print(f"  la ficha da largo total a {FICHA_L1:.3f} m (punta de patines = eje de ruedas de carga)")
print(f"  con uña de {FLEN:.2f} m sobre cara de ficha, la punta cae en "
      f"{FICHA_FACE + FLEN:.3f} m, no en los {TIP:.2f} m medidos "
      f"({TIP - FICHA_FACE - FLEN:+.3f} m)\n")

for piv, etq in ((P_MAX, 'coherente con Wa'), (FICHA_L1, 'patines de ficha')):
    for tip, tetq in ((TIP, 'punta medida 2.91'), (FICHA_FACE + FLEN, 'punta de ficha 2.79')):
        chasis = [(-HW, 0.0), (HW, 0.0), (HW, FICHA_FACE), (-HW, FICHA_FACE)]
        face = tip - FLEN
        carga = [(-CUBE_W/2, face), (CUBE_W/2, face),
                 (CUBE_W/2, face + CUBE_D), (-CUBE_W/2, face + CUBE_D)]
        pts = chasis + carga + [(-0.30, tip), (0.30, tip)]
        barr = envolvente(pts, piv)
        print(f"  pivote {etq:<18} {tetq:<20} barrido {barr:.3f} m"
              f"   {'CABE' if barr + CLR <= PAS else 'NO CABE'} (con holgura)"
              f"   {'cabe' if barr <= PAS else 'no cabe'} (sin holgura)")

print(f"\n  el barrido se mueve poco con el pivote: el giro de 90 lo manda la")
print(f"  DIAGONAL del conjunto chasis+carga, no donde este exactamente el eje.")
print(f"  Por eso la conclusion aguanta aunque el pivote siga en discusion.")
