# ─────────────────────────────────────────────────────────────────────────────
# Visibilidad de ArUco a lo largo de las rutas — qué ve cada cámara y qué espaciado hace falta
#
#   py percepcion/rutas_densas.py      # una vez: recorridos densos del planificador (~10 min)
#   py percepcion/visibilidad.py       # visibilidad + barrido de espaciado con el EKF + controles
#
# Encargo: tarea_visibilidad.md. Primera pasada en 2D+altura, sin Isaac: sin luz, sin motion blur,
# sin oclusión por gente ni por otro equipo. Lo que no está medido dice SUPUESTO.
#
# Marcas: SOLO en las caras de los racks, los dos lados (nada en las cabeceras: quedan lejos). Se
#   ponen sobre los postes, cada `paso` × 2.47 m (paso de bahía = 2.35 + poste 0.12); medio paso
#   pone una también a mitad de bahía. A H_MARCA de altura, de lado L.
# Cámara: la C920 calibrada (LEEME, 03-nov): fx 623.4, fy 623.5, centro (349.1, 252.4), 640×480,
#   FOV horizontal 54.3°. Modelo estenopeico sin distorsión.
# Se ve una marca si: las 4 esquinas caen dentro de la imagen y delante de la cámara, mide al menos
#   PX_MIN px (raíz del área proyectada) y el ángulo de incidencia es menor que ANG_MAX.
# ─────────────────────────────────────────────────────────────────────────────
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'analisis'))
import bahias as B                                                          # noqa: E402
from ekf import EKF, ColocacionMarcas, R_pose, envolver, marca_vista_desde, pose_desde_marca  # noqa: E402
from odometria import avanzar                                               # noqa: E402

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ── SUPUESTOS (maje mide PX_MIN y ANG_MAX en casa; ver tarea_visibilidad.md) ──
PX_MIN = 20.0                   # SUPUESTO: lado mínimo de la marca en la imagen, px
ANG_MAX = math.radians(60)      # SUPUESTO: incidencia máxima (0 = de frente)
H_MARCA = 1.00                  # SUPUESTO: altura del centro de la marca sobre el poste, m
L_MARCA = 0.15                  # marca de 15 cm (la impresa y medida, LEEME)
PERIODO_CAM = 0.10              # 10 Hz, como sim_sintetico.py
DT = 0.02                       # SYNC del bus (docs/21)
REQ_LAT = 0.045                 # ±4.5 cm lateral al llegar a la bahía (aruco_precision.py)
PASO_BAHIA = B.BAHIA + B.POSTE  # 2.47 m entre postes
PAUSA_SENTIDO = 0.5             # SUPUESTO: quieto en cada cambio de sentido, s
PAUSA_HUECO = 20.0              # ELEVA 7 s + pantógrafo ~5 s + TRANSITO 7 s (rutas_resultados.md)

# ruido de la medición: el de sim_sintetico.py (lado pesimista de aruco_precision.py) a 1.5 m,
# escalado con la distancia: lateral ∝ d, profundidad ∝ d², ángulo ∝ 1/px. SUPUESTO
SIG_REF = dict(d=1.5, dist=0.02, lat=0.005, yaw=math.radians(2.0), px=623.4 * 0.15 / 1.5)
SIG_COLOCACION = 0.01           # SUPUESTO, como sim_sintetico.py
SESGO_V, SESGO_D = 1.02, math.radians(0.5)    # odometría: SUPUESTOS de sim_sintetico.py
RUIDO_V, RUIDO_D = 0.02, math.radians(0.5)

W_IMG, H_IMG = 640, 480
FX, FY, CX, CY = 623.4, 623.5, 349.1, 252.4


# ── cámaras y montajes ───────────────────────────────────────────────────────
class Camara:
    """Montaje respecto del eje de carga: (cx adelante, cy a la izquierda, h altura), yaw (0 =
    hacia las uñas, +90° = a la izquierda), pitch (negativo = hacia abajo), FOV horizontal."""

    def __init__(self, nombre, cx, cy, h, yaw_deg, pitch_deg=0.0, fov_deg=54.3):
        self.nombre, self.cx, self.cy, self.h = nombre, cx, cy, h
        self.yaw, self.pitch = math.radians(yaw_deg), math.radians(pitch_deg)
        esc = math.tan(math.radians(54.3) / 2) / math.tan(math.radians(fov_deg) / 2)
        self.fx, self.fy = FX * esc, FY * esc            # mismo sensor, otra óptica

    @property
    def montaje2d(self):
        return (self.cx, self.cy, self.yaw)


