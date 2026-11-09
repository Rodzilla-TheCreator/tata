"""Datos de la simulación del pasillo (sim/simulacion.html): un turno de cuatro pedidos con el
planificador v3b (Hybrid A*, silueta de la ficha, δmax 90°), la FSM de etapas, el pantógrafo y la
elevación con los tiempos de la ficha, el margen a postes y caras en cada instante, y qué ArUco ve
cada cámara (montaje A2, marcas cada 2 bahías, percepcion/visibilidad.py).

    python sim/exportar.py            # ~11 min en la i3: 8 rutas de ~80 s
    python sim/build.py               # mete los datos en simulacion.html

Todo lo que no está medido es SUPUESTO y está marcado en `supuestos` del .json.
"""
import json
import math
import os
import sys
import time

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'analisis'))
sys.path.insert(0, os.path.join(RAIZ, 'percepcion'))
import bahias as B                    # noqa: E402
import planificador_rutas as P        # noqa: E402
import visibilidad as V               # noqa: E402

# ── tiempos de la ficha VDI del ETR 335d (herramientas/fichas/LEEME.md) ──
V_SUBE = (0.84, 0.55)       # m/s elevación vacío / cargado (VDI 5.2)
V_BAJA = (0.57, 0.53)       # descenso vacío / cargado (VDI 5.3)
V_EMPUJE = (0.30, 0.28)     # pantógrafo vacío / cargado (VDI 5.4)
EXT_MAX = 1.067             # empuje, doble profundidad (VDI 4.28)
H_VIAJE = 0.05              # SUPUESTO: altura de las uñas al viajar y al girar
T_MIN = 0.8                 # SUPUESTO: cada etapa quieta dura al menos esto (asentar, confirmar)
INSERTA = B.IBC_FONDO + B.GAP_OBJ - EXT_MAX   # lo que falta meter con el equipo (APROXIMA): 0.163 m
DT_VIS = 0.25               # s entre cálculos de visibilidad

PEDIDOS = [  # (de dónde arranca, hueco). El primero es el caso de maje (3L → 5 3 Ra → descarga)
    ('3L', '5 3 Ra'),
    ('descarga', '2 1A Lb'),
    ('descarga', '7 5 Rb'),
    ('descarga', '4 2 La'),
]


def perfil(prims):
    """Velocidad en cada nodo de un tramo (mismo sentido): VMAX recto, VMAN con mucho timón, ACC,
    arranca y para en cero. Los ds son de la rueda motriz (v3)."""
    n = len(prims)
    vt = [P.VMAN if abs(fr) > 0.45 else P.VMAX for _, fr, _ in prims]
    v = [0.0] * (n + 1)
    for k in range(n):
        v[k + 1] = min(vt[k], math.sqrt(v[k] ** 2 + 2 * P.ACC * prims[k][2]))
    v[n] = 0.0
    for k in range(n - 1, -1, -1):
        v[k] = min(v[k], math.sqrt(v[k + 1] ** 2 + 2 * P.ACC * prims[k][2]))
    return v


def mover(res, etapa, t0, cargado):
    """Muestras (t, x, y, th, δ, sentido, v) de un movimiento del planificador, desde t0."""
    prims, poses = res['prims'], res['poses']
    out, t = [], t0
    i = 0
    while i < len(prims):
        j = i
        while j < len(prims) and prims[j][0] == prims[i][0]:
            j += 1
        tr = prims[i:j]
        v = perfil(tr)
        for k, (sg, fr, ds) in enumerate(tr):
            p = poses[i + k]
            out.append(dict(t=t, x=p[0], y=p[1], th=p[2], d=fr * math.pi / 2, sg=sg, v=v[k] * sg,
                            e=etapa, c=cargado))
            vm = (v[k] + v[k + 1]) / 2
            t += ds / vm if vm > 1e-6 else 2 * math.sqrt(ds / P.ACC)
        i = j
    p = poses[-1]
    out.append(dict(t=t, x=p[0], y=p[1], th=p[2], d=0.0, sg=0, v=0.0, e=etapa, c=cargado))
    return out, t


