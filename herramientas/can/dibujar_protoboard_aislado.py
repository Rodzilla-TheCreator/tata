"""Dibuja protoboard_aislado.svg: el CAN aislado (ADuM1201 + B0505S + TJA1050) en protoboard.

    python dibujar_protoboard_aislado.py

Idea del armado: la protoboard se parte en dos mundos.
  rieles de ARRIBA = lado ESP   (+5 V del ESP y GND del ESP = amarillo)
  rieles de ABAJO  = lado bus   (+5 V aislado del B0505S y GND_bus = negativo de batería)
Nada une un riel de arriba con uno de abajo. Lo único que cruza son el B0505S y el ADuM1201.
"""
from pathlib import Path

W, H = 1240, 900
o = []
a = o.append

COL = {
    "rojo": "#d62728", "negro": "#222", "morado": "#8e44ad", "azul": "#1f77b4",
    "verde": "#2ca02c", "naranja": "#ff7f0e", "gris": "#8a8a8a",
}


def txt(x, y, s, size=13, anchor="start", weight="normal", fill="#222", italic=False):
    st = ' font-style="italic"' if italic else ""
    a(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
      f'fill="{fill}"{st}>{s}</text>')


def caja(x, y, w, h, fill, stroke="#333", r=6):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')


def cable(puntos, color, ancho=4):
    d = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(puntos))
    a(f'<path d="{d}" fill="none" stroke="{COL[color]}" stroke-width="{ancho}" stroke-linejoin="round" '
      f'stroke-linecap="round"/>')
    for x, y in (puntos[0], puntos[-1]):
        a(f'<circle cx="{x}" cy="{y}" r="4" fill="{COL[color]}"/>')


a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'font-family="Segoe UI, Arial, sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#fafafa"/>')
txt(30, 34, "CAN aislado en protoboard — ADuM1201 + B0505S + TJA1050", 22, weight="bold")
txt(30, 56, "Rieles de ARRIBA = lado ESP (GND = amarillo). Rieles de ABAJO = lado bus (GND_bus = negativo de batería). "
    "Ningún cable une arriba con abajo.", 13, fill="#444")

# ---- protoboard ----
BX0, BX1, BY0, BY1 = 330, 1190, 120, 770
R_5V, R_GND, R_5VA, R_GB = 142, 164, 718, 740
caja(BX0, BY0, BX1 - BX0, BY1 - BY0, "#f1ece2", "#b9ad97", 10)
a(f'<rect x="{BX0 + 10}" y="182" width="{BX1 - BX0 - 20}" height="238" fill="#e8f0fb" rx="6"/>')
a(f'<rect x="{BX0 + 10}" y="450" width="{BX1 - BX0 - 20}" height="240" fill="#fdeedd" rx="6"/>')
for y, c, nom in [(R_5V, "rojo", "+5 V del ESP"), (R_GND, "negro", "GND del ESP = amarillo"),
                  (R_5VA, "naranja", "+5 V AISLADO (sale del B0505S)"), (R_GB, "gris", "GND_bus = negativo de batería")]:
    a(f'<line x1="{BX0 + 20}" y1="{y}" x2="{BX1 - 20}" y2="{y}" stroke="{COL[c]}" stroke-width="3" stroke-dasharray="2 6"/>')
    txt(BX1 - 24, y - 5, nom, 11, "end", "bold", COL[c])
txt(BX0 + 22, 200, "LADO ESP", 13, "start", "bold", "#3a5f8f")
txt(BX0 + 22, 684, "LADO BUS", 13, "start", "bold", "#a8590c")
a(f'<rect x="{BX0 + 10}" y="424" width="{BX1 - BX0 - 20}" height="22" fill="#d9cfbd"/>')
a(f'<line x1="{BX0}" y1="435" x2="{BX1}" y2="435" stroke="#c0392b" stroke-width="2.5" stroke-dasharray="10 6"/>')
txt(BX0 + 50, 431, "BARRERA", 12, "start", "bold", "#c0392b")

