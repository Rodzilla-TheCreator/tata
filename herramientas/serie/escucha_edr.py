#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaTa · escucha del puerto de servicio del EDR18N2 — cable FTDI directo a USB

El cable es el que el chino usaba con Judit: DB9 macho → USB, chip FTDI.
Confirmado por él el 25-sep-2026. Va DIRECTO, sin null-modem, como él lo usaba.

    SOLO ESCUCHA. Este programa nunca escribe al puerto.
    Tampoco levanta DTR ni RTS: se dejan en bajo antes de abrir.

Uso:

    python escucha_edr.py --listar
    python escucha_edr.py --barrido                  # las 54 combinaciones
    python escucha_edr.py --fijo 9600 8N1            # clavado, para el menú
    python escucha_edr.py --estimulo 9600 8N1        # clavado + marcas a mano

Cada corrida escribe un log con marca de tiempo en ./logs/.
Requiere pyserial:  pip install pyserial
"""

import argparse
import datetime as dt
import os
import sys
import time

# La consola de Windows arranca en cp1252 y revienta con UnicodeEncodeError
# en el primer «·» o «─» que se imprima. Es el mismo bug de encoding que se
# corrigió en build_sec.py. Acá se corre en la i3, que es Windows, así que se
# fuerza utf-8 antes de imprimir nada. errors="replace" para que un carácter
# raro degrade a «?» en vez de matar una corrida en el taller.
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


# ── combinaciones ─────────────────────────────────────────────────────────
# Las mismas nueve velocidades del sketch. El techo de 14400 era del CH340,
# no del equipo: el FT232 llega a 3 Mbaud, así que por primera vez el barrido
# pasa de 14400 de verdad.
BAUDS = [1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]

# nombre → (bytesize, parity, stopbits)
CFGS = {
    "8N1": (serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE),
    "8E1": (serial.EIGHTBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE),
    "8O1": (serial.EIGHTBITS, serial.PARITY_ODD,  serial.STOPBITS_ONE),
    "7E1": (serial.SEVENBITS, serial.PARITY_EVEN, serial.STOPBITS_ONE),
    "7O1": (serial.SEVENBITS, serial.PARITY_ODD,  serial.STOPBITS_ONE),
    "8N2": (serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_TWO),
}

VENTANA = 3.0        # segundos de escucha por combinación en el barrido
ANCHO_HEX = 16       # bytes por renglón del volcado


# ── log ───────────────────────────────────────────────────────────────────
class Log:
    """Escribe a pantalla y a archivo al mismo tiempo."""

    def __init__(self, etiqueta):
        os.makedirs("logs", exist_ok=True)
        sello = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.ruta = os.path.join("logs", "edr-%s-%s.log" % (sello, etiqueta))
        self.f = open(self.ruta, "w", encoding="utf-8")
        self.t0 = time.time()

    def __call__(self, txt="", marca=False):
        if marca:
            txt = "[%8.3f] %s" % (time.time() - self.t0, txt)
        print(txt)
        self.f.write(txt + "\n")
        self.f.flush()

    def cerrar(self):
        self.f.close()


# ── puerto ────────────────────────────────────────────────────────────────
def listar():
    puertos = list(serial.tools.list_ports.comports())
    if not puertos:
        print("No hay puertos serie. ¿Está enchufado el cable?")
        return []
    print("Puertos:")
    for p in puertos:
        print("  %-14s  %s" % (p.device, p.description))
    return [p.device for p in puertos]


def abrir(puerto, baud, cfg):
    """Abre en solo-lectura efectiva, con DTR y RTS en bajo.

    pyserial afirma DTR/RTS al abrir en varias plataformas. Poniéndolos en
    False ANTES del open() se guardan en la configuración y se aplican ahí,
    en vez de dar un pulso al equipo. Levantar esas líneas sí sería meter
    señal al montacargas, y eso no se hace sin decidirlo aparte.
    """
    bits, par, stop = CFGS[cfg]
    s = serial.Serial()
    s.port = puerto
    s.baudrate = baud
    s.bytesize = bits
    s.parity = par
    s.stopbits = stop
    s.timeout = 0.2
    s.dtr = False
    s.rts = False
    s.open()
    s.reset_input_buffer()
    return s


def leer(s, segundos):
    """Junta todo lo que llegue en la ventana. Nunca escribe."""
    datos = bytearray()
    fin = time.time() + segundos
    while time.time() < fin:
        n = s.in_waiting
        if n:
            datos += s.read(n)
        else:
            datos += s.read(1)   # bloquea hasta timeout, no quema CPU
    return bytes(datos)


# ── calificación ──────────────────────────────────────────────────────────
def legible(datos):
    """% de bytes que son texto imprimible o salto de línea."""
    if not datos:
        return 0
    ok = sum(1 for b in datos
             if 32 <= b < 127 or b in (10, 13, 9))
    return (100 * ok) // len(datos)

# Una velocidad equivocada devuelve basura: los bits se parten mal y salen
# valores repartidos por todo el rango, casi siempre con el bit alto puesto.
# La velocidad correcta devuelve estructura. Ninguna de las dos señales sola
# alcanza, así que se reportan ambas y decide el ojo.
def alto(datos):
    """% de bytes con el bit 7 puesto. Mucho 0x80+ huele a baud errado."""
    if not datos:
        return 0
    return (100 * sum(1 for b in datos if b & 0x80)) // len(datos)


def distintos(datos):
    """Cuántos valores distintos. Una línea en reposo mal leída suele dar 1 o 2."""
    return len(set(datos))


def volcar(log, datos, limite=256):
    trozo = datos[:limite]
    for i in range(0, len(trozo), ANCHO_HEX):
        fila = trozo[i:i + ANCHO_HEX]
        hexa = " ".join("%02X" % b for b in fila)
        txt = "".join(chr(b) if 32 <= b < 127 else "." for b in fila)
        log("    %04X  %-*s  |%s|" % (i, ANCHO_HEX * 3 - 1, hexa, txt))
    if len(datos) > limite:
        log("    ... %d bytes más" % (len(datos) - limite))


# ── modos ─────────────────────────────────────────────────────────────────
def barrido(puerto, log):
    log("BARRIDO · %d velocidades × %d encuadres = %d combinaciones"
        % (len(BAUDS), len(CFGS), len(BAUDS) * len(CFGS)))
    log("Ventana de %.1f s cada una. Total ~%.0f s."
        % (VENTANA, VENTANA * len(BAUDS) * len(CFGS)))
    log("Puerto: %s" % puerto)
    log("")

    hallazgos = []
    for baud in BAUDS:
        for cfg in CFGS:
            # Un encuadre que el driver no acepta tira termios.error, que NO
            # es SerialException. Si no se atrapa ancho, el barrido se muere a
            # media pasada en vez de saltarse esa combinación — y eso pasa en
            # el equipo, con los paneles abiertos y el tiempo corriendo.
            try:
                s = abrir(puerto, baud, cfg)
            except Exception as e:
                log("  %6d %s  no la acepta el driver: %s"
                    % (baud, cfg, type(e).__name__))
                continue
            try:
                datos = leer(s, VENTANA)
            except Exception as e:
                log("  %6d %s  falló al leer: %s" % (baud, cfg, e))
                datos = b""
            finally:
                s.close()

            if not datos:
                log("  %6d %s  —" % (baud, cfg))
                continue

            pl, pa, nd = legible(datos), alto(datos), distintos(datos)
            log("  %6d %s  %5d bytes · %3d%% legible · %3d%% bit7 · %d valores"
                % (baud, cfg, len(datos), pl, pa, nd))
            volcar(log, datos, 128)
            hallazgos.append((len(datos), pl, pa, nd, baud, cfg, datos))

    log("")
    log("─" * 70)
    if not hallazgos:
        log("SILENCIO EN LAS 54.")
        log("")
        log("Antes de concluir que el puerto no habla, en este orden:")
        log("  1. ¿Pasó el loopback el cable?  (jumper 2-3 + probador.py)")
        log("     Si no se validó, este silencio no dice nada del equipo.")
        log("  2. ¿Está encendido el equipo? El puerto no habla apagado.")
        log("  3. Repetir mientras se navega Settings → Menu → Drive:")
        log("     --fijo, y probar si el puerto solo habla cuando el display habla.")
        log("  4. A esta máquina le falta la válvula de temperatura de aceite.")
        log("     Un controlador en falla puede no levantar todo su stack.")
        log("     Eso es candidato a explicación, NO prueba de puerto muerto.")
        log("  5. Última palanca: levantar DTR/RTS. Eso SÍ mete señal al")
        log("     equipo — se decide aparte, no se hace de corrido.")
    else:
        log("HABLÓ. Combinaciones ordenadas por lo que más parece estructura:")
        # más bytes y más legible arriba; mucho bit7 y pocos valores, abajo
        hallazgos.sort(key=lambda h: (h[1], h[0], -h[2]), reverse=True)
        for n, pl, pa, nd, baud, cfg, _ in hallazgos[:8]:
            log("  %6d %s  %5d bytes · %3d%% legible · %3d%% bit7 · %d valores"
                % (baud, cfg, n, pl, pa, nd))
        log("")
        log("El ganador no es el que más bytes da: una velocidad equivocada")
        log("puede dar más basura que la correcta datos buenos. Se elige el que")
        log("repite estructura, y se confirma con --fijo dos veces.")
    log("─" * 70)


def fijo(puerto, baud, cfg, log, segundos=None):
    log("FIJO · %d %s en %s" % (baud, cfg, puerto))
    log("Ctrl-C para parar. Todo queda en %s" % log.ruta)
    log("")
    s = abrir(puerto, baud, cfg)
    total = 0
    fin = None if segundos is None else time.time() + segundos
    try:
        while fin is None or time.time() < fin:
            datos = leer(s, 1.0)
            if datos:
                total += len(datos)
                log("%d bytes (total %d)" % (len(datos), total), marca=True)
                volcar(log, datos)
    except KeyboardInterrupt:
        log("")
        log("Cortado a mano.")
    finally:
        s.close()
    log("")
    log("Total recibido: %d bytes" % total)


def estimulo(puerto, baud, cfg, log):
    """Escucha clavada mientras se provoca al equipo, marcando cada acción.

    La pregunta que contesta: ¿el puerto habla solo, o solo contesta?
    Si el flujo se mueve con una acción, es telemetría viva. Si solo se mueve
    con el menú del tablero, habla cuando el display habla.
    """
    guion = [
        "línea base: nada, quieto 30 s",
        "girar el timón tope a tope (EPS, anda aunque no ruede)",
        "subir y bajar las uñas",
        "pisar y soltar el hombre-presente",
        "Settings → Menu → Drive → diagnóstico",
        "provocar/leer el código de falla en el display",
    ]
    log("ESTÍMULO · %d %s en %s" % (baud, cfg, puerto))
    log("")
    log("Cada paso: hacé la acción, y cuando termines dale ENTER.")
    log("El log queda con marca de tiempo, así que después se cruza")
    log("cada acción contra lo que salió del puerto.")
    log("")

    s = abrir(puerto, baud, cfg)
    try:
        for i, paso in enumerate(guion, 1):
            log("")
            log("═══ PASO %d/%d · %s" % (i, len(guion), paso), marca=True)
            print("      (hacelo, después ENTER)")
            antes = time.time()
            # se escucha mientras el operador actúa: se lee en tandas cortas
            # hasta que entre el ENTER. input() bloquea, así que se drena
            # primero lo acumulado y se vuelve a drenar al volver.
            try:
                input()
            except KeyboardInterrupt:
                log("Cortado a mano."); break
            datos = b""
            if s.in_waiting:
                datos = s.read(s.in_waiting)
            datos += leer(s, 0.5)
            log("  %.1f s, %d bytes" % (time.time() - antes, len(datos)),
                marca=True)
            if datos:
                log("  %3d%% legible · %3d%% bit7 · %d valores"
                    % (legible(datos), alto(datos), distintos(datos)))
                volcar(log, datos)
            else:
                log("  nada")
    finally:
        s.close()
    log("")
    log("Cruzá las marcas de tiempo: si algún paso movió el flujo y la línea")
    log("base no, el puerto responde a esa acción. Eso es lo que se buscaba.")


# ── main ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Escucha pasiva del puerto de servicio del EDR18N2.")
    ap.add_argument("--puerto", help="COM3, /dev/ttyUSB0, … (si falta, se elige el único)")
    ap.add_argument("--listar", action="store_true", help="listar puertos y salir")
    ap.add_argument("--barrido", action="store_true", help="las 54 combinaciones")
    ap.add_argument("--fijo", nargs=2, metavar=("BAUD", "CFG"),
                    help="clavado en una combinación, p.ej. --fijo 9600 8N1")
    ap.add_argument("--estimulo", nargs=2, metavar=("BAUD", "CFG"),
                    help="clavado + guion de acciones marcadas a mano")
    ap.add_argument("--segundos", type=float, help="tope de tiempo para --fijo")
    a = ap.parse_args()

    if a.listar:
        listar()
        return

    puerto = a.puerto
    if not puerto:
        cand = [p.device for p in serial.tools.list_ports.comports()]
        if len(cand) == 1:
            puerto = cand[0]
            print("Puerto único: %s" % puerto)
        else:
            listar()
            sys.exit("Decí cuál con --puerto")

    if a.fijo or a.estimulo:
        baud, cfg = a.fijo or a.estimulo
        baud = int(baud)
        cfg = cfg.upper()
        if cfg not in CFGS:
            sys.exit("Encuadre desconocido: %s. Opciones: %s"
                     % (cfg, ", ".join(CFGS)))
        etiqueta = "estimulo" if a.estimulo else "fijo"
        log = Log("%s-%d-%s" % (etiqueta, baud, cfg))
        try:
            # misma razón que en el barrido: el error de encuadre no es
            # SerialException, y acá conviene que se lea claro y no como traza

            try:
                if a.estimulo:
                    estimulo(puerto, baud, cfg, log)
                else:
                    fijo(puerto, baud, cfg, log, a.segundos)
            except Exception as e:
                log("FALLÓ: %s: %s" % (type(e).__name__, e))
                log("Si es un encuadre, probá 8N1, que lo acepta todo driver.")
        finally:
            log.cerrar()
            print("\nLog: %s" % log.ruta)
        return

    # por defecto, barrido
    log = Log("barrido")
    try:
        barrido(puerto, log)
    finally:
        log.cerrar()
        print("\nLog: %s" % log.ruta)


if __name__ == "__main__":
    main()
