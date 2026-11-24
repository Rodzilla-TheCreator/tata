#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · generar_mundo.py — el pasillo B del DXF en Gazebo (Harmonic), con los números de la v4 (24-nov-2026).

Lee TODO de sim/sim_datos.json (el mismo turno que sim/simulacion.html): postes, bahías, alturas de nivel,
zonas de carga y descarga, la silueta del equipo (culo de la ficha, uñas), las cámaras (montaje A2) y las
16 marcas ArUco (cada 2 bahías, en las dos caras, a 1.0 m, de 15 cm). Escribe:

    sim-gazebo/mundo/pasillo.sdf
    sim-gazebo/mundo/aruco/aruco_<id>.png        (DICT_4X4_50, como percepcion/generar_aruco.py)

    python3 sim-gazebo/generar_mundo.py

Modelos que se mueven (los mueve correr.py con /world/pasillo/set_pose_vector, cinemática propia):
    edr        el chasis, la torre y las dos cámaras (A2: lateral izq. + trasera diagonal), 640×480, 54.3°
    rueda      la rueda motriz, corrida 0.325 bajo el timón, gira con δ
    carro      el carro y las uñas (altura, pantógrafo, inclinación)
    ibc_unas   el cubo cuando va en las uñas
    ibc_<k>    los cubos del turno en el rack / en las zonas
    fantasma   dónde CREE el equipo que está (lo que estima el EKF), azul y transparente
Todo lo demás (racks, cubos de relleno, marcas) es estático.
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SALIDA = os.path.join(AQUI, 'mundo')

L_MARCA = 0.15            # lado del cuadro negro (percepcion/visibilidad.py)
BORDE = 0.03              # margen blanco alrededor (la zona quieta que pide el detector)
H_MARCA = 1.00            # centro de la marca sobre el poste
H_CAM = 1.00              # las cámaras A2 (visibilidad_v3.montajes)
HFOV = math.radians(54.3)  # C920 (visibilidad.py)
W_IMG, H_IMG = 640, 480
H_PLAT = 0.115            # grosor de plataforma (CLAUDE.md, el rack)
PROF_POSTE = 0.08
H_RACK = 8.2
H_BASE = 0.30             # chasis: la base (patas incluidas)
H_CAPO = 1.20             # el capó / compartimento de batería
H_TECHO = 2.413           # techo protector (VDI)
H_TORRE = 2.72            # mástil replegado (VDI h1)


ENCABEZADO = """<?xml version="1.0"?>
<sdf version="1.9">
<world name="pasillo">
  <physics name="1ms" type="ignored"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor></physics>
  <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
  <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
  <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
  <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>{motor}</render_engine></plugin>
  <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.75 0.8 0.85 1</background><shadows>false</shadows></scene>
  <gui fullscreen="0">
    <plugin filename="MinimalScene" name="3D View">
      <gz-gui><title>3D View</title><property type="bool" key="showTitleBar">false</property><property type="string" key="state">docked</property></gz-gui>
      <engine>{motor}</engine><scene>scene</scene><ambient_light>0.5 0.5 0.5</ambient_light><background_color>0.75 0.8 0.85</background_color>
      <camera_pose>{cam}</camera_pose>
    </plugin>
    <plugin filename="EntityContextMenuPlugin" name="Entity context menu"><gz-gui><property key="state" type="string">floating</property><property key="width" type="double">5</property><property key="height" type="double">5</property><property key="showTitleBar" type="bool">false</property></gz-gui></plugin>
    <plugin filename="GzSceneManager" name="Scene Manager"><gz-gui><property key="resizable" type="bool">false</property><property key="width" type="double">5</property><property key="height" type="double">5</property><property key="state" type="string">floating</property><property key="showTitleBar" type="bool">false</property></gz-gui></plugin>
    <plugin filename="InteractiveViewControl" name="Interactive view control"><gz-gui><property key="resizable" type="bool">false</property><property key="width" type="double">5</property><property key="height" type="double">5</property><property key="state" type="string">floating</property><property key="showTitleBar" type="bool">false</property></gz-gui></plugin>
    <plugin filename="CameraTracking" name="Camera Tracking"><gz-gui><property key="resizable" type="bool">false</property><property key="width" type="double">5</property><property key="height" type="double">5</property><property key="state" type="string">floating</property><property key="showTitleBar" type="bool">false</property></gz-gui></plugin>
    <plugin filename="ImageDisplay" name="Cámara lateral"><gz-gui><title>lateral</title><property type="string" key="state">docked</property></gz-gui><topic>/tata/cam_lateral</topic></plugin>
    <plugin filename="ImageDisplay" name="Cámara trasera"><gz-gui><title>trasera diag.</title><property type="string" key="state">docked</property></gz-gui><topic>/tata/cam_trasera</topic></plugin>
  </gui>
  <light type="directional" name="sol"><cast_shadows>false</cast_shadows><pose>0 0 20 0 0 0</pose><diffuse>0.9 0.9 0.88 1</diffuse><specular>0.2 0.2 0.2 1</specular><direction>-0.3 0.4 -1</direction></light>
  <light type="directional" name="luz_relleno"><cast_shadows>false</cast_shadows><pose>0 0 20 0 0 0</pose><diffuse>0.35 0.35 0.38 1</diffuse><specular>0 0 0 1</specular><direction>0.4 -0.3 -1</direction></light>
"""


