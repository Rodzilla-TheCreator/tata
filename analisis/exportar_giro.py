# Exporta las trayectorias reales del planificador para que el visor las reproduzca.
#
# Antes el visor interpolaba el rumbo y dejaba x,z congelados: eso es un giro
# sobre el propio eje, que un reach truck de direccion trasera no puede hacer.
# Aca se saca el camino de verdad, con sus cambios de sentido, y se guarda
# normalizado al origen para que el visor lo pegue donde haga falta.
#
# Salida: datos/giro_trayectorias.json
import io, json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = io.open(os.path.join(BASE, 'analisis', 'planificador_giro.py'),
              encoding='utf-8').read().split('print(f"silueta:')[0]
M = {}
exec(compile(src, 'planificador_giro', 'exec'), M)

HALF, plan, libre, silueta = M['HALF'], M['plan'], M['libre'], M['silueta']

# Carriles a exportar. El visor elige el mas cercano al que tenga la unidad.
CARRILES = [75, 85, 95, 110, 125, 145]
SIL = silueta(0.30)


def camino(idx, nodos):
    """Reconstruye la secuencia de poses desde el nodo final hasta la raiz."""
    out = []
    while idx is not None:
        p, padre, ult = nodos[idx]
        out.append((p, ult))
        idx = padre
    return out[::-1]


def densificar(a, b, sub=8):
    """Subdivide un tramo del A*. Cada arista es de curvatura constante, asi que
       el arco se reconstruye exacto en vez de interpolar recto entre nodos."""
    x0, z0, t0 = a
    x1, z1, t1 = b
    dth = t1 - t0
    if abs(dth) < 1e-7:                       # tramo recto
        return [[x0 + (x1 - x0) * i / sub,
                 z0 + (z1 - z0) * i / sub,
                 t0] for i in range(1, sub + 1)]
    # largo de arco con signo, despejado de la propia geometria del tramo
    den = math.sin(t1) - math.sin(t0)
    s = ((x1 - x0) * dth / den) if abs(den) > 1e-9 else \
        ((z1 - z0) * dth / (math.cos(t0) - math.cos(t1)))
    k = dth / s
    out = []
    for i in range(1, sub + 1):
        u = s * i / sub
        th = t0 + k * u
        out.append([x0 + (math.sin(th) - math.sin(t0)) / k,
                    z0 - (math.cos(th) - math.cos(t0)) / k,
                    th])
    return out


def exportar(cm):
    lane = -(HALF - cm / 100.0)
    p0 = (0.0, lane, 0.0)
    if not libre(p0, SIL):
        return None
    g, rev, idx, nodos = plan(p0, math.pi / 2, SIL)
    if g is None:
        return None
    cam = camino(idx, nodos)
    x0, z0, th0 = cam[0][0]

    crudo = [cam[0][0]]
    sent = [0 if cam[0][1] is None else int(cam[0][1])]
    for i in range(1, len(cam)):
        tramo = densificar(cam[i - 1][0], cam[i][0])
        crudo += tramo
        s_i = 0 if cam[i][1] is None else int(cam[i][1])
        sent += [s_i] * len(tramo)

    pts = [[round(x - x0, 4), round(z - z0, 4), round(t - th0, 5)]
           for x, z, t in crudo]
    return dict(carril=cm, largo=round(g, 3), cambios=rev,
                pts=pts, sentidos=sent, n=len(pts))


res = []
for cm in CARRILES:
    r = exportar(cm)
    if r:
        res.append(r)
        print(f"  carril {cm:3d} cm -> {r['n']:3d} poses · {r['largo']:.2f} m · "
              f"{r['cambios']} cambio(s) de sentido")
    else:
        print(f"  carril {cm:3d} cm -> sin solucion")

if not res:
    print('ninguna trayectoria: no se escribe nada')
    sys.exit(1)

out = os.path.join(BASE, 'datos', 'giro_trayectorias.json')
io.open(out, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(dict(carriles=res), separators=(',', ':')))
print(f"\nescrito {out} · {os.path.getsize(out)/1024:.1f} KB")
