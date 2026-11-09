"""Visibilidad de ArUco por montaje de cámaras, con el modelo v3b y el pasillo B del DXF (09-nov).

Usa el turno de sim/sim_datos.json (rutas del planificador v3b: 2.91 m, culo de la ficha, timón a 90°,
pasillo B con 13 bahías por lado, zonas de descarga y carga en las puntas, lado R) y el mismo modelo de
cámara de visibilidad.py (C920, FOV 54.3°, PX_MIN, ANG_MAX). Compara montajes, incluidos los pares a 90°
que no se habían probado, y marcas sobre los postes cada 1 o 2 bahías.

    python percepcion/visibilidad_v3.py          # escribe percepcion/visibilidad_v3.json

    python percepcion/visibilidad_v3.py --ekf    # + el error al llegar con el EKF (rueda motriz), ~10 min

El EKF corre con la odometría de la RUEDA MOTRIZ (ekf.py rueda=True, validado en prueba_ekf_rueda.py):
la vieja integraba con tan(δ) y la velocidad del eje de carga, que con el timón a 90° no sirve.
"""
import json
import math
import os
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'analisis'))
sys.path.insert(0, os.path.join(RAIZ, 'percepcion'))
import bahias as B                    # noqa: E402
import visibilidad as V               # noqa: E402

DT = 0.10                              # 10 Hz, como visibilidad.py
FASES = {'RECTA': 'tránsito', 'TRANSITO': 'tránsito', 'VUELTA': 'tránsito', 'GIRO': 'giro', 'DESGIRA': 'giro',
         'APROXIMA': 'alineación', 'RETROCEDE': 'alineación'}
QUIETAS = ('ELEVA', 'EXTIENDE', 'TOMA', 'DEPOSITA', 'RETRAE', 'BAJA', 'DEJA', 'LIBRE')


def montajes(xpiv):
    """Posición respecto del eje de carga (cx adelante, cy a la izquierda), altura, yaw (0 = hacia las
    uñas, +90 = izquierda). Los que ya estaban (A, A2, B, D) y los pares a 90° que faltaban."""
    C, Xc, Yc = V.Camara, V.X_CAPO, V.Y_CAPO
    a_torre = 1.71 - xpiv + 0.30                    # la cara de la torre (LCH_V3 − XPIV) y un poco adelante
    lat_i = C('lateral izq.', Xc, Yc, 1.0, 90)
    lat_d = C('lateral der.', Xc, -Yc, 1.0, -90)
    return {
        'A2': ('lateral izq. + trasera diagonal a la derecha (−135°): el de la simulación',
               [lat_i, C('trasera diag. der.', -xpiv, 0.0, 1.0, -135)]),
        'A2-esp': ('lateral izq. + trasera diagonal a la izquierda (+135°)',
                   [lat_i, C('trasera diag. izq.', -xpiv, 0.0, 1.0, 135)]),
        'A': ('lateral izq. + trasera recta (180°): 90° entre sí, la idea original de maje',
              [lat_i, C('trasera', -xpiv, 0.0, 1.0, 180)]),
        'A-der': ('lateral DER. + trasera recta (180°): 90° entre sí, la lateral del lado de las zonas',
                  [lat_d, C('trasera', -xpiv, 0.0, 1.0, 180)]),
        'B': ('dos laterales (±90°): 180° entre sí', [lat_i, lat_d]),
        'V90': ('dos traseras en V, ±135° desde el culo: 90° entre sí',
                [C('trasera diag. izq.', -xpiv, 0.0, 1.0, 135), C('trasera diag. der.', -xpiv, 0.0, 1.0, -135)]),
        'A2-der': ('lateral DER. + trasera diagonal a la izquierda (+135°): A2 en espejo',
                   [lat_d, C('trasera diag. izq.', -xpiv, 0.0, 1.0, 135)]),
        'D': ('frontal (2.2 m, −10°) + lateral izq.: 90° entre sí (docs/03)',
              [C('frontal', B.LCH - xpiv, 0.0, 2.2, 0, -10), lat_i]),
        # una tercera cámara para la alineación: en la torre, a 1.0 m, mirando a las uñas (la ficha
        # ofrece cámara en las horquillas). Con la óptica de la C920 y con un gran angular de 90°
        'A2+F': ('A2 + frontal en la torre (1.0 m, 0°, 54°)',
                 [lat_i, C('trasera diag. der.', -xpiv, 0.0, 1.0, -135), C('frontal torre', a_torre, 0.0, 1.0, 0)]),
        'A2+F90': ('A2 + frontal en la torre gran angular (1.0 m, 0°, 90°)',
                   [lat_i, C('trasera diag. der.', -xpiv, 0.0, 1.0, -135),
                    C('frontal torre 90°', a_torre, 0.0, 1.0, 0, 0.0, 90.0)]),
    }


