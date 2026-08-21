# ─────────────────────────────────────────────────────────────────────────────
# La ocupación como firma de lugar
#
# Los 10 pasillos son geométricamente idénticos, pero el PATRÓN de bahías llenas
# y vacías no lo es. Y el WMS ya sabe cuál es ese patrón: no hay que aprenderlo,
# hay que consultarlo.
#
# Pregunta: ¿cuántas bahías hay que ver para saber en qué pasillo estás, y cuánta
# desactualización del WMS aguanta antes de fallar?
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
rng = np.random.default_rng(7)

PASILLOS   = 10       # 6 en Nave Este + 4 en Oeste
BAHIAS     = 17       # por lado
LADOS      = 2
NIVELES    = 5
OCUPACION  = 0.822    # 1,758 de 2,138 en el almacén actual
P_ERR_VIS  = 0.05     # el LiDAR se equivoca al juzgar lleno/vacío 5% de las veces

def entropia(p):
    return -(p*np.log2(p) + (1-p)*np.log2(1-p))

H = entropia(OCUPACION)
print(f"\nCada bahía carga {H:.2f} bits (ocupación {OCUPACION:.1%})")
print(f"Distinguir {PASILLOS} pasillos pide {np.log2(PASILLOS):.2f} bits")
print(f"Un pasillo entero, un nivel, dos lados: {BAHIAS*LADOS} bahías = {BAHIAS*LADOS*H:.0f} bits")
print(f"Los 5 niveles: {BAHIAS*LADOS*NIVELES*H:.0f} bits\n")

def prueba(k_bahias, stale, n=6000):
    """k_bahias observadas · 'stale' = fracción del mapa desactualizada."""
    aciertos = 0
    for _ in range(n):
        mapa = rng.random((PASILLOS, BAHIAS*LADOS*NIVELES)) < OCUPACION   # lo que dice el WMS
        real = mapa.copy()
        mov = rng.random(real.shape) < stale                              # lo que se movió
        real[mov] = ~real[mov]
        yo = rng.integers(PASILLOS)
        idx = rng.choice(real.shape[1], k_bahias, replace=False)
        obs = real[yo, idx].copy()
        flip = rng.random(k_bahias) < P_ERR_VIS                           # error de percepción
        obs[flip] = ~obs[flip]
        # verosimilitud: cuántas bahías coinciden con el mapa de cada pasillo
        coincide = (mapa[:, idx] == obs).sum(1)
        aciertos += int(np.argmax(coincide) == yo and (coincide == coincide.max()).sum() == 1)
    return aciertos / n

print("Acierto al identificar el pasillo\n")
print(f"{'bahías vistas':>14} │" + "".join(f"{int(s*100):>7}%" for s in (0, .05, .10, .20, .35)))
print(f"{'':>14} │" + "  desactualización del WMS")
print("─"*14 + "─┼" + "─"*40)
for k in (4, 6, 8, 12, 17, 25, 34):
    fila = "".join(f"{prueba(k, s)*100:>7.1f}" for s in (0, .05, .10, .20, .35))
    print(f"{k:>14} │{fila}")
print()
