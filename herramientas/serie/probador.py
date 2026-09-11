#!/usr/bin/env python3
"""
TaTa · PROBADOR DE CABLES SERIE
Interfaz para probar un adaptador USB-serie en el mostrador.
Solo necesita:  pip install pyserial      (tkinter viene con Python)

    python probador.py
"""
import tkinter as tk
import threading, time

try:
    import serial, serial.tools.list_ports
    HAY_SERIAL = True
except ImportError:
    HAY_SERIAL = False

# ── paleta ────────────────────────────────────────────────────────────────
BG     = "#0a1633"
PANEL  = "#122a63"
BORDE  = "#3d6fd9"
LUZ    = "#7fb2ff"
TEXTO  = "#d6e6ff"
AMBAR  = "#ffd23f"
OK     = "#4ade80"
MAL    = "#ff5b6e"
SOMBRA = "#061024"

F  = lambda n, b=True: ("Consolas", n, "bold" if b else "normal")

META_FICHA    = 1_000_000
META_NECESITA = 115_200
BAUDS = [1200, 2400, 4800, 9600, 14400, 19200, 38400,
         57600, 115200, 230400, 460800, 921600, 1000000]


def barra(valor, meta, ancho=30):
    frac = min(1.0, (valor / meta) if meta else 0)
    n = int(round(frac * ancho))
    return "█" * n + "░" * (ancho - n)