X_CAPO = -0.75                  # SUPUESTO: a media capota
Y_CAPO = 1.065 / 2             # costado de la capota (W_CAPO / 2)
MONTAJES = {
    'A': ('lateral + trasera (la idea de maje)',
          [Camara('lateral', X_CAPO, Y_CAPO, 1.0, 90), Camara('trasera', -B.XPIV, 0.0, 1.0, 180)]),
    'A2': ('lateral + trasera en diagonal (135°)',
           [Camara('lateral', X_CAPO, Y_CAPO, 1.0, 90), Camara('trasera diag.', -B.XPIV, 0.0, 1.0, -135)]),
    'B': ('dos laterales (lo de sim_sintetico.py)',
          [Camara('lateral izq.', X_CAPO, Y_CAPO, 1.0, 90), Camara('lateral der.', X_CAPO, -Y_CAPO, 1.0, -90)]),
    'C': ('dos laterales altas en la jaula, hacia abajo',
          [Camara('alta izq.', X_CAPO, 0.40, 2.2, 90, -47), Camara('alta der.', X_CAPO, -0.40, 2.2, -90, -47)]),
    'D': ('frontal + lateral (docs/03)',
          [Camara('frontal', B.LCH - B.XPIV, 0.0, 2.2, 0, -10), Camara('lateral', X_CAPO, Y_CAPO, 1.0, 90)]),
}


# ── el mapa ──────────────────────────────────────────────────────────────────
def mapa(paso, lado=L_MARCA):
    """Marcas en las dos caras, sobre los postes cada `paso` bahías (0.5 = también a mitad de
    bahía). paso=None → una sola marca por cara, a mitad del pasillo (control).
    Devuelve arreglo (n, 6): x, y, h, θ normal, lado, id."""
    x0, x1 = B.X0 + B.POSTE / 2, B.fin_rack() - B.POSTE / 2
    xs = [(x0 + x1) / 2] if paso is None else list(np.arange(x0, x1 + 1e-6, paso * PASO_BAHIA))
    filas = []
    for x in xs:
        filas.append((x, +B.HALF, H_MARCA, -math.pi / 2, lado))
        filas.append((x, -B.HALF, H_MARCA, +math.pi / 2, lado))
    M = np.array(filas)
    return np.c_[M, np.arange(len(M))]


def _esquinas(M):
    """(n, 4, 3) esquinas de cada marca: cuadrado vertical sobre la cara del rack."""
    t = np.c_[np.cos(M[:, 3] + math.pi / 2), np.sin(M[:, 3] + math.pi / 2), np.zeros(len(M))]
    up = np.array([0.0, 0.0, 1.0])
    c = M[:, :3]
    l2 = M[:, 4:5] / 2
    return np.stack([c - t * l2 - up * l2, c + t * l2 - up * l2, c + t * l2 + up * l2, c - t * l2 + up * l2], 1)


