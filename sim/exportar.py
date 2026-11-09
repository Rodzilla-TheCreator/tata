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

# El turno, con el flujo de RETHINK (docs/09): el montacargas humano deja los cubos que ENTRAN en la zona de
# carga del fondo (junto al último rack R, maje 09-nov) y recoge los que SALEN al principio del pasillo.
#   ('salida', desde, hueco)   desde (pose '3L', 'principio' o una bahía) → toma en hueco → deja en el principio
#   ('entrada', desde, hueco)  desde → toma en la zona de carga → deja en hueco
ZONA = None                 # se arma adentro de geometria('dxf'): la «bahía» N + 1, lado R, al piso
PEDIDOS = [
    ('salida', '3L', '5 3 Ra'),            # el caso de maje
    ('entrada', 'principio', '11 2 Lb'),
    ('salida', '11 2 Lb', '9 5 Rb'),
    ('entrada', 'principio', '3 1B La'),
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


DESCARGA = None             # la zona de descarga como «bahía» 0 (lado R, al piso): se arma adentro de geometria('dxf')


def _pose(pl, lugar):
    if lugar == 'principio':
        return B.pose_descarga(pl.xpiv, pl.lch)
    return B.pose_en_pasillo(lugar, 'descarga')


def _lugar(v):
    """'principio' es la zona de descarga cuando la geometría la tiene."""
    return DESCARGA if (v == 'principio' and DESCARGA) else v


def _ruta(pl, desde, hasta, cargado, log, txt):
    """Ruta del planificador entre poses o direcciones (str con espacio = dirección de bahía)."""
    t = time.time()
    desde, hasta = _lugar(desde), _lugar(hasta)
    es_dir = lambda v: isinstance(v, B.Direccion) or (isinstance(v, str) and ' ' in v)
    if es_dir(desde):
        objetivo = hasta if es_dir(hasta) else _pose(pl, hasta)
        r = pl.ruta(None, objetivo, origen=desde, cargado=cargado)
    else:
        r = pl.ruta(_pose(pl, desde), hasta if es_dir(hasta) else _pose(pl, hasta), cargado=cargado)
    log(f'   {txt}: {"ok" if r["ok"] else "NO"} ({time.time() - t:.0f} s)')
    if not r['ok']:
        raise RuntimeError(f'sin ruta: {txt}')
    return r


def planificar_turno(pl, log):
    """Las rutas de cada pedido: [(tipo, desde, hueco, ida, vuelta)]."""
    out = []
    for tipo, desde, hueco in PEDIDOS:
        log(f'pedido {len(out) + 1}: {tipo} {desde} → {hueco}')
        if tipo == 'salida':
            ida = _ruta(pl, desde, hueco, False, log, f'{desde} → {hueco}, vacío')
            vuelta = _ruta(pl, hueco, 'principio', True, log, f'{hueco} → principio, cargado')
        else:
            ida = _ruta(pl, desde, ZONA, False, log, f'{desde} → zona de carga, vacío')
            vuelta = _ruta(pl, ZONA, hueco, True, log, f'zona de carga → {hueco}, cargado')
        out.append((tipo, desde, hueco, ida, vuelta))
    return out


def armar(pl, rutas):
    """La línea de tiempo del turno: muestras de pose (S), parte vertical (V: h, ext, ibc, etapa) y los
    cubos que se ven quietos (en el rack, en la zona de carga, recién dejados en el principio)."""
    S, Vt, cubos, pedidos = [], [], [], []
    t, h, ext = 0.0, H_VIAJE, 0.0
    a_ibc = B.a_punta(pl.xpiv, pl.lch) + EXT_MAX - 0.6        # centro del cubo con las uñas extendidas

    def vert(e, ibc):
        Vt.append(dict(t=t, h=h, ext=ext, ibc=ibc, e=e))

    def mundo_de(pose, a):
        return [pose[0] + a * math.cos(pose[2]), pose[1] + a * math.sin(pose[2]), pose[2]]

    def mover_ruta(r, ida, cargado):
        nonlocal t
        for nom, res in r['partes']:
            m, t = mover(res, nombre_parte(nom, ida), t, cargado)
            S.extend(m)
            vert(nombre_parte(nom, ida), 'uñas' if cargado else 'nada')

    def etapas(pose, lugar, tomar):
        """Toma (tomar=True) o deja en un hueco o en la zona de carga, con el equipo ya enfrentado."""
        nonlocal t, h, ext
        d = lugar
        h_ent, h_agr = B.altura_uña(d, 'entrada'), B.altura_uña(d, 'agarre')
        car0 = not tomar
        h_ini = h_ent if tomar else h_agr                      # para dejar, se entra por arriba
        pasos = [('ELEVA', abs(h_ini - h) / (V_SUBE[0] if tomar else V_SUBE[1]), h_ini, 0.0, car0),
                 ('APROXIMA', None, h_ini, 0.0, car0),
                 ('EXTIENDE', EXT_MAX / V_EMPUJE[0 if tomar else 1], h_ini, EXT_MAX, car0)]
        if tomar:
            pasos.append(('TOMA', (h_agr - h_ent) / V_SUBE[1], h_agr, EXT_MAX, True))
        else:
            pasos.append(('DEPOSITA', (h_agr - h_ent) / V_BAJA[1], h_ent, EXT_MAX, False))
        car1 = tomar
        h_sal = h_agr if tomar else h_ent
        pasos += [('RETRAE', EXT_MAX / V_EMPUJE[1 if tomar else 0], h_sal, 0.0, car1),
                  ('RETROCEDE', None, h_sal, 0.0, car1),
                  ('BAJA', abs(h_sal - H_VIAJE) / V_BAJA[1 if tomar else 0], H_VIAJE, 0.0, car1)]
        t_cubo = None
        for etapa, dur, h1, e1, car in pasos:
            ibc = 'uñas' if car else 'nada'
            if etapa in ('APROXIMA', 'RETROCEDE'):
                dist = INSERTA if etapa == 'APROXIMA' else -INSERTA
                m, t1 = mover(recta_local(pose, dist), etapa, t, car)
                S.extend(m)
                pose = (pose[0] + dist * math.cos(pose[2]), pose[1] + dist * math.sin(pose[2]), pose[2])
                vert(etapa, ibc)
                t = max(t1, t + T_MIN)
                vert(etapa, ibc)
            else:
                if etapa == 'TOMA':
                    t_cubo = t                                  # desde acá el cubo va en las uñas
                    ibc = 'uñas'
                m, t1 = quieto(pose, etapa, t, max(dur, T_MIN), car)
                S.extend(m)
                vert(etapa, 'uñas' if etapa in ('TOMA', 'DEPOSITA') else ibc)
                t = t1
                h, ext = h1, e1
                if etapa == 'DEPOSITA':
                    t_cubo = t                                  # desde acá el cubo queda en el rack
                vert(etapa, 'uñas' if etapa == 'TOMA' else ('nada' if etapa == 'DEPOSITA' else ibc))
            if etapa == 'EXTIENDE':
                donde = mundo_de(pose, a_ibc)
        return donde, t_cubo

    for n, (tipo, desde, hueco, ida, vuelta) in enumerate(rutas):
        t_ini = t
        mover_ruta(ida, True, False)
        lugar_toma = B.leer(hueco) if tipo == 'salida' else ZONA
        donde, t_toma = etapas(ida['total']['poses'][-1], lugar_toma, True)
        cubos.append(dict(x=donde[0], y=donde[1], th=donde[2], t0=-1.0 if tipo == 'salida' else t_ini,
                          t1=t_toma, tipo='rack' if tipo == 'salida' else 'zona'))
        mover_ruta(vuelta, False, True)
        pose = vuelta['total']['poses'][-1]
        if tipo == 'salida' and DESCARGA:                     # deja en la zona de descarga, al piso
            donde, t_dep = etapas(pose, DESCARGA, False)
            cubos.append(dict(x=donde[0], y=donde[1], th=donde[2], t0=t_dep, t1=t_dep + 10.0, tipo='principio'))
            p = S[-1]
            S.append(dict(t=t, x=p['x'], y=p['y'], th=p['th'], d=0.0, sg=0, v=0.0, e='LIBRE', c=False))
        elif tipo == 'salida':                                # deja en el piso del principio (sin zona)
            m, t1 = quieto(pose, 'DEJA', t, max(H_VIAJE / V_BAJA[1], T_MIN), True)
            S.extend(m)
            vert('DEJA', 'uñas')
            t = t1
            h = 0.0
            vert('DEJA', 'nada')
            cubos.append(dict(x=pose[0] + (B.a_punta(pl.xpiv, pl.lch) - 0.6) * math.cos(pose[2]),
                              y=pose[1] + (B.a_punta(pl.xpiv, pl.lch) - 0.6) * math.sin(pose[2]), th=pose[2],
                              t0=t, t1=t + 8.0, tipo='principio'))
            h = H_VIAJE
            t += 0.4
            vert('LIBRE', 'nada')
            S.append(dict(t=t, x=pose[0], y=pose[1], th=pose[2], d=0.0, sg=0, v=0.0, e='LIBRE', c=False))
        else:
            donde, t_dep = etapas(pose, B.leer(hueco), False)
            cubos.append(dict(x=donde[0], y=donde[1], th=donde[2], t0=t_dep, t1=1e9, tipo='rack'))
            p = S[-1]
            S.append(dict(t=t, x=p['x'], y=p['y'], th=p['th'], d=0.0, sg=0, v=0.0, e='LIBRE', c=False))
        d = B.leer(hueco)
        R1, R2 = P.resumen(ida['total'], None), P.resumen(vuelta['total'], None)
        pedidos.append(dict(n=n + 1, tipo=tipo, desde=desde, hueco=hueco, t0=round(t_ini, 2), t1=round(t, 2),
                            lado=d.s, nivel=d.y, x_bahia=d.x, pos=d.p,
                            ida=dict(largo=round(R1['largo'], 2), cambios=R1['cambios']),
                            vuelta=dict(largo=round(R2['largo'], 2), cambios=R2['cambios'])))
    return S, Vt, cubos, pedidos


EN_EL_CUBO = ('APROXIMA', 'EXTIENDE', 'TOMA', 'DEPOSITA', 'RETRAE', 'RETROCEDE')   # las uñas van dentro del IBC


def holguras(pl, S):
    """Margen (m) entre la silueta y el límite más cercano (cara de poste, o cara del cubo de N1 en la
    luz de la bahía, 6 cm atrás), con holgura 0, y el punto que lo da. Fuera del rack (zona), None.
    En la toma (EN_EL_CUBO) las uñas y el cubo entran al hueco a propósito: se mide el resto."""
    out = []
    for s in S:
        eq = pl.eq[s['c']]
        X, Y = eq.huella((s['x'], s['y'], s['th']))
        if s['e'] in EN_EL_CUBO:
            X, Y = X[~eq.frente], Y[~eq.frente]
        luz = B.en_luz(X)
        en_rack = (X >= (-B.ZONA_ATRAS if B.ZONA_DESCARGA else B.X0)) & (X <= B.x_fondo())
        sup = np.where(luz, B.HALF + pl.rec[0], B.HALF)
        inf = np.where(luz, -(B.HALF + pl.rec[1]), -B.HALF)
        if B.ZONA_DESCARGA:                      # la zona de descarga, al principio (Mundo)
            zd = X <= B.X0
            if B.ZONA_DESCARGA == 'R':
                inf = np.where(zd, -(B.HALF + B.FONDO_RACK + B.REC_R), inf)
            else:
                sup = np.where(zd, B.HALF + B.FONDO_RACK + B.REC_L, sup)
            hol_pared = X + B.ZONA_ATRAS
        if B.ZONA_CARGA:                         # la zona de carga: piso hasta el fondo del rack (Mundo)
            zc = X >= B.fin_rack()
            if B.ZONA_CARGA == 'R':
                inf = np.where(zc, -(B.HALF + B.FONDO_RACK + B.REC_R), inf)
            else:
                sup = np.where(zc, B.HALF + B.FONDO_RACK + B.REC_L, sup)
        hol = np.minimum(sup - Y, Y - inf)
        hol = np.minimum(hol, B.x_fondo() - X)   # la pared del fondo
        if B.ZONA_DESCARGA:
            hol = np.minimum(hol, hol_pared)     # la pared del principio
        hol = np.where(en_rack, hol, np.inf)
        j = int(np.argmin(hol))
        out.append(None if not np.isfinite(hol[j]) else [round(float(hol[j]), 4), round(float(X[j]), 3),
                                                         round(float(Y[j]), 3)])
    return out


def vista(pl, S):
    """Qué marcas ve cada cámara del montaje A2, cada DT_VIS (interpolando la pose)."""
    # marcas sobre los postes cada 2 bahías, en los dos tramos y las dos caras (lo de V.mapa(2), pero
    # siguiendo los postes reales: con el hueco del DXF los postes no van a paso fijo)
    filas, n1 = [], B.CORTE or B.N
    xs = [x for k, x in enumerate(B.postes()) if (k <= n1 and k % 2 == 0) or (k > n1 and (k - n1 - 1) % 2 == 0)]
    for x in xs:
        xc = x + B.POSTE / 2
        filas.append((xc, +B.HALF, V.H_MARCA, -math.pi / 2, V.L_MARCA))
        filas.append((xc, -B.HALF, V.H_MARCA, +math.pi / 2, V.L_MARCA))
    M = np.c_[np.array(filas), np.arange(len(filas))]
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
    global ZONA, DESCARGA
    log = lambda s: print(s, flush=True)
    t0 = time.time()
    with B.geometria('dxf'):
        DESCARGA = repr(B.Direccion(0, '1A', B.ZONA_DESCARGA, 'c'))   # '0 1A Rc'
        ZONA = repr(B.Direccion(B.N + 1, '1A', B.ZONA_CARGA, 'c'))     # '14 1A Rc': el planificador pide texto
        pl = P.Planificador(modelo='v3')
        rutas = planificar_turno(pl, log)
        S, Vt, cubos, pedidos = armar(pl, rutas)
        log(f'{len(S)} muestras de pose, turno de {S[-1]["t"]:.0f} s; holguras y visibilidad…')
        hol = holguras(pl, S)
        vis, marcas, camaras = vista(pl, S)
        piezas = {}
        for c in (False, True):
            pol = P.poligonos(pl.xpiv, cargado=c, lch=pl.lch, r_culo=pl.r_culo)
            piezas['cargado' if c else 'vacio'] = [[[round(a, 4), round(y, 4)] for a, y in p] for p in pol]
        a_mast = pl.lch - pl.xpiv
        geo = dict(PASILLO=B.PASILLO, X0=B.X0, N=B.N, POSTE=B.POSTE, BAHIA=B.BAHIA, PASO=B.PASO_POSTE,
                   FONDO_RACK=B.FONDO_RACK, ZONA_ANCHO=B.ZONA_ANCHO, ZONA_ATRAS=B.ZONA_ATRAS, X_FONDO=B.x_fondo(),
                   FIN_RACK=B.fin_rack(), IBC=[B.IBC_CARA, B.IBC_FONDO], ALTURAS=B.ALTURAS,
                   descarga=list(B.pose_descarga(pl.xpiv, pl.lch)),
                   bahias=[[round(v, 3) for v in B.bahia_x(n)] for n in range(1, B.N + 1)],
                   postes=[round(x, 3) for x in B.postes()],
                   zona_carga=dict(lado=B.ZONA_CARGA, x0=round(B.fin_rack(), 3), x1=round(B.x_fondo(), 3)),
                   zona_descarga=dict(lado=B.ZONA_DESCARGA, x0=-B.ZONA_ATRAS, x1=round(B.X0, 3)),
                   hueco=[round(B.bahia_x(B.CORTE)[1] + B.POSTE, 3), round(B.bahia_x(B.CORTE + 1)[0] - B.POSTE, 3)],
                   fuente='datos/sectorA.json (pasillo B: verde | azul) + zona de carga de maje')
        datos = dict(
            generado=time.strftime('%Y-%m-%d %H:%M'),
            supuestos=dict(modelo='v3b (planificador_rutas.py, modelo=v3, culo de la ficha), geometría del DXF',
                           XPIV=round(pl.xpiv, 3), WB=P.WB, DMAX=90, REC=list(pl.rec), VMAX=P.VMAX, VMAN=P.VMAN,
                           ACC=P.ACC, V_SUBE=V_SUBE, V_BAJA=V_BAJA, V_EMPUJE=V_EMPUJE, EXT_MAX=EXT_MAX,
                           H_VIAJE=H_VIAJE, T_MIN=T_MIN, INSERTA=round(INSERTA, 3), montaje='A2', marcas_cada=2,
                           PX_MIN=V.PX_MIN, ANG_MAX=round(math.degrees(V.ANG_MAX)),
                           nota='VMAX 1.5 m/s = sobre del kit, dentro de los 5–8 km/h que dicen los operadores. '
                                'SUPUESTOS: VMAN, ACC, H_VIAJE, T_MIN, PX_MIN, ANG_MAX, y el hueco entre tramos tratado '
                                'como cara de rack'),
            geo=geo,
            equipo=dict(piezas=piezas, xpiv=pl.xpiv, a_mast=a_mast, a_pata=a_mast + P.L_ANCHO,
                        a_punta=B.a_punta(pl.xpiv, pl.lch), wb=P.WB, rueda=[0.343, 0.140], w_capo=P.W_CAPO,
                        w_max=P.W_MAX),
            pedidos=pedidos,
            cubos=[dict(x=round(c['x'], 3), y=round(c['y'], 3), th=round(c['th'], 4), t0=round(c['t0'], 2),
                        t1=round(c['t1'], 2), tipo=c['tipo']) for c in cubos],
            S=[[round(s['t'], 3), round(s['x'], 4), round(s['y'], 4), round(s['th'], 4), round(s['d'], 3),
                s['sg'], round(s['v'], 3), s['e'], int(s['c'])] for s in S],
            H=hol,
            V=[[round(v['t'], 3), round(v['h'], 3), round(v['ext'], 3), v['ibc'], v['e']] for v in Vt],
            vis=vis, marcas=marcas, camaras=camaras)
    with open(os.path.join(RAIZ, 'sim', 'sim_datos.json'), 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
    log(f'listo en {time.time() - t0:.0f} s → sim/sim_datos.json')


def solo_holguras():
    """Recalcula H sobre el sim_datos.json ya hecho, sin volver a planificar (10 min)."""
    ruta = os.path.join(RAIZ, 'sim', 'sim_datos.json')
    with open(ruta, encoding='utf-8') as f:
        d = json.load(f)
    with B.geometria('dxf'):
        pl = P.Planificador(modelo='v3')
        S = [dict(t=r[0], x=r[1], y=r[2], th=r[3], e=r[7], c=bool(r[8])) for r in d['S']]
        d['H'] = holguras(pl, S)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
    print('H recalculado')


if __name__ == '__main__':
    solo_holguras() if '--solo-holguras' in sys.argv else main()
