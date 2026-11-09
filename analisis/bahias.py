# ─────────────────────────────────────────────────────────────────────────────
# Direcciones de bahía `x y s` → pose objetivo del equipo y altura de uña
#
# Notación de maje (05-nov-2026):
#   x  posición horizontal: la bahía, contada desde la zona de descarga hacia adentro (1, 2, 3…)
#   y  nivel (altura)
#   s  lado, L o R, VISTO DESDE LA DESCARGA MIRANDO HACIA ADENTRO DEL PASILLO
#
# Lo que se agregó sin romperla:
#   · POSICIÓN DENTRO DE LA BAHÍA, `a` o `b`, en minúscula y pegada al lado: `5 3 Ra`.
#     En 2.35 m de luz entran DOS IBC por nivel (cara de 1.00 al pasillo, 35 cm sobrantes,
#     CLAUDE.md). `a` = la más cercana a la descarga, `b` = la más lejana. Sin letra, vale `a`.
#   · NIVEL 1 TIENE DOS ALTURAS, como la tabla de CLAUDE.md: `1A` (al piso) y `1B` (sobre el
#     cubo de abajo). `1` a secas es `1A`. Del 2 al 5 es un número solo. Se usan mayúsculas para
#     que no se confundan con la posición `a`/`b`, que va en minúscula.
#   · Se aceptan también `5R` o `3L` (bahía y lado, sin nivel), que es como lo dice maje al hablar
#     del lugar en el pasillo y no del hueco.
#
# Marco del pasillo (el mismo para todo analisis/planificador_rutas.py):
#   x a lo largo del pasillo, CRECE HACIA ADENTRO; x = 0 es el punto de descarga
#   y a lo ancho, 0 en el eje del pasillo. L queda en +y (a la izquierda mirando hacia adentro),
#   R en −y. θ es el rumbo de las UÑAS: θ = 0 uñas hacia adentro, θ = π uñas hacia la descarga
#   La pose es la del EJE DE RUEDAS DE CARGA (el pivote), igual que planificador_giro.py
#
# SUPUESTOS (no medidos; todos son parámetro):
#   X0           3.00  m del punto de descarga a la cara del primer poste del rack
#   N               7  bahías por lado — la fila de 17.41 m del pasillo B en datos/sectorA.json
#                      tiene 14 posiciones de piso = 7 bahías. Derivado del DXF, no contado
#   POSTE        0.12  m — derivado del mismo DXF: 17.41 = 7 × 2.35 + 8 × 0.12
#   reparto de los 35 cm sobrantes: tres huelgos iguales (poste·a·b·poste)
#   VEL_ELEV     0.55  m/s — la de sim-web (T.LIFTV), no medida en el equipo
#   la zona de descarga: piso libre de 6 m de ancho y 3 m detrás del punto de descarga
# ─────────────────────────────────────────────────────────────────────────────
import math
import re

# ── el pasillo y el rack (CLAUDE.md) ─────────────────────────────────────────
PASILLO = 3.00                  # m libres entre caras de rack, dato de campo
HALF = PASILLO / 2
BAHIA = 2.35                    # luz de bahía
FONDO_RACK = 1.10
IBC_CARA, IBC_FONDO = 1.00, 1.20

X0 = 3.00                       # SUPUESTO
N = 7                           # SUPUESTO (derivado del DXF)
POSTE = 0.12                    # SUPUESTO (derivado del DXF)
LIBRE_FONDO = 2.00              # SUPUESTO: del último poste a la pared del fondo (trasbordo)
ZONA_ANCHO = 6.00               # SUPUESTO
ZONA_ATRAS = 3.00               # SUPUESTO
VEL_ELEV = 0.55                 # SUPUESTO (sim-web)