# ---- ESP32 (afuera) ----
caja(40, 140, 200, 230, "#20242c", "#000")
txt(140, 166, "ESP32", 20, "middle", "bold", "#fff")
txt(140, 352, "(el mismo de COM6)", 11, "middle", fill="#bbb")
ESP = {"GPIO22": 190, "GPIO21": 220, "3V3": 250, "5V": 290, "GND": 320}
for n, y in ESP.items():
    a(f'<circle cx="240" cy="{y}" r="6" fill="#ffd54a" stroke="#000"/>')
    txt(228, y + 4, n, 13, "end", "bold", "#fff")

# ---- B0505S (lado ESP; su salida baja con cables al lado bus) ----
bx, by = 380, 230
caja(bx, by, 170, 64, "#2b2b2b", "#000")
txt(bx + 85, by + 26, "B0505S-1WR3", 15, "middle", "bold", "#fff")
txt(bx + 85, by + 44, "DC-DC aislado 5→5 V", 11, "middle", fill="#ccc")
txt(bx + 6, by + 59, "● = pata 1", 10, fill="#ccc")
B = {}
for i, n in enumerate(["1 GND", "2 Vin", "3 0V", "4 +Vo"]):
    x = bx + 25 + i * 40
    B[n.split()[0]] = (x, by + 82)
    a(f'<line x1="{x}" y1="{by + 64}" x2="{x}" y2="{by + 82}" stroke="#999" stroke-width="3"/>')
    a(f'<circle cx="{x}" cy="{by + 82}" r="5" fill="#ffd54a" stroke="#333"/>')
    txt(x + 7, by + 78, n.split()[0], 10, weight="bold")
# etiquetas de las patas, al costado para no tapar cables

# ---- ADuM1201 (a caballo de la barrera) ----
ax, ay, aw, ah = 700, 290, 200, 290
caja(ax, ay, aw, ah, "#1d5d34", "#0b3a1e")
txt(ax + 100, ay + 140, "ADuM1201", 17, "middle", "bold", "#fff")
txt(ax + 100, ay + 160, "(módulo CJMCU)", 11, "middle", fill="#cfe")
txt(ax + 100, ay + 178, "lado 1 arriba · lado 2 abajo", 10, "middle", fill="#cfe")
A1, A2 = {}, {}
for i, n in enumerate(["VDD1", "VOA", "VIB", "GND1"]):
    x = ax + 25 + i * 50
    A1[n] = (x, ay)
    a(f'<circle cx="{x}" cy="{ay}" r="5" fill="#ffd54a" stroke="#333"/>')
    txt(x, ay + 20, n, 11, "middle", "bold", "#fff")
for i, n in enumerate(["VDD2", "VIA", "VOB", "GND2"]):
    x = ax + 25 + i * 50
    A2[n] = (x, ay + ah)
    a(f'<circle cx="{x}" cy="{ay + ah}" r="5" fill="#ffd54a" stroke="#333"/>')
    txt(x, ay + ah - 12, n, 11, "middle", "bold", "#fff")

# ---- TJA1050 (lado bus) ----
tx, ty = 960, 560
caja(tx, ty, 190, 95, "#1b4f8a", "#0d2b4d")
txt(tx + 85, ty + 55, "TJA1050", 17, "middle", "bold", "#fff")
txt(tx + 85, ty + 73, "(el nuevo, 20/20)", 11, "middle", fill="#cde")
T = {}
for i, n in enumerate(["VCC", "TX", "RX", "GND"]):
    x = tx + 25 + i * 47
    T[n] = (x, ty)
    a(f'<circle cx="{x}" cy="{ty}" r="5" fill="#ffd54a" stroke="#333"/>')
    txt(x, ty + 20, n, 11, "middle", "bold", "#fff")
for n, y in (("CANH", ty + 35), ("CANL", ty + 70)):
    a(f'<rect x="{tx + 182}" y="{y - 8}" width="16" height="16" fill="#3a8f4a" stroke="#000"/>')
    txt(tx + 178, y + 4, n, 11, "end", "bold", "#fff")
