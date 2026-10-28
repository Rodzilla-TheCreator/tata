#!/usr/bin/env python3
"""
rueda_timon.py — volante en pantalla para manejar el emulador del timon.

Dibuja un timon que rotas con A/D o arrastrando con el mouse, y le manda al ESP
el angulo absoluto por serial ("P<grados>"). El ESP (emulador_timon.ino) saca el
seno/coseno por los DAC. Sirve para probar el emulador a mano en el banco.

Uso:
    python rueda_timon.py            # abre COM6 (default)
    python rueda_timon.py COM7       # otro puerto
    python rueda_timon.py /dev/ttyUSB0

Requiere pyserial:  pip install pyserial

OJO: mientras esta GUI tiene el puerto del ESP, CERRA el Monitor Serie del IDE
(solo un programa puede abrir el COM a la vez). El circulo lo ves en el OTRO
monitor, el del Arduino lector (COM3), con caracterizador_timon.ino.

Controles:  A / D = girar izq/der (manteniendo)   ·   mouse = tomar y rotar
            C = centrar (0)   ·   Q = salir
"""
import sys, math
import tkinter as tk

try:
    import serial
except ImportError:
    serial = None

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM6"
BAUD = 115200
Vo, Va = 2.47, 1.98          # mismos que el sketch, solo para mostrar verde/cafe
STEP = 2.0                   # grados por tick (~30 ms) con A/D -> ~67 deg/s

ser = None
if serial is not None:
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0)
    except Exception as e:
        print(f"No pude abrir {PORT}: {e}  (sigo en modo demo, sin enviar)")

theta = 0.0                  # grados, acumula (gira libre, multivuelta)
held = set()
last_sent = None
drag = {"on": False, "prev": 0.0}

root = tk.Tk()
root.title("Rueda del timon -> ESP")
root.configure(bg="#0b1e3a")
W = 480
cx = cy = W / 2
R = 185
HUB = 44
cv = tk.Canvas(root, width=W, height=W, bg="#0b1e3a", highlightthickness=0)
cv.pack()
info = tk.Label(root, bg="#0b1e3a", fg="#cfe3ff", font=("Consolas", 12), justify="left")
info.pack(fill="x", padx=8, pady=6)


def draw():
    cv.delete("all")
    th = math.radians(theta)
    # referencia fija arriba (0 grados)
    cv.create_polygon(cx - 11, cy - R - 18, cx + 11, cy - R - 18, cx, cy - R + 2,
                      fill="#ffd24d", outline="")
    # aro y cubo
    cv.create_oval(cx - R, cy - R, cx + R, cy + R, outline="#5a8fd6", width=11)
    cv.create_oval(cx - HUB, cy - HUB, cx + HUB, cy + HUB, outline="#5a8fd6",
                   width=6, fill="#13294d")
    # rayos (3) que giran con theta
    for s in (0, 120, 240):
        a = th + math.radians(s)
        cv.create_line(cx + HUB * math.sin(a), cy - HUB * math.cos(a),
                       cx + R * math.sin(a),   cy - R * math.cos(a),
                       fill="#5a8fd6", width=9)
    # marcador rojo en el aro (gira)
    mx = cx + R * math.sin(th)
    my = cy - R * math.cos(th)
    cv.create_oval(mx - 10, my - 10, mx + 10, my + 10, fill="#ff5b5b", outline="")
    verde = Vo + Va * math.cos(th)
    cafe = Vo + Va * math.sin(th)
    estado = "conectado" if ser else "SIN serial (demo)"
    info.config(text=(
        f" angulo = {theta:8.1f} deg       verde = {verde:5.3f} V     cafe = {cafe:5.3f} V\n"
        f" A/D = girar    mouse = tomar y rotar    C = centrar    Q = salir\n"
        f" puerto: {PORT}   [{estado}]"))


def send():
    global last_sent
    v = round(theta, 1)
    if ser and v != last_sent:
        try:
            ser.write(f"P{v}\n".encode())
            last_sent = v
        except Exception:
            pass


def tick():
    global theta
    if 'a' in held:
        theta -= STEP
    if 'd' in held:
        theta += STEP
    draw()
    send()
    root.after(30, tick)


def key_down(e):
    global theta
    k = e.keysym.lower()
    if k in ('a', 'd'):
        held.add(k)
    elif k == 'c':
        theta = 0.0
    elif k == 'q':
        root.destroy()


def key_up(e):
    held.discard(e.keysym.lower())


def mouse_down(e):
    drag["on"] = True
    drag["prev"] = math.degrees(math.atan2(e.x - cx, -(e.y - cy)))


def mouse_move(e):
    global theta
    if not drag["on"]:
        return
    a = math.degrees(math.atan2(e.x - cx, -(e.y - cy)))
    d = a - drag["prev"]
    if d > 180:
        d -= 360
    elif d < -180:
        d += 360
    theta += d
    drag["prev"] = a


def mouse_up(e):
    drag["on"] = False


root.bind("<KeyPress>", key_down)
root.bind("<KeyRelease>", key_up)
cv.bind("<Button-1>", mouse_down)
cv.bind("<B1-Motion>", mouse_move)
cv.bind("<ButtonRelease-1>", mouse_up)

tick()
root.mainloop()
if ser:
    try:
        ser.close()
    except Exception:
        pass
