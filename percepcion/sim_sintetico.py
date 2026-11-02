# ─────────────────────────────────────────────────────────────────────────────
# Prueba sintética del EKF — odometría + ArUco, con su control de falsación
#
#   py percepcion/sim_sintetico.py            # corrida + 30 semillas + figura
#
# Trayectoria verdadera: arranca en el pasillo, acelera a 1.0 m/s, recorre ~16 m, frena a
# 0.4 m/s, gira 90° a la izquierda y para. Se generan odometría ruidosa (con SESGO, que es lo
# que hace derivar de verdad) y detecciones ArUco ruidosas contra un mapa de marcas.
#
# Tres corridas con el MISMO ruido de odometría (números aleatorios comunes):
#   A · ArUco encendido            → el error tiene que quedar acotado (< 4.5 cm lateral)
#   B · ArUco apagado (CONTROL)    → solo odometría: el error tiene que CRECER. Si no crece, el
#                                    test no probó nada
#   C · ArUco con oclusión          → tapas cubiertas entre x = 6 y 11 m: el filtro navega con
#                                    odometría y se vuelve a enganchar al reaparecer una marca
#
# Valores elegidos y de dónde salen (lo que no tiene fuente dice SUPUESTO):
#   dt 20 ms                 el SYNC del bus es de 20 ms (medido 19-oct, docs/21)
#   velocidad 1.0 m/s        bajo el sobre de 1.5 m/s (CLAUDE.md)
#   pasillo ±1.50 m          3.00 m de pasillo (CLAUDE.md); marcas en las caras del rack
#   marca cada 2.35 m        una por bahía (CLAUDE.md: bahía de 2.35 m) — SUPUESTO de dónde van
#   ruido ArUco              analisis/aruco_precision.py, USB 5 MP, marca 15 cm, 1–2.5 m:
#                            lateral 1–3 mm, profundidad ~1–2 cm, ángulo ~1–2°. Se toma
#                            σ_dist 2 cm, σ_lat 0.5 cm, σ_yaw 2° (el lado pesimista)
#   error de colocación      σ 1 cm por marca, fijo (mapa creído ≠ mapa real) — SUPUESTO.
#                            Es el mismo en cada vista: ver ColocacionMarcas en ekf.py
#   odometría                velocidad: sesgo +2 % y ruido 0.02 m/s; dirección: sesgo +0.5° y
#                            ruido 0.5° — SUPUESTOS hasta capturar el bus con el equipo andando
#   cámaras                  dos laterales a ±0.55 m del eje de carga, mirando a cada rack,
#                            10 Hz, ven marcas entre 0.3 y 3 m, ±50° — SUPUESTO de montaje
#   requisito                ±4.5 cm lateral: lo que deja la bahía (analisis/aruco_precision.py)
# ─────────────────────────────────────────────────────────────────────────────
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ekf import EKF, ColocacionMarcas, envolver, marca_vista_desde, pose_desde_marca, R_pose   # noqa: E402
from odometria import avanzar                                              # noqa: E402

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DT = 0.02
HALF = 1.50
PASO_MARCAS = 2.35
REQ_LAT = 0.045                 # requisito lateral, m
SIG_MED = np.array([0.02, 0.005, math.radians(2.0)])     # dist, lateral, yaw
SIG_COLOCACION = 0.01
CAMARAS = {"izq": (0.0, +0.55, +math.pi / 2), "der": (0.0, -0.55, -math.pi / 2)}
PERIODO_CAM = 0.10
OCLUSION = (6.0, 11.0)          # x donde las marcas están tapadas (corrida C)


def mapa_marcas():
    """id → (x, y, θ normal). Rack izquierdo en y = +1.5 (normal hacia −y), derecho en −1.5."""
    m, i = {}, 0
    for x in np.arange(0.0, 24.0, PASO_MARCAS):
        m[i] = (x, +HALF, -math.pi / 2); i += 1
        m[i] = (x + PASO_MARCAS / 2, -HALF, +math.pi / 2); i += 1
    return m


