#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · saludos inofensivos al puerto de servicio del EDR18N2

    ESTE PROGRAMA SÍ TRANSMITE. Es la primera herramienta del proyecto que
    le manda bytes al equipo. Decisión de maje, 30-sep-2026.

Qué manda, y nada más: una lista FIJA de saludos y lecturas, definida abajo
en SALUDOS. No acepta texto libre. Ningún saludo escribe parámetros: son
Enter, «?», «help», y lecturas CiA 309-3 del diccionario de objetos.

Por qué CiA 309-3: el manual dice que el «PC de servicio» es el nodo 30 de un
bus CANopen, y CiA 309-3 es el estándar para hablarle a CANopen por serie en
texto. Es una apuesta con fundamento, no un dato. Judit bien puede usar un
protocolo propio de Jungheinrich, y entonces nada de esto contesta.

Uso:

    py saludo_edr.py --seco          # muestra qué mandaría, sin abrir el puerto
    py saludo_edr.py --banco         # control: CON jumper 2-3 en el cable,
                                     # todo saludo tiene que volver como eco
    py saludo_edr.py                 # al equipo: 9 velocidades, 8N1
    py saludo_edr.py --baud 9600     # una sola velocidad
    py saludo_edr.py --dtr           # con DTR/RTS arriba, como Judit en Windows

