#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · maneja multipiloto_campo.ino en el equipo. Pantalla limpia: solo pide Enter y avisa
los eventos que importan. Todo lo demás (cada trama) va al log en herramientas/can/logs/.

    py campo_nodo2.py            # COM6
    py campo_nodo2.py COM7

MANDOS (22-oct), una vez armado, escribiendo en esta ventana + Enter:
    a 100 / t 100     joystick adelante / atrás (0–255)    i 100 / d 100   izquierda / derecha
    n s e w           botones de arriba (quedan hasta 0)    r   botón trasero (pito)
    0                 todo a cero        X   SILENCIO (vuelve a solo escucha)
    cualquier otro texto = MARCA en el log («pantalla 8.08», «Diagnose b0 = 100»…)
Desde el primer mando el script manda '.' cada 50 ms: si se cae, el watchdog del ESP32 (200 ms)
pone el 0x182 en cero. Al salir con Ctrl-C manda '0'.
"""
import datetime as dt
import os
import re
import sys
import threading
import time

import serial

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

puerto = sys.argv[1] if len(sys.argv) > 1 else "COM6"
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
ruta = os.path.join(aqui, "logs", "campo_nodo2_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
f = open(ruta, "w", encoding="utf-8")

NOMBRE = {1: "MASTER", 3: "pantalla", 4: "direccion", 5: "direccion 2", 6: "direccion 3",
          7: "elevacion", 8: "traccion", 10: "multipiloto 2", 28: "CanCode", 30: "nodo 30"}
TRAMA = re.compile(r"^(\d+) ([0-9A-F]{3}) \[(\d)\]((?: [0-9A-F]{2})*)$")
visto = set()


def aviso(clave, texto):
    if clave in visto:
        return
    visto.add(clave)
    print("  %s  %s" % (dt.datetime.now().strftime("%H:%M:%S"), texto), flush=True)


s = serial.Serial(puerto, 921600, timeout=0.5)
fin = time.time() + 6
while time.time() < fin:
    l = s.readline().decode("utf-8", "replace").strip()
    f.write(l + "\n")
    if "LISTO" in l:
        break

print("\nLLAVE EN OFF. Enter cuando esté apagada.", flush=True)
input()
s.write(b"A")
print("Armado. Sube la llave cuando quieras. Ctrl-C para terminar.", flush=True)
print("Mandos: a/t/i/d N · n s e w r · 0 · X · otro texto = marca\n", flush=True)

MANDO = re.compile(r"^([atid] \d{1,3}|[nsewr0X])$")
cerrojo = threading.Lock()
latiendo = threading.Event()
vivo = True


def escribir(texto):
    with cerrojo:
        s.write((texto + "\n").encode())


def marca(texto):
    with cerrojo:
        f.write(">>> MARCA %s · %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], texto)); f.flush()


def teclado():
    while vivo:
        try:
            t = input().strip()
        except EOFError:
            return
        if not t:
            continue
        marca(t)
        if MANDO.match(t):
            latiendo.set()
            escribir(t)
        else:
            print("  (marca)", flush=True)


def latido():
    while vivo:
        if latiendo.is_set():
            escribir(".")
        time.sleep(0.05)


threading.Thread(target=teclado, daemon=True).start()
threading.Thread(target=latido, daemon=True).start()

try:
    while True:
        l = s.readline().decode("utf-8", "replace").strip()
        if not l:
            continue
        with cerrojo:
            f.write(l + "\n"); f.flush()
        if l.startswith("# YO"):
            t = l[5:]
            if t.startswith("mando") or "WATCHDOG" in t or "SILENCIO" in t:
                print("  %s  %s" % (dt.datetime.now().strftime("%H:%M:%S"), t), flush=True)
            elif "boot-up" in t:          aviso("boot", "NOSOTROS: mandamos el arranque del nodo 2 (702 00)")
            elif "0x1000" in t:         aviso("sdo", "el Master le pidió 0x1000 al nodo 2 y CONTESTAMOS")
            elif "START" in t:          aviso("start", "el Master nos dio NMT START -> operacional (joystick en cero)")
            elif "abort" in t:          aviso("abort" + t, "el Master pidió otro objeto: " + t)
            elif "plan B" in t:         aviso("planb", "bus vivo 15 s sin grupo: arranque igual")
            elif "grupo" in t:          aviso("grupo", "arrancó el grupo de nodos")
            elif t.startswith("estado"):
                if not t.startswith("estado 0") and "pendientes 0 " in t and "TEC 0 " in t:
                    aviso("enbus", "nuestro nodo está en el bus: sus tramas salen y las aceptan (TEC 0)")
            elif "STOP" in t or "RESET" in t or "PRE-OP" in t: aviso(t, "NMT: " + t)
            continue
        m = TRAMA.match(l)
        if not m:
            continue
        cid = int(m.group(2), 16)
        datos = m.group(4).split()
        aviso("bus", "bus vivo")
        if 0x701 <= cid <= 0x77F and datos == ["00"]:
            n = cid - 0x700
            aviso("bu%d" % n, "arrancó nodo %d (%s)" % (n, NOMBRE.get(n, "?")))
        if cid == 0x701:
            aviso("master", ">>> EL MASTER ESTÁ EN EL BUS <<<")
        if cid == 0x080:
            aviso("sync", "SYNC del Master: el bus está en marcha")
        if cid == 0x703 and datos == ["05"]:
            aviso("pant5", "la pantalla pasó a OPERACIONAL")
        if cid == 0x000:
            aviso("nmt" + "".join(datos), "NMT del Master: %s" % " ".join(datos))
        if (cid & 0x780) == 0x080 and cid != 0x080:
            aviso("emcy%03X" % cid, "EMERGENCIA del nodo %d: %s" % (cid & 0x7F, " ".join(datos)))
except KeyboardInterrupt:
    pass
finally:
    vivo = False
    try:
        escribir("0")
    except serial.SerialException:
        pass
    f.close()
    print("\nlog: " + ruta)
