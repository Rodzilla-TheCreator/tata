#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · levanta DTR/RTS por fases y escucha. NUNCA escribe datos al puerto.

Segunda palanca, después de escucha_edr.py: si el puerto calla en las 54, se
prueba si el equipo espera ver a la PC (DTR/RTS arriba), como hacía Judit al
abrir el puerto desde Windows.

    Esto SÍ pone voltaje en los pines 4 (DTR) y 7 (RTS) del DB9.
    Decisión de maje, 29-sep-2026. DTR va solo primero; RTS después,
    porque el pin 7 es CAN_H en el pinout CiA-303.

Uso:

    py lineas_edr.py              # puerto único, se elige solo
    py lineas_edr.py COM9

Fases: base 10 s · DTR 15 s · RTS 15 s · ambas 20 s · fin 5 s. Registra los
bytes que lleguen y cualquier cambio en CTS/DSR/DCD/RI. Al terminar, o si se
corta a medias, DTR y RTS vuelven a bajo. Log en ./logs/, como escucha_edr.py.
"""

import datetime as dt
import os
import sys
import time

for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    sys.exit("Falta pyserial.  py -m pip install pyserial")

# A 115200 cualquier transmisión cae como bytes, aunque venga a otra velocidad.
BAUD = 115200

# (nombre, dtr, rts, segundos)
FASES = [
    ("base   DTR=0 RTS=0", False, False, 10),
    ("DTR    DTR=1 RTS=0", True,  False, 15),
    ("RTS    DTR=0 RTS=1", False, True,  15),
    ("AMBAS  DTR=1 RTS=1", True,  True,  20),
    ("fin    DTR=0 RTS=0", False, False, 5),
]


def elegir_puerto():
    if len(sys.argv) > 1:
        return sys.argv[1]
    cand = [p.device for p in serial.tools.list_ports.comports()]
    if len(cand) != 1:
        sys.exit("Puertos: %s — decí cuál:  py lineas_edr.py COM9"
                 % (", ".join(cand) or "ninguno (¿está enchufado el cable?)"))
    return cand[0]


def main():
    puerto = elegir_puerto()
    os.makedirs("logs", exist_ok=True)
    sello = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    ruta = os.path.join("logs", "edr-%s-lineas.log" % sello)
    f = open(ruta, "w", encoding="utf-8")
    t0 = time.time()

    def log(txt):
        txt = "[%7.2f] %s" % (time.time() - t0, txt)
        print(txt, flush=True)
        f.write(txt + "\n")
        f.flush()

    log("LÍNEAS · %s a %d · nunca se transmite un byte" % (puerto, BAUD))
    s = serial.Serial()
    s.port = puerto
    s.baudrate = BAUD
    s.timeout = 0.2
    s.dtr = False          # antes del open(), para no dar un pulso al abrir
    s.rts = False
    s.open()
    s.reset_input_buffer()
    total = 0
    try:
        for nombre, dtr, rts, seg in FASES:
            s.dtr, s.rts = dtr, rts
            log("═══ %s  (%d s)" % (nombre, seg))
            fin, n_fase, lineas = time.time() + seg, 0, None
            while time.time() < fin:
                d = s.read(s.in_waiting or 1)
                if d:
                    n_fase += len(d)
                    log("  %d bytes: %s" % (len(d), d[:48].hex(" ")))
                e = "CTS=%d DSR=%d DCD=%d RI=%d" % (s.cts, s.dsr, s.cd, s.ri)
                if e != lineas:
                    log("  líneas del equipo: " + e)
                    lineas = e
            log("  fase: %d bytes" % n_fase)
            total += n_fase
    except KeyboardInterrupt:
        log("Cortado a mano.")
    finally:
        s.dtr = False
        s.rts = False
        s.close()
        log("TOTAL %d bytes. DTR/RTS devueltos a bajo." % total)
        f.close()
        print("\nLog: %s" % ruta)


if __name__ == "__main__":
    main()
