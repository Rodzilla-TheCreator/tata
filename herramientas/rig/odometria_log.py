#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · odometria_log.py — los giros de la prueba de piso, desde el log del teleop, y lo que dice la tiza (24-nov-2026).

    py odometria_log.py logs\teleop_wasd_20261125-101500.log            # un renglón por tramo entre MARCAs
    py odometria_log.py --tiza 120.0 120.2 31.5 30.8 150.1 140.3         # las 6 medidas de flexómetro, en cm
    py odometria_log.py LOG --marca 3 --tiza 120.0 120.2 31.5 30.8 150.1 140.3       # el tramo 3 contra la tiza
    py odometria_log.py LOG --marca 3 --tiza ... --centro 0.4 --adelante 5           # con el centro ya ajustado (T1)
    py odometria_log.py --objetivo -95.4 90 --ancho 131.5 --retro 7      # dónde deberían caer I2 y D2 (para pintarlos)
    py odometria_log.py --prueba                                         # se prueba a sí mismo, con control

LOG. Lee las líneas «T ... ang=... dist=...» que manda teleop_wasd.ino (~10 por segundo) y las «>>> ... MARCA n» que
deja la tecla M. Integra con percepcion/odometria.py (entre ejes 1.688, motriz corrida 0.325 del lado del timón,
LADO_MOTRIZ +1): por tramo, cuánto giró el equipo y cuánto se movió el MEDIO DEL EJE DE CARGA, en el marco del equipo
al empezar el tramo (x hacia las uñas, y a la izquierda mirando hacia las uñas).

TIZA. Antes y después de cada maniobra se marca en el piso, con escuadra, dónde cae la línea del eje de carga junto a
cada pata: I (izquierda, mirando hacia las uñas) y D (derecha). Se miden seis distancias con el flexómetro:
    I1-D1  I2-D2  I1-I2  D1-D2  I1-D2  D1-I2
y esto da el giro y el desplazamiento del medio del eje con la misma convención que el log. Si las marcas no caen
justo sobre el eje de carga, --adelante dice cuántos cm hacia las uñas quedaron (negativo: hacia el culo). Seis distancias para
cuatro puntos dejan UNA de sobra: el «cierre» compara I2-D2 medido con el que sale de las otras cinco. Delata un error
en esa, pero uno en otra medida puede quedar absorbido: medir cada una dos veces. Una ambigüedad no se
puede quitar con distancias (el espejo hacia adelante / hacia atrás): se elige la que se parece al log (--log) o se
imprimen las dos.

COMPARAR (LOG --marca n --tiza ...). El tramo n del log contra la tiza, y lo que eso dice del modelo:
    recta (giro < 10°):   el CENTRO del 0x184 que hace que el log dé el giro de la tiza, y la escala de la marcha
    giro (giro > 45°):    la escala del giro (tiza / log: junta la de la marcha y el entre ejes) y el corrimiento `e`
                          de la motriz que hace que el medio del eje se mueva lo que dice la tiza
