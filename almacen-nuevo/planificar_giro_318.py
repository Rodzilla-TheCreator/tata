# ─────────────────────────────────────────────────────────────────────────────
# Giro de 90° del EDR18N2 en el pasillo de 3.18 m del almacén nuevo
#
# Diferencia con analisis/planificador_giro.py: aquí la silueta SÍ trae las
# uñas (punta a 2.90 m del culo). Ese planificador es solo chasis.
#
# Modelo: pivote en el eje de ruedas de carga, rueda de tracción/dirección
# atrás a WB. Cotas de CLAUDE.md («Corregido en campo»):
#   XPIV 1.50 (derivado) · WB 1.562 · W_MAX 1.315 · W_CAPO 1.065 · FLEN 1.20
#   δmax 78° · largo con uñas 2.90 (2.91 medido)
#
# Salida: almacen-nuevo/giro_318.json con la trayectoria de pasillo → cara del rack.
# ─────────────────────────────────────────────────────────────────────────────
import math, heapq, json, sys, os

AISLE = 3.18
MARGEN = 0.05              # holgura mínima contra la cara del rack en toda la maniobra
XPIV, WB, LCH, FLEN = 1.50, 1.562, 1.70, 1.20
W_MAX, W_CAPO = 1.315, 1.065
DMAX = math.radians(78)

A_CULO = -XPIV
A_MAST = -(XPIV - LCH)          # +0.20
A_PUNTA = A_MAST + FLEN         # +1.40  → largo total 2.90

def silueta():
    hc, hp = W_CAPO/2, W_MAX/2
    P = [(A_CULO, hc), (A_MAST, hc), (A_MAST, hp), (A_MAST+.9, hp),
         (A_MAST+.9, -hp), (A_MAST, -hp), (A_MAST, -hc), (A_CULO, -hc)]
    for s in (1, -1):                       # uñas: 0.13 de ancho, centro a ±0.30
        for e in (0.235, 0.365):
            P += [(A_PUNTA, s*e)]
    return P
SIL = silueta()

def huella(p):
    c, s = math.cos(p[2]), math.sin(p[2])
    return [(p[0]+a*c-l*s, p[1]+a*s+l*c) for a, l in SIL]

def holgura(p):
    ys = [q[1] for q in huella(p)]
    return min(min(ys), AISLE-max(ys))

def step(p, ds, d):
    dth = (ds/WB)*math.tan(d); th2 = p[2]+dth*.5
    return (p[0]+ds*math.cos(th2), p[1]+ds*math.sin(th2), p[2]+dth)

DS = 0.04; N_SUB = 5
STEERS = [DMAX*k for k in (-1, -.5, 0, .5, 1)]

def meta(p):
    """De frente al rack de arriba (θ=90°), punta de uña a 8–15 cm de la cara."""
    if abs(p[2]-math.pi/2) > math.radians(1.5): return False
    gap = AISLE - (p[1]+A_PUNTA)
    return 0.05 <= gap <= 0.15

def plan(y0):
    start = (0.0, y0, 0.0)
    if holgura(start) < MARGEN: return None
    key = lambda p, dr: (round(p[0]/.08), round(p[1]/.04), round(p[2]/math.radians(3)), dr)
    H = lambda p: abs(math.pi/2-p[2])*0.9 + abs((AISLE-0.10-A_PUNTA)-p[1])
    pq = [(H(start), 0.0, 0, start, 1, None)]; seen = {}; cnt = 1; nodes = {}
    while pq and cnt < 200000:
        f, g, nid, p, dr, par = heapq.heappop(pq)
        k = key(p, dr)
        if k in seen: continue
        seen[k] = 1; nodes[nid] = (p, par, dr)
        if meta(p):
            path = []; n = nid
            while n is not None:
                q, pr, d2 = nodes[n]; path.append((q, d2)); n = pr
            return path[::-1]
        for d in STEERS:
            for nd in (1, -1):
                q = p; ok = True
                for _ in range(N_SUB):
                    q = step(q, nd*DS/N_SUB, d)
                    if holgura(q) < MARGEN: ok = False; break
                if not ok: continue
                c = DS + (0.6 if nd != dr else 0) + (0.05 if nd < 0 else 0)
                heapq.heappush(pq, (g+c+H(q), g+c, cnt, q, nd, nid)); cnt += 1
    return None

def densificar(path):
    """Reconstruye la trayectoria fina reproduciendo el control entre nodos."""
    out = [path[0][0]]
    for (a, _), (b, _) in zip(path, path[1:]):
        out.append(b)
    return out

if __name__ == "__main__":
    mejor = None
    for y0 in [i/100 for i in range(100, 220, 5)]:
        r = plan(y0)
        if not r: continue
        n_rev = sum(1 for (_, a), (_, b) in zip(r, r[1:]) if a != b)
        largo = len(r)*DS
        hmin = min(holgura(q) for q, _ in r)
        print(f"carril pivote y0={y0:.2f}  cambios de sentido={n_rev}  recorrido={largo:.2f} m  holgura mín={hmin*100:.1f} cm")
        cand = (n_rev, largo, -hmin, y0, r)
        if mejor is None or cand[:3] < mejor[:3]: mejor = cand
    if not mejor: sys.exit("No hay giro de 90° en este pasillo con esta silueta")
    n_rev, largo, nh, y0, r = mejor
    poses = [[round(q[0], 4), round(q[1], 4), round(q[2], 5), d] for q, d in r]
    out = dict(aisle=AISLE, margen=MARGEN, y0=y0, cambios_sentido=n_rev,
               recorrido=round(largo, 2), holgura_min=round(-nh, 3), poses=poses)
    with open(os.path.join(os.path.dirname(__file__), "giro_318.json"), "w") as f:
        json.dump(out, f)
    print(f"\nELEGIDO y0={y0:.2f}: {n_rev} cambios de sentido, {largo:.2f} m, holgura mín {-nh*100:.1f} cm")