def f(x):
    return f"{x:.4f}"


def pose(x=0, y=0, z=0, r=0, p=0, yaw=0):
    return f"<pose>{f(x)} {f(y)} {f(z)} {f(r)} {f(p)} {f(yaw)}</pose>"


def material(r, g, b, a=1.0, emisivo=None):
    e = f"<emissive>{emisivo}</emissive>" if emisivo else ""
    return (f"<material><ambient>{r} {g} {b} {a}</ambient><diffuse>{r} {g} {b} {a}</diffuse>"
            f"<specular>0.1 0.1 0.1 {a}</specular>{e}</material>")


def caja(nombre, sx, sy, sz, x, y, z, color, yaw=0.0, alfa=1.0):
    return (f"<visual name='{nombre}'>{pose(x, y, z, 0, 0, yaw)}<geometry><box><size>{f(sx)} {f(sy)} {f(sz)}"
            f"</size></box></geometry>{material(*color, alfa)}"
            + (f"<transparency>{1 - alfa:.2f}</transparency>" if alfa < 1 else "") + "</visual>")


def poligono(nombre, pts, z0, alto, color, alfa=1.0):
    p = "".join(f"<point>{f(a)} {f(b)}</point>" for a, b in pts)
    return (f"<visual name='{nombre}'>{pose(0, 0, z0)}<geometry><polyline>{p}<height>{f(alto)}</height>"
            f"</polyline></geometry>{material(*color, alfa)}"
            + (f"<transparency>{1 - alfa:.2f}</transparency>" if alfa < 1 else "") + "</visual>")


def simplificar(pts, n=120):
    """El contorno del cuerpo tiene 606 puntos (el culo de la ficha): con ~120 se ve igual y carga rápido."""
    pts = np.asarray(pts)
    if len(pts) <= n:
        return pts
    idx = np.unique(np.r_[np.linspace(0, len(pts) - 1, n).astype(int)])
    return pts[idx]


