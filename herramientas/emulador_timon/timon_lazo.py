#!/usr/bin/env python3
"""timon_lazo.py — ventana para timon_lazo.ino: el timón A MANO y la rueda A UN ÁNGULO (lazo cerrado).

    py timon_lazo.py            (COM6)        py timon_lazo.py COM7

  IZQUIERDA · el timón en pantalla: arrastralo con el mouse o mantené A / D. El ESP gira el volante
              emulado igual que vos (como rueda_timon.py). Al tocarlo se cancela el objetivo.
  DERECHA   · la rueda: aguja ROJA = ángulo real medido (0x184); VERDE = objetivo.
              Botones de ángulo o escribir uno + Enter: la rueda va sola ahí (lazo cerrado).
  ESPACIO o PARAR = volante quieto y sin objetivo. «Invertir sentido» si la rueda va para el otro lado.
  Manda '.' cada 50 ms: si esta ventana se cae, el ESP para el volante en 300 ms.
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
PASO_TECLA = 2.0                   # grados de volante por tick (50 ms) con A/D: 40 °/s
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
    if t != "." and not t.startswith("P"):
        log.write(">>> %s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], t))


class Ventana:
    def __init__(self, r):
        self.r = r
        self.ang = None            # rueda medida
        self.obj = None            # objetivo
        self.vol = 0.0             # volante, multivuelta (lo que se ve en pantalla)
        self.volEsp = None         # último vol= del ESP (0..360) para seguirlo cuando no se toca
        self.tocando = False
        self.enviado = None
        self.teclas = set()
        self.drag = None
        r.title("Timón · %s" % PUERTO)
        r.configure(bg="#1e2228")

        arriba = tk.Frame(r, bg="#1e2228"); arriba.pack(padx=10, pady=10)
        self.cv = tk.Canvas(arriba, width=300, height=300, bg="#0b1e3a", highlightthickness=0)
        self.cv.pack(side="left")
        self.c = tk.Canvas(arriba, width=420, height=260, bg="#2a2f37", highlightthickness=0)
        self.c.pack(side="left", padx=(10, 0))
        self.cv.bind("<Button-1>", self.tomar)
        self.cv.bind("<B1-Motion>", self.arrastrar)
        self.cv.bind("<ButtonRelease-1>", self.soltar)

        self.lEst = tk.Label(r, text="esperando al ESP…", fg="#f0b429", bg="#1e2228", font=("Segoe UI", 14, "bold"))
        self.lEst.pack()
        self.lNum = tk.Label(r, text="", fg="white", bg="#1e2228", font=("Consolas", 12))
        self.lNum.pack(pady=(0, 6))

        f = tk.Frame(r, bg="#1e2228"); f.pack()
        tk.Label(f, text="rueda a:", fg="#9aa4b1", bg="#1e2228").pack(side="left", padx=4)
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
        tk.Label(r, text="timón: arrastrar con el mouse o mantener A / D", fg="#9aa4b1", bg="#1e2228").pack()
        self.t = tk.Text(r, width=90, height=7, bg="#11151a", fg="#d6dde6", font=("Consolas", 9))
        self.t.pack(padx=10, pady=10)
        r.bind("<space>", lambda ev: self.parar() if r.focus_get() is not self.e else None)
        r.bind("<KeyPress>", self.teclaAbajo)
        r.bind("<KeyRelease>", lambda ev: self.teclas.discard(ev.keysym.lower()))
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.tic()

    # ---- rueda a un ángulo (lazo cerrado) ----
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

    # ---- timón a mano ----
    def teclaAbajo(self, ev):
        if self.r.focus_get() is self.e:
            return
        k = ev.keysym.lower()
        if k in ("a", "d"):
            self.teclas.add(k)

    def angMouse(self, ev):
        return math.degrees(math.atan2(ev.x - 150, -(ev.y - 150)))

    def tomar(self, ev):
        self.drag = self.angMouse(ev)
        self.tocando = True
        self.obj = None

    def arrastrar(self, ev):
        if self.drag is None:
            return
        a = self.angMouse(ev)
        d = a - self.drag
        d = d - 360 if d > 180 else d + 360 if d < -180 else d
        d = max(-30, min(30, d))              # pasos chicos: el nodo 4 deriva velocidad del cambio
        self.vol += d
        self.drag = a

    def soltar(self, ev):
        self.drag = None
        self.tocando = False
        if self.enviado is not None:       # lo que no llegó a mandarse se descarta: pantalla = ESP
            self.vol = self.enviado

    # ---- dibujo ----
    def dibujarTimon(self):
        cv = self.cv
        cv.delete("all")
        cx = cy = 150
        R, HUB = 125, 30
        th = math.radians(self.vol)
        cv.create_polygon(cx - 9, cy - R - 16, cx + 9, cy - R - 16, cx, cy - R + 2, fill="#ffd24d", outline="")
        cv.create_oval(cx - R, cy - R, cx + R, cy + R, outline="#5a8fd6", width=10)
        cv.create_oval(cx - HUB, cy - HUB, cx + HUB, cy + HUB, outline="#5a8fd6", width=5, fill="#13294d")
        for s in (0, 120, 240):
            a = th + math.radians(s)
            cv.create_line(cx + HUB * math.sin(a), cy - HUB * math.cos(a), cx + R * math.sin(a), cy - R * math.cos(a),
                           fill="#5a8fd6", width=8)
        cv.create_oval(cx + R * math.sin(th) - 9, cy - R * math.cos(th) - 9, cx + R * math.sin(th) + 9,
                       cy - R * math.cos(th) + 9, fill="#ff5b5b", outline="")
        cv.create_text(cx, cy, text="%.0f°" % self.vol, fill="#cfe3ff", font=("Consolas", 10))

    def dibujarRueda(self):
        c = self.c
        c.delete("all")
        cx, cy, R = 210, 235, 180
        c.create_text(cx, 14, text="RUEDA (vista de arriba, uñas hacia arriba)", fill="#9aa4b1")
        c.create_arc(cx - R, cy - R, cx + R, cy + R, start=0, extent=180, style="arc", outline="#5b6573", width=3)
        for a in (-90, -45, 0, 45, 90):
            t = math.radians(90 - a)
            c.create_line(cx + (R - 12) * math.cos(t), cy - (R - 12) * math.sin(t),
                          cx + R * math.cos(t), cy - R * math.sin(t), fill="#9aa4b1", width=2)
            c.create_text(cx + (R + 14) * math.cos(t), cy - (R + 14) * math.sin(t), text="%+d" % a if a else "0",
                          fill="#9aa4b1")
        for v, color, ancho in ((self.obj, "#4caf50", 4), (self.ang, "#ef5350", 7)):
            if v is None:
                continue
            t = math.radians(90 - max(-105, min(105, v)))
            c.create_line(cx, cy, cx + (R - 20) * math.cos(t), cy - (R - 20) * math.sin(t), fill=color, width=ancho)
        c.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill="#ddd", outline="")

    def escribir(self, s):
        self.t.insert("end", "%s  %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), s))
        self.t.see("end")

    def tic(self):
        if "a" in self.teclas:
            self.vol -= PASO_TECLA; self.tocando = True; self.obj = None
        if "d" in self.teclas:
            self.vol += PASO_TECLA; self.tocando = True; self.obj = None
        mano = bool(self.tocando or self.teclas)
        if self.enviado is None:
            self.enviado = self.vol
        if mano and abs(self.vol - self.enviado) >= 0.1:
            # como mucho 60° de volante por tick (1200 °/s): un salto grande el nodo 4 lo leería mal
            paso = max(-60.0, min(60.0, self.vol - self.enviado))
            self.enviado += paso
            mandar("P%.1f" % self.enviado)
        else:
            mandar(".")
            if not mano:
                self.enviado = self.vol
        if not self.teclas and self.drag is None:
            self.tocando = False
        while not entrada.empty():
            l = entrada.get()
            if not l.startswith("T "):
                self.escribir(l)
                continue
            kv = dict(p.split("=", 1) for p in l[2:].split() if "=" in p)
            try:
                self.ang = float(kv["ang"]) if kv.get("hz184", "0") != "0" else None
                ve = float(kv["vol"])
            except (KeyError, ValueError):
                continue
            if self.volEsp is not None and not mano:        # seguir al volante cuando lo mueve el lazo
                d = ve - self.volEsp
                d = d - 360 if d > 180 else d + 360 if d < -180 else d
                self.vol += d
            self.volEsp = ve
            est = kv.get("est", "?")
            color = {"LLEGO": "#4caf50", "YENDO": "#f0b429", "QUIETO": "#9aa4b1", "MANO": "#5a8fd6"}.get(est, "#ef5350")
            self.lEst.configure(text={"LLEGO": "LLEGÓ", "YENDO": "yendo…", "QUIETO": "quieto", "MANO": "a mano",
                                      "SIN_184": "SIN 0x184 (¿llave? ¿CAN?)", "SIGNO_MAL": "SENTIDO AL REVÉS: invertir sentido",
                                      "SIN_RESP": "LA RUEDA NO RESPONDE"}.get(est, est), fg=color)
            if est not in ("YENDO", "LLEGO"):
                self.obj = None
            self.lNum.configure(text="rueda %s°   objetivo %s°   error %s°   volante %s°/s   0x184 %s Hz" % (
                kv.get("ang"), kv.get("obj"), kv.get("err"), kv.get("gps"), kv.get("hz184")))
        self.dibujarTimon()
        self.dibujarRueda()
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
