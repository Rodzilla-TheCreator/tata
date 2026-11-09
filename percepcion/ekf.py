# ─────────────────────────────────────────────────────────────────────────────
# EKF de localización — odometría (predicción) + ArUco (corrección absoluta)
#
# Pose: la del EJE DE RUEDAS DE CARGA en el marco del pasillo, [x, y, θ] (x a lo largo, y
#   lateral, θ = 0 hacia +x). Mismo marco que los simuladores del repo. Es lo que se lee de
#   afuera: ekf.pose y ekf.P_pose.
#
# Estado interno: [x, y, θ, b, s]
#   b  sesgo del ángulo de dirección, rad        δ_real = δ_medido − b
#   s  escala de la velocidad de tracción         v_real = s · v_medida
#   POR QUÉ: la primera versión (02-nov) tenía solo [x, y, θ] y FALLÓ la prueba de oclusión:
#   un sesgo de dirección hace derivar el rumbo LINEALMENTE, y un ruido de proceso aleatorio
#   solo crece como la raíz del tiempo. Tras 5 s sin marcas el filtro decía σ_θ = 0.23° con un
#   error real de 1.75°, rechazaba toda marca que reaparecía y no se volvía a enganchar nunca.
#   Estimando b y s mientras ve marcas, la odometría llega corregida a la oclusión.
#
# predict(v, δ, dt): propaga con odometria.avanzar (la cinemática del planificador), o con
#   avanzar_rueda si rueda=True (09-nov: v de la rueda motriz, aguanta el timón a 90° del giro v3). Ruido de
#   proceso Q = G·M·Gᵀ desde la incertidumbre de las entradas, más una deriva lenta de b y s.
#
# update_aruco(pose, R): corrige con una pose absoluta (H = [I₃ 0]). Ángulo envuelto.
#   Compuerta de Mahalanobis (χ² 3 gl, 99 %) contra marcas mal identificadas o reflejos.
#   Red de seguridad: si se rechazan RECHAZOS_PARA_REABRIR seguidas, el filtro admite que
#   está perdido, reabre la covarianza de la pose y vuelve a aceptar.
# ─────────────────────────────────────────────────────────────────────────────
import math

import numpy as np

from odometria import WB, avanzar, avanzar_rueda

CHI2_3_99 = 11.345          # χ² con 3 grados de libertad al 99 %
RECHAZOS_PARA_REABRIR = 10  # ≈ 0.5 s de marcas que contradicen al filtro, con dos cámaras a 10 Hz


