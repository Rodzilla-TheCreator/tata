#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · correr.py — el turno del EDR18N2 en Gazebo, en 3D, con las llaves de localización (24-nov-2026).

    python3 sim-gazebo/correr.py                    # abre Gazebo (3D) y la consola: START, STOP, ODOMETRÍA, ARUCO
    python3 sim-gazebo/correr.py --sin-gui --modo ambos --hasta 100     # sin ventanas: corre y resume
    python3 sim-gazebo/correr.py --prueba-vision    # pone el equipo frente a marcas y compara lo que mide la cámara
    opciones: --no-lanzar (Gazebo ya abierto)  --aruco-geometrico (sin procesar imágenes: más liviano)
              --velocidad 2   --semilla 0

Qué hace: la lógica está en nucleo.py (el plan, la planta con sus errores, el EKF, el ejecutor). Esto la corre en
tiempo real, mueve los modelos en Gazebo (/world/pasillo/set_pose_vector), toma las imágenes de las dos cámaras
(montaje A2, 640×480, 54.3°), detecta ArUco con OpenCV (DICT_4X4_50, 15 cm), saca la pose de cada marca con
solvePnP y se la da al EKF. El fantasma azul es dónde CREE el equipo que está; el amarillo es dónde está.
Las llaves se pueden cambiar en plena corrida.
"""
import argparse
import math
import os
import queue
import subprocess
import sys
import threading
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import nucleo as N                                  # noqa: E402

MUNDO = os.path.join(AQUI, 'mundo', 'pasillo.sdf')
W_IMG, H_IMG = 640, 480
K_CAM = np.array([[N.FX, 0, W_IMG / 2], [0, N.FX, H_IMG / 2], [0, 0, 1]], float)
OBJ = np.array([[-1, 1, 0], [1, 1, 0], [1, -1, 0], [-1, -1, 0]], float) * N.L_MARCA / 2   # TL TR BR BL
HZ_POSES = 30.0


# ── visión: de una imagen a mediciones de pose ─────────────────────────────────────────────────────────────────
class Vision:
    def __init__(self, D):
        import cv2
        self.cv2 = cv2
        self.M = N.marcas(D)
        self.mon = N.montajes(D)
        self.det = {}
        self.dic = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    def _detector(self):
        t = threading.get_ident()
        if t not in self.det:
            p = self.cv2.aruco.DetectorParameters()
            p.cornerRefinementMethod = self.cv2.aruco.CORNER_REFINE_SUBPIX
            self.det[t] = self.cv2.aruco.ArucoDetector(self.dic, p)
        return self.det[t]

    def medir(self, cam, rgb):
        """[(id, z pose, R, dist, px)] de las marcas que ve esta cámara."""
        cv2 = self.cv2
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        esquinas, ids, _ = self._detector().detectMarkers(g)
        out = []
        if ids is None:
            return out
        for c, mid in zip(esquinas, ids.ravel()):
            mid = int(mid)
            if mid not in self.M:
                continue
            c = c.reshape(4, 2).astype(np.float64)
            px = float(np.mean([np.linalg.norm(c[k] - c[(k + 1) % 4]) for k in range(4)]))
            if px < N.PX_MIN:
                continue
            ok, rvec, tvec = cv2.solvePnP(OBJ, c, K_CAM, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            if not ok:
                continue
            R, _ = cv2.Rodrigues(rvec)
            n = R[:, 2]                                       # la normal de la marca, hacia la cámara
            dist, lat = float(tvec[2][0]), float(tvec[0][0])
            yaw = N.envolver(math.pi - math.atan2(-n[0], n[2]))
            if dist <= 0.2 or abs(yaw) > N.ANG_MAX:
                continue
            z, Rz = N.medicion(self.M[mid], dist, lat, yaw, self.mon[cam])
            out.append((mid, z, Rz, dist, px))
        return out


# ── Gazebo ─────────────────────────────────────────────────────────────────────────────────────────────────────
class Gazebo:
    def __init__(self, D, lanzar=True, headless=False):
        from gz.transport13 import Node
        from gz.msgs10.boolean_pb2 import Boolean
        from gz.msgs10.image_pb2 import Image
        from gz.msgs10.pose_v_pb2 import Pose_V
        self.Boolean, self.Image, self.Pose_V = Boolean, Image, Pose_V
        self.proc = None
        if not os.path.exists(MUNDO):
            import generar_mundo
            generar_mundo.main()
        if lanzar:
            cmd = ['gz', 'sim', '-r', MUNDO] if not headless else ['gz', 'sim', '-s', '-r', '--headless-rendering', MUNDO]
            self.proc = subprocess.Popen(cmd, cwd=os.path.dirname(MUNDO))
        self.node = Node()
        self.imgs = {}
        self.D = D
        EQ = D['equipo']
        self.a_mast, self.wb, self.e = EQ['a_mast'], EQ['wb'], EQ.get('e', 0.0)
        self.cubos_z = self._alturas_cubos(D)
        t0 = time.time()
        while time.time() - t0 < 120:                           # espera a que el mundo esté arriba
            ok, _ = self._poner([('edr', 0, 0, -20, 0, 0)])
            if ok:
                break
            time.sleep(1.0)
        else:
            raise RuntimeError('Gazebo no contesta en /world/pasillo/set_pose_vector')

    @staticmethod
    def _alturas_cubos(D):
        z = []
        alt = D['geo']['ALTURAS']
        for c in D['cubos']:
            zz = 0.0
            if c['tipo'] == 'rack':
                for p in D['pedidos']:
                    x0, x1 = D['geo']['bahias'][p['x_bahia'] - 1]
                    lado = 'L' if c['y'] > 0 else 'R'
                    if x0 <= c['x'] <= x1 and p['lado'] == lado:
                        zz = alt[p['nivel']][0]
            z.append(zz)
        return z

    def camaras(self, cb):
        for top in ('cam_lateral', 'cam_trasera'):
            def f(msg, top=top):
                a = np.frombuffer(msg.data, dtype=np.uint8)
                if a.size != msg.height * msg.width * 3:
                    return
                cb(top, a.reshape(msg.height, msg.width, 3))
            self.node.subscribe(self.Image, '/tata/' + top, f)

    def _poner(self, poses):
        req = self.Pose_V()
        for nombre, x, y, z, yaw, pitch in poses:
            p = req.pose.add()
            p.name = nombre
            p.position.x, p.position.y, p.position.z = float(x), float(y), float(z)
            cy, sy, cp, sp = math.cos(yaw / 2), math.sin(yaw / 2), math.cos(pitch / 2), math.sin(pitch / 2)
            p.orientation.w, p.orientation.x, p.orientation.y, p.orientation.z = cy * cp, -sy * sp, cy * sp, sy * cp
        try:
            ok, rep = self.node.request('/world/pasillo/set_pose_vector', req, self.Pose_V, self.Boolean, 500)
            return ok and rep.data, rep
        except Exception:
            return False, None

    def escena(self, q, d_rueda, vert, desplazador, fantasma, cubos):
        """q pose verdadera; vert = altura, pantógrafo, ibc, inclinación; fantasma = pose que cree (o None)."""
        x, y, th = q
        c, s = math.cos(th), math.sin(th)
        L = lambda a, b: (x + a * c - b * s, y + a * s + b * c)
        rx, ry = L(-self.wb, self.e)
        cx, cy = L(self.a_mast + vert['ext'], desplazador)
        pitch = -math.radians(vert['inc'])
        poses = [('edr', x, y, 0.0, th, 0.0), ('rueda', rx, ry, 0.0, th + d_rueda, 0.0),
                 ('carro', cx, cy, vert['h'], th, pitch)]
        if vert['ibc'] == 'uñas':
            # el cubo, de dorso a punta, apoyado sobre las uñas
            ox, oz = 0.60 * math.cos(pitch) + 0.036 * math.sin(pitch), -0.60 * math.sin(pitch) + 0.036 * math.cos(pitch)
            poses.append(('ibc_unas', cx + ox * c, cy + ox * s, vert['h'] + oz, th, pitch))
        else:
            poses.append(('ibc_unas', 0, 0, -10, 0, 0))
        if fantasma is not None:
            poses.append(('fantasma', fantasma[0], fantasma[1], 0.005, fantasma[2], 0.0))
        for k, pz in enumerate(cubos):
            poses.append((f'ibc_{k}',) + tuple(pz))
        self._poner(poses)

    def seguir(self):
        """Prende / apaga la cámara que persigue al equipo. Va por encima del eje del pasillo, 7 m detrás (hacia el
        principio) y a 8 m de alto, mirando al equipo: nunca queda metida en un rack. (El seguimiento de Gazebo,
        /gui/follow, rota con el equipo y al girar hacia una bahía mete la cámara en el rack de enfrente.)"""
        self.persigue = not getattr(self, 'persigue', False)
        self.t_cam = 0.0
        return self.persigue

    def camara(self, q):
        if not getattr(self, 'persigue', False) or time.time() - self.t_cam < 0.4:
            return
        self.t_cam = time.time()
        try:
            from gz.msgs10.gui_camera_pb2 import GUICamera
            x, y, _ = q
            cx, cy, cz = x - 7.0, 0.0, 8.0
            yaw = math.atan2(y - cy, x - cx)
            pitch = math.atan2(cz - 0.5, math.hypot(x - cx, y - cy))
            m = GUICamera()
            m.pose.position.x, m.pose.position.y, m.pose.position.z = cx, cy, cz
            qy, sy, qp, sp = math.cos(yaw / 2), math.sin(yaw / 2), math.cos(pitch / 2), math.sin(pitch / 2)
            m.pose.orientation.w, m.pose.orientation.x = qy * qp, -sy * sp
            m.pose.orientation.y, m.pose.orientation.z = qy * sp, sy * qp
            self.node.request('/gui/move_to/pose', m, GUICamera, self.Boolean, 200)
        except Exception:
            pass

    def cerrar(self):
        if self.proc:
            self.proc.terminate()


# ── la simulación en tiempo real ───────────────────────────────────────────────────────────────────────────────
class Sim:
    def __init__(self, D, gz, odo=True, aruco=True, geometrico=False, semilla=0):
        self.D, self.gz, self.geometrico = D, gz, geometrico
        self.semilla = semilla
        self.odo0, self.aruco0 = odo, aruco
        self.vision = Vision(D) if (gz and not geometrico) else None
        self.q_med = queue.Queue()
        self.vistas = {'cam_lateral': 0, 'cam_trasera': 0}
        self.ultimas = {}
        if gz and self.vision:
            gz.camaras(self._imagen)
        self.reiniciar()

    def reiniciar(self):
        odo = self.c.est.odo if hasattr(self, 'c') else self.odo0
        aruco = self.c.est.aruco if hasattr(self, 'c') else self.aruco0
        self.c = N.Corrida(self.D, odo, aruco, self.semilla)
        self.corriendo = False
        self.k = 0
        self.ultima_llegada = None
        self.m_min = 9.0
        self.ibc_prev = 'nada'
        self.cubos = []
        for k, cb in enumerate(self.D['cubos']):
            self.cubos.append(dict(x=cb['x'], y=cb['y'], th=cb['th'], z=self.gz.cubos_z[k] if self.gz else 0.0,
                                   t0=cb['t0'], t1=cb['t1'], tipo=cb['tipo']))
        self.t_pose = 0.0
        while not self.q_med.empty():
            self.q_med.get_nowait()

    def _imagen(self, cam, rgb):
        self.ultimas[cam] = (time.time(), rgb)
        if not self.corriendo or not self.c.est.aruco:
            return
        for mid, z, R, dist, px in self.vision.medir(cam, rgb):
            self.q_med.put((cam, mid, z, R))

    def tic(self, dt_real):
        """Avanza dt_real segundos de simulación (en pasos de 20 ms)."""
        c = self.c
        n = max(1, int(round(dt_real / N.DT)))
        r = None
        for _ in range(n):
            if c.ejec.fin:
                self.corriendo = False
                break
            r = c.paso()
            self.k += 1
            if c.est.aruco and self.geometrico and self.k % 5 == 0:
                for nom, mid, z, R in N.aruco_geometrico(c.planta.q, c.M, c.cams, c.rng):
                    c.est.marca(z, R)
                    self.vistas[nom] += 1
            if r['etapa'] == 'EXTIENDE' and getattr(self, '_et', None) != 'EXTIENDE':
                self.ultima_llegada = c.llegada(r)
            self._et = r['etapa']
            if self.k % 5 == 0:
                self.m_min = min(self.m_min, c.margen(c.planta.q, r['c'], r['etapa'])[0])
        while not self.q_med.empty():
            cam, mid, z, R = self.q_med.get_nowait()
            c.est.marca(z, R)
            self.vistas[cam] += 1
        return r

    def estado(self):
        c = self.c
        tau = c.ejec.S_t()
        r = c.plan.ref(tau)
        vert = c.plan.vert(tau)
        q = c.planta.q
        cree = c.est.pose if c.est.activo else None
        m = c.margen(q, r['c'], r['etapa'])[0]
        return dict(t=c.t, tau=tau, etapa=c.ejec.p.S[min(c.ejec.i, len(c.ejec.p.S) - 1)][7], q=q, cree=cree,
                    ref=(r['x'], r['y'], r['th']), vert=vert, margen=m,
                    e_real_plan=math.hypot(q[0] - r['x'], q[1] - r['y']),
                    e_cree_real=None if cree is None else math.hypot(q[0] - cree[0], q[1] - cree[1]),
                    d_rueda=c.planta.d, desplazador=c.ejec.desplazador)

    def a_gazebo(self, e):
        if not self.gz:
            return
        tau = e['tau']
        # los cubos: en el rack / zona según el plan; los que deja el equipo, donde de verdad los dejó
        if self.ibc_prev == 'uñas' and e['vert']['ibc'] == 'nada':
            x, y, th = e['q']
            c, s = math.cos(th), math.sin(th)
            a = self.gz.a_mast + e['vert']['ext'] + 0.60
            bx, by = x + a * c - e['desplazador'] * s, y + a * s + e['desplazador'] * c
            cand = [k for k, cb in enumerate(self.cubos) if cb['t0'] > 0 and cb['tipo'] in ('rack', 'principio')
                    and abs(cb['t0'] - tau) < 3.0]
            if cand:
                k = min(cand, key=lambda k: abs(self.cubos[k]['t0'] - tau))
                self.cubos[k].update(x=bx, y=by, th=th)
        self.ibc_prev = e['vert']['ibc']
        pz = []
        for cb in self.cubos:
            if cb['t0'] <= tau < cb['t1']:
                pz.append((cb['x'], cb['y'], cb['z'], cb['th'], 0.0))
            else:
                pz.append((0.0, 0.0, -10.0, 0.0, 0.0))
        self.gz.camara(e['q'])
        fant = e['cree'] if e['cree'] is not None else e['ref']
        self.gz.escena(e['q'], e['d_rueda'], e['vert'], e['desplazador'], fant, pz)


# ── la consola (a prueba de tontos: START verde, STOP rojo) ────────────────────────────────────────────────────
def consola(sim, velocidad, auto=0.0):
    import tkinter as tk
    r = tk.Tk()
    r.title('TaTa · turno en Gazebo')
    r.configure(bg='#1e2228')
    est = dict(vel=velocidad)
    fuente = ('Segoe UI', 13, 'bold')

    def boton(padre, txt, color, cmd, ancho=12):
        return tk.Button(padre, text=txt, bg=color, fg='white', font=fuente, width=ancho, height=2, command=cmd,
                         activebackground=color, relief='flat')

    fila = tk.Frame(r, bg='#1e2228'); fila.pack(padx=10, pady=8)
    boton(fila, 'START', '#2e7d32', lambda: setattr(sim, 'corriendo', True)).pack(side='left', padx=4)
    boton(fila, 'STOP', '#c62828', lambda: setattr(sim, 'corriendo', False)).pack(side='left', padx=4)
    boton(fila, 'REINICIAR', '#455a64', sim.reiniciar).pack(side='left', padx=4)
    boton(fila, 'seguir al equipo', '#37474f', lambda: sim.gz and sim.gz.seguir(), 14).pack(side='left', padx=4)

    llaves = tk.Frame(r, bg='#1e2228'); llaves.pack(padx=10, pady=4)
    bo = boton(llaves, '', '#2e7d32', None, 22)
    ba = boton(llaves, '', '#2e7d32', None, 22)

    def pintar_llaves():
        o, a = sim.c.est.odo, sim.c.est.aruco
        bo.configure(text=f"ODOMETRÍA: {'SÍ' if o else 'NO'}", bg='#2e7d32' if o else '#5d4037')
        ba.configure(text=f"ARUCO: {'SÍ' if a else 'NO'}", bg='#2e7d32' if a else '#5d4037')

    def cambiar(cual):
        setattr(sim.c.est, cual, not getattr(sim.c.est, cual))
        sim.odo0, sim.aruco0 = sim.c.est.odo, sim.c.est.aruco
        pintar_llaves()

    bo.configure(command=lambda: cambiar('odo')); ba.configure(command=lambda: cambiar('aruco'))
    bo.pack(side='left', padx=4); ba.pack(side='left', padx=4)
    pintar_llaves()

    vf = tk.Frame(r, bg='#1e2228'); vf.pack(pady=2)
    tk.Label(vf, text='velocidad', fg='#9aa4b1', bg='#1e2228').pack(side='left')
    for v in (1, 2, 4, 8):
        tk.Button(vf, text=f'×{v}', width=4, command=lambda v=v: est.update(vel=v)).pack(side='left', padx=2)

    lModo = tk.Label(r, text='', fg='#f0b429', bg='#1e2228', font=('Segoe UI', 14, 'bold')); lModo.pack(pady=4)
    lNum = tk.Label(r, text='', fg='white', bg='#1e2228', font=('Consolas', 12), justify='left'); lNum.pack(padx=10, pady=6)
    lAlarma = tk.Label(r, text='', fg='white', bg='#1e2228', font=('Segoe UI', 14, 'bold')); lAlarma.pack(pady=4)
    tk.Label(r, text='amarillo = dónde está el equipo · azul transparente = dónde CREE que está\n'
                     'sin odometría ni ArUco: hace el plan a ciegas (el azul es el plan)',
             fg='#9aa4b1', bg='#1e2228').pack(pady=(0, 8))

    reloj = dict(t=time.time(), pose=0.0)

    def tic():
        ahora = time.time()
        dt = min(0.1, ahora - reloj['t'])
        reloj['t'] = ahora
        if sim.corriendo:
            sim.tic(dt * est['vel'])
        e = sim.estado()
        if ahora - reloj['pose'] >= 1.0 / HZ_POSES:
            sim.a_gazebo(e)
            reloj['pose'] = ahora
        o, a = sim.c.est.odo, sim.c.est.aruco
        modo = {(True, True): 'odometría + ArUco', (True, False): 'solo odometría', (False, True): 'solo ArUco',
                (False, False): 'NINGUNO: a ciegas (lazo abierto)'}[(o, a)]
        lModo.configure(text=f"{'▶' if sim.corriendo else '■'}  {modo}")
        ll = sim.ultima_llegada
        lNum.configure(text=(
            f"tiempo {e['t']:7.1f} s   plan {e['tau']:6.1f} / {sim.c.plan.T_FIN:.0f} s   etapa {e['etapa']}\n"
            f"real vs plan        {100 * e['e_real_plan']:7.1f} cm\n"
            f"cree vs real        {'—' if e['e_cree_real'] is None else '%7.1f cm' % (100 * e['e_cree_real'])}\n"
            f"margen a los racks  {100 * e['margen']:7.1f} cm   (mínimo de la corrida {100 * sim.m_min:.1f})\n"
            f"última llegada      {'—' if ll is None else 'uñas %.1f cm de lado, punta %.1f cm, rumbo %.1f°' % (100 * ll[0], 100 * ll[1], ll[2])}\n"
            f"ArUco aceptados     lateral {sim.vistas['cam_lateral']} · trasera {sim.vistas['cam_trasera']}"))
        if e['margen'] < 0:
            lAlarma.configure(text=f"¡ROCE / CHOQUE: {-100 * e['margen']:.1f} cm adentro de la cara!", bg='#c62828')
        elif ll is not None and ll[0] > N.REQ_LAT:
            lAlarma.configure(text=f"uñas fuera de ±4.5 cm en la última bahía ({100 * ll[0]:.1f} cm)", bg='#c77700')
        else:
            lAlarma.configure(text='', bg='#1e2228')
        r.after(20, tic)

    def cerrar():
        if sim.gz:
            sim.gz.cerrar()
        r.destroy()

    r.protocol('WM_DELETE_WINDOW', cerrar)
    if auto:
        sim.corriendo = True
        def fin():
            e = sim.estado()
            print(f"consola: {e['t']:.1f} s simulados, etapa {e['etapa']}, sin errores")
            cerrar()
        r.after(int(auto * 1000), fin)
    tic()
    r.mainloop()


def prueba_vision(D, gz, sim):
    """Pone el equipo en poses donde se ven marcas y compara la pose que da cada marca con la verdadera."""
    M = N.marcas(D)
    casos = []
    for mid, (mx, my, mth) in list(M.items())[:8]:
        s = 1 if my > 0 else -1
        casos.append((mx + 0.75, 0.0 + 0.3 * s, 0.0))           # la lateral (izq.) mira +y: marcas del lado L
        casos.append((mx + 1.5, -0.2 * s, math.pi))
        casos.append((mx + 2.2, 0.1, 0.0))
    errs = []
    for q in casos:
        gz.escena(q, 0.0, dict(h=0.05, ext=0.0, ibc='nada', inc=0.0), 0.0, None, [])
        t_puesto = time.time() + 0.6                      # imágenes renderizadas después de mover el equipo
        while time.time() - t_puesto < 2.5 and sum(1 for v in sim.ultimas.values() if v[0] > t_puesto) < 2:
            time.sleep(0.1)
        if not sim.ultimas:
            print('  (no llegan imágenes de las cámaras)')
        for cam, (tt, rgb) in list(sim.ultimas.items()):
            if tt < t_puesto:
                continue
            for mid, z, R, dist, px in sim.vision.medir(cam, rgb):
                e = math.hypot(z[0] - q[0], z[1] - q[1])
                eth = math.degrees(abs(N.envolver(z[2] - q[2])))
                errs.append((e, eth, dist))
                print(f"  {cam:11s} marca {mid:2d} a {dist:4.2f} m ({px:4.0f} px): error de pose {100 * e:5.1f} cm, {eth:4.1f}°  "
                      f"σ que dice el modelo {100 * math.sqrt(R[0, 0] + R[1, 1]):4.1f} cm")
    if errs:
        E = np.array(errs)
        print(f"PRUEBA VISIÓN: {len(E)} lecturas · error mediana {100 * np.median(E[:, 0]):.1f} cm, máx {100 * E[:, 0].max():.1f} cm · "
              f"rumbo mediana {np.median(E[:, 1]):.1f}°")
    else:
        print('PRUEBA VISIÓN: ninguna marca vista — revisar la orientación de las texturas')
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sin-gui', action='store_true')
    ap.add_argument('--no-lanzar', action='store_true')
    ap.add_argument('--aruco-geometrico', action='store_true')
    ap.add_argument('--modo', default='ambos', choices=['ambos', 'odo', 'aruco', 'ninguno'])
    ap.add_argument('--velocidad', type=float, default=1.0)
    ap.add_argument('--hasta', type=float, default=None)
    ap.add_argument('--semilla', type=int, default=0)
    ap.add_argument('--prueba-vision', action='store_true')
    ap.add_argument('--sin-gazebo', action='store_true', help='solo la lógica (ArUco geométrico)')
    ap.add_argument('--gz-sin-ventana', action='store_true', help='Gazebo sin su ventana 3D (solo la consola)')
    ap.add_argument('--auto', type=float, default=0.0, help='(prueba) arranca solo y cierra la consola a los N s')
    ap.add_argument('--seguir', action='store_true', help='arranca con la cámara 3D persiguiendo al equipo')
    a = ap.parse_args()
    D = N.cargar()
    odo, aruco = {'ambos': (True, True), 'odo': (True, False), 'aruco': (False, True), 'ninguno': (False, False)}[a.modo]
    headless = a.sin_gui or a.prueba_vision or a.gz_sin_ventana
    gz = None if a.sin_gazebo else Gazebo(D, lanzar=not a.no_lanzar, headless=headless)
    sim = Sim(D, gz, odo, aruco, geometrico=a.aruco_geometrico or a.sin_gazebo, semilla=a.semilla)
    if a.seguir and gz:
        gz.seguir()
    try:
        if a.prueba_vision:
            prueba_vision(D, gz, sim)
            return
        if a.sin_gui:
            sim.corriendo = True
            hasta = a.hasta or sim.c.plan.T_FIN
            t0, ultimo = time.time(), 0.0
            while sim.corriendo and sim.c.ejec.S_t() < hasta:
                sim.tic(N.DT * a.velocidad)
                e = sim.estado()
                if gz and time.time() - ultimo > 1.0 / HZ_POSES:
                    sim.a_gazebo(e)
                    ultimo = time.time()
                time.sleep(max(0.0, N.DT - 0.002) if gz else 0.0)
            e = sim.estado()
            ll = sim.ultima_llegada
            print(f"modo {a.modo}: {e['t']:.0f} s de simulación ({time.time() - t0:.0f} s reales) hasta τ {e['tau']:.0f} · "
                  f"real vs plan {100 * e['e_real_plan']:.1f} cm · cree vs real "
                  f"{'—' if e['e_cree_real'] is None else '%.1f cm' % (100 * e['e_cree_real'])} · margen mínimo {100 * sim.m_min:.1f} cm · "
                  f"última llegada {('—' if ll is None else 'uñas %.1f cm, punta %.1f cm, %.1f°' % (100 * ll[0], 100 * ll[1], ll[2]))} · "
                  f"ArUco aceptados {sim.vistas}")
            return
        consola(sim, a.velocidad, a.auto)
    finally:
        if gz:
            gz.cerrar()
        sys.stdout.flush()
        os._exit(0)                         # los hilos de gz-transport no terminan solos


if __name__ == '__main__':
    main()
