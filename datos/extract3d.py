import json, math
import ezdxf
from ezdxf import bbox

doc = ezdxf.readfile("plano.dxf")
msp = doc.modelspace()

# Region of interest: the warehouse (RETHINK nave + naves L4 + bodegas)
X0, X1, Y0, Y1 = 706.0, 945.0, -848.0, -756.0

def inside(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

# ---------- 1. Maxicubos ----------
cubes = []
for e in msp.query("INSERT"):
    if e.dxf.name != "MAXICUBO":
        continue
    b = bbox.extents([e], fast=False)
    cx = (b.extmin.x + b.extmax.x) / 2
    cy = (b.extmin.y + b.extmax.y) / 2
    if not inside(cx, cy):
        continue
    cubes.append({
        "x": round(cx, 3), "y": round(cy, 3),
        "w": round(b.size.x, 3), "d": round(b.size.y, 3),
        "rot": round(float(getattr(e.dxf, "rotation", 0.0)) % 360, 1),
    })
print("maxicubos:", len(cubes))

# ---------- 2. Rack level labels ----------
levels = []
for e in msp:
    if e.dxftype() == "TEXT":
        t, p = e.dxf.text, e.dxf.insert
    elif e.dxftype() == "MTEXT":
        t, p = e.text, e.dxf.insert
    else:
        continue
    tu = t.upper()
    if "RACK" in tu and "NIVEL" in tu:
        n = 5 if " 5 " in tu else (4 if " 4 " in tu else 4)
        levels.append({"x": round(p.x, 2), "y": round(p.y, 2), "n": n, "txt": t.strip()})
print("etiquetas de nivel:", len(levels))

# ---------- 3. Group maxicubos into rack rows (rows run along X) ----------
cubes.sort(key=lambda c: (round(c["y"], 1), c["x"]))
rows = []
for c in cubes:
    placed = False
    for r in rows:
        if abs(r["y"] - c["y"]) < 0.45 and any(abs(c["x"] - xx) < 3.0 for xx in r["xs"][-4:]):
            r["xs"].append(c["x"]); r["n"] += 1
            r["y"] = (r["y"] * (r["n"] - 1) + c["y"]) / r["n"]
            r["x0"] = min(r["x0"], c["x"] - c["w"] / 2)
            r["x1"] = max(r["x1"], c["x"] + c["w"] / 2)
            r["w"] = c["w"]; r["d"] = c["d"]
            placed = True
            break
    if not placed:
        rows.append({"y": c["y"], "xs": [c["x"]], "n": 1,
                     "x0": c["x"] - c["w"] / 2, "x1": c["x"] + c["w"] / 2,
                     "w": c["w"], "d": c["d"], "rot": c["rot"]})

racks = []
for r in rows:
    if r["n"] < 3:
        continue
    # nearest level label
    best, bd = 4, 1e9
    for L in levels:
        d = math.hypot(L["x"] - (r["x0"] + r["x1"]) / 2, L["y"] - r["y"])
        if d < bd:
            bd, best = d, L["n"]
    racks.append({
        "x0": round(r["x0"], 2), "x1": round(r["x1"], 2), "y": round(r["y"], 2),
        "bays": r["n"], "cw": round(r["w"], 2), "cd": round(r["d"], 2),
        "levels": best,
    })
racks.sort(key=lambda r: (-r["y"], r["x0"]))
print("filas de rack:", len(racks), "| posiciones piso:", sum(r["bays"] for r in racks))
for r in racks:
    print(f"   y={r['y']:8.2f}  x {r['x0']:7.2f}->{r['x1']:7.2f}  largo {r['x1']-r['x0']:6.2f} m  bays={r['bays']:3d}  niveles={r['levels']}")

# ---------- 4. Vehicles ----------
veh = []
for e in msp.query("INSERT"):
    n = e.dxf.name
    kind = None
    if n == "A$C79796889":
        kind, L, W = "montacargas", 2.44, 0.79
    elif "paleteira" in n.lower():
        kind, L, W = "paleteira", 1.62, 0.88
    if not kind:
        continue
    x, y = e.dxf.insert.x, e.dxf.insert.y
    if not inside(x, y):
        continue
    veh.append({"kind": kind, "x": round(x, 2), "y": round(y, 2),
                "rot": round(float(getattr(e.dxf, "rotation", 0.0)) % 360, 1),
                "L": L, "W": W})
print("vehiculos:", len(veh))

# ---------- 5. Columns ----------
cols = []
for e in msp.query("INSERT"):
    if e.dxf.name.lower() in ("col", "col-2", "columna"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if inside(x, y):
            cols.append({"x": round(x, 2), "y": round(y, 2)})
print("columnas:", len(cols))

# ---------- 6. Zone labels ----------
zones = []
for e in msp:
    if e.dxftype() == "TEXT":
        t, p, h = e.dxf.text, e.dxf.insert, e.dxf.height
    elif e.dxftype() == "MTEXT":
        t, p, h = e.text, e.dxf.insert, e.dxf.char_height
    else:
        continue
    t = " ".join(t.replace("\n", " ").split())
    if not t or not inside(p.x, p.y):
        continue
    tu = t.upper().replace(" ", "")
    KEY = ["BODEGA", "BOBEGA", "MAXICUBO", "EMPAQUE", "LAVADO", "SHOWROOM", "LABORATORIO",
           "ACCESOPRINCIPAL", "AMPLIACION", "CARGADEMONTACARGAS", "MANTENIMIENTO",
           "PLANTA", "TALLER", "COMEDOR", "OFICINA", "MAQUISUPRO", "RAMPA", "DESPACHO"]
    if "RACK" in tu and "NIVEL" in tu:
        continue
    if any(k in tu for k in KEY) and len(t) > 3 and not t.replace(".", "").isdigit():
        zones.append({"x": round(p.x, 2), "y": round(p.y, 2), "t": t[:42], "h": round(float(h), 2)})
# dedupe by proximity+text
ded = []
for z in zones:
    if not any(z["t"] == o["t"] and abs(z["x"] - o["x"]) < 4 and abs(z["y"] - o["y"]) < 4 for o in ded):
        ded.append(z)
zones = ded
print("etiquetas de zona:", len(zones))

# ---------- 7. Walls ----------
WALL_LAYERS = {"PAREDES", "A-WALL", "A-WALLM", "PROY", "PTA"}
walls = []
def add_seg(ax, ay, bx, by):
    if not (inside(ax, ay) or inside(bx, by)):
        return
    L = math.hypot(bx - ax, by - ay)
    if L < 0.45 or L > 90:
        return
    walls.append([round(ax, 2), round(ay, 2), round(bx, 2), round(by, 2)])

for e in msp:
    if e.dxf.layer.upper() not in WALL_LAYERS:
        continue
    if e.dxftype() == "LINE":
        s, t = e.dxf.start, e.dxf.end
        add_seg(s.x, s.y, t.x, t.y)
    elif e.dxftype() == "LWPOLYLINE":
        pts = [(p[0], p[1]) for p in e.get_points()]
        if e.closed and len(pts) > 2:
            pts.append(pts[0])
        for i in range(len(pts) - 1):
            add_seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
print("segmentos de muro:", len(walls))

# ---------- 8. Sectores: el DWG trae tres propuestas lado a lado ----------
SECTORES = [
    {"id": "A", "nom": "Actual", "titulo": "LAYOUT RETHINK · 1er nivel (nov-2024)",
     "x0": 706.0, "x1": 775.0, "color": "#58a6ff",
     "desc": "Cómo opera hoy la nave RETHINK"},
    {"id": "B", "nom": "Ampliación", "titulo": "AMPLIACIÓN RETHINK · naves L4-A/B/C",
     "x0": 775.0, "x1": 838.0, "color": "#d29922",
     "desc": "Ampliación proyectada de 1,736.64 m²"},
    {"id": "C", "nom": "Propuesta IT", "titulo": "LAYOUT PROPUESTA IT · planta primer nivel",
     "x0": 838.0, "x1": 945.0, "color": "#3fb950",
     "desc": "Bodega sin racks diseñados — aquí va la propuesta TaTa"},
]
def sector_de(x):
    for s in SECTORES:
        if s["x0"] <= x < s["x1"]:
            return s["id"]
    return "C"
for r in racks:
    r["sec"] = sector_de((r["x0"] + r["x1"]) / 2)
from collections import Counter
print("racks por sector:", dict(Counter(r["sec"] for r in racks)))

# ---------- 9. Propuesta TaTa ----------
# Las salas salen de un análisis de espacio libre sobre los muros reales del DWG:
# hay un muro divisorio en x≈868.4 que parte la bodega del sector IT en dos naves,
# y el muro norte está en y=-788.0. La propuesta se genera en el visor, viva,
# a partir de estos rectángulos y de los parámetros que el usuario mueva.
SALAS = [
    {"nom": "Nave este",  "x0": 869.0,  "y0": -815.0, "x1": 896.5, "y1": -788.75},
    {"nom": "Nave oeste", "x0": 844.75, "y0": -808.75, "x1": 868.0, "y1": -788.75},
]
for r in SALAS:
    r["area"] = round((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]), 1)
    print(f'  sala {r["nom"]}: {r["x1"]-r["x0"]:.1f} x {r["y1"]-r["y0"]:.1f} m = {r["area"]} m2')

PROP = {
    "salas": SALAS,
    "pasillo_min": 4.50,   # Ast 3.82 del KBE 20 + margen de operación
    "margen": 1.50,        # holgura contra muros
    "flue": 0.32,          # espalda con espalda
    "depth": 1.00, "bay": 1.20, "niveles": 5,
}

out = {
    "bounds": {"x0": X0, "x1": X1, "y0": Y0, "y1": Y1},
    "sectores": SECTORES,
    "propuesta": PROP,
    "racks": racks, "vehicles": veh, "columns": cols, "zones": zones, "walls": walls,
    "cube": {"w": 1.2, "d": 1.0, "h": 1.16},
    "stats": {
        "posiciones_piso": sum(r["bays"] for r in racks),
        "posiciones_totales": sum(r["bays"] * r["levels"] for r in racks),
        "filas": len(racks),
        "montacargas": sum(1 for v in veh if v["kind"] == "montacargas"),
        "paleteiras": sum(1 for v in veh if v["kind"] == "paleteira"),
    },
}
json.dump(out, open("almacen3d.json", "w"), ensure_ascii=False)
print()
print("STATS:", json.dumps(out["stats"], ensure_ascii=False))
