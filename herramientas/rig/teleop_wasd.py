#!/usr/bin/env python3
"""teleop_wasd.py — manejar el equipo con el teclado (teleop_wasd.ino). maje PARADO EN EL PEDAL REAL.

    py teleop_wasd.py            (COM6)        py teleop_wasd.py COM7

  W / S   marcha (soltar = 0)                     A / D   rueda (soltar = se queda)
  Q / E   uñas ARRIBA / ABAJO                     U / O   pantógrafo ADELANTE / ATRÁS
  J / L   desplazador IZQUIERDA / DERECHA         I / K   puntas de las uñas ARRIBA / ABAJO
  H       pito
  Todo menos A/D vuelve a 0 al soltar. ESPACIO = PARAR (todo a 0, timón quieto). Sin foco = todo a 0.
  M       MARCA (24-nov): deja «>>> MARCA n» en el log y pone en cero la pose de la odometría en vivo (el giro, el
          avance y cuánto se movió el medio del eje de carga desde la marca: percepcion/odometria.py, motriz corrida)
  Botones de rueda: la recta del modelo (+1.2), tope corto, tope largo y la receta del giro (analisis/giro_opciones.py).
  Para la prueba de giros con tiza: campo/giros_odometria/LEEME.md.
  NO reemplaza al pedal: levantar el pie es el paro.
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "percepcion"))
from odometria import CENTRO_184, GRADOS_184, LADO_MOTRIZ, avanzar_rueda   # noqa: E402

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "COM6"
ANG_MIN, ANG_MAX = -100.0, 78.0
GIRO_GPS = 20.0                     # grados de RUEDA por segundo mientras se mantiene A o D

# tecla: (texto en pantalla, fila, columna)
TECLAS = {
    "q": ("Q\nuñas ↑", 0, 0), "w": ("W\nmarcha ↑", 0, 1), "e": ("E\nuñas ↓", 0, 2),
    "a": ("A\nrueda ←", 1, 0), "s": ("S\nmarcha ↓", 1, 1), "d": ("D\nrueda →", 1, 2),
    "u": ("U\npantóg. adel.", 0, 4), "i": ("I\npuntas ↑", 0, 5), "o": ("O\npantóg. atrás", 0, 6),
    "j": ("J\ndesplaz. ←", 1, 4), "k": ("K\npuntas ↓", 1, 5), "l": ("L\ndesplaz. →", 1, 6),
    "h": ("H\npito", 1, 3),
}
BOTON_B5 = {"j": 8, "l": 4, "k": 2, "i": 1}   # N, S, E, W (herramientas/can/multipiloto.md)

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
        self.ultimo = None
        r.title("Teleop por teclado · %s" % PUERTO)
        r.configure(bg="#1e2228")

        top = tk.Frame(r, bg="#1e2228"); top.pack(fill="x", padx=10, pady=8)
        self.bArmar = tk.Button(top, text="ARMAR (llave en OFF)", font=("Segoe UI", 12, "bold"), bg="#2e7d32",
                                fg="white", command=self.armar, takefocus=0)
        self.bArmar.pack(side="left")
        self.lCan = tk.Label(top, text="CAN: —", fg="#f0b429", bg="#1e2228", font=("Segoe UI", 14, "bold"))
        self.lCan.pack(side="left", padx=16)

        mid = tk.Frame(r, bg="#1e2228"); mid.pack(padx=10)
        self.c = tk.Canvas(mid, width=380, height=230, bg="#2a2f37", highlightthickness=0)
        self.c.pack(side="left")
        teclado = tk.Frame(mid, bg="#1e2228"); teclado.pack(side="left", padx=12)
        self.k = {}
        for k, (txt, fila, col) in TECLAS.items():
            l = tk.Label(teclado, text=txt, width=10, height=3, font=("Segoe UI", 9, "bold"), bg="#3c444f", fg="white")
            l.grid(row=fila, column=col, padx=2, pady=2)
            self.k[k] = l
        tk.Label(teclado, text="", width=2, bg="#1e2228").grid(row=0, column=3)

        f = tk.Frame(r, bg="#1e2228"); f.pack(fill="x", padx=10, pady=4)
        self.vel = self.slider(f, "marcha (W/S)", 60)
        self.elev = self.slider(f, "uñas (Q/E)", 80)
        self.pant = self.slider(f, "pantógrafo (U/O)", 80)
        g = tk.Frame(r, bg="#1e2228"); g.pack(fill="x", padx=10)
        self.wUnas = tk.BooleanVar(value=True)
        tk.Checkbutton(g, text="W = hacia las uñas", variable=self.wUnas, bg="#1e2228", fg="white",
                       selectcolor="#1e2228", activebackground="#1e2228", takefocus=0).pack(side="left")
        tk.Button(g, text="rueda recta (0°)", command=lambda: self.ponerObj(0.0), takefocus=0).pack(side="left", padx=8)
        tk.Button(g, text="invertir timón", command=lambda: mandar("S"), takefocus=0).pack(side="left")
        tk.Button(g, text="odometría a 0", command=lambda: mandar("Z"), takefocus=0).pack(side="left", padx=8)
        self.lOdo = tk.Label(g, text="distancia —", fg="#4fc3f7", bg="#1e2228", font=("Consolas", 16, "bold"))
        self.lOdo.pack(side="left", padx=8)
        # 24-nov: la rueda a los ángulos de las pruebas de giro (en unidades del 0x184 / 100: el centro es +1.2)
        h = tk.Frame(r, bg="#1e2228"); h.pack(fill="x", padx=10, pady=2)
        tk.Label(h, text="rueda a:", fg="#9aa4b1", bg="#1e2228").pack(side="left")
        for txt, a in (("+1.2 recta del modelo", 1.2), ("+78 tope corto", 78.0), ("−100 tope largo", -100.0), ("receta −95.4 (δ −96.6)", -95.4),
                       ("receta +76.1 (δ +74.9)", 76.1), ("+30 arco", 30.0)):
            tk.Button(h, text=txt, command=lambda a=a: self.ponerObj(a), takefocus=0).pack(side="left", padx=3)
        tk.Button(h, text="MARCA (M)", bg="#6a1b9a", fg="white", command=self.marca, takefocus=0).pack(side="left", padx=12)
        self.lPose = tk.Label(r, text="desde la marca —", fg="#ce93d8", bg="#1e2228", font=("Consolas", 14, "bold"))
        self.lPose.pack(pady=2)
        self.pose, self.dist_ant, self.ang_ant, self.n_marca = (0.0, 0.0, 0.0), None, None, 0

        tk.Button(r, text="PARAR  (espacio) — el paro de verdad es levantar el pie", font=("Segoe UI", 12, "bold"),
                  bg="#c62828", fg="white", command=self.parar, takefocus=0).pack(fill="x", padx=10, pady=6)
        self.lMando = tk.Label(r, text="", fg="#f0b429", bg="#1e2228", font=("Consolas", 12, "bold"))
        self.lMando.pack()
        self.lNum = tk.Label(r, text="", fg="white", bg="#1e2228", font=("Consolas", 10))
        self.lNum.pack(pady=2)
        self.t = tk.Text(r, width=110, height=7, bg="#11151a", fg="#d6dde6", font=("Consolas", 9))
        self.t.pack(padx=10, pady=(0, 10))

        r.bind("<KeyPress>", self.abajo)
        r.bind("<KeyRelease>", self.arriba)
        r.bind("<space>", lambda e: self.parar())
        r.bind("<m>", lambda e: self.marca())
        r.bind("<M>", lambda e: self.marca())
        r.bind("<FocusOut>", lambda e: self.teclas.clear() if e.widget is r else None)
        r.protocol("WM_DELETE_WINDOW", self.cerrar)
        r.focus_force()
        self.tic()

    def slider(self, padre, texto, ini):
        fr = tk.Frame(padre, bg="#1e2228"); fr.pack(side="left", padx=8)
        tk.Label(fr, text=texto, fg="#9aa4b1", bg="#1e2228").pack()
        s = tk.Scale(fr, from_=10, to=255, orient="horizontal", length=200, bg="#1e2228", fg="white",
                     highlightthickness=0, takefocus=0)
        s.set(ini)
        s.pack()
        return s

    # ---- teclado (antirrebote del autorepetir de Windows/Linux) ----
    def abajo(self, e):
        k = e.keysym.lower()
        if k in TECLAS:
            self.teclas.add(k)
            self.soltando.pop(k, None)

    def arriba(self, e):
        k = e.keysym.lower()
        if k in TECLAS:
            self.soltando[k] = True
            self.r.after(40, lambda: self.soltar(k))

    def soltar(self, k):
        if self.soltando.pop(k, None):
            self.teclas.discard(k)

    # ---- acciones ----
    def armar(self):
        if messagebox.askyesno("Armar", "¿La llave está en OFF?\n\nDespués de armar, subí la llave y esperá "
                                        "«OPERACIONAL». Parado en el pedal real."):
            mandar("A")
            self.bArmar.configure(text="ARMADO", bg="#555", state="disabled")
        self.r.focus_force()

    def ponerObj(self, a):
        if self.ang is None:
            self.escribir("sin 0x184: no se puede girar la rueda")
            return
        self.obj = max(ANG_MIN, min(ANG_MAX, a))

    def marca(self):
        self.n_marca += 1
        log.write(">>> %s MARCA %d\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], self.n_marca))
        self.pose = (0.0, 0.0, 0.0)
        self.escribir("MARCA %d: odometría de la marca en cero" % self.n_marca)

    def integrar(self, kv):
        """La pose desde la última marca, con lo que manda el ESP: dist (m de rueda, integrado a 50 Hz en el ESP) y
        ang (0x184 / 100). Misma cinemática que percepcion/odometria.py (entre ejes 1.688, motriz corrida 0.325)."""
        try:
            dist, ang = float(kv["dist"]), float(kv["ang"])
        except (KeyError, ValueError):
            return
        if kv.get("hz184", "0") == "0":
            return
        if self.dist_ant is not None:
            ds = dist - self.dist_ant
            if abs(ds) < 0.5:                                   # «odometría a 0» en el ESP: se salta
                a = 0.5 * (ang + self.ang_ant)
                d = LADO_MOTRIZ * math.radians(a - CENTRO_184 * GRADOS_184)
                self.pose = avanzar_rueda(self.pose, ds, d, 1.0)
        self.dist_ant, self.ang_ant = dist, ang
        x, y, th = self.pose
        self.lPose.configure(text="desde la MARCA %d:  giro %+6.1f°   avance %+.3f m   de lado %+.3f m   "
                                  "medio del eje de carga movido %.1f cm" % (self.n_marca, math.degrees(th), x, y,
                                                                             100 * math.hypot(x, y)))

    def parar(self):
        self.teclas.clear()
        self.obj = None

    def escribir(self, s):
        self.t.insert("end", "%s  %s\n" % (dt.datetime.now().strftime("%H:%M:%S"), s))
        self.t.see("end")

    def dibujar(self):
        c = self.c
        c.delete("all")
        cx, cy, R = 190, 210, 160
        c.create_text(cx, 14, text="RUEDA · roja = medida (0x184) · verde = objetivo", fill="#9aa4b1")
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

    @staticmethod
    def eje(t, mas, menos, v):
        if mas in t and menos not in t:
            return v
        if menos in t and mas not in t:
            return -v
        return 0

    def tic(self):
        t = self.teclas
        sm = 1 if self.wUnas.get() else -1
        m = self.eje(t, "w", "s", int(self.vel.get())) * sm
        y = self.eje(t, "e", "q", int(self.elev.get()))          # + = joystick adelante = uñas ABAJO
        p = self.eje(t, "u", "o", int(self.pant.get()))          # + = palanca adelante
        b = 0
        for k, bit in BOTON_B5.items():
            if k in t:
                b |= bit
        h = 1 if "h" in t else 0
        if ("a" in t) != ("d" in t) and self.ang is not None:
            if self.obj is None:
                self.obj = self.ang
            self.obj = max(ANG_MIN, min(ANG_MAX, self.obj + GIRO_GPS * 0.05 * (-1 if "a" in t else 1)))
        linea = "L m=%d y=%d p=%d b=%d h=%d r=%s" % (m, y, p, b, h, "-" if self.obj is None else "%.1f" % self.obj)
        mandar(linea)
        clave = (m, y, p, b, h)
        if clave != self.ultimo:
            log.write(">>> %s %s\n" % (dt.datetime.now().strftime("%H:%M:%S.%f")[:-3], linea))
            self.ultimo = clave
        for k, l in self.k.items():
            l.configure(bg="#f0b429" if k in t else "#3c444f", fg="black" if k in t else "white")
        partes = []
        if m: partes.append("MARCHA %s %d" % ("hacia las uñas" if m > 0 else "opuesto a las uñas", abs(m)))
        if y: partes.append("UÑAS %s %d" % ("ABAJO" if y > 0 else "ARRIBA", abs(y)))
        if p: partes.append("PANTÓGRAFO %s %d" % ("ADELANTE" if p > 0 else "ATRÁS", abs(p)))
        for k, nom in (("j", "DESPLAZ ←"), ("l", "DESPLAZ →"), ("i", "PUNTAS ↑"), ("k", "PUNTAS ↓"), ("h", "PITO")):
            if k in t: partes.append(nom)
        if ("a" in t) != ("d" in t): partes.append("RUEDA %s" % ("←" if "a" in t else "→"))
        self.lMando.configure(text="  ·  ".join(partes) if partes else "quieto")

        while not entrada.empty():
            l = entrada.get()
            if not l.startswith("T "):
                self.escribir(l)
                continue
            kv = dict(x.split("=", 1) for x in l[2:].split() if "=" in x)
            self.integrar(kv)
            try:
                self.ang = float(kv["ang"]) if kv.get("hz184", "0") != "0" else None
            except (KeyError, ValueError):
                pass
            can, tim = kv.get("can", "?"), kv.get("tim", "?")
            if tim in ("SIGNO_MAL", "SIN_RESP", "SIN_184"):
                self.obj = None
            self.lCan.configure(text="CAN: %s%s" % (can, "" if kv.get("arm") == "1" else " (sin armar)"),
                                fg="#4caf50" if can == "OPERACIONAL" else "#f0b429")
            try:
                self.lOdo.configure(text="distancia %+.3f m · camino %.3f m · %+.2f m/s" % (
                    float(kv["dist"]), float(kv["camino"]), float(kv["vel"])))
            except (KeyError, ValueError):
                pass
            self.lNum.configure(text="0x182 = %s   rueda %s°  objetivo %s°  timón %s   0x184 %s Hz   TEC %s REC %s bus %s" % (
                " ".join(kv.get("x182", "")[i:i + 2] for i in range(0, 16, 2)), kv.get("ang"), kv.get("obj"), tim,
                kv.get("hz184"), kv.get("tec"), kv.get("rec"), kv.get("bus")))
        self.dibujar()
        if vivo:
            self.r.after(50, self.tic)

    def cerrar(self):
        global vivo
        mandar("L m=0 y=0 p=0 b=0 h=0 r=-")
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