def quieto(pose, etapa, t0, dur, cargado):
    return [dict(t=t0, x=pose[0], y=pose[1], th=pose[2], d=0.0, sg=0, v=0.0, e=etapa, c=cargado)], t0 + dur


def recta_local(pose, dist, n=8):
    """Avanzar `dist` sobre el rumbo (APROXIMA / RETROCEDE frente al hueco), como res del planificador."""
    poses = [(pose[0] + dist * k / n * math.cos(pose[2]), pose[1] + dist * k / n * math.sin(pose[2]), pose[2])
             for k in range(n + 1)]
    sg = 1 if dist > 0 else -1
    return dict(prims=[(sg, 0.0, abs(dist) / n)] * n, poses=poses)


def nombre_parte(n, ida):
    if n == 'TRASLADO':
        return 'RECTA' if ida else 'TRANSITO'
    if n.startswith('ENTRADA'):
        return 'GIRO'
    if n.startswith('SALIDA'):
        return 'DESGIRA'
    if n.startswith('VUELTA'):
        return 'VUELTA'
    return n


def pedido(pl, desde, hueco, log):
    """Ida vacío → toma → vuelta cargado → deja. Devuelve (muestras, etapas verticales, resumen)."""
    p0 = B.pose_en_pasillo(desde, 'descarga') if desde != 'descarga' else B.pose_descarga(pl.xpiv, pl.lch)
    t = time.time()
    ida = pl.ruta(p0, hueco)
    log(f'   ida a {hueco}: {"ok" if ida["ok"] else "NO"} ({time.time() - t:.0f} s)')
    t = time.time()
    vuelta = pl.ruta(None, B.pose_descarga(pl.xpiv, pl.lch), origen=hueco, cargado=True)
    log(f'   vuelta: {"ok" if vuelta["ok"] else "NO"} ({time.time() - t:.0f} s)')
    if not (ida['ok'] and vuelta['ok']):
        raise RuntimeError(f'sin ruta para {hueco}')
    return ida, vuelta


