import json, collections
d = json.load(open('propuesta_it.json'))
CX, CY = d['CX'], d['CY']
tx = lambda X: X - CX          # igual que el visor
tz = lambda Y: -(Y - CY)
BAY, DEP, PITCH, CUBE_H = 1.20, 1.00, d['LEVEL_PITCH'], d['CUBE_H']
LOAD_W, LOAD_D = d['LOAD_W'], d['LOAD_D']

# three.js es Y-arriba; USD/Isaac es Z-arriba. (x,y,z) -> (x, -z, y)
def P(x, y, z): return (round(x,4), round(-z,4), round(y,4))

# --- filas y niveles: se agrupan POR NAVE, porque las dos comparten rango de z ---
slots = d['pslots']
niveles = sorted({round(s['y'],2) for s in slots})
naves = []
for sa in d['salas']:
    naves.append({'nom': sa['nom'], 'x0': min(tx(sa['x0']), tx(sa['x1'])),
                  'x1': max(tx(sa['x0']), tx(sa['x1']))})
def naveDe(s):
    for i, n in enumerate(naves):
        if n['x0'] - 1 <= s['x'] <= n['x1'] + 1: return i
    return 0
porFila, filas = collections.defaultdict(list), []
for i, n in enumerate(naves):
    ss = [s for s in slots if naveDe(s) == i]
    zs = sorted({round(s['z'],2) for s in ss})
    gr = []
    for z in zs:
        if not gr or abs(z - gr[-1][-1]) > 0.5: gr.append([z])
        else: gr[-1].append(z)
    for g in gr:
        zc = sum(g)/len(g); k = len(filas); filas.append(zc)
        porFila[k] = [s for s in ss if abs(s['z'] - zc) < 0.5]
    print(f"  {n['nom']}: {len(gr)} filas, {len(ss)} ubicaciones")
print('filas de rack:', len(filas), '| niveles:', len(niveles), niveles)

prims, insta = [], []

def cubo(name, cx, cy, cz, sx, sy, sz, colision=True, color=(.55,.58,.62)):
    px, py, pz = P(cx, cy, cz)
    # el tamaño se remapea igual que la posición: (sx, sz, sy)
    # UsdPhysics crea el collider a partir del Gprim, no del Xform que lo contiene:
    # si la API se aplica al Xform, PhysX no genera nada y todo se vuelve atravesable.
    _api = ' (prepend apiSchemas = ["PhysicsCollisionAPI"])' if colision else ''
    prims.append(f'''
    def Xform "{name}"
    {{
        double3 xformOp:translate = ({px}, {py}, {pz})
        double3 xformOp:scale = ({round(sx,4)}, {round(sz,4)}, {round(sy,4)})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
        def Cube "geo"{_api} {{
            double size = 1
            float3[] extent = [(-0.5,-0.5,-0.5), (0.5,0.5,0.5)]
            color3f[] primvars:displayColor = [({color[0]}, {color[1]}, {color[2]})]
        }}
    }}''')

# piso del sector C
x0, x1 = tx(838.0), tx(945.0)
z0, z1 = tz(-756.0), tz(-848.0)
cx, cz = (x0+x1)/2, (z0+z1)/2
cubo('Piso', cx, -0.05, cz, abs(x1-x0), 0.1, abs(z1-z0), color=(.30,.32,.34))

# muros del sector C
for i, (ax, ay, bx, by) in enumerate(d['muros']):
    X0, Z0, X1, Z1 = tx(ax), tz(ay), tx(bx), tz(by)
    L = ((X1-X0)**2 + (Z1-Z0)**2) ** .5
    if L < 0.15: continue
    if abs(X1-X0) >= abs(Z1-Z0):
        cubo(f'Muro_{i}', (X0+X1)/2, 3.0, (Z0+Z1)/2, L, 6.0, 0.20, color=(.62,.64,.66))
    else:
        cubo(f'Muro_{i}', (X0+X1)/2, 3.0, (Z0+Z1)/2, 0.20, 6.0, L, color=(.62,.64,.66))

# estructura de rack: montantes + vigas por fila
for fi, zc in enumerate(filas):
    ss = porFila[fi]
    if not ss: continue
    xs = sorted({round(s['x'],2) for s in ss})
    xmin, xmax = min(xs)-BAY/2, max(xs)+BAY/2
    alto = niveles[-1] + PITCH
    for j, xu in enumerate([xmin] + [x+BAY/2 for x in xs]):
        cubo(f'RackPost_{fi}_{j}', xu, alto/2, zc, 0.09, alto, DEP, color=(.18,.35,.62))
    for k, yv in enumerate(niveles):
        cubo(f'RackBeam_{fi}_{k}', (xmin+xmax)/2, yv-0.06, zc, xmax-xmin, 0.10, DEP, color=(.85,.45,.12))

# maxicubos: PointInstancer (790 posiciones, mucho más liviano)
pos = [P(s['x'], s['y']+CUBE_H/2, s['z']) for s in slots]
pts = ', '.join(f'({p[0]}, {p[1]}, {p[2]})' for p in pos)
insta.append(f'''
    def PointInstancer "Maxicubos"
    {{
        point3f[] positions = [{pts}]
        int[] protoIndices = [{', '.join('0' for _ in pos)}]
        rel prototypes = </World/Almacen/Maxicubos/Proto/Cubo>
        def Scope "Proto" {{
            def Xform "Cubo" {{
                double3 xformOp:scale = ({LOAD_W}, {LOAD_D}, {CUBE_H})
                uniform token[] xformOpOrder = ["xformOp:scale"]
                def Cube "geo" (prepend apiSchemas = ["PhysicsCollisionAPI"]) {{
                    double size = 1
                    float3[] extent = [(-0.5,-0.5,-0.5), (0.5,0.5,0.5)]
                    color3f[] primvars:displayColor = [(0.78, 0.80, 0.83)]
                }}
            }}
        }}
    }}''')

usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
    doc = "TaTa · Propuesta IT (sector C) del almacen RETHINK — {len(slots)} ubicaciones, {len(filas)} filas de rack"
)

def Xform "World"
{{
    def Xform "Almacen"
    {{{''.join(prims)}{''.join(insta)}
    }}
}}
'''
open('PropuestaIT_RETHINK.usda','w').write(usda)
print('USD escrito:', len(usda)//1024, 'KB | prims:', len(prims), '| instancias:', len(pos))