txt(1150, 676, "CANH / CANL al aire en el banco", 11, "end", fill="#a8590c", italic=True)

# ---- cables lado ESP: las señales entran por arriba de la protoboard ----
cable([(240, ESP["GPIO22"]), (255, ESP["GPIO22"]), (255, 76), (A1["VIB"][0], 76), A1["VIB"]], "azul")
cable([(240, ESP["GPIO21"]), (268, ESP["GPIO21"]), (268, 90), (A1["VOA"][0], 90), A1["VOA"]], "verde")
cable([(240, ESP["3V3"]), (281, ESP["3V3"]), (281, 104), (A1["VDD1"][0], 104), A1["VDD1"]], "morado")
cable([(240, ESP["5V"]), (300, ESP["5V"]), (300, R_5V), (345, R_5V)], "rojo")
cable([(240, ESP["GND"]), (312, ESP["GND"]), (312, R_GND), (345, R_GND)], "negro")
cable([B["1"], (B["1"][0], by + 92), (365, by + 92), (365, R_GND)], "negro", 3)
cable([B["2"], (B["2"][0], by + 104), (352, by + 104), (352, R_5V)], "rojo", 3)
cable([A1["GND1"], (A1["GND1"][0], R_GND)], "negro", 3)

# ---- cables lado bus ----
cable([B["3"], (B["3"][0], R_GB)], "gris", 3)
cable([B["4"], (B["4"][0], R_5VA)], "naranja", 3)
cable([A2["VDD2"], (A2["VDD2"][0], R_5VA)], "naranja", 3)
cable([A2["GND2"], (A2["GND2"][0], R_GB)], "gris", 3)
cable([T["VCC"], (T["VCC"][0], 548), (945, 548), (945, R_5VA)], "naranja", 3)
cable([T["GND"], (T["GND"][0], 545), (1172, 545), (1172, R_GB)], "gris", 3)
cable([A2["VOB"], (A2["VOB"][0], 600), (900, 600), (900, 532), (T["TX"][0], 532), T["TX"]], "azul")
cable([A2["VIA"], (A2["VIA"][0], 625), (915, 625), (915, 518), (T["RX"][0], 518), T["RX"]], "verde")

# ---- leyenda y reglas ----
ly = 800
txt(30, ly, "Cables:", 13, weight="bold")
x = 95
for c, n in [("rojo", "+5 V ESP"), ("negro", "GND ESP (amarillo)"), ("morado", "3V3 ESP → VDD1"), ("azul", "TX"),
             ("verde", "RX"), ("naranja", "+5 V aislado"), ("gris", "GND_bus")]:
    a(f'<line x1="{x}" y1="{ly - 4}" x2="{x + 26}" y2="{ly - 4}" stroke="{COL[c]}" stroke-width="5"/>')
    txt(x + 32, ly, n, 12)
    x += 32 + len(n) * 6.6 + 22
txt(30, ly + 24, "• VDD1 a 3V3, NUNCA a 5 V: VOA sale al GPIO21 con lo que haya en VDD1.   "
    "• TX: GPIO22 → VIB → VOB → TX.   • RX: RX → VIA → VOA → GPIO21.   • B0505S: 1 GND · 2 Vin · 3 0V · 4 +Vo.", 12)
txt(30, ly + 44, "• En el montacargas (no hoy): CANH → DB9 8, CANL → DB9 3, GND_bus → negativo de batería "
    "(ficha del multipiloto, pin 7). El GND del ESP nunca va ahí.", 12)
txt(30, ly + 64, "• Si el ADuM no entra a caballo del canal, ponelo donde quepa: cuentan las conexiones, "
    "y que nada del lado 2 toque un riel de arriba. La barrera solo la cruzan el B0505S y el ADuM1201.", 12)
a("</svg>")

Path(__file__).with_name("protoboard_aislado.svg").write_text("\n".join(o), encoding="utf-8")
print("protoboard_aislado.svg escrito")
