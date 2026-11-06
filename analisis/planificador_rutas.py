# ─────────────────────────────────────────────────────────────────────────────
# Planificador de rutas del EDR18N2 entre bahías — Hybrid A* general, CON UÑAS
#
#   py analisis/planificador_rutas.py          # v3 (06-nov): silueta de la ficha → rutas_v3.json, ruta_3L_5R_v3.png
#   py analisis/planificador_rutas.py --v2     # v2 (05-nov, tarde): postes + retranqueo → rutas_v2.json
#   py analisis/planificador_rutas.py --v1     # v1 (05-nov): casos 1–3 y controles → ruta_3L_5R.png y
#                                              # rutas_tabla.json (la usa la FSM)
#
# v3: 2.91 culo → punta (medido), culo con esquinas de 0.17 (ficha VDI), δmax = 90° (manual, modo
# 180°/360°) y XPIV 1.93 (derivado). Con δ = 90° tan δ explota: en v3 los ds de las primitivas son de la
# RUEDA MOTRIZ (step(..., rueda=True)), así una rotación en el lugar tiene largo y tiempo.
#
# Qué agrega sobre analisis/planificador_giro.py (que se deja como está):
#   · pose inicial y final CUALQUIERA, con cambios de sentido (costo parámetro)
#   · silueta CON UÑAS (la de almacen-nuevo/planificar_giro_318.py) y con el IBC si va cargado
#   · L_ANCHO = 0.48 medido el 18-sep (el viejo tiene 0.20, desmentido)
#   · el mundo: pasillo, zona de descarga, pared del fondo, y la luz de las bahías
#   · tramos con sentido (adelante = uñas primero), largo y tiempo con el sobre de 1.5 m/s
#   · el mismo step() (cinemática de bicicleta, rueda directriz atrás a WB, punto medio)
#
# EL HALLAZGO QUE ORDENA TODO (ver rutas_resultados.md):
#   Con uñas, la silueta cruzada al pasillo mide 3.03 m a ~72° (culo a punta, proyectado). Eso es
#   una propiedad de la FORMA, no del camino: trasladar no cambia el ancho que ocupa a un rumbo
#   dado. Ningún giro de 90° ni de 180° cabe en 3.00 m con TODO el equipo dentro del pasillo.
#   El operador gira 90° todos los días → algo entra a la bahía. Lo que se modela: durante el
#   giro, LAS UÑAS (y el cubo, si va cargado) pueden pasar la cara del rack hasta PROF_BAHIA,
#   pero SOLO en la luz de la bahía a la que se entra o de la que se sale. El chasis nunca.
#   sec/gen_svg.py ya dibujaba «uñas N cm dentro de la bahía al girar» con el modelo viejo.
#   PROF_BAHIA es SUPUESTO, y lo que se mide para cerrarlo está en rutas_resultados.md.
# ─────────────────────────────────────────────────────────────────────────────
import heapq
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bahias as B                                             # noqa: E402

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ── el equipo (CLAUDE.md) ────────────────────────────────────────────────────
WB, Wa = 1.562, 1.797
W_MAX, W_CAPO = 1.315, 1.065
L_ANCHO = 0.48                  # medido 18-sep (el viejo planificador tiene 0.20)
UNA_ANCHO, UNA_CENTRO = 0.13, 0.30
PROF_BAHIA = 0.20               # SUPUESTO: cuánto pueden pasar la cara las uñas/el cubo al girar

# ── velocidades (CLAUDE.md y sim-web) ────────────────────────────────────────
VMAX = 1.50                     # sobre de velocidad, CLAUDE.md
VMAN = 0.35                     # maniobra con la dirección por encima del 45 %: sim-web T.VMAN, SUPUESTO
ACC = 0.90                      # m/s², sim-web T.ACC, SUPUESTO
COSTO_CAMBIO = 1.0              # m equivalentes por cambio de sentido (parámetro)
COSTO_REVERSA = 0.0             # el reach truck maneja igual en los dos sentidos (CLAUDE.md, el 180°)


def dmax(xpiv):
    """Tope de dirección con la fórmula de planificador_giro.py (≈ 78° con XPIV = 1.50)."""
    return math.atan(WB / (math.sqrt(Wa ** 2 - xpiv ** 2) - W_MAX / 2))


def step(p, ds, d, rueda=False):
    """Copia de planificador_giro.py:54 — la misma que percepcion/odometria.py.
    rueda=True (v3): `ds` es lo que recorre la RUEDA MOTRIZ, no el eje de carga. Con δ = 90° el eje
    de carga no se mueve (rota en el lugar) y tan δ explota; así queda finito. Para δ < 90° es la
    misma cinemática: ds_eje = ds·cos δ y Δθ = −(ds/WB)·sin δ = −(ds_eje/WB)·tan δ. Igual de reversible."""
    if rueda:
        dth = -(ds / WB) * math.sin(d); th2 = p[2] + dth * 0.5; de = ds * math.cos(d)
        return (p[0] + de * math.cos(th2), p[1] + de * math.sin(th2), p[2] + dth)
    dth = -(ds / WB) * math.tan(d); th2 = p[2] + dth * 0.5
    return (p[0] + ds * math.cos(th2), p[1] + ds * math.sin(th2), p[2] + dth)


# ── silueta ──────────────────────────────────────────────────────────────────
def _muestrear(poly, paso=0.05):
    out = []
    for (a0, l0), (a1, l1) in zip(poly, poly[1:] + poly[:1]):
        n = max(1, int(math.ceil(math.hypot(a1 - a0, l1 - l0) / paso)))
        out += [(a0 + (a1 - a0) * k / n, l0 + (l1 - l0) * k / n) for k in range(n)]
    return out


def _cuerpo(a_culo, a_mast, a_pata, hc, hp, r_culo=0.0):
    """Capó del culo a la torre y patas; con r_culo > 0 los dos rincones del culo van redondeados
    (v3: 0.17 del dibujo de la ficha VDI, herramientas/fichas/LEEME.md)."""
    out = [(a_culo + r_culo, hc), (a_mast, hc), (a_mast, hp), (a_pata, hp),
           (a_pata, -hp), (a_mast, -hp), (a_mast, -hc), (a_culo + r_culo, -hc)]
    if r_culo > 0:
        for c_l, a0 in ((-hc + r_culo, -90.0), (hc - r_culo, 180.0)):
            for k in range(1, 19):
                t = math.radians(a0 - 90.0 * k / 18)
                out.append((a_culo + r_culo + r_culo * math.cos(t), c_l + r_culo * math.sin(t)))
            if a0 < 0:
                out.append((a_culo, hc - r_culo))
    return out


def poligonos(xpiv=B.XPIV, unas=True, cargado=False, l_ancho=L_ANCHO, lch=B.LCH, r_culo=0.0):
    """Las piezas de la silueta por separado (para dibujar): cuerpo, uñas, IBC."""
    a_culo, a_mast = -xpiv, lch - xpiv
    a_pata, a_pun = a_mast + l_ancho, B.a_punta(xpiv, lch)
    hc, hp = W_CAPO / 2, W_MAX / 2
    out = [_cuerpo(a_culo, a_mast, a_pata, hc, hp, r_culo)]
    if unas:
        for s in (1, -1):
            e0, e1 = UNA_CENTRO - UNA_ANCHO / 2, UNA_CENTRO + UNA_ANCHO / 2
            out.append([(a_pata, s * e1), (a_pun, s * e1), (a_pun, s * e0), (a_pata, s * e0)])
    if cargado:
        out.append([(a_pun - B.IBC_FONDO, 0.5), (a_pun, 0.5), (a_pun, -0.5), (a_pun - B.IBC_FONDO, -0.5)])
    return out


def silueta(xpiv=B.XPIV, unas=True, cargado=False, l_ancho=L_ANCHO, paso=0.05, lch=B.LCH, r_culo=0.0):
    """Puntos del contorno en el marco del vehículo (a = 0 pivote, + hacia las uñas) y la máscara
    de los que pueden entrar a la luz de una bahía abierta (uñas y cubo por delante de las patas).
    Forma (almacen-nuevo/planificar_giro_318.py, con L_ANCHO medido): capó 1.065 del culo a la
    torre, patas 1.315 por L_ANCHO delante de la torre, uñas de 0.13 a ±0.30 hasta la punta."""
    a_culo, a_mast = -xpiv, lch - xpiv
    a_pata, a_pun = a_mast + l_ancho, B.a_punta(xpiv, lch)
    hc, hp = W_CAPO / 2, W_MAX / 2
    pts = _muestrear(_cuerpo(a_culo, a_mast, a_pata, hc, hp, r_culo), paso)
    frente = [False] * len(pts)
    if unas:
        for s in (1, -1):
            e0, e1 = UNA_CENTRO - UNA_ANCHO / 2, UNA_CENTRO + UNA_ANCHO / 2
            una = [(a_pata, s * e1), (a_pun, s * e1), (a_pun, s * e0), (a_pata, s * e0)]
            q = _muestrear(una, paso)
            pts += q; frente += [True] * len(q)
    if cargado:                                  # el IBC en las uñas: 1.20 de fondo, 1.00 de cara
        cubo = [(a_pun - B.IBC_FONDO, 0.5), (a_pun, 0.5), (a_pun, -0.5), (a_pun - B.IBC_FONDO, -0.5)]
        q = _muestrear(cubo, paso)
        pts += q; frente += [a > a_pata - 1e-9 for a, _ in q]
    return np.array(pts), np.array(frente)


def ancho_a_rumbo(sil, phi):
    """Lo que ocupa la silueta a lo ancho del pasillo con rumbo φ respecto del eje. Independiente
    de dónde esté: es la condición necesaria para girar por φ en un pasillo recto."""
    ys = sil[:, 0] * math.sin(phi) + sil[:, 1] * math.cos(phi)
    return ys.max() - ys.min()


