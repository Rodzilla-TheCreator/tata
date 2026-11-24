#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · nucleo.py — la lógica de la simulación 3D, sin Gazebo (24-nov-2026). correr.py la usa y le pone la vista.

    python3 sim-gazebo/nucleo.py --prueba        # los 4 modos de localización sobre el turno, con ArUco geométrico

QUÉ SIMULA. El equipo ejecuta el turno de sim/sim_datos.json (rutas v4, 4 pedidos) con un SEGUIDOR que corrige con
lo que cree que es su pose. Lo que cree sale del estimador, según dos llaves:

    odometría  on/off   el EKF predice con lo que lee el bus (0x188 velocidad, 0x184 ángulo). Off: predice con el mando
    ArUco      on/off   el EKF corrige con las marcas que ven las dos cámaras (A2)
    las dos off         lazo abierto: el equipo hace el plan «a ciegas», con el mando del plan y nada más

LA PLANTA (el equipo de verdad) no hace exactamente lo que se le manda. Dos clases de error:
    · los que la odometría VE (actuador): la marcha da el 92 % de lo mandado (batería, carga) y tarda 0.3 s; la rueda
      gira a 50 °/s como mucho (medido el 23-nov) y el lazo se queda a ±0.5° del objetivo
    · los que la odometría NO ve (sensor): el 0x184 lee la rueda 0.6° corrida (el centro se marcó a ojo) y el 0x188 lee
      la velocidad 1.5 % de más (la escala se sacó de 3.19 m con flexómetro)
    Sin localización se acumulan los dos; con odometría, solo los de sensor; con ArUco, el EKF además estima el
    sesgo y la escala (ekf.py lo hace) y los corrige.
La cinemática es la de percepcion/odometria.py: entre ejes 1.688, motriz corrida 0.325, ds de la rueda motriz.
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, 'percepcion'))
from odometria import E, WB, avanzar_rueda                          # noqa: E402
from ekf import EKF, R_pose, envolver, marca_vista_desde, pose_desde_marca   # noqa: E402

DATOS = os.path.join(RAIZ, 'sim', 'sim_datos.json')
DT = 0.02                                 # el SYNC del bus, 50 Hz

# ── la planta: lo que el equipo hace de verdad (SUPUESTOS, salvo W_RUEDA) ─────────────────────────────────────
K_MOTOR = 0.92            # la marcha real / la mandada (la odometría lo ve)
TAU_V = 0.30              # s
W_RUEDA = math.radians(50.0)   # medido, teleop del 23-nov
BANDA = math.radians(0.5)      # el lazo del timón para a ±0.5° del objetivo
SESGO_ANG = math.radians(0.6)  # el 0x184 lee la rueda 0.6° de más (la odometría NO lo ve)
ESCALA_VEL = 1.015             # el 0x188 lee 1.5 % de más (la odometría NO lo ve)
RUIDO_V = 0.01                 # 1 % de la velocidad
RUIDO_ANG = math.radians(0.2)

# ── el seguidor ───────────────────────────────────────────────────────────────────────────────────────────────
K_TH, K_LAT, K_LON, K_ROT = 1.0, 1.5, 1.0, 1.0
D_FB_MAX = math.radians(20)
V_FB_MAX = 0.20
GIROS = ('GIRO', 'DESGIRA', 'VUELTA')
DESPLAZADOR = 0.12        # ±0.12 m (CLAUDE.md, la ficha)
REQ_LAT = 0.045           # ±4.5 cm lateral al llegar (analisis/aruco_precision.py)
EN_EL_CUBO = ('APROXIMA', 'EXTIENDE', 'TOMA', 'INCLINA', 'NIVELA', 'DEPOSITA', 'RETRAE', 'RETROCEDE')

# ── las cámaras (montaje A2) para el ArUco geométrico (sin Gazebo) ────────────────────────────────────────────
HFOV = math.radians(54.3)
FX = 320 / math.tan(HFOV / 2)            # 623.4 px
L_MARCA = 0.15
PX_MIN = 20.0
ANG_MAX = math.radians(60)


