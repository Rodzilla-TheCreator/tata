# Diagnóstico aislado: ¿se ve UNA marca ArUco desde 1 m de frente? Sin pasillo,
# sin chasis moviéndose — solo para separar "no renderiza" de "no detecta".
import os, numpy as np
from isaacsim import SimulationApp
sim_app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})

from isaacsim.core.api import World
from isaacsim.core.utils.prims import create_prim
from isaacsim.sensors.camera import Camera
from isaacsim.core.utils.rotations import lookat_to_quatf, gf_quat_to_np_array
import omni.usd
from pxr import Gf, UsdGeom, UsdShade, UsdLux, Sdf

HERE = os.path.dirname(__file__)
world = World(stage_units_in_meters=1.0)
stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

UsdLux.DomeLight.Define(stage, "/World/Luz_domo").CreateIntensityAttr(1000)
sol = UsdLux.DistantLight.Define(stage, "/World/Luz_sol")
sol.CreateIntensityAttr(3000)
sol.CreateAngleAttr(1.0)
UsdGeom.Xformable(sol).AddRotateXOp().Set(-55)

img_path = os.path.join(HERE, "assets", "aruco", "aruco_10.png")
print("existe imagen:", os.path.exists(img_path), img_path)

mat_path = "/World/Mat"
material = UsdShade.Material.Define(stage, mat_path)
tex = UsdShade.Shader.Define(stage, f"{mat_path}/Textura")
tex.CreateIdAttr("UsdUVTexture")
tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(img_path))
tex.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
tex.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
st_reader = UsdShade.Shader.Define(stage, f"{mat_path}/STReader")
st_reader.CreateIdAttr("UsdPrimvarReader_float2")
st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(st_reader.ConnectableAPI(), "result")
surf = UsdShade.Shader.Define(stage, f"{mat_path}/Superficie")
surf.CreateIdAttr("UsdPreviewSurface")
surf.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(), "rgb")
material.CreateSurfaceOutput().ConnectToSource(surf.ConnectableAPI(), "surface")

lado = 0.30
mesh = UsdGeom.Mesh.Define(stage, "/World/Marca")
h = lado / 2
mesh.CreatePointsAttr([(0, -h, -h), (0, h, -h), (0, h, h), (0, -h, h)])
mesh.CreateFaceVertexCountsAttr([4])
mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
mesh.CreateExtentAttr([(0, -h, -h), (0, h, h)])
mesh.CreateDoubleSidedAttr(True)
mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
mesh.CreateNormalsAttr([(1, 0, 0)] * 4)
mesh.SetNormalsInterpolation(UsdGeom.Tokens.constant)
st = UsdGeom.PrimvarsAPI(mesh.GetPrim()).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
st.Set([(0, 0), (1, 0), (1, 1), (0, 1)])
UsdGeom.Xformable(mesh).AddTranslateOp().Set(Gf.Vec3d(1.0, 0, 1.0))
UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)
print("marca en", mesh.GetPrim().GetPath(), "puntos:", mesh.GetPointsAttr().Get())

# control: un cubo simple sin textura, al lado, para saber si el problema es
# del Mesh a mano o de algo mas general del render headless
create_prim("/World/CuboControl", "Cube", attributes={"size": 1.0},
            scale=Gf.Vec3d(0.3, 0.3, 0.3), position=Gf.Vec3d(1.0, 0.0, 0.5))
mat_rojo = UsdShade.Material.Define(stage, "/World/MatRojo")
surf_rojo = UsdShade.Shader.Define(stage, "/World/MatRojo/Superficie")
surf_rojo.CreateIdAttr("UsdPreviewSurface")
surf_rojo.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1.0, 0.0, 0.0))
mat_rojo.CreateSurfaceOutput().ConnectToSource(surf_rojo.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(stage.GetPrimAtPath("/World/CuboControl")).Bind(mat_rojo)

cam = Camera(prim_path="/World/Cam", resolution=(800, 800),
             translation=np.array([0.0, 0.0, 1.0]),
             orientation=gf_quat_to_np_array(
                 lookat_to_quatf(Gf.Vec3d(1, 0, 0), Gf.Vec3d(0, 0, 0), Gf.Vec3d(0, 0, 1))),
             frequency=20)

world.reset()
cam.initialize()
cam.set_horizontal_aperture(20.955)
cam.set_focal_length(20.955 / (2 * np.tan(np.radians(60 / 2))))  # ~60° FOV
print("FOV real:", np.degrees(cam.get_horizontal_fov()))
for _ in range(30):
    world.step(render=True)

frame = cam.get_rgba()
print("frame shape:", None if frame is None else frame.shape, "max:", None if frame is None else frame.max())
from PIL import Image
Image.fromarray(frame[:, :, :3]).save(os.path.join(HERE, "runs", "debug_una_marca.png"))
print("guardado en runs/debug_una_marca.png")
sim_app.close()
