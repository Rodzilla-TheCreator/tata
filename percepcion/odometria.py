# ─────────────────────────────────────────────────────────────────────────────
# Odometría del EDR18N2 — modelo cinemático de bicicleta
#
# Es la MISMA cinemática de analisis/planificador_giro.py (función step, línea 54):
#   · el punto de referencia es el EJE DE RUEDAS DE CARGA (el pivote, a = 0)
#   · la rueda directriz va ATRÁS, a WB del pivote
#   · dθ = −(ds/WB)·tan(δ), integración por punto medio del rumbo
# No se importa del planificador porque ese archivo corre el plan al importarlo; se copia
# la fórmula y se comprueba que coincide (ver comparar_con_planificador abajo).
#
# Entradas, en producción: velocidad de tracción (nodo 8) y ángulo de dirección (nodo 4),
# leídas del bus. Hoy no hay captura real del bus: sim_sintetico.py las genera.
# ─────────────────────────────────────────────────────────────────────────────
import math

WB = 1.562          # entre ejes, m (CLAUDE.md; igual que el planificador)
Wa = 1.797          # radio de giro de ficha, m
XPIV = 1.50         # culo → eje de carga, DERIVADO (CLAUDE.md), no medido
W_MAX = 1.315
# tope de dirección, con la misma fórmula del planificador (≈ 78°)
DMAX = math.atan(WB / (math.sqrt(Wa**2 - XPIV**2) - W_MAX / 2))


def incremento(v, delta, dt):
    """Incremento de pose en el marco del VEHÍCULO al inicio del paso.

    v en m/s (positiva = hacia adelante), delta en rad, dt en s.
    Devuelve (dx, dy, dtheta): dx a lo largo del rumbo inicial, dy a su izquierda.
    """
    ds = v * dt
    dth = -(ds / WB) * math.tan(delta)
    thm = dth * 0.5                       # rumbo medio del paso, relativo al inicial
    return ds * math.cos(thm), ds * math.sin(thm), dth


def avanzar(pose, v, delta, dt):
    """Pose (x, y, θ) en el marco del pasillo después de dt. Igual que step() del planificador."""
    x, y, th = pose
    ds = v * dt
    dth = -(ds / WB) * math.tan(delta)
    thm = th + dth * 0.5
    return (x + ds * math.cos(thm), y + ds * math.sin(thm), th + dth)


def avanzar_rueda(pose, v_rueda, delta, dt):
    """Lo mismo que avanzar(), pero con la velocidad de la RUEDA MOTRIZ (lo que mide el encoder de
    tracción) en vez de la del eje de carga. Es la cinemática v3 del planificador
    (planificador_rutas.step con rueda=True): con δ = 90° el equipo rota sobre el eje de carga y
    tan δ, que usa avanzar(), es infinita. Para δ < 90° es idéntica a avanzar(v_rueda·cos δ, δ).

        ds_eje = ds_rueda · cos δ          dθ = −(ds_rueda / WB) · sin δ
    """
    x, y, th = pose
    dsr = v_rueda * dt
    ds = dsr * math.cos(delta)
    dth = -(dsr / WB) * math.sin(delta)
    thm = th + dth * 0.5
    return (x + ds * math.cos(thm), y + ds * math.sin(thm), th + dth)


def comparar_con_planificador(n=200):
    """Control: la fórmula copiada da lo mismo que step() del planificador (sin importarlo)."""
    import random
    def step(p, ds, d):                   # copia literal de analisis/planificador_giro.py:54
        dth = -(ds / WB) * math.tan(d); th2 = p[2] + dth * 0.5
        return (p[0] + ds * math.cos(th2), p[1] + ds * math.sin(th2), p[2] + dth)
    r = random.Random(1)
    peor = 0.0
    for _ in range(n):
        p = (r.uniform(-5, 5), r.uniform(-1.5, 1.5), r.uniform(-math.pi, math.pi))
        v, d, dt = r.uniform(-1.5, 1.5), r.uniform(-DMAX, DMAX), r.uniform(0.01, 0.1)
        a, b = avanzar(p, v, d, dt), step(p, v * dt, d)
        peor = max(peor, max(abs(a[i] - b[i]) for i in range(3)))
    return peor


if __name__ == "__main__":
    print(f"WB = {WB} m · tope de dirección DMAX = {math.degrees(DMAX):.1f}°")
    print(f"radio de giro del pivote a tope: {WB / math.tan(DMAX):.2f} m")
    print(f"diferencia máxima contra step() del planificador: {comparar_con_planificador():.2e}")
