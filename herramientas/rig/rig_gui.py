#!/usr/bin/env python3
"""rig_gui.py — la consola del rig integrado (rig.ino): timón, multipiloto y pie en una ventana.

    python3 rig_gui.py /dev/ttyUSB0          (maquinon)        python rig_gui.py COM6   (Windows)
    python3 rig_gui.py --demo                (sin ESP: para mirar la interfaz)

Manda cada 50 ms la línea de estado completo, que es mando y latido a la vez:
    L y=.. x=.. b=.. n=0 s=0 e=0 w=0 r=0 th=.. pie=0|1
Si esta ventana se cae o se cuelga, el ESP pone el 0x182 en cero, suelta el pie y deja el timón quieto
en 200 ms.

SEGURIDAD
  · ESPACIO o el botón rojo = PARO de software: todo a cero y pie suelto. NO reemplaza al hongo.
  · El joystick y la palanca vuelven a cero al soltar el mouse. Los botones N S E W y el pito
    son momentáneos (solo mientras se aprietan).
  · Si la ventana pierde el foco, se suelta todo (se puede desactivar en «Opciones»).
  · El CAN se arma con «Armar CAN», que pregunta antes. Al cerrar: todo a cero, pie suelto y X.

Requiere:  pip install pyserial      (y en Linux: sudo apt install python3-tk)
"""
import datetime as dt
import math
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    import serial
except ImportError:
    serial = None

PERIODO = 0.050
BAUD = 921600
VUELTAS_TOPE = 5.5            # 0x2414 de fábrica: vueltas de volante de tope a tope (docs/16)
GRADOS_RUEDA_TOPE = 180.0     # ±90° de la rueda (δmax 90°, manual)
RUEDA_POR_GRADO = GRADOS_RUEDA_TOPE / (VUELTAS_TOPE * 360.0)   # ESTIMADO, sin medir

FONDO, PANEL, TXT, AZUL, ROJO, VERDE, AMBAR = "#0b1e3a", "#13294d", "#cfe3ff", "#5a8fd6", "#ff5b5b", "#3ecf6e", "#ffd24d"


class Estado:
    """Lo que la GUI quiere mandar. Lo lee el hilo del latido."""
    def __init__(self):
        self.lock = threading.Lock()
        self.y = self.x = self.b = 0
        self.n = self.s = self.e = self.w = self.r = 0
        self.th = 0.0
        self.pie = 0
        self.latido = True

    def linea(self):
        with self.lock:
            return (f"L y={self.y} x={self.x} b={self.b} n={self.n} s={self.s} e={self.e} w={self.w} "
                    f"r={self.r} th={self.th:.1f} pie={self.pie}\n")

    def paro(self):
        with self.lock:
            self.y = self.x = self.b = 0
            self.n = self.s = self.e = self.w = self.r = 0
            self.pie = 0


class Enlace:
    """El puerto serie: un hilo que lee y otro que late. En --demo no abre nada."""
    def __init__(self, puerto, est, log):
        self.est, self.log, self.q = est, log, queue.Queue()
        self.ser, self.vivo, self.cerrojo = None, True, threading.Lock()
        if puerto != "--demo":
            if serial is None:
                raise SystemExit("Falta pyserial:  pip install pyserial")
            s = serial.Serial()
            s.port, s.baudrate, s.timeout = puerto, BAUD, 0.1
            s.dtr = False                     # no tocar EN ni GPIO0 al abrir
            s.rts = False
            s.open()
            self.ser = s
            threading.Thread(target=self._leer, daemon=True).start()
        threading.Thread(target=self._latir, daemon=True).start()

    def escribir(self, texto, registrar=True):
        if registrar:
            self.log.write(f"{dt.datetime.now():%H:%M:%S.%f}"[:-3] + " >> " + texto.strip() + "\n")
        if self.ser:
            with self.cerrojo:
                self.ser.write(texto.encode())

    def _leer(self):
        while self.vivo:
            try:
                l = self.ser.readline().decode("utf-8", "replace").strip()
            except Exception as e:          # se desenchufó
                self.q.put(("EV", f"puerto perdido: {e}"))
                return
            if not l:
                continue
            self.log.write(f"{dt.datetime.now():%H:%M:%S.%f}"[:-3] + " " + l + "\n")
            if l.startswith("S "):
                self.q.put(("S", dict(kv.split("=", 1) for kv in l[2:].split() if "=" in kv)))
            elif l.startswith("EV "):
                self.q.put(("EV", l[3:]))

    def _latir(self):
        prox, ultima = time.monotonic(), None
        while self.vivo:
            if self.est.latido:
                l = self.est.linea()
                self.escribir(l, registrar=(l != ultima))   # al log solo cuando cambia
                ultima = l
            prox += PERIODO
            time.sleep(max(0.0, prox - time.monotonic()))

    def cerrar(self):
        self.est.paro()
        for _ in range(3):
            self.escribir(self.est.linea())
            time.sleep(PERIODO)
        self.escribir("X\n")
        self.vivo = False
        time.sleep(0.1)
        if self.ser:
            self.ser.close()