# ── el mundo ─────────────────────────────────────────────────────────────────
class Mundo:
    """Pasillo de ancho `pasillo`, zona de descarga en x < X0, pared al fondo, y:
       v1 (05-nov, mañana): caras de rack como pared, y bahías abiertas [(nro, 'L'|'R')] donde
          SOLO las uñas/el cubo pueden pasar la cara hasta `prof`
       v2 (05-nov, el video): `rec=(rec_L, rec_R)`: el pasillo mide `pasillo` entre CARAS DE POSTE;
          en la luz de cada bahía (entre postes, los dos lados) CUALQUIER punto del equipo puede ir
          hasta rec más allá: las uñas al piso y el culo usan el retranqueo del cubo de N1"""

    def __init__(self, pasillo=B.PASILLO, abiertas=(), prof=PROF_BAHIA, holgura=B.HOLGURA,
                 zona=True, rec=None):
        self.half = pasillo / 2
        self.hol = holgura
        self.zona = zona
        self.rec = rec
        self.abiertas = []
        for nro, s in abiertas:
            x0, x1 = B.bahia_x(nro)
            self.abiertas.append((x0, x1, 1 if s == 'L' else -1, prof))

    def libre(self, X, Y, frente):
        """X, Y arreglos (..., P); frente (P,). True donde TODOS los puntos están libres."""
        h, m = self.half, self.hol
        en_zona = (X < B.X0) if self.zona else np.zeros_like(X, dtype=bool)
        sup = np.where(en_zona, B.ZONA_ANCHO / 2 - m, h - m)
        inf = -sup
        if self.rec is not None:
            rel = X - B.X0
            k = np.floor(rel / B.PASO_POSTE)
            off = rel - k * B.PASO_POSTE                   # desde la cara de atrás del poste k
            luz = (k >= 0) & (k < B.N) & (off >= B.POSTE + m) & (off <= B.PASO_POSTE - m)
            sup = np.where(luz & ~en_zona, h + self.rec[0] - m, sup)
            inf = np.where(luz & ~en_zona, -(h + self.rec[1] - m), inf)
        for x0, x1, sg, prof in self.abiertas:
            dentro = (X >= x0 + m) & (X <= x1 - m) & frente
            if sg > 0:
                sup = np.where(dentro, h + prof, sup)
            else:
                inf = np.where(dentro, -(h + prof), inf)
        ok = (Y <= sup) & (Y >= inf) & (X <= B.x_fondo() - m)
        if self.zona:
            ok &= X >= -B.ZONA_ATRAS + m
        return ok.all(axis=-1)


# ── v3 (06-nov): la silueta de la ficha (herramientas/fichas/LEEME.md, tarea_rutas_v3.md) ──
LARGO_V3 = 2.91               # culo → punta de uña, MEDIDO por maje. Manda sobre la ficha (2.65–2.78)
LCH_V3 = LARGO_V3 - B.FLEN    # culo → dorso de las uñas: 1.71 (uñas adaptadas de 1.20)
X_FICHA = 0.219               # eje de carga → dorso de las uñas, retraído (VDI 1.8)
XPIV_V3 = LCH_V3 + X_FICHA    # 1.929: DERIVADO (2.91 − 1.20 + 0.219). Se barre 1.80–1.95
R_CULO_V3 = 0.17              # esquinas del culo, del dibujo VDI (±3 cm, esquemático)
PEN_FR_V3 = 0.005             # castigo por timón en el A* (v1/v2: 0.02). Con 0.02 y ds de rueda, rotar en el
                              # lugar parecía 67 % más caro y el giro no salía en 6000 expansiones (sí en 22 700)

DS_GIRO = 0.03                # primitivas del giro en v2: el huelgo es de centímetros
HOLGURA_V2 = 0.01             # el margen del giro CARGADO sin reversa es 1 cm (rutas_resultados.md, v2)
LARGO_CARRIL = 4.0            # m de pasillo que se reserva para un cambio de carril (≈ los 4.16 medidos)

# ── primitivas ───────────────────────────────────────────────────────────────
DS, NSUB = 0.10, 5          # 2 cm por submuestra; contra una cara recta, muestrear el arco erra < 1 mm
FRACS = (-1.0, -0.6, -0.3, 0.0, 0.3, 0.6, 1.0)


FRACS_FINO = (-1.0, -0.85, -0.7, -0.55, -0.4, -0.25, -0.1, 0.0, 0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0)


class Equipo:
    def __init__(self, xpiv=B.XPIV, unas=True, cargado=False, l_ancho=L_ANCHO, fracs=FRACS, paso_sil=0.05,
                 ds=None, lch=B.LCH, r_culo=0.0, d_max=None, rueda=False, pen_fr=0.02):
        """v3: lch 1.71 (2.91 culo → punta), r_culo, d_max = 90° (modo 180°/360° del manual) y
        rueda=True (los ds son de la rueda motriz: ver step)."""
        ds = DS if ds is None else ds
        self.ds, self.rueda, self.pen_fr = ds, rueda, pen_fr
        self.xpiv, self.dmax = xpiv, (dmax(xpiv) if d_max is None else d_max)
        self.sil, self.frente = silueta(xpiv, unas, cargado, l_ancho, paso_sil, lch, r_culo)
        self.prims = []                                  # (sentido, frac, poses locales)
        LX, LY, FIN = [], [], []
        for sg in (1, -1):
            for f in fracs:
                q, poses = (0.0, 0.0, 0.0), []
                for _ in range(NSUB):
                    q = step(q, sg * ds / NSUB, f * self.dmax, rueda)
                    poses.append(q)
                self.prims.append((sg, f))
                FIN.append(q)
                c = np.array([math.cos(p[2]) for p in poses])[:, None]
                s = np.array([math.sin(p[2]) for p in poses])[:, None]
                px = np.array([p[0] for p in poses])[:, None]
                py = np.array([p[1] for p in poses])[:, None]
                LX.append(px + self.sil[:, 0] * c - self.sil[:, 1] * s)
                LY.append(py + self.sil[:, 0] * s + self.sil[:, 1] * c)
        self.LX, self.LY = np.array(LX), np.array(LY)    # (n_prim, NSUB, P)
        self.fin = FIN
        self.por_sentido = {sg: np.array([i for i, (s_, _) in enumerate(self.prims) if s_ == sg]) for sg in (1, -1)}

    def huella(self, p):
        c, s = math.cos(p[2]), math.sin(p[2])
        return (p[0] + self.sil[:, 0] * c - self.sil[:, 1] * s,
                p[1] + self.sil[:, 0] * s + self.sil[:, 1] * c)

    def libre_en(self, p, mundo):
        X, Y = self.huella(p)
        return bool(mundo.libre(X[None], Y[None], self.frente)[0])

    def sucesores(self, p, mundo, sentidos=(1, -1)):
        c, s = math.cos(p[2]), math.sin(p[2])
        idx = np.concatenate([self.por_sentido[sg] for sg in sentidos])
        LX, LY = self.LX[idx], self.LY[idx]
        WX = p[0] + LX * c - LY * s
        WY = p[1] + LX * s + LY * c
        ok = mundo.libre(WX, WY, self.frente).all(axis=1)
        out = []
        for i in idx[np.nonzero(ok)[0]]:
            fx, fy, fth = self.fin[i]
            out.append((self.prims[i], (p[0] + fx * c - fy * s, p[1] + fx * s + fy * c, p[2] + fth)))
        return out


