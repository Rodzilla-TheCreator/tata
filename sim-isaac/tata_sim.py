# ─────────────────────────────────────────────────────────────────────────────
# TaTa · banco de pruebas en Isaac Sim 6.0
# Escena: Propuesta IT (sector C) del almacén RETHINK — 790 ubicaciones, 10 filas
#
# Filosofía del banco: en simulación los sensores no cuestan dinero, cuestan GPU.
# Por eso NO se simula un nivel de BOM: se simula el conjunto completo y se van
# APAGANDO sensores hasta que algo se rompe. El que rompe es el que hay que comprar.
#
# Uso:  ./python.sh tata_sim.py --nivel produccion
#       ./python.sh tata_sim.py --nivel scrappy --ruido alto
# ─────────────────────────────────────────────────────────────────────────────
import argparse, os, sys

ap = argparse.ArgumentParser()
ap.add_argument('--nivel', default='produccion',
                choices=['scrappy', 'industrial', 'produccion', 'maximo'])
ap.add_argument('--ruido', default='real', choices=['ideal', 'real', 'alto'])
ap.add_argument('--headless', action='store_true')
ap.add_argument('--sin-sensores', dest='sin_sensores', action='store_true',
                help='carga solo bodega + montacargas; no importa ni monta sensores')
ap.add_argument('--usd', default=os.path.join(os.path.dirname(__file__), 'PropuestaIT_RETHINK.usda'))
A = ap.parse_args()

# ── el SimulationApp debe arrancar ANTES de cualquier import de omni/isaacsim ──
from isaacsim import SimulationApp
sim_app = SimulationApp({"headless": A.headless, "renderer": "RayTracedLighting"})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.prims import create_prim
from isaacsim.core.utils.viewports import set_camera_view
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics

# ─────────────────────────────────────────────────────────────────────────────
# 1 · SUITE DE SENSORES  — un solo lugar para toda la ablación
#     'on' por nivel: qué sensores existen en cada escalón del BOM.
#     La posición de montaje sale del BOM real (columna "Posición de montaje").
# ─────────────────────────────────────────────────────────────────────────────
NIVELES = ['scrappy', 'industrial', 'produccion', 'maximo']

SENSORES = {
    # ── navegación ──────────────────────────────────────────────────────────
    'lidar3d': dict(
        tipo='lidar', desde='scrappy',                 # existe desde el scrappy
        montaje=(0.00, 0.00, 2.15),                    # techo de protección
        config={'scrappy': 'Example_Rotary',           # sustituto barato, 10 Hz
                'industrial': 'Example_Rotary',        # ≈ Livox Mid-360
                'produccion': 'Example_Rotary',
                'maximo': 'OS1_REV7_128ch10hz1024res'},
        hz={'scrappy': 10, 'industrial': 10, 'produccion': 10, 'maximo': 20},
        nota='Livox Mid-360 real: 360°x59°, 40 m, zona ciega 0.1 m'),

    'lidar2d_izq': dict(
        tipo='lidar', desde='produccion',              # sólo aparece en producción
        montaje=(0.55, 0.40, 0.15),                    # esquina frontal izquierda
        config={'produccion': 'Example_Rotary', 'maximo': 'Example_Rotary'},
        hz={'produccion': 25, 'maximo': 25},
        nota='SICK nanoScan3 · 275° · PL d · el que decide los $7,000'),

    'lidar2d_der': dict(
        tipo='lidar', desde='produccion',
        montaje=(0.55, -0.40, 0.15),
        config={'produccion': 'Example_Rotary', 'maximo': 'Example_Rotary'},
        hz={'produccion': 25, 'maximo': 25}, nota='par del anterior'),

    # ── visión ──────────────────────────────────────────────────────────────
    'cam_frontal': dict(
        tipo='camara', desde='scrappy',
        montaje=(0.20, 0.00, 1.52), mira=(1, 0, -0.02),
        res={'scrappy': (640, 400), 'industrial': (1280, 720),
             'produccion': (1280, 800), 'maximo': (1920, 1200)},
        fov=72, nota='RealSense D455 — alerta y frenado'),

    'cam_mastil': dict(
        tipo='camara', desde='scrappy',
        montaje=(1.05, 0.00, 0.70), mira=(1, 0, 0),    # SUBE con el carro
        res={'scrappy': (1280, 960), 'industrial': (1920, 1080),
             'produccion': (2592, 1944), 'maximo': (2592, 1944)},
        fov=48, sigue_uñas=True,
        nota='la pieza que vuelve el nivel 1 un sistema de inventario'),

    'cam_uñas': dict(
        tipo='camara', desde='scrappy',
        montaje=(1.10, 0.00, 0.28), mira=(1, 0, -0.15),
        res={'scrappy': (640, 480), 'industrial': (1280, 720),
             'produccion': (1440, 1080), 'maximo': (1440, 1080)},
        fov=120, sigue_uñas=True, nota='verifica que agarró el maxicubo correcto'),

    'cam_reversa': dict(
        tipo='camara', desde='produccion',
        montaje=(-1.20, 0.00, 1.20), mira=(-1, 0, -0.25),
        res={'produccion': (1280, 720), 'maximo': (1920, 1080)},
        fov=150, nota='sólo hace falta cuando la máquina se maneja sola'),
}