def visibles(pose, cam, M, E=None, px_min=None, ang_max=None):
    """Índices de las marcas que ve `cam` desde `pose`, y su tamaño en px."""
    px_min = PX_MIN if px_min is None else px_min
    ang_max = ANG_MAX if ang_max is None else ang_max
    E = _esquinas(M) if E is None else E
    x, y, th = pose
    c, s = math.cos(th), math.sin(th)
    p = np.array([x + cam.cx * c - cam.cy * s, y + cam.cx * s + cam.cy * c, cam.h])
    a = th + cam.yaw
    cp, sp = math.cos(cam.pitch), math.sin(cam.pitch)
    f = np.array([math.cos(a) * cp, math.sin(a) * cp, sp])
    r = np.array([math.sin(a), -math.cos(a), 0.0])
    d = np.cross(f, r)
    rel = E - p
    z = rel @ f
    delante = (z > 0.05).all(1)
    zz = np.where(z > 0.05, z, 1.0)
    u = cam.fx * (rel @ r) / zz + CX
    v = cam.fy * (rel @ d) / zz + CY
    dentro = delante & (u >= 0).all(1) & (u <= W_IMG).all(1) & (v >= 0).all(1) & (v <= H_IMG).all(1)
    area = 0.5 * np.abs((u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]) + (u[:, 1] * v[:, 2] - u[:, 2] * v[:, 1])
                        + (u[:, 2] * v[:, 3] - u[:, 3] * v[:, 2]) + (u[:, 3] * v[:, 0] - u[:, 0] * v[:, 3]))
    px = np.sqrt(area)
    hacia = p - M[:, :3]
    dist = np.linalg.norm(hacia, axis=1)
    n = np.c_[np.cos(M[:, 3]), np.sin(M[:, 3]), np.zeros(len(M))]
    inc = np.arccos(np.clip((hacia * n).sum(1) / dist, -1, 1))
    ok = dentro & (px >= px_min) & (inc <= ang_max)
    return np.nonzero(ok)[0], px, dist


# ── del recorrido del planificador a una trayectoria en el tiempo ────────────
def trayectoria(ruta, dmax):
    """Entradas verdaderas (v, δ) cada DT y etiquetas, reproduciendo las primitivas del planificador
    con el perfil de velocidad de planificador_rutas (VMAX recto, VMAN con mucha dirección, ACC).
    Devuelve dict de arreglos: t, pose, v, d, parte, clase, cargado, y los índices de llegada."""
    import planificador_rutas as P
    pose = tuple(ruta['inicio'])
    T, DTS, POS, V, D, PARTE, CARGA = [], [], [], [], [], [], []
    llegadas, t = [], 0.0

    def quieto(seg, parte, carg):
        nonlocal t
        for _ in range(int(round(seg / DT))):
            t += DT; T.append(t); DTS.append(DT); POS.append(pose); V.append(0.0); D.append(0.0)
            PARTE.append(parte); CARGA.append(carg)

    for pierna in ruta['piernas']:
        prims, carg = pierna['prims'], pierna['cargado']
        # tramos: primitivas seguidas con el mismo sentido
        tramos, actual = [], []
        for pr in prims:
            if actual and pr[1] != actual[-1][1]:
                tramos.append(actual); actual = []
            actual.append(pr)
        if actual:
            tramos.append(actual)
        for k, tr in enumerate(tramos):
            # piezas de 1 cm con su límite de velocidad
            piezas = []
            for parte, sg, fr, ds in tr:
                n = max(1, int(math.ceil(ds / 0.01)))
                lim = P.VMAN if abs(fr) > 0.45 else P.VMAX
                piezas += [(parte, sg, fr, ds / n, lim)] * n
            nb = len(piezas) + 1
            vb = np.zeros(nb)
            for i in range(1, nb):                                # acelera
                vb[i] = min(piezas[i - 1][4], math.sqrt(vb[i - 1] ** 2 + 2 * P.ACC * piezas[i - 1][3]))
            vb[-1] = 0.0
            for i in range(nb - 2, -1, -1):                       # frena
                vb[i] = min(vb[i], math.sqrt(vb[i + 1] ** 2 + 2 * P.ACC * piezas[i][3]),
                            piezas[i][4] if i < len(piezas) else 9)
            # un paso por pieza, con su propio dt: la verdad es EXACTAMENTE la traza del planificador
            # (la primera versión iba en pasos fijos de 20 ms con la dirección de una sola pieza y
            # se corría hasta 60 cm al llegar)
            for i, (parte, sg, fr, ds, _) in enumerate(piezas):
                v = max(0.02, (vb[i] + vb[i + 1]) / 2)
                dt = ds / v
                d = fr * dmax
                pose = avanzar(pose, sg * v, d, dt)
                t += dt
                T.append(t); DTS.append(dt); POS.append(pose); V.append(sg * v); D.append(d)
                PARTE.append(parte); CARGA.append(carg)
            if k < len(tramos) - 1:
                quieto(PAUSA_SENTIDO, tr[-1][0], carg)
        if any(p[0] == 'ENTRADA' for p in prims):
            llegadas.append(len(T) - 1)
            quieto(PAUSA_HUECO, 'HUECO', carg)
    POS = np.array(POS)
    phi = np.degrees(np.abs(np.arcsin(np.abs(np.sin(POS[:, 2])))))      # 0 = alineado al pasillo, 90 = de frente al rack
    clase = []
    for parte, f, v in zip(PARTE, phi, V):
        if parte == 'HUECO':
            clase.append('en el hueco')
        elif abs(v) < 1e-6:
            clase.append('quieto')
        elif f < 3:
            clase.append('tránsito')                          # alineado al pasillo
        elif parte == 'TRASLADO' and f < 25:
            clase.append('cambio de carril')                  # la curva en S
        elif f >= 80:
            clase.append('alineación')                        # de frente al rack
        else:
            clase.append('giro')
    T = np.array(T)
    cuadros = np.searchsorted(T, np.arange(PERIODO_CAM, T[-1], PERIODO_CAM))   # 10 Hz
    return dict(t=T, dt=np.array(DTS), pose=POS, v=np.array(V), d=np.array(D), parte=PARTE, clase=clase,
                cargado=np.array(CARGA), llegadas=llegadas, cuadros=np.unique(cuadros))