def armar(pl, rutas):
    """La línea de tiempo completa del turno: muestras de pose y la parte vertical (h, ext, ibc)."""
    S, Vt = [], []                  # muestras de pose; eventos verticales (t, h, ext, ibc)
    t = 0.0
    h, ext = H_VIAJE, 0.0
    pedidos = []

    def vert(t, h, ext, ibc, e):
        Vt.append(dict(t=t, h=h, ext=ext, ibc=ibc, e=e))

    vert(0.0, h, ext, 'ninguno', 'LIBRE')
    for n, (desde, hueco, ida, vuelta) in enumerate(rutas):
        t_ini = t
        d = B.leer(hueco)
        h_ent, h_agr = B.altura_uña(hueco, 'entrada'), B.altura_uña(hueco, 'agarre')
        # ── ida, vacío ──
        for nom, res in ida['partes']:
            m, t = mover(res, nombre_parte(nom, True), t, False)
            S += m
            vert(t, h, ext, 'rack', nombre_parte(nom, True))
        pose = ida['total']['poses'][-1]
        # ── la toma ──
        for etapa, dur, h1, e1, ibc in (
                ('ELEVA', abs(h_ent - h) / V_SUBE[0], h_ent, 0.0, 'rack'),
                ('APROXIMA', None, h_ent, 0.0, 'rack'),
                ('EXTIENDE', EXT_MAX / V_EMPUJE[0], h_ent, EXT_MAX, 'rack'),
                ('TOMA', (h_agr - h_ent) / V_SUBE[1], h_agr, EXT_MAX, 'uñas'),
                ('RETRAE', EXT_MAX / V_EMPUJE[1], h_agr, 0.0, 'uñas'),
                ('RETROCEDE', None, h_agr, 0.0, 'uñas'),
                ('BAJA', abs(h_agr - H_VIAJE) / V_BAJA[1], H_VIAJE, 0.0, 'uñas')):
            if etapa in ('APROXIMA', 'RETROCEDE'):
                dist = INSERTA if etapa == 'APROXIMA' else -INSERTA
                m, t1 = mover(recta_local(pose, dist), etapa, t, etapa == 'RETROCEDE')
                m[-1]['x'], m[-1]['y'] = (m[-1]['x'], m[-1]['y'])
                S += m
                pose = (pose[0] + dist * math.cos(pose[2]), pose[1] + dist * math.sin(pose[2]), pose[2])
                vert(t, h, ext, ibc, etapa)
                t = max(t1, t + T_MIN)
            else:
                m, t1 = quieto(pose, etapa, t, max(dur, T_MIN), ibc == 'uñas')
                S += m
                vert(t, h, ext, ibc, etapa)
                t = t1
                h, ext = h1, e1
            vert(t, h, ext, ibc, etapa)
        # ── vuelta, cargado ──
        for nom, res in vuelta['partes']:
            m, t = mover(res, nombre_parte(nom, False), t, True)
            S += m
            vert(t, h, ext, 'uñas', nombre_parte(nom, False))
        pose = vuelta['total']['poses'][-1]
        m, t1 = quieto(pose, 'DEJA', t, max(H_VIAJE / V_BAJA[1], T_MIN), True)
        S += m
        vert(t, h, ext, 'uñas', 'DEJA')
        t = t1
        h = 0.0
        vert(t, h, ext, 'descarga', 'DEJA')
        h = H_VIAJE
        vert(t + 0.4, h, ext, 'descarga', 'LIBRE')
        S.append(dict(t=t, x=pose[0], y=pose[1], th=pose[2], d=0.0, sg=0, v=0.0, e='LIBRE', c=False))
        pedidos.append(dict(n=n + 1, desde=desde, hueco=hueco, t0=round(t_ini, 2), t1=round(t, 2),
                            lado=d.s, nivel=d.y, x_bahia=d.x, pos=d.p,
                            ida=dict(largo=round(P.resumen(ida['total'], None)['largo'], 2),
                                     cambios=P.resumen(ida['total'], None)['cambios']),
                            vuelta=dict(largo=round(P.resumen(vuelta['total'], None)['largo'], 2),
                                        cambios=P.resumen(vuelta['total'], None)['cambios'])))
    return S, Vt, pedidos


def holguras(pl, S):
    """Margen (m) entre la silueta y el límite más cercano (cara de poste, o cara del cubo de N1 en la
    luz de la bahía, 6 cm atrás), con holgura 0, y el punto que lo da. Fuera del rack (zona), None."""
    out = []
    for s in S:
        eq = pl.eq[s['c']]
        X, Y = eq.huella((s['x'], s['y'], s['th']))
        rel = X - B.X0
        k = np.floor(rel / B.PASO_POSTE)
        off = rel - k * B.PASO_POSTE
        luz = (k >= 0) & (k < B.N) & (off >= B.POSTE) & (off <= B.PASO_POSTE)
        en_rack = (X >= B.X0) & (X <= B.fin_rack())
        sup = np.where(luz, B.HALF + pl.rec[0], B.HALF)
        inf = np.where(luz, -(B.HALF + pl.rec[1]), -B.HALF)
        hol = np.minimum(sup - Y, Y - inf)
        hol = np.where(en_rack, hol, np.inf)
        j = int(np.argmin(hol))
        out.append(None if not np.isfinite(hol[j]) else [round(float(hol[j]), 4), round(float(X[j]), 3),
                                                         round(float(Y[j]), 3)])
    return out


def vista(pl, S):
    """Qué marcas ve cada cámara del montaje A2, cada DT_VIS (interpolando la pose)."""
    M = V.mapa(2)
    E = V._esquinas(M)
    cams = V.montajes(pl.xpiv)['A2'][1]
    ts = np.array([s['t'] for s in S])
    out = []
    t = 0.0
    while t <= ts[-1]:
        j = max(0, int(np.searchsorted(ts, t, 'right')) - 1)
        s = S[j]
        fila = [round(t, 2)]
        for c in cams:
            ids, px, dist = V.visibles((s['x'], s['y'], s['th']), c, M, E)
            fila.append([int(i) for i in ids])
        out.append(fila)
        t += DT_VIS
    marcas = [dict(id=int(m[5]), x=round(float(m[0]), 3), y=round(float(m[1]), 3)) for m in M]
    camaras = [dict(nombre=c.nombre, cx=round(c.cx, 3), cy=round(c.cy, 3), yaw=round(c.yaw, 4)) for c in cams]
    return out, marcas, camaras


