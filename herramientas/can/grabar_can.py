#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · graba la salida de escucha_can.ino a herramientas/can/logs/, sin límite de tiempo.

Si el puerto se cae (USB movido, otro programa lo abrió), espera y se reconecta solo.
Ctrl-C para parar. Muestra todo en pantalla y lo guarda. Para mirarlo desde otra terminal:
    Get-Content -Path logs\<archivo>.log -Encoding UTF8 -Tail 30 -Wait

    py grabar_can.py            # COM6 por defecto
    py grabar_can.py COM7
"""
import datetime as dt, os, sys, time
import serial

for _f in (sys.stdout, sys.stderr):
    try: _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

puerto = sys.argv[1] if len(sys.argv) > 1 else "COM6"
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
ruta = os.path.join(aqui, "logs", "escucha_equipo_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
print(ruta, flush=True)
f = open(ruta, "w", encoding="utf-8")

def marca(txt):
    print("[grabar_can] " + txt, flush=True)
    f.write("\n[grabar_can %s] %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), txt)); f.flush()

try:
    while True:
        try:
            s = serial.Serial(puerto, 115200, timeout=0.5)
            marca("puerto %s abierto (el ESP32 se reinicia y hace el barrido)" % puerto)
            while True:
                d = s.read(8192)
                if d:
                    t = d.decode("utf-8", "replace")
                    f.write(t); f.flush()
                    sys.stdout.write(t); sys.stdout.flush()
        except serial.SerialException as e:
            marca("puerto caído: %s — reintento en 2 s" % e)
            time.sleep(2)
except KeyboardInterrupt:
    marca("parado a mano")
finally:
    f.close()
