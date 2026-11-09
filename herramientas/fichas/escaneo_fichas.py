"""Escaneo de las dos fichas: cotas medidas en los DIBUJOS VECTORIALES contra la tabla, y el culo de
Mitsubishi contra el de Jungheinrich. Complementa culo_de_la_ficha.py. Ver LEEME.md (09-nov).

    pip install pymupdf
    python herramientas/fichas/escaneo_fichas.py

Las coordenadas (pt) son de estas versiones de los PDF; si cambian, las aserciones fallan.
"""
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
JH = os.path.join(AQUI, 'jungheinrich_etr_hoja_tecnica.pdf')
MC = os.path.join(AQUI, 'mitsubishi_esr15n2_edr18n2_brochure.pdf')


def costado_jh():
    """Vista de costado de la hoja VDI (pág. 2): extremos de las líneas de cota, en pt."""
    import pymupdf
    pag = pymupdf.open(JH)[1]
    hs = {}
    for g in pag.get_drawings():
        for it in g['items']:
            if it[0] == 'l' and abs(it[1].y - it[2].y) < 0.05:
                y = round(it[1].y, 2)
                hs.setdefault(y, []).append((min(it[1].x, it[2].x), max(it[1].x, it[2].x)))
    # filas de cota (y en pt) → tramos; los extremos son las puntas de flecha
    fila = lambda y: hs[y]
    assert 310.53 in hs and 302.62 in hs and 318.15 in hs and 326.26 in hs, '¿cambió el PDF?'
    culo, motriz, carga, dorso = 101.56, 111.02, 172.44, 163.97
    pata = max(b for a, b in fila(318.15))
    punta = max(b for a, b in fila(326.26))
    k = 1562 / (carga - motriz)                     # mm/pt por y (entre ejes)
    filas = [('240: culo → eje rueda motriz', motriz - culo, 240),
             ('y: entre ejes (escala)', carga - motriz, 1562),
             ('l2: culo → dorso de uñas', dorso - culo, 1582),
             ('x: dorso de uñas → eje de carga', carga - dorso, 219),
             ('l7: culo → punta de las patas', pata - culo, 1983),
             ('l1: culo → punta de uñas', punta - culo, 2999)]
    print(f'Jungheinrich, vista de costado (escala {k:.2f} mm/pt por y):')
    for nombre, pt, tabla in filas:
        print(f'   {nombre:34s} dibujo {pt * k:6.0f}   tabla {tabla:5d}')


def culo_mitsubishi():
    """Contorno del culo en la vista de arriba del brochure (pág. 7, caminos 10101/10110/10129)."""
    import pymupdf
    D = pymupdf.open(MC)[6].get_drawings()
    pts = []
    for i in (10110, 10101, 10129):
        for it in D[i]['items']:
            if it[0] == 'l':
                a, b = it[1], it[2]
                pts += [(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t) for t in np.linspace(0, 1, 30)]
            elif it[0] == 'c':
                P = [np.array([q.x, q.y]) for q in it[1:5]]
                pts += [tuple((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2]
                              + t ** 3 * P[3]) for t in np.linspace(0, 1, 60)]
    A = np.array(pts)
    A = A[(A[:, 0] < 404) & (A[:, 1] > 200) & (A[:, 1] < 238)]
    prof = []
    for y in np.arange(200, 238, 0.1):
        s = A[np.abs(A[:, 1] - y) < 0.06]
        if len(s):
            prof.append((y, s[:, 0].min()))
    prof = np.array(prof)
    x0 = prof[:, 1].min()
    assert abs(x0 - 397.61) < 0.05, f'culo en x = {x0:.2f}: ¿cambió el PDF?'
    yc = prof[prof[:, 1] < x0 + 0.02, 0].mean()
    hw = yc - prof[:, 0].min()                      # lado de arriba, el completo
    k = 0.5221 / hw * 1000                          # al semiancho del contorno JH
    jh = np.loadtxt(os.path.join(AQUI, 'culo_ficha.csv'), delimiter=',')
    print('\nEl culo: retiro del contorno respecto del punto del eje (mm), escalado al mismo ancho')
    print('    y (m)   Jungheinrich   Mitsubishi')
    for yy in (0.10, 0.20, 0.30, 0.35, 0.40, 0.45, 0.48, 0.50):
        a = jh[np.argmin(np.abs(jh[:, 1] - yy) + (jh[:, 0] > 0.3) * 9), 0] * 1000
        s = prof[np.argmin(np.abs(prof[:, 0] - (yc - yy * 1000 / k)))]
        print(f'    {yy:5.2f}   {a:8.0f}       {(s[1] - x0) * k:8.0f}')


if __name__ == '__main__':
    costado_jh()
    culo_mitsubishi()
