#!/usr/bin/env python3
"""teleop_wasd.py — manejar el equipo con W A S D (teleop_wasd.ino). maje PARADO EN EL PEDAL REAL.

    py teleop_wasd.py            (COM6)        py teleop_wasd.py COM7

  W / S   marcha mientras se mantiene apretada, a la velocidad del slider. Al soltar: 0.
  A / D   gira la rueda (lazo cerrado con el 0x184). Al soltar, la rueda SE QUEDA donde está.
  ESPACIO PARAR: marcha a 0 y timón sin objetivo. NO reemplaza al pedal: levantar el pie es el paro.
  Si la ventana pierde el foco: marcha a 0.
  Arranque: llave en OFF → «ARMAR» → subir la llave → esperar «OPERACIONAL».
  Manda la línea de estado cada 50 ms: si la ventana se cae, el ESP pone todo a cero en 200 ms.
Log en herramientas/rig/logs/teleop_wasd_<fecha>.log.
"""
import datetime as dt
import math
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import serial

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM6"
ANG_MIN, ANG_MAX = -100.0, 78.0
GIRO_GPS = 20.0                     # grados de RUEDA por segundo mientras se mantiene A o D
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
log = open(os.path.join(aqui, "logs", "teleop_wasd_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S")),
           "w", encoding="utf-8")

ser = serial.Serial()
ser.port, ser.baudrate, ser.timeout = PUERTO, 115200, 0.2
ser.dtr = ser.rts = False
ser.open()
entrada = queue.Queue()
vivo = True