class App:
    def __init__(self, root):
        self.root = root
        root.title("TaTa · Probador de cables serie")
        root.configure(bg=BG)
        root.geometry("940x680")
        root.minsize(880, 620)

        # ── banner + puerto ──────────────────────────────────────────────
        cab = tk.Frame(root, bg=PANEL, highlightbackground=BORDE,
                       highlightthickness=4)
        cab.pack(fill="x", padx=14, pady=(14, 8))

        izq = tk.Frame(cab, bg=PANEL)
        izq.pack(side="left", padx=16, pady=10)
        tk.Label(izq, text="▚▚  P R O B A D O R   D E   C A B L E S  ▚▚",
                 font=F(20), bg=PANEL, fg=AMBAR).pack(anchor="w")
        tk.Label(izq, text="TaTa · proyecto Montasa · puerto serie RS-232",
                 font=F(10, False), bg=PANEL, fg=LUZ).pack(anchor="w")

        der = tk.Frame(cab, bg=SOMBRA, highlightbackground=BORDE,
                       highlightthickness=3)
        der.pack(side="right", padx=16, pady=10)
        tk.Label(der, text="  PUERTOS DETECTADOS  ", font=F(10), bg=BORDE,
                 fg="white").pack(fill="x")
        self.puerto = tk.StringVar(value="—")
        self.om = tk.OptionMenu(der, self.puerto, "—")
        self.om.configure(font=F(13), bg=SOMBRA, fg=AMBAR, activebackground=BORDE,
                          activeforeground="white", highlightthickness=0,
                          bd=0, width=26, anchor="w")
        self.om["menu"].configure(font=F(12), bg=PANEL, fg=TEXTO,
                                  activebackground=BORDE, activeforeground="white")
        self.om.pack(fill="x", padx=6, pady=(6, 2))
        self.aviso = tk.Label(der, text="", font=F(9, False), bg=SOMBRA, fg=LUZ)
        self.aviso.pack(pady=(0, 4))
        self.boton(der, "◄ REESCANEAR", self.escanear).pack(pady=(0, 7))

        # ── cuerpo ────────────────────────────────────────────────────────
        cuerpo = tk.Frame(root, bg=BG)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=10)

        menu = tk.Frame(cuerpo, bg=PANEL, highlightbackground=BORDE,
                        highlightthickness=4)
        menu.pack(side="left", fill="y", padx=(0, 12))
        tk.Label(menu, text="  ELEGÍ UNA PRUEBA  ", font=F(13), bg=BORDE,
                 fg="white").pack(fill="x", pady=(0, 6))

        self.items = []
        for txt, fn in (("PRUEBA COMPLETA",  self.completa),
                        ("VELOCIDAD MÁXIMA", self.velocidad),
                        ("PARIDAD",          self.paridad),
                        ("LOOPBACK",         self.loopback)):
            self.items.append(self.opcion(menu, txt, fn))

        tk.Label(menu, text="\n  LOOPBACK necesita\n  jumper entre los\n  pines 2 y 3\n",
                 font=F(9, False), bg=PANEL, fg=LUZ, justify="left").pack(pady=6)

        pan = tk.Frame(cuerpo, bg=SOMBRA, highlightbackground=BORDE,
                       highlightthickness=4)
        pan.pack(side="left", fill="both", expand=True)
        self.out = tk.Text(pan, bg=SOMBRA, fg=TEXTO, font=F(12, False),
                           bd=0, padx=16, pady=14, wrap="none",
                           insertbackground=SOMBRA)
        self.out.pack(fill="both", expand=True)
        for tag, col in (("ok", OK), ("mal", MAL), ("amb", AMBAR),
                         ("luz", LUZ), ("tit", "white")):
            self.out.tag_configure(tag, foreground=col)
        self.out.tag_configure("grande", font=F(17))
        self.out.configure(state="disabled")

        self.ocupado = False
        self.lista = []
        self.escanear()
        self.bienvenida()
        self.auto()

    # ── widgets ───────────────────────────────────────────────────────────
    def boton(self, padre, txt, cmd):
        b = tk.Label(padre, text=f" {txt} ", font=F(11), bg=BORDE, fg="white",
                     padx=6, pady=3, cursor="hand2")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: b.configure(bg=LUZ, fg=SOMBRA))
        b.bind("<Leave>", lambda e: b.configure(bg=BORDE, fg="white"))
        return b

    def opcion(self, padre, txt, fn):
        l = tk.Label(padre, text=f"   {txt}   ", font=F(15), bg=PANEL, fg=TEXTO,
                     anchor="w", padx=10, pady=11, cursor="hand2")
        l.pack(fill="x", padx=8, pady=3)
        l.bind("<Enter>", lambda e: l.configure(bg=BORDE, fg="white",
                                                text=f" ► {txt}   "))
        l.bind("<Leave>", lambda e: l.configure(bg=PANEL, fg=TEXTO,
                                                text=f"   {txt}   "))
        l.bind("<Button-1>", lambda e: self.lanzar(fn))
        return l

    # ── salida ────────────────────────────────────────────────────────────
    def limpiar(self):
        self.out.configure(state="normal"); self.out.delete("1.0", "end")
        self.out.configure(state="disabled")

    def p(self, txt="", tag=None):
        self.out.configure(state="normal")
        self.out.insert("end", txt + "\n", tag or ())
        self.out.see("end"); self.out.configure(state="disabled")
        self.root.update_idletasks()

    def bienvenida(self):
        self.limpiar()
        self.p()
        self.p("   ¿QUÉ HACE ESTO?", "amb")
        self.p()
        self.p("   Mide si un cable USB-serie cumple lo que")
        self.p("   promete su ficha técnica.")
        self.p()
        self.p("   ┌────────────────────────────────────────┐", "luz")
        self.p("   │  LA FICHA PROMETE .....  1,000,000     │", "luz")
        self.p("   │  NOSOTROS NECESITAMOS .....  115,200   │", "luz")
        self.p("   └────────────────────────────────────────┘", "luz")
        self.p()
        self.p("   Elegí una prueba en el menú de la izquierda.")
        self.p()
        if not HAY_SERIAL:
            self.p("   FALTA pyserial:  pip install pyserial", "mal")

    # ── control ───────────────────────────────────────────────────────────
    def _listar(self):
        if not HAY_SERIAL:
            return []
        return [f"{x.device}  ({x.description[:24]})"
                for x in serial.tools.list_ports.comports()]

    def escanear(self, ps=None):
        ps = self._listar() if ps is None else ps
        self.lista = list(ps)
        m = self.om["menu"]; m.delete(0, "end")
        vis = ps or ["— sin puertos —"]
        for x in vis:
            m.add_command(label=x, command=lambda v=x: self.puerto.set(v))
        # conserva la seleccion si el puerto sigue ahi; si no, toma el primero
        if self.puerto.get() not in vis:
            self.puerto.set(vis[0])
        n = len(ps)
        if n == 0:
            self.aviso.configure(text="conectá el cable", fg=MAL)
        elif n == 1:
            self.aviso.configure(text="1 puerto", fg=LUZ)
        else:
            self.aviso.configure(text=f"{n} puertos · elegí arriba", fg=AMBAR)

    def auto(self):
        """Refresca solo si la lista cambio. Asi el cable nuevo aparece solo."""
        if not self.ocupado:
            ps = self._listar()
            if ps != self.lista:
                self.escanear(ps)
        self.root.after(1500, self.auto)

    def com(self):
        return self.puerto.get().split()[0]

    def lanzar(self, fn):
        if self.ocupado:
            return
        if not HAY_SERIAL:
            self.limpiar(); self.p("\n   Falta pyserial.  pip install pyserial", "mal"); return
        if "—" in self.puerto.get():
            self.limpiar(); self.p("\n   No hay puerto. Conectá el cable y REESCANEAR.", "mal"); return
        self.ocupado = True
        threading.Thread(target=self._correr, args=(fn,), daemon=True).start()

    def _correr(self, fn):
        try:
            fn()
        except Exception as e:
            self.p(f"\n   ERROR: {e}", "mal")
        finally:
            self.ocupado = False

    # ── pruebas ───────────────────────────────────────────────────────────
    def _abre(self, baud, parity='N'):
        try:
            s = serial.Serial(self.com(), baud, parity=parity, timeout=0.3)
            s.close(); return True
        except Exception:
            return False

    def _velocidad(self):
        tope = 0
        for b in BAUDS:
            ok = self._abre(b)
            self.p(f"      {b:>9,}   {'ABRE' if ok else 'no abre'}",
                   "ok" if ok else "mal")
            if ok: tope = max(tope, b)
            time.sleep(0.12)
        return tope

    def velocidad(self):
        self.limpiar()
        self.p("\n   VELOCIDAD MÁXIMA\n", "amb")
        tope = self._velocidad()
        self._resumen_velocidad(tope)
        return tope

    def _resumen_velocidad(self, tope):
        self.p()
        self.p("   ══════════════════════════════════════════════", "luz")
        self.p(f"   LA FICHA PROMETE .......  {META_FICHA:>9,}", "luz")
        self.p(f"   NOSOTROS NECESITAMOS ...  {META_NECESITA:>9,}", "luz")
        self.p(f"   ESTE CABLE LLEGÓ A .....  {tope:>9,}",
               "ok" if tope >= META_NECESITA else "mal")
        self.p("   ══════════════════════════════════════════════", "luz")
        self.p()
        p1 = 100 * tope / META_FICHA
        p2 = 100 * tope / META_NECESITA
        self.p(f"   [{barra(tope, META_FICHA)}]  {p1:5.1f}%  de la ficha",
               "ok" if p1 >= 90 else "mal")
        self.p(f"   [{barra(tope, META_NECESITA)}]  {p2:5.1f}%  de lo que necesitamos",
               "ok" if p2 >= 100 else "mal")

    def _paridad(self):
        r = {}
        for p, nom in (('N', "ninguna"), ('E', "par"), ('O', "impar")):
            ok = self._abre(9600, p)
            r[nom] = ok
            self.p(f"      paridad {nom:<8} {'SI' if ok else 'NO'}",
                   "ok" if ok else "mal")
            time.sleep(0.12)
        return r

    def paridad(self):
        self.limpiar()
        self.p("\n   PARIDAD\n", "amb")
        self.p("   Un cable serio acepta las tres. Si solo acepta")
        self.p("   una, hay pruebas que nunca vamos a poder hacer.\n")
        r = self._paridad()
        n = sum(r.values())
        self.p()
        self.p(f"   PASÓ {n} DE 3", "ok" if n == 3 else "mal")
        return r

    def _loopback(self):
        patron = b"TATA-0123456789-abcdefghij\r\n"
        mejor = 0
        for b in (1200, 9600, 14400, 115200):
            try:
                s = serial.Serial(self.com(), b, timeout=1.0, write_timeout=2.0)
            except Exception:
                self.p(f"      {b:>7,}   no abre", "mal"); continue
            try:
                s.reset_input_buffer(); s.write(patron); s.flush()
                t0 = time.time(); eco = bytearray()
                while time.time() - t0 < 1.5 and len(eco) < len(patron):
                    eco += s.read(len(patron) - len(eco))
            finally:
                s.close()
            if bytes(eco) == patron:
                self.p(f"      {b:>7,}   {len(eco)}/{len(patron)} bytes  IDÉNTICOS", "ok")
                mejor += 1
            elif eco:
                self.p(f"      {b:>7,}   volvió basura", "mal")
            else:
                self.p(f"      {b:>7,}   no volvió nada", "mal")
            time.sleep(0.5)
        return mejor

    def loopback(self):
        self.limpiar()
        self.p("\n   LOOPBACK\n", "amb")
        self.p("   Necesita un puente entre el pin 2 y el pin 3")
        self.p("   del conector DB9. Manda un texto y lo lee de")
        self.p("   vuelta por el mismo cable.\n")
        n = self._loopback()
        self.p()
        if n:
            self.p(f"   EL CABLE MANDA Y RECIBE BIEN  ({n} velocidades)", "ok")
        else:
            self.p("   NO VOLVIÓ NADA", "mal")
            self.p("   O falta el puente 2-3, o el cable está muerto.", "mal")
        return n

    # ── completa ──────────────────────────────────────────────────────────
    def completa(self):
        self.limpiar()
        self.p("\n   PRUEBA COMPLETA\n", "amb")
        self.p("   1 · VELOCIDAD", "luz")
        tope = self._velocidad()
        self.p()
        self.p("   2 · PARIDAD", "luz")
        par = self._paridad()
        self.p()
        self._resumen_velocidad(tope)

        vel_ok = tope >= META_NECESITA
        par_ok = sum(par.values()) == 3
        self.p()
        self.p()
        if vel_ok and par_ok:
            self.p("   ╔══════════════════════════════════════╗", "ok")
            self.p("   ║        E S T E   S I R V E           ║", "ok")
            self.p("   ╚══════════════════════════════════════╝", "ok")
        else:
            self.p("   ╔══════════════════════════════════════╗", "mal")
            self.p("   ║     E S T E   N O   S I R V E        ║", "mal")
            self.p("   ╚══════════════════════════════════════╝", "mal")
            self.p()
            if not vel_ok:
                self.p(f"   · No llega a {META_NECESITA:,}. Se queda en {tope:,}.", "mal")
                self.p(f"     Eso es el {100*tope/META_FICHA:.1f}% de lo que dice la ficha.", "mal")
            if not par_ok:
                faltan = [k for k, v in par.items() if not v]
                self.p(f"   · No acepta paridad: {', '.join(faltan)}.", "mal")


if __name__ == "__main__":
    r = tk.Tk()
    App(r)
    r.mainloop()
