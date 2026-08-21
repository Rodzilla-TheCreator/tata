# ─────────────────────────────────────────────────────────────────────────────
# TaTa · banco comparativo de LiDAR — Isaac Sim 6.0
#
# Monta VARIOS LiDAR a la vez en el mismo montacargas y recorre UNA trayectoria.
# Todos ven exactamente la misma escena en el mismo instante, así que las nubes
# quedan pareadas: la única variable es el sensor. Eso en la vida real sólo se
# consigue comprando los cinco.
#
#   ./python.sh tata_multilidar.py                       # todos, pasada completa
#   ./python.sh tata_multilidar.py --solo os0_128
#   ./python.sh tata_multilidar.py --headless --vel 0.8
# ─────────────────────────────────────────────────────────────────────────────
import argparse, json, os, time

ap = argparse.ArgumentParser()
ap.add_argument('--solo', default=None, help='correr un solo sensor por su clave')
ap.add_argument('--vel', type=float, default=1.0, help='m/s a lo largo del pasillo')
ap.add_argument('--pasillo', type=int, default=0, help='cuál pasillo de la Nave Este (0-4)')
ap.add_argument('--salida', default='capturas')
ap.add_argument('--headless', action='store_true')
ap.add_argument('--usd', default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'PropuestaIT_RETHINK.usda'))
A = ap.parse_args()

from isaacsim import SimulationApp
sim_app = SimulationApp({"headless": A.headless, "renderer": "RayTracedLighting"})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.prims import create_prim
from isaacsim.sensors.experimental.rtx import Lidar
import omni.usd
from pxr import Gf, UsdPhysics

# ─────────────────────────────────────────────────────────────────────────────
# LOS CANDIDATOS
#   'config' = perfil RTX. Los marcados PROPIO hay que escribirlos (ver README).
#   Todos van al MISMO punto de montaje para que la comparación sea limpia:
#   si cada uno va en un sitio distinto, no sabés si la diferencia es el sensor
#   o la posición.
# ─────────────────────────────────────────────────────────────────────────────
MONTAJE_TECHO = (0.0, 0.0, 2.15)      # techo de protección del Baoli KBE 20

CANDIDATOS = {
    'os0_128': dict(
        config='OS0_REV7_128ch10hz1024res', hz=10, montaje=MONTAJE_TECHO,
        precio=None, viene=True,
        nota='Ouster OS0-128 · viene de fábrica en Isaac · 90° vertical, 50 m. '
             'El "sensor optimista": si con éste degenera, degenera con todo.'),
    'os1_64': dict(
        config='OS1_REV7_64ch10hz1024res', hz=10, montaje=MONTAJE_TECHO,
        precio=12000, viene=True,
        nota='Ouster OS1-64 · nivel Tesla del BOM · 45° vertical, 120 m'),
    'hesai_xt32': dict(
        config='Hesai_XT32_SD10', hz=10, montaje=MONTAJE_TECHO,
        precio=4500, viene=True,
        nota='Hesai XT32 · aproximación al nivel Producción (RoboSense Helios)'),
    'rotativo_generico': dict(
        config='Example_Rotary', hz=10, montaje=MONTAJE_TECHO,
        precio=500, viene=True,
        nota='Genérico · sustituto del SLAMTEC/Unitree del nivel Taller'),
    'mid360': dict(
        config='Livox_Mid360', hz=10, montaje=MONTAJE_TECHO,
        precio=749, viene=False,
        nota='Livox Mid-360 · PERFIL PROPIO, patrón no repetitivo. '
             'El más barato del BOM y el más caro de simular.'),
    'nanoscan3_izq': dict(
        config='Example_Rotary_2D', hz=25, montaje=(0.55, 0.40, 0.15),
        precio=3500, viene=True,
        nota='SICK nanoScan3 · 2D de seguridad · el que decide los $7,000'),
    'nanoscan3_der': dict(
        config='Example_Rotary_2D', hz=25, montaje=(0.55, -0.40, 0.15),
        precio=3500, viene=True, nota='par del anterior'),
}

if A.solo:
    CANDIDATOS = {A.solo: CANDIDATOS[A.solo]}

