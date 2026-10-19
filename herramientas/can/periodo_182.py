#!/usr/bin/env python3
# periodo_182.py — saca el período real de una trama CAN de un log de escucha_can.ino
#
# TaTa · herramientas/can · ver banco_imitador/LEEME.md
#
# PARA QUÉ. `multipiloto_falso.ino` y `master_falso.ino` usan PERIODO_182_MS = 20 y
# PERIODO_HB_MS = 500 como SUPUESTOS, contados a ojo del log del 06-oct. Pero
# `escucha_can.ino` estampa millis() en la primera columna de CADA trama (línea 139),
# así que el período real ya está en el log: es la resta entre marcas consecutivas de
# la misma id. Esto lo calcula, en vez de adivinarlo.
#
# NO necesita otra captura ni el banco: corre contra el .log que ya tenés.
#
# USO
#   python3 periodo_182.py <ruta-al-log>
#   python3 periodo_182.py <ruta-al-log> --id 182 303 20A      # otras tramas
#
# El log no se versiona (es pesado); este script sí. Corré el script contra tu log
# local y pegá la salida.
#
# FORMATO que lee (de escucha_can.ino):
#   "   12345     182  [8] 00 00 ...  TPDO1 nodo 2 ..."
#    ^millis()    ^id    ^dlc ^bytes
#
# OJO con los millis(): resolución 1 ms. Para un período de ~20 ms da ~5 % de
# cuantización, suficiente para fijar el supuesto. La marca se pone cuando el sketch
# procesa la trama, no cuando llega al bus, así que el jitter instantáneo no es fiable;
# el PROMEDIO sobre muchas tramas sí. min/max delatan si el serie se atoró (huecos).

import argparse
import re
import statistics
import sys

for _f in (sys.stdout, sys.stderr):      # la consola de Windows (cp1252) no imprime «→»
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# id a 3 hex (%03lX), con timestamp al inicio; tolera el "EXT" o los espacios del %s
LINEA = re.compile(r"^\s*(\d+)\s+(?:EXT\s+)?([0-9A-Fa-f]{3})\s+\[")

# ids de interés por defecto: 182 = TPDO1 del multipiloto, 702 = su heartbeat,
# 080 = SYNC (para ver si el 182 sale solo o detrás de un SYNC)
DEFECTO = ["182", "702"]
SYNC = "080"


def marcas(path, ids_interes):
    """Devuelve {id: [millis, ...]} en orden, para las ids pedidas más el SYNC."""
    quiero = {i.upper() for i in ids_interes} | {SYNC}
    out = {i: [] for i in quiero}
    n = 0
    with open(path, "r", errors="replace") as f:
        for ln in f:
            m = LINEA.match(ln)
            if not m:
                continue
            n += 1
            cid = m.group(2).upper()
            if cid in out:
                out[cid].append(int(m.group(1)))
    return out, n


def deltas(ts):
    """Restas entre marcas consecutivas, descartando wrap de millis() y huecos absurdos."""
    d = []
    for a, b in zip(ts, ts[1:]):
        dt = b - a
        if 0 <= dt < 60000:  # un hueco > 60 s es un corte de captura, no un período
            d.append(dt)
    return d


def resumen(cid, ts):
    if len(ts) < 2:
        print(f"  {cid}: {len(ts)} trama(s) — no alcanza para un período")
        return None
    d = deltas(ts)
    if not d:
        print(f"  {cid}: {len(ts)} tramas pero sin deltas válidos (¿todas iguales o huecos?)")
        return None
    span = (ts[-1] - ts[0]) / 1000.0
    hz = len(ts) / span if span > 0 else 0
    print(f"  {cid}: {len(ts)} tramas en {span:.1f} s  ·  {hz:.1f} Hz")
    print(f"       período  medio {statistics.mean(d):6.2f} ms   mediana {statistics.median(d):6.2f} ms"
          f"   min {min(d)} ms   max {max(d)} ms")
    return statistics.median(d)


def correlacion_sync(ts_182, ts_sync, ventana=3):
    """¿Cada 182 viene justo detrás de un SYNC? Si sí, el PDO es síncrono."""
    if not ts_182 or not ts_sync:
        print(f"\n  SYNC: {len(ts_sync)} tramas 080, {len(ts_182)} tramas 182 — sin comparar")
        return
    import bisect
    cerca = 0
    for t in ts_182:
        i = bisect.bisect_right(ts_sync, t) - 1  # último SYNC en <= t
        if i >= 0 and 0 <= t - ts_sync[i] <= ventana:
            cerca += 1
    pct = 100.0 * cerca / len(ts_182)
    print(f"\n  SYNC: {len(ts_sync)} tramas 080.  {cerca}/{len(ts_182)} tramas 182 "
          f"caen dentro de {ventana} ms detrás de un SYNC ({pct:.0f} %).")
    if pct > 90:
        print("       → el 182 parece SÍNCRONO (sale al recibir SYNC). El imitador debe")
        print("         mandarlo contra el SYNC, no por temporizador libre.")
    elif pct < 20:
        print("       → el 182 parece ASÍNCRONO (temporizador propio). Vale el período de arriba.")
    else:
        print("       → mezclado; mirar a mano un tramo del log.")


def main():
    ap = argparse.ArgumentParser(description="Período real de tramas CAN de un log de escucha_can.ino")
    ap.add_argument("log", help="ruta al .log")
    ap.add_argument("--id", nargs="+", default=DEFECTO, help="ids en hex (default: 182 702)")
    a = ap.parse_args()

    try:
        datos, total = marcas(a.log, a.id)
    except OSError as e:
        sys.exit(f"no se pudo abrir {a.log}: {e}")

    print(f"\nlog: {a.log}  ·  {total} tramas reconocidas\n")
    for cid in [i.upper() for i in a.id]:
        resumen(cid, datos.get(cid, []))
    correlacion_sync(datos.get("182", []), datos.get(SYNC, []))
    print()


if __name__ == "__main__":
    main()