def cargar(ruta=DATOS):
    with open(ruta, encoding='utf-8') as fh:
        return json.load(fh)


def interp_ang(a, b, f):
    return a + envolver(b - a) * f


class Plan:
    """El turno: muestras S (t, x, y, θ, δ, sentido, v rueda, etapa, cargado) y V (t, h, ext, ibc, etapa, inc)."""

    def __init__(self, D):
        self.D = D
        S = D['S']
        self.t = np.array([s[0] for s in S])
        self.S = S
        self.V = D['V']
        self.tv = np.array([v[0] for v in self.V])
        self.T_FIN = float(self.t[-1])

    def ref(self, t):
        i = int(np.clip(np.searchsorted(self.t, t, side='right') - 1, 0, len(self.S) - 1))
        a, b = self.S[i], self.S[min(i + 1, len(self.S) - 1)]
        f = 0.0 if b[0] <= a[0] else min(1.0, max(0.0, (t - a[0]) / (b[0] - a[0])))
        return dict(x=a[1] + (b[1] - a[1]) * f, y=a[2] + (b[2] - a[2]) * f, th=interp_ang(a[3], b[3], f),
                    d=a[4] + (b[4] - a[4]) * f, v=a[6] + (b[6] - a[6]) * f, sg=a[5], etapa=a[7], c=bool(a[8]))

    def vert(self, t):
        """Altura de uñas, pantógrafo, qué llevan, etapa e inclinación (°), como la página."""
        j = int(np.clip(np.searchsorted(self.tv, t, side='right') - 1, 0, len(self.V) - 1))
        p, q = self.V[j], self.V[min(j + 1, len(self.V) - 1)]
        g = 1.0 if q[0] <= p[0] else min(1.0, max(0.0, (t - p[0]) / (q[0] - p[0])))
        inc_p = p[5] if len(p) > 5 else 0.0
        inc_q = q[5] if len(q) > 5 else 0.0
        return dict(h=p[1] + (q[1] - p[1]) * g, ext=p[2] + (q[2] - p[2]) * g, ibc=p[3], etapa=p[4],
                    inc=inc_p + (inc_q - inc_p) * g)


class Planta:
    """El equipo de verdad: la marcha con retardo y ganancia, la rueda con límite de 50 °/s y el lazo con banda, y
    los dos sensores con su error. Devuelve lo que lee el bus."""

    def __init__(self, pose, rng):
        self.q = tuple(pose)
        self.d_med = 0.0                  # lo que lee el 0x184 (el lazo cierra sobre esto)
        self.v = 0.0
        self.rng = rng

    @property
    def d(self):                          # la rueda de verdad
        return self.d_med - SESGO_ANG

    def paso(self, v_cmd, d_cmd, dt=DT):
        err = d_cmd - self.d_med
        if abs(err) > BANDA:
            self.d_med += max(-W_RUEDA * dt, min(W_RUEDA * dt, err))
        self.v += (K_MOTOR * v_cmd - self.v) * min(1.0, dt / TAU_V)
        self.q = avanzar_rueda(self.q, self.v, self.d, dt)
        v_med = ESCALA_VEL * self.v * (1 + RUIDO_V * self.rng.standard_normal()) if abs(self.v) > 1e-4 else 0.0
        d_med = self.d_med + RUIDO_ANG * self.rng.standard_normal()
        return v_med, d_med


class Estimador:
    """El EKF de percepcion/ekf.py (rueda=True, motriz corrida). Las dos llaves deciden con qué predice y si corrige."""

    def __init__(self, pose, odo=True, aruco=True):
        self.odo, self.aruco = odo, aruco
        self.ekf = EKF(np.array(pose, float), np.diag([0.02, 0.02, math.radians(1.0)]) ** 2, rueda=True)
        self.n_marcas = 0

    @property
    def activo(self):
        return self.odo or self.aruco

    def paso(self, v_med, d_med, v_cmd, d_cmd, dt=DT):
        if self.odo:
            self.ekf.predict(v_med, d_med, dt)
        else:
            self.ekf.predict(v_cmd, d_cmd, dt)          # sin odometría: lo que se mandó

    def marca(self, z, R):
        if self.aruco:
            antes = self.ekf.rechazadas
            self.ekf.update_aruco(np.asarray(z, float), R)
            self.n_marcas += self.ekf.rechazadas == antes

    @property
    def pose(self):
        return tuple(self.ekf.pose)


