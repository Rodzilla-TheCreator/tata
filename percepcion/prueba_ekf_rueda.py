"""Prueba del EKF con la velocidad de la RUEDA MOTRIZ (rueda=True, 09-nov), con sus controles.

    python percepcion/prueba_ekf_rueda.py

1. La odometría nueva es la cinemática del planificador v3: avanzar_rueda = planificador_rutas.step(rueda=True),
   y para δ < 90° es la misma que la vieja con v_eje = v_rueda·cos δ.
   Control: con la fórmula de tan δ en 90° da infinito / basura.
2. Los jacobianos F y G del predict son los de verdad (diferencias finitas), también con δ = 90°.
   Control: un jacobiano con un signo cambiado tiene que fallar la misma comprobación.
3. El filtro en el giro v3: recta con marcas, rotación de 90° sobre el eje de carga sin marcas (8 s),
   llegada. Odometría con sesgo de dirección y de escala. 30 semillas: el error al llegar tiene que quedar
   dentro de 3σ de lo que el filtro dice (que sepa cuánto no sabe) y acotado.
   Control: el mismo recorrido con el filtro viejo (tan δ, alimentado con v_eje = v_rueda·cos δ) tiene que
   NO cumplir los ±4.5 cm. (Se esperaba que no diera número; da, pero se va 5–31 cm: cerca de 90° el término
   1 + tan²δ de su jacobiano vale ~10⁴, la covarianza explota y deja de aprovechar las marcas.)

24-nov · la motriz corrida (odometria.E = 0.325, WB 1.688, topes −104.4 / +79.4):
1. compara contra el planificador con la MISMA geometría (planificador_rutas.con_geo), y de_bus contra los
   crudos del 23-nov. Control: con e la pose cambia respecto de e = 0 (si no, el corrimiento no se aplica).
2. los jacobianos con e, en todo el rango de los topes y justo en ellos.
3. el giro rota en el lugar con δ = atan(WB/e) ≈ 79° (ya no con 90°). Segundo control: el filtro del 09-nov
   (rueda, pero e = 0) en el equipo de verdad (e = 0.325) tampoco cumple: cree que el eje de carga avanza.
   Tercer control: con la motriz del otro lado (LADO_MOTRIZ al revés) tampoco: el signo de e hay que saberlo.
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'analisis'))
from ekf import EKF, envolver                       # noqa: E402
from odometria import (E, LADO_MOTRIZ, TOPES_184, WB, avanzar, avanzar_rueda, de_bus,  # noqa: E402
                       delta_en_el_lugar)
TOPE_NEG, TOPE_POS = sorted(LADO_MOTRIZ * math.radians(t) for t in TOPES_184)

rng = np.random.default_rng(7)


def prueba_odometria():
    import planificador_rutas as P
    peor_plan = peor_vieja = 0.0
    cambio_e = 0.0
    with P.con_geo(WB, E):
        for _ in range(500):
            p = (rng.uniform(-5, 5), rng.uniform(-1.5, 1.5), rng.uniform(-math.pi, math.pi))
            v, d, dt = rng.uniform(-1.5, 1.5), rng.uniform(TOPE_NEG, TOPE_POS), rng.uniform(0.01, 0.1)
            a, b = avanzar_rueda(p, v, d, dt), P.step(p, v * dt, d, rueda=True)
            peor_plan = max(peor_plan, max(abs(a[i] - b[i]) for i in range(3)))
            a0 = avanzar_rueda(p, v, d, dt, e=0.0)
            cambio_e = max(cambio_e, math.hypot(a[0] - a0[0], a[1] - a0[1]) / max(abs(v * dt), 1e-9))
            if abs(d) < math.radians(80):
                c = avanzar(p, v * math.cos(d), d, dt)
                peor_vieja = max(peor_vieja, max(abs(a0[i] - c[i]) for i in range(3)))
    with np.errstate(all='ignore'):
        q = avanzar((0.0, 0.0, 0.0), 0.35, math.pi / 2, 0.1)     # la vieja en 90°: tan(π/2) ~ 1.6e16
    control = abs(q[2]) > 1e6
    # de_bus con los crudos del 23-nov: el pico de 479 ≈ 0.35 m/s; la recta (+120) = 0; el tope corto (+7 940
    # desde el centro) = +79.4° del lado de la motriz
    v, d0 = de_bus(479, 120)
    _, dc = de_bus(0, 120 + 7940)
    bus = abs(v - 0.3497) < 1e-3 and abs(d0) < 1e-12 and abs(math.degrees(dc) - LADO_MOTRIZ * 79.4) < 1e-9
    ok = peor_plan < 1e-12 and peor_vieja < 1e-12 and control and cambio_e > 0.1 and bus
    print(f"1. odometría (WB {WB}, e {E:+.3f}): contra step(rueda=True) del planificador con la misma geometría "
          f"{peor_plan:.1e} · con e = 0, contra la vieja con v·cos δ (δ < 80°) {peor_vieja:.1e} · de_bus "
          f"{'bien' if bus else 'MAL'} · control, e cambia la pose (máx {cambio_e:.2f} m por m de rueda) · control, "
          f"la vieja en 90°: Δθ = {q[2]:.1e} rad → {'PASA' if ok else 'FALLA'}")
    return ok


def _paso(x, u, rueda, dt=0.05):
    """Un predict desde el estado x (5) con entradas u = (v, δ); devuelve el estado nuevo y (F, G)."""
    f = EKF(x[:3], np.eye(3) * 1e-4, rueda=rueda)
    f.x = np.array(x, float)
    f.predict(u[0], u[1], dt)
    return f.x.copy(), f.ultimo


def _comprobar(rueda, roto=False, n=300):
    peor = 0.0
    for _ in range(n):
        lo, hi = (TOPE_NEG, TOPE_POS) if rueda else (-math.radians(75), math.radians(75))
        x = np.array([rng.uniform(-5, 5), rng.uniform(-1.5, 1.5), rng.uniform(-3, 3),
                      rng.normal(0, 0.02), rng.uniform(0.95, 1.05)])
        u = np.array([rng.uniform(-1.5, 1.5), rng.uniform(lo, hi)])
        if rueda and rng.random() < 0.3:
            u[1] = rng.choice([lo, hi, math.pi / 2, delta_en_el_lugar()])   # en los topes, en 90° y en el lugar
        x1, (F, G) = _paso(x, u, rueda)
        if roto:                                                       # el control: un signo cambiado
            F = F.copy(); F[:3, 3] = -F[:3, 3]
        h = 1e-6
        Fn, Gn = np.zeros((5, 5)), np.zeros((5, 2))
        for k in range(5):
            e = np.zeros(5); e[k] = h
            a, _ = _paso(x + e, u, rueda); b, _ = _paso(x - e, u, rueda)
            d = (a - b) / (2 * h); d[2] = envolver(a[2] - b[2]) / (2 * h); Fn[:, k] = d
        for k in range(2):
            e = np.zeros(2); e[k] = h
            a, _ = _paso(x, u + e, rueda); b, _ = _paso(x, u - e, rueda)
            d = (a - b) / (2 * h); d[2] = envolver(a[2] - b[2]) / (2 * h); Gn[:, k] = d
        escala = max(1.0, np.abs(Fn).max(), np.abs(Gn).max())
        peor = max(peor, np.abs(F - Fn).max() / escala, np.abs(G[:, :] - Gn).max() / escala)
    return peor


def prueba_jacobianos():
    e_r, e_t, e_roto = _comprobar(True), _comprobar(False), _comprobar(True, roto=True, n=60)
    ok = e_r < 1e-6 and e_t < 1e-6 and e_roto > 1e-3
    print(f"2. jacobianos contra diferencias finitas: rueda (e {E:+.3f}, topes, 90° y en el lugar) {e_r:.1e} · eje de carga {e_t:.1e} · "
          f"control con ∂/∂b de signo cambiado {e_roto:.1e} (tiene que ser grande) → {'PASA' if ok else 'FALLA'}")
    return ok


def recorrido():
    """La verdad: (v_rueda, δ, dt, marca?) — recta 4 m con marcas, rotación de 90° sin marcas, 0.16 m.
    24-nov: la rotación sobre el eje de carga es con δ = atan(WB/e) ≈ 79° (la motriz corrida), no con 90°."""
    pasos, dt = [], 0.02
    for k in range(int(4.0 / (1.0 * dt))):
        pasos.append((1.0, 0.0, dt, k % 5 == 0))                       # marca a 10 Hz
    d_rot = delta_en_el_lugar()
    for _ in range(int((WB * math.pi / 2) / (0.35 * math.sin(d_rot) * dt))):
        pasos.append((0.35, d_rot, dt, False))                         # rota sobre el eje de carga
    for _ in range(int(0.163 / (0.2 * dt))):
        pasos.append((0.2, 0.0, dt, False))                            # APROXIMA, sin marcas
    return pasos


def correr(semilla, rueda, e_filtro=None):
    r = np.random.default_rng(semilla)
    sesgo_d, escala = math.radians(0.5), 1.02
    verdad = np.array([0.0, 0.0, 0.0])
    f = EKF(verdad + r.normal(0, [0.02, 0.02, 0.01]), np.diag([0.02 ** 2, 0.02 ** 2, 0.01 ** 2]), rueda=rueda,
            e=e_filtro)
    with np.errstate(all='ignore'):
        for v, d, dt, marca in recorrido():
            verdad = np.array(avanzar_rueda(verdad, v, d, dt))
            vm = v / escala + r.normal(0, 0.01)
            dm = d + sesgo_d + r.normal(0, math.radians(0.3))
            vin = vm if rueda else vm * math.cos(dm)                   # el viejo espera la del eje de carga
            f.predict(vin, dm, dt)
            if marca:
                z = verdad + r.normal(0, [0.01, 0.005, math.radians(0.5)])
                f.update_aruco(z, np.diag([0.01 ** 2, 0.005 ** 2, math.radians(0.5) ** 2]))
    e = f.pose - verdad
    e[2] = envolver(e[2])
    P = f.P_pose
    if not np.all(np.isfinite(e)) or not np.all(np.isfinite(P)):
        return None
    nees = float(e @ np.linalg.solve(P, e))
    lat = math.hypot(e[0], e[1])
    return lat, nees


def prueba_giro():
    res = [correr(s, True) for s in range(30)]
    lat = np.array([r[0] for r in res]); nees = np.array([r[1] for r in res])
    dentro = np.mean(nees < 14.16)                                     # χ² 3 gl al 99.7 % (3σ)
    viejos = [correr(s, False) for s in range(30)]
    lat_v = np.array([np.inf if r is None else r[0] for r in viejos])
    control = np.median(lat_v) > 0.045
    sin_e = [correr(s, True, e_filtro=0.0) for s in range(30)]
    lat_0 = np.array([np.inf if r is None else r[0] for r in sin_e])
    control_e = np.median(lat_0) > 0.045
    al_reves = [correr(s, True, e_filtro=-E) for s in range(30)]
    lat_r = np.array([np.inf if r is None else r[0] for r in al_reves])
    control_lado = np.median(lat_r) > 0.045
    print(f"   control 3, el filtro con la motriz del OTRO lado (LADO_MOTRIZ al revés, e {-E:+.3f}): mediana "
          f"{100 * np.median(lat_r):.1f} cm ({'no cumple ±4.5' if control_lado else 'CUMPLE: el lado no importa'})")
    ok = dentro >= 0.9 and lat.max() < 0.10 and control and control_e and control_lado
    print(f"   control 2, el filtro del 09-nov (rueda, e = 0) en el equipo con e {E:+.3f}: mediana "
          f"{100 * np.median(lat_0):.1f} cm, máx {100 * lat_0.max():.1f} cm "
          f"({'no cumple ±4.5' if control_e else 'CUMPLE: el corrimiento no importa'})")
    print(f"3. el giro a ciegas (90° sobre el eje de carga con δ {math.degrees(delta_en_el_lugar()):.1f}°, sesgo 0.5° "
          f"y escala 2 %): error al llegar "
          f"máx {100 * lat.max():.1f} cm, mediana {100 * np.median(lat):.1f} cm · dentro de 3σ del filtro "
          f"{100 * dentro:.0f} % · control, el filtro viejo: mediana {100 * np.median(lat_v):.1f} cm, máx "
          f"{100 * lat_v.max():.1f} cm ({'no cumple ±4.5' if control else 'CUMPLE: el control no prueba nada'}) "
          f"→ {'PASA' if ok else 'FALLA'}")
    return ok


if __name__ == '__main__':
    oks = [prueba_odometria(), prueba_jacobianos(), prueba_giro()]
    print('RESULTADO:', 'PASA' if all(oks) else 'FALLA')
    sys.exit(0 if all(oks) else 1)
