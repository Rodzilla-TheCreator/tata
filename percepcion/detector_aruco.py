#!/usr/bin/env python3
"""
detector_aruco.py — detecta marcas ArUco con una webcam y mide la pose, EN VIVO.

Es el par de campo de analisis/aruco_precision.py: ese da la TEORIA (que precision
deberia dar una marca a tal distancia); esto mide lo REAL. Corre en maquinon (o
cualquier PC con camara). NO necesita el montacargas.

Que mide, por marca detectada:
  - distancia (profundidad hacia la marca, en metros)
  - corrimiento lateral (en metros)
  - yaw aproximado (grados)
  - error de reproyeccion (px) = indicador de calidad de la deteccion

Uso:
    python detector_aruco.py --marca 0.15            # marca de 15 cm, camara 0
    python detector_aruco.py --camara 1 --fov 70     # otra camara, FOV horizontal 70 deg
    python detector_aruco.py --calib calib.npz       # con calibracion real (recomendado)
    python detector_aruco.py --log corrida.csv       # guarda cada deteccion a CSV

Teclas (en la ventana):  q = salir   ·   s = guardar cuadro PNG

Calibracion: sin --calib se SINTETIZAN los intrinsecos desde --fov (aproximado:
sirve para ver que detecta, el rango y el yaw; para precision de verdad hay que
calibrar con un tablero de ajedrez y pasar el .npz). Ver LEEME.md.

Requiere:  pip install opencv-contrib-python numpy   (OpenCV >= 4.7)
"""
import argparse
import sys
import time

import numpy as np
import cv2

DICCIONARIOS = {
    "4x4_50": cv2.aruco.DICT_4X4_50, "4x4_100": cv2.aruco.DICT_4X4_100,
    "5x5_100": cv2.aruco.DICT_5X5_100, "6x6_250": cv2.aruco.DICT_6X6_250,
    "apriltag_36h11": cv2.aruco.DICT_APRILTAG_36h11,
}


def intrinsecos_desde_fov(w, h, fov_deg):
    """Matriz de camara aproximada a partir del FOV horizontal. Sin distorsion."""
    f = (w / 2.0) / np.tan(np.radians(fov_deg) / 2.0)
    K = np.array([[f, 0, w / 2.0], [0, f, h / 2.0], [0, 0, 1]], float)
    return K, np.zeros(5)


def cargar_calib(path):
    d = np.load(path)
    return d["camera_matrix"].astype(float), d["dist_coeffs"].astype(float).ravel()


def obj_points(lado):
    """Esquinas de la marca en su propio marco, en el orden de ArUco (TL, TR, BR, BL)."""
    h = lado / 2.0
    return np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)


def main():
    ap = argparse.ArgumentParser(description="Detector ArUco en vivo (TaTa)")
    ap.add_argument("--camara", default="0", help="indice (0,1,...) o ruta del dispositivo")
    ap.add_argument("--marca", type=float, default=0.15, help="lado de la marca, en metros")
    ap.add_argument("--diccionario", default="4x4_50", choices=list(DICCIONARIOS))
    ap.add_argument("--fov", type=float, default=70.0, help="FOV horizontal en grados (si no hay --calib)")
    ap.add_argument("--calib", default=None, help=".npz con camera_matrix y dist_coeffs")
    ap.add_argument("--log", default=None, help="ruta de un CSV donde guardar cada deteccion")
    a = ap.parse_args()

    if not hasattr(cv2.aruco, "ArucoDetector"):
        sys.exit("Esta OpenCV es vieja (<4.7). Instala: pip install -U opencv-contrib-python")

    cam = int(a.camara) if a.camara.isdigit() else a.camara
    cap = cv2.VideoCapture(cam)
    if not cap.isOpened():
        sys.exit(f"No pude abrir la camara {a.camara}")
    ok, frame = cap.read()
    if not ok:
        sys.exit("La camara no entrega cuadros")
    h, w = frame.shape[:2]

    if a.calib:
        K, dist = cargar_calib(a.calib)
        fuente = f"calib {a.calib}"
    else:
        K, dist = intrinsecos_desde_fov(w, h, a.fov)
        fuente = f"FOV {a.fov:.0f} (sintetico)"

    adict = cv2.aruco.getPredefinedDictionary(DICCIONARIOS[a.diccionario])
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    det = cv2.aruco.ArucoDetector(adict, params)
    objp = obj_points(a.marca)

    logf = open(a.log, "w") if a.log else None
    if logf:
        logf.write("t,id,dist_m,lateral_m,yaw_deg,reproj_px\n")

    print(f"Camara {a.camara}  {w}x{h} · marca {a.marca * 100:.0f} cm · {a.diccionario} · {fuente}")
    print("q = salir · s = guardar cuadro")
    t0 = time.time()
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = det.detectMarkers(gray)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            for c, i in zip(corners, ids.ravel()):
                img = c.reshape(4, 2).astype(float)
                ok2, rvec, tvec = cv2.solvePnP(objp, img, K, dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                if not ok2:
                    continue
                proy, _ = cv2.projectPoints(objp, rvec, tvec, K, dist)
                reproj = float(np.mean(np.linalg.norm(proy.reshape(4, 2) - img, axis=1)))
                x, _y, z = tvec.ravel()
                dist_m = float(z)          # profundidad hacia la marca
                lateral = float(x)         # corrimiento lateral (+ a la derecha)
                R, _ = cv2.Rodrigues(rvec)
                yaw = float(np.degrees(np.arctan2(-R[2, 0], np.hypot(R[2, 1], R[2, 2]))))
                cv2.drawFrameAxes(frame, K, dist, rvec, tvec, a.marca * 0.6)
                px = img[0].astype(int)
                cv2.putText(frame, f"id{i} {dist_m:.2f}m lat{lateral:+.2f} yaw{yaw:+.0f} e{reproj:.1f}px",
                            (px[0], px[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                if logf:
                    logf.write(f"{time.time() - t0:.3f},{i},{dist_m:.4f},{lateral:.4f},{yaw:.2f},{reproj:.2f}\n")
        n += 1
        fps = n / (time.time() - t0 + 1e-9)
        cv2.putText(frame, f"{fuente} · {fps:.0f} fps · q sale", (10, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        cv2.imshow("detector ArUco — TaTa", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        if k == ord('s'):
            nombre = f"aruco_{int(time.time())}.png"
            cv2.imwrite(nombre, frame)
            print("cuadro guardado:", nombre)

    cap.release()
    cv2.destroyAllWindows()
    if logf:
        logf.close()


if __name__ == "__main__":
    main()