# ── visibilidad por recorrido ────────────────────────────────────────────────
CLASES = ('tránsito', 'cambio de carril', 'giro', 'alineación')


def cobertura(tr, camaras, M, **kw):
    """Por cuadro de cámara (10 Hz): cuántas cámaras ven al menos una marca."""
    E = _esquinas(M)
    idx = list(tr['cuadros'])
    n = np.zeros(len(idx), int)
    por_cam = np.zeros((len(idx), len(camaras)), bool)
    for j, i in enumerate(idx):
        for k, cam in enumerate(camaras):
            vis, _, _ = visibles(tr['pose'][i], cam, M, E, **kw)
            por_cam[j, k] = len(vis) > 0
        n[j] = por_cam[j].sum()
    return np.array(idx), n, por_cam


def resumen_cobertura(tr, idx, n):
    """% del tiempo con 0/1/2 cámaras por clase de tramo, y el tramo ciego más largo (en
    movimiento: m y s). Quieto en el hueco o en un cambio de sentido no cuenta."""
    cl = [tr['clase'][i] for i in idx]
    out = {}
    for c in CLASES + ('total',):
        sel = np.array([(x in CLASES) if c == 'total' else (x == c) for x in cl])
        if sel.sum() == 0:
            out[c] = None; continue
        out[c] = [round(100 * np.mean(n[sel] == k), 1) for k in (0, 1, 2)]
    # tramo ciego más largo EN MOVIMIENTO: quieto (en el hueco, en un cambio de sentido) la
    # odometría no deriva, así que ese tiempo no cuenta ni corta la racha
    pos = tr['pose'][idx][:, :2]
    paso_m = np.r_[0.0, np.hypot(*np.diff(pos, axis=0).T)]
    mejor_m = mejor_s = act_m = act_s = 0.0
    for j in range(len(idx)):
        if cl[j] not in CLASES:
            continue
        if n[j] == 0:
            act_m += paso_m[j]; act_s += PERIODO_CAM
            mejor_m, mejor_s = max(mejor_m, act_m), max(mejor_s, act_s)
        else:
            act_m = act_s = 0.0
    out['ciego_m'], out['ciego_s'] = round(mejor_m, 2), round(mejor_s, 1)
    return out


# ── el EKF a lo largo del recorrido ──────────────────────────────────────────
def sigmas(dist, px):
    k = dist / SIG_REF['d']
    return np.array([SIG_REF['dist'] * k * k, SIG_REF['lat'] * k, SIG_REF['yaw'] * SIG_REF['px'] / max(px, 1.0)])