# ── la geometría del DXF (09-nov): el pasillo B real, no solo su primer tramo ──
# datos/sectorA.json, filas verde (y −811.55) y azul (−807.39): 14 posiciones (7 bahías) de x 718.93 a
# 736.34, un HUECO de 2.66 m sin rack, 12 posiciones (6 bahías) de 739.00 a 753.91, y la pared del fondo
# en x 756.96 → 3.05 m libres después del último poste. Ahí, junto al último rack del lado R, está la
# ZONA DE CARGA (maje, 09-nov): el montacargas humano deja los cubos que entran (docs/09: «deja los cubos
# que entran al final del rack»). Por defecto todo queda como antes (un tramo de 7); `geometria('dxf')`
# cambia a esto mientras dura el `with`.
CORTE = None                    # bahías del primer tramo (None = un solo tramo)
HUECO = 0.0                     # m libres entre el último poste del tramo 1 y el primero del tramo 2
ZONA_CARGA = None               # 'L' o 'R': piso libre al fondo, junto al último rack de ese lado
ZONA_DESCARGA = None            # 'L' o 'R': piso libre al principio, junto al primer rack (maje 09-nov: del mismo
                                # ancho que la de carga, lado R, con pared a ~3 m como al fondo). Es la «bahía» 0

# ── v2 (05-nov, el video del operador y el afinado de maje) ───────────────────
# Los 3.00 m son de CARA DE POSTE a cara de poste: el punto más angosto. Hay un poste en cada borde
# de bahía. Entre postes (la luz de 2.35 m), la cara del cubo de N1 queda REC más atrás, en los DOS
# racks: ahí entran las uñas (al piso) y el culo al girar. Sin uñas en los huecos del IBC.
# Reconciliado con visibilidad.py: 2.35 es la LUZ entre caras de poste; 2.47 = 2.35 + 0.12 es el
# PASO entre centros de poste. Los dos números son el mismo rack.
REC_L = 0.06                    # maje, ~6 cm. N1 al piso: depende de dónde lo dejó el operador
REC_R = 0.06
POSTE_ALTO = 1.00               # SUPUESTO, sin uso en la cuenta plana (las uñas y el culo van al piso)
PASO_POSTE = BAHIA + POSTE      # 2.47 m entre centros de poste

# ── el equipo (CLAUDE.md, «Corregido en campo») ──────────────────────────────
XPIV = 1.50                     # culo → eje de carga, DERIVADO
LCH = 1.70                      # culo → cara de torre
FLEN = 1.20                     # uña útil
def a_punta(xpiv=XPIV, lch=LCH):
    """Punta de uña en el marco del vehículo (a = 0 en el pivote). Largo total lch + FLEN: 2.90 en
    v1/v2; en v3 2.91 medido (lch 1.71)."""
    return (lch - xpiv) + FLEN

# ── alturas por nivel: Base / Entrada / Agarre, al fondo de la uña (CLAUDE.md, El rack) ──
ALTURAS = {
    '1A': (0.000, 0.022, 0.082),
    '1B': (1.160, 1.182, 1.242),
    '2':  (2.545, 2.567, 2.627),
    '3':  (3.925, 3.947, 4.007),
    '4':  (5.305, 5.327, 5.387),
    '5':  (6.685, 6.707, 6.767),
}

# ── la punta de uña frente al rack ───────────────────────────────────────────
# El encargo pide 8–15 cm (como meta() de almacen-nuevo/planificar_giro_318.py). En 3.18 m entra;
# en 3.00 m NO: de frente al rack el equipo mide 2.90 de culo a punta y sobran 10 cm EN TOTAL.
# Con 5 cm de holgura en el culo contra el rack de enfrente, a la punta le quedan 5 cm como mucho.
# Se fija la meta en 3 cm (ventana 0–5) y se deja como parámetro. Ver rutas_resultados.md.
HOLGURA = 0.05                  # holgura mínima del chasis contra cualquier cara
GAP_OBJ = 0.03
GAP_MIN, GAP_MAX = -0.02, 0.05  # negativa = la punta ya pasó la cara (está en la luz de la bahía)

# ── carriles ─────────────────────────────────────────────────────────────────
CARRIL_CM = 85                  # línea recomendada; 75 es la del operador (1 cambio de sentido)


def carril(objetivo, cm=CARRIL_CM, pasillo=PASILLO):
    """y del pivote en cada carril. 'R' = giro hacia R: a `cm` del rack L. 'L' = a `cm` del R."""
    if objetivo == 'R':
        return pasillo / 2 - cm / 100.0
    if objetivo == 'L':
        return -(pasillo / 2 - cm / 100.0)
    return 0.0                                  # 'central', traslado