Antes de transmitir pide escribir SI. Log en ./logs/, como escucha_edr.py.
"""

import argparse
import datetime as dt
import difflib
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


BAUDS = [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]

# (nombre, bytes). LA ÚNICA LISTA DE LO QUE SE PUEDE MANDAR.
# Agregar algo acá es decidir transmitirlo: nada de escrituras (w / write).
SALUDOS = [
    ("enter",            b"\r"),
    ("enter crlf",       b"\r\n"),
    ("?",                b"?\r\n"),
    ("help",             b"help\r\n"),
    ("309-3 tipo n30",   b"[1] 30 r 0x1000 0 u32\r\n"),   # 0x1000 = device type
    ("309-3 nombre n30", b"[2] 30 r 0x1008 0 vs\r\n"),    # 0x1008 = nombre del equipo
    ("309-3 tipo",       b"[3] r 0x1000 0 u32\r\n"),      # sin nodo: el por defecto
    ("309-3 versión",    b"[4] info version\r\n"),
]

ESPERA = 1.0      # segundos escuchando después de cada saludo
PAUSA = 0.3       # silencio entre saludos, para no atropellar


def texto(b):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


# El 30-sep-2026 el equipo devolvió cada saludo DEFORMADO: mismo largo, el texto
# nuestro con bits cambiados, peor cuanto más lenta la velocidad. No era una
# respuesta: era la señal de nuestro TX colándose al RX por algo del lado del
# equipo. El control con el cable al aire dio silencio, así que no es el cable.
# Desde entonces se separa lo que se parece a lo mandado de lo que no.
def clasificar(mandado, r):
    if r == mandado:
        return "eco"
    parecido = difflib.SequenceMatcher(None, mandado, r).ratio()
    if parecido >= 0.5:
        return "eco deformado"
    if abs(len(r) - len(mandado)) <= 1:
        return "¿eco? mismo largo"
    return "RESPUESTA"


def elegir_puerto(pedido):
    if pedido:
        return pedido
    cand = [p.device for p in serial.tools.list_ports.comports()]
    if len(cand) != 1:
        sys.exit("Puertos: %s — decí cuál con --puerto COM9"
                 % (", ".join(cand) or "ninguno (¿está enchufado el cable?)"))
    return cand[0]


def abrir(puerto, baud, dtr):
    s = serial.Serial()
    s.port = puerto
    s.baudrate = baud
    s.timeout = 0.1
    s.dtr = dtr          # antes del open(), para no dar un pulso al abrir
    s.rts = dtr
    s.open()
    s.reset_input_buffer()
    return s


def escuchar(s, segundos):
    datos = bytearray()
    fin = time.time() + segundos
    while time.time() < fin:
        datos += s.read(s.in_waiting or 1)
    return bytes(datos)


def main():
    ap = argparse.ArgumentParser(description="Saludos inofensivos al puerto del EDR18N2.")
    ap.add_argument("--puerto", help="COM9, … (si falta, se elige el único)")
    ap.add_argument("--baud", type=int, help="una sola velocidad")
    ap.add_argument("--dtr", action="store_true", help="DTR y RTS arriba, como Judit")
    ap.add_argument("--seco", action="store_true", help="mostrar qué se mandaría, sin abrir nada")
    ap.add_argument("--banco", action="store_true", help="control con jumper 2-3: espera eco")
    ap.add_argument("--si", action="store_true", help="no preguntar antes de transmitir")
    a = ap.parse_args()

    bauds = [a.baud] if a.baud else ([9600] if a.banco else BAUDS)

    if a.seco:
        print("SECO · no se abre ningún puerto. Esto es lo que se mandaría:\n")
        for nombre, b in SALUDOS:
            print("  %-17s %-32s %s" % (nombre, repr(b), b.hex(" ")))
        print("\n× %d velocidad(es), 8N1, DTR/RTS %s. %.0f s aprox."
              % (len(bauds), "arriba" if a.dtr else "abajo",
                 len(bauds) * len(SALUDOS) * (ESPERA + PAUSA + 0.1)))
        return

    puerto = elegir_puerto(a.puerto)

    if a.banco:
        print("BANCO · el cable tiene que tener el JUMPER 2-3 y NO estar en el equipo.")
    else:
        print("VA A TRANSMITIR AL EQUIPO por %s: %d saludos × %d velocidad(es)."
              % (puerto, len(SALUDOS), len(bauds)))
        print("Solo saludos y lecturas. Revisá: jumper FUERA, laptop a batería.")
    if not a.si and input("Escribí SI para seguir: ").strip().upper() != "SI":
        sys.exit("No se transmitió nada.")

    os.makedirs("logs", exist_ok=True)
    sello = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    ruta = os.path.join("logs", "edr-%s-%s.log" % (sello, "banco" if a.banco else "saludo"))
    f = open(ruta, "w", encoding="utf-8")
    t0 = time.time()

    def log(txt):
        txt = "[%7.2f] %s" % (time.time() - t0, txt)
        print(txt, flush=True)
        f.write(txt + "\n")
        f.flush()

    log("%s · %s · DTR/RTS %s · SE TRANSMITE"
        % ("BANCO" if a.banco else "SALUDO", puerto, "arriba" if a.dtr else "abajo"))
    respuestas, ecos, deformados, total = [], 0, 0, 0
    try:
        for baud in bauds:
            try:
                s = abrir(puerto, baud, a.dtr)
            except Exception as e:
                log("%6d  no abre: %s" % (baud, e))
                continue
            try:
                log("═══ %d 8N1" % baud)
                previo = escuchar(s, 0.3)        # lo que ya venía, antes de saludar
                if previo:
                    log("  ya venía algo: %d bytes |%s|" % (len(previo), texto(previo[:48])))
                for nombre, b in SALUDOS:
                    s.write(b)
                    s.flush()
                    total += 1
                    r = escuchar(s, ESPERA)
                    if not r:
                        log("  %-17s →  —" % nombre)
                    else:
                        clase = clasificar(b, r)
                        if clase == "eco":
                            ecos += 1
                            log("  %-17s →  ECO exacto" % nombre)
                        else:
                            log("  %-17s →  %-18s %d bytes |%s|"
                                % (nombre, clase, len(r), texto(r[:64])))
                            log("  %17s     %s" % ("", r[:48].hex(" ")))
                            if clase == "RESPUESTA":
                                respuestas.append((baud, nombre, r))
                            else:
                                deformados += 1
                    time.sleep(PAUSA)
            finally:
                s.close()
    except KeyboardInterrupt:
        log("Cortado a mano.")
    finally:
        log("─" * 60)
        log("Saludos mandados: %d · ecos exactos: %d · ecos deformados: %d · respuestas: %d"
            % (total, ecos, deformados, len(respuestas)))
        if a.banco:
            if total and ecos == total:
                log("BANCO PASÓ: el cable transmite y recibe. El instrumento sirve.")
            else:
                log("BANCO FALLÓ: con jumper, todo saludo tiene que volver igual.")
        else:
            if deformados and deformados + ecos >= len(respuestas):
                log("MAYORÍA ECO: el equipo devuelve lo mandado sin procesarlo. Es señal")
                log("colándose de TX a RX, no una respuesta. Las «RESPUESTA» sueltas a")
                log("velocidad baja probablemente son el mismo eco, más destrozado.")
            elif ecos and not deformados:
                log("OJO: hubo ECO exacto. ¿Quedó el jumper puesto en el cable?")
            if respuestas and not deformados:
                log("CONTESTÓ. No repetir a lo loco: pegar esto y leerlo antes de seguir.")
            elif respuestas:
                log("Hay %d «RESPUESTA»: revisarlas a mano antes de creerles." % len(respuestas))
            elif not ecos and not deformados:
                log("Silencio a todo. El puerto no contesta a estos saludos.")
        f.close()
        print("\nLog: %s" % ruta)


if __name__ == "__main__":
    main()