def angdif(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


# ── metas ────────────────────────────────────────────────────────────────────
class MetaPose:
    """Llegar a (x, y, θ) con tolerancias. `recta` permite cerrar la última distancia en línea
    recta sobre el rumbo (así se aproxima de frente al rack sin buscarlo a ciegas)."""

    def __init__(self, x, y, th, tol_xy=0.04, tol_th=math.radians(2.0), recta=True, eje='y', k_th=0.33):
        """k_th: m de recorrido mínimo por radián de giro en la heurística. 0.33 = WB/tan 78° (el eje
        de carga); en v3 los ds son de la rueda motriz y el mínimo es WB (rotar en el lugar)."""
        self.x, self.y, self.th = x, y, th
        self.tol_xy, self.tol_th, self.recta, self.eje, self.k_th = tol_xy, tol_th, recta, eje, k_th

    def a_la_linea(self, p):
        """Distancia de p a la LÍNEA de la meta (por (x, y) con rumbo θ). Para un traslado es lo
        que cuenta: la meta puede venir inclinada unos grados (la tolerancia de una salida) y a
        16 m eso son 70 cm de diferencia con |y − y_meta| (corregido 05-nov)."""
        return abs(-(p[0] - self.x) * math.sin(self.th) + (p[1] - self.y) * math.cos(self.th))

    def h(self, p):
        if self.eje == 'x':                 # traslado: el largo en x lo cierra la recta final
            return self.a_la_linea(p) + self.k_th * abs(angdif(p[2], self.th))
        return math.hypot(p[0] - self.x, p[1] - self.y) + self.k_th * abs(angdif(p[2], self.th))

    @property
    def max_cierre(self):
        return 1.5 if self.eje == 'y' else 100.0

    def cerca(self, p):
        if abs(angdif(p[2], self.th)) > self.tol_th:
            return False
        if self.eje == 'y':                 # de frente a un rack: x fija, y se cierra en recta
            return abs(p[0] - self.x) <= self.tol_xy and (self.recta or abs(p[1] - self.y) <= self.tol_xy)
        return self.a_la_linea(p) <= self.tol_xy and (self.recta or abs(p[0] - self.x) <= self.tol_xy)

    def dentro(self, p):
        return self.cerca(p) and math.hypot(p[0] - self.x, p[1] - self.y) <= self.tol_xy

    def cierre(self, p):
        """Distancia con signo a recorrer en recta sobre el rumbo para quedar en la meta."""
        c, s = math.cos(p[2]), math.sin(p[2])
        if self.eje == 'y':
            return (self.y - p[1]) / s if abs(s) > 0.5 else None
        return (self.x - p[0]) / c if abs(c) > 0.5 else None


class MetaRumbo:
    """Alinearse con el pasillo con rumbo `th`, |y − y0| ≤ tol, en cualquier x (salidas)."""

    def __init__(self, th, y0=0.0, tol_y=0.30, tol_th=math.radians(3.0), k_th=0.33):
        self.th, self.y0, self.tol_y, self.tol_th, self.k_th = th, y0, tol_y, tol_th, k_th

    def h(self, p):
        return self.k_th * abs(angdif(p[2], self.th)) + max(0.0, abs(p[1] - self.y0) - self.tol_y)

    def cerca(self, p):
        return abs(angdif(p[2], self.th)) <= self.tol_th and abs(p[1] - self.y0) <= self.tol_y

    max_cierre = 0.0

    def dentro(self, p):
        return self.cerca(p)

    def cierre(self, p):
        return 0.0


# ── Hybrid A* ────────────────────────────────────────────────────────────────
def planificar(p0, meta, eq, mundo, max_exp=60000, peso=1.5, costo_cambio=COSTO_CAMBIO,
               sentidos=(1, -1), res_xy=0.05, res_th=3.0):
    """Devuelve dict(ok, prims=[(sentido, frac, ds)], poses, expansiones) o ok=False.
    sentidos=(-1,): solo reversa (una salida sin cambios de sentido = una entrada sin reversa)."""
    if not eq.libre_en(p0, mundo):
        return dict(ok=False, motivo='la pose inicial choca', expansiones=0)
    n_th = int(round(360 / res_th))
    key = lambda p, sg: (round(p[0] / res_xy), round(p[1] / res_xy),
                         round((p[2] % (2 * math.pi)) / math.radians(res_th)) % n_th, sg)
    Q = [(peso * meta.h(p0), 0.0, 0, p0, 0)]
    info = {0: (p0, None, None)}                 # id → (pose, padre, primitiva que llevó ahí)
    cierres = {}                                 # id de nodo final → (id del que cierra, cierre)
    mejor, desde = None, None                    # el cierre más barato visto y en qué expansión

    def terminar(n):
        n0, ac = cierres[n]
        prims, poses = _reconstruir(info, n0)
        for pr, q in ac:
            prims.append(pr); poses.append(q)
        return dict(ok=True, prims=prims, poses=poses, expansiones=len(visto))

    visto, cnt = {}, 1
    while Q:
        f, g, nid, p, sg = heapq.heappop(Q)
        if nid in cierres:                       # el cierre más barato salió de la cola: listo
            return terminar(nid)
        # si el único cierre que hay invierte el sentido, no se espera para siempre uno que no:
        # 3000 expansiones más y se queda con el mejor (en la zona abierta la cola es un llano)
        if mejor is not None and len(visto) - desde > 3000:
            return terminar(mejor[1])
        k = key(p, sg)
        if k in visto:
            continue
        visto[k] = g
        if meta.cerca(p) and getattr(meta, 'eje', None) == 'x':
            # traslado: se cierra EXACTO (curva en S de dos arcos + recta), no con una recta sobre
            # el rumbo que trae (ver _acomodar: así quedaban saltos de hasta 1.3 m entre piezas).
            # El cierre entra a la cola con su costo (y el del cambio de sentido, si invierte): sale
            # el más barato, no el primero que se encontró. El largo del cierre no entra al orden: la
            # recta final termina en la misma x para todos, así que g + cierre es casi constante
            ac = _acomodar(p, sg, meta, eq, mundo)
            if ac is not None:
                c = costo_cambio if sg != 0 and ac[0][0][0] != sg else 0.0
                cierres[cnt] = (nid, ac)
                if mejor is None or g + c < mejor[0]:
                    mejor = (g + c, cnt)
                    desde = desde if desde is not None else len(visto)
                heapq.heappush(Q, (g + c, g + c, cnt, ac[-1][1], 0))
                cnt += 1
        elif meta.cerca(p):
            if meta.dentro(p):                   # ya está: no se agrega un tramo de 1 cm
                prims, poses = _reconstruir(info, nid)
                return dict(ok=True, prims=prims, poses=poses, expansiones=len(visto))
            d = meta.cierre(p)
            # la recta final sigue el sentido que traía; si hay que invertirlo, cuenta como cambio
            # y se lo deja a la búsqueda (no se regala un cambio de sentido gratis)
            if d is not None and (sg == 0 or (d > 0) == (sg > 0)):
                final = _cerrar(p, d, eq, mundo, meta.max_cierre)
                if final is not None:
                    prims, poses = _reconstruir(info, nid)
                    prims.append((1 if d > 0 else -1, 0.0, abs(d)))
                    poses.append(final)
                    return dict(ok=True, prims=prims, poses=poses, expansiones=len(visto))
        if len(visto) > max_exp:
            if mejor is not None:
                return terminar(mejor[1])
            break
        for (s2, fr), q in eq.sucesores(p, mundo, sentidos):
            cambio = sg != 0 and s2 != sg
            ng = (g + eq.ds + (costo_cambio if cambio else 0.0) + (COSTO_REVERSA * eq.ds if s2 < 0 else 0.0)
                  + eq.pen_fr * abs(fr))
            heapq.heappush(Q, (ng + peso * meta.h(q), ng, cnt, q, s2))
            info[cnt] = (q, nid, (s2, fr, eq.ds))
            cnt += 1
    return dict(ok=False, motivo='sin camino', expansiones=len(visto))


def _cerrar(p, d, eq, mundo, max_d, paso=0.02):
    """Recta de largo d (con signo) sobre el rumbo de p, verificando choque. None si choca."""
    if abs(d) > max_d:
        return None
    n = max(1, int(math.ceil(abs(d) / paso)))
    q = p
    for _ in range(n):
        q = step(q, d / n, 0.0)
        if not eq.libre_en(q, mundo):
            return None
    return q


def _arco(p, sg, largo, d, n=10, rueda=False):
    q = p
    for _ in range(n):
        q = step(q, sg * largo / n, d, rueda)
    return q


def _acomodar(p, sg, meta, eq, mundo):
    """Cierre EXACTO de un traslado: dos arcos de largo ℓ (dirección δ1, δ2 resueltas por Newton
    con la cinemática exacta) que dejan lateral 0 y rumbo exacto sobre la línea de la meta, y una
    recta hasta su x. Devuelve [((sentido, frac, ds), pose), …] o None si no entra o choca.

    Corregido 05-nov: la primera versión cerraba con una recta sobre el rumbo que traía, que
    tenía hasta 2–3° de error; en 20 m de pasillo eso son decenas de cm, y unir() pegaba la pieza
    siguiente desde SU pose exacta: el salto quedaba escondido. Se vio al reproducir las rutas de
    forma continua para tarea_visibilidad.md: llegadas corridas de 17 cm (mediana) a 1.28 m."""
    th = meta.th
    u, n = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    falta = (meta.x - p[0]) * u[0] + (meta.y - p[1]) * u[1]          # a lo largo de la línea de la meta
    sgn = 1 if falta * math.cos(p[2] - th) > 0 else -1               # hacia la meta; si no es el que
    dmx = eq.dmax                                                    # traía, cuenta como cambio de sentido
    ru = eq.rueda

    def err(q):
        return ((q[0] - meta.x) * n[0] + (q[1] - meta.y) * n[1], angdif(q[2], th))

    if abs(err(p)[0]) < 1e-4 and abs(err(p)[1]) < 1e-5:
        arcos = []
        q = p
    else:
        arcos = None
        for largo in [l for l in (1.0, 0.6, 0.3, 0.15) if 2 * l <= abs(falta)]:
            d = np.zeros(2)
            for _ in range(12):
                q = _arco(_arco(p, sgn, largo, d[0], rueda=ru), sgn, largo, d[1], rueda=ru)
                e = np.array(err(q))
                if abs(e[0]) < 1e-5 and abs(e[1]) < 1e-6:
                    break
                J = np.zeros((2, 2))
                for i in range(2):
                    dd = d.copy(); dd[i] += 1e-6
                    qq = _arco(_arco(p, sgn, largo, dd[0], rueda=ru), sgn, largo, dd[1], rueda=ru)
                    J[:, i] = (np.array(err(qq)) - e) / 1e-6
                try:
                    d = d - np.linalg.solve(J, e)
                except np.linalg.LinAlgError:
                    break
            if abs(e[0]) < 1e-4 and abs(e[1]) < 1e-5 and np.all(np.abs(d) <= dmx):
                q1 = _arco(p, sgn, largo, d[0], rueda=ru)
                arcos = [((sgn, d[0] / dmx, largo), q1), ((sgn, d[1] / dmx, largo), q)]
                break
        if arcos is None:
            return None
    # la recta final, en el sentido que trae
    resto = ((meta.x - q[0]) * u[0] + (meta.y - q[1]) * u[1]) * (1 if math.cos(q[2] - th) > 0 else -1)
    if resto * sgn < -1e-6 or abs(resto) > meta.max_cierre:
        return None
    out = list(arcos)
    if abs(resto) > 1e-6:
        out.append(((sgn, 0.0, abs(resto)), step(q, resto, 0.0)))
    # choque a lo largo de todo el cierre
    prev = p
    for (sg_, fr, ds), q_fin in out:
        m = max(1, int(math.ceil(ds / 0.02)))
        r = prev
        for _ in range(m):
            r = step(r, sg_ * ds / m, fr * dmx, ru)
            if not eq.libre_en(r, mundo):
                return None
        prev = r
    return [(pr, q_fin) for pr, q_fin in out]


def saltos(res, dm=None, rueda=False):
    """Mayor salto entre poses consecutivas que NO se explica por la primitiva entre ellas
    (control de continuidad: reproducir las primitivas tiene que dar las poses)."""
    peor = 0.0
    for (sg, fr, ds), a, b in zip(res['prims'], res['poses'], res['poses'][1:]):
        m = max(1, int(math.ceil(ds / 0.02)))
        q = a
        for _ in range(m):
            q = step(q, sg * ds / m, fr * (dm or dmax(B.XPIV)), rueda)
        peor = max(peor, math.hypot(q[0] - b[0], q[1] - b[1]))
    return peor


def _reconstruir(info, nid):
    prims, poses = [], []
    while nid is not None:
        p, padre, prim = info[nid]
        poses.append(p)
        if prim is not None:
            prims.append((prim[0], prim[1], prim[2] if len(prim) > 2 else DS))
        nid = padre
    return prims[::-1], poses[::-1]


# ── tramos y tiempo ──────────────────────────────────────────────────────────
def tramos(res, eq):
    """Agrupa las primitivas por sentido. Cada tramo: sentido, largo, giro neto, tiempo."""
    out, poses = [], res['poses']
    i = 0
    for k, (sg, fr, ds) in enumerate(res['prims']):
        if not out or out[-1]['sg'] != sg:
            out.append(dict(sg=sg, largo=0.0, t_crucero=0.0, vpico=0.0, ini=poses[k], fin=None, fr=[]))
        t = out[-1]
        v = VMAN if abs(fr) > 0.45 else VMAX
        t['largo'] += ds
        t['t_crucero'] += ds / v
        t['vpico'] = max(t['vpico'], v)
        t['fin'] = poses[k + 1]
        t['fr'].append(fr)
    for t in out:
        # arranca y para en cada tramo: trapecio con ACC; si es corto, triángulo
        vp = t['vpico']
        if t['largo'] < vp ** 2 / ACC:
            t['tiempo'] = max(t['t_crucero'], 2 * math.sqrt(t['largo'] / ACC))
        else:
            t['tiempo'] = t['t_crucero'] + vp / ACC
        t['giro'] = math.degrees(angdif(t['fin'][2], t['ini'][2]))
        t['sentido'] = 'adelante (uñas primero)' if t['sg'] > 0 else 'reversa (culo primero)'
    return out


def resumen(res, eq):
    ts = tramos(res, eq)
    return dict(tramos=ts, cambios=max(0, len(ts) - 1), largo=sum(t['largo'] for t in ts),
                tiempo=sum(t['tiempo'] for t in ts))


# ── rutas: salida de bahía, entrada (= salida al revés), traslado y vueltas ────
def invertir(res):
    """La misma traza recorrida al revés. step() con punto medio es exactamente reversible:
    step(step(p, ds, δ), −ds, δ) = p. Por eso una ENTRADA a la bahía es una SALIDA invertida."""
    prims = [(-sg, fr, ds) for sg, fr, ds in reversed(res['prims'])]
    return dict(res, prims=prims, poses=list(reversed(res['poses'])))


def unir(*partes):
    """Concatena piezas. Una pieza tiene que arrancar donde terminó la anterior: si no, falla
    (antes del 05-nov esto se pegaba en silencio — ver _acomodar)."""
    prims, poses = [], []
    for r in partes:
        if not r or not r['prims']:
            continue
        if poses:
            a, b = poses[-1], r['poses'][0]
            assert math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-3 and abs(angdif(a[2], b[2])) < 1e-3, \
                f"salto entre piezas: {a} → {b}"
        prims += r['prims']
        poses += r['poses'] if not poses else r['poses'][1:]
    return dict(ok=True, prims=prims, poses=poses, expansiones=sum(r['expansiones'] for r in partes if r))


def familia(th):
    """0 = uñas hacia adentro, π = uñas hacia la descarga (rumbo alineado al pasillo)."""
    return 0.0 if math.cos(th) > 0 else math.pi


def _rumbo_txt(r):
    return 'uñas hacia adentro' if r == 0.0 else 'uñas hacia la descarga'


def costo(res):
    R = resumen(res, None)
    return R['largo'] + COSTO_CAMBIO * R['cambios']


class Planificador:
    """Arma rutas componiendo maniobras, todas con el mismo Hybrid A*:
         SALIDA     de la pose frente a un hueco hasta quedar alineado (rumbo 0 o π) en su carril
         ENTRADA    una SALIDA invertida
         TRASLADO   por el pasillo, de alineado a alineado (cambio de carril + recta)
         VUELTA     cambiar el rumbo de viaje: dos 90° por el centro de una bahía (`k s c`), o una
                    maniobra libre en la zona de descarga
       y se queda con la combinación más barata (largo + COSTO_CAMBIO por cambio de sentido).
       El A* de una sola pieza también existe (planificar), pero de 5 m de pasillo más un giro de
       huelgo de centímetros no sale en un presupuesto razonable en i3: por eso se compone.
       Cada SALIDA se busca una vez por (dirección, rumbo, carga) y se guarda."""

    def __init__(self, xpiv=B.XPIV, pasillo=B.PASILLO, prof=PROF_BAHIA, cm=B.CARRIL_CM,
                 max_exp=15000, unas=True, n_vueltas=6, modelo='v1', rec=(B.REC_L, B.REC_R),
                 holgura=None, sin_reversa=None, central=False, tol_carril=None, r_culo=None, gap=None):
        """modelo 'v1': pared + uñas en la bahía (PROF_BAHIA). 'v2': postes + retranqueo `rec` en
        los dos lados, timón fino, giro SIN cambios de sentido (como el video), holgura chica.
        'v3': el mundo y las reglas de v2 con la silueta de la ficha: 2.91 culo → punta (LCH_V3),
        culo con esquinas de `r_culo` (R_CULO_V3), δmax = 90° y XPIV_V3 si no se da otro.
        central=True: el tránsito va por el carril central y solo se baja al de giro para alinearse."""
        v3 = modelo == 'v3'
        v2 = modelo in ('v2', 'v3')
        if v3 and xpiv == B.XPIV:
            xpiv = XPIV_V3
        self.xpiv, self.pasillo, self.prof, self.cm, self.max_exp = xpiv, pasillo, prof, cm, max_exp
        self.n_vueltas, self.modelo, self.rec, self.central = n_vueltas, modelo, rec, central
        self.lch = LCH_V3 if v3 else B.LCH
        self.gap = B.GAP_OBJ if gap is None else gap        # punta de uña → cara del cubo, en el hueco
        self.k_th = WB if v3 else 0.33
        self.r_culo = (R_CULO_V3 if r_culo is None else r_culo) if v3 else 0.0
        geo = dict(lch=self.lch, r_culo=self.r_culo, d_max=math.pi / 2, rueda=True, pen_fr=PEN_FR_V3) if v3 else {}
        self.hol = (HOLGURA_V2 if v2 else B.HOLGURA) if holgura is None else holgura
        self.sin_reversa = v2 if sin_reversa is None else sin_reversa
        # v3: el giro rota casi sobre el eje de carga y termina con el eje del lado de la bahía (~0.5 m del
        # eje del pasillo): la salida acepta cualquier y alineada (el traslado acomoda el carril)
        self.tol_carril = (1.00 if v3 else 0.80 if v2 else 0.10) if tol_carril is None else tol_carril
        self.eq = {False: Equipo(xpiv, unas=unas, **geo), True: Equipo(xpiv, unas=unas, cargado=unas, **geo)}
        if v2:      # el giro: timón fino y silueta cada 2 cm (con 5 cm la esquina de un poste se cuela)
            self.eq_giro = {c: Equipo(xpiv, unas=unas, cargado=c and unas, fracs=FRACS_FINO, paso_sil=0.02,
                                      ds=DS_GIRO, **geo) for c in (False, True)}
        else:
            self.eq_giro = self.eq
        self.cache = {}

    def mundo(self, abiertas=()):
        if self.modelo in ('v2', 'v3'):
            return Mundo(self.pasillo, holgura=self.hol, rec=self.rec)
        return Mundo(self.pasillo, abiertas=abiertas, prof=self.prof, holgura=self.hol)

    def pose_hueco(self, d):
        rec = (self.rec[0] if d.s == 'L' else self.rec[1]) if self.modelo in ('v2', 'v3') else 0.0
        return B.pose_de(d, gap=self.gap, xpiv=self.xpiv, pasillo=self.pasillo, rec=rec, lch=self.lch)

    def salida(self, direccion, rumbo, cargado=False):
        d = B.leer(direccion) if isinstance(direccion, str) else direccion
        k = (repr(d), round(rumbo, 3), cargado)
        if k not in self.cache:
            x, y, th, _ = self.pose_hueco(d)
            y0 = 0.0 if self.modelo == 'v3' else B.carril(d.s, self.cm, self.pasillo)
            meta = MetaRumbo(rumbo, y0, self.tol_carril, k_th=self.k_th)
            kw = dict(sentidos=(-1,), res_xy=0.01, res_th=1.0) if self.sin_reversa else {}
            self.cache[k] = planificar((x, y, th), meta, self.eq_giro[cargado], self.mundo([(d.x, d.s)]),
                                       max_exp=self.max_exp, **kw)
        return self.cache[k]

    def entrada(self, direccion, rumbo, cargado=False):
        r = self.salida(direccion, rumbo, cargado)
        return invertir(r) if r['ok'] else r

    def traslado(self, p0, p1, cargado=False, _central=None):
        if abs(angdif(p0[2], p1[2])) > math.radians(10):
            return dict(ok=False, motivo='rumbos opuestos', expansiones=0)
        central = self.central if _central is None else _central
        if central:
            # tránsito por el carril central (idea de maje): sube al central apenas puede y baja al
            # de giro LARGO_CARRIL antes de la meta. Si no hay lugar para las dos curvas, directo
            th = familia(p1[2])
            s = 1 if p1[0] > p0[0] else -1
            if abs(p1[0] - p0[0]) > 2 * LARGO_CARRIL and (abs(p0[1]) > 0.05 or abs(p1[1]) > 0.05):
                piezas, q = [], p0
                for w in ((p0[0] + s * LARGO_CARRIL, 0.0, th) if abs(p0[1]) > 0.05 else None,
                          (p1[0] - s * LARGO_CARRIL, 0.0, th) if abs(p1[1]) > 0.05 else None, p1):
                    if w is None:
                        continue
                    r = self.traslado(q, w, cargado, _central=False)
                    if not r['ok']:
                        break
                    piezas.append(r); q = r['poses'][-1]
                else:
                    return unir(*piezas)
        th_eje = familia(p1[2])
        if abs(angdif(p1[2], th_eje)) > 1e-6:
            # la meta viene inclinada (la tolerancia de 3° de una salida): se viaja alineado al eje
            # y se corrige con UN arco corto al final. Cerrar con una recta sobre la línea inclinada
            # la saca del pasillo a 16 m (corregido 05-nov). Δθ de un arco = −(ds/WB)·tan δ, exacto
            s = 1 if (p1[0] - p0[0]) * math.cos(th_eje) > 0 else -1
            dth = angdif(th_eje, p1[2])
            ru = self.eq[cargado].rueda
            for largo in (0.5, 1.0, 0.3):
                if ru:                                      # v3: Δθ = −(ds/WB)·sin δ
                    if abs(dth * WB / (s * largo)) > 1:
                        continue
                    d = math.asin(dth * WB / (s * largo))
                else:
                    d = math.atan(-dth * WB / (-s * largo))
                if abs(d) > self.eq[cargado].dmax:
                    continue
                q = _arco(p1, -s, largo, d, rueda=ru)       # hacia atrás desde la meta
                q = (q[0], q[1], th_eje)                    # alineado exacto (error < 1e-12)
                arco = dict(ok=True, prims=[(s, d / self.eq[cargado].dmax, largo)],
                            poses=[q, _arco(q, s, largo, d, rueda=ru)], expansiones=0)
                if not all(self.eq[cargado].libre_en(_arco(q, s, largo * k / 10, d, rueda=ru), self.mundo())
                           for k in range(11)):
                    continue
                antes = self.traslado(p0, q, cargado)
                if antes['ok']:
                    arco['poses'][-1] = p1                  # la misma pose, sin el redondeo del arco
                    return unir(antes, arco)
            return dict(ok=False, motivo='no entra el arco final', expansiones=0)
        meta = MetaPose(p1[0], p1[1], p1[2], tol_xy=0.05, eje='x', k_th=self.k_th)
        if abs(p0[1] - p1[1]) < 0.10 and abs(angdif(p0[2], p1[2])) < math.radians(3):
            ac = _acomodar(p0, 0, meta, self.eq[cargado], self.mundo())   # misma línea: S corta + recta
            if ac is not None:
                return dict(ok=True, prims=[a for a, _ in ac], poses=[p0] + [q for _, q in ac], expansiones=0)
        return planificar(p0, MetaPose(p1[0], p1[1], p1[2], tol_xy=0.05, eje='x', k_th=self.k_th), self.eq[cargado],
                          self.mundo(), max_exp=self.max_exp)

    def vuelta_zona(self, p0, rumbo1, cargado=False):
        """Dar la vuelta en la zona de descarga: salir del rack, maniobrar en piso libre, quedar
        alineado con el rumbo opuesto en la boca del pasillo."""
        k = ('zona', tuple(round(v, 3) for v in p0), rumbo1, cargado)
        if k not in self.cache:
            self.cache[k] = self._vuelta_zona(p0, rumbo1, cargado)
        return self.cache[k]

    def _vuelta_zona(self, p0, rumbo1, cargado):
        eq = self.eq[cargado]
        largo_hacia = lambda r: B.a_punta(self.xpiv, self.lch) if r == 0.0 else self.xpiv
        r0 = familia(p0[2])
        x_fuera = B.X0 - B.HOLGURA - largo_hacia(r0) - 0.30      # todo el equipo fuera del rack
        ida = self.traslado(p0, (x_fuera, 0.0, r0), cargado)
        if not ida['ok']:
            return ida
        x1 = B.X0 - B.HOLGURA - largo_hacia(rumbo1) - 0.30
        giro = planificar(ida['poses'][-1], MetaPose(x1, 0.0, rumbo1, tol_xy=0.10, eje='x', k_th=self.k_th), eq,
                          self.mundo(), max_exp=4 * self.max_exp, peso=2.0)
        return unir(ida, giro) if giro['ok'] else giro

    def vueltas_bahia(self, p0, rumbo1, cargado=False, cerca_de=None, n=6):
        """Dos 90° por el centro de una bahía: entra con el rumbo que trae, sale con el otro.
        Devuelve las candidatas que existen [(res, 'k sc')], de las `n` bahías más cercanas."""
        r0 = familia(p0[2])
        x_ref = p0[0] if cerca_de is None else cerca_de
        cands = sorted(((nro, s) for nro in range(1, B.N + 1) for s in 'LR'),
                       key=lambda c: abs(B.centro_posicion(c[0], 'c') - x_ref))
        out = []
        for nro, s in cands[:n]:
            d = B.Direccion(nro, None, s, 'c')
            r_in, r_out = self.entrada(d, r0, cargado), self.salida(d, rumbo1, cargado)
            if not (r_in['ok'] and r_out['ok']):
                continue
            tr = self.traslado(p0, r_in['poses'][0], cargado)
            if tr['ok']:
                out.append((unir(tr, r_in, r_out), f"{nro} {s}c"))
        return out

    def ruta(self, p0=None, objetivo=None, origen=None, cargado=False):
        """De la pose p0 (alineada al pasillo) o de la bahía `origen`, a `objetivo` (dirección de
        bahía o pose alineada). Devuelve dict(ok, partes=[(nombre, res)], total, intentos)."""
        if origen is not None:
            arranques = []
            for r in (0.0, math.pi):
                s = self.salida(origen, r, cargado)
                if s['ok']:
                    arranques.append((r, [('SALIDA de ' + repr(B.leer(origen)), s)]))
        else:
            arranques = [(familia(p0[2]), [('INICIO', dict(ok=True, prims=[], poses=[p0], expansiones=0))])]
        if isinstance(objetivo, str):
            llegadas = []
            for r in (0.0, math.pi):
                e = self.entrada(objetivo, r, cargado)
                if e['ok']:
                    llegadas.append((r, e['poses'][0], [('ENTRADA a ' + repr(B.leer(objetivo)), e)]))
        else:
            llegadas = [(familia(objetivo[2]), objetivo, [])]
        intentos, mejor = [], None
        for r0, partes0 in arranques:
            p = partes0[-1][1]['poses'][-1]
            for r1, p1, partes1 in llegadas:
                if r0 == r1:
                    tr = self.traslado(p, p1, cargado)
                    opciones = [[('TRASLADO', tr)]] if tr['ok'] else []
                else:
                    opciones = []
                    vz = self.vuelta_zona(p, r1, cargado)
                    if vz['ok']:
                        tr = self.traslado(vz['poses'][-1], p1, cargado)
                        if tr['ok']:
                            opciones.append([('VUELTA en la zona de descarga', vz), ('TRASLADO', tr)])
                    for vb, donde in self.vueltas_bahia(p, r1, cargado, cerca_de=(p[0] + p1[0]) / 2, n=self.n_vueltas):
                        tr = self.traslado(vb['poses'][-1], p1, cargado)
                        if tr['ok']:
                            opciones.append([(f'VUELTA por la bahía {donde} (dos 90°)', vb), ('TRASLADO', tr)])
                nombre = f"sale con {_rumbo_txt(r0)}, llega con {_rumbo_txt(r1)}"
                if not opciones:
                    intentos.append((nombre, None)); continue
                medio = min(opciones, key=lambda o: costo(unir(*[x for _, x in o])))
                partes = [x for x in partes0 if x[1]['prims']] + medio + partes1
                total = unir(*[x for _, x in partes])
                intentos.append((nombre, round(costo(total), 2),
                                 [(o[0][0], round(costo(unir(*[x for _, x in o])), 2)) for o in opciones]))
                if mejor is None or costo(total) < costo(mejor['total']):
                    mejor = dict(ok=True, partes=partes, total=total)
        if mejor is None:
            return dict(ok=False, intentos=intentos, arranques=[a[0] for a in arranques],
                        llegadas=[l[0] for l in llegadas])
        mejor['intentos'] = intentos
        return mejor


# ── informe: casos 1–3, controles y barridos ─────────────────────────────────
TICK = 0.5                       # s por tick de la FSM (percepcion/fsm_estados.py)
DUR_PANTO = {'APROXIMA': 1.0, 'EXTIENDE': 1.4, 'TOMA': 1.2, 'RETRAE': 1.4}   # sim-web DUR, SUPUESTO


def _res_txt(r):
    if not r['ok']:
        return dict(ok=False, motivo=r.get('motivo', ''))
    R = resumen(r, None)
    return dict(ok=True, cambios=R['cambios'], largo=round(R['largo'], 2), tiempo=round(R['tiempo'], 1),
                tramos=[dict(sentido='adelante' if t['sg'] > 0 else 'reversa', largo=round(t['largo'], 2),
                             giro=round(t['giro']), tiempo=round(t['tiempo'], 1),
                             ini=[round(v, 3) for v in t['ini']], fin=[round(v, 3) for v in t['fin']])
                        for t in R['tramos']])


def _ruta_txt(r, pl=None):
    if not r['ok']:
        return dict(ok=False, intentos=[(a, b) for a, b, *_ in r.get('intentos', [])])
    d = _res_txt(r['total'])
    d['salto_max_m'] = (saltos(r['total']) if pl is None else
                        saltos(r['total'], pl.eq[False].dmax, pl.eq[False].rueda))
    d['partes'] = [(n, _res_txt(x)) for n, x in r['partes']]
    d['intentos'] = r['intentos']
    return d


def anchos():
    out = {}
    lim = B.PASILLO - 2 * B.HOLGURA
    for nombre, kw in (('con uñas, vacío', {}), ('con uñas, con el IBC', dict(cargado=True)),
                       ('sin uñas (chasis + patas)', dict(unas=False))):
        sil, _ = silueta(**kw)
        tabla = [(d, round(ancho_a_rumbo(sil, math.radians(d)), 3)) for d in range(0, 91, 5)]
        fino = [(k / 2, ancho_a_rumbo(sil, math.radians(k / 2))) for k in range(181)]
        mx = max(fino, key=lambda f: f[1])
        malos = [f for f, a in fino if a > lim + 1e-9]
        out[nombre] = dict(tabla=tabla, max=round(mx[1], 3), en=mx[0],
                           no_caben=(min(malos), max(malos)) if malos else None)
    return out


def caso_maje(pl, log):
    p0 = B.pose_en_pasillo('3L', 'descarga')
    out = dict(inicio=[round(v, 3) for v in p0])
    for hueco in ('5 3 Ra', '5 3 Rb'):
        ida = pl.ruta(p0, hueco)
        log(f"  caso 1 · {hueco}: ida {'ok' if ida['ok'] else 'NO'}")
        vuelta = pl.ruta(None, B.pose_descarga(pl.xpiv, pl.lch), origen=hueco, cargado=True)
        log(f"  caso 1 · {hueco}: vuelta a la descarga {'ok' if vuelta['ok'] else 'NO'}")
        h = B.altura_uña(hueco, 'entrada'); ha = B.altura_uña(hueco, 'agarre')
        vertical = dict(ELEVA=round(B.t_elevar(0, h), 1), TOMA_sube=round(ha - h, 3),
                        TRANSITO_baja=round(B.t_elevar(ha, 0), 1), **DUR_PANTO)
        out[hueco] = dict(ida=_ruta_txt(ida), vuelta=_ruta_txt(vuelta), vertical=vertical,
                          _ida=ida, _vuelta=vuelta)
    return out


def barrido(pl, log):
    p_can = (0.0, 0.0, 0.0)                          # en la descarga, uñas hacia adentro
    filas = []
    for x in range(1, B.N + 1):
        for s in 'LR':
            for p in 'ab':
                d = f"{x} {s}{p}"
                r = pl.ruta(p_can, d)
                sd, sf = pl.salida(d, math.pi), pl.salida(d, 0.0)
                filas.append(dict(dir=d, llega=_ruta_txt(r), sale_descarga=_res_txt(sd), sale_fondo=_res_txt(sf)))
                log(f"  barrido {d}: llega {'sí' if r['ok'] else 'NO'} · sale a descarga "
                    f"{'sí' if sd['ok'] else 'no'} · al fondo {'sí' if sf['ok'] else 'no'}")
    return dict(inicio=list(p_can), filas=filas)


def giro_180(log):
    p = (B.centro_posicion(4, 'c'), 0.0, 0.0)
    m = Mundo(abiertas=(), zona=False)
    out = {}
    for nombre, eq in (('con uñas', Equipo()), ('sin uñas', Equipo(unas=False))):
        r = planificar(p, MetaRumbo(math.pi, 0.0, 1.0), eq, m, max_exp=15000)
        out[nombre] = _res_txt(r); out[nombre]['expansiones'] = r['expansiones']
        log(f"  180° en el pasillo, {nombre}: {'sí' if r['ok'] else 'no'} ({r['expansiones']} expansiones)")
    pl = Planificador()
    vb = pl.vueltas_bahia(p, math.pi, n=2)
    out['dos 90°'] = [(donde, _res_txt(r)) for r, donde in vb]
    log(f"  dos 90° por una bahía: {len(vb)} bahías sirven")
    return out


def control_sin_unas(log, cms=(70, 75, 80, 90, 100, 110, 120, 130, 140, 150)):
    """Lo de planificador_giro.py: desde el carril a cm del rack opuesto, girar 90° (meta vieja:
    θ = 90°, |y| < 1.0), en un pasillo sin bahías abiertas."""
    out = {}
    m = Mundo(abiertas=(), zona=False)
    for nombre, eq in (('sin uñas', Equipo(unas=False)), ('con uñas', Equipo())):
        fila = []
        for cm in cms:
            p0 = (10.0, -(B.HALF - cm / 100), 0.0)
            if not eq.libre_en(p0, m):
                fila.append((cm, None)); continue
            r = planificar(p0, MetaRumbo(math.pi / 2, 0.0, 1.0), eq, m, max_exp=20000)
            fila.append((cm, resumen(r, None)['cambios'] if r['ok'] else None))
        out[nombre] = fila
        log(f"  control sin uñas · {nombre}: " + ' '.join(f"{c}:{'-' if v is None else v}" for c, v in fila))
    # con uñas y la bahía abierta: la ventana de carriles para entrar a 4 La / 4 Lb
    fila = []
    for cm in cms:
        pl = Planificador(cm=cm, max_exp=8000)
        ra, rb = pl.salida('4 La', 0.0), pl.salida('4 Lb', math.pi)
        fila.append((cm, resumen(ra, None)['cambios'] if ra['ok'] else None,
                     resumen(rb, None)['cambios'] if rb['ok'] else None))
    out['con uñas y bahía abierta (4 La rumbo 0 / 4 Lb rumbo π)'] = fila
    log("  control · con uñas y bahía: " + ' '.join(f"{c}:{a}/{b}" for c, a, b in fila))
    return out


def _salidas(pl, dirs=(('4 La', 0.0), ('4 La', math.pi), ('4 Lb', 0.0), ('4 Lb', math.pi),
                       ('4 Lc', 0.0), ('4 Lc', math.pi))):
    out = []
    for d, r in dirs:
        x = pl.salida(d, r)
        out.append((d, 'adentro' if r == 0.0 else 'descarga', _res_txt(x)))
    return out


def control_pasillo(log):
    out = {}
    for ancho in (3.00, 2.80):
        out[f"{ancho:.2f}"] = _salidas(Planificador(pasillo=ancho))
        log(f"  pasillo {ancho:.2f}: " + ' '.join(f"{d}→{r}:{'sí' if x['ok'] else 'no'}" for d, r, x in out[f'{ancho:.2f}']))
    return out


def barrido_xpiv(log):
    out = {}
    for xp in (1.30, 1.40, 1.50, 1.60):
        out[f"{xp:.2f}"] = dict(dmax=round(math.degrees(dmax(xp)), 1), salidas=_salidas(Planificador(xpiv=xp)))
        log(f"  XPIV {xp:.2f}: " + ' '.join(f"{d}→{r}:{'sí' if x['ok'] else 'no'}" for d, r, x in out[f'{xp:.2f}']['salidas']))
    return out


def barrido_prof(log):
    out = {}
    for pr in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
        out[f"{pr:.2f}"] = _salidas(Planificador(prof=pr))
        log(f"  PROF {pr:.2f}: " + ' '.join(f"{d}→{r}:{'sí' if x['ok'] else 'no'}" for d, r, x in out[f'{pr:.2f}']))
    return out


def tabla_fsm(pl):
    """Lo que necesita la FSM (percepcion/fsm_rutas.py), medido en la bahía 4 (lejos de la boca y
    del fondo; las maniobras no dependen de x)."""
    out = dict(TICK=TICK, VMAX=VMAX, ACC=ACC, VEL_ELEV=B.VEL_ELEV, DUR_PANTO=DUR_PANTO, salidas={})
    for s in 'LR':
        for p in 'abc':
            d = f"4 {s}{p}"
            xc = B.centro_posicion(4, p)
            for r in (0.0, math.pi):
                x = pl.salida(d, r)
                if not x['ok']:
                    out['salidas'][f"{s}{p}|{'adentro' if r == 0.0 else 'descarga'}"] = None
                    continue
                R = resumen(x, None)
                ts = R['tramos']
                out['salidas'][f"{s}{p}|{'adentro' if r == 0.0 else 'descarga'}"] = dict(
                    tiempo=round(R['tiempo'], 2), cambios=R['cambios'], largo=round(R['largo'], 2),
                    primer_tramo=round(ts[0]['tiempo'], 2), resto=round(R['tiempo'] - ts[0]['tiempo'], 2),
                    dx_fin=round(x['poses'][-1][0] - xc, 3), y_fin=round(x['poses'][-1][1], 3))
    for nombre, y0, y1 in (('central→giro', 0.0, B.carril('L')), ('giro→giro', B.carril('R'), B.carril('L'))):
        r = pl.traslado((10.0, y0, 0.0), (14.0, y1, 0.0))
        if not r['ok']:             # v3: de un carril de giro al otro en 4 m no sale (06-nov); se anota
            out[f"carril {nombre}"] = None
            continue
        R = resumen(r, None)
        out[f"carril {nombre}"] = dict(largo=round(R['largo'], 2), tiempo=round(R['tiempo'], 2),
                                       cambios=R['cambios'])
    vz = pl.vuelta_zona((B.X0 + 1.0, 0.0, 0.0), math.pi)
    out['vuelta_zona'] = _res_txt(vz) if vz['ok'] else None
    return out


# ── figura ───────────────────────────────────────────────────────────────────
def figura(maje, pl, ruta_png, pie=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle
    fig, axs = plt.subplots(2, 1, figsize=(15, 8.6))
    for ax, hueco in zip(axs, ('5 3 Ra', '5 3 Rb')):
        ida, vuelta = maje[hueco]['_ida'], maje[hueco]['_vuelta']
        h = B.HALF
        x_fin = B.x_fondo()
        ax.add_patch(Rectangle((-B.ZONA_ATRAS, -B.ZONA_ANCHO / 2), B.X0 + B.ZONA_ATRAS, B.ZONA_ANCHO,
                               fc='#f3efe4', ec='none'))
        for sg in (1, -1):
            y0 = h if sg > 0 else -h - B.FONDO_RACK
            ax.add_patch(Rectangle((B.X0, y0), B.fin_rack() - B.X0, B.FONDO_RACK, fc='#d9d9d9', ec='#888'))
            for nro in range(1, B.N + 1):
                a0, a1 = B.bahia_x(nro)
                ax.add_patch(Rectangle((a0, y0), a1 - a0, B.FONDO_RACK, fc='#ececec', ec='#aaa', lw=0.6))
                ax.text((a0 + a1) / 2, y0 + B.FONDO_RACK / 2, f"{nro}{'L' if sg > 0 else 'R'}",
                        ha='center', va='center', fontsize=8, color='#777')
        ax.plot([x_fin, x_fin], [-h - 1.1, h + 1.1], color='#555', lw=3)
        ax.plot([0], [0], marker='X', color='#c0392b', ms=10)
        ax.text(0, -0.35, 'descarga', ha='center', fontsize=8, color='#c0392b')
        d = B.leer(hueco)
        xc = B.centro_posicion(d.x, d.p)
        ax.add_patch(Rectangle((xc - 0.5, -h - B.IBC_FONDO), 1.0, B.IBC_FONDO, fc='#f5b041', ec='#b9770e'))
        for res, est, nombre in ((ida, '-', 'ida (vacío)'), (vuelta, '--', 'vuelta (con el IBC)')):
            if not res['ok']:
                continue
            tot = res['total']; poses = tot['poses']
            for k, (sg, fr, ds) in enumerate(tot['prims']):
                a, b = poses[k], poses[k + 1]
                ax.plot([a[0], b[0]], [a[1], b[1]], est, color='#1f77b4' if sg > 0 else '#d62728', lw=1.8)
            polis = poligonos(pl.xpiv, cargado=res is vuelta, lch=pl.lch, r_culo=pl.r_culo)
            cortes = [0] + [k for k in range(1, len(tot['prims'])) if tot['prims'][k][0] != tot['prims'][k - 1][0]] + [len(tot['prims'])]
            for k in cortes:
                q = poses[k]; c, sn = math.cos(q[2]), math.sin(q[2])
                for pg in polis:
                    ax.add_patch(Polygon([(q[0] + a * c - l * sn, q[1] + a * sn + l * c) for a, l in pg], closed=True,
                                         fc='none', ec='#1f77b4' if est == '-' else '#7d3c98', lw=0.8, alpha=0.75))
        R1 = resumen(ida['total'], None) if ida['ok'] else None
        R2 = resumen(vuelta['total'], None) if vuelta['ok'] else None
        tit = f"3L (uñas hacia la descarga) → {hueco} → descarga"
        if R1 and R2:
            tit += (f"   ·   ida {R1['largo']:.1f} m, {R1['cambios']} cambios de sentido, {R1['tiempo']:.0f} s"
                    f"   ·   vuelta {R2['largo']:.1f} m, {R2['cambios']} cambios, {R2['tiempo']:.0f} s")
        ax.set_title(tit, fontsize=10, loc='left')
        ax.plot([], [], color='#1f77b4', label='adelante (uñas primero)')
        ax.plot([], [], color='#d62728', label='reversa (culo primero)')
        ax.plot([], [], '--', color='#555', label='con el IBC')
        ax.legend(loc='lower left', fontsize=8, ncol=3)
        ax.set_xlim(-B.ZONA_ATRAS, x_fin + 0.3); ax.set_ylim(-h - 1.2, h + 1.2)
        ax.set_aspect('equal'); ax.set_xlabel('x a lo largo del pasillo (m) — crece hacia adentro')
        ax.set_ylabel('y (m)')
    fig.text(0.01, 0.005, pie or (f"SUPUESTOS: {B.N} bahías, poste {B.POSTE} m, X0 {B.X0} m, uñas hasta "
             f"{PROF_BAHIA * 100:.0f} cm dentro de la bahía al girar. Silueta con uñas, XPIV {B.XPIV}."),
             fontsize=8, color='#666')
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(ruta_png, dpi=130)


def main():
    """v1 (05-nov, mañana). Se conserva para poder volver: `py analisis/planificador_rutas.py --v1`."""
    import time
    t0 = time.time()
    aqui = os.path.dirname(os.path.abspath(__file__))
    log = lambda s: print(f"[{time.time() - t0:6.0f} s] {s}", flush=True)
    R = {}
    R['anchos'] = anchos(); log("anchos a rumbo listos")
    for k, v in R['anchos'].items():
        log(f"  {k}: máximo {v['max']} m a {v['en']}° · no caben de {v['no_caben']}")
    pl = Planificador()
    R['caso1'] = caso_maje(pl, log)
    figura(R['caso1'], pl, os.path.join(aqui, 'ruta_3L_5R.png')); log("figura lista")
    R['tabla_fsm'] = tabla_fsm(pl); log("tabla para la FSM lista")
    R['giro_180'] = giro_180(log)
    R['control_sin_unas'] = control_sin_unas(log)
    R['control_pasillo'] = control_pasillo(log)
    R['xpiv'] = barrido_xpiv(log)
    R['prof'] = barrido_prof(log)
    R['barrido'] = barrido(Planificador(n_vueltas=2), log)
    for h in ('5 3 Ra', '5 3 Rb'):
        R['caso1'][h].pop('_ida'); R['caso1'][h].pop('_vuelta')
    R['supuestos'] = dict(N=B.N, X0=B.X0, POSTE=B.POSTE, PROF_BAHIA=PROF_BAHIA, HOLGURA=B.HOLGURA,
                          GAP_OBJ=B.GAP_OBJ, CARRIL_CM=B.CARRIL_CM, XPIV=B.XPIV, L_ANCHO=L_ANCHO,
                          VMAX=VMAX, VMAN=VMAN, ACC=ACC, VEL_ELEV=B.VEL_ELEV, COSTO_CAMBIO=COSTO_CAMBIO)
    with open(os.path.join(aqui, 'rutas_tabla.json'), 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    log("rutas_tabla.json escrito")


# ── v2: postes, retranqueo y el giro sin reversa del video ───────────────────
XPIV_V2 = 1.60          # el menor de la grilla con el que sale el giro del video (ver validar_video)
COMBOS = (('4 La', 0.0), ('4 La', math.pi), ('4 Lb', 0.0), ('4 Lb', math.pi), ('4 Lc', 0.0), ('4 Lc', math.pi))


def _rt(r):
    return 'adentro' if r == 0.0 else 'descarga'


def giro_sin_reversa(xpiv, rec, hol, d, r, cargado, max_exp=6000):
    pl = Planificador(modelo='v2', xpiv=xpiv, rec=(rec, rec), holgura=hol, max_exp=max_exp)
    return pl.salida(d, r, cargado)


def umbral_xpiv(log, xps=(1.50, 1.52, 1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.66), recs=(0.03, 0.06, 0.09)):
    """¿Con qué XPIV (y su δmax por la fórmula de ficha) aparece el giro SIN reversa, holgura 0?
    Solo La y Lc: la Lb es el espejo de la La (Lb→descarga = La→adentro)."""
    out = {}
    for rec in recs:
        for c in (False, True):
            fila = {}
            for xp in xps:
                fila[f"{xp:.2f}"] = {f"{d}→{_rt(r)}": giro_sin_reversa(xp, rec, 0.0, d, r, c)['ok']
                                     for d, r in (('4 La', 0.0), ('4 La', math.pi), ('4 Lc', 0.0))}
            out[f"rec {rec:.2f} {'cargado' if c else 'vacío'}"] = fila
            log(f"  umbral XPIV · rec {rec:.2f} {'cargado' if c else 'vacío'}: " +
                ' '.join(f"{xp}:" + ''.join('S' if v else '·' for v in f.values()) for xp, f in fila.items()))
    return out


def margen(xpiv, rec, d, r, c, pasos=(0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)):
    """La mayor holgura (contra postes y caras de cubo) con la que el giro sin reversa sigue saliendo."""
    mejor, res = None, None
    for h in pasos:
        x = giro_sin_reversa(xpiv, rec, h, d, r, c)
        if not x['ok']:
            break
        mejor, res = h, x
    return mejor, res


def validar_video(log, xpiv=XPIV_V2, rec=B.REC_L):
    """Para cada hueco a/b/c y sentido de viaje, vacío y cargado: ¿sale sin reversa?, margen, carril."""
    out = {}
    for d, r in COMBOS:
        for c in (False, True):
            m, x = margen(xpiv, rec, d, r, c)
            fila = dict(ok=m is not None, margen_cm=None if m is None else round(100 * m))
            if x is not None:
                R = resumen(x, None)
                f = x['poses'][-1]
                fila.update(largo=round(R['largo'], 2), carril_cm=round(100 * (B.HALF - abs(f[1]))),
                            y_carril=round(f[1], 3))
            out[f"{d}→{_rt(r)} {'cargado' if c else 'vacío'}"] = fila
            log(f"  video · {d} con {_rt(r)}, {'cargado' if c else 'vacío'}: "
                f"{'sale' if fila['ok'] else 'NO sale'}" + (f", margen {fila['margen_cm']} cm, termina a "
                f"{fila['carril_cm']} cm del rack {'R' if d.endswith('Lc') or 'L' in d else 'L'}" if fila['ok'] else ''))
    return out


def retranqueo_minimo(log, xps=(1.50, 1.60), recs=(0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09)):
    out = {}
    for xp in xps:
        for c in (False, True):
            for d, r in (('4 La', 0.0), ('4 Lc', 0.0)):
                fila = {f"{rec:.2f}": giro_sin_reversa(xp, rec, 0.0, d, r, c)['ok'] for rec in recs}
                minimo = next((k for k, v in fila.items() if v), None)
                out[f"XPIV {xp:.2f} {d}→{_rt(r)} {'cargado' if c else 'vacío'}"] = dict(fila=fila, minimo=minimo)
                log(f"  retranqueo mínimo · XPIV {xp} {d} {'cargado' if c else 'vacío'}: {minimo} · "
                    + ''.join('S' if v else '·' for v in fila.values()))
    return out


def rutas_v2(log, xpiv=XPIV_V2):
    """Caso de maje y barrido con el modelo v2, con y sin la regla del carril central."""
    out = {}
    for central in (False, True):
        pl = Planificador(modelo='v2', xpiv=xpiv, central=central, n_vueltas=2)
        nom = 'central' if central else 'libre'
        caso = {}
        p0 = B.pose_en_pasillo('3L', 'descarga')
        for h in ('5 3 Ra', '5 3 Rb'):
            ida = pl.ruta(p0, h)
            vuelta = pl.ruta(None, B.pose_descarga(pl.xpiv, pl.lch), origen=h, cargado=True)
            caso[h] = dict(ida=_ruta_txt(ida), vuelta=_ruta_txt(vuelta))
            log(f"  rutas v2 {nom} · {h}: ida {_corto(ida)} · vuelta {_corto(vuelta)}")
        filas = []
        for x in range(1, B.N + 1):
            for s in 'LR':
                for p in 'ab':
                    r = pl.ruta((0.0, 0.0, 0.0), f"{x} {s}{p}")
                    filas.append(dict(dir=f"{x} {s}{p}", llega=_ruta_txt(r)))
        log(f"  rutas v2 {nom} · barrido: llegan {sum(f['llega']['ok'] for f in filas)}/{len(filas)}")
        out[nom] = dict(caso1=caso, barrido=filas, tabla_fsm=tabla_fsm(pl))
    return out


def _corto(r):
    if not r['ok']:
        return 'NO'
    R = resumen(r['total'], None)
    return f"{R['largo']:.1f} m, {R['cambios']} cambios, {R['tiempo']:.0f} s"


def main_v2():
    import time
    t0 = time.time()
    aqui = os.path.dirname(os.path.abspath(__file__))
    log = lambda s: print(f"[{time.time() - t0:6.0f} s] {s}", flush=True)
    R = dict(supuestos=dict(XPIV_V2=XPIV_V2, REC=(B.REC_L, B.REC_R), POSTE=B.POSTE, PASO_POSTE=B.PASO_POSTE,
                            HOLGURA_V2=HOLGURA_V2, DS_GIRO=DS_GIRO, FRACS_FINO=FRACS_FINO,
                            LARGO_CARRIL=LARGO_CARRIL))
    lim = B.PASILLO + B.REC_L + B.REC_R
    R['cuenta'] = {k: dict(max=v['max'], entre_postes=lim, sobra_cm=round(100 * (lim - v['max']), 1))
                   for k, v in anchos().items()}
    log(f"cuenta: entre postes {lim:.2f} m · " + ' · '.join(f"{k}: sobra {v['sobra_cm']} cm" for k, v in R['cuenta'].items()))
    R['base_1_50'] = {f"{d}→{_rt(r)} {'cargado' if c else 'vacío'}": giro_sin_reversa(1.50, B.REC_L, 0.0, d, r, c)['ok']
                      for d, r in COMBOS for c in (False, True)}
    log(f"con XPIV 1.50 (δmax 78°), holgura 0: salen {sum(R['base_1_50'].values())}/{len(R['base_1_50'])}")
    R['umbral_xpiv'] = umbral_xpiv(log)
    R['video'] = validar_video(log)
    R['retranqueo'] = retranqueo_minimo(log)
    R['control_rec0'] = {f"{d}→{_rt(r)} {'cargado' if c else 'vacío'}": giro_sin_reversa(XPIV_V2, 0.0, 0.0, d, r, c)['ok']
                         for d, r in COMBOS for c in (False, True)}
    log(f"CONTROL retranqueo 0 (XPIV {XPIV_V2}): salen {sum(R['control_rec0'].values())}/{len(R['control_rec0'])}")
    R['rutas'] = rutas_v2(log)
    with open(os.path.join(aqui, 'rutas_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    log("rutas_v2.json escrito")




# ── v3: la silueta de la ficha — 2.91 de culo a punta, culo redondeado, δmax 90° ──
COMBOS3 = (('4 La', 0.0), ('4 La', math.pi), ('4 Lc', 0.0))     # la Lb es el espejo de la La


def giro_v3(d, r, cargado, xpiv=XPIV_V3, r_culo=R_CULO_V3, rec=B.REC_L, hol=0.0, max_exp=6000, gap=None):
    pl = Planificador(modelo='v3', xpiv=xpiv, r_culo=r_culo, rec=(rec, rec), holgura=hol, max_exp=max_exp,
                      gap=gap)
    return pl.salida(d, r, cargado)


def anchos_v3(radios=(0.0, 0.10, 0.17, 0.24)):
    """La cuenta de herramientas/fichas/LEEME.md con la silueta del planificador: ancho a rumbo
    máximo (no depende de XPIV: es la forma)."""
    out = {}
    for r in radios:
        fila = {}
        for c in (False, True):
            sil, _ = silueta(XPIV_V3, cargado=c, paso=0.005, lch=LCH_V3, r_culo=r)
            fino = [(k / 4, ancho_a_rumbo(sil, math.radians(k / 4))) for k in range(361)]
            mx = max(fino, key=lambda f: f[1])
            fila['cargado' if c else 'vacío'] = dict(max=round(float(mx[1]), 3), en=mx[0])
        out[f"{r:.2f}"] = fila
    return out


def _forma_giro(x):
    """Cuánto se mueve el eje de carga en el giro (0 = rota en el lugar) y cuánto la rueda motriz."""
    a, b = x['poses'][0], x['poses'][-1]
    return dict(rueda_m=round(sum(ds for _, _, ds in x['prims']), 2),
                eje_m=round(math.hypot(b[0] - a[0], b[1] - a[1]), 3),
                giro=round(math.degrees(angdif(b[2], a[2]))),
                fr_max=round(max(abs(fr) for _, fr, _ in x['prims']), 2))


def validar_video_v3(log):
    """Nominal (XPIV 1.93, culo 0.17, retranqueo 6 cm): ¿sale sin reversa?, con qué margen, y cómo.
    Para medir el margen la punta arranca a max(3 cm, holgura + 0.5 cm) del cubo: con la de siempre
    (3 cm), una holgura de 4 cm ya hace chocar la pose de arranque y el margen topaba en 3."""
    out = {}
    for d, r in COMBOS:
        for c in (False, True):
            mejor, res = None, None
            for h in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10):
                x = giro_v3(d, r, c, hol=h, gap=max(B.GAP_OBJ, h + 0.005))
                if not x['ok']:
                    break
                mejor, res = h, x
            fila = dict(ok=mejor is not None, margen_cm=None if mejor is None else round(100 * mejor))
            if res is not None:
                f = giro_v3(d, r, c, hol=HOLGURA_V2) if mejor >= HOLGURA_V2 else res
                fila.update(_forma_giro(f), largo=round(resumen(f, None)['largo'], 2),
                            y_fin=round(f['poses'][-1][1], 3))
            out[f"{d}→{_rt(r)} {'cargado' if c else 'vacío'}"] = fila
            log(f"  video v3 · {d} con {_rt(r)}, {'cargado' if c else 'vacío'}: "
                + (f"sale, margen {fila['margen_cm']} cm, rueda {fila['rueda_m']} m, eje de carga se mueve "
                   f"{fila['eje_m']} m" if fila['ok'] else 'NO sale'))
    return out


def sensibilidad_v3(log, radios=(0.10, 0.17, 0.24), xps=(1.80, 1.93), recs=(0.0, 0.03, 0.06)):
    """Holgura 0. ¿Con qué (radio del culo, XPIV, retranqueo) sale el giro sin reversa? Con
    retranqueo 0 es «todo dentro de los 3.00»."""
    out = {}
    for c in (False, True):
        for xp in xps:
            for r in radios:
                fila = {f"{rec:.2f}": [giro_v3(d, rr, c, xp, r, rec)['ok'] for d, rr in COMBOS3] for rec in recs}
                out[f"{'cargado' if c else 'vacío'} · XPIV {xp:.2f} · culo {r:.2f}"] = fila
                log(f"  sensibilidad · {'cargado' if c else 'vacío '} XPIV {xp:.2f} culo {r:.2f}: " +
                    ' '.join(f"rec {k}:" + ''.join('S' if v else '·' for v in f) for k, f in fila.items()))
    return out


def barrido_xpiv_v3(log, xps=(1.80, 1.85, 1.90, 1.93, 1.95), recs=(0.0, 0.06)):
    out = {}
    for c in (False, True):
        for rec in recs:
            fila = {f"{xp:.2f}": [giro_v3(d, rr, c, xp, R_CULO_V3, rec)['ok'] for d, rr in COMBOS3] for xp in xps}
            out[f"{'cargado' if c else 'vacío'} · rec {rec:.2f}"] = fila
            log(f"  XPIV v3 · {'cargado' if c else 'vacío '} rec {rec:.2f}: " +
                ' '.join(f"{k}:" + ''.join('S' if v else '·' for v in f) for k, f in fila.items()))
    return out


def control_v3(log):
    """Culo en ángulo recto y retranqueo 0, holgura 0: cargado pide 3.088 > 3.00 → NO tiene que salir.
    Vacío (3.045) tampoco. Si sale, algo no está restringiendo."""
    out = {}
    for c in (True, False):
        out['cargado' if c else 'vacío'] = {f"{d}→{_rt(r)}": giro_v3(d, r, c, r_culo=0.0, rec=0.0)['ok']
                                             for d, r in COMBOS}
        log(f"  CONTROL culo recto, retranqueo 0, {'cargado' if c else 'vacío'}: salen "
            f"{sum(out['cargado' if c else 'vacío'].values())}/{len(COMBOS)}")
    return out


def rutas_v3(log):
    out, pls = {}, {}
    for central in (False, True):
        pl = Planificador(modelo='v3', central=central, n_vueltas=2)
        nom = 'central' if central else 'libre'
        caso = {}
        p0 = B.pose_en_pasillo('3L', 'descarga')
        for h in ('5 3 Ra', '5 3 Rb'):
            ida = pl.ruta(p0, h)
            vuelta = pl.ruta(None, B.pose_descarga(pl.xpiv, pl.lch), origen=h, cargado=True)
            caso[h] = dict(ida=_ruta_txt(ida, pl), vuelta=_ruta_txt(vuelta, pl), _ida=ida, _vuelta=vuelta)
            log(f"  rutas v3 {nom} · {h}: ida {_corto(ida)} · vuelta {_corto(vuelta)}")
        filas = []
        for x in range(1, B.N + 1):
            for s in 'LR':
                for p in 'ab':
                    r = pl.ruta((0.0, 0.0, 0.0), f"{x} {s}{p}")
                    filas.append(dict(dir=f"{x} {s}{p}", llega=_ruta_txt(r, pl)))
        ok = [f for f in filas if f['llega']['ok']]
        log(f"  rutas v3 {nom} · barrido: llegan {len(ok)}/{len(filas)} · cambios de sentido "
            f"{sorted(set(f['llega']['cambios'] for f in ok))}")
        out[nom] = dict(caso1=caso, barrido=filas, tabla_fsm=tabla_fsm(pl))
        pls[nom] = pl
    return out, pls


def main_v3():
    import time
    t0 = time.time()
    aqui = os.path.dirname(os.path.abspath(__file__))
    log = lambda s: print(f"[{time.time() - t0:6.0f} s] {s}", flush=True)
    R = dict(supuestos=dict(LARGO_V3=LARGO_V3, LCH_V3=round(LCH_V3, 3), X_FICHA=X_FICHA, XPIV_V3=round(XPIV_V3, 3),
                            R_CULO_V3=R_CULO_V3, DMAX=90, REC=(B.REC_L, B.REC_R), POSTE=B.POSTE,
                            PASO_POSTE=B.PASO_POSTE, HOLGURA_V2=HOLGURA_V2, DS_GIRO=DS_GIRO, FRACS_FINO=FRACS_FINO,
                            W_MAX=W_MAX, W_CAPO=W_CAPO, L_ANCHO=L_ANCHO, cinematica='ds de la rueda motriz'))
    R['anchos'] = anchos_v3()
    for r, f in R['anchos'].items():
        log(f"ancho a rumbo · culo {r}: vacío {f['vacío']['max']} a {f['vacío']['en']}° · "
            f"cargado {f['cargado']['max']} a {f['cargado']['en']}°")
    R['video'] = validar_video_v3(log)
    R['control'] = control_v3(log)
    R['sensibilidad'] = sensibilidad_v3(log)
    R['xpiv'] = barrido_xpiv_v3(log)
    R['rutas'], pls = rutas_v3(log)
    pl = pls['central']
    figura(R['rutas']['central']['caso1'], pl, os.path.join(aqui, 'ruta_3L_5R_v3.png'),
           pie=f"v3: 2.91 culo → punta, culo con esquinas de {pl.r_culo} m, XPIV {pl.xpiv:.3f} (derivado), δmax 90°, "
               f"postes cada {B.PASO_POSTE} m, retranqueo {B.REC_L * 100:.0f} cm, holgura {HOLGURA_V2 * 100:.0f} cm, "
               f"carril central. SUPUESTOS: {B.N} bahías, X0 {B.X0} m.")
    log("figura lista")
    for nom in R['rutas']:
        for h in ('5 3 Ra', '5 3 Rb'):
            R['rutas'][nom]['caso1'][h].pop('_ida'); R['rutas'][nom]['caso1'][h].pop('_vuelta')
    with open(os.path.join(aqui, 'rutas_v3.json'), 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    log("rutas_v3.json escrito")


if __name__ == "__main__":
    if '--v1' in sys.argv:
        main()          # lo del 05-nov a la mañana: pared + uñas en la bahía (rutas_tabla.json v1)
    elif '--v2' in sys.argv:
        main_v2()       # postes + retranqueo + giro sin reversa (rutas_v2.json)
    else:
        main_v3()       # la silueta de la ficha: 2.91, culo redondeado, δmax 90° (rutas_v3.json)
