# ─────────────────────────────────────────────────────────────────────────────
# TaTa · banco de pasillo — cámaras + ArUco
#
# No es la bodega completa (PropuestaIT_RETHINK.usda): es un pasillo aislado,
# a propósito, para estresar cámara+ArUco sin pagar el GPU de 790 ubicaciones.
#
# Medidas reales, no inventadas (CLAUDE.md / docs/02 / docs/09):
#   AISLE = 3.00   luz del pasillo, dato de campo, no de plano
#   BAY   = 1.30   luz entre parales (espaciado de columna de rack)
#   RACKD = 1.10   fondo del rack
#
# Propósito del pasillo: es donde el EDR18N2 navega entre bahías. La
# localización la dan DOS CÁMARAS con ArUco + odometría (docs/03) — el LiDAR
# no navega acá, solo vigila. Por eso este banco monta cam_frontal + cam_lateral
# (no lidar) y siembra ArUco en las dos cabeceras (identidad de pasillo) más
# marcas repartidas en una fila, a --espaciado, para el experimento de
# "cuántos marcadores hacen falta" de docs/03.
#
# Uso:
#   ./python.sh pasillo_aruco.py --espaciado 2.60 --headless --capturas
# ─────────────────────────────────────────────────────────────────────────────
import argparse, os, sys, json

HERE = os.path.dirname(__file__)

ap = argparse.ArgumentParser()
ap.add_argument('--largo', type=float, default=12.0, help='m de pasillo a modelar')
ap.add_argument('--espaciado', type=float, default=2.60, help='separación entre ArUco de fila, en m')
ap.add_argument('--marca', type=float, default=0.15, help='lado del ArUco, en m (docs/02: 15-20cm sobra)')
ap.add_argument('--velocidad', type=float, default=1.5, help='m/s de tránsito (docs: sobre de 1.5 m/s)')
ap.add_argument('--headless', action='store_true')
ap.add_argument('--capturas', action='store_true', help='guarda PNG de cada cámara cada 0.5 m')
ap.add_argument('--out', default=os.path.join(HERE, 'runs', 'pasillo_aruco'))
A = ap.parse_args()

AISLE, BAY, RACKD = 3.00, 1.30, 1.10
NCOL = max(2, int(A.largo // BAY))
LARGO = NCOL * BAY

os.makedirs(A.out, exist_ok=True)

from isaacsim import SimulationApp
sim_app = SimulationApp({"headless": A.headless, "renderer": "RayTracedLighting"})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.prims import create_prim
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.sensors.camera import Camera
from isaacsim.core.utils.rotations import lookat_to_quatf, gf_quat_to_np_array
import omni.usd
from pxr import Gf, UsdGeom, UsdShade, UsdPhysics, UsdLux, Sdf

world = World(stage_units_in_meters=1.0)
stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

# sin esto RTX renderiza negro puro, tenga o no geometría/textura: no hay luz por defecto
UsdLux.DomeLight.Define(stage, "/World/Luz_domo").CreateIntensityAttr(1000)
sol = UsdLux.DistantLight.Define(stage, "/World/Luz_sol")
sol.CreateIntensityAttr(3000)
sol.CreateAngleAttr(1.0)
UsdGeom.Xformable(sol).AddRotateXOp().Set(-55)

# ── piso ────────────────────────────────────────────────────────────────────
create_prim("/World/Piso", "Cube", attributes={"size": 1.0},
            scale=Gf.Vec3d(LARGO + 4, AISLE + 2 * RACKD + 4, 0.05),
            position=Gf.Vec3d(LARGO / 2, 0, -0.025))
UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath("/World/Piso"))

# ── las dos filas de rack, como paredes continuas a RACKD de fondo ──────────
# Geometría simplificada (no BOM completo): lo que importa para este banco es
# que el ArUco quede sobre una cara plana a la altura de montaje de cámara,
# no la estructura del parante.
ALTO_RACK = 2.60  # cubre hasta nivel 2 (docs/02: nivel 2 en 2.15 m de viga)
for lado, y_cara in (("izq", AISLE / 2), ("der", -AISLE / 2)):
    y_centro = y_cara + (RACKD / 2 if lado == "izq" else -RACKD / 2)
    create_prim(f"/World/Rack_{lado}", "Cube", attributes={"size": 1.0},
                scale=Gf.Vec3d(LARGO, RACKD, ALTO_RACK),
                position=Gf.Vec3d(LARGO / 2, y_centro, ALTO_RACK / 2))
    UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath(f"/World/Rack_{lado}"))