def trayectoria():
    """Entradas verdaderas (v, δ) por paso: acelerar, recorrer, frenar, girar 90° a la izquierda, parar."""
    u, pose = [], (0.0, 0.0, 0.0)
    v = 0.0
    while pose[0] < 16.0:
        v = min(1.0, v + 0.5 * DT)
        u.append((v, 0.0)); pose = avanzar(pose, v, 0.0, DT)
    while v > 0.4:
        v = max(0.4, v - 0.5 * DT)
        u.append((v, 0.0)); pose = avanzar(pose, v, 0.0, DT)
    d = -math.radians(60)                       # dθ = −(ds/WB)·tanδ: δ < 0 gira a la izquierda
    while pose[2] < math.pi / 2:
        u.append((v, d)); pose = avanzar(pose, v, d, DT)
    while v > 0:
        v = max(0.0, v - 0.5 * DT)
        u.append((v, 0.0)); pose = avanzar(pose, v, 0.0, DT)
    for _ in range(int(1.0 / DT)):              # 1 s quieto
        u.append((0.0, 0.0))
    return u


def correr(semilla, aruco=True, oclusion=False):
    rng = np.random.default_rng(semilla)
    rng_med = np.random.default_rng(semilla + 10_000)
    real = mapa_marcas()
    creido = {k: (x + rng.normal(0, SIG_COLOCACION), y + rng.normal(0, SIG_COLOCACION), th)
              for k, (x, y, th) in real.items()}
    u = trayectoria()
    sesgo_v, sesgo_d = 1.02, math.radians(0.5)
    verdad = (0.0, 0.0, 0.0)
    pose0 = (0.05, -0.03, math.radians(1.0))          # el arranque no se conoce exacto
    P0 = np.diag([0.10 ** 2, 0.10 ** 2, math.radians(3) ** 2])
    f = EKF(pose0, P0)
    coloc = ColocacionMarcas(SIG_COLOCACION)
    t, proxima_cam = 0.0, 0.0
    T, V, E, SIG, VISTAS = [], [], [], [], []
    Rm = np.diag(SIG_MED ** 2)
    for v, d in u:
        verdad = avanzar(verdad, v, d, DT)
        v_med = v * sesgo_v + (rng.normal(0, 0.02) if v > 0 else 0.0)
        d_med = d + sesgo_d + rng.normal(0, math.radians(0.5))
        f.predict(v_med, d_med, DT)
        t += DT
        vistas = 0
        if aruco and t >= proxima_cam:
            proxima_cam += PERIODO_CAM
            tapado = oclusion and OCLUSION[0] <= verdad[0] <= OCLUSION[1]
            for k, mk in real.items():
                if tapado:
                    break
                for mont in CAMARAS.values():
                    dist, lat, yaw = marca_vista_desde(verdad, mk, mont)
                    if not (0.3 < dist < 3.0 and abs(math.atan2(lat, dist)) < math.radians(50)
                            and abs(yaw) < math.radians(50)):
                        continue
                    dm = np.array([dist, lat, yaw]) + rng_med.normal(0, SIG_MED)
                    z = pose_desde_marca(creido[k], *dm, mont)
                    R = R_pose(creido[k], *dm, mont, Rm) + coloc.R(k, t)
                    if f.update_aruco(z, R):
                        vistas += 1
        T.append(t); V.append(verdad); E.append(f.pose)
        SIG.append(np.sqrt(np.diag(f.P_pose))); VISTAS.append(vistas)
    V, E = np.array(V), np.array(E)
    dx, dy = E[:, 0] - V[:, 0], E[:, 1] - V[:, 1]
    lat = -np.sin(V[:, 2]) * dx + np.cos(V[:, 2]) * dy        # error lateral (perpendicular al rumbo real)
    pos = np.hypot(dx, dy)
    rumbo = np.degrees(np.abs([envolver(a) for a in E[:, 2] - V[:, 2]]))
    return dict(t=np.array(T), verdad=V, est=E, lat=lat, pos=pos, rumbo=rumbo,
                sig=np.array(SIG), vistas=np.array(VISTAS), rechazadas=f.rechazadas,
                reaperturas=f.reaperturas, b=f.x[3], s=f.x[4], b_real=sesgo_d, s_real=1 / sesgo_v)


