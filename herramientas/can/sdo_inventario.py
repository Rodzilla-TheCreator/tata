#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · inventario por SDO, SOLO LECTURA. Maneja sdo_lee.ino (115200) y le pide, en orden:

  1. identidad de cada nodo (0x1000, 0x1008, 0x1009, 0x100A, 0x1018.1-4)
  2. los parámetros de opciones del manual (docs/16), en el nodo donde deberían vivir
  3. 0x1F81 del Master: qué nodos espera (CiA 302)

sdo_lee solo sabe pedir lecturas (upload 0x40/0x60/0x70); este script solo le manda los
comandos «l», «id» y «esperados». No hay forma de escribir desde acá.

    py sdo_inventario.py            # COM6
    py sdo_inventario.py COM7

    py sdo_inventario.py --crudo    # solo: tramas crudas 601/581 de 1000, 2414 y 2100, subs 0–7
    py sdo_inventario.py --opciones # opciones del Master: actual, mín, máx, fábrica
    py sdo_inventario.py --pdos 7   # mapeo de los PDO de un nodo (qué objeto va en cada byte)
    py sdo_inventario.py --barre 4 2300 2500   # qué objetos existen en el rango y su valor

El nodo 3 (pantalla) NO se lee por defecto: el Master le escribe por SDO (603) ~5 veces por
segundo y nuestro pedido iría por el mismo canal. --con-pantalla lo agrega al final.