class Direccion:
    def __init__(self, x, y, s, p='a'):
        self.x, self.y, self.s, self.p = x, y, s, p

    def __repr__(self):
        y = '' if self.y is None else f"{self.y} "
        return f"{self.x} {y}{self.s}{self.p}"

    def __eq__(self, o):
        return isinstance(o, Direccion) and repr(self) == repr(o)

    def __hash__(self):
        return hash(repr(self))


def leer(texto):
    """'5 3 Ra', '5 3 R a', '5-1B-L-b', '53R', '5R', '3L' → Direccion."""
    t = texto.strip().replace('-', ' ').replace('·', ' ')
    m = re.fullmatch(r'\s*(\d+)\s*(?:(1A|1B|[1-5])\s*)?([LR])\s*([abc])?\s*', t)
    if not m:
        raise ValueError(f"dirección de bahía no válida: {texto!r}")
    x, y, s, p = int(m.group(1)), m.group(2), m.group(3), m.group(4) or 'a'
    if y == '1':
        y = '1A'
    return Direccion(x, y, s, p)


def _extra(x):
    """Corrimiento de la bahía x por el hueco entre tramos (0 en la geometría de siempre)."""
    return HUECO + POSTE if (CORTE and x > CORTE) else 0.0


def bahia_x(x):
    """(inicio, fin) de la luz de la bahía x a lo largo del pasillo. Con ZONA_CARGA, la «bahía» N + 1
    es la zona de carga: del último poste a la pared del fondo."""
    if ZONA_CARGA and x == N + 1:
        return fin_rack(), x_fondo()
    if ZONA_DESCARGA and x == 0:
        return -ZONA_ATRAS, X0
    if not 1 <= x <= N:
        raise ValueError(f"bahía {x} fuera del pasillo (1…{N})")
    x0 = X0 + POSTE + (x - 1) * (BAHIA + POSTE) + _extra(x)
    return x0, x0 + BAHIA


def centro_posicion(x, p='a'):
    """Centro de la posición a/b dentro de la bahía: tres huelgos iguales con los 35 cm."""
    x0, x1 = bahia_x(x)
    if p == 'c':
        return (x0 + x1) / 2
    g = (BAHIA - 2 * IBC_CARA) / 3
    return x0 + g + IBC_CARA / 2 if p == 'a' else x0 + 2 * g + 1.5 * IBC_CARA


def fin_rack():
    return X0 + POSTE + N * (BAHIA + POSTE) + (HUECO + POSTE if CORTE else 0.0)


def postes():
    """x de la cara de atrás (hacia la descarga) de cada poste, en los dos tramos."""
    n1 = CORTE or N
    out = [X0 + k * (BAHIA + POSTE) for k in range(n1 + 1)]
    if CORTE:
        x2 = X0 + CORTE * (BAHIA + POSTE) + POSTE + HUECO
        out += [x2 + k * (BAHIA + POSTE) for k in range(N - CORTE + 1)]
    return out


def en_luz(X, m=0.0):
    """Arreglo bool: X cae en la luz de alguna bahía (entre caras de poste, con margen m).
    Con un solo tramo es exactamente la cuenta de siempre del Mundo v2."""
    import numpy as np
    paso = BAHIA + POSTE
    n1 = CORTE or N
    rel = X - X0
    k = np.floor(rel / paso)
    off = rel - k * paso
    luz = (k >= 0) & (k < n1) & (off >= POSTE + m) & (off <= paso - m)
    if CORTE:
        rel = X - (X0 + CORTE * paso + POSTE + HUECO)
        k = np.floor(rel / paso)
        off = rel - k * paso
        luz |= (k >= 0) & (k < N - CORTE) & (off >= POSTE + m) & (off <= paso - m)
    return luz


from contextlib import contextmanager