def recortar_x(pts, xmax):
    """Sutherland–Hodgman contra el semiplano x ≤ xmax (el capó es la parte de atrás del cuerpo)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ia, ib = a[0] <= xmax, b[0] <= xmax
        if ia:
            out.append(a)
        if ia != ib:
            t = (xmax - a[0]) / (b[0] - a[0])
            out.append((xmax, a[1] + t * (b[1] - a[1])))
    return out


def modelo_movil(nombre, cuerpo, x=0.0, y=0.0, z=0.0, yaw=0.0):
    """Modelo cinemático: sin gravedad ni colisiones; lo mueve correr.py."""
    return (f"<model name='{nombre}'>{pose(x, y, z, 0, 0, yaw)}<link name='base'><gravity>false</gravity>"
            f"<kinematic>true</kinematic>{cuerpo}</link></model>")


def png_aruco(mid, ruta):
    import cv2
    lado_px = 240
    borde_px = int(round(lado_px * BORDE / L_MARCA))
    img = cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), mid, lado_px)
    img = cv2.copyMakeBorder(img, borde_px, borde_px, borde_px, borde_px, cv2.BORDER_CONSTANT, value=255)
    cv2.imwrite(ruta, cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))


def main(ruta_datos=os.path.join(RAIZ, 'sim', 'sim_datos.json'), motor='ogre2'):
    with open(ruta_datos, encoding='utf-8') as fh:
        D = json.load(fh)
    G, EQ = D['geo'], D['equipo']
    HALF = G['PASILLO'] / 2
    os.makedirs(os.path.join(SALIDA, 'aruco'), exist_ok=True)
    m = []
    # la vista de arranque: desde detrás del principio del pasillo, alto, mirando por el eje hacia el fondo
    cam = f"{f(-G['ZONA_ATRAS'] - 3.0)} 0 7.5 0 0.5 0"
    m.append(ENCABEZADO.replace('{motor}', motor).replace('{cam}', cam))

    # ── el piso, las paredes y la línea del eje ─────────────────────────────────────────────────────────
    x_fondo = G['X_FONDO']
    largo = x_fondo + G['ZONA_ATRAS'] + 6
    piso = caja('piso', largo, 12, 0.02, (x_fondo - G['ZONA_ATRAS']) / 2, 0, -0.01, (0.62, 0.62, 0.6))
    eje = caja('eje', x_fondo + G['ZONA_ATRAS'], 0.04, 0.003, (x_fondo - G['ZONA_ATRAS']) / 2, 0, 0.002, (0.95, 0.8, 0.1))
    paredes = (caja('pared_fondo', 0.2, 8, 3.0, x_fondo + 0.1, 0, 1.5, (0.85, 0.85, 0.82))
               + caja('pared_principio', 0.2, 8, 3.0, -G['ZONA_ATRAS'] - 0.1, 0, 1.5, (0.85, 0.85, 0.82)))
    zonas = ''
    for nom, z in (('carga', G['zona_carga']), ('descarga', G['zona_descarga'])):
        if z:
            s = -1 if z['lado'] == 'R' else 1
            ancho = G['FONDO_RACK']
            zonas += caja(f'zona_{nom}', z['x1'] - z['x0'], ancho, 0.004, (z['x0'] + z['x1']) / 2,
                          s * (HALF + ancho / 2), 0.003, (0.2, 0.55, 0.9) if nom == 'carga' else (0.9, 0.5, 0.2))
    m.append(f"<model name='nave'><static>true</static><link name='l'>{piso}{eje}{paredes}{zonas}</link></model>")

    # ── los racks: postes (adelante y atrás) y plataformas de N2 a N5 ────────────────────────────────────
    alt = G['ALTURAS']
    vis = []
    gris, naranja = (0.35, 0.38, 0.42), (0.85, 0.45, 0.1)
    for s in (1, -1):
        yf, yb = s * (HALF + PROF_POSTE / 2), s * (HALF + G['FONDO_RACK'] - PROF_POSTE / 2)
        for k, xp in enumerate(G['postes']):
            xc = xp + G['POSTE'] / 2
            vis.append(caja(f'p{s}_{k}', G['POSTE'], PROF_POSTE, H_RACK, xc, yf, H_RACK / 2, naranja))
            vis.append(caja(f'q{s}_{k}', G['POSTE'], PROF_POSTE, H_RACK, xc, yb, H_RACK / 2, naranja))
        for n, (x0, x1) in enumerate(G['bahias']):
            for nv in ('2', '3', '4', '5'):
                zb = alt[nv][0]
                vis.append(caja(f'pl{s}_{n}_{nv}', x1 - x0, G['FONDO_RACK'], H_PLAT, (x0 + x1) / 2,
                                s * (HALF + G['FONDO_RACK'] / 2), zb - H_PLAT / 2, gris))
    m.append(f"<model name='racks'><static>true</static><link name='l'>{''.join(vis)}</link></model>")

    # ── cubos de relleno: casi todos los huecos, menos los del turno (esos se mueven) ─────────────────────
    ocupados = {p['hueco'] for p in D['pedidos']}
    g = (G['BAHIA'] - 2 * 1.0) / 3                       # tres huelgos iguales con los 35 cm (bahias.centro_posicion)
    rel = []
    ibc_c, ibc_jaula = (0.93, 0.94, 0.95), (0.55, 0.57, 0.6)
    for s, lado in ((1, 'L'), (-1, 'R')):
        yc = s * (HALF + 0.06 + 0.60)
        for n, (x0, x1) in enumerate(G['bahias']):
            for pos, xc in (('a', x0 + g + 0.5), ('b', x0 + 2 * g + 1.5)):
                hay_1a = False
                for nv in ('1A', '1B', '2', '3', '4', '5'):
                    clave = f"{n + 1} {nv} {lado}{pos}"
                    debajo = f"{n + 1} 1B {lado}{pos}" in ocupados and nv == '1A'
                    vacio = (n * 7 + len(nv) * 3 + (pos == 'b') * 5 + (s > 0) * 2 + int(nv[0])) % 5 == 0
                    if clave in ocupados or (vacio and not debajo) or (nv == '1B' and not hay_1a):
                        continue
                    hay_1a = hay_1a or nv == '1A'
                    zb = alt[nv][0]
                    rel.append(caja(f'r{s}{n}{pos}{nv}', 1.0, 1.2, 1.0, xc, yc, zb + 0.15 + 0.5, ibc_c, alfa=0.9))
                    rel.append(caja(f't{s}{n}{pos}{nv}', 1.0, 1.2, 0.15, xc, yc, zb + 0.075, ibc_jaula))
    m.append(f"<model name='relleno'><static>true</static><link name='l'>{''.join(rel)}</link></model>")

    # ── las marcas ArUco (planas, en la cara de los postes, mirando al pasillo) ───────────────────────────
    lado_vis = L_MARCA + 2 * BORDE
    for mk in D['marcas']:
        ruta = os.path.join(SALIDA, 'aruco', f"aruco_{mk['id']}.png")
        png_aruco(mk['id'], ruta)
        s = 1 if mk['y'] > 0 else -1
        y = s * (HALF - 0.004)
        # el plano (normal +z) se acuesta con roll +90° (normal −y) y en el lado R se gira 180° (normal +y): así mira
        # al pasillo y la marca queda derecha, no espejada (probado con el detector en las dos caras)
        rot = f"{f(math.pi / 2)} 0 {f(0 if s > 0 else math.pi)}"      # el plano tiene una sola cara: mira al pasillo
        m.append(f"""<model name='aruco_{mk['id']}'><static>true</static><pose>{f(mk['x'])} {f(y)} {f(H_MARCA)} {rot}</pose>
  <link name='l'><visual name='v'><geometry><plane><normal>0 0 1</normal><size>{f(lado_vis)} {f(lado_vis)}</size></plane></geometry>
  <material><diffuse>1 1 1 1</diffuse><ambient>1 1 1 1</ambient><emissive>0.55 0.55 0.55 1</emissive>
  <pbr><metal><albedo_map>aruco/aruco_{mk['id']}.png</albedo_map><metalness>0</metalness><roughness>1</roughness></metal></pbr></material></visual></link></model>""")

    # ── el equipo ────────────────────────────────────────────────────────────────────────────────────────
    cuerpo = simplificar(EQ['piezas']['vacio'][0])
    amarillo, negro, acero = (0.95, 0.72, 0.05), (0.08, 0.08, 0.08), (0.25, 0.27, 0.3)
    am = EQ['a_mast']
    capo = recortar_x([tuple(p) for p in cuerpo], am - 0.25)
    vis = [poligono('base', cuerpo, 0.0, H_BASE, amarillo),
           poligono('capo', capo, H_BASE, H_CAPO - H_BASE, amarillo)]
    # techo protector sobre el compartimento (de la torre hacia atrás, ~1.0 m)
    xt0, xt1 = am - 1.25, am - 0.25
    for xx in (xt0, xt1):
        for yy in (0.45, -0.45):
            vis.append(caja(f'col{xx:.2f}{yy}', 0.05, 0.05, H_TECHO - H_CAPO, xx, yy, (H_TECHO + H_CAPO) / 2, negro))
    vis.append(caja('techo', xt1 - xt0 + 0.05, 0.95, 0.05, (xt0 + xt1) / 2, 0, H_TECHO, negro))
    # la torre (mástil replegado)
    for yy in (0.33, -0.33):
        vis.append(caja(f'torre{yy}', 0.12, 0.10, H_TORRE, am - 0.16, yy, H_TORRE / 2, acero))
    vis.append(caja('torre_trav', 0.10, 0.76, 0.12, am - 0.16, 0, H_TORRE - 0.06, acero))
    # las ruedas de carga y la de apoyo
    for yy in (0.6, -0.6):
        vis.append(caja(f'carga{yy}', 0.127 * 2, 0.20, 0.127, 0.0, yy, 0.0635, negro))
    e, wb = EQ.get('e', 0.0), EQ['wb']
    if e:
        vis.append(caja('apoyo', 0.18, 0.10, 0.18, -wb, -e, 0.09, negro))
    # las cámaras (montaje A2), con su cuerpito para verlas
    sensores = []
    for cam, top in zip(D['camaras'], ('cam_lateral', 'cam_trasera')):
        vis.append(caja(f"c_{top}", 0.08, 0.10, 0.06, cam['cx'], cam['cy'], H_CAM, negro, yaw=cam['yaw']))
        sensores.append(f"""<sensor name='{top}' type='camera'>{pose(cam['cx'], cam['cy'], H_CAM, 0, 0, cam['yaw'])}
      <topic>/tata/{top}</topic><update_rate>10</update_rate><always_on>true</always_on>
      <camera><horizontal_fov>{f(HFOV)}</horizontal_fov><image><width>{W_IMG}</width><height>{H_IMG}</height><format>R8G8B8</format></image>
      <clip><near>0.05</near><far>30</far></clip></camera></sensor>""")
    p0 = D['S'][0]
    m.append(modelo_movil('edr', ''.join(vis) + ''.join(sensores), p0[1], p0[2], 0, p0[3]))

    # la rueda motriz (el cilindro de 343 × 140, eje horizontal)
    r_rueda, a_rueda = EQ['rueda'][0] / 2, EQ['rueda'][1]
    m.append(modelo_movil('rueda', f"<visual name='v'>{pose(0, 0, r_rueda, math.pi / 2, 0, 0)}<geometry><cylinder>"
                                   f"<radius>{f(r_rueda)}</radius><length>{f(a_rueda)}</length></cylinder></geometry>"
                                   f"{material(0.15, 0.15, 0.15)}</visual>"
                                   + caja('marca', 0.30, 0.02, 0.02, 0.0, a_rueda / 2 + 0.01, r_rueda, (0.9, 0.1, 0.1)),
                          0, 0, -5))
    # el carro y las uñas: origen en el dorso de las uñas, a la altura del fondo de la uña
    uñas = [caja('placa', 0.06, 0.825, 0.50, -0.03, 0, 0.25, acero)]
    for yy in (0.30, -0.30):
        uñas.append(caja(f'u{yy}', 1.20, 0.10, 0.036, 0.60, yy, 0.018, acero))
        uñas.append(caja(f'v{yy}', 0.05, 0.10, 0.50, 0.025, yy, 0.25, acero))
    m.append(modelo_movil('carro', ''.join(uñas), 0, 0, -5))
    # el cubo en las uñas y los cubos del turno
    cubo = (caja('t', 1.2, 1.0, 1.0, 0, 0, 0.15 + 0.5, ibc_c, alfa=0.9) + caja('b', 1.2, 1.0, 0.15, 0, 0, 0.075, ibc_jaula))
    m.append(modelo_movil('ibc_unas', cubo, 0, 0, -10))
    for k, c in enumerate(D['cubos']):
        m.append(modelo_movil(f'ibc_{k}', cubo, 0, 0, -10))
    # el fantasma: dónde cree el equipo que está
    m.append(modelo_movil('fantasma', poligono('f', cuerpo, 0.0, 0.06, (0.1, 0.45, 1.0), alfa=0.55), 0, 0, -5))
    m.append("</world>\n</sdf>\n")
    ruta = os.path.join(SALIDA, 'pasillo.sdf')
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(m))
    print(f"{ruta}: {len(G['postes'])} postes por lado, {len(G['bahias'])} bahías por lado, {len(D['marcas'])} marcas, "
          f"{len(rel) // 2} cubos de relleno, {len(D['cubos'])} cubos del turno")
    return ruta


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('datos', nargs='?', default=os.path.join(RAIZ, 'sim', 'sim_datos.json'))
    ap.add_argument('--motor', default='ogre2', choices=['ogre2', 'ogre'],
                    help='ogre2 (por defecto); ogre si la gráfica es vieja o en WSL2 se ve mal')
    a = ap.parse_args()
    main(a.datos, a.motor)