# ruido: lo que separa un dataset bonito de uno que se parece a la realidad
RUIDO = {
    'ideal': dict(lidar_sigma=0.000, dropout=0.00, cam_blur=0.0),
    'real':  dict(lidar_sigma=0.020, dropout=0.02, cam_blur=0.4),
    'alto':  dict(lidar_sigma=0.045, dropout=0.06, cam_blur=1.0),
}[A.ruido]

def activo(s):
    """¿este sensor existe en el nivel pedido?"""
    return NIVELES.index(A.nivel) >= NIVELES.index(s['desde'])

def por_nivel(d, defecto=None):
    """toma el valor del nivel actual, o el más alto disponible por debajo"""
    if not isinstance(d, dict): return d
    for n in NIVELES[NIVELES.index(A.nivel)::-1]:
        if n in d: return d[n]
    return defecto

# ─────────────────────────────────────────────────────────────────────────────
# 2 · ESCENA
# ─────────────────────────────────────────────────────────────────────────────
world = World(stage_units_in_meters=1.0)
add_reference_to_stage(usd_path=A.usd, prim_path="/World/Almacen")

stage = omni.usd.get_context().get_stage()

# El montacargas: por ahora un cuerpo rígido con las cotas reales del Baoli KBE 20.
# La articulación (dirección trasera + mástil) se arma en la fase 2 — ver abajo.
FK = dict(L=2.29, W=1.147, WB=1.50, FLEN=1.07, ALTO=2.177, LIFT=3.0)

# Pasillo norte de la nave este. Medido sobre la geometria del USD, no sobre los
# centros de slot: la fila 1 termina en y=5.21 y la fila 0 empieza en y=10.75,
# o sea 5.54 m libres (coincide con la ficha) y eje en y=7.98.
# Las bahias corren de x=45.6 a x=64.8, asi que x=58 es MITAD de pasillo.
SPAWN = (58.0, 7.98, 0.0)

# El cuerpo rigido va en el Xform padre y la colision en la geometria hija.
# Asi los sensores, que cuelgan de /World/Montacargas, se mueven CON el chasis.
# (Antes el RigidBodyAPI estaba en el Cube y los sensores eran sus hermanos:
#  la fisica movia el cubo y dejaba los sensores flotando en el aire.)
chasis = create_prim("/World/Montacargas", "Xform",
                     position=Gf.Vec3d(*SPAWN), orientation=None)
cuerpo = create_prim("/World/Montacargas/Chasis", "Cube",
                     attributes={"size": 1.0},
                     scale=Gf.Vec3d(FK['L'], FK['W'], FK['ALTO']),
                     position=Gf.Vec3d(0, 0, FK['ALTO'] / 2))