@contextmanager
def geometria(cual='dxf'):
    """`with geometria('dxf'):` el pasillo B del DXF (13 bahías por lado en dos tramos, 3.05 m al fondo
    y la zona de carga junto al último rack R; pared al principio a 3.07 m y la zona de descarga junto al
    primer rack R). Restaura la geometría de siempre al salir."""
    global N, CORTE, HUECO, LIBRE_FONDO, ZONA_CARGA, ZONA_DESCARGA, X0, ZONA_ATRAS, ZONA_ANCHO
    viejo = (N, CORTE, HUECO, LIBRE_FONDO, ZONA_CARGA, ZONA_DESCARGA, X0, ZONA_ATRAS, ZONA_ANCHO)
    if cual == 'dxf':
        # principio: pared a 3.07 m del primer poste (DXF: muro en x 715.86, rack desde 718.93); la zona de
        # descarga es ese hueco, del lado R, como la de carga al fondo. Sin piso abierto detrás.
        N, CORTE, HUECO, LIBRE_FONDO, ZONA_CARGA = 13, 7, 2.66, 3.05, 'R'
        ZONA_DESCARGA, X0, ZONA_ATRAS, ZONA_ANCHO = 'R', 3.07, 0.0, PASILLO
    try:
        yield
    finally:
        N, CORTE, HUECO, LIBRE_FONDO, ZONA_CARGA, ZONA_DESCARGA, X0, ZONA_ATRAS, ZONA_ANCHO = viejo


def x_fondo():
    return fin_rack() + LIBRE_FONDO


def pose_de(direccion, gap=GAP_OBJ, xpiv=XPIV, pasillo=PASILLO, rec=0.0, lch=LCH):
    """Pose objetivo (x, y, θ, altura_uña) frente al hueco: uñas encarando el rack `s`, punta de uña
    a `gap` de la cara, centrado en la posición a/b. Altura = la de ENTRADA del nivel. `rec`: retranqueo
    de la cara del cubo detrás de la cara del poste (v2); la punta queda a `gap` de la cara del CUBO."""
    d = leer(direccion) if isinstance(direccion, str) else direccion
    xc = centro_posicion(d.x, d.p)
    lado = 1 if d.s == 'L' else -1
    y = lado * (pasillo / 2 + rec - gap - a_punta(xpiv, lch))
    th = lado * math.pi / 2
    alt = ALTURAS[d.y][1] if d.y else 0.0
    return xc, y, th, alt


def pose_en_pasillo(texto, mirando='descarga', cm=None):
    """'3L' → el equipo en el carril central (o en `cm`), a la altura de la bahía 3, uñas hacia
    `mirando` ('descarga' o 'adentro'). Para poses de arranque como la del caso de maje."""
    d = leer(texto)
    xc = (bahia_x(d.x)[0] + bahia_x(d.x)[1]) / 2
    th = math.pi if mirando == 'descarga' else 0.0
    y = 0.0 if cm is None else carril(d.s, cm)
    return xc, y, th


def pose_descarga(xpiv=XPIV, lch=LCH):
    """Dejar el cubo en el punto de descarga (x = 0, eje del pasillo), uñas hacia afuera (θ = π).
    El IBC va de la torre a la punta: su centro queda a (a_punta − 0.60) del pivote."""
    return a_punta(xpiv, lch) - IBC_FONDO / 2, 0.0, math.pi


def altura_uña(direccion, momento='entrada'):
    d = leer(direccion) if isinstance(direccion, str) else direccion
    b, e, a = ALTURAS[d.y]
    return {'base': b, 'entrada': e, 'agarre': a}[momento]


def t_elevar(h0, h1, vel=VEL_ELEV):
    return abs(h1 - h0) / vel


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    print(f"pasillo {PASILLO} m · {N} bahías por lado (SUPUESTO) · rack de x={X0 + POSTE:.2f} a {fin_rack():.2f}")
    for t in ('3L', '5R', '5 3 Ra', '5 3 Rb', '1 1 La', '2 1B Lb', '7 5 R'):
        d = leer(t)
        x, y, th, h = pose_de(d) if d.y else (*pose_en_pasillo(t), 0.0)
        print(f"  {t:<8} → {d!r:<8} pose ({x:6.3f}, {y:+.3f}, {math.degrees(th):+5.0f}°)  uña {h:.3f} m")
    print(f"  descarga → {tuple(round(v, 3) for v in pose_descarga())}")