class Ejecutor:
    """Ejecuta el plan como lo haría el equipo: los tramos con marcha se siguen POR DISTANCIA (avanza el plan lo que
    avanzó la rueda, medido o mandado), no por reloj; al final de cada tramo, si cree que no llegó, se arrima
    despacio hasta quedar a 1 cm / 0.3° (con lo que cree, no con la verdad); las etapas quietas (girar la rueda,
    elevar, extender…) van por reloj. Sin localización no hay arrime: el plan se hace a ciegas."""

    V_MIN = 0.05                  # m/s: para arrancar un tramo (el plan arranca en 0)
    V_ARRIME = 0.05
    V_ARRIME_MAX = 0.30
    TOL_LON, TOL_TH = 0.01, math.radians(0.3)
    T_ARRIME = 8.0                # s como mucho arrimándose

    def __init__(self, plan):
        self.p = plan
        S = plan.S
        n = len(S)
        self.mov = np.array([S[i][5] != 0 for i in range(n)])
        s = np.zeros(n)
        for i in range(n - 1):
            ds = 0.0
            if self.mov[i]:
                ds = abs(S[i][6] + S[i + 1][6]) / 2 * (S[i + 1][0] - S[i][0])
                if ds < 1e-6:
                    # tramo de una sola primitiva: el plan guarda v = 0 en las dos puntas (sim/exportar.perfil).
                    # El largo de rueda sale de la geometría: con giro, |Δθ|·WB/|sin δ|; si no, cuerda / |cos δ − e/WB·sin δ|
                    d0, dth = S[i][4], abs(envolver(S[i + 1][3] - S[i][3]))
                    cuerda = math.hypot(S[i + 1][1] - S[i][1], S[i + 1][2] - S[i][2])
                    if dth > 1e-3 and abs(math.sin(d0)) > 0.05:
                        ds = dth * WB / abs(math.sin(d0))
                    else:
                        ds = cuerda / max(0.05, abs(math.cos(d0) - E / WB * math.sin(d0)))
            s[i + 1] = s[i] + ds
        self.s = s
        # el timón de cada tramo con marcha, de la geometría (Δθ = −ds·sin δ / WB): en RECTA/TRANSITO el δ guardado
        # es la rueda ATRASADA que dibuja la página (sim/exportar.py), no el timón de la ruta
        self.d_ff = np.array([S[i][4] for i in range(n)], float)
        for i in range(n - 1):
            if self.mov[i] and S[i][7] in ('RECTA', 'TRANSITO'):
                ds = s[i + 1] - s[i]
                if ds > 1e-6:
                    dth = envolver(S[i + 1][3] - S[i][3])
                    sg = 1.0 if S[i][5] > 0 else -1.0
                    self.d_ff[i] = math.asin(max(-1.0, min(1.0, -dth * WB / (sg * ds))))
        self.i, self.tau, self.s_hecho = 0, 0.0, 0.0
        self.arrimando, self.t_arrime = None, 0.0
        self.fin = False
        self.desplazador = 0.0         # m, + a la izquierda del equipo (±0.12, VDI): corrige el lateral al llegar

    def S_t(self):
        """Por dónde va del plan, en segundos de plan."""
        return self.p.S[min(self.i, len(self.p.S) - 1)][0]

    def _ref_en(self, i, f):
        a, b = self.p.S[i], self.p.S[min(i + 1, len(self.p.S) - 1)]
        return dict(x=a[1] + (b[1] - a[1]) * f, y=a[2] + (b[2] - a[2]) * f, th=interp_ang(a[3], b[3], f),
                    d=a[4] + (b[4] - a[4]) * f, v=a[6] + (b[6] - a[6]) * f, sg=a[5], etapa=a[7], c=bool(a[8]),
                    t=a[0] + (b[0] - a[0]) * f)

    def mando(self, est, ds_rueda, dt, d_rueda=None):
        """est: la pose que cree (None = a ciegas); ds_rueda: lo que avanzó la rueda en este paso (medido o
        mandado); d_rueda: el ángulo que lee el 0x184 (None sin odometría). Devuelve (v, δ, ref)."""
        self.d_rueda = d_rueda
        S, n = self.p.S, len(self.p.S)
        if self.i >= n - 1:
            self.fin = True
            r = self._ref_en(n - 1, 0.0)
            return 0.0, r['d'], r
        if self.arrimando is not None:
            return self._arrimar(est, dt)
        a, b = S[self.i], S[self.i + 1]
        if not self.mov[self.i]:                                     # etapa quieta o rueda girando: por reloj
            if self.tau == 0.0:
                self._desplazar(est, S[self.i][7])
            self.tau += dt
            f = min(1.0, self.tau / max(1e-6, b[0] - a[0]))
            r = self._ref_en(self.i, f)
            if self.tau >= b[0] - a[0]:
                self.i, self.tau = self.i + 1, 0.0
                self._entrar(est)
            return 0.0, r['d'], r
        # tramo con marcha: por distancia
        self.s_hecho += abs(ds_rueda)
        while self.i < n - 1 and self.mov[self.i] and self.s[self.i + 1] - self.s[self.i] <= self.s_hecho:
            self.s_hecho -= self.s[self.i + 1] - self.s[self.i]
            self.i += 1
        if self.i >= n - 1 or not self.mov[self.i]:
            self.s_hecho = 0.0
            ultimo = self.i
            self._entrar(est, fin_tramo=ultimo)
            r = self._ref_en(min(self.i, n - 1), 0.0)
            return 0.0, r['d'], r
        a = S[self.i]
        largo = self.s[self.i + 1] - self.s[self.i]
        f = 0.0 if largo <= 0 else min(1.0, self.s_hecho / largo)
        r = self._ref_en(self.i, f)
        r['d'] = self.d_ff[self.i]
        sg = 1.0 if a[5] > 0 else -1.0
        v = sg * max(abs(r['v']), self.V_MIN)
        v, d, r = self._corregir(est, v, r['d'], r)
        # como el operador: si la rueda va atrasada respecto de lo que se pide, se frena hasta que llegue (el plan
        # salta de timón en los cambios de carril; a 1.5 m/s la rueda tarda ~0.6 s en llegar y el equipo se va)
        if self.d_rueda is not None:
            atraso = abs(d - self.d_rueda)
            v *= max(0.1, 1.0 - atraso / math.radians(20))
        return v, d, r

    def _desplazar(self, est, etapa):
        """El desplazador: al empezar a extender, corre las uñas lo que cree que está corrido de lado respecto del hueco
        (con lo que cree); vuelve al centro al bajar."""
        if etapa == 'EXTIENDE' and est is not None:
            r = self._ref_en(self.i, 0.0)
            ex, ey = est[0] - r['x'], est[1] - r['y']
            e_lat = -math.sin(r['th']) * ex + math.cos(r['th']) * ey      # + = el equipo está a la izquierda del hueco
            self.desplazador = max(-DESPLAZADOR, min(DESPLAZADOR, -e_lat))
        elif etapa in ('BAJA', 'DESGIRA', 'LIBRE'):
            self.desplazador = 0.0

    def _entrar(self, est, fin_tramo=None):
        """Al terminar un tramo con marcha: ¿llegó? (según lo que cree)."""
        if fin_tramo is None or est is None:
            return
        self.arrimando, self.t_arrime = fin_tramo, 0.0

    def _arrimar(self, est, dt):
        k = self.arrimando
        r = self._ref_en(k, 0.0)
        r['etapa'] = self.p.S[k - 1][7] if k > 0 else r['etapa']      # sigue en la etapa del tramo (p. ej. RETROCEDE)
        d = self.d_ff[k - 1] if k > 0 else self.d_ff[k]               # el timón con que terminó el tramo
        self.t_arrime += dt
        c, s = math.cos(r['th']), math.sin(r['th'])
        ex, ey = est[0] - r['x'], est[1] - r['y']
        e_lon, e_th = c * ex + s * ey, envolver(est[2] - r['th'])
        giro = abs(math.sin(d)) > 0.5
        listo = (abs(e_th) < self.TOL_TH) if giro else (abs(e_lon) < self.TOL_LON)
        if listo or self.t_arrime > self.T_ARRIME:
            self.arrimando = None
            return 0.0, d, r
        if giro:                                                      # dθ = −ds·sin δ / WB
            v = max(-self.V_ARRIME, min(self.V_ARRIME, K_ROT * WB * e_th / math.sin(d)))
        else:
            v = max(-self.V_ARRIME_MAX, min(self.V_ARRIME_MAX, -K_LON * e_lon * (1 if math.cos(d) > 0 else -1)))
            v = math.copysign(max(abs(v), 0.02), v)
            return self._corregir(est, v, d, r)
        return v, d, r

    def _corregir(self, est, v, d, r):
        if est is None:
            return v, d, r
        ex, ey = est[0] - r['x'], est[1] - r['y']
        c, s = math.cos(r['th']), math.sin(r['th'])
        e_lat = -s * ex + c * ey
        e_th = envolver(est[2] - r['th'])
        if abs(r['d']) < math.radians(60):
            sg = 1.0 if v > 0 else -1.0
            d += max(-D_FB_MAX, min(D_FB_MAX, K_TH * (sg * e_th + K_LAT * e_lat)))
        return v, d, r


