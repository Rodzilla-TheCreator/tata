#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaTa · visor tipo cansniffer sobre la salida de escucha_can.ino (LISTEN_ONLY, 921600).

Una fila por COB-ID, ordenada, redibujada EN SU LUGAR (~10 Hz, sin scroll). Los bytes que
cambiaron hace menos de 1 s salen en INVERTIDO y se apagan solos. Columna «hace» = cuánto
pasó desde el último cambio de datos de esa fila.

    py visor_can.py              # COM6
    py visor_can.py COM7
    py visor_can.py --log logs\escucha_equipo_X.log    # reproduce un log grabado (prueba)

TECLAS
    m   marca: escribís el texto + Enter (Esc cancela). Queda en el log con t del ESP32
    f   filtro: solo candidatos de dirección (184/5/6, 284/5/6, 704/5/6 y sus RPDO 204/5/6,
        304/5/6). Otra vez f = todo
    r   ruido: los bytes que cambiaron en los últimos 3 s pasan a «ruidosos» (gris, sin
        resaltar). Con todo quieto, r → después solo se enciende lo que movés. R lo limpia
    q   salir

LOG: todas las tramas crudas, con la hora de la laptop delante, a logs\direccion_<fecha>.log
(los .log no se versionan).
"""
import datetime as dt
import os
import re
import shutil
import sys
import threading
import time

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

if os.name == "nt":
    import msvcrt
    os.system("")                       # activa las secuencias ANSI en la consola de Windows
else:
    import select
    import termios
    import tty

RESALTE_S = 1.0
RUIDO_S = 3.0
REFRESCO_S = 0.1
CANDIDATOS = {0x184, 0x185, 0x186, 0x284, 0x285, 0x286, 0x704, 0x705, 0x706,
              0x204, 0x205, 0x206, 0x304, 0x305, 0x306}

TRAMA = re.compile(r"^\s*(\d+)\s+(?:EXT\s+)?([0-9A-F]{3,8})\s+\[(\d)\]((?: [0-9A-F]{2})*)\s*(.*)$")
RESUMEN = re.compile(r"resumen (\d+) s .* err RX (\d+) .* perdidas (\d+)")

INV, GRIS, NEG, FIN = "\x1b[7m", "\x1b[90m", "\x1b[1m", "\x1b[0m"


class Fila:
    __slots__ = ("dlc", "datos", "nombre", "cambio", "ultimo_cambio", "n", "ruido")

    def __init__(self, nombre):
        self.dlc, self.datos, self.nombre, self.n = 0, [], nombre, 0
        self.cambio = [0.0] * 8              # hora (laptop) del último cambio de cada byte
        self.ultimo_cambio = 0.0
        self.ruido = [False] * 8


filas = {}
cerrojo = threading.Lock()
estado = {"esp_ms": 0, "err": "0", "perdidas": "0", "tramas": 0, "fin": False, "aviso": ""}

modo_log = "--log" in sys.argv
if modo_log:
    fuente = sys.argv[sys.argv.index("--log") + 1]
    puerto = None
else:
    puerto = next((a for a in sys.argv[1:] if not a.startswith("-")), "COM6")

aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
ruta = os.path.join(aqui, "logs", "direccion_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
log = open(ruta, "w", encoding="utf-8")


def escribir_log(texto):
    with cerrojo:
        if not log.closed:
            log.write(texto + "\n")


def procesar(linea):
    ahora = time.time()
    m = TRAMA.match(linea)
    if not m:
        r = RESUMEN.search(linea)
        if r:
            estado["err"], estado["perdidas"] = r.group(2), r.group(3)
        return
    t, cid, dlc = int(m.group(1)), int(m.group(2), 16), int(m.group(3))
    datos = m.group(4).split()
    nombre = re.sub(r"\bnodo \d+\s*", "", m.group(5)).strip()
    estado["esp_ms"] = t
    estado["tramas"] += 1
    with cerrojo:
        f = filas.get(cid)
        if f is None:
            f = filas[cid] = Fila(nombre)
        if f.n:
            for i in range(max(len(datos), len(f.datos))):
                a = datos[i] if i < len(datos) else None
                b = f.datos[i] if i < len(f.datos) else None
                if a != b and i < 8:
                    f.cambio[i] = ahora
                    f.ultimo_cambio = ahora
        f.dlc, f.datos, f.n = dlc, datos, f.n + 1


def lector_serie():
    import serial
    try:
        s = serial.Serial(puerto, 921600, timeout=0.2)
    except serial.SerialException as e:
        estado["aviso"] = "no se pudo abrir %s: %s" % (puerto, e)
        estado["fin"] = True
        return
    while not estado["fin"]:
        try:
            l = s.readline().decode("utf-8", "replace").rstrip()
        except serial.SerialException as e:
            estado["aviso"] = "se cayó el puerto: %s" % e
            time.sleep(1)
            continue
        if not l:
            continue
        escribir_log("%s %s" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], l))
        procesar(l)
    s.close()


def lector_log():
    """Reproduce un log grabado a la velocidad real del ESP32 (para probar el visor)."""
    t0 = None
    inicio = time.time()
    with open(fuente, encoding="utf-8", errors="replace") as f:
        for l in f:
            if estado["fin"]:
                return
            l = l.rstrip()
            m = TRAMA.match(l)
            if m:
                t = int(m.group(1))
                t0 = t if t0 is None else t0
                espera = (t - t0) / 1000.0 - (time.time() - inicio)
                if espera > 0:
                    time.sleep(espera)
            escribir_log(l)
            procesar(l)
    estado["aviso"] = "fin del log"


def tecla():
    if os.name == "nt":
        return msvcrt.getwch() if msvcrt.kbhit() else None
    return sys.stdin.read(1) if select.select([sys.stdin], [], [], 0)[0] else None


def dibujar(filtro, entrada):
    ancho, alto = shutil.get_terminal_size((100, 40))
    ahora = time.time()
    out = ["\x1b[H"]
    cab = " visor_can · %s · t ESP %d s · tramas %d · err RX %s · perdidas %s · filtro %s" % (
        puerto or os.path.basename(fuente), estado["esp_ms"] // 1000, estado["tramas"],
        estado["err"], estado["perdidas"], "DIRECCION" if filtro else "todo")
    out.append(NEG + cab[:ancho - 1] + FIN + "\x1b[K\n")
    out.append(" m marca · f filtro · r ruido (R limpia) · q salir    log: %s\x1b[K\n" % os.path.basename(ruta))
    out.append(GRIS + "  ID   nombre                     dlc  datos                     hace     n" + FIN + "\x1b[K\n")
    with cerrojo:
        ids = sorted(i for i in filas if not filtro or i in CANDIDATOS)
        cupo = alto - 6
        for cid in ids[:cupo]:
            f = filas[cid]
            bs = []
            for i in range(8):
                if i >= len(f.datos):
                    bs.append("  ")
                elif f.ruido[i]:
                    bs.append(GRIS + f.datos[i] + FIN)
                elif ahora - f.cambio[i] < RESALTE_S:
                    bs.append(INV + f.datos[i] + FIN)
                else:
                    bs.append(f.datos[i])
            if f.ultimo_cambio:
                h = ahora - f.ultimo_cambio
                hace = ("%5.1f s" % h) if h < 600 else "  >10m"
            else:
                hace = "   ---"
            idt = ("%03X" % cid)
            if f.ultimo_cambio and ahora - f.ultimo_cambio < RESALTE_S:
                idt = NEG + idt + FIN
            out.append("  %s  %-26.26s [%d]  %s  %s %6d\x1b[K\n" % (
                idt, f.nombre, f.dlc, " ".join(bs), hace, f.n))
        sobran = len(ids) - cupo
    if sobran > 0:
        out.append(GRIS + "  … %d filas más (agrandá la ventana o f para filtrar)" % sobran + FIN + "\x1b[K\n")
    if entrada is not None:
        out.append("\x1b[K\n" + NEG + " MARCA> " + FIN + entrada + "\x1b[K")
    elif estado["aviso"]:
        out.append("\x1b[K\n " + estado["aviso"] + "\x1b[K")
    out.append("\x1b[J")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def main():
    viejo = None
    if os.name != "nt":
        viejo = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    threading.Thread(target=lector_log if modo_log else lector_serie, daemon=True).start()
    sys.stdout.write("\x1b[?25l\x1b[2J")
    filtro, entrada = False, None
    try:
        while not estado["fin"]:
            k = tecla()
            while k is not None:
                if entrada is not None:
                    if k in ("\r", "\n"):
                        if entrada.strip():
                            escribir_log(">>> MARCA t=%d · %s · %s" % (
                                estado["esp_ms"], dt.datetime.now().strftime("%H:%M:%S"), entrada.strip()))
                            estado["aviso"] = "marca: " + entrada.strip()
                        entrada = None
                    elif k == "\x1b":
                        entrada = None
                    elif k in ("\b", "\x7f"):
                        entrada = entrada[:-1]
                    elif k.isprintable():
                        entrada += k
                elif k == "q":
                    estado["fin"] = True
                elif k == "m":
                    entrada = ""
                elif k == "f":
                    filtro = not filtro
                    sys.stdout.write("\x1b[2J")
                elif k == "r":
                    ahora = time.time()
                    with cerrojo:
                        for f in filas.values():
                            f.ruido = [f.ruido[i] or ahora - f.cambio[i] < RUIDO_S for i in range(8)]
                    estado["aviso"] = "ruido marcado (gris): lo que cambió en los últimos %d s" % RUIDO_S
                elif k == "R":
                    with cerrojo:
                        for f in filas.values():
                            f.ruido = [False] * 8
                    estado["aviso"] = "ruido limpiado"
                k = tecla()
            dibujar(filtro, entrada)
            time.sleep(REFRESCO_S)
    except KeyboardInterrupt:
        pass
    finally:
        estado["fin"] = True
        if viejo:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, viejo)
        sys.stdout.write(FIN + "\x1b[?25h\n")
        with cerrojo:
            log.close()
        if estado["aviso"]:
            print(estado["aviso"])
        print("log: " + ruta)


if __name__ == "__main__":
    main()