def mapa_postes(paso):
    """Marcas sobre los postes reales (los dos tramos del DXF), cada `paso` bahías, en las dos caras."""
    filas, n1 = [], B.CORTE or B.N
    for k, x in enumerate(B.postes()):
        kk = k if k <= n1 else k - n1 - 1
        if kk % paso:
            continue
        xc = x + B.POSTE / 2
        filas.append((xc, +B.HALF, V.H_MARCA, -math.pi / 2, V.L_MARCA))
        filas.append((xc, -B.HALF, V.H_MARCA, +math.pi / 2, V.L_MARCA))
    return np.c_[np.array(filas), np.arange(len(filas))]


def muestras(d):
    """Pose a 10 Hz interpolando el turno, con su fase y si se mueve."""
    S = d['S']
    t = np.array([s[0] for s in S])
    out = []
    tt = 0.0
    while tt <= t[-1]:
        i = max(0, int(np.searchsorted(t, tt, 'right')) - 1)
        a, b = S[i], S[min(i + 1, len(S) - 1)]
        f = 0.0 if b[0] <= a[0] else min(1.0, (tt - a[0]) / (b[0] - a[0]))
        dth = (b[3] - a[3] + math.pi) % (2 * math.pi) - math.pi
        pose = (a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + dth * f)
        mueve = abs(a[6]) > 1e-3 or abs(b[6]) > 1e-3
        v_rueda = abs(a[6] + (b[6] - a[6]) * f)                        # v3: los ds son de la rueda motriz
        out.append((tt, pose, FASES.get(a[7], 'quieto') if mueve else 'quieto', a[7], v_rueda))
        tt += DT
    return out


def evaluar(M, cams, ms):
    E = V._esquinas(M)
    filas = []
    for tt, pose, fase, etapa, vr in ms:
        ve = [len(V.visibles(pose, c, M, E)[0]) > 0 for c in cams]
        filas.append((tt, pose, fase, etapa, ve, vr))
    res = {}
    for fase in ('tránsito', 'giro', 'alineación'):
        sel = [f for f in filas if f[2] == fase]
        n = np.array([sum(f[4]) for f in sel])
        res[fase] = [round(100 * float(np.mean(n == k)), 1) for k in (0, 1, 2)] if len(n) else None
    # en la toma, quieto frente al hueco: ¿alguna cámara ve una marca?
    sel = [f for f in filas if f[3] in ('EXTIENDE', 'TOMA', 'DEPOSITA')]
    res['toma_ve'] = round(100 * float(np.mean([any(f[4]) for f in sel])), 1) if sel else None
    # tramo ciego más largo en movimiento: metros de RUEDA MOTRIZ (lo que integra la odometría), grados
    # girados y segundos. Quieto no suma ni corta
    peor = dict(rueda_m=0.0, grados=0.0, s=0.0)
    act = dict(rueda_m=0.0, grados=0.0, s=0.0)
    prev = None
    for tt, pose, fase, etapa, ve, vr in filas:
        if fase == 'quieto':
            prev = pose
            continue
        dth = 0.0 if prev is None else abs((pose[2] - prev[2] + math.pi) % (2 * math.pi) - math.pi)
        prev = pose
        if not any(ve):
            act['rueda_m'] += vr * DT; act['grados'] += math.degrees(dth); act['s'] += DT
            for k in peor:
                peor[k] = max(peor[k], act[k])
        else:
            act = dict(rueda_m=0.0, grados=0.0, s=0.0)
    res['ciego_rueda_m'], res['ciego_grados'], res['ciego_s'] = (round(peor['rueda_m'], 2), round(peor['grados']),
                                                                  round(peor['s'], 1))
    res['por_camara'] = [round(100 * float(np.mean([f[4][k] for f in filas if f[2] != 'quieto'])), 1)
                         for k in range(len(cams))]
    return res


# ── el EKF con la rueda motriz (ekf.py, rueda=True; validado en prueba_ekf_rueda.py) ─────────────────
LLEGADAS = ('EXTIENDE',)              # se mide el error al empezar a extender: el equipo ya no se mueve
SEMILLAS = 6