# ── margen contra los racks (la regla del Mundo v2/v3, como sim/exportar.holguras) ───────────────────────────
class Margen:
    def __init__(self, D, rec=0.06):
        G, EQ = D['geo'], D['equipo']
        self.G, self.rec = G, rec
        self.HALF = G['PASILLO'] / 2
        self.bahias = np.array(G['bahias'])
        self.puntos, self.frente = {}, {}
        for nombre in ('vacio', 'cargado'):
            piezas = EQ['piezas'][nombre]
            pts, fr = [], []
            for k, p in enumerate(piezas):
                p = np.array(p)
                if k > 0:                                       # uñas y cubo: rectángulos, se densifican los lados
                    q = []
                    for a, b in zip(p, np.roll(p, -1, axis=0)):
                        q += [a + (b - a) * u for u in np.linspace(0, 1, 12, endpoint=False)]
                    p = np.array(q)
                pts.append(p)
                fr.append(np.full(len(p), k > 0))
            self.puntos[nombre], self.frente[nombre] = np.vstack(pts), np.concatenate(fr)

    def __call__(self, pose, cargado, etapa):
        G, HALF, rec = self.G, self.HALF, self.rec
        P = self.puntos['cargado' if cargado else 'vacio']
        c, s = math.cos(pose[2]), math.sin(pose[2])
        X = pose[0] + P[:, 0] * c - P[:, 1] * s
        Y = pose[1] + P[:, 0] * s + P[:, 1] * c
        if etapa in EN_EL_CUBO:
            fr = self.frente['cargado' if cargado else 'vacio']
            X, Y = X[~fr], Y[~fr]
        luz = ((X[:, None] >= self.bahias[:, 0]) & (X[:, None] <= self.bahias[:, 1])).any(axis=1)
        sup = np.where(luz, HALF + rec, HALF)
        inf = np.where(luz, -(HALF + rec), -HALF)
        for z in (G.get('zona_descarga'), G.get('zona_carga')):
            if z:
                dentro = (X >= z['x0']) & (X <= z['x1'])
                if z['lado'] == 'R':
                    inf = np.where(dentro, -(HALF + G['FONDO_RACK'] + rec), inf)
                else:
                    sup = np.where(dentro, HALF + G['FONDO_RACK'] + rec, sup)
        h = np.minimum(sup - Y, Y - inf)
        h = np.minimum(h, G['X_FONDO'] - X)
        h = np.minimum(h, X + G['ZONA_ATRAS'])
        j = int(np.argmin(h))
        return float(h[j]), float(X[j]), float(Y[j])