# ─────────────────────────────────────────────────────────────────────────────
# TRAYECTORIA — los pasillos reales de la Nave Este (del USD)
# Recorre el pasillo de punta a punta y regresa. Ida y vuelta importa: si el
# SLAM está derivando, el error al volver al punto de partida lo delata.
# ─────────────────────────────────────────────────────────────────────────────
PASILLOS_NAVE_ESTE = [      # (x_inicio, x_fin, y) en metros, marco del USD
    (44.5, 70.0,  10.4), (44.5, 70.0,   3.6), (44.5, 70.0,  -3.2),
    (44.5, 70.0, -10.0), (44.5, 70.0, -16.8),
]
X0, X1, Y = PASILLOS_NAVE_ESTE[A.pasillo % len(PASILLOS_NAVE_ESTE)]
LARGO = X1 - X0
T_TRAMO = LARGO / A.vel
T_TOTAL = 2 * T_TRAMO + 2.0          # ida, vuelta, y un respiro al final

def pose_en(t):
    """Trayectoria guionada: sin control, sin ruido de piloto, 100% repetible."""
    if t < T_TRAMO:
        return X0 + A.vel * t, Y, 0.0
    if t < 2 * T_TRAMO:
        return X1 - A.vel * (t - T_TRAMO), Y, np.pi
    return X0, Y, np.pi

# ─────────────────────────────────────────────────────────────────────────────
world = World(stage_units_in_meters=1.0)
add_reference_to_stage(usd_path=A.usd, prim_path="/World/Almacen")
stage = omni.usd.get_context().get_stage()

FK = dict(L=2.29, W=1.147, ALTO=2.177)
create_prim("/World/Montacargas", "Xform", position=Gf.Vec3d(X0, Y, 0.0))
create_prim("/World/Montacargas/Chasis", "Cube", attributes={"size": 1.0},
            scale=Gf.Vec3d(FK['L'], FK['W'], FK['ALTO']),
            position=Gf.Vec3d(0, 0, FK['ALTO']/2))
UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath("/World/Montacargas/Chasis"))

os.makedirs(A.salida, exist_ok=True)
montados, faltantes = {}, []
for k, c in CANDIDATOS.items():
    if not c['viene']:
        faltantes.append(k); continue
    try:
        montados[k] = Lidar.create(path=f"/World/Montacargas/{k}",
                                   config=c['config'], tick_rate=float(c['hz']),
                                   translations=[list(c['montaje'])])
    except Exception as e:
        faltantes.append(k); print(f"  ! {k}: {e}")

print(f"\n{'='*72}")
print(f"  Banco comparativo de LiDAR · pasillo {A.pasillo} · {LARGO:.1f} m ida y vuelta")
print(f"{'='*72}")
for k in montados: print(f"  ✓ {k:20s} {CANDIDATOS[k]['nota'][:44]}")
for k in faltantes: print(f"  · {k:20s} PERFIL PENDIENTE — ver README_MULTILIDAR.md")
print(f"{'='*72}\n")

# ─────────────────────────────────────────────────────────────────────────────
world.reset()
verdad, t0 = [], time.time()
paso = 0
try:
    while sim_app.is_running():
        t = world.current_time
        if t > T_TOTAL: break
        x, y, th = pose_en(t)
        xf = stage.GetPrimAtPath("/World/Montacargas")
        xf.GetAttribute('xformOp:translate').Set(Gf.Vec3d(x, y, 0.0))
        verdad.append(dict(t=round(t,4), x=round(x,5), y=round(y,5), th=round(th,5)))
        world.step(render=True)
        paso += 1
        if paso % 120 == 0:
            print(f"  t={t:5.1f}s / {T_TOTAL:.1f}s   x={x:6.2f} m")
finally:
    with open(os.path.join(A.salida, 'verdad_de_terreno.json'), 'w') as f:
        json.dump(dict(pasillo=A.pasillo, x0=X0, x1=X1, y=Y, vel=A.vel,
                       sensores=list(montados), poses=verdad), f)
    print(f"\n  verdad de terreno → {A.salida}/verdad_de_terreno.json  ({len(verdad)} poses)")
    print("  las nubes salen por el Annotator de cada Lidar o por ROS 2 — ver README\n")
    sim_app.close()