# ── material con textura, uno por imagen (cada ArUco es un ID distinto) ─────
_mat_cache = {}
def material_textura(img_path):
    if img_path in _mat_cache:
        return _mat_cache[img_path]
    nombre = os.path.splitext(os.path.basename(img_path))[0]
    mat_path = f"/World/Materiales/{nombre}"
    material = UsdShade.Material.Define(stage, mat_path)
    tex = UsdShade.Shader.Define(stage, f"{mat_path}/Textura")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(img_path)
    tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
    tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
    tex_out = tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    st_reader = UsdShade.Shader.Define(stage, f"{mat_path}/STReader")
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        st_reader.ConnectableAPI(), "result")

    surf = UsdShade.Shader.Define(stage, f"{mat_path}/Superficie")
    surf.CreateIdAttr("UsdPreviewSurface")
    surf.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        tex.ConnectableAPI(), "rgb")
    surf.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.9)
    surf.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(surf.ConnectableAPI(), "surface")
    _mat_cache[img_path] = material
    return material

def marcador_aruco(path, id_marca, pos, rot_z_deg, lado_m):
    img = os.path.join(HERE, "assets", "aruco", f"aruco_{id_marca:02d}.png")
    if not os.path.exists(img):
        print(f"  [aviso] falta {img}, se omite {path}")
        return
    mesh = UsdGeom.Mesh.Define(stage, path)
    h = lado_m / 2
    mesh.CreatePointsAttr([(0, -h, -h), (0, h, -h), (0, h, h), (0, -h, h)])
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    mesh.CreateExtentAttr([(0, -h, -h), (0, h, h)])
    mesh.CreateDoubleSidedAttr(True)
    st = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    st.Set([(0, 0), (1, 0), (1, 1), (0, 1)])
    xf = UsdGeom.Xformable(mesh)
    xf.AddTranslateOp().Set(Gf.Vec3d(*pos))
    xf.AddRotateZOp().Set(rot_z_deg)
    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material_textura(img))

# alto de montaje del ArUco: a media altura del nivel 1 de trabajo (docs/02: 0.70)
Z_MARCA = 0.90

# cabeceras: identidad de pasillo, mirando A LO LARGO del pasillo (eje X),
# una en cada boca — es lo que ve cam_frontal desde lejos al entrar (docs/03).
marcador_aruco("/World/Aruco/cabecera_entrada", 10, (0.05, 0, Z_MARCA), 90, 0.20)
marcador_aruco("/World/Aruco/cabecera_fondo", 11, (LARGO - 0.05, 0, Z_MARCA), -90, 0.20)

# marcas de fila en el rack izquierdo, cada --espaciado, mirando AL PASILLO
# (eje Y) — es lo que ve cam_lateral. IDs 20+ para no chocar con cabeceras.
x = A.espaciado / 2
n_fila = 0
while x < LARGO:
    marcador_aruco(f"/World/Aruco/fila_{n_fila:02d}", 20 + n_fila,
                    (x, AISLE / 2 - 0.02, Z_MARCA), 180, A.marca)
    x += A.espaciado
    n_fila += 1

print(f"\n{'='*66}")
print(f"  pasillo: {LARGO:.2f} m × {AISLE:.2f} m libres · {n_fila} marcas de fila @ {A.espaciado} m")
print(f"  ArUco: 512px + 64px de quiet zone, DICT_4X4_50 (assets/aruco/)")
print(f"{'='*66}\n")

# ── chasis + cámaras (mismo montaje que tata_sim.py: cam_frontal real) ──────
SPAWN = (0.30, 0.0, 0.0)
create_prim("/World/Montacargas", "Xform", position=Gf.Vec3d(*SPAWN))
create_prim("/World/Montacargas/Chasis", "Cube", attributes={"size": 1.0},
            scale=Gf.Vec3d(1.70, 1.054, 2.177),
            position=Gf.Vec3d(0, 0, 2.177 / 2))
# Sin RigidBodyAPI a propósito: todavía no hay física (fase 2, ver cabecera del
# archivo). El recorrido es cinemático puro — poner RigidBodyAPI y sobrescribir
# la misma transformada a mano cada paso hace que PhysX y mi Set() se peleen por
# la pose del chasis, y de ahí cuelgan las cámaras.