# ── las marcas y el ArUco geométrico (para probar sin Gazebo) ─────────────────────────────────────────────────
def marcas(D):
    """{id: (x, y, θ)}: θ es hacia dónde mira la marca (al pasillo)."""
    return {m['id']: (m['x'], m['y'], -math.pi / 2 if m['y'] > 0 else math.pi / 2) for m in D['marcas']}


def montajes(D):
    return {('cam_lateral', 'cam_trasera')[k]: (c['cx'], c['cy'], c['yaw']) for k, c in enumerate(D['camaras'])}


def R_medida(dist):
    """Ruido de una lectura (dist, lateral, yaw), como sube con la distancia. Ajustado con la prueba de visión en Gazebo
    (24-nov: con imágenes renderizadas, error de pose mediana 1.9 cm, máx 5.9; rumbo 0.2°): queda del lado pesimista."""
    return np.diag([(0.005 + 0.006 * dist) ** 2, (0.003 + 0.002 * dist) ** 2, math.radians(0.5 + 0.3 * dist) ** 2])


def medicion(marca, dist, lateral, yaw, montaje):
    """De lo que ve una cámara a una pose del equipo, con su covarianza."""
    z = pose_desde_marca(marca, dist, lateral, yaw, montaje)
    R = R_pose(marca, dist, lateral, yaw, montaje, R_medida(dist))
    return z, R


