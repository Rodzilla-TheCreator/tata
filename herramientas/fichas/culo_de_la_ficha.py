"""El culo del ETR 335d sacado de los VECTORES de la hoja VDI (pág. 2), no de una imagen.

La vista de arriba de jungheinrich_etr_hoja_tecnica.pdf está dibujada en vectores y A ESCALA:
el ancho del chasis b2 (1,054) y el radio de giro Wa (1,801) dan la misma escala con 0.1 %.
Este script saca las tres curvas Bézier del contorno del culo, las pasa a metros con el centro
del eje de carga como origen, y escribe culo_ficha.csv (a desde el culo, y).

    pip install pymupdf
    python herramientas/fichas/culo_de_la_ficha.py           # imprime y escribe el .csv
    python herramientas/fichas/culo_de_la_ficha.py --ancho   # + ancho a rumbo con los 2.91 (usa analisis/)

Control: si las coordenadas del PDF cambian (otra versión de la hoja), las aserciones fallan.
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(AQUI, 'jungheinrich_etr_hoja_tecnica.pdf')

WA, B2 = 1.801, 1.054                     # ficha VDI 4.35 y 4.21
CENTRO = (177.06, 372.864)                # pt: centro del eje de carga (origen de la cota Wa)
CULO_X = 102.407                          # pt: punto del culo sobre el eje (= línea de a/2)
EXT_B2 = (351.04, 394.69)                 # pt: líneas de cota de b2


def curvas():
    """Las tres Bézier del contorno del culo (camino 1118 de la pág. 2): esquina, cara, esquina."""
    import pymupdf
    pag = pymupdf.open(PDF)[1]
    out = []
    for g in pag.get_drawings():
        for it in g['items']:
            if it[0] != 'c':
                continue
            q = [(v.x, v.y) for v in it[1:5]]
            xs, ys = [v[0] for v in q], [v[1] for v in q]
            if min(xs) < 111 and max(xs) < 111 and 350 < min(ys) and max(ys) < 395 and \
                    abs(q[0][1] - q[3][1]) > 4 and min(xs) > 101:
                out.append(q)
    out = sorted({tuple(c) for c in out}, key=lambda c: c[0][1])
    caras = [c for c in out if abs(c[0][0] - 104.436) < 0.01 or abs(c[3][0] - 104.436) < 0.01]
    assert len(caras) == 3, f'esperaba 3 curvas del culo, hay {len(caras)}: ¿cambió el PDF?'
    return caras


def contorno(n=200):
    k = WA / (CENTRO[0] - CULO_X)                                  # m/pt por Wa
    k2 = B2 / (EXT_B2[1] - EXT_B2[0])                              # m/pt por b2
    assert abs(k / k2 - 1) < 0.005, f'escala Wa {k * 1000:.2f} vs b2 {k2 * 1000:.2f} mm/pt'
    pts = []
    for c in curvas():
        P = [np.array(v) for v in c]
        for t in np.linspace(0, 1, n):
            q = (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]
            pts.append(((q[0] - CENTRO[0]) * k, (CENTRO[1] - q[1]) * k))
    return np.array(pts), k


def main():
    c, k = contorno()
    r = np.hypot(c[:, 0], c[:, 1])
    print(f'escala {k * 1000:.3f} mm/pt (por b2: {B2 / (EXT_B2[1] - EXT_B2[0]) * 1000:.3f})')
    print(f'culo sobre el eje: {-c[:, 0].min():.3f} m del eje de carga   (Wa ficha {WA})')
    print(f'distancia máxima del culo al eje de carga: {r.max():.3f} m, en y = {c[r.argmax(), 1]:+.3f}')
    print(f'semiancho del culo en el dibujo: {c[:, 1].max():.3f} m  (b2/2 = {B2 / 2:.3f})')
    s = c[np.abs(c[:, 1]) < 0.40]
    A = np.c_[2 * s[:, 0], 2 * s[:, 1], np.ones(len(s))]
    cx, cy, cc = np.linalg.lstsq(A, (s ** 2).sum(1), rcond=None)[0]
    print(f'cara del culo: arco de R = {math.sqrt(cc + cx ** 2 + cy ** 2):.3f} m, centro {cx:+.3f} m del eje de carga')
    a0 = c[:, 0].min()
    print('retiro del contorno respecto del punto del eje:')
    for yy in (0.2, 0.3, 0.4, 0.45, 0.5, 0.52):
        m = c[c[:, 0] < a0 + 0.3]
        j = np.argmin(np.abs(m[:, 1] - yy))
        print(f'   y = {yy:.2f}  →  {(m[j, 0] - a0) * 1000:5.0f} mm')
    rel = np.c_[c[:, 0] - a0, c[:, 1]]
    np.savetxt(os.path.join(AQUI, 'culo_ficha.csv'), rel, delimiter=',', fmt='%.5f',
               header='a_desde_culo_m,y_m  (ETR 335d, hoja VDI pag. 2, vectores; ver culo_de_la_ficha.py)')
    if '--ancho' in sys.argv:
        ancho(rel)


def ancho(rel):
    """Ancho a rumbo máximo con la silueta v3 de analisis/planificador_rutas.py (2.91 de culo a punta,
    capó 1.065) cambiando SOLO el culo por el de la ficha (escalado en y al capó medido)."""
    sys.path.insert(0, os.path.join(AQUI, '..', '..', 'analisis'))
    import planificador_rutas as P
    X, hc = P.XPIV_V3, P.W_CAPO / 2
    ey = hc / rel[:, 1].max()
    for cargado in (False, True):
        s, _ = P.silueta(X, cargado=cargado, paso=0.005, lch=P.LCH_V3, r_culo=0.0)
        s = s[~((s[:, 0] < -X + 0.20) & (np.abs(s[:, 1]) <= hc + 1e-6))]
        lados = [(a, sg * hc) for a in np.arange(rel[:, 0].max() - X, -X + 0.20, 0.005) for sg in (1, -1)]
        s = np.vstack([s, np.c_[rel[:, 0] - X, rel[:, 1] * ey], lados])
        mx = max((P.ancho_a_rumbo(s, math.radians(q / 4)), q / 4) for q in range(361))
        print(f'ancho a rumbo máximo, {"cargado" if cargado else "vacío  "}: {mx[0]:.3f} m a {mx[1]:.1f}°')


if __name__ == '__main__':
    main()
