# ─────────────────────────────────────────────────────────────────────────────
# Recorridos densos del planificador, para visibilidad.py
#
#   py percepcion/rutas_densas.py          # ~10–15 min en la i3; escribe rutas_densas.json
#
# analisis/rutas_tabla.json guarda los recorridos RESUMIDOS (tramos con pose de inicio y fin).
# Para saber qué ve cada cámara hace falta la pose en cada instante, así que acá se vuelven a
# planificar con analisis/planificador_rutas.py y se guarda cada primitiva: (parte, sentido,
# fracción de dirección, largo). Se reproduce exacto con odometria.avanzar (mismo step()).
#
# Recorridos:
#   maje_Ra / maje_Rb   3L (uñas hacia la descarga) → 5 3 Ra / Rb → descarga, con el IBC a la vuelta
#   barrido_<x><s><p>   desde la descarga (uñas hacia adentro) hasta cada hueco, 7 bahías × L/R × a/b
# ─────────────────────────────────────────────────────────────────────────────
import json
import math
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'analisis'))
import bahias as B                                             # noqa: E402
import planificador_rutas as P                                 # noqa: E402

ARCHIVO = os.path.join(AQUI, 'rutas_densas.json')


def _parte(nombre):
    """ENTRADA / SALIDA / VUELTA / TRASLADO (sin el detalle)."""
    return nombre.split(' ')[0]


def _prims(ruta):
    out = []
    for nombre, res in ruta['partes']:
        for sg, fr, ds in res['prims']:
            out.append([_parte(nombre), sg, fr, ds])
    return out


def generar(archivo=ARCHIVO, **kw_pl):
    t0 = time.time()
    log = lambda s: print(f"[{time.time() - t0:5.0f} s] {s}", flush=True)
    pl = P.Planificador(n_vueltas=2, **kw_pl)
    out = dict(xpiv=pl.xpiv, dmax=P.dmax(pl.xpiv), modelo=pl.modelo, central=pl.central, rutas={})
    p0 = B.pose_en_pasillo('3L', 'descarga')
    for h in ('5 3 Ra', '5 3 Rb'):
        ida = pl.ruta(p0, h)
        vuelta = pl.ruta(None, B.pose_descarga(pl.xpiv), origen=h, cargado=True)
        if not (ida['ok'] and vuelta['ok']):
            log(f"maje {h}: NO sale"); continue
        out['rutas'][f"maje_{h[-2:]}"] = dict(inicio=list(p0), hueco=h, piernas=[
            dict(nombre=f'3L → {h}', cargado=False, prims=_prims(ida)),
            dict(nombre=f'{h} → descarga', cargado=True, prims=_prims(vuelta))])
        log(f"maje {h}")
    p_can = (0.0, 0.0, 0.0)
    for x in range(1, B.N + 1):
        for s in 'LR':
            for p in 'ab':
                d = f"{x} {s}{p}"
                r = pl.ruta(p_can, d)
                if not r['ok']:
                    log(f"barrido {d}: NO sale"); continue
                out['rutas'][f"barrido_{x}{s}{p}"] = dict(inicio=list(p_can), hueco=d, piernas=[
                    dict(nombre=f'descarga → {d}', cargado=False, prims=_prims(r))])
                log(f"barrido {d}")
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(out, f)
    log(f"escrito {archivo}")


def archivo_v2(central):
    return os.path.join(AQUI, f"rutas_densas_v2_{'central' if central else 'libre'}.json")


def cargar(archivo=ARCHIVO):
    with open(archivo, encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    if '--v2' in sys.argv:          # postes + retranqueo + giro sin reversa, con y sin carril central
        for central in (False, True):
            generar(archivo_v2(central), modelo='v2', xpiv=P.XPIV_V2, central=central)
    else:
        generar()