def aruco_geometrico(pose, M, cams, rng):
    """Lo que verían las cámaras desde la pose VERDADERA, con ruido: campo de visión, tamaño en px e incidencia."""
    out = []
    for nom, mon in cams.items():
        for mid, mk in M.items():
            dist, lat, yaw = marca_vista_desde(pose, mk, mon)
            if dist <= 0.2 or abs(math.atan2(lat, dist)) > HFOV / 2 - 0.02 or abs(yaw) > ANG_MAX:
                continue
            if FX * L_MARCA * math.cos(yaw) / dist < PX_MIN:
                continue
            Rm = R_medida(dist)
            ruido = rng.multivariate_normal(np.zeros(3), Rm)
            out.append((nom, mid) + medicion(mk, dist + ruido[0], lat + ruido[1], yaw + ruido[2], mon))
    return out


# ── una corrida completa sin vista (la prueba) ────────────────────────────────────────────────────────────────
class Corrida:
    def __init__(self, D, odo, aruco, semilla=0):
        self.D, self.plan = D, Plan(D)
        self.rng = np.random.default_rng(semilla)
        p0 = self.plan.ref(0.0)
        self.planta = Planta((p0['x'], p0['y'], p0['th']), self.rng)
        self.est = Estimador((p0['x'], p0['y'], p0['th']), odo, aruco)
        self.ejec = Ejecutor(self.plan)
        self.margen = Margen(D)
        self.t = 0.0
        self.M, self.cams = marcas(D), montajes(D)
        self.ds = 0.0
        self.d_med = 0.0
        self.ult = (0.0, 0.0)

    def paso(self, dt=DT):
        usa = self.est.pose if self.est.activo else None
        v_cmd, d_cmd, r = self.ejec.mando(usa, self.ds, dt, self.d_med if self.est.odo else None)
        v_med, d_med = self.planta.paso(v_cmd, d_cmd, dt)
        self.est.paso(v_med, d_med, v_cmd, d_cmd, dt)
        self.ds = (v_med if self.est.odo else v_cmd) * dt          # lo que cree que avanzó la rueda
        self.d_med = d_med
        self.ult = (v_cmd, d_cmd)
        self.t += dt
        return r

    def llegada(self, r):
        """Al empezar a extender: lateral de las UÑAS respecto del hueco (después del desplazador), distancia de la
        punta al cubo respecto de lo planeado, y rumbo. Con la pose verdadera."""
        q = self.planta.q
        ex, ey = q[0] - r['x'], q[1] - r['y']
        c, s = math.cos(r['th']), math.sin(r['th'])
        lat = -s * ex + c * ey + self.ejec.desplazador
        lon = c * ex + s * ey
        return abs(lat), abs(lon), abs(math.degrees(envolver(q[2] - r['th'])))

    def errores(self, r):
        q, e = self.planta.q, self.est.pose if self.est.activo else (r['x'], r['y'], r['th'])
        return math.hypot(q[0] - r['x'], q[1] - r['y']), math.hypot(q[0] - e[0], q[1] - e[1])


