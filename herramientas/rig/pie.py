"""pie.py — manda el latido del pie al ESP (pie.ino) y deja pisar / soltar desde el teclado.

Embrión de rig.py: la línea de estado completo cada 50 ms es mando y latido a la vez
(herramientas/rig/tarea_firmware.md, regla 1). Hoy solo lleva el pie; los demás campos van en cero.

    python pie.py COM5            (Windows)      python pie.py /dev/ttyUSB0   (Linux)

Teclas:  p = pisar   s = soltar   m = matar el latido (prueba del watchdog)   v = volver a mandar
         q o Ctrl-C = pie suelto y salir
El rearme NO está en el teclado a propósito: es el botón del GPIO32 (regla 3, rearme manual).
"""
import sys
import time
import threading

import serial

PERIODO = 0.050


class Teclado:
    def __enter__(self):
        if sys.platform == "win32":
            import msvcrt
            self._lee = lambda: msvcrt.getwch() if msvcrt.kbhit() else None
        else:
            import termios, tty, select
            self._fd = sys.stdin.fileno()
            self._viejo = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
            self._lee = lambda: sys.stdin.read(1) if select.select([sys.stdin], [], [], 0)[0] else None
        return self

    def tecla(self):
        return self._lee()

    def __exit__(self, *a):
        if sys.platform != "win32":
            import termios
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._viejo)


def linea(pie):
    # mismos campos que rig.py; solo pie= se usa hoy
    return f"L a=0 t=0 i=0 d=0 b=0 r=0 pie={1 if pie else 0}\n".encode()


def lector(ser, alto):
    while not alto.is_set():
        try:
            s = ser.readline().decode(errors="replace").strip()
        except serial.SerialException:
            return
        if s:
            print(f"  ESP | {s}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    ser = serial.Serial()
    ser.port = sys.argv[1]
    ser.baudrate = 115200
    ser.timeout = 0.1
    ser.dtr = False          # no tocar EN ni GPIO0 al abrir
    ser.rts = False
    ser.open()

    alto = threading.Event()
    threading.Thread(target=lector, args=(ser, alto), daemon=True).start()

    pie, latido = False, True
    print("p pisar · s soltar · m matar latido · v volver · q salir  (rearme: botón GPIO32)")
    proximo = time.monotonic()
    try:
        with Teclado() as t:
            while True:
                k = t.tecla()
                if k == "p": pie = True;  print(">> pisar")
                elif k == "s": pie = False; print(">> soltar")
                elif k == "m": latido = False; print(">> latido MUERTO (el ESP tiene que soltar en <= 200 ms)")
                elif k == "v": latido = True;  print(">> latido de vuelta (el pie sigue suelto hasta el rearme)")
                elif k in ("q", "\x03"): break
                if latido:
                    ser.write(linea(pie))
                proximo += PERIODO
                time.sleep(max(0.0, proximo - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        for _ in range(3):           # Ctrl-C = pie suelto antes de cerrar
            ser.write(linea(False))
            time.sleep(PERIODO)
        alto.set()
        ser.close()
        print("pie suelto, cerrado")


if __name__ == "__main__":
    main()