def evaluar(A, B, C, verbose=False):
    """Los tres criterios. Devuelve dict de bool."""
    asentado = A["t"] > 2.0                              # deja converger el arranque
    okA = (np.max(np.abs(A["lat"][asentado])) < REQ_LAT) and (np.sqrt(np.mean(A["rumbo"][asentado] ** 2)) < 1.0)
    n = len(B["pos"])
    crece = B["pos"][-1] > 2 * B["pos"][n // 3]
    okB = crece and (B["pos"][-1] > 3 * np.max(A["pos"][asentado]))
    en_ocl = (C["verdad"][:, 0] >= OCLUSION[0]) & (C["verdad"][:, 0] <= OCLUSION[1])
    # Control de que la oclusión fue real y el filtro navegó a ciegas:
    #   · cero marcas aceptadas en el tramo
    #   · la incertidumbre del filtro crece (sabe que va a ciegas)
    #   · el error real queda dentro de 3σ (no se miente: es lo que habría atrapado la primera
    #     versión, que decía σθ 0.23° con 1.75° de error real)
    # Historial (02-nov): se probó «error en la oclusión > máximo de toda la corrida A» y luego
    # «> 2× A en el mismo tramo». Ninguno medía lo que se quería: con el sesgo estimado el
    # filtro bueno deriva solo 1–3 cm en 5 s, y el máximo de A cae en el giro. Se quitaron.
    sin_marcas = C["vistas"][en_ocl].sum() == 0
    deriva_ocl = True
    sabe = C["sig"][np.where(en_ocl)[0][-1], 1] > 3 * C["sig"][np.where(en_ocl)[0][0], 1]
    consistente = np.all(np.abs(C["lat"][en_ocl]) < 3 * np.maximum(C["sig"][en_ocl, 1], 1e-3) + 0.01)
    i_fin = np.where(en_ocl)[0][-1]
    t_fin = C["t"][i_fin]
    despues = (C["t"] > t_fin + 2.0)
    reengancha = np.max(np.abs(C["lat"][despues])) < REQ_LAT
    okC = sin_marcas and deriva_ocl and sabe and consistente and reengancha
    if verbose:
        print("A · ArUco encendido")
        print(f"    error lateral  RMS {100*np.sqrt(np.mean(A['lat'][asentado]**2)):.2f} cm · máx {100*np.max(np.abs(A['lat'][asentado])):.2f} cm   (requisito ±{100*REQ_LAT:.1f} cm)")
        print(f"    rumbo          RMS {np.sqrt(np.mean(A['rumbo'][asentado]**2)):.2f}° · máx {np.max(A['rumbo'][asentado]):.2f}°")
        print(f"    correcciones rechazadas por la compuerta: {A['rechazadas']} · reaperturas: {A['reaperturas']}")
        print(f"    sesgo de dirección estimado {math.degrees(A['b']):+.2f}° (real {math.degrees(A['b_real']):+.2f}°) · escala de velocidad {A['s']:.4f} (real {A['s_real']:.4f})")
        print(f"    → {'PASA' if okA else 'FALLA'}: error acotado")
        print("B · ArUco apagado (control, solo odometría)")
        print(f"    error de posición: {100*B['pos'][n//3]:.1f} cm al tercio · {100*B['pos'][-1]:.1f} cm al final · lateral final {100*B['lat'][-1]:+.1f} cm · rumbo final {B['rumbo'][-1]:.2f}°")
        print(f"    → {'PASA' if okB else 'FALLA'}: el error crece sin ArUco (si no creciera, el test no probaría nada)")
        print(f"C · ArUco con oclusión (x = {OCLUSION[0]:.0f}–{OCLUSION[1]:.0f} m, {t_fin - C['t'][np.where(en_ocl)[0][0]]:.1f} s sin marcas)")
        print(f"    marcas aceptadas durante la oclusión: {C['vistas'][en_ocl].sum()} (tiene que ser 0)")
        print(f"    error de posición máx en el tramo: {100*np.max(C['pos'][en_ocl]):.2f} cm con oclusión vs {100*np.max(A['pos'][en_ocl]):.2f} cm con ArUco en el mismo tramo")
        print(f"    σ lateral del filtro: {100*C['sig'][np.where(en_ocl)[0][0],1]:.2f} → {100*C['sig'][np.where(en_ocl)[0][-1],1]:.2f} cm (sabe que va a ciegas) · error dentro de 3σ: {'sí' if consistente else 'NO'}")
        print(f"    error lateral máx desde 2 s después de reaparecer: {100*np.max(np.abs(C['lat'][despues])):.2f} cm · reaperturas: {C['reaperturas']}")
        print(f"    → {'PASA' if okC else 'FALLA'}: navega con odometría y se vuelve a enganchar")
    return dict(A=okA, B=okB, C=okC)


def figura(A, B, C, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), gridspec_kw=dict(height_ratios=[1.2, 1]))
    ax1.axhspan(-HALF, HALF, color="0.95")
    ax1.axvspan(*OCLUSION, color="#ffe9a8", alpha=0.6, label="oclusión (corrida C)")
    for k, (x, y, th) in mapa_marcas().items():
        ax1.plot(x, y, "s", ms=4, color="0.4")
    ax1.plot(A["verdad"][:, 0], A["verdad"][:, 1], "k-", lw=2.2, label="verdad")
    ax1.plot(B["est"][:, 0], B["est"][:, 1], "-", color="#d62728", lw=1.4, label="solo odometría (B)")
    ax1.plot(C["est"][:, 0], C["est"][:, 1], "--", color="#1f77b4", lw=1.4, label="EKF con oclusión (C)")
    ax1.set_aspect("equal"); ax1.set_xlim(-0.5, 22); ax1.set_ylim(-1.8, 2.2)
    ax1.set_xlabel("x a lo largo del pasillo (m)"); ax1.set_ylabel("y lateral (m)")
    ax1.set_title("EKF odometría + ArUco — trayectoria (marcas en las caras del rack)")
    ax1.legend(loc="upper left", fontsize=8, ncol=2)
    ax2.plot(A["t"], 100 * np.abs(A["lat"]), color="#2ca02c", label="A · ArUco encendido")
    ax2.plot(B["t"], 100 * np.abs(B["lat"]), color="#d62728", label="B · solo odometría")
    ax2.plot(C["t"], 100 * np.abs(C["lat"]), color="#1f77b4", label="C · ArUco con oclusión")
    en = (C["verdad"][:, 0] >= OCLUSION[0]) & (C["verdad"][:, 0] <= OCLUSION[1])
    ax2.axvspan(C["t"][en][0], C["t"][en][-1], color="#ffe9a8", alpha=0.6)
    ax2.axhline(100 * REQ_LAT, color="k", ls=":", lw=1, label="requisito ±4.5 cm")
    ax2.set_yscale("log"); ax2.set_ylim(0.01, 200)
    ax2.set_xlabel("tiempo (s)"); ax2.set_ylabel("|error lateral| (cm)")
    ax2.legend(fontsize=8, loc="upper left"); ax2.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(ruta, dpi=110)


def main():
    from odometria import comparar_con_planificador
    print(f"odometría vs step() del planificador: diferencia máx {comparar_con_planificador():.1e}\n")
    A, B, C = correr(0, aruco=True), correr(0, aruco=False), correr(0, aruco=True, oclusion=True)
    r = evaluar(A, B, C, verbose=True)
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ekf_sintetico.png")
    figura(A, B, C, ruta)
    print(f"\nfigura: {ruta}")
    N = 30
    tot = dict(A=0, B=0, C=0)
    for s in range(1, N + 1):
        rr = evaluar(correr(s), correr(s, aruco=False), correr(s, oclusion=True))
        for k in tot:
            tot[k] += rr[k]
    print(f"\n{N} semillas más: A pasa {tot['A']}/{N} · B pasa {tot['B']}/{N} · C pasa {tot['C']}/{N}")
    ok = all(r.values()) and all(v == N for v in tot.values())
    print("RESULTADO:", "PASA" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
