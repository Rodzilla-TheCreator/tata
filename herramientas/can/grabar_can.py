#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · graba la salida de escucha_can.ino a herramientas/can/logs/, sin límite de tiempo.

Si el puerto se cae (USB movido, otro programa lo abrió), espera y se reconecta solo.
Ctrl-C para parar. Muestra todo en pantalla y lo guarda.

MARCAS: escribí en esta misma ventana lo que vas a hacer y Enter («palanca 1 arriba»).
Queda en el log como   >>> MARCA t=<ms del ESP32> · <hora> · <texto>
en la misma escala de tiempo que las tramas, para cruzar después qué cambió con cada acción.

    py grabar_can.py                 # COM6, 921600 baud
    py grabar_can.py COM7
    py grabar_can.py COM6 115200     # para un sketch viejo
    py grabar_can.py COM6 921600 multipiloto    # MODO GUION: te va diciendo qué hacer

MODO GUION: en pantalla solo salen los pasos y el resumen de cada 5 s (las tramas se
guardan todas en el log igual). Muestra el paso siguiente; Enter vacío = «empiezo este
paso» y queda marcado. Texto + Enter = marca libre.
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
baudios = int(sys.argv[2]) if len(sys.argv) > 2 else 921600
guion_nombre = sys.argv[3] if len(sys.argv) > 3 else None

GUIONES = {
    "multipiloto": [
        "llave on — después 20 s SIN TOCAR NADA (se graba el arranque)",
        "nada — 10 s quieto (referencia)",
        "north — 3 veces, después 10 s quieto",
        "south — 3 veces, después 10 s quieto",
        "east — 3 veces, después 10 s quieto",
        "west — 3 veces, después 10 s quieto",
        "trasero — el botón trasero 3 veces, después 10 s quieto",
        "palanca trasera — de tope a tope, despacio, 3 veces, después 10 s quieto",
        "palanca trasera lento — UNA vez, muy despacio de un tope al otro, después 10 s",
        "joystick full forward — 3 veces, soltando entre una y otra, después 10 s",
        "joystick full back — 3 veces, después 10 s",
        "joystick full left — 3 veces, después 10 s",
        "joystick full right — 3 veces, después 10 s",
        "fin",
    ],
}

# GUIONES CON TEMPORIZADOR: (acción, segundos). No hay que dar Enter: la pantalla avisa,
# cuenta, y marca INICIO y FIN solos. Entre paso y paso, 3 s de «prepárate».
TEMPORIZADOS = {
    "multipiloto_tiempo": [
        ("llave OFF y quieto", 10),
        ("llave ON y NO TOCAR NADA (se graba el arranque)", 20),
        ("nada, quieto", 8),
        ("north: apretar y soltar, 3 veces", 8),
        ("south: apretar y soltar, 3 veces", 8),
        ("east: apretar y soltar, 3 veces", 8),
        ("west: apretar y soltar, 3 veces", 8),
        ("trasero: apretar y soltar, 3 veces", 8),
        ("palanca trasera ADELANTE: del centro al tope y soltar, 3 veces", 10),
        ("palanca trasera ATRAS: del centro al tope y soltar, 3 veces", 10),
        ("joystick ADELANTE: al tope y soltar, 3 veces", 8),
        ("joystick ATRAS: al tope y soltar, 3 veces", 8),
        ("joystick IZQUIERDA: al tope y soltar, 3 veces", 8),
        ("joystick DERECHA: al tope y soltar, 3 veces", 8),
        ("nada, quieto", 8),
    ],
}
temporizado = TEMPORIZADOS.get(guion_nombre, None)
if temporizado:
    GUIONES[guion_nombre] = []
guion = GUIONES.get(guion_nombre, None)
modo_guion = guion_nombre is not None   # con o sin temporizador: la pantalla es solo para instrucciones
if guion_nombre and guion is None:
    sys.exit("No conozco el guion %r. Hay: %s" % (guion_nombre, ", ".join(GUIONES)))