def correr_ekf(tr, camaras, M, semilla, activa=None, **kw):
    """EKF con odometría sesgada y las marcas que se ven. activa(clase, k_cam) → bool permite
    apagar una cámara en ciertos tramos. Devuelve el error lateral en cada llegada (m)."""
    rng = np.random.default_rng(semilla)
    rmed = np.random.default_rng(semilla + 10_000)
    E = _esquinas(M)
    creido = {int(m[5]): (m[0] + rng.normal(0, SIG_COLOCACION), m[1] + rng.normal(0, SIG_COLOCACION), m[3])
              for m in M}
    p0 = tr['pose'][0]
    pose0 = p0 + rng.normal(0, [0.05, 0.05, math.radians(1.0)])
    f = EKF(pose0, np.diag([0.10 ** 2, 0.10 ** 2, math.radians(3) ** 2]))
    coloc = ColocacionMarcas(SIG_COLOCACION)
    errores, llegadas = [], set(tr['llegadas'])
    cuadros = set(tr['cuadros'].tolist())
    ult = max(tr['llegadas'])
    for i in range(1, ult + 1):
        v, d, dt = tr['v'][i], tr['d'][i], tr['dt'][i]
        moviendo = abs(v) > 1e-6
        k = math.sqrt(DT / dt)                  # mismo ruido por segundo que a 20 ms (sim_sintetico)
        v_med = v * SESGO_V + (rng.normal(0, RUIDO_V * k) if moviendo else 0.0)
        d_med = d + SESGO_D + (rng.normal(0, RUIDO_D * k) if moviendo else 0.0)
        f.predict(v_med, d_med, dt)
        verdad = tr['pose'][i]
        if i in cuadros:
            for k, cam in enumerate(camaras):
                if activa is not None and not activa(tr['clase'][i], k):
                    continue
                vis, px, dist = visibles(verdad, cam, M, E, **kw)
                for j in vis:
                    mk = M[j]
                    dd, lat, yaw = marca_vista_desde(verdad, (mk[0], mk[1], mk[3]), cam.montaje2d)
                    sg = sigmas(dist[j], px[j])
                    z = np.array([dd, lat, yaw]) + rmed.normal(0, sg)
                    cid = int(mk[5])
                    z_pose = pose_desde_marca(creido[cid], *z, cam.montaje2d)
                    R = R_pose(creido[cid], *z, cam.montaje2d, np.diag(sg ** 2)) + coloc.R(cid, tr['t'][i])
                    f.update_aruco(z_pose, R)
        if i in llegadas:
            e = f.pose - verdad
            th = verdad[2]
            errores.append(-math.sin(th) * e[0] + math.cos(th) * e[1])
    return errores


# ── el informe ───────────────────────────────────────────────────────────────
PASOS = (0.5, 1, 2, 3, 4, None)     # marcas cada N bahías (0.5 = también a mitad); None = una por cara
SEMILLAS = 6
RUTAS_EKF = ['maje_Ra', 'maje_Rb'] + [f'barrido_{x}{s}{p}' for x in (2, 4, 6) for s in 'LR' for p in 'ab']


def _txt_paso(p):
    if p is None:
        return 'una por cara'
    return f"{p:g} bahía{'' if p == 1 else 's'} ({p * PASO_BAHIA:.2f} m)"


def evaluar_ekf(trs, camaras, paso, lado=L_MARCA, activa=None, semillas=SEMILLAS, **kw):
    M = mapa(paso, lado)
    errs = []
    for tr in trs:
        for s in range(semillas):
            errs += correr_ekf(tr, camaras, M, s, activa, **kw)
    e = np.abs(np.array(errs))
    return dict(ok=bool((e < REQ_LAT).all()), fuera=int((e >= REQ_LAT).sum()), n=len(e),
                max_cm=round(100 * e.max(), 2), p95_cm=round(100 * np.percentile(e, 95), 2))


def paso_maximo(fila):
    """El mayor paso de la grilla que cumple, con todos los más chicos cumpliendo también."""
    mejor = None
    for p in PASOS:
        if p is None:
            continue
        if not fila[p]['ok']:
            break
        mejor = p
    return mejor


