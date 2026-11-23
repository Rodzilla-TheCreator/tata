#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · descifrar.py — qué bytes del bus cambian con cada acción marcada (23-nov-2026).

Lee un log de grabar_can.py (escucha_can.ino, LISTEN_ONLY) con marcas INICIO k / FIN k (modo
Enter-acción-Enter, guion «diagnostico») y, para cada paso, compara contra los 3 s de ANTES:

  · LIMPIO  : el byte estaba quieto antes (un solo valor) y durante la acción tomó otros.
              Esto es lo que buscamos: un mando o un sensor que respondió a la acción.
  · RUIDOSO : el byte ya se movía antes (contador, reloj, medición) y durante la acción salió
              de su rango. Puede ser real, pero se mira con cuidado.
  Para cada uno: valor de antes, valores durante (mín–máx), qué BITS cambiaron, y si vuelve a su
  valor de antes en los 2 s después del FIN (mando momentáneo) o se queda (posición, estado).

    py descifrar.py logs\escucha_equipo_20261123-101500.log
    py descifrar.py <log> --paso 7          # solo un paso
    python3 descifrar.py --prueba           # se prueba a sí mismo con un log sintético, y su control

Al final, los bytes que solo cambian CON el pedal pisado, y el que cambia al pisar y al soltar el
pedal: ese es el candidato al bit del hombre muerto.
"""
import collections
import re
import sys

TRAMA = re.compile(r"^\s*(\d+)\s+(?:EXT|   )\s([0-9A-F]{3})\s+\[(\d)\]((?: [0-9A-F]{2})*)")
MARCA = re.compile(r">>> MARCA t=(\d+) · [^·]* · (INICIO|FIN) (\d+) · (.*)$")
ANTES_MS, DESPUES_MS = 3000, 2000


def leer(ruta):
    tramas, marcas = [], {}
    with open(ruta, encoding="utf-8", errors="replace") as f:
        for l in f:
            m = TRAMA.match(l)
            if m:
                datos = [int(x, 16) for x in m.group(4).split()]
                tramas.append((int(m.group(1)), int(m.group(2), 16), datos))
                continue
            m = MARCA.search(l)
            if m:
                t, tipo, k, nombre = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4).strip()
                marcas.setdefault(k, {"nombre": nombre})[tipo] = t
    pasos = [(k, v["nombre"], v["INICIO"], v["FIN"]) for k, v in sorted(marcas.items())
             if "INICIO" in v and "FIN" in v and v["FIN"] > v["INICIO"]]
    return tramas, pasos


def valores(tramas, t0, t1):
    """{(id, byte): [valores en orden]} entre t0 y t1."""
    v = collections.defaultdict(list)
    for t, i, d in tramas:
        if t0 <= t < t1:
            for b, x in enumerate(d):
                v[(i, b)].append(x)
    return v


def analizar_paso(tramas, t_ini, t_fin):
    antes = valores(tramas, t_ini - ANTES_MS, t_ini)
    durante = valores(tramas, t_ini, t_fin)
    despues = valores(tramas, t_fin, t_fin + DESPUES_MS)
    limpios, ruidosos = [], []
    for clave, dur in durante.items():
        ant = antes.get(clave)
        if not ant:
            continue                      # sin referencia: no se puede decir nada
        sa, sd = set(ant), set(dur)
        if len(sa) == 1:
            ref = ant[0]
            if sd == {ref}:
                continue
            bits = 0
            for x in sd:
                bits |= x ^ ref
            desp = despues.get(clave, [])
            vuelve = bool(desp) and desp[-1] == ref
            limpios.append((clave, ref, min(sd), max(sd), bits, vuelve, len(sd)))
        else:
            if min(sd) < min(sa) or max(sd) > max(sa):
                ruidosos.append((clave, min(sa), max(sa), min(sd), max(sd)))
    return limpios, ruidosos


def nombre_id(i):
    f = i & 0x780
    nodo = i & 0x7F
    tipo = {0x000: "NMT", 0x080: "SYNC/EMCY", 0x180: "TPDO1", 0x200: "RPDO1", 0x280: "TPDO2", 0x300: "RPDO2",
            0x380: "TPDO3", 0x400: "RPDO3", 0x480: "TPDO4", 0x500: "RPDO4", 0x580: "SDO resp", 0x600: "SDO pide",
            0x700: "latido"}.get(f, "?")
    return "%03X %-9s n%-2d" % (i, tipo, nodo)


def informe(ruta, solo=None):
    tramas, pasos = leer(ruta)
    print("%s: %d tramas, %d pasos marcados\n" % (ruta, len(tramas), len(pasos)))
    por_paso = {}
    for k, nombre, t0, t1 in pasos:
        if solo and k != solo:
            continue
        limpios, ruidosos = analizar_paso(tramas, t0, t1)
        por_paso[k] = (nombre, {c[0] for c in limpios})
        print("=" * 96)
        print("PASO %d · %s   (%.1f s)" % (k, nombre, (t1 - t0) / 1000))
        if not limpios and not ruidosos:
            print("   nada cambió respecto de los 3 s de antes")
        for (i, b), ref, lo, hi, bits, vuelve, n in sorted(limpios):
            print("   LIMPIO   %s byte %d: antes %02X → durante %02X–%02X (%d valores)  bits %s  %s"
                  % (nombre_id(i), b, ref, lo, hi, n, format(bits, "08b"),
                     "vuelve (momentáneo)" if vuelve else "SE QUEDA (posición/estado)"))
        for (i, b), alo, ahi, dlo, dhi in sorted(ruidosos):
            print("   ruidoso  %s byte %d: antes %02X–%02X → durante %02X–%02X" % (nombre_id(i), b, alo, ahi, dlo, dhi))
    # cruce: sin pedal vs con pedal, y el pedal mismo
    sin = {n.split("·", 1)[1].strip(): s for n, s in por_paso.values() if n.startswith("SIN pedal")}
    con = {n.split("·", 1)[1].strip(): s for n, s in por_paso.values() if n.startswith("CON pedal")}
    if sin and con:
        print("\n" + "=" * 96 + "\nSOLO CON EL PEDAL (lo que la acción mueve únicamente con el pie puesto):")
        for accion in con:
            extra = con[accion] - sin.get(accion, set())
            if extra:
                print("   %-18s %s" % (accion, ", ".join("%s b%d" % (nombre_id(i).split()[0], b) for i, b in sorted(extra))))
    pis = [s for n, s in por_paso.values() if n.startswith("PISAR pedal")]
    sol = [s for n, s in por_paso.values() if n.startswith("SOLTAR pedal")]
    if pis and sol:
        cand = pis[0] & sol[0]
        print("\nCANDIDATOS AL BIT DEL PEDAL (cambian al pisar Y al soltar): " +
              (", ".join("%s byte %d" % (nombre_id(i).split()[0], b) for i, b in sorted(cand)) or "ninguno"))


# ---------------------------------------------------------------------------------------------
def prueba():
    """Log sintético con un mando conocido (0x182 b0 durante el paso 2), un reloj ruidoso
    (0x187 b0 alterna siempre) y un paso 1 sin acción. Control: el paso 1 no puede dar nada LIMPIO."""
    import os
    import tempfile
    lineas = []
    t = 0
    def trama(t, i, d):
        lineas.append("%10d      %03X  [%d] %s   TPDO nodo %d" % (t, i, len(d), " ".join("%02X" % x for x in d), i & 0x7F))
    def marca(t, tipo, k, n):
        lineas.append(">>> MARCA t=%d · 10:00:00 · %s %d · %s" % (t, tipo, k, n))
    for t in range(0, 20000, 20):
        en_paso2 = 12000 <= t < 14000
        trama(t, 0x182, [100 if en_paso2 else 0, 0, 0, 0, 0x08 if en_paso2 else 0, 0, 0, 0])
        trama(t, 0x187, [(t // 1000) % 2 * 0x80, 0x30, 0x3E, 0x0E])
        if t == 5000: marca(t, "INICIO", 1, "referencia")
        if t == 8000: marca(t, "FIN", 1, "referencia")
        if t == 12000: marca(t, "INICIO", 2, "SIN pedal · joy adelante")
        if t == 14000: marca(t, "FIN", 2, "SIN pedal · joy adelante")
    ruta = os.path.join(tempfile.mkdtemp(), "sintetico.log")
    open(ruta, "w").write("\n".join(lineas) + "\n")
    tramas, pasos = leer(ruta)
    l1, _ = analizar_paso(tramas, pasos[0][2], pasos[0][3])
    l2, _ = analizar_paso(tramas, pasos[1][2], pasos[1][3])
    encontrados = {(c[0][0], c[0][1]) for c in l2}
    ok_mando = (0x182, 0) in encontrados and (0x182, 4) in encontrados
    ok_reloj = (0x187, 0) not in encontrados                 # el reloj no puede salir como LIMPIO
    ok_control = len(l1) == 0
    vuelve = all(c[5] for c in l2 if c[0][0] == 0x182)
    print("prueba: mando 0x182 b0/b4 encontrado %s · reloj 0x187 no confundido %s · vuelve %s · "
          "control (paso sin acción = nada) %s" % (ok_mando, ok_reloj, vuelve, ok_control))
    ok = ok_mando and ok_reloj and ok_control and vuelve
    print("RESULTADO:", "PASA" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    for _f in (sys.stdout, sys.stderr):
        try:
            _f.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if len(sys.argv) > 1 and sys.argv[1] == "--prueba":
        sys.exit(prueba())
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    solo = int(sys.argv[sys.argv.index("--paso") + 1]) if "--paso" in sys.argv else None
    informe(sys.argv[1], solo)
