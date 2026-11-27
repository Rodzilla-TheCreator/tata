"""banco_timon.py — prueba en banco del emulador de timón SOLDADO, leído con el Arduino. 26-nov-2026.

    ESP32  : emulador_timon.ino   (comando "P<grados>" por serie)
    Arduino: caracterizador_timon.ino  (A0 = verde, A1 = café; con 'l' manda CSV ms,verde,cafe,...)

    python banco_timon.py COM_ESP COM_ARDUINO [--vref 5.0]

1) 12 ángulos fijos (0, 30 ... 330): voltaje esperado vs medido por canal, y el radio.
2) Recta por canal medido = a·esperado + b  ->  k/o nuevos para el sketch si la placa cambió la ganancia.
3) Barrido de 2 vueltas a ~150 °/s: el radio debe quedar plano (lo que chequea node 4).

--vref: el 5 V REAL del Arduino medido con el multímetro (pin 5V–GND). El caracterizador asume 5.000.
Solo banco: nada de esto va al montacargas.
"""
import argparse, math, sys, threading, time
import serial

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VO, VA = 2.47, 1.98                 # sensor real (24-oct)
K_OLD = {"verde": (1.380, 0.093), "cafe": (1.374, 0.123)}   # lo que tiene emulador_timon.ino (27-nov)


def esperado(ang):
    t = math.radians(ang)
    return VO + VA * math.cos(t), VO + VA * math.sin(t)


class Arduino:
    def __init__(self, puerto, vref):
        self.esc = vref / 5.0
        self.s = serial.Serial(puerto, 115200, timeout=0.2)
        self.muestras = []          # (t, verde, cafe)
        self.lock = threading.Lock()
        time.sleep(2.5)             # el Uno/Nano se resetea al abrir el puerto
        self.s.reset_input_buffer()
        self.s.write(b"l")          # activa el CSV
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        while True:
            try:
                linea = self.s.readline().decode(errors="ignore").strip()
            except serial.SerialException:
                return
            p = linea.split(",")
            if len(p) == 6:
                try:
                    v, c = float(p[1]) * self.esc, float(p[2]) * self.esc
                except ValueError:
                    continue
                with self.lock:
                    self.muestras.append((time.time(), v, c))
                    if len(self.muestras) > 2000:
                        del self.muestras[:1000]

    def desde(self, t0):
        with self.lock:
            return [(v, c) for (t, v, c) in self.muestras if t >= t0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("esp"); ap.add_argument("arduino")
    ap.add_argument("--vref", type=float, default=5.0)
    a = ap.parse_args()

    esp = serial.Serial()
    esp.port, esp.baudrate, esp.timeout = a.esp, 115200, 0
    esp.dtr = esp.rts = False
    esp.open()
    ard = Arduino(a.arduino, a.vref)

    def P(ang):
        esp.write(f"P{ang:.1f}\n".encode()); esp.reset_input_buffer()

    t0 = time.time()
    while not ard.desde(t0):
        if time.time() - t0 > 3:
            sys.exit("El Arduino no manda datos: ¿caracterizador_timon cargado? ¿puerto correcto?")
        time.sleep(0.1)

    # ---- 1) ángulos fijos ----
    print("\n 1) ÁNGULOS FIJOS            verde                      café            radio")
    print("   ang    esperado  medido     Δ      esperado  medido     Δ")
    filas = []
    for ang in range(0, 360, 30):
        P(ang); time.sleep(0.5)
        t = time.time(); time.sleep(0.4)
        m = ard.desde(t)
        if not m:
            sys.exit("Se cortó el Arduino a media prueba.")
        v = sum(x[0] for x in m) / len(m); c = sum(x[1] for x in m) / len(m)
        ev, ec = esperado(ang)
        r = math.hypot(v - VO, c - VO)
        filas.append((ang, ev, v, ec, c, r))
        print(f"   {ang:3d}    {ev:6.3f}   {v:6.3f}   {v-ev:+.3f}     {ec:6.3f}   {c:6.3f}   {c-ec:+.3f}    {r:.3f}")

    vs = [f[2] for f in filas] + [f[4] for f in filas]
    if max(vs) > 4.95:
        print("\n  !! Hay lecturas en 4.95-5.0 V: el Arduino está saturado o la salida está pegada arriba."
              "\n     Cortá el +11 V y revisá: op-amp sin realimentación (Rf/Rg) o el DAC no llega al IN+.")
    if max(vs) < 1.0:
        print("\n  !! Todo bajo 1 V: zener al revés, salida en corto a GND o sin +11 V en el pin 8.")

    # ---- 2) recta por canal ----
    print("\n 2) RECTA POR CANAL (medido = a·esperado + b)")
    nuevos, peor_res = {}, 0.0
    for nombre, ie, im in (("verde", 1, 2), ("cafe", 3, 4)):
        xs = [f[ie] for f in filas]; ys = [f[im] for f in filas]
        n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        aa = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        bb = my - aa * mx
        res = max(abs(y - (aa * x + bb)) for x, y in zip(xs, ys))
        peor_res = max(peor_res, res)
        ko, oo = K_OLD[nombre]
        nuevos[nombre] = (aa * ko, bb + aa * oo)
        print(f"   {nombre:5s}  a={aa:.3f}  b={bb:+.3f}  residuo máx {res:.3f} V   ->  k={aa*ko:.3f}  o={bb+aa*oo:.3f}")

    err = max(max(abs(f[2] - f[1]), abs(f[4] - f[3])) for f in filas)

    # ---- 3) barrido ----
    print("\n 3) BARRIDO 2 vueltas a ~150 °/s ...")
    P(0); time.sleep(0.5)          # sin esto, el salto 330->0 entra al barrido y da un radio falso (27-nov: 1.71)
    t = time.time(); ang = 0.0
    while ang <= 720:
        P(ang); ang += 3; time.sleep(0.02)
    m = ard.desde(t)
    P(0)
    radios = [math.hypot(v - VO, c - VO) for v, c in m]
    rmin, rmax = min(radios), max(radios)
    print(f"   {len(m)} muestras · radio min {rmin:.3f}  max {rmax:.3f}  (sensor real 1.95–1.98)")

    # ---- veredicto ----
    print("\n VEREDICTO")
    if err <= 0.06 and 1.88 <= rmin and rmax <= 2.05:
        print(f"   PASA: error máx {err:.3f} V, radio {rmin:.3f}–{rmax:.3f}. La placa soldada reproduce el sensor.")
    elif peor_res <= 0.04:
        print(f"   LINEAL pero descalibrada (error máx {err:.3f} V). Cambiar en emulador_timon.ino, timon_lazo.ino y teleop_wasd.ino:")
        print(f"     const float kV = {nuevos['verde'][0]:.3f}, oV = {nuevos['verde'][1]:.3f};")
        print(f"     const float kC = {nuevos['cafe'][0]:.3f}, oC = {nuevos['cafe'][1]:.3f};")
        print("   y volver a correr esta prueba.")
    else:
        print(f"   NO LINEAL (residuo {peor_res:.3f} V): algo satura o hay una soldadura mala. Mirar la tabla 1:"
              "\n   el canal y el ángulo donde Δ se dispara dicen dónde.")
    esp.close()


if __name__ == "__main__":
    main()