def cobertura_agregada(trs, camaras, paso, lado=L_MARCA, **kw):
    M = mapa(paso, lado)
    cuenta = {c: np.zeros(3) for c in CLASES + ('total',)}
    ciego_m = ciego_s = 0.0
    for tr in trs:
        idx, n, _ = cobertura(tr, camaras, M, **kw)
        cl = [tr['clase'][i] for i in idx]
        for c in CLASES:
            sel = np.array([x == c for x in cl])
            for k in range(3):
                cuenta[c][k] += np.sum(n[sel] == k)
                cuenta['total'][k] += np.sum(n[sel] == k)
        r = resumen_cobertura(tr, idx, n)
        ciego_m, ciego_s = max(ciego_m, r['ciego_m']), max(ciego_s, r['ciego_s'])
    pct = {c: (None if v.sum() == 0 else [round(100 * x / v.sum(), 1) for x in v]) for c, v in cuenta.items()}
    return dict(pct=pct, ciego_m=ciego_m, ciego_s=ciego_s)


def figura(nombre, desc, camaras, trs, paso, ruta_png):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    M = mapa(paso)
    fig, axs = plt.subplots(len(trs), 1, figsize=(14, 3.6 * len(trs)))
    axs = np.atleast_1d(axs)
    for ax, (rn, tr) in zip(axs, trs.items()):
        for sg in (1, -1):
            y0 = B.HALF if sg > 0 else -B.HALF - B.FONDO_RACK
            ax.add_patch(Rectangle((B.X0, y0), B.fin_rack() - B.X0, B.FONDO_RACK, fc='#eeeeee', ec='#999'))
            for nro in range(1, B.N + 1):
                a0, a1 = B.bahia_x(nro)
                ax.text((a0 + a1) / 2, y0 + B.FONDO_RACK / 2, f"{nro}{'L' if sg > 0 else 'R'}",
                        ha='center', va='center', fontsize=7, color='#888')
        ax.plot(M[:, 0], M[:, 1], 's', ms=4, color='k')
        idx, n, _ = cobertura(tr, camaras, M)
        col = np.array(['#d62728', '#ff9f1c', '#2ca02c'])[n]
        P = tr['pose'][idx]
        ax.scatter(P[:, 0], P[:, 1], c=col, s=7, zorder=3)
        for i in tr['llegadas']:
            ax.plot(*tr['pose'][i][:2], marker='*', ms=13, color='#1f77b4', zorder=4)
        r = resumen_cobertura(tr, idx, n)
        tot = r['total']
        ax.set_title(f"{rn}: 0/1/2 cámaras {tot[0]:.0f} / {tot[1]:.0f} / {tot[2]:.0f} % del tiempo en movimiento · "
                     f"tramo ciego más largo {r['ciego_m']:.1f} m, {r['ciego_s']:.1f} s", fontsize=9, loc='left')
        ax.set_xlim(-2.5, B.x_fondo()); ax.set_ylim(-B.HALF - 1.2, B.HALF + 1.2); ax.set_aspect('equal')
    for c, t in (('#d62728', 'ninguna cámara ve marcas'), ('#ff9f1c', 'una'), ('#2ca02c', 'las dos')):
        axs[0].scatter([], [], c=c, s=20, label=t)
    axs[0].legend(loc='lower left', fontsize=8, ncol=3)
    fig.suptitle(f"Montaje {nombre} · {desc} · marcas cada {_txt_paso(paso)} · PX_MIN {PX_MIN:.0f} px, "
                 f"ANG_MAX {math.degrees(ANG_MAX):.0f}° (SUPUESTOS)", fontsize=10)
    fig.tight_layout()
    fig.savefig(ruta_png, dpi=110)
    plt.close(fig)