def verdad(d):
    """Trayectoria verdadera en pasos de ≤ 2 cm de rueda, reproduciendo las muestras del turno con
    avanzar_rueda (la cinemática v3). Devuelve arreglos t, dt, pose, v (rueda), δ, fase, y las llegadas."""
    from odometria import avanzar_rueda
    S = d['S']
    T, DTS, POS, VV, DD, FASE, LLEG = [], [], [], [], [], [], []
    pose = tuple(S[0][1:4])
    t = S[0][0]
    salto = 0.0
    for a, b in zip(S, S[1:]):
        dt_tot = b[0] - a[0]
        if dt_tot <= 0:
            continue
        dsw = 0.5 * (a[6] + b[6]) * dt_tot if a[5] != 0 else 0.0
        n = max(1, int(math.ceil(abs(dsw) / 0.02)), int(math.ceil(dt_tot / 0.1)))
        vw, dd, dt = dsw / dt_tot, a[4], dt_tot / n
        if a[7] in LLEGADAS and (not FASE or FASE[-1] != a[7]):
            LLEG.append(len(T) - 1)
        for _ in range(n):
            pose = avanzar_rueda(pose, vw, dd, dt)
            t += dt
            T.append(t); DTS.append(dt); POS.append(pose); VV.append(vw); DD.append(dd)
            FASE.append(a[7])
        e = math.hypot(pose[0] - b[1], pose[1] - b[2])
        salto = max(salto, e)
        pose = (b[1], b[2], b[3])                     # se re-ancla a la muestra (el salto se informa)
        POS[-1] = pose
    T = np.array(T)
    cuadros = set(np.searchsorted(T, np.arange(0.1, T[-1], 0.1)).tolist())
    return dict(t=T, dt=np.array(DTS), pose=np.array(POS), v=np.array(VV), d=np.array(DD), fase=FASE,
                llegadas=LLEG, cuadros=cuadros, salto=salto)


def correr_ekf(tr, camaras, M, semilla):
    """Como visibilidad.correr_ekf, con el EKF de la rueda motriz. Devuelve el error lateral (a lo
    largo del pasillo, que es lo que alinea las uñas con los huecos del IBC) en cada llegada."""
    from ekf import EKF, ColocacionMarcas, R_pose, marca_vista_desde, pose_desde_marca
    r = np.random.default_rng(semilla)
    rmed = np.random.default_rng(semilla + 10_000)
    E = V._esquinas(M)
    creido = {int(m[5]): (m[0] + r.normal(0, V.SIG_COLOCACION), m[1] + r.normal(0, V.SIG_COLOCACION), m[3]) for m in M}
    p0 = tr['pose'][0]
    f = EKF(p0 + r.normal(0, [0.05, 0.05, math.radians(1.0)]),
            np.diag([0.10 ** 2, 0.10 ** 2, math.radians(3) ** 2]), rueda=True)
    coloc = ColocacionMarcas(V.SIG_COLOCACION)
    errores, lleg = [], set(tr['llegadas'])
    for i in range(1, len(tr['t'])):
        v, dd, dt = tr['v'][i], tr['d'][i], tr['dt'][i]
        moviendo = abs(v) > 1e-6
        k = math.sqrt(V.DT / dt)
        f.predict(v * V.SESGO_V + (r.normal(0, V.RUIDO_V * k) if moviendo else 0.0),
                  dd + V.SESGO_D + (r.normal(0, V.RUIDO_D * k) if moviendo else 0.0), dt)
        ver = tr['pose'][i]
        if i in tr['cuadros']:
            for cam in camaras:
                vis, px, dist = V.visibles(ver, cam, M, E)
                for j in vis:
                    mk = M[j]
                    dz = marca_vista_desde(ver, (mk[0], mk[1], mk[3]), cam.montaje2d)
                    sg = V.sigmas(dist[j], px[j])
                    z = np.array(dz) + rmed.normal(0, sg)
                    cid = int(mk[5])
                    f.update_aruco(pose_desde_marca(creido[cid], *z, cam.montaje2d),
                                   R_pose(creido[cid], *z, cam.montaje2d, np.diag(sg ** 2)) + coloc.R(cid, tr['t'][i]))
        if i in lleg:
            e = f.pose - ver
            th = ver[2]
            errores.append(-math.sin(th) * e[0] + math.cos(th) * e[1])
    return errores