def lector():
    while vivo:
        try:
            l = ser.readline().decode("utf-8", "replace").strip()
        except Exception as e:
            entrada.put("EV GUI: se cortó el USB (%s)" % e)
            return
        if l:
            log.write("%s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], l))
            entrada.put(l)


threading.Thread(target=lector, daemon=True).start()


def mandar(t):
    try:
        ser.write((t + "\n").encode())
    except Exception:
        pass
    if not t.startswith("L "):
        log.write(">>> %s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], t))


class Ventana:
    def __init__(self, r):
        self.r = r
        self.teclas = set()
        self.soltando = {}
        self.ang = None
        self.obj = None
        self.can = "?"
        self.ultimoM = None
        r.title("Teleop W A S D · %s" % PUERTO)
        r.configure(bg="#1e2228")

        top = tk.Frame(r, bg="#1e2228"); top.pack(fill="x", padx=10, pady=8)
        self.bArmar = tk.Button(top, text="ARMAR (llave en OFF)", font=("Segoe UI", 12, "bold"), bg="#2e7d32",
                                fg="white", command=self.armar)
        self.bArmar.pack(side="left")
        self.lCan = tk.Label(top, text="CAN: —", fg="#f0b429", bg="#1e2228", font=("Segoe UI", 14, "bold"))
        self.lCan.pack(side="left", padx=16)

        mid = tk.Frame(r, bg="#1e2228"); mid.pack(padx=10)
        self.c = tk.Canvas(mid, width=420, height=250, bg="#2a2f37", highlightthickness=0)
        self.c.pack(side="left")
        teclado = tk.Frame(mid, bg="#1e2228"); teclado.pack(side="left", padx=16)
        self.k = {}
        for t, fila, col in (("W", 0, 1), ("A", 1, 0), ("S", 1, 1), ("D", 1, 2)):
            l = tk.Label(teclado, text=t, width=4, height=2, font=("Segoe UI", 18, "bold"), bg="#3c444f", fg="white")
            l.grid(row=fila, column=col, padx=3, pady=3)
            self.k[t.lower()] = l

        f = tk.Frame(r, bg="#1e2228"); f.pack(fill="x", padx=10, pady=6)
        tk.Label(f, text="velocidad (joystick 0–255)", fg="#9aa4b1", bg="#1e2228").pack(side="left")
        self.vel = tk.Scale(f, from_=10, to=255, orient="horizontal", length=260, bg="#1e2228", fg="white",
                            highlightthickness=0, takefocus=0)
        self.vel.set(60)
        self.vel.pack(side="left", padx=6)
        self.wUnas = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="W = hacia las uñas", variable=self.wUnas, bg="#1e2228", fg="white",
                       selectcolor="#1e2228", activebackground="#1e2228", takefocus=0).pack(side="left", padx=10)
        tk.Button(f, text="rueda recta (0°)", command=lambda: self.ponerObj(0.0), takefocus=0).pack(side="left")
        tk.Button(f, text="invertir timón", command=lambda: mandar("S"), takefocus=0).pack(side="left", padx=6)

        tk.Button(r, text="PARAR  (espacio) — el paro de verdad es levantar el pie", font=("Segoe UI", 12, "bold"),
                  bg="#c62828", fg="white", command=self.parar, takefocus=0).pack(fill="x", padx=10)
        self.lNum = tk.Label(r, text="", fg="white", bg="#1e2228", font=("Consolas", 11))
        self.lNum.pack(pady=4)
        self.t = tk.Text(r, width=96, height=8, bg="#11151a", fg="#d6dde6", font=("Consolas", 9))
        self.t.pack(padx=10, pady=(0, 10))

        r.bind("<KeyPress>", self.abajo)
        r.bind("<KeyRelease>", self.arriba)
        r.bind("<space>", lambda e: self.parar())
        r.bind("<FocusOut>", lambda e: self.sinFoco() if e.widget is r else None)
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        r.focus_force()
        self.tic()

    # ---- teclado (con antirrebote del autorepetir) ----
    def abajo(self, e):
        k = e.keysym.lower()
        if k in ("w", "a", "s", "d"):
            self.teclas.add(k)
            self.soltando.pop(k, None)

    def arriba(self, e):
        k = e.keysym.lower()
        if k in ("w", "a", "s", "d"):
            self.soltando[k] = self.r.after(40, lambda: self.soltar(k))

    def soltar(self, k):
        if k in self.soltando:
            self.soltando.pop(k, None)
            self.teclas.discard(k)

    def sinFoco(self):
        self.teclas.clear()

    # ---- acciones ----
    def armar(self):
        if messagebox.askyesno("Armar", "¿La llave está en OFF?\n\nDespués de armar, subí la llave y esperá "
                                        "«OPERACIONAL». Parado en el pedal real."):
            mandar("A")
            self.bArmar.configure(text="ARMADO", bg="#555", state="disabled")

    def ponerObj(self, a):
        if self.ang is None:
            self.escribir("sin 0x184: no se puede girar la rueda")
            return
        self.obj = max(ANG_MIN, min(ANG_MAX, a))

    def parar(self):
        self.teclas.clear()
        self.obj = None

    def escribir(self, s):
        self.t.insert("end", "%s  %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), s))
        self.t.see("end")

    def dibujar(self):
        c = self.c
        c.delete("all")
        cx, cy, R = 210, 225, 175
        c.create_text(cx, 14, text="RUEDA  ·  roja = medida (0x184)  ·  verde = objetivo", fill="#9aa4b1")
        c.create_arc(cx - R, cy - R, cx + R, cy + R, start=0, extent=180, style="arc", outline="#5b6573", width=3)
        for a in (-90, -45, 0, 45, 90):
            t = math.radians(90 - a)
            c.create_line(cx + (R - 12) * math.cos(t), cy - (R - 12) * math.sin(t), cx + R * math.cos(t),
                          cy - R * math.sin(t), fill="#9aa4b1", width=2)
            c.create_text(cx + (R + 14) * math.cos(t), cy - (R + 14) * math.sin(t), text="%+d" % a if a else "0",
                          fill="#9aa4b1")
        for v, color, w in ((self.obj, "#4caf50", 4), (self.ang, "#ef5350", 7)):
            if v is not None:
                t = math.radians(90 - max(-105, min(105, v)))
                c.create_line(cx, cy, cx + (R - 20) * math.cos(t), cy - (R - 20) * math.sin(t), fill=color, width=w)
        c.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill="#ddd", outline="")

    def tic(self):
        # marcha
        v = int(self.vel.get())
        signo = 1 if self.wUnas.get() else -1
        m = 0
        if "w" in self.teclas and "s" not in self.teclas:
            m = v * signo
        elif "s" in self.teclas and "w" not in self.teclas:
            m = -v * signo
        # timón: A/D mueven el objetivo; al soltar se queda
        if ("a" in self.teclas) != ("d" in self.teclas) and self.ang is not None:
            if self.obj is None:
                self.obj = self.ang
            paso = GIRO_GPS * 0.05 * (-1 if "a" in self.teclas else 1)
            self.obj = max(ANG_MIN, min(ANG_MAX, self.obj + paso))
        mandar("L m=%d r=%s" % (m, "-" if self.obj is None else "%.1f" % self.obj))
        if m != self.ultimoM:
            log.write(">>> %s marcha m=%d\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], m))
            self.ultimoM = m
        for k, l in self.k.items():
            l.configure(bg="#f0b429" if k in self.teclas else "#3c444f")

        while not entrada.empty():
            l = entrada.get()
            if not l.startswith("T "):
                self.escribir(l)
                continue
            kv = dict(p.split("=", 1) for p in l[2:].split() if "=" in p)
            try:
                self.ang = float(kv["ang"]) if kv.get("hz184", "0") != "0" else None
            except (KeyError, ValueError):
                pass
            self.can = kv.get("can", "?")
            tim = kv.get("tim", "?")
            if tim in ("SIGNO_MAL", "SIN_RESP", "SIN_184"):
                self.obj = None                 # no reintentar solo: hace falta volver a apretar A/D
            ok = self.can == "OPERACIONAL"
            self.lCan.configure(text="CAN: %s%s" % (self.can, "" if kv.get("arm") == "1" else " (sin armar)"),
                                fg="#4caf50" if ok else "#f0b429")
            self.lNum.configure(text="marcha m=%s   rueda %s°   objetivo %s°   timón %s   0x184 %s Hz   TEC %s REC %s  bus %s" % (
                kv.get("m"), kv.get("ang"), kv.get("obj"), tim, kv.get("hz184"), kv.get("tec"), kv.get("rec"), kv.get("bus")))
        self.dibujar()
        if vivo:
            self.r.after(50, self.tic)

    def cerrar(self):
        global vivo
        mandar("L m=0 r=-")
        mandar("X")
        vivo = False
        try:
            ser.close()
        except Exception:
            pass
        log.close()
        self.r.destroy()


raiz = tk.Tk()
Ventana(raiz)
raiz.mainloop()
