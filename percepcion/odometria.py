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
# leídas del bus: de_bus() pasa los crudos del 0x188 y el 0x184 (23-nov) a (v_rueda, δ).
#
# 24-nov · la geometría medida (campo/2026-11-23/resultados.md, analisis/rutas_resultados.md v4):
#
# | Decía | Es | Qué lo tumbó |
# |---|---|---|
# | entre ejes 1.562 (ficha de serie) | **1.688** (1.69 medido, batería de 539) | flexómetro, 23-nov |
# | la motriz sobre el eje del equipo | **corrida e ≈ 0.325 de lado**, bajo el timón (H1) | motriz ↔ apoyo 0.65; los topes |
# | topes ±90° | **−104.4° / +79.4°** del 0x184 (centro en +120 crudo) | 0x184 en los topes |
#
# Con la motriz corrida el giro no cambia (dθ = −(ds_rueda/WB)·sin δ) pero el medio del eje de carga
# avanza ds_rueda·(cos δ − (e/WB)·sin δ): rota en el lugar con tan δ = WB/e (≈ 79°), no con 90°.
# avanzar_rueda() y el EKF con rueda=True usan esto. avanzar() (tan δ, eje de carga, sin e) queda
# como estaba: la usan los simuladores sintéticos y la prueba del 02-nov.
#
# Marco: x hacia las uñas, y a la IZQUIERDA mirando del culo hacia las uñas, θ antihorario visto desde
# arriba. δ > 0 = la rueda rodando hacia +y. e > 0 = la motriz del lado +y.
# ─────────────────────────────────────────────────────────────────────────────
import math

WB_SERIE = 1.562    # entre ejes de la ficha de serie (lo que se usó hasta el 23-nov)
WB = 1.688          # entre ejes MEDIDO (1.69, 23-nov): batería de 539
E_MAG = 0.325       # corrimiento lateral de la motriz, m (motriz ↔ apoyo 0.65 / 2, supone la de apoyo simétrica).
                    # Los topes lo acotan a 0.316–0.433 (analisis/rutas_resultados.md, v4)
LADO_MOTRIZ = +1    # +1: el timón (y la motriz bajo él) a la IZQUIERDA mirando del culo hacia las uñas.
                    # SIN CONFIRMAR: sale de las dos vistas de arriba de las fichas, que dibujan el timón de ese lado.
                    # Si es al revés, poner −1: con el signo mal el rumbo integra al revés en cada curva
E = LADO_MOTRIZ * E_MAG
# 0x184 b2–b3 (int16, b2 bajo) × 0.01° = ángulo de la rueda; recta en +120 crudo. Tope corto +79.4°, largo
# −104.4°, desde la recta. Con H1 (confirmada 24-nov) el tope corto apunta hacia el lado de la motriz, así
# que δ del modelo = LADO_MOTRIZ · ángulo del 0x184
CENTRO_184 = 120
GRADOS_184 = 0.01
TOPES_184 = (-104.4, 79.4)
# 0x188 b2–b3 (int16, b2 bajo) × 7.30e-4 = velocidad de la rueda motriz, m/s. Positiva = hacia las uñas
M_S_188 = 7.30e-4
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


def avanzar(pose, v, delta, dt, wb=None):
    """Pose (x, y, θ) en el marco del pasillo después de dt. Igual que step() del planificador."""
    wb = WB if wb is None else wb
    x, y, th = pose
    ds = v * dt
    dth = -(ds / wb) * math.tan(delta)
    thm = th + dth * 0.5
    return (x + ds * math.cos(thm), y + ds * math.sin(thm), th + dth)


def avanzar_rueda(pose, v_rueda, delta, dt, e=None, wb=None):
    """Lo mismo que avanzar(), pero con la velocidad de la RUEDA MOTRIZ (lo que mide el encoder de
    tracción) en vez de la del eje de carga. Es la cinemática del planificador (planificador_rutas.step con
    rueda=True, v4 con E_MOTRIZ): tan δ, que usa avanzar(), es infinita en 90°; esto no.

        ds_eje = ds_rueda · (cos δ − (e/WB) · sin δ)          dθ = −(ds_rueda / WB) · sin δ

    e = 0 es el modelo v3 (09-nov), idéntico a avanzar(v_rueda·cos δ, δ) para δ < 90°.
    Por defecto e = E (24-nov) y wb = WB."""
    e = E if e is None else e
    wb = WB if wb is None else wb
    x, y, th = pose
    dsr = v_rueda * dt
    ds = dsr * (math.cos(delta) - (e / wb) * math.sin(delta))
    dth = -(dsr / wb) * math.sin(delta)
    thm = th + dth * 0.5
    return (x + ds * math.cos(thm), y + ds * math.sin(thm), th + dth)


def de_bus(crudo_188, crudo_184):
    """Los int16 del bus (0x188 b2–b3, 0x184 b2–b3) → (v_rueda m/s, δ rad) en el marco del modelo."""
    v = crudo_188 * M_S_188
    grados = (crudo_184 - CENTRO_184) * GRADOS_184
    return v, LADO_MOTRIZ * math.radians(grados)


def delta_en_el_lugar(e=None, wb=None):
    """δ con la que el medio del eje de carga no se mueve: tan δ = WB / e (con e = 0, 90°)."""
    e = E if e is None else e
    wb = WB if wb is None else wb
    return math.atan2(wb, e) if e >= 0 else -math.atan2(wb, -e)


def centro_de_giro(delta, e=None, wb=None):
    """y del centro de giro sobre la línea del eje de carga, desde su medio: e − WB / tan δ."""
    e = E if e is None else e
    wb = WB if wb is None else wb
    return float('inf') if abs(math.sin(delta)) < 1e-12 else e - wb * math.cos(delta) / math.sin(delta)


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
    print(f"motriz: WB {WB} · e {E:+.3f} (lado {LADO_MOTRIZ:+d}) · rota en el lugar con δ = "
          f"{math.degrees(delta_en_el_lugar()):.1f}° · topes del 0x184 {TOPES_184} → centro de giro "
          + ", ".join(f"{centro_de_giro(LADO_MOTRIZ * math.radians(t)) * 100:+.0f} cm" for t in TOPES_184))