def orientacion_mirando(direccion_local):
    """Cuaternión (w,x,y,z) para que la cámara, en el frame de su padre, mire hacia
    `direccion_local`. USD mira por defecto en -Z; lookat_to_quatf(objetivo, origen, up)
    calcula backward = origen - objetivo, así que el objetivo va PRIMERO."""
    objetivo = Gf.Vec3d(*direccion_local)
    origen = Gf.Vec3d(0.0, 0.0, 0.0)
    q = lookat_to_quatf(objetivo, origen, Gf.Vec3d(0, 0, 1))
    return gf_quat_to_np_array(q)

CAMARAS = {
    'cam_frontal': dict(montaje=(0.20, 0.00, 1.52), mira=(1, 0, 0), res=(1280, 800), fov=72,
                         nota='RealSense D455 — ve la cabecera al frente'),
    'cam_lateral': dict(montaje=(0.20, 0.45, 1.10), mira=(0, 1, 0), res=(1280, 800), fov=90,
                         nota='ve la cara del rack — la fila de ArUco'),
}
camaras = {}
for nombre, c in CAMARAS.items():
    # OJO: translation= (relativa al chasis), NUNCA position= — position fija la
    # cámara en el mundo y se desacopla del chasis cuando este se mueve. Mismo bug
    # que arrastra tata_sim.py, nunca se notó porque nadie miró una imagen.
    cam = Camera(prim_path=f"/World/Montacargas/{nombre}",
                 resolution=c['res'], translation=np.array(c['montaje']),
                 orientation=orientacion_mirando(c['mira']), frequency=20)
    camaras[nombre] = cam

world.reset()
APERTURA_H = 20.955  # mm, estándar Academy. El default del prim es 2.0955 —
                      # diez veces más chico — y con eso set_focal_length()
                      # calculaba un FOV real muy distinto del pedido.
for nombre, cam in camaras.items():
    cam.initialize()
    fov = CAMARAS[nombre]['fov']
    cam.set_horizontal_aperture(APERTURA_H)
    focal = APERTURA_H / (2 * np.tan(np.radians(fov / 2)))
    cam.set_focal_length(focal)
    print(f"  {nombre}: focal={focal:.1f}mm  FOV real "
          f"h={np.degrees(cam.get_horizontal_fov()):.1f}° "
          f"v={np.degrees(cam.get_vertical_fov()):.1f}°")

if not A.headless:
    set_camera_view(eye=[SPAWN[0] - 6, SPAWN[1] - 6, 4.0], target=[SPAWN[0] + 3, 0, 1.0])

# ── recorrido cinemático: cruzar el pasillo a A.velocidad, sin física todavía ─
chasis_prim = stage.GetPrimAtPath("/World/Montacargas")
xf_chasis = UsdGeom.Xformable(chasis_prim)
op_t = None
for op in xf_chasis.GetOrderedXformOps():
    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
        op_t = op
if op_t is None:
    op_t = xf_chasis.AddTranslateOp()

dt = 1.0 / 60.0
x_actual = SPAWN[0]
siguiente_captura = 0.0
manifest = []

def capturar(paso, x):
    global siguiente_captura
    if not A.capturas or x < siguiente_captura:
        return
    siguiente_captura = x + 0.5  # cada 0.5 m
    for nombre, cam in camaras.items():
        frame = cam.get_rgba()
        if frame is None or frame.size == 0:
            continue
        fn = os.path.join(A.out, f"{nombre}_x{x:05.2f}.png")
        import omni.replicator.core as rep  # noqa: F401 (solo para asegurar backend listo)
        try:
            from PIL import Image
            Image.fromarray(frame[:, :, :3]).save(fn)
        except Exception as e:
            np.save(fn.replace('.png', '.npy'), frame)
        manifest.append({"x": round(x, 2), "camara": nombre, "archivo": fn})

paso = 0
try:
    while sim_app.is_running() and x_actual < LARGO - 0.3:
        x_actual += A.velocidad * dt
        op_t.Set(Gf.Vec3d(x_actual, SPAWN[1], SPAWN[2]))
        world.step(render=True)
        capturar(paso, x_actual)
        paso += 1
        if paso % 120 == 0:
            print(f"  paso {paso} · x={x_actual:.2f} m / {LARGO:.2f} m")
finally:
    if A.capturas:
        with open(os.path.join(A.out, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  {len(manifest)} capturas en {A.out}")
    sim_app.close()