def main():
    import json
    import time
    import rutas_densas
    t0 = time.time()
    log = lambda s: print(f"[{time.time() - t0:5.0f} s] {s}", flush=True)
    D = rutas_densas.cargar()
    trs = {k: trayectoria(r, D['dmax']) for k, r in D['rutas'].items()}
    log(f"{len(trs)} recorridos")
    ekf_trs = [trs[k] for k in RUTAS_EKF]
    todos = list(trs.values())
    R = dict(supuestos=dict(PX_MIN=PX_MIN, ANG_MAX=math.degrees(ANG_MAX), H_MARCA=H_MARCA, L_MARCA=L_MARCA,
                            SEMILLAS=SEMILLAS, RUTAS_EKF=RUTAS_EKF), cobertura={}, ekf={}, una_camara={},
             sensibilidad={}, controles={})

    # 1 · visibilidad, todos los recorridos
    for m, (desc, cams) in MONTAJES.items():
        R['cobertura'][m] = {str(p): cobertura_agregada(todos, cams, p) for p in PASOS}
        c = R['cobertura'][m]['1']
        log(f"cobertura {m}: 1 bahía → 0/1/2 {c['pct']['total']} · ciego {c['ciego_m']} m")

    # 2 · el EKF: ¿llega a ±4.5 cm?
    for m, (desc, cams) in MONTAJES.items():
        fila = {p: evaluar_ekf(ekf_trs, cams, p) for p in PASOS}
        R['ekf'][m] = {str(p): v for p, v in fila.items()}
        R['ekf'][m]['maximo'] = paso_maximo(fila)
        log(f"EKF {m}: " + ' · '.join(f"{_txt_paso(p).split(' (')[0]} {'sí' if v['ok'] else 'no'} ({v['max_cm']} cm)"
                                      for p, v in fila.items()) + f" → máximo {R['ekf'][m]['maximo']}")

    # 3 · ¿alcanza una sola cámara en el giro y la alineación?
    en_giro = ('giro', 'alineación', 'en el hueco', 'quieto')
    for m, (desc, cams) in MONTAJES.items():
        R['una_camara'][m] = {}
        for k, cam in enumerate(cams):
            act = (lambda kk: (lambda clase, j: j == kk or clase not in en_giro))(k)
            fila = {p: evaluar_ekf(ekf_trs, cams, p, activa=act) for p in PASOS if p is not None}
            fila[None] = dict(ok=False)
            R['una_camara'][m][cam.nombre] = dict(maximo=paso_maximo(fila),
                                                  **{str(p): v for p, v in fila.items() if p is not None})
            log(f"una cámara en el giro, {m} solo {cam.nombre}: máximo {R['una_camara'][m][cam.nombre]['maximo']}")

    # 4 · cuánto depende de lo no medido (PX_MIN, ANG_MAX) y del lado de la marca
    for etiqueta, kw, lado in (('pesimista: 30 px, 45°', dict(px_min=30, ang_max=math.radians(45)), L_MARCA),
                               ('optimista: 15 px, 75°', dict(px_min=15, ang_max=math.radians(75)), L_MARCA),
                               ('marca de 30 cm', {}, 0.30)):
        R['sensibilidad'][etiqueta] = {}
        for m in ('A', 'B'):
            cams = MONTAJES[m][1]
            fila = {p: evaluar_ekf(ekf_trs, cams, p, lado=lado, **kw) for p in PASOS}
            cob = cobertura_agregada(todos, cams, 1, lado=lado, **kw)
            R['sensibilidad'][etiqueta][m] = dict(maximo=paso_maximo(fila), cobertura_1=cob,
                                                  **{str(p): v for p, v in fila.items()})
            log(f"sensibilidad {etiqueta}, {m}: máximo {paso_maximo(fila)}")

    # 5 · controles
    R['controles']['una_por_cara'] = {m: R['ekf'][m][str(None)] for m in MONTAJES}
    angosta = [Camara(cm.nombre, cm.cx, cm.cy, cm.h, math.degrees(cm.yaw), math.degrees(cm.pitch), fov_deg=5)
               for cm in MONTAJES['A'][1]]
    R['controles']['fov_5'] = dict(A=cobertura_agregada(todos, angosta, 1), A_normal=R['cobertura']['A']['1'])
    log(f"control FOV 5°: ciego {R['controles']['fov_5']['A']['ciego_m']} m contra "
        f"{R['cobertura']['A']['1']['ciego_m']} m con 54.3°")
    sin_marcas = evaluar_ekf(ekf_trs, MONTAJES['A'][1], 1, px_min=1e9)
    R['controles']['sin_marcas'] = sin_marcas
    log(f"control sin marcas (solo odometría): {sin_marcas}")

    # 6 · figuras
    for m, (desc, cams) in MONTAJES.items():
        figura(m, desc, cams, {k: trs[k] for k in ('maje_Ra', 'maje_Rb')}, 1,
               os.path.join(AQUI, f"visibilidad_{m}.png"))
    log("figuras")
    with open(os.path.join(AQUI, 'visibilidad_resultados.json'), 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    log("visibilidad_resultados.json escrito")


if __name__ == "__main__":
    main()
