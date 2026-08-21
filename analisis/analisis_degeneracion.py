# ─────────────────────────────────────────────────────────────────────────────
# ¿Se desliza el SLAM a lo largo del pasillo? — cálculo analítico previo
#
# No necesita Isaac Sim. Reproduce en 2D la geometría real del pasillo de la
# Nave Este (17 bahías, 5.54 m) y calcula la MATRIZ DE INFORMACIÓN del emparejado
# de escaneos (point-to-plane ICP). Los autovalores dicen en qué dirección el
# LiDAR restringe la pose y en cuál no.
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np, json

BAHIAS, BAY = 17, 1.20
ANCHO = 5.54            # pasillo real de la Nave Este
POSTE = 0.09            # ancho del montante
SIGMA = 0.02            # ruido de rango del LiDAR, 2 cm
RANGO = 40.0            # alcance (Mid-360 / OS0)

def geometria(relieve=0.08, tapar_extremos=False, marcadores=0):
    """Devuelve segmentos [(ax,ay,bx,by)] del pasillo visto en planta."""
    S, L = [], BAHIAS * BAY
    for lado in (+1, -1):
        yP, yC = lado * ANCHO / 2, lado * (ANCHO / 2 + relieve)   # poste / carga
        for k in range(BAHIAS):
            x0 = k * BAY
            S += [(x0, yP, x0 + POSTE, yP)]                        # cara del poste
            S += [(x0 + POSTE, yP, x0 + POSTE, yC)]                # ── transición
            S += [(x0 + POSTE, yC, x0 + BAY, yC)]                  # cara de la carga
            S += [(x0 + BAY, yC, x0 + BAY, yP)]                    # ── transición
    if tapar_extremos:      # pared al fondo: el caso "pasillo cerrado"
        S += [(-0.2, -ANCHO/2, -0.2, ANCHO/2), (L + 0.2, -ANCHO/2, L + 0.2, ANCHO/2)]
    else:                   # pasillo abierto al transversal, pared a 4.5 m
        S += [(-4.5, -ANCHO/2, -4.5, ANCHO/2), (L + 4.5, -ANCHO/2, L + 4.5, ANCHO/2)]
    for i in range(marcadores):   # marcadores fiduciales: placas normales al pasillo
        xm = (i + 0.5) * L / marcadores
        for lado in (+1, -1):
            y = lado * ANCHO / 2
            S += [(xm - 0.15, y, xm - 0.15, y - lado * 0.25),
                  (xm + 0.15, y, xm + 0.15, y - lado * 0.25)]
    return np.array(S, float)

def escanear(O, S, nb=900):
    """Raycast 2D: devuelve puntos de impacto y normales."""
    th = np.linspace(0, 2*np.pi, nb, endpoint=False)
    D = np.stack([np.cos(th), np.sin(th)], 1)                     # (nb,2)
    A, B = S[:, :2], S[:, 2:]
    V2 = B - A                                                    # (ns,2)
    V1 = O[None, :] - A                                           # (ns,2)
    V3 = np.stack([-D[:, 1], D[:, 0]], 1)                         # (nb,2)
    den = V2 @ V3.T                                               # (ns,nb)
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (V2[:, 0:1]*V1[:, 1:2] - V2[:, 1:2]*V1[:, 0:1]) / den
        u = (V1 @ V3.T) / den
    ok = (np.abs(den) > 1e-9) & (t > 1e-3) & (t < RANGO) & (u >= 0) & (u <= 1)
    t = np.where(ok, t, np.inf)
    idx = np.argmin(t, 0); tm = t[idx, np.arange(nb)]
    v = np.isfinite(tm)
    if v.sum() < 10: return None, None
    P = O[None, :] + D[v] * tm[v, None]                           # impactos
    seg = S[idx[v]]
    d = seg[:, 2:] - seg[:, :2]; d /= np.linalg.norm(d, axis=1, keepdims=True)
    N = np.stack([-d[:, 1], d[:, 0]], 1)                          # normal
    hacia = O[None, :] - P
    N *= np.sign(np.einsum('ij,ij->i', N, hacia))[:, None]        # orientar al sensor
    return P, N

def informacion(O, S):
    """Matriz de información de Fisher del emparejado punto-a-plano."""
    P, N = escanear(O, S)
    if P is None: return None
    p = P - O[None, :]
    J = np.stack([N[:, 0], N[:, 1], N[:, 1]*p[:, 0] - N[:, 0]*p[:, 1]], 1)
    return (J.T @ J) / SIGMA**2

def evaluar(nom, **kw):
    S = geometria(**kw)
    L = BAHIAS * BAY
    xs = np.linspace(0.5, L - 0.5, 33)
    out = []
    for x in xs:
        H = informacion(np.array([x, 0.0]), S)
        if H is None: continue
        C = np.linalg.inv(H)
        sx, sy, st = np.sqrt(np.diag(C))          # desviación de la pose
        w = np.linalg.eigvalsh(H)
        out.append((x, sx*100, sy*100, np.degrees(st), w[0]/w[-1]))
    a = np.array(out)
    print(f"  {nom:38s}  σ_largo {a[:,1].mean():6.2f} cm (máx {a[:,1].max():6.2f})"
          f" · σ_ancho {a[:,2].mean():5.2f} cm · relación {a[:,1].mean()/a[:,2].mean():6.1f}×")
    return a

print("\n Incertidumbre de una sola pose, ruido de rango σ = 2 cm")
print(" 'largo' = a lo largo del pasillo (el eje del problema)\n")
R = {}
R['relieve 0.15 m']      = evaluar("rack con mucho relieve (0.15 m)", relieve=0.15)
R['relieve 0.08 m']      = evaluar("rack típico (relieve 0.08 m)",    relieve=0.08)
R['relieve 0.02 m']      = evaluar("rack casi liso (relieve 0.02 m)", relieve=0.02)
R['extremos tapados']    = evaluar("pasillo cerrado en ambos extremos", relieve=0.08, tapar_extremos=True)
R['+2 marcadores']       = evaluar("relieve 0.08 + 2 marcadores",     relieve=0.08, marcadores=2)
R['+4 marcadores']       = evaluar("relieve 0.08 + 4 marcadores",     relieve=0.08, marcadores=4)
np.save('degeneracion.npy', R, allow_pickle=True)