def main_ekf(nombres=('A2', 'A2-der', 'A2-esp', 'B', 'V90', 'A', 'D', 'A2+F90'), pasos=(1, 2)):
    with open(os.path.join(RAIZ, 'sim', 'sim_datos.json'), encoding='utf-8') as f:
        d = json.load(f)
    ruta = os.path.join(RAIZ, 'percepcion', 'visibilidad_v3.json')
    with open(ruta, encoding='utf-8') as f:
        out = json.load(f)
    with B.geometria('dxf'):
        tr = verdad(d)
        print(f"verdad: {len(tr['t'])} pasos, {len(tr['llegadas'])} llegadas, salto máx contra las muestras "
              f"{1000 * tr['salto']:.2f} mm", flush=True)
        mons = montajes(d['supuestos']['XPIV'])
        for paso in pasos:
            M = mapa_postes(paso)
            for nombre in nombres:
                errs = []
                for s in range(SEMILLAS):
                    errs += correr_ekf(tr, mons[nombre][1], M, s)
                e = np.abs(np.array(errs))
                r = dict(max_cm=round(100 * e.max(), 2), p95_cm=round(100 * np.percentile(e, 95), 2),
                         fuera=int((e >= V.REQ_LAT).sum()), n=len(e))
                out['montajes'][nombre].setdefault(f'cada_{paso}', {})['ekf'] = r
                print(f"EKF {nombre:7s} cada {paso}: error al llegar máx {r['max_cm']:5.2f} cm · p95 {r['p95_cm']:5.2f} · "
                      f"fuera de ±4.5 cm: {r['fuera']}/{r['n']}", flush=True)
        # control de falsación: con una sola marca por cara (a mitad del pasillo) tiene que salirse de ±4.5 cm
        M1 = mapa_postes(1)
        xs = sorted(set(M1[:, 0]))
        Mc = M1[np.isclose(M1[:, 0], xs[len(xs) // 2])]
        Mc = np.c_[Mc[:, :5], np.arange(len(Mc))]
        errs = []
        for s in range(SEMILLAS):
            errs += correr_ekf(tr, mons['A2'][1], Mc, s)
        e = np.abs(np.array(errs))
        ctl = dict(max_cm=round(100 * e.max(), 2), fuera=int((e >= V.REQ_LAT).sum()), n=len(e),
                   falla_como_debe=bool((e >= V.REQ_LAT).any()))
        out['control_una_por_cara_A2'] = ctl
        print(f"CONTROL A2 con una marca por cara: máx {ctl['max_cm']} cm, fuera {ctl['fuera']}/{ctl['n']} → "
              f"{'falla como debe' if ctl['falla_como_debe'] else 'NO FALLA: la prueba no mide nada'}", flush=True)
    out['supuestos']['ekf'] = dict(semillas=SEMILLAS, odometria='rueda motriz (ekf.py rueda=True)',
                                   SESGO_V=V.SESGO_V, SESGO_D_grados=round(math.degrees(V.SESGO_D), 2),
                                   salto_verdad_mm=round(1000 * tr['salto'], 3))
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def main():
    with open(os.path.join(RAIZ, 'sim', 'sim_datos.json'), encoding='utf-8') as f:
        d = json.load(f)
    xpiv = d['supuestos']['XPIV']
    out = dict(supuestos=dict(XPIV=xpiv, PX_MIN=V.PX_MIN, ANG_MAX=round(math.degrees(V.ANG_MAX)), H_MARCA=V.H_MARCA,
                              L_MARCA=V.L_MARCA, X_CAPO=V.X_CAPO, turno_s=d['S'][-1][0], geometria='dxf'),
               montajes={})
    with B.geometria('dxf'):
        ms = muestras(d)
        mons = montajes(xpiv)
        for paso in (1, 2):
            M = mapa_postes(paso)
            for nombre, (desc, cams) in mons.items():
                r = evaluar(M, cams, ms)
                out['montajes'].setdefault(nombre, dict(desc=desc, camaras=[c.nombre for c in cams]))[f'cada_{paso}'] = r
                print(f"{nombre:7s} cada {paso}: ciego {r['ciego_rueda_m']:5.1f} m de rueda / {r['ciego_grados']:3d}° / {r['ciego_s']:4.1f} s · "
                      f"0 cám. tránsito {r['tránsito'][0]:5.1f} % · giro {r['giro'][0]:5.1f} % · "
                      f"alineación {r['alineación'][0]:5.1f} % · toma ve {r['toma_ve']:5.1f} % · por cámara {r['por_camara']}",
                      flush=True)
    with open(os.path.join(RAIZ, 'percepcion', 'visibilidad_v3.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main_ekf() if '--ekf' in sys.argv else main()