UsdPhysics.RigidBodyAPI.Apply(stage.GetPrimAtPath("/World/Montacargas"))
UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath("/World/Montacargas/Chasis"))

# ─────────────────────────────────────────────────────────────────────────────
# 3 · MONTAJE DE SENSORES
# ─────────────────────────────────────────────────────────────────────────────
montados, omitidos, camaras = {}, [], []

if A.sin_sensores:
    omitidos = list(SENSORES)
else:
    # Import diferido a proposito: si el namespace de sensores cambia entre
    # versiones de Isaac, --sin-sensores tiene que seguir arrancando igual.
    from isaacsim.sensors.experimental.rtx import Lidar
    from isaacsim.sensors.camera import Camera

    for nombre, s in SENSORES.items():
        if not activo(s):
            omitidos.append(nombre)
            continue
        ruta = f"/World/Montacargas/{nombre}"

        if s['tipo'] == 'lidar':
            montados[nombre] = Lidar.create(
                path=ruta,
                config=por_nivel(s['config'], 'Example_Rotary'),
                tick_rate=float(por_nivel(s['hz'], 10)),
                translations=[list(s['montaje'])],
            )
        else:
            w, h = por_nivel(s['res'], (1280, 720))
            cam = Camera(prim_path=ruta, resolution=(w, h),
                         position=np.array(s['montaje']), frequency=20)
            # OJO: initialize() NO va aca. La camara no tiene backend de render
            # hasta que el World se resetea; llamarlo antes revienta el arranque.
            montados[nombre] = cam
            camaras.append((cam, s))

print(f"\n{'='*66}")
_modo = 'SIN SENSORES (solo bodega + montacargas)' if A.sin_sensores else f"nivel '{A.nivel}' · ruido '{A.ruido}'"
print(f"  TaTa · banco de pruebas — {_modo}")
print(f"{'='*66}")
print(f"  montados ({len(montados)}): {', '.join(montados) or '—'}")
print(f"  omitidos ({len(omitidos)}): {', '.join(omitidos) or '—'}")
print(f"  ruido lidar σ={RUIDO['lidar_sigma']} m · dropout {RUIDO['dropout']*100:.0f}%")
print(f"{'='*66}\n")

# ─────────────────────────────────────────────────────────────────────────────
# 4 · LO QUE FALTA — hoja de ruta dentro del propio archivo
# ─────────────────────────────────────────────────────────────────────────────
# FASE 2 · articulación real del montacargas
#   - dirección en la rueda TRASERA (θ̇ = -(v/WB)·tan(δ)), ya validada en el visor web
#   - mástil prismático 0→3.0 m que arrastre cam_mastil y cam_uñas
#   - uñas con joint prismático para separación
#
# FASE 3 · el experimento que de verdad importa (ver README_SIM.md)
#   - correr SLAM sólo con lidar3d por un pasillo de 17 bahías
#   - medir deriva longitudinal: es el modo de falla clásico del pasillo uniforme
#   - si deriva, agregar AprilTags en cabecera y volver a medir → dice cuántos marcadores
#
# FASE 4 · ablación
#   - correr la misma misión en los 4 niveles y tabular qué se rompe en cada uno
#   - ese cuadro ES la justificación del BOM frente a Omar
#
# FASE 5 · ROS 2
#   - publicar /scan, /points, /camera/* y cerrar el lazo con Nav2

world.reset()

# Recien ahora las camaras tienen backend valido.
for cam, s in camaras:
    cam.initialize()
    cam.set_focal_length(24.0 / max(1e-3, (s['fov'] / 60.0)))

# Encuadre inicial: mirando el montacargas desde la boca del pasillo.
if not A.headless:
    set_camera_view(eye=[SPAWN[0] - 14.0, SPAWN[1] - 5.0, 6.0],
                    target=[SPAWN[0], SPAWN[1], 1.0])

paso = 0
try:
    while sim_app.is_running():
        world.step(render=not A.headless)
        paso += 1
        if paso % 600 == 0:
            print(f"  paso {paso} · t={world.current_time:.1f}s")
finally:
    sim_app.close()