def envolver(a):
    """Ángulo a (−π, π]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class EKF:
    def __init__(self, pose0, P0, sigma_v_rel=0.01, sigma_v_abs=0.01, sigma_delta=math.radians(0.5),
                 sigma_b0=math.radians(1.0), sigma_s0=0.05,
                 deriva_b=math.radians(0.01), deriva_s=1e-4, rueda=False):
        """
        pose0, P0     pose inicial [x, y, θ] y su covarianza 3×3
        sigma_v_*     ruido aleatorio de la velocidad (relativo a v, y piso en m/s)
        sigma_delta   ruido aleatorio del ángulo de dirección, rad
        sigma_b0/s0   duda inicial sobre el sesgo de dirección (rad) y la escala de velocidad
        deriva_b/s    cuánto pueden cambiar b y s por segundo (raíz): casi constantes
        rueda         False (02-nov, validado): v es la velocidad del EJE DE CARGA y se integra con
                      tan δ. True (09-nov): v es la de la RUEDA MOTRIZ, que es lo que mide el encoder,
                      y se integra con cos δ / sin δ: aguanta δ = 90° (el giro v3, rotación sobre el
                      eje de carga), donde tan δ es infinita. s es la escala de esa velocidad.
        """
        self.rueda = rueda
        self.x = np.r_[np.asarray(pose0, float), 0.0, 1.0]
        self.P = np.zeros((5, 5))
        self.P[:3, :3] = P0
        self.P[3, 3], self.P[4, 4] = sigma_b0 ** 2, sigma_s0 ** 2
        self.sv_rel, self.sv_abs, self.sd = sigma_v_rel, sigma_v_abs, sigma_delta
        self.qb, self.qs = deriva_b ** 2, deriva_s ** 2
        self.rechazadas = 0
        self.seguidas = 0
        self.reaperturas = 0

    @property
    def pose(self):
        return self.x[:3].copy()

    @property
    def P_pose(self):
        return self.P[:3, :3].copy()

    def predict(self, v, delta, dt):
        x, y, th, b, s = self.x
        de = delta - b
        dsw = s * v * dt                                 # lo que recorre el punto de la velocidad medida
        if self.rueda:                                   # v de la rueda motriz (v3, aguanta δ = 90°)
            cd, sd = math.cos(de), math.sin(de)
            ds, dth = dsw * cd, -(dsw / WB) * sd
            dds_dsw, ddth_dsw = cd, -sd / WB             # ∂(ds, dθ)/∂ds_rueda
            dds_dde, ddth_dde = -dsw * sd, -(dsw / WB) * cd
        else:                                            # v del eje de carga (02-nov, con tan δ)
            t = math.tan(de)
            ds, dth = dsw, -(dsw / WB) * t
            dds_dsw, ddth_dsw = 1.0, -t / WB
            dds_dde, ddth_dde = 0.0, -(ds / WB) * (1 + t * t)
        thm = th + 0.5 * dth
        c, sn = math.cos(thm), math.sin(thm)

        def fila(dds, ddth):          # cómo cambia (x', y', θ') si ds y dθ cambian en (dds, ddth)
            return np.array([dds * c - ds * sn * 0.5 * ddth,
                             dds * sn + ds * c * 0.5 * ddth,
                             ddth])

        F = np.eye(5)
        F[0, 2], F[1, 2] = -ds * sn, ds * c
        F[:3, 3] = fila(-dds_dde, -ddth_dde)                    # ∂/∂b  (δ_real = δ − b)
        F[:3, 4] = fila(dds_dsw * v * dt, ddth_dsw * v * dt)    # ∂/∂s
        G = np.zeros((5, 2))
        G[:3, 0] = fila(dds_dsw * s * dt, ddth_dsw * s * dt)    # ∂/∂v medida
        G[:3, 1] = fila(dds_dde, ddth_dde)                      # ∂/∂δ medida
        moviendo = abs(v) > 1e-3
        sv = self.sv_rel * abs(v) + self.sv_abs if moviendo else 0.0
        M = np.diag([sv ** 2, self.sd ** 2 if moviendo else 0.0])
        Q = G @ M @ G.T
        Q[3, 3] += self.qb * dt
        Q[4, 4] += self.qs * dt

        nx, ny, nth = (avanzar_rueda if self.rueda else avanzar)((x, y, th), s * v, de, dt)
        self.x = np.array([nx, ny, envolver(nth), b, s])
        self.P = F @ self.P @ F.T + Q
        self.ultimo = (F, G)                             # para la prueba de jacobianos (prueba_ekf_rueda.py)

    def update_aruco(self, pose_medida, R):
        H = np.zeros((3, 5)); H[:, :3] = np.eye(3)
        nu = np.asarray(pose_medida, float) - self.x[:3]
        nu[2] = envolver(nu[2])
        S = H @ self.P @ H.T + R
        d2 = float(nu @ np.linalg.solve(S, nu))
        if d2 > CHI2_3_99:
            self.rechazadas += 1
            self.seguidas += 1
            if self.seguidas >= RECHAZOS_PARA_REABRIR:
                # muchas marcas distintas contradicen al filtro: el perdido es el filtro, no ellas
                self.P[:3, :3] += np.diag([0.5 ** 2, 0.5 ** 2, math.radians(10) ** 2])
                self.seguidas = 0
                self.reaperturas += 1
            return False
        self.seguidas = 0
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ nu
        self.x[2] = envolver(self.x[2])
        I_KH = np.eye(5) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T          # forma de Joseph: P simétrica y positiva
        return True


# ─── de una detección ArUco a la pose del equipo ─────────────────────────────
# Lo que entrega detector_aruco.py por marca: id, dist_m (hacia adelante de la cámara),
# lateral_m (a la DERECHA de la cámara, convención OpenCV) y yaw_deg (giro de la marca
# respecto de mirarla de frente). Con el mapa (id → x, y, θ de la normal de la marca, que
# apunta hacia el pasillo) y el montaje de la cámara en el equipo se deduce la pose.
#
# Verificado contra marca real (03-nov-2026, C920, calib.npz, ver percepcion/LEEME.md):
# lateral SÍ coincidía (+derecha, −izquierda). yaw NO: la fórmula daba +α girando la marca de
# forma que su borde derecho (visto desde la cámara) se aleja (bisagra en el borde izquierdo),
# y el detector real, para ese mismo giro, da −42.4°. Signo de yaw CORREGIDO acá (cam_th usa
# +yaw, no −yaw; yaw queda π + cam_th − mth, no mth − π − cam_th). Round-trip interno seguía
# pasando con el signo viejo —por eso sim_sintetico.py no lo agarró— porque pose_desde_marca y
# marca_vista_desde son álgebra inversa entre sí: cualquier convención consistente entre las dos
# pasa el synthetic aunque esté al revés respecto del detector real.

def _rot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def pose_desde_marca(marca, dist, lateral, yaw, montaje):
    """marca = (mx, my, mθ) en el pasillo; montaje = (cx, cy, cθ) de la cámara en el equipo
    (respecto del eje de carga). Devuelve la pose (x, y, θ) del equipo."""
    mx, my, mth = marca
    cx, cy, cth = montaje
    cam_th = mth - math.pi + yaw                       # yaw = 0 → la marca mira de frente a la cámara
    cam_p = np.array([mx, my]) - _rot(cam_th) @ np.array([dist, -lateral])
    th = cam_th - cth
    p = cam_p - _rot(th) @ np.array([cx, cy])
    return np.array([p[0], p[1], envolver(th)])


def marca_vista_desde(pose, marca, montaje):
    """Inversa de pose_desde_marca: qué (dist, lateral, yaw) ve la cámara (sin ruido)."""
    x, y, th = pose
    cx, cy, cth = montaje
    cam_th = th + cth
    cam_p = np.array([x, y]) + _rot(th) @ np.array([cx, cy])
    rel = _rot(-cam_th) @ (np.array(marca[:2]) - cam_p)
    dist, lateral = rel[0], -rel[1]
    yaw = envolver(math.pi + cam_th - marca[2])
    return dist, lateral, yaw


def R_pose(marca, dist, lateral, yaw, montaje, Rm, h=1e-6):
    """Covarianza de la pose deducida, propagando el ruido de medición Rm = diag(σ_dist²,
    σ_lat², σ_yaw²) por el Jacobiano numérico de pose_desde_marca. Importa: un error de yaw
    se multiplica por la distancia y mueve la posición (palanca)."""
    m0 = np.array([dist, lateral, yaw])
    f0 = pose_desde_marca(marca, *m0, montaje)
    J = np.zeros((3, 3))
    for i in range(3):
        m = m0.copy(); m[i] += h
        d = pose_desde_marca(marca, *m, montaje) - f0
        d[2] = envolver(d[2])
        J[:, i] = d / h
    return J @ Rm @ J.T


class ColocacionMarcas:
    """El error de colocación de una marca es el MISMO en cada vista: no es ruido blanco.

    Si se suma igual a cada detección, el filtro cuenta 20 vistas de una marca mal puesta como
    20 marcas independientes y se vuelve sobreconfiado (02-nov: 5.6σ de error lateral en la
    oclusión con σ 1 cm de colocación; 0.55σ con colocación perfecta). Regla: la k-ésima vista
    seguida de la misma marca carga k veces la varianza de colocación, así la información total
    sobre dónde está esa marca queda acotada. La cuenta se reinicia si la marca deja de verse.
    """

    def __init__(self, sigma, reinicio_s=2.0):
        self.var, self.reinicio = sigma ** 2, reinicio_s
        self.veces, self.ultima = {}, {}

    def R(self, id_marca, t):
        if t - self.ultima.get(id_marca, -1e9) > self.reinicio:
            self.veces[id_marca] = 0
        self.veces[id_marca] = self.veces.get(id_marca, 0) + 1
        self.ultima[id_marca] = t
        k = self.veces[id_marca]
        return np.diag([self.var * k, self.var * k, 0.0])
