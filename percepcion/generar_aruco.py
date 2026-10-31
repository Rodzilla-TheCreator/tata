#!/usr/bin/env python3
"""
generar_aruco.py — genera marcas ArUco imprimibles, en NEGRO, con ID y tamaño rotulados.

Las marcas del RoboMaster S1 NO son ArUco (son de visión propietarias de DJI): el
detector de OpenCV no las lee. Esto genera las de verdad, del MISMO diccionario que
usa detector_aruco.py, con ID conocido — necesario para mapear cada marca a una
ubicación del rack.

Uso:
    python generar_aruco.py --ids 0-7 --lado-cm 15
    python generar_aruco.py --diccionario 5x5_100 --ids 0,1,2,10 --lado-cm 20
    python generar_aruco.py --ids 0-5 --hoja              # además una hoja de contacto

Cada marca sale como PNG con zona blanca alrededor (imprescindible) y un rótulo
con ID, diccionario y tamaño. Imprimí "a tamaño real" (100 %, sin ajustar a página).
**Medí con regla el lado negro después de imprimir y usá ESE número en**
`detector_aruco.py --marca`. La precisión de pose depende de que ese número sea exacto.

Requiere:  pip install opencv-contrib-python numpy   (Pillow opcional, para fijar DPI)
"""
import argparse
import os
import sys

import numpy as np
import cv2

DICCIONARIOS = {
    "4x4_50": cv2.aruco.DICT_4X4_50, "4x4_100": cv2.aruco.DICT_4X4_100,
    "5x5_100": cv2.aruco.DICT_5X5_100, "6x6_250": cv2.aruco.DICT_6X6_250,
    "apriltag_36h11": cv2.aruco.DICT_APRILTAG_36h11,
}


def parse_ids(s):
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if "-" in tok:
            a, b = tok.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(tok))
    return out


def guardar(path, img, dpi):
    """Guarda PNG; fija el DPI con Pillow si está, para imprimir a tamaño real."""
    try:
        from PIL import Image
        Image.fromarray(img).save(path, dpi=(dpi, dpi))
    except Exception:
        cv2.imwrite(path, img)


def hacer_marca(adict, mid, lado_px, dict_name, lado_cm):
    img = cv2.aruco.generateImageMarker(adict, mid, lado_px)   # negro/blanco, borde negro incluido
    grid = adict.markerSize + 2
    celda = max(1, lado_px // grid)
    qz = max(celda, int(0.1 * lado_px))                        # zona blanca >= 1 celda
    lab = int(0.12 * lado_px)                                  # franja del rótulo
    canvas = np.full((lado_px + 2 * qz + lab, lado_px + 2 * qz), 255, np.uint8)
    canvas[qz:qz + lado_px, qz:qz + lado_px] = img
    txt = f"ID {mid}  ·  {dict_name}  ·  {lado_cm:g} cm"
    fs = max(0.4, lado_px / 900.0)
    cv2.putText(canvas, txt, (qz, lado_px + 2 * qz + int(lab * 0.7)),
                cv2.FONT_HERSHEY_SIMPLEX, fs, 0, max(1, int(fs * 2)), cv2.LINE_AA)
    return canvas


def main():
    ap = argparse.ArgumentParser(description="Genera marcas ArUco imprimibles (TaTa)")
    ap.add_argument("--diccionario", default="4x4_50", choices=list(DICCIONARIOS))
    ap.add_argument("--ids", default="0-7", help="ej. '0-7' o '0,1,2,10'")
    ap.add_argument("--lado-cm", type=float, default=15.0, help="lado del cuadro negro, en cm")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--out", default="marcas", help="carpeta de salida")
    ap.add_argument("--hoja", action="store_true", help="además una hoja de contacto con todas")
    a = ap.parse_args()

    if not hasattr(cv2.aruco, "generateImageMarker"):
        sys.exit("OpenCV vieja (<4.7). Instala: pip install -U opencv-contrib-python")

    adict = cv2.aruco.getPredefinedDictionary(DICCIONARIOS[a.diccionario])
    ids = parse_ids(a.ids)
    maxid = adict.bytesList.shape[0]
    malos = [i for i in ids if i < 0 or i >= maxid]
    if malos:
        sys.exit(f"IDs fuera de rango para {a.diccionario} (0..{maxid - 1}): {malos}")

    os.makedirs(a.out, exist_ok=True)
    lado_px = int(round(a.lado_cm / 2.54 * a.dpi))
    hechas = []
    for mid in ids:
        img = hacer_marca(adict, mid, lado_px, a.diccionario, a.lado_cm)
        path = os.path.join(a.out, f"marca_{a.diccionario}_{mid:02d}.png")
        guardar(path, img, a.dpi)
        hechas.append(img)
        print("escrita:", path)

    if a.hoja and hechas:
        cols = min(4, len(hechas))
        filas = (len(hechas) + cols - 1) // cols
        hmax = max(h.shape[0] for h in hechas)
        wmax = max(h.shape[1] for h in hechas)
        g = 20
        hoja = np.full((filas * (hmax + g) + g, cols * (wmax + g) + g), 255, np.uint8)
        for k, img in enumerate(hechas):
            r, c = divmod(k, cols)
            y, x = g + r * (hmax + g), g + c * (wmax + g)
            hoja[y:y + img.shape[0], x:x + img.shape[1]] = img
        path = os.path.join(a.out, f"hoja_{a.diccionario}.png")
        guardar(path, hoja, a.dpi)
        print("escrita:", path)

    print(f"\n{len(ids)} marca(s) · {a.diccionario} · {a.lado_cm:g} cm @ {a.dpi} dpi")
    print("Imprimí al 100% (sin ajustar a página). Medí el lado negro con regla y usá")
    print("ese número exacto en:  detector_aruco.py --marca <metros>")


if __name__ == "__main__":
    main()