def main():
    log = lambda s: print(s, flush=True)
    t0 = time.time()
    pl = P.Planificador(modelo='v3')
    rutas = []
    for desde, hueco in PEDIDOS:
        log(f'pedido {len(rutas) + 1}: {desde} → {hueco} → descarga')
        rutas.append((desde, hueco, *pedido(pl, desde, hueco, log)))
    S, Vt, pedidos = armar(pl, rutas)
    log(f'{len(S)} muestras de pose, turno de {S[-1]["t"]:.0f} s; holguras y visibilidad…')
    hol = holguras(pl, S)
    vis, marcas, camaras = vista(pl, S)
    piezas = {}
    for c in (False, True):
        pol = P.poligonos(pl.xpiv, cargado=c, lch=pl.lch, r_culo=pl.r_culo)
        piezas['cargado' if c else 'vacio'] = [[[round(a, 4), round(y, 4)] for a, y in p] for p in pol]
    a_mast = pl.lch - pl.xpiv
    datos = dict(
        generado=time.strftime('%Y-%m-%d %H:%M'),
        supuestos=dict(modelo='v3b (planificador_rutas.py, modelo=v3, culo de la ficha)', XPIV=round(pl.xpiv, 3),
                       WB=P.WB, DMAX=90, REC=list(pl.rec), VMAX=P.VMAX, VMAN=P.VMAN, ACC=P.ACC,
                       V_SUBE=V_SUBE, V_BAJA=V_BAJA, V_EMPUJE=V_EMPUJE, EXT_MAX=EXT_MAX, H_VIAJE=H_VIAJE,
                       T_MIN=T_MIN, INSERTA=round(INSERTA, 3), montaje='A2', marcas_cada=2,
                       PX_MIN=V.PX_MIN, ANG_MAX=round(math.degrees(V.ANG_MAX)),
                       nota='VMAX/VMAN/ACC, H_VIAJE, T_MIN, PX_MIN, ANG_MAX y la geometría del rack son SUPUESTOS'),
        geo=dict(PASILLO=B.PASILLO, X0=B.X0, N=B.N, POSTE=B.POSTE, BAHIA=B.BAHIA, PASO=B.PASO_POSTE,
                 FONDO_RACK=B.FONDO_RACK, ZONA_ANCHO=B.ZONA_ANCHO, ZONA_ATRAS=B.ZONA_ATRAS, X_FONDO=B.x_fondo(),
                 FIN_RACK=B.fin_rack(), IBC=[B.IBC_CARA, B.IBC_FONDO], ALTURAS=B.ALTURAS,
                 descarga=list(B.pose_descarga(pl.xpiv, pl.lch))),
        equipo=dict(piezas=piezas, xpiv=pl.xpiv, a_mast=a_mast, a_pata=a_mast + P.L_ANCHO,
                    a_punta=B.a_punta(pl.xpiv, pl.lch), wb=P.WB, rueda=[0.343, 0.140], w_capo=P.W_CAPO,
                    w_max=P.W_MAX),
        pedidos=pedidos,
        S=[[round(s['t'], 3), round(s['x'], 4), round(s['y'], 4), round(s['th'], 4), round(s['d'], 3), s['sg'],
            round(s['v'], 3), s['e'], int(s['c'])] for s in S],
        H=hol,
        V=[[round(v['t'], 3), round(v['h'], 3), round(v['ext'], 3), v['ibc'], v['e']] for v in Vt],
        vis=vis, marcas=marcas, camaras=camaras)
    with open(os.path.join(RAIZ, 'sim', 'sim_datos.json'), 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
    log(f'listo en {time.time() - t0:.0f} s → sim/sim_datos.json')


if __name__ == '__main__':
    main()
