#!/usr/bin/env python3
"""multipiloto_gui.py — ventana para manejar multipiloto_campo.ino (nodo 2 falso) en el equipo.

    py multipiloto_gui.py            (COM6)        py multipiloto_gui.py COM7

Es campo_nodo2.py con mouse: mismo sketch, mismo protocolo, mismas reglas.
  · «Armar» (con la llave en OFF) manda 'A': el ESP pasa de solo escucha a modo normal.
  · Joystick: arrastrar el punto. Arriba = a N (adelante), abajo = t N, izquierda = i N, derecha = d N.
    Al soltar el mouse vuelve a cero.
  · N S E W y pito: solo mientras se aprietan (al soltar, '0').
  · ESPACIO o el botón rojo = todo a cero. NO reemplaza al paro de hongo.
  · Manda '.' cada 50 ms: si esta ventana se cae, el watchdog del ESP (200 ms) pone el 0x182 en cero.
  · Si la ventana pierde el foco, todo a cero. Al cerrar: '0' y 'X' (vuelve a solo escucha).
Log crudo en herramientas/can/logs/multipiloto_gui_<fecha>.log.
"""
import datetime as dt
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

import serial

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM6"
PERIODO_MS = 50
R = 110                      # radio del joystick en píxeles
NOMBRE = {1: "Master", 2: "nosotros (nodo 2)", 3: "pantalla", 4: "dirección", 7: "elevación",
          8: "tracción", 30: "nodo 30"}
ESTADOS = {"0": "SIN BOOT", "1": "PRE-OPERACIONAL", "2": "OPERACIONAL", "3": "PARADO"}
TRAMA = re.compile(r"^(\d+) ([0-9A-F]{3}) \[(\d)\]((?: [0-9A-F]{2})*)$")

aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
log = open(os.path.join(aqui, "logs", "multipiloto_gui_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S")),
           "w", encoding="utf-8")

ser = serial.Serial()
ser.port, ser.baudrate, ser.timeout = PUERTO, 921600, 0.2
ser.dtr = ser.rts = False
ser.open()
entrada = queue.Queue()
vivo = True


def lector():
    while vivo:
        try:
            linea = ser.readline().decode("utf-8", "replace").strip()
        except Exception as e:  # el USB se cayó
            entrada.put("# GUI: se cortó el USB (%s)" % e)
            return
        if linea:
            log.write(linea + "\n")
            entrada.put(linea)


threading.Thread(target=lector, daemon=True).start()


