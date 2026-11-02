#!/usr/bin/env python3
"""
calibrar_camara.py — calibra la webcam con el tablero de ajedrez y guarda el .npz que usa
detector_aruco.py --calib.

Tablero: percepcion/marcas/tablero_9x6_22mm_carta.pdf (10 x 7 cuadros de 22 mm → 9 x 6 esquinas
interiores). Imprimir al 100 %, MEDIR un cuadro con regla y pasar lo medido en --cuadro-mm.
Pegarlo PLANO sobre cartón duro: un tablero curvo calibra mal.

Uso:
    python calibrar_camara.py                         # webcam 0, en vivo
    python calibrar_camara.py --camara 1 --cuadro-mm 21.9
    python calibrar_camara.py --carpeta fotos/        # con fotos ya tomadas
    python calibrar_camara.py --generar-tablero       # vuelve a hacer el PDF

En vivo: ESPACIO captura cuando el tablero sale detectado (esquinas de colores); C calibra
(con 15 o más capturas); Q sale. Variá la pose: cerca y lejos, inclinado a los cuatro lados,
en las esquinas de la imagen. Todas de frente y a la misma distancia calibran mal.

Calidad: el error RMS de reproyección debería quedar < 0.5 px. Arriba de 1 px, repetir.
"""
import argparse
import glob
import os
import sys

import numpy as np
import cv2

ESQ = (9, 6)            # esquinas interiores (columnas, filas)


def generar_tablero(path, cuadro_mm=22.0, dpi=300):
    """PDF carta vertical: 7 x 10 cuadros (9 x 6 esquinas interiores, rotado), con regla de 10 cm."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = int(8.5 * dpi), int(11 * dpi)
    c = cuadro_mm / 25.4 * dpi
    nx, ny = ESQ[1] + 1, ESQ[0] + 1          # vertical: 7 de ancho x 10 de alto
    tw, th = nx * c, ny * c
    x0, y0 = (W - tw) / 2, int(0.75 * dpi)
    pag = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(pag)
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2 == 0:
                d.rectangle([round(x0 + i * c), round(y0 + j * c),
                             round(x0 + (i + 1) * c) - 1, round(y0 + (j + 1) * c) - 1], fill=0)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", int(0.13 * dpi))
    except OSError:
        f = ImageFont.load_default()
    d.text((W // 2, int(0.45 * dpi)), f"Tablero de calibración · 9 x 6 esquinas · cuadro {cuadro_mm:g} mm · TaTa",
           fill=0, font=f, anchor="mm")
    reg = round(10 / 2.54 * dpi); ry = int(y0 + th + 0.45 * dpi); rx = (W - reg) // 2
    d.line([(rx, ry), (rx + reg, ry)], fill=0, width=6)
    for k in range(11):
        xx = rx + round(k * reg / 10); hh = int(0.12 * dpi) if k % 5 == 0 else int(0.06 * dpi)
        d.line([(xx, ry - hh), (xx, ry)], fill=0, width=4)
    d.text((W // 2, ry + int(0.3 * dpi)),
           "regla de 10 cm · imprimir al 100 % · medir un cuadro y pasarlo en --cuadro-mm",
           fill=0, font=f, anchor="mm")
    pag.save(path, "PDF", resolution=dpi)
    print("escrito:", path)


def puntos_objeto(cuadro_m):
    objp = np.zeros((ESQ[0] * ESQ[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:ESQ[0], 0:ESQ[1]].T.reshape(-1, 2) * cuadro_m
    return objp


def buscar(gris):
    ok, esq = cv2.findChessboardCorners(gris, ESQ, cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE)
    if not ok:
        return None
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
    return cv2.cornerSubPix(gris, esq, (11, 11), (-1, -1), crit)


def calibrar(lista_esq, tam, cuadro_m, salida):
    objp = puntos_objeto(cuadro_m)
    rms, K, dist, _, _ = cv2.calibrateCamera([objp] * len(lista_esq), lista_esq, tam, None, None)
    np.savez(salida, camera_matrix=K, dist_coeffs=dist, rms=rms, image_size=np.array(tam))
    fov = 2 * np.degrees(np.arctan(tam[0] / (2 * K[0, 0])))
    print(f"\n{len(lista_esq)} vistas · RMS {rms:.3f} px  ({'bien' if rms < 0.5 else 'aceptable' if rms < 1 else 'MALO: repetir'})")
    print(f"fx {K[0,0]:.1f}  fy {K[1,1]:.1f}  cx {K[0,2]:.1f}  cy {K[1,2]:.1f}  · FOV horizontal {fov:.1f}°")
    print(f"guardado: {salida}   →   python detector_aruco.py --calib {salida}")
    return rms, K, dist


def main():
    ap = argparse.ArgumentParser(description="Calibra la webcam con el tablero de ajedrez (TaTa)")
    ap.add_argument("--camara", default="0")
    ap.add_argument("--cuadro-mm", type=float, default=22.0, help="lado del cuadro MEDIDO, en mm")
    ap.add_argument("--carpeta", default=None, help="calibrar con fotos (.jpg/.png) en vez de en vivo")
    ap.add_argument("--salida", default="calib.npz")
    ap.add_argument("--minimo", type=int, default=15)
    ap.add_argument("--generar-tablero", action="store_true")
    a = ap.parse_args()
    cuadro_m = a.cuadro_mm / 1000.0

    if a.generar_tablero:
        os.makedirs("marcas", exist_ok=True)
        generar_tablero(os.path.join("marcas", f"tablero_9x6_{a.cuadro_mm:g}mm_carta.pdf"), a.cuadro_mm)
        return

    if a.carpeta:
        lista, tam = [], None
        for f in sorted(glob.glob(os.path.join(a.carpeta, "*.jpg")) + glob.glob(os.path.join(a.carpeta, "*.png"))):
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            e = buscar(g)
            print(f"{os.path.basename(f)}: {'tablero' if e is not None else 'NO encontrado'}")
            if e is not None:
                lista.append(e); tam = g.shape[::-1]
        if len(lista) < a.minimo:
            sys.exit(f"solo {len(lista)} vistas útiles; hacen falta {a.minimo}")
        calibrar(lista, tam, cuadro_m, a.salida)
        return

    cam = cv2.VideoCapture(int(a.camara) if a.camara.isdigit() else a.camara)
    if not cam.isOpened():
        sys.exit("no se pudo abrir la cámara")
    lista = []
    while True:
        ok, frame = cam.read()
        if not ok:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        e = buscar(g)
        vista = frame.copy()
        if e is not None:
            cv2.drawChessboardCorners(vista, ESQ, e, True)
        cv2.putText(vista, f"capturas {len(lista)}/{a.minimo}  ESPACIO captura · C calibra · Q sale",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow("calibrar", vista)
        k = cv2.waitKey(1) & 0xFF
        if k == ord(" ") and e is not None:
            lista.append(e); print(f"captura {len(lista)}")
        elif k in (ord("c"), ord("C")):
            if len(lista) < a.minimo:
                print(f"faltan capturas: {len(lista)}/{a.minimo}")
            else:
                calibrar(lista, g.shape[::-1], cuadro_m, a.salida)
                break
        elif k in (ord("q"), ord("Q")):
            break
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