Todo va a logs\sdo_inventario_<fecha>.log; en pantalla solo los resultados.
"""
import datetime as dt
import os
import re
import sys
import time

import serial

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

NODOS = [1, 2, 4, 5, 6, 7, 8, 10, 30]
NOMBRE = {1: "Master", 2: "Multi-Pilot 1", 3: "Display", 4: "Direccion 1", 5: "Direccion 2",
          6: "Direccion 3", 7: "Elevacion", 8: "Traccion 1", 10: "Multi-Pilot 2", 30: "nodo 30"}
# (índice, nodos donde buscarlo en orden, qué es)
OPCIONES = [
    (0x2414, [4, 1], "relación de dirección, vueltas tope a tope (×0.1; fábrica 5.5)"),
    (0x23BA, [7, 1], "altura de elevación: 0 no · 1 indicador · 2 PRESELECTOR"),
    (0x23BB, [7, 1], "altura de elevación libre, mm (fábrica 2500)"),
    (0x23D1, [7, 1], "peso de carga: 0 no · 1..2040 BÁSCULA"),
    (0x2108, [1, 8], "velocidad sentido tracción, prog. 1"),
    (0x2128, [1, 8], "velocidad sentido tracción, prog. 3"),
    (0x210C, [1, 7], "velocidad sentido horquilla, prog. 1"),
    (0x211C, [1, 7], "velocidad sentido horquilla, prog. 2"),
    (0x212C, [1, 7], "velocidad sentido horquilla, prog. 3"),
    (0x2100, [1, 8], "aceleración, prog. 1"),
]
RES = re.compile(r"^nodo\s+(\d+)\s+([0-9A-F]{4})\.([0-9A-F]{2})\s+(.*)$")

puerto = next((a for a in sys.argv[1:] if a.upper().startswith("COM") or a.startswith("/dev/")), "COM6")
con_pantalla = "--con-pantalla" in sys.argv
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
ruta = os.path.join(aqui, "logs", "sdo_inventario_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
log = open(ruta, "w", encoding="utf-8")


def anotar(texto):
    log.write("%s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], texto)); log.flush()


s = serial.Serial(puerto, 115200, timeout=0.2)


def lineas_hasta_silencio(silencio=1.2, maximo=60):
    """Lee hasta que pasen `silencio` s sin líneas nuevas (cada lectura de sdo_lee tarda ≤ 0.35 s)."""
    out, ult, ini = [], time.time(), time.time()
    while time.time() - ult < silencio and time.time() - ini < maximo:
        l = s.readline().decode("utf-8", "replace").strip()
        if l:
            anotar("< " + l); out.append(l); ult = time.time()
    return out


def comando(c):
    anotar("> " + c)
    s.write((c + "\n").encode())
    return lineas_hasta_silencio()


def resultados(lineas):
    return [m.groups() for m in (RES.match(l) for l in lineas) if m]


# arranque: abrir el puerto reinicia el ESP32, que escucha 3 s antes de decidir si transmite
print("Esperando a sdo_lee (escucha 3 s sin transmitir)…", flush=True)
fin, listo = time.time() + 10, None
while time.time() < fin and listo is None:
    l = s.readline().decode("utf-8", "replace").strip()
    if l:
        anotar("< " + l)
        if "Escucha previa" in l:
            print("  " + l, flush=True)
        if "Bus sano" in l:
            listo = True
        elif "NO TRANSMITO" in l:
            listo = False
if not listo:
    print("sdo_lee NO habilitó la transmisión (bus no sano o no contestó). No se pidió nada.")
    print("log: " + ruta); sys.exit(1)
print("Bus sano. Empiezo (solo lecturas).\n", flush=True)

if "--crudo" in sys.argv:
    # 23-oct: el Master contesta lo mismo a todo 0x2xxx sub 0. Ver la conversación trama a trama.
    # 0x1000 va primero como control: un objeto estándar que sabemos que contesta bien.
    comando("crudo on")
    for idx in (0x1000, 0x2414, 0x2100):
        for sub in range(8):
            print("== nodo 1  %04X.%02X" % (idx, sub), flush=True)
            for l in comando("l 1 %X %d" % (idx, sub)):
                print("  " + l, flush=True)
    comando("crudo off")
    s.close(); anotar("FIN"); log.close()
    print("\nlog: " + ruta)
    sys.exit(0)

if "--opciones" in sys.argv:
    # 23-oct, descifrado con --crudo: cada parámetro 0x2xxx del Master es un registro.
    # sub 0 = cabecera fija (06 00 08 00 00 78), 1 = 0x0100, 2 = ACTUAL, 3 = mín, 4 = máx,
    # 5 = fábrica, 6 = igual a 5 en lo visto. Comprobado con 0x2100 (actual 60 ≠ fábrica 70).
    print("== OPCIONES en el Master: actual (mín · máx · fábrica) ==", flush=True)
    for idx, _, que in OPCIONES:
        v = {}
        for sub in (2, 3, 4, 5):
            r = resultados(comando("l 1 %X %d" % (idx, sub)))
            m = re.match(r"= 0x([0-9A-F]+)", r[0][3]) if r else None
            v[sub] = int(m.group(1), 16) if m else (r[0][3] if r else "?")
        print("  %04X  actual %-6s (mín %s · máx %s · fábrica %s)   %s" % (idx, v[2], v[3], v[4], v[5], que), flush=True)
    s.close(); anotar("FIN"); log.close()
    print("\nlog: " + ruta)
    sys.exit(0)

def valor(nodo, idx, sub):
    r = resultados(comando("l %d %X %d" % (nodo, idx, sub)))
    if not r:
        return None, "?"
    m = re.match(r"= 0x([0-9A-F]+)", r[0][3])
    return (int(m.group(1), 16), r[0][3]) if m else (None, r[0][3])


if "--pdos" in sys.argv:
    # 23-oct: qué objeto viaja en cada byte de cada PDO de un nodo (CiA 301: 0x1800/0x1A00 TPDO,
    # 0x1400/0x1600 RPDO). Cada entrada de mapeo = índice << 16 | sub << 8 | bits.
    nodo = int(sys.argv[sys.argv.index("--pdos") + 1])
    print("== PDOs del nodo %d (%s) ==" % (nodo, NOMBRE.get(nodo, "?")), flush=True)
    for tipo, com, mapa in (("TPDO", 0x1800, 0x1A00), ("RPDO", 0x1400, 0x1600)):
        for k in range(4):
            cob, txt = valor(nodo, com + k, 1)
            if cob is None:
                print("  %s%d  %04X: %s" % (tipo, k + 1, com + k, txt), flush=True)
                continue
            tt, _ = valor(nodo, com + k, 2)
            n, txtn = valor(nodo, mapa + k, 0)
            print("  %s%d  COB-ID 0x%03X%s · tipo %s · %s objetos" % (
                tipo, k + 1, cob & 0x7FF, " (DESACTIVADO)" if cob & 0x80000000 else "", tt, n if n is not None else txtn), flush=True)
            byte = 0
            for e in range(1, (n or 0) + 1):
                ent, txte = valor(nodo, mapa + k, e)
                if ent is None:
                    print("      %d: %s" % (e, txte), flush=True)
                    continue
                oi, os_, bits = ent >> 16, (ent >> 8) & 0xFF, ent & 0xFF
                _, actual = valor(nodo, oi, os_) if oi >= 0x2000 else (None, "")
                print("      b%-4s %04X.%02X  %2d bits   %s" % (
                    "%d" % (byte // 8) if bits >= 8 else "%d.%d" % (byte // 8, byte % 8), oi, os_, bits, actual), flush=True)
                byte += bits
    s.close(); anotar("FIN"); log.close()
    print("\nlog: " + ruta)
    sys.exit(0)

if "--barre" in sys.argv:
    # 23-oct: qué objetos existen en un rango (sub 0, con «barre» de sdo_lee) y el valor en reposo
    # de cada sub de los que existen. Solo lecturas.
    k = sys.argv.index("--barre")
    nodo, desde, hasta = int(sys.argv[k + 1]), sys.argv[k + 2], sys.argv[k + 3]
    print("== nodo %d · objetos %s–%s ==" % (nodo, desde, hasta), flush=True)
    hallados = []
    c = "barre %d %s %s" % (nodo, desde, hasta)
    anotar("> " + c); s.write((c + "\n").encode())
    lineas, fin = [], time.time() + 300           # los que no existen no imprimen: esperar el final
    while time.time() < fin:
        l = s.readline().decode("utf-8", "replace").strip()
        if l:
            anotar("< " + l); lineas.append(l)
            if "fin del barrido" in l:
                break
    for l in lineas:
        m = re.match(r"([0-9A-F]{4}) existe(\?)?", l)
        if m:
            hallados.append(int(m.group(1), 16))
        if "SIN RESPUESTA" in l:
            print("  " + l, flush=True)
    print("  %d objetos existen" % len(hallados), flush=True)
    for idx in hallados:
        n, txt = valor(nodo, idx, 0)
        print("  %04X.00  %s" % (idx, txt), flush=True)
        if n is not None and 0 < n <= 16:            # registro: leer sus subs
            for sub in range(1, n + 1):
                print("  %04X.%02X  %s" % (idx, sub, valor(nodo, idx, sub)[1]), flush=True)
    s.close(); anotar("FIN"); log.close()
    print("\nlog: " + ruta)
    sys.exit(0)

resumen = []

print("== 1 · IDENTIDAD ==", flush=True)
for n in NODOS + ([3] if con_pantalla else []):
    r = resultados(comando("id %d" % n))
    vivos = [x for x in r if "SIN RESPUESTA" not in x[3]]
    print("nodo %2d %-14s %s" % (n, NOMBRE.get(n, "?"), "" if vivos else "SIN RESPUESTA (no está o no tiene SDO)"), flush=True)
    for nodo, idx, sub, v in vivos:
        print("    %s.%s  %s" % (idx, sub, v), flush=True)
        resumen.append(("id", nodo, idx, sub, v))

print("\n== 2 · OPCIONES ==", flush=True)
for idx, donde, que in OPCIONES:
    print("%04X  %s" % (idx, que), flush=True)
    for n in donde:
        r = resultados(comando("l %d %X 0" % (n, idx)))
        if r and "06090011" in r[0][3]:               # subíndice no existe: probar el 1
            r = resultados(comando("l %d %X 1" % (n, idx)))
        for nodo, i, sub, v in r:
            print("    nodo %2s  %s.%s  %s" % (nodo, i, sub, v), flush=True)
            resumen.append(("op", nodo, i, sub, v))
        if r and r[0][3].startswith("="):
            break                                       # encontrado: no seguir buscando

print("\n== 3 · 0x1F81 del Master (nodos que espera) ==", flush=True)
for l in comando("esperados 1"):
    if "1F81" in l and "ABORT 06090011" not in l:
        print("    " + l.strip(), flush=True)
        resumen.append(("1f81", "1", "1F81", "", l.strip()))

s.close()
anotar("FIN")
log.close()
print("\nlog: " + ruta)