def prueba(hasta=None, semillas=(0, 1, 2)):
    D = cargar()
    hasta = hasta or Plan(D).T_FIN
    print(f"turno de {hasta:.0f} s · planta: marcha ×{K_MOTOR}, rueda {math.degrees(W_RUEDA):.0f} °/s ±{math.degrees(BANDA)}°, "
          f"0x184 corrido {math.degrees(SESGO_ANG)}°, 0x188 ×{ESCALA_VEL}")
    filas = {}
    for odo, aruco, nombre in ((False, False, 'ninguno (lazo abierto)'), (True, False, 'solo odometría'),
                               (False, True, 'solo ArUco'), (True, True, 'odometría + ArUco')):
        peor_plan, peor_est, choques, llegadas, durs = [], [], [], [], []
        for sem in semillas:
            c = Corrida(D, odo, aruco, sem)
            m_min, e_plan, e_est, choque, etapa_ant, lleg = 9.0, 0.0, 0.0, 0, None, []
            k = 0
            while c.ejec.S_t() < hasta and not c.ejec.fin and c.t < 3 * hasta:
                r = c.paso()
                k += 1
                if aruco and k % 5 == 0:                    # 10 Hz
                    for nom, mid, z, R in aruco_geometrico(c.planta.q, c.M, c.cams, c.rng):
                        c.est.marca(z, R)
                ep, ee = c.errores(r)
                e_plan, e_est = max(e_plan, ep), max(e_est, ee)
                if k % 5 == 0:
                    m = c.margen(c.planta.q, r['c'], r['etapa'])[0]
                    m_min = min(m_min, m)
                    choque += m < 0
                if r['etapa'] == 'EXTIENDE' and etapa_ant != 'EXTIENDE':
                    lleg.append(c.llegada(r))
                etapa_ant = r['etapa']
            peor_plan.append(e_plan); peor_est.append(e_est); choques.append(choque); llegadas += lleg
            durs.append(c.t)
        L = np.array(llegadas)
        lleg = L[:, 0] * 100
        filas[nombre] = dict(llegada_max_cm=round(float(lleg.max()), 1), llegada_med_cm=round(float(np.median(lleg)), 1),
                             fuera_45=int((L[:, 0] > REQ_LAT).sum()), n_llegadas=len(L),
                             punta_max_cm=round(float(L[:, 1].max() * 100), 1), rumbo_max=round(float(L[:, 2].max()), 2),
                             desvio_max_cm=round(100 * max(peor_plan), 1), cree_vs_real_max_cm=round(100 * max(peor_est), 1),
                             instantes_en_choque=int(sum(choques)), duracion_s=round(float(np.mean(durs)), 1))
        print(f"  {nombre:24s} uñas vs hueco, lateral: máx {filas[nombre]['llegada_max_cm']:6.1f} cm, mediana "
              f"{filas[nombre]['llegada_med_cm']:5.1f}, fuera de ±4.5: {filas[nombre]['fuera_45']}/{filas[nombre]['n_llegadas']} · "
              f"punta máx {filas[nombre]['punta_max_cm']} cm · rumbo máx {filas[nombre]['rumbo_max']}° · desvío máx {filas[nombre]['desvio_max_cm']:6.1f} cm · "
              f"cree vs real máx {filas[nombre]['cree_vs_real_max_cm']:6.1f} cm · instantes en choque {filas[nombre]['instantes_en_choque']} · "
              f"{filas[nombre]['duracion_s']} s",
              flush=True)
    return filas


if __name__ == '__main__':
    if '--prueba' in sys.argv:
        h = None
        if '--hasta' in sys.argv:
            h = float(sys.argv[sys.argv.index('--hasta') + 1])
        prueba(h)
    else:
        print(__doc__)