def mandar(texto):
    try:
        ser.write((texto + "\n").encode())
    except Exception:
        pass
    log.write(">>> %s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], texto))


class Ventana:
    def __init__(self, raiz):
        self.raiz = raiz
        self.armado = False
        self.y = self.x = 0          # -255..255 (y + = adelante, x + = derecha)
        self.enviado = (None, None)
        self.tramas = 0
        self.tTramas = time.time()
        self.nodos = {}
        raiz.title("Multipiloto falso (nodo 2) · %s" % PUERTO)
        raiz.configure(bg="#1e2228")

        izq = tk.Frame(raiz, bg="#1e2228"); izq.pack(side="left", padx=12, pady=12)
        der = tk.Frame(raiz, bg="#1e2228"); der.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        self.bArmar = tk.Button(izq, text="ARMAR (llave en OFF)", font=("Segoe UI", 12, "bold"),
                                bg="#2e7d32", fg="white", command=self.armar)
        self.bArmar.pack(fill="x", pady=(0, 8))

        self.c = tk.Canvas(izq, width=2 * R + 20, height=2 * R + 20, bg="#2a2f37", highlightthickness=0)
        self.c.pack()
        cx = cy = R + 10
        self.c.create_oval(cx - R, cy - R, cx + R, cy + R, outline="#5b6573", width=2)
        self.c.create_line(cx - R, cy, cx + R, cy, fill="#3c444f")
        self.c.create_line(cx, cy - R, cx, cy + R, fill="#3c444f")
        for t, xx, yy in (("adelante (a)", cx, 4), ("atrás (t)", cx, 2 * R + 16), ("izq (i)", 6, cy), ("der (d)", 2 * R + 14, cy)):
            self.c.create_text(xx, yy, text=t, fill="#9aa4b1", font=("Segoe UI", 9),
                               anchor={"adelante (a)": "n", "atrás (t)": "s", "izq (i)": "w", "der (d)": "e"}[t])
        self.punto = self.c.create_oval(cx - 14, cy - 14, cx + 14, cy + 14, fill="#f0b429", outline="")
        self.c.bind("<B1-Motion>", self.arrastrar)
        self.c.bind("<Button-1>", self.arrastrar)
        self.c.bind("<ButtonRelease-1>", lambda e: self.soltarJoy())
        self.lJoy = tk.Label(izq, text="y 0 · x 0", fg="white", bg="#1e2228", font=("Consolas", 11))
        self.lJoy.pack(pady=4)

        tope = tk.Frame(izq, bg="#1e2228"); tope.pack(pady=4)
        tk.Label(tope, text="magnitud máx", fg="#9aa4b1", bg="#1e2228").pack(side="left")
        self.maximo = tk.Scale(tope, from_=20, to=255, orient="horizontal", length=150, bg="#1e2228",
                               fg="white", highlightthickness=0)
        self.maximo.set(100)
        self.maximo.pack(side="left")

        bot = tk.Frame(izq, bg="#1e2228"); bot.pack(pady=6)
        for i, (t, k) in enumerate((("N", "n"), ("S", "s"), ("E", "e"), ("W", "w"), ("pito", "r"))):
            b = tk.Button(bot, text=t, width=5, font=("Segoe UI", 10, "bold"))
            b.grid(row=0, column=i, padx=2)
            b.bind("<ButtonPress-1>", lambda e, k=k: mandar(k))
            b.bind("<ButtonRelease-1>", lambda e: self.cero("botón suelto"))

        tk.Button(izq, text="TODO A CERO  (espacio)", font=("Segoe UI", 13, "bold"), bg="#c62828", fg="white",
                  command=lambda: self.cero("botón rojo")).pack(fill="x", pady=(8, 0))

        self.lEstado = tk.Label(der, text="sin armar · solo escucha", fg="#f0b429", bg="#1e2228",
                                font=("Segoe UI", 14, "bold"), anchor="w")
        self.lEstado.pack(fill="x")
        self.lBus = tk.Label(der, text="bus: —", fg="white", bg="#1e2228", font=("Consolas", 11), anchor="w")
        self.lBus.pack(fill="x")
        self.lNodos = tk.Label(der, text="nodos: —", fg="white", bg="#1e2228", font=("Consolas", 11),
                               anchor="w", justify="left")
        self.lNodos.pack(fill="x", pady=(0, 6))
        marca = tk.Frame(der, bg="#1e2228"); marca.pack(fill="x")
        self.eMarca = tk.Entry(marca, font=("Segoe UI", 11))
        self.eMarca.pack(side="left", fill="x", expand=True)
        self.eMarca.bind("<Return>", self.marcar)
        tk.Button(marca, text="marca al log", command=self.marcar).pack(side="left", padx=4)
        self.txt = tk.Text(der, width=70, height=24, bg="#11151a", fg="#d6dde6", font=("Consolas", 9))
        self.txt.pack(fill="both", expand=True, pady=(6, 0))

        raiz.bind("<space>", lambda e: self.cero("espacio") if raiz.focus_get() is not self.eMarca else None)
        raiz.bind("<FocusOut>", lambda e: self.cero("ventana sin foco") if e.widget is raiz else None)
        raiz.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.tic()

    def escribir(self, s):
        self.txt.insert("end", "%s  %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), s))
        self.txt.see("end")

    def armar(self):
        if self.armado:
            return
        if not messagebox.askyesno("Armar", "¿La llave está en OFF?\n\nAl armar, el ESP deja de solo escuchar "
                                            "y empieza a transmitir como nodo 2 cuando el equipo arranque."):
            return
        mandar("A")
        self.armado = True
        self.bArmar.configure(text="ARMADO · subí la llave", bg="#555")
        self.escribir("armado: subí la llave")

    def arrastrar(self, e):
        cx = cy = R + 10
        dx, dy = e.x - cx, e.y - cy
        d = (dx * dx + dy * dy) ** 0.5
        if d > R:
            dx, dy = dx * R / d, dy * R / d
        self.c.coords(self.punto, cx + dx - 14, cy + dy - 14, cx + dx + 14, cy + dy + 14)
        m = self.maximo.get()
        self.y, self.x = int(round(-dy / R * m)), int(round(dx / R * m))
        self.lJoy.configure(text="y %d · x %d" % (self.y, self.x))

    def soltarJoy(self):
        cx = cy = R + 10
        self.c.coords(self.punto, cx - 14, cy - 14, cx + 14, cy + 14)
        self.y = self.x = 0
        self.lJoy.configure(text="y 0 · x 0")

    def cero(self, porque):
        self.soltarJoy()
        mandar("0")
        self.enviado = (0, 0)
        log.write(">>> CERO (%s)\n" % porque)

    def marcar(self, e=None):
        t = self.eMarca.get().strip()
        if t:
            log.write(">>> MARCA %s · %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], t))
            self.escribir("marca: " + t)
            self.eMarca.delete(0, "end")

    def tic(self):
        if self.armado:
            if (self.y, self.x) != self.enviado:
                py, px = self.enviado
                if self.y != py:
                    mandar(("a %d" if self.y >= 0 else "t %d") % abs(self.y))
                if self.x != px:
                    mandar(("d %d" if self.x >= 0 else "i %d") % abs(self.x))
                self.enviado = (self.y, self.x)
            else:
                mandar(".")
        while not entrada.empty():
            self.procesar(entrada.get())
        ahora = time.time()
        if ahora - self.tTramas >= 1:
            self.lBus.configure(text="bus: %d tramas/s%s" % (self.tramas / (ahora - self.tTramas),
                                "   ← NO SE OYE NADA: revisar CANH/CANL/GND_bus en el DB9" if self.tramas == 0 else ""))
            self.tramas, self.tTramas = 0, ahora
            vivos = ["%d %s" % (n, NOMBRE.get(n, "?")) for n, t in sorted(self.nodos.items()) if ahora - t < 2]
            self.lNodos.configure(text="nodos con latido: " + (", ".join(vivos) if vivos else "ninguno"))
        if vivo:
            self.raiz.after(PERIODO_MS, self.tic)

    def procesar(self, l):
        m = TRAMA.match(l)
        if m:
            self.tramas += 1
            ident = int(m.group(2), 16)
            if 0x701 <= ident <= 0x77F:
                self.nodos[ident - 0x700] = time.time()
            return
        if l.startswith("# YO estado"):
            n = l.split()[3]
            txt = ESTADOS.get(n, n)
            self.lEstado.configure(text="nodo 2: " + txt, fg="#4caf50" if n == "2" else "#f0b429")
            if "TEC 0" not in l or "bus ok" not in l:
                self.escribir(l[2:])
            return
        if l.startswith("#"):
            self.escribir(l[2:])

    def cerrar(self):
        global vivo
        self.cero("cerrar")
        time.sleep(0.1)
        mandar("X")
        time.sleep(0.2)
        vivo = False
        try:
            ser.close()
        except Exception:
            pass
        log.close()
        self.raiz.destroy()


raiz = tk.Tk()
Ventana(raiz)
raiz.mainloop()