paso = [0]
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
ruta = os.path.join(aqui, "logs", "escucha_equipo_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
print(ruta, flush=True)
f = open(ruta, "w", encoding="utf-8")
candado = threading.Lock()

# milisegundos del ESP32 de la última trama vista: la escala de tiempo de las marcas
ultimo_ms = [0]
TRAMA = re.compile(r"^\s*(\d+)\s+(?:EXT|   )\s[0-9A-F]{3}")


def escribir(texto):
    with candado:
        f.write(texto)
        f.flush()


def marca(txt):
    if not modo_guion:
        print("[grabar_can] " + txt, flush=True)
    escribir("\n[grabar_can %s] %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), txt))


def poner_marca(texto):
    m = ">>> MARCA t=%d · %s · %s" % (ultimo_ms[0], dt.datetime.now().strftime("%H:%M:%S"), texto)
    escribir("\n" + m + "\n")
    print(m, flush=True)


def correr_temporizado():
    time.sleep(8)   # deja que el ESP32 arranque y haga su barrido
    n = len(temporizado)
    for k, (accion, seg) in enumerate(temporizado, 1):
        print("", flush=True)
        print("", flush=True)
        print("========================================================", flush=True)
        print("  SIGUIENTE (%d/%d):  %s" % (k, n, accion), flush=True)
        print("========================================================", flush=True)
        for c in (3, 2, 1):
            print("  prepárate... %d" % c, flush=True)
            time.sleep(1)
        poner_marca("INICIO %d · %s" % (k, accion))
        print("", flush=True)
        print("  >>>>>>>>>>  AHORA:  %s  <<<<<<<<<<" % accion, flush=True)
        for r in range(seg, 0, -1):
            print("     %2d s" % r, flush=True)
            time.sleep(1)
        poner_marca("FIN %d · %s" % (k, accion))
        print("  ---- PARA. Suelta todo y quieto ----", flush=True)
        time.sleep(3)
    print("", flush=True)
    print("GUION TERMINADO. Ctrl-C para parar la grabación.", flush=True)


def mostrar_paso():
    if guion and paso[0] < len(guion):
        print("\n========================================================", flush=True)
        print("  PASO %d/%d:  %s" % (paso[0] + 1, len(guion), guion[paso[0]]), flush=True)
        print("  -> Enter JUSTO cuando empieces", flush=True)
        print("========================================================", flush=True)


def marcas_del_teclado():
    for linea in sys.stdin:
        texto = linea.strip()
        if guion and not texto and paso[0] < len(guion):
            poner_marca("PASO %d · %s" % (paso[0] + 1, guion[paso[0]].split(" — ")[0]))
            paso[0] += 1
            mostrar_paso()
            if paso[0] >= len(guion):
                print("\nGuion terminado. Ctrl-C para parar la grabación.", flush=True)
        elif texto:
            poner_marca(texto)


threading.Thread(target=marcas_del_teclado, daemon=True).start()
if temporizado:
    threading.Thread(target=correr_temporizado, daemon=True).start()
else:
    mostrar_paso()

try:
    while True:
        try:
            s = serial.Serial(puerto, baudios, timeout=0.5)
            marca("puerto %s abierto a %d (el ESP32 se reinicia y hace el barrido)" % (puerto, baudios))
            resto = ""
            while True:
                d = s.read(8192)
                if not d:
                    continue
                t = d.decode("utf-8", "replace")
                lineas = (resto + t).split("\n")
                resto = lineas.pop()
                for l in lineas:
                    m = TRAMA.match(l)
                    if m:
                        ultimo_ms[0] = int(m.group(1))
                escribir(t)
                if modo_guion:
                    pass   # en modo guion la pantalla es solo para las instrucciones
                else:
                    sys.stdout.write(t)
                    sys.stdout.flush()
        except serial.SerialException as e:
            marca("puerto caído: %s — reintento en 2 s" % e)
            time.sleep(2)
except KeyboardInterrupt:
    marca("parado a mano")
finally:
    f.close()
