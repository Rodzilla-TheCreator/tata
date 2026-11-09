"""Visibilidad de ArUco por montaje de cámaras, con el modelo v3b y el pasillo B del DXF (09-nov).

Usa el turno de sim/sim_datos.json (rutas del planificador v3b: 2.91 m, culo de la ficha, timón a 90°,
pasillo B con 13 bahías por lado, zonas de descarga y carga en las puntas, lado R) y el mismo modelo de
cámara de visibilidad.py (C920, FOV 54.3°, PX_MIN, ANG_MAX). Compara montajes, incluidos los pares a 90°
que no se habían probado, y marcas sobre los postes cada 1 o 2 bahías.

    python percepcion/visibilidad_v3.py          # escribe percepcion/visibilidad_v3.json

NO corre el EKF: odometria.py y ekf.py integran con tan(δ) y la velocidad del eje de carga, que con el
timón a 90° (rotación sobre el eje de carga) es infinita. Hay que pasarlos a la velocidad de la rueda
motriz antes. Mientras tanto, lo que se compara es cobertura: cuánto tiempo y cuántos metros en
movimiento no ve marcas ninguna cámara, por fase.
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
    main()