El `e` depende del centro (3 cm de centro de giro por grado de rueda cerca del tope): ajustar el centro primero con
la recta (T1) y pasarlo con --centro a las demás.
"""
import math
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "percepcion"))
from odometria import CENTRO_184, GRADOS_184, LADO_MOTRIZ, M_S_188, WB, avanzar_rueda   # noqa: E402

T = re.compile(r"^(\d\d:\d\d:\d\d\.\d+) T .*?\bang=(-?[\d.]+).*?\bdist=(-?[\d.]+).*?\bhz184=(\d+)")
MARCA = re.compile(r"^>>> (\d\d:\d\d:\d\d\.\d+) MARCA (\d+)")


def leer(ruta):
    """[(hora, ang, dist)] y {n: índice en esa lista donde se marcó}."""
    filas, marcas = [], {}
    with open(ruta, encoding="utf-8", errors="replace") as f:
        for l in f:
            m = T.match(l)
            if m and m.group(4) != "0":
                filas.append((m.group(1), float(m.group(2)), float(m.group(3))))
                continue
            m = MARCA.match(l)
            if m:
                marcas[int(m.group(2))] = len(filas)
    return filas, marcas


def integrar(filas, centro=None, e=None, k=1.0):
    """La pose del medio del eje de carga al final, desde (0, 0, 0), y el camino de la rueda. `centro` es la recta
    del 0x184 en grados (por defecto CENTRO_184 · GRADOS_184 = +1.20), `e` el corrimiento de la motriz con su signo
    (por defecto el de odometria.py) y `k` la escala de la marcha."""
    c = CENTRO_184 * GRADOS_184 if centro is None else centro
    p, camino = (0.0, 0.0, 0.0), 0.0
    for (h0, a0, d0), (h1, a1, d1) in zip(filas, filas[1:]):
        ds = d1 - d0
        if abs(ds) > 0.5:                                    # «odometría a 0» en el ESP
            continue
        d = LADO_MOTRIZ * math.radians(0.5 * (a0 + a1) - c)
        p = avanzar_rueda(p, k * ds, d, 1.0, e=e)
        camino += abs(k * ds)
    return p, camino


def tramos(ruta):
    filas, marcas = leer(ruta)
    cortes = sorted(marcas.items(), key=lambda kv: kv[1])
    if not cortes:
        cortes = [(0, 0)]
    out = []
    for k, (n, i) in enumerate(cortes):
        j = cortes[k + 1][1] if k + 1 < len(cortes) else len(filas)
        seg = filas[i:j]
        if len(seg) < 2:
            continue
        (x, y, th), camino = integrar(seg)
        pesos = [abs(b[2] - a[2]) for a, b in zip(seg, seg[1:]) if abs(b[2] - a[2]) <= 0.5]
        angs = [0.5 * (a[1] + b[1]) for a, b in zip(seg, seg[1:]) if abs(b[2] - a[2]) <= 0.5]
        medio = sum(p * a for p, a in zip(pesos, angs)) / sum(pesos) if sum(pesos) > 0 else seg[0][1]
        out.append(dict(marca=n, desde=seg[0][0], hasta=seg[-1][0], giro=math.degrees(th), x=x, y=y,
                        eje=math.hypot(x, y), camino=camino, rueda=(min(a for _, a, _ in seg), max(a for _, a, _ in seg)),
                        ang_medio=medio, filas=seg))
    return out


def _punto(pA, pB, dA, dB, lado):
    """Punto a distancia dA de pA y dB de pB; `lado` elige cuál de las dos soluciones (+1 / −1 respecto de A→B)."""
    pA, pB = np.asarray(pA, float), np.asarray(pB, float)
    d = np.linalg.norm(pB - pA)
    a = (dA ** 2 - dB ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(0.0, dA ** 2 - a ** 2))
    u = (pB - pA) / d
    n = np.array([-u[1], u[0]])
    return pA + a * u + lado * h * n


def tiza(i1d1, i2d2, i1i2, d1d2, i1d2, d1i2, adelante=0.0):
    """Las dos lecturas posibles (espejo adelante/atrás) de giro (°) y desplazamiento del medio del eje (x, y) en el
    marco del equipo al empezar: I1 = (0, +a/2), D1 = (0, −a/2). `adelante` (m): cuánto quedaron las marcas por
    delante del eje de carga, hacia las uñas; se descuenta para dar el movimiento del medio del eje."""
    a = i1d1
    I1, D1 = np.array([0.0, a / 2]), np.array([0.0, -a / 2])
    sols = []
    for li in (1, -1):
        for ld in (1, -1):
            I2 = _punto(I1, D1, i1i2, d1i2, li)
            D2 = _punto(I1, D1, i1d2, d1d2, ld)
            err = abs(np.linalg.norm(I2 - D2) - i2d2)
            sols.append((err, I2, D2))
    sols.sort(key=lambda s: s[0])
    out = []
    for err, I2, D2 in sols:
        v1, v2 = I1 - D1, I2 - D2
        giro = math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))
        g = math.radians(giro)
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        m = (I2 + D2) / 2 - (R - np.eye(2)) @ np.array([adelante, 0.0])
        lectura = dict(giro=giro, x=float(m[0]), y=float(m[1]), eje=float(np.linalg.norm(m)), cierre=float(err))
        if not any(abs(o['giro'] - giro) < 1e-6 and abs(o['x'] - m[0]) < 1e-6 for o in out):
            out.append(lectura)
    # se quedan las dos mejores que sean espejo una de otra (mismo cierre)
    return out[:2]


def elegir(lecturas, t):
    """De las dos lecturas espejo de la tiza, la que se parece al log; el giro de la tiza, desenrollado para que
    quede a menos de 180° del log (una vuelta entera da ~0 en la tiza y 360 en el log)."""
    out = []
    for l in lecturas:
        l = dict(l)
        l['giro'] += 360.0 * round((t['giro'] - l['giro']) / 360.0)
        out.append(l)
    return min(out, key=lambda l: abs(l['giro'] - t['giro']) + 100 * math.hypot(l['x'] - t['x'], l['y'] - t['y']))


def _biseccion(f, a, b, n=60):
    fa = f(a)
    if fa * f(b) > 0:
        return None
    for _ in range(n):
        m = 0.5 * (a + b)
        fm = f(m)
        if fa * fm <= 0:
            b = m
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


def comparar(t, l, centro=None):
    """El tramo `t` del log contra la lectura `l` de la tiza. Devuelve lo que se ajustó (dict)."""
    from odometria import E
    filas = t['filas']
    c0 = CENTRO_184 * GRADOS_184 if centro is None else centro
    (x, y, th), camino = integrar(filas, centro=c0)
    r = dict(giro_log=math.degrees(th), giro_tiza=l['giro'], eje_log=(x, y), eje_tiza=(l['x'], l['y']), camino=camino,
             centro_usado=c0)
    if abs(l['giro']) < 10 and camino > 2.0:                      # recta: el centro y la escala de la marcha
        g = math.radians(l['giro'])
        f = lambda c: integrar(filas, centro=c)[0][2] - g
        r['centro'] = _biseccion(f, t['ang_medio'] - 8.0, t['ang_medio'] + 8.0)
        (xc, yc, _), _ = integrar(filas, centro=c0 if r['centro'] is None else r['centro'])
        r['k_marcha'] = math.hypot(l['x'], l['y']) / max(1e-9, math.hypot(xc, yc))   # con el centro ajustado
        r['tipo'] = 'recta'
    elif abs(l['giro']) > 45:                                     # giro: la escala del giro y el corrimiento e
        k = l['giro'] / math.degrees(th) if abs(th) > 1e-6 else float('nan')
        r['k_giro'] = k
        objetivo = np.array([l['x'], l['y']])
        mejor = None
        for mm in range(-600, 601):
            e = LADO_MOTRIZ * mm / 1000.0
            (xe, ye, _), _ = integrar(filas, centro=c0, e=e, k=k)
            d = float(np.linalg.norm(np.array([xe, ye]) - objetivo))
            if mejor is None or d < mejor[1]:
                mejor = (abs(e), d)
        r['e'], r['resto_e'] = mejor
        r['e_modelo'] = abs(E)
        r['tipo'] = 'giro'
    else:
        r['tipo'] = 'arco'
        r['k_giro'] = l['giro'] / math.degrees(th) if abs(th) > 1e-6 else float('nan')
    return r


def imprimir_comparacion(t, l, r):
    print(f"MARCA {t['marca']} · {r['tipo']} · rueda {t['ang_medio']:+.2f}° de media (0x184/100), {r['camino']:.3f} m de rueda")
    print(f"  giro:            log {r['giro_log']:+8.2f}°   tiza {r['giro_tiza']:+8.2f}°   diferencia {r['giro_tiza'] - r['giro_log']:+.2f}°")
    print(f"  medio del eje:   log ({100 * r['eje_log'][0]:+6.1f}, {100 * r['eje_log'][1]:+6.1f}) cm   tiza ({100 * r['eje_tiza'][0]:+6.1f}, "
          f"{100 * r['eje_tiza'][1]:+6.1f}) cm   (adelante, izquierda)   separados "
          f"{100 * math.hypot(r['eje_tiza'][0] - r['eje_log'][0], r['eje_tiza'][1] - r['eje_log'][1]):.1f} cm")
    print(f"  cierre de la tiza {100 * l['cierre']:.1f} cm" + ("   ← más de 1 cm: volver a medir" if l['cierre'] > 0.01 else ""))
    sep = math.hypot(r['eje_tiza'][0] - r['eje_log'][0], r['eje_tiza'][1] - r['eje_log'][1])
    if abs(r['giro_tiza'] - r['giro_log']) > 20 or sep > 0.5:
        print("  ⚠ el log y la tiza no se parecen (más de 20° o 50 cm): ¿es la MARCA correcta? ¿las 6 medidas en orden?"
              " Lo de abajo no vale hasta aclararlo.")
    if r['tipo'] == 'recta':
        c = r['centro']
        print(f"  → la recta del 0x184 está en {c:+.2f}° (odometria.py usa {CENTRO_184 * GRADOS_184:+.2f})" if c is not None
              else "  → no se encontró un centro que dé ese giro: ¿la tiza está bien?")
        print(f"  → escala de la marcha: tiza / log = {r['k_marcha']:.4f} (odometria.py: {M_S_188:.3e} m/s por unidad)")
    elif r['tipo'] == 'giro':
        print(f"  → escala del giro: tiza / log = {r['k_giro']:.4f}  (si la escala de la marcha está bien, el entre ejes "
              f"real sería {WB / r['k_giro']:.3f} m; odometria.py usa {WB})")
        print(f"  → corrimiento de la motriz que explica la tiza: e = {r['e']:.3f} m (odometria.py {r['e_modelo']:.3f}), "
              f"queda {100 * r['resto_e']:.1f} cm sin explicar · con el centro {r['centro_usado']:+.2f}°")
    else:
        print(f"  → escala del giro en el arco: tiza / log = {r['k_giro']:.4f} (con el centro y el entre ejes bien, "
              f"lo que sobra es la escala del ángulo: 0.01 °/unidad)")


def objetivo(ang, grados, ancho, retro=0.0, adelante=0.0):
    """Dónde deberían caer I2 y D2 (marco de I1/D1: x hacia las uñas, y a la izquierda) si el equipo retrocede
    `retro` m recto y después gira `grados` con la rueda a `ang` (0x184/100), según odometria.py. Y las seis
    distancias que se esperan."""
    from odometria import WB as wb
    d = LADO_MOTRIZ * math.radians(ang - CENTRO_184 * GRADOS_184)
    p = avanzar_rueda((0.0, 0.0, 0.0), -retro, 0.0, 1.0)
    paso = 0.001 * (1 if (grados > 0) == (math.sin(d) < 0) else -1)
    for _ in range(200000):
        if abs(math.degrees(p[2])) >= abs(grados):
            break
        p = avanzar_rueda(p, paso, d, 1.0)
    x, y, th = p
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    A = np.array([adelante, ancho / 2]); B = np.array([adelante, -ancho / 2])
    I1, D1 = A - [adelante, 0], B - [adelante, 0]
    I2 = np.array([x, y]) + R @ A - [adelante, 0]
    D2 = np.array([x, y]) + R @ B - [adelante, 0]
    dd = dict(zip(("I1-D1", "I2-D2", "I1-I2", "D1-D2", "I1-D2", "D1-I2"),
                  (np.linalg.norm(I1 - D1), np.linalg.norm(I2 - D2), np.linalg.norm(I1 - I2), np.linalg.norm(D1 - D2),
                   np.linalg.norm(I1 - D2), np.linalg.norm(D1 - I2))))
    marcha = "W (hacia las uñas)" if paso > 0 else "S (hacia el culo)"
    return dict(I2=I2, D2=D2, eje=(x, y), giro=math.degrees(th), marcha=marcha, dist=dd, rueda_m=abs(paso) * _ + retro)


def prueba():
    """1) tiza: con un movimiento conocido se arman las 6 distancias y se recupera el giro y el desplazamiento.
    Control: con una distancia corrida 5 cm el cierre tiene que delatarlo. 2) log: un log sintético de un giro de
    90° en el lugar (rueda a la línea de rotar sobre el medio del eje) tiene que dar 90° y el eje quieto."""
    ok = True
    a = 1.20
    for giro, mx, my in ((90.0, 0.03, -0.02), (-37.0, 0.5, 0.2), (180.0, 0.0, 0.0)):
        g = math.radians(giro)
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        I1, D1 = np.array([0, a / 2]), np.array([0, -a / 2])
        I2, D2 = R @ I1 + [mx, my], R @ D1 + [mx, my]
        dd = [np.linalg.norm(I1 - D1), np.linalg.norm(I2 - D2), np.linalg.norm(I1 - I2), np.linalg.norm(D1 - D2),
              np.linalg.norm(I1 - D2), np.linalg.norm(D1 - I2)]
        ls = tiza(*dd)
        bien = any(abs(((l['giro'] - giro + 180) % 360) - 180) < 0.01 and abs(l['x'] - mx) < 1e-3 and abs(l['y'] - my) < 1e-3
                   for l in ls)
        dd2 = list(dd); dd2[1] += 0.05                 # la medida redundante (I2-D2) con 5 cm de error
        control = min(l['cierre'] for l in tiza(*dd2)) > 0.02
        print(f"  tiza · giro {giro:+.0f}°, eje ({mx:+.2f}, {my:+.2f}): {'recupera' if bien else 'NO recupera'} · "
              f"control, I2-D2 con 5 cm de error: el cierre {'lo delata' if control else 'NO lo delata'}")
        ok &= bien and control
    import tempfile
    from odometria import WB, E, delta_en_el_lugar
    d = math.degrees(delta_en_el_lugar())
    ang = d / LADO_MOTRIZ + CENTRO_184 * GRADOS_184
    total = WB * math.pi / 2 / math.sin(math.radians(d))       # metros de rueda para 90°
    ruta = os.path.join(tempfile.mkdtemp(), "t.log")
    with open(ruta, "w") as f:
        f.write(">>> 10:00:00.000 MARCA 1\n")
        n = 200
        for k in range(n + 1):
            f.write(f"10:00:{k // 10:02d}.{(k % 10) * 100:03d} T can=OPERACIONAL ang={ang:.2f} vel=0.1 dist={total * k / n:.4f} "
                    f"camino=0 hz184=50 tec=0 rec=0 bus=ok\n")
    t = tramos(ruta)[0]
    bien = abs(abs(t['giro']) - 90) < 0.5 and t['eje'] < 0.01
    print(f"  log · rueda a {d:.1f}° (rotar sobre el medio del eje), {total:.3f} m de rueda: giro {t['giro']:+.1f}°, "
          f"eje movido {100 * t['eje']:.1f} cm → {'bien' if bien else 'MAL'}")
    ok &= bien

    # 3) comparar: un equipo «real» con el centro en +0.4 (no +1.2), e = 0.38 y la marcha 2 % corta. Se le pasa la
    # tiza que daría ese equipo y el log que daría su bus; el ajuste tiene que devolver esos números. Control: si el
    # equipo real es el modelo, el ajuste tiene que devolver el modelo.
    def sintetico(ang, metros, real_c, real_e, real_k, n=400):
        filas = [(f"10:00:{k // 10 % 60:02d}.{(k % 10) * 100:03d}", ang, metros * k / n) for k in range(n + 1)]
        (x, y, th), _ = integrar(filas, centro=real_c, e=LADO_MOTRIZ * real_e, k=real_k)
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        I1, D1 = np.array([0, a / 2]), np.array([0, -a / 2])
        I2, D2 = R @ I1 + [x, y], R @ D1 + [x, y]
        dd = [np.linalg.norm(I1 - D1), np.linalg.norm(I2 - D2), np.linalg.norm(I1 - I2), np.linalg.norm(D1 - D2),
              np.linalg.norm(I1 - D2), np.linalg.norm(D1 - I2)]
        t = dict(filas=filas, ang_medio=ang, marca=0)
        (t['x'], t['y'], th0), _ = integrar(filas)
        t['giro'] = math.degrees(th0)
        return t, dd
    from odometria import E, WB
    for nombre, (rc, re_, rk) in (("equipo distinto del modelo", (0.4, 0.38, 0.98)),
                                  ("control: el equipo ES el modelo", (CENTRO_184 * GRADOS_184, abs(E), 1.0))):
        t, dd = sintetico(0.4 if rc != CENTRO_184 * GRADOS_184 else 1.2, 5.0, rc, re_, rk)
        rr = comparar(t, elegir(tiza(*dd), t))
        t2, dd2 = sintetico(-100.0, WB * math.pi / 2 / math.sin(math.radians(101.2)) / rk, rc, re_, rk)
        rg = comparar(t2, elegir(tiza(*dd2), t2), centro=rr['centro'])
        bien = (rr['centro'] is not None and abs(rr['centro'] - rc) < 0.02 and abs(rr['k_marcha'] - rk) < 0.002
                and abs(rg['k_giro'] - rk) < 0.002 and abs(rg['e'] - re_) < 0.003)
        print(f"  comparar · {nombre} (centro {rc:+.2f}, e {re_:.3f}, marcha ×{rk:.2f}): ajusta centro "
              f"{rr['centro']:+.2f}, marcha ×{rr['k_marcha']:.3f}, giro ×{rg['k_giro']:.3f}, e {rg['e']:.3f} → "
              f"{'bien' if bien else 'MAL'}")
        ok &= bien
    # control del control: sin el centro de la recta (dejando el +1.2 del modelo), el e sale mal
    t, dd = sintetico(-100.0, 2.7, 0.4, 0.38, 1.0)
    rg = comparar(t, elegir(tiza(*dd), t))
    mal = abs(rg['e'] - 0.38) > 0.01
    print(f"  control: el giro sin pasarle el centro de la recta da e {rg['e']:.3f} (real 0.38) → "
          f"{'se nota, por eso va T1 primero' if mal else 'NO se nota (el control no discrimina)'}")
    ok &= mal
    print("RESULTADO:", "PASA" if ok else "FALLA")
    return 0 if ok else 1


def main():
    for _f in (sys.stdout, sys.stderr):
        try:
            _f.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if "--prueba" in sys.argv:
        sys.exit(prueba())
    def opcion(nombre, defecto=None):
        return float(sys.argv[sys.argv.index(nombre) + 1]) if nombre in sys.argv else defecto
    adelante = opcion("--adelante", 0.0) / 100
    if "--objetivo" in sys.argv:
        k = sys.argv.index("--objetivo")
        ang, grados = float(sys.argv[k + 1]), float(sys.argv[k + 2])
        o = objetivo(ang, grados, opcion("--ancho", 131.5) / 100, opcion("--retro", 0.0) / 100, adelante)
        print(f"rueda a {ang:+.1f} (0x184/100), {'retroceder %.0f cm recto y ' % opcion('--retro', 0.0) if opcion('--retro') else ''}"
              f"girar {grados:+.0f}° con {o['marcha']}: {o['rueda_m']:.2f} m de rueda")
        print(f"  medio del eje de carga se mueve ({100 * o['eje'][0]:+.1f}, {100 * o['eje'][1]:+.1f}) cm (adelante, izquierda)")
        for n, P in (("I2", o['I2']), ("D2", o['D2'])):
            print(f"  {n}: {100 * P[0]:+7.1f} cm hacia las uñas y {100 * P[1]:+7.1f} cm a la izquierda, desde el medio de I1-D1")
        print("  distancias esperadas (cm): " + "  ".join(f"{n} {100 * v:.1f}" for n, v in o['dist'].items()))
        return
    if "--tiza" in sys.argv and len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        k = sys.argv.index("--tiza")
        dd = [float(x) / 100 for x in sys.argv[k + 1:k + 7]]
        n = int(opcion("--marca", 1))
        t = [t for t in tramos(sys.argv[1]) if t['marca'] == n]
        if not t:
            print(f"no hay MARCA {n} en el log")
            return
        l = elegir(tiza(*dd, adelante=adelante), t[0])
        imprimir_comparacion(t[0], l, comparar(t[0], l, centro=opcion("--centro")))
        return
    if "--tiza" in sys.argv:
        k = sys.argv.index("--tiza")
        dd = [float(x) / 100 for x in sys.argv[k + 1:k + 7]]
        for l in tiza(*dd, adelante=adelante):
            print(f"  tiza: giro {l['giro']:+7.2f}° · medio del eje movido {100 * l['eje']:5.1f} cm (adelante {100 * l['x']:+.1f}, "
                  f"izquierda {100 * l['y']:+.1f}) · cierre {100 * l['cierre']:.1f} cm (grande = alguna medida está mal)")
        print("  (las dos son espejo una de otra: vale la que tiene el mismo signo de giro que la odometría)")
        return
    if len(sys.argv) < 2:
        print(__doc__)
        return
    for t in tramos(sys.argv[1]):
        print(f"MARCA {t['marca']:2d}  {t['desde']}–{t['hasta']}  giro {t['giro']:+7.2f}°  medio del eje movido "
              f"{100 * t['eje']:5.1f} cm (adelante {100 * t['x']:+.1f}, izquierda {100 * t['y']:+.1f})  rueda recorrió "
              f"{t['camino']:.3f} m  ang {t['rueda'][0]:+.1f}…{t['rueda'][1]:+.1f} (media {t['ang_medio']:+.2f})")


if __name__ == "__main__":
    main()
