#!/usr/bin/env python3
"""timon_lazo.py — ventana para timon_lazo.ino: pedirle a la RUEDA un ángulo y ver si llega.

    py timon_lazo.py            (COM6)        py timon_lazo.py COM7

  · Botones de ángulo o escribir uno + Enter: la rueda va ahí (lazo cerrado con el 0x184).
  · ESPACIO o PARAR: volante quieto y sin objetivo.
  · «Invertir sentido»: si la rueda va para el otro lado (el ESP lo detecta y para solo).
  · La aguja ROJA es la rueda medida (0x184); la VERDE, el objetivo.
  · Manda '.' cada 50 ms: si esta ventana se cae, el ESP para el volante en 300 ms.
Log en herramientas/emulador_timon/logs/timon_lazo_<fecha>.log.
"""
import datetime as dt
import math
import os
import queue
import sys
import threading
import tkinter as tk

import serial

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM6"
ANG_MIN, ANG_MAX = -100.0, 78.0
aqui = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
log = open(os.path.join(aqui, "logs", "timon_lazo_%s.log" % dt.datetime.now().strftime("%Y%m%d-%H%M%S")),
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
    if t != ".":
        log.write(">>> %s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], t))


class Ventana:
    def __init__(self, r):
        self.r = r
        self.ang = None
        self.obj = None
        r.title("Timón, lazo cerrado · %s" % PUERTO)
        r.configure(bg="#1e2228")
        self.c = tk.Canvas(r, width=460, height=270, bg="#2a2f37", highlightthickness=0)
        self.c.pack(padx=10, pady=10)
        self.lEst = tk.Label(r, text="esperando al ESP…", fg="#f0b429", bg="#1e2228", font=("Segoe UI", 14, "bold"))
        self.lEst.pack()
        self.lNum = tk.Label(r, text="", fg="white", bg="#1e2228", font=("Consolas", 12))
        self.lNum.pack(pady=(0, 6))

        f = tk.Frame(r, bg="#1e2228"); f.pack()
        for a in (-90, -45, -20, 0, 20, 45, 78):
            tk.Button(f, text="%+d°" % a if a else "0° recta", width=7, font=("Segoe UI", 10, "bold"),
                      command=lambda a=a: self.ir(a)).pack(side="left", padx=2)
        g = tk.Frame(r, bg="#1e2228"); g.pack(pady=6)
        tk.Label(g, text="ángulo exacto:", fg="#9aa4b1", bg="#1e2228").pack(side="left")
        self.e = tk.Entry(g, width=8, font=("Segoe UI", 11)); self.e.pack(side="left", padx=4)
        self.e.bind("<Return>", lambda ev: self.irTexto())
        tk.Button(g, text="ir", command=self.irTexto).pack(side="left")
        tk.Button(g, text="invertir sentido", command=lambda: mandar("S")).pack(side="left", padx=12)

        tk.Button(r, text="PARAR  (espacio)", font=("Segoe UI", 13, "bold"), bg="#c62828", fg="white",
                  command=self.parar).pack(fill="x", padx=10)
        self.t = tk.Text(r, width=64, height=9, bg="#11151a", fg="#d6dde6", font=("Consolas", 9))
        self.t.pack(padx=10, pady=10)
        r.bind("<space>", lambda ev: self.parar() if r.focus_get() is not self.e else None)
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.tic()

    def ir(self, a):
        a = max(ANG_MIN, min(ANG_MAX, float(a)))
        self.obj = a
        mandar("A%.1f" % a)

    def irTexto(self):
        try:
            self.ir(float(self.e.get().replace(",", ".")))
        except ValueError:
            pass

    def parar(self):
        self.obj = None
        mandar("X")

    def escribir(self, s):
        self.t.insert("end", "%s  %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), s))
        self.t.see("end")

    def dibujar(self):
        c = self.c
        c.delete("all")
        cx, cy, R = 230, 240, 200
        c.create_arc(cx - R, cy - R, cx + R, cy + R, start=0, extent=180, style="arc", outline="#5b6573", width=3)
        for a, txt in ((-90, "-90"), (-45, "-45"), (0, "0"), (45, "+45"), (90, "+90")):
            th = math.radians(90 - a)
            c.create_line(cx + (R - 12) * math.cos(th), cy - (R - 12) * math.sin(th),
                          cx + R * math.cos(th), cy - R * math.sin(th), fill="#9aa4b1", width=2)
            c.create_text(cx + (R + 16) * math.cos(th), cy - (R + 16) * math.sin(th), text=txt, fill="#9aa4b1")
        c.create_text(cx - R + 10, cy + 18, text="izquierda", fill="#9aa4b1", anchor="w")
        c.create_text(cx + R - 10, cy + 18, text="derecha", fill="#9aa4b1", anchor="e")
        for v, color, ancho in ((self.obj, "#4caf50", 4), (self.ang, "#ef5350", 7)):
            if v is None:
                continue
            th = math.radians(90 - max(-105, min(105, v)))
            c.create_line(cx, cy, cx + (R - 20) * math.cos(th), cy - (R - 20) * math.sin(th), fill=color, width=ancho)
        c.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#ddd", outline="")

    def tic(self):
        mandar(".")
        while not entrada.empty():
            l = entrada.get()
            if l.startswith("T "):
                kv = dict(p.split("=", 1) for p in l[2:].split() if "=" in p)
                try:
                    self.ang = float(kv.get("ang", "nan"))
                except ValueError:
                    pass
                est = kv.get("est", "?")
                color = {"LLEGO": "#4caf50", "YENDO": "#f0b429", "QUIETO": "#9aa4b1"}.get(est, "#ef5350")
                self.lEst.configure(text={"LLEGO": "LLEGÓ", "YENDO": "yendo…", "QUIETO": "quieto",
                                          "SIN_184": "SIN 0x184 (¿llave? ¿CAN?)", "SIGNO_MAL": "SENTIDO AL REVÉS",
                                          "SIN_RESP": "LA RUEDA NO RESPONDE"}.get(est, est), fg=color)
                if est not in ("YENDO", "LLEGO"):
                    self.obj = None
                self.lNum.configure(text="rueda %s°   objetivo %s°   error %s°   volante %s°/s   0x184 %s Hz" % (
                    kv.get("ang"), kv.get("obj"), kv.get("err"), kv.get("gps"), kv.get("hz184")))
            else:
                self.escribir(l)
        self.dibujar()
        if vivo:
            self.r.after(50, self.tic)

    def cerrar(self):
        global vivo
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