class Gui:
    def __init__(self, raiz, puerto):
        self.raiz, self.est = raiz, Estado()
        aqui = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(os.path.join(aqui, "logs"), exist_ok=True)
        self.ruta_log = os.path.join(aqui, "logs", f"rig_{dt.datetime.now():%Y%m%d-%H%M%S}.log")
        self.log = open(self.ruta_log, "w", encoding="utf-8", buffering=1)
        self.enlace = Enlace(puerto, self.est, self.log)
        self.demo = puerto == "--demo"

        raiz.title("TaTa · rig" + ("  (DEMO, sin ESP)" if self.demo else f"  ({puerto})"))
        raiz.configure(bg=FONDO)
        self.soltar_al_perder_foco = tk.BooleanVar(value=True)
        self.mag_teclado = tk.IntVar(value=60)

        arriba = tk.Frame(raiz, bg=FONDO); arriba.pack(fill="x", padx=8, pady=6)
        self._barra(arriba)
        medio = tk.Frame(raiz, bg=FONDO); medio.pack(padx=8, pady=4)
        self._timon(medio)
        self._multipiloto(medio)
        self._pie(medio)
        self._eventos(raiz)

        raiz.bind("<space>", lambda e: self.paro())
        raiz.bind("<FocusOut>", self._foco)
        for k, (dx, dy) in {"Up": (0, 1), "Down": (0, -1), "Left": (-1, 0), "Right": (1, 0)}.items():
            raiz.bind(f"<KeyPress-{k}>", lambda e, d=(dx, dy): self._tecla(d, True))
            raiz.bind(f"<KeyRelease-{k}>", lambda e, d=(dx, dy): self._tecla(d, False))
        raiz.protocol("WM_DELETE_WINDOW", self.salir)
        self.raiz.after(50, self._tic)

    # ---------- barra superior: CAN, latido, paro ----------
    def _barra(self, f):
        b = dict(font=("Helvetica", 11, "bold"), width=12)
        tk.Button(f, text="Armar CAN", bg=AMBAR, command=self.armar_can, **b).pack(side="left", padx=3)
        tk.Button(f, text="Silencio (X)", bg="#ccc", command=lambda: self.enlace.escribir("X\n"), **b).pack(side="left", padx=3)
        self.latido_var = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="latido (desmarcar = probar el watchdog)", variable=self.latido_var,
                       command=self._latido, bg=FONDO, fg=TXT, selectcolor=PANEL,
                       activebackground=FONDO).pack(side="left", padx=10)
        tk.Checkbutton(f, text="soltar todo al perder el foco", variable=self.soltar_al_perder_foco,
                       bg=FONDO, fg=TXT, selectcolor=PANEL, activebackground=FONDO).pack(side="left", padx=4)
        tk.Button(f, text="PARO  (espacio)", bg=ROJO, fg="white", font=("Helvetica", 14, "bold"),
                  command=self.paro).pack(side="right", padx=3)
        self.lbl_can = tk.Label(f, text="CAN: —", bg=FONDO, fg=TXT, font=("Consolas", 11))
        self.lbl_can.pack(side="right", padx=12)

    # ---------- timón ----------
    def _timon(self, padre):
        f = tk.LabelFrame(padre, text=" Timón (volante emulado) ", bg=PANEL, fg=TXT, font=("Helvetica", 11, "bold"))
        f.grid(row=0, column=0, padx=6, sticky="n")
        self.W, self.R, self.HUB = 300, 120, 30
        self.cv = tk.Canvas(f, width=self.W, height=self.W, bg=PANEL, highlightthickness=0)
        self.cv.pack(padx=6, pady=4)
        self.cv.bind("<ButtonPress-1>", self._timon_toma)
        self.cv.bind("<B1-Motion>", self._timon_arrastra)
        self.cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "_arr", None))
        self._arr = None
        fila = tk.Frame(f, bg=PANEL); fila.pack(pady=2)
        for d in (-90, -10, 10, 90):
            tk.Button(fila, text=f"{d:+d}°", width=5, command=lambda d=d: self._timon_a(self.est.th + d)).pack(side="left", padx=2)
        tk.Button(fila, text="0", width=4, command=lambda: self._timon_a(0)).pack(side="left", padx=2)
        fila2 = tk.Frame(f, bg=PANEL); fila2.pack(pady=4)
        tk.Label(fila2, text="ir a", bg=PANEL, fg=TXT).pack(side="left")
        self.ent_ir = tk.Entry(fila2, width=8, justify="right"); self.ent_ir.pack(side="left", padx=3)
        self.ent_ir.bind("<Return>", lambda e: self._ir())
        tk.Label(fila2, text="° volante", bg=PANEL, fg=TXT).pack(side="left")
        tk.Button(fila2, text="Ir", width=4, command=self._ir).pack(side="left", padx=4)
        fila3 = tk.Frame(f, bg=PANEL); fila3.pack(pady=4)
        tk.Label(fila3, text="ángulo actual del sensor", bg=PANEL, fg=TXT).pack(side="left")
        self.ent_t = tk.Entry(fila3, width=7, justify="right"); self.ent_t.insert(0, "0"); self.ent_t.pack(side="left", padx=3)
        tk.Button(fila3, text="Armar timón (T)", bg=AMBAR, command=self.armar_timon).pack(side="left", padx=4)
        self.lbl_timon = tk.Label(f, text="", bg=PANEL, fg=TXT, font=("Consolas", 10), justify="left")
        self.lbl_timon.pack(fill="x", padx=6, pady=4)

    def _timon_a(self, grados):
        with self.est.lock:
            self.est.th = float(grados)

    def _ir(self):
        try:
            self._timon_a(float(self.ent_ir.get().replace(",", ".")))
        except ValueError:
            self._evento("«ir a» necesita un número de grados")

    def _ang_mouse(self, e):
        return math.degrees(math.atan2(e.x - self.W / 2, -(e.y - self.W / 2)))

    def _timon_toma(self, e):
        self._arr = self._ang_mouse(e)

    def _timon_arrastra(self, e):
        if self._arr is None:
            return
        a = self._ang_mouse(e)
        d = (a - self._arr + 180) % 360 - 180          # sigue vueltas enteras
        self._arr = a
        self._timon_a(self.est.th + d)

    def armar_timon(self):
        try:
            t = float(self.ent_t.get().replace(",", "."))
        except ValueError:
            return self._evento("el ángulo del sensor tiene que ser un número")
        if not messagebox.askokcancel("Armar timón",
                f"El emulador va a sacar el seno/coseno de {t:.1f}°.\n\n"
                "Tiene que ser el ángulo que daba el sensor REAL al desconectarlo, para que el cambio no "
                "gire la rueda. En el banco, 0 está bien.\n\n¿Armar?"):
            return
        self._timon_a(t)
        self.enlace.escribir(f"T {t:.1f}\n")

    def _dibujar_timon(self, esp_th):
        cv, W, R, H = self.cv, self.W, self.R, self.HUB
        cx = cy = W / 2
        cv.delete("all")
        cv.create_polygon(cx - 9, cy - R - 16, cx + 9, cy - R - 16, cx, cy - R + 2, fill=AMBAR, outline="")
        cv.create_oval(cx - R, cy - R, cx + R, cy + R, outline=AZUL, width=9)
        cv.create_oval(cx - H, cy - H, cx + H, cy + H, outline=AZUL, width=5, fill=FONDO)
        th = math.radians(self.est.th)
        for s in (0, 120, 240):
            a = th + math.radians(s)
            cv.create_line(cx + H * math.sin(a), cy - H * math.cos(a), cx + R * math.sin(a), cy - R * math.cos(a), fill=AZUL, width=7)
        mx, my = cx + R * math.sin(th), cy - R * math.cos(th)
        cv.create_oval(mx - 9, my - 9, mx + 9, my + 9, fill=ROJO, outline="")
        if esp_th is not None:                          # dónde está de verdad el ESP (sigue con rampa)
            t2 = math.radians(esp_th)
            ex, ey = cx + (R - 22) * math.sin(t2), cy - (R - 22) * math.cos(t2)
            cv.create_oval(ex - 6, ey - 6, ex + 6, ey + 6, fill=VERDE, outline="")
        cv.create_text(cx, cy, text=f"{self.est.th:.0f}°", fill=TXT, font=("Helvetica", 12, "bold"))

    # ---------- multipiloto ----------
    def _multipiloto(self, padre):
        f = tk.LabelFrame(padre, text=" Multipiloto (0x182, nodo 2) ", bg=PANEL, fg=TXT, font=("Helvetica", 11, "bold"))
        f.grid(row=0, column=1, padx=6, sticky="n")
        self.JS = 220
        self.jcv = tk.Canvas(f, width=self.JS, height=self.JS, bg=FONDO, highlightthickness=0)
        self.jcv.grid(row=0, column=0, rowspan=3, padx=6, pady=6)
        self.jcv.bind("<B1-Motion>", self._joy)
        self.jcv.bind("<ButtonPress-1>", self._joy)
        self.jcv.bind("<ButtonRelease-1>", lambda e: self._joy_cero())
        tk.Label(f, text="joystick: arrastrar · flechas = magnitud de abajo", bg=PANEL, fg=TXT).grid(row=3, column=0)
        tk.Scale(f, from_=0, to=255, orient="horizontal", variable=self.mag_teclado, bg=PANEL, fg=TXT,
                 highlightthickness=0, length=200).grid(row=4, column=0)
        # palanca trasera (vertical, vuelve a cero al soltar)
        tk.Label(f, text="palanca\ntrasera", bg=PANEL, fg=TXT).grid(row=0, column=1)
        self.pal = tk.Scale(f, from_=255, to=-255, orient="vertical", bg=PANEL, fg=TXT, length=170,
                            highlightthickness=0, command=self._palanca)
        self.pal.grid(row=1, column=1, rowspan=2, padx=4)
        self.pal.bind("<ButtonRelease-1>", lambda e: self.pal.set(0))
        tk.Label(f, text="(sin probar\nen el equipo)", bg=PANEL, fg=AMBAR, font=("Helvetica", 8)).grid(row=3, column=1)
        # botones momentáneos
        bf = tk.Frame(f, bg=PANEL); bf.grid(row=5, column=0, columnspan=2, pady=6)
        for i, (k, txt) in enumerate((("n", "N"), ("s", "S"), ("e", "E"), ("w", "W"), ("r", "PITO"))):
            bt = tk.Button(bf, text=txt, width=5, font=("Helvetica", 11, "bold"))
            bt.grid(row=0, column=i, padx=3)
            bt.bind("<ButtonPress-1>", lambda e, k=k: self._boton(k, 1))
            bt.bind("<ButtonRelease-1>", lambda e, k=k: self._boton(k, 0))
        self.lbl_mp = tk.Label(f, text="", bg=PANEL, fg=TXT, font=("Consolas", 10), justify="left")
        self.lbl_mp.grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=4)

    def _joy(self, e):
        c = self.JS / 2
        x = max(-1, min(1, (e.x - c) / (c - 12)))
        y = max(-1, min(1, -(e.y - c) / (c - 12)))
        with self.est.lock:
            self.est.x, self.est.y = int(round(x * 255)), int(round(y * 255))

    def _joy_cero(self):
        with self.est.lock:
            self.est.x = self.est.y = 0

    def _tecla(self, d, abajo):
        m = self.mag_teclado.get() if abajo else 0
        with self.est.lock:
            if d[0]:
                self.est.x = d[0] * m
            if d[1]:
                self.est.y = d[1] * m

    def _palanca(self, v):
        with self.est.lock:
            self.est.b = int(float(v))

    def _boton(self, k, v):
        with self.est.lock:
            setattr(self.est, k, v)

    def _dibujar_joy(self):
        cv, S = self.jcv, self.JS
        c = S / 2
        cv.delete("all")
        cv.create_rectangle(10, 10, S - 10, S - 10, outline=AZUL, width=2)
        cv.create_line(c, 10, c, S - 10, fill="#2a4a7a"); cv.create_line(10, c, S - 10, c, fill="#2a4a7a")
        for txt, x, y in (("adelante", c, 20), ("atrás", c, S - 20), ("izq", 28, c - 10), ("der", S - 28, c - 10)):
            cv.create_text(x, y, text=txt, fill="#7f9cc9", font=("Helvetica", 8))
        kx = c + self.est.x / 255 * (c - 12)
        ky = c - self.est.y / 255 * (c - 12)
        cv.create_oval(kx - 14, ky - 14, kx + 14, ky + 14, fill=AMBAR if (self.est.x or self.est.y) else AZUL, outline="")

    # ---------- pie ----------
    def _pie(self, padre):
        f = tk.LabelFrame(padre, text=" Pedal de hombre muerto ", bg=PANEL, fg=TXT, font=("Helvetica", 11, "bold"))
        f.grid(row=0, column=2, padx=6, sticky="n")
        self.bt_pie = tk.Button(f, text="SUELTO", width=12, height=3, font=("Helvetica", 16, "bold"),
                                bg="#556", fg="white", command=self._pie_toggle)
        self.bt_pie.pack(padx=10, pady=10)
        tk.Button(f, text="Rearmar (R)", width=14, command=lambda: self.enlace.escribir("R\n")).pack(pady=4)
        tk.Label(f, text="R por serie es solo de BANCO\n(en el equipo: botón GPIO32)\n\nCAN y timón obedecen SOLO\ncon el pie ARMADO", bg=PANEL, fg=AMBAR,
                 font=("Helvetica", 8)).pack()
        self.lbl_pie = tk.Label(f, text="", bg=PANEL, fg=TXT, font=("Consolas", 10), justify="left")
        self.lbl_pie.pack(fill="x", padx=6, pady=8)

    def _pie_toggle(self):
        with self.est.lock:
            self.est.pie = 0 if self.est.pie else 1

    # ---------- eventos ----------
    def _eventos(self, raiz):
        self.lst = tk.Listbox(raiz, height=9, bg="#081428", fg=TXT, font=("Consolas", 10))
        self.lst.pack(fill="both", expand=True, padx=8, pady=6)
        self._evento(f"log: {self.ruta_log}")

    def _evento(self, t):
        self.lst.insert("end", f"{dt.datetime.now():%H:%M:%S}  {t}")
        self.lst.see("end")
        if self.lst.size() > 300:
            self.lst.delete(0)

    # ---------- acciones globales ----------
    def paro(self):
        self.est.paro()
        self.pal.set(0)
        self._evento("PARO de software: todo a cero, pie suelto")

    def _foco(self, e):
        # FocusOut llega también al pasar entre widgets; solo cuenta si la ventana entera perdió el foco
        self.raiz.after(60, self._foco_check)

    def _foco_check(self):
        if self.soltar_al_perder_foco.get() and self.raiz.focus_get() is None:
            if self.est.pie or self.est.x or self.est.y or self.est.b:
                self._evento("la ventana perdió el foco: todo a cero, pie suelto")
            self.est.paro(); self.pal.set(0)

    def _latido(self):
        self.est.latido = self.latido_var.get()
        self._evento("latido " + ("de vuelta (el pie queda suelto hasta el rearme)" if self.est.latido
                                  else "CORTADO: el ESP tiene que soltar todo en <= 200 ms"))

    def armar_can(self):
        if messagebox.askokcancel("Armar CAN",
                "El ESP va a TRANSMITIR al bus como nodo 2.\n\n"
                "· ¿El CAN del multipiloto real está FUERA?\n"
                "· ¿Llave en OFF (para que vea el arranque del grupo)?\n"
                "· En el banco: ¿el Master falso o el SH-C30G está conectado?\n\n¿Armar?"):
            self.enlace.escribir("A\n")

    def salir(self):
        try:
            self.enlace.cerrar()
        finally:
            self.log.close()
            self.raiz.destroy()

    # ---------- refresco ----------
    def _tic(self):
        esp_th = None
        try:
            while True:
                tipo, dato = self.enlace.q.get_nowait()
                if tipo == "EV":
                    self._evento(dato)
                else:
                    self.ultimo = dato
        except queue.Empty:
            pass
        u = getattr(self, "ultimo", {})
        if u:
            try:
                esp_th = float(u.get("th", "nan"))
            except ValueError:
                esp_th = None
            self.lbl_can.config(text=f"CAN: {u.get('can')} · bus {u.get('bus')} · TEC {u.get('tec')} REC {u.get('rec')}"
                                     f" · rx {u.get('rx')}/s · Master {'sí' if u.get('master') == '1' else 'no'}")
        th = self.est.th
        self._dibujar_timon(esp_th)
        self.lbl_timon.config(text=f"volante pedido {th:8.1f}°  ({th / 360:+.2f} vueltas)\n"
                                   f"ESP (con rampa) {u.get('th', '—'):>8}°   armado: {'sí' if u.get('tarm') == '1' else 'NO'}\n"
                                   f"rueda ESTIMADA  {th * RUEDA_POR_GRADO:8.1f}°  (5.5 vueltas = 180°, sin medir)")
        self._dibujar_joy()
        e = self.est
        self.lbl_mp.config(text=f"y {e.y:+4d}  x {e.x:+4d}  palanca {e.b:+4d}\n"
                                f"N{e.n} S{e.s} E{e.e} W{e.w} pito {e.r}\n0x182 del ESP: {u.get('f182', '—')}")
        if u.get("pie") == "DISPARADO" and self.est.pie:     # tras un disparo, pisar otra vez es a propósito
            with self.est.lock:
                self.est.pie = 0
            self._evento("pie DISPARADO: el botón vuelve a SUELTO; rearmar y después pisar")
        pisa = u.get("pisa") == "1"
        self.bt_pie.config(text="PISADO" if e.pie else "SUELTO", bg=(VERDE if pisa else AMBAR) if e.pie else "#556")
        self.lbl_pie.config(text=f"pido: {'pisar' if e.pie else 'soltar'}\nESP: {u.get('pie', '—')}\n"
                                 f"relés: {'PISANDO' if pisa else 'sueltos'}\nparo: {u.get('paro', '—')} mV\n"
                                 f"disparos: {u.get('disparos', '—')}\nlatido: {u.get('lat', '—')} ms\n"
                                 f"loop máx: {u.get('loopmax', '—')} µs")
        self.raiz.after(50, self._tic)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    raiz = tk.Tk()
    Gui(raiz, sys.argv[1])
    raiz.mainloop()


if __name__ == "__main__":
    main()
