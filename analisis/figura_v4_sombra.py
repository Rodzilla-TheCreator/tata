# ─────────────────────────────────────────────────────────────────────────────
# La sombra del giro de 90° con la motriz corrida: H1 contra H2 (24-nov)
#
#   python3 analisis/figura_v4_sombra.py      → analisis/v4_sombra_h1_h2.png
#
# Vista desde arriba, uñas a la derecha, culo a la izquierda. El origen es el medio del eje de carga.
# Arriba: qué es el tope corto (+79.4°) y el largo (−104.4°). Abajo: para cada hipótesis de dónde está la
# motriz y cada tope, el equipo girando 90° sobre su centro de giro (la mancha gris es todo lo que pisa)
# y cuánto barre el culo. Misma cinemática que planificador_rutas.step (v4): centro en y = e − WB / tan δ.
# ─────────────────────────────────────────────────────────────────────────────
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                  # noqa: E402
import numpy as np                                               # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import planificador_rutas as P                                   # noqa: E402

WB, E = P.WB_V4, P.E_V4
CORTO, LARGO = math.radians(79.4), -math.radians(104.4)
Y_CARGA = 0.60                    # ruedas de carga, ~1.2 m de centro a centro (maje, 23-nov)
POLIS = [np.array(p) for p in P.poligonos(P.XPIV_V3, True, False, P.L_ANCHO, P.LCH_V3, 'ficha')]
CUERPO = POLIS[0]


def rot(pts, ang, c):
    c_, s_ = math.cos(ang), math.sin(ang)
    q = pts - c
    return np.c_[q[:, 0] * c_ - q[:, 1] * s_, q[:, 0] * s_ + q[:, 1] * c_] + c


def equipo(ax, ang=0.0, c=(0.0, 0.0), **kw):
    for p in POLIS:
        r = rot(p, ang, np.array(c))
        ax.fill(r[:, 0], r[:, 1], **kw)


def rueda(ax, x, y, d, color, largo=0.34, ancho=0.14):
    """La rueda motriz vista de arriba: rectángulo orientado a δ, y la línea de su eje (perpendicular)."""
    u, n = np.array([math.cos(d), math.sin(d)]), np.array([-math.sin(d), math.cos(d)])
    c = np.array([x, y])
    pts = np.array([c + u * largo / 2 + n * ancho / 2, c - u * largo / 2 + n * ancho / 2,
                    c - u * largo / 2 - n * ancho / 2, c + u * largo / 2 - n * ancho / 2])
    ax.fill(pts[:, 0], pts[:, 1], color=color, zorder=6)
    ax.annotate('', xy=c + u * 0.42, xytext=c, arrowprops=dict(arrowstyle='->', color=color, lw=1.6), zorder=7)


def panel_topes(ax):
    ax.set_title('Qué es cada tope: la rueda motriz vista desde arriba\n(0° = recta, rodando hacia las uñas)', fontsize=10)
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, color='0.8', lw=1, ls=':'))
    for a in (CORTO, LARGO):
        th = np.linspace(0, a, 60)
        ax.plot(0.75 * np.cos(th), 0.75 * np.sin(th), color='#1f77b4' if a > 0 else '#d62728', lw=3)
    ax.annotate('', xy=(1, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color='0.3', lw=1.5))
    ax.text(1.05, 0, 'recta (0°)\nhacia las uñas', va='center', fontsize=8)
    for a, col, txt, dx in ((CORTO, '#1f77b4', 'tope CORTO +79.4°\nno llega a 90°\n(0x184 +7 940, el que\nmaje anotó «derecho»)', -0.75),
                            (LARGO, '#d62728', 'tope LARGO −104.4°\npasa de 90°\n(0x184 −10 440, el que\nmaje anotó «izquierdo»)', -0.85)):
        ax.annotate('', xy=(math.cos(a), math.sin(a)), xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=col, lw=2))
        ax.text(dx, 1.05 * math.sin(a), txt, color=col, fontsize=8, ha='center', va='center')
    ax.plot([0, 0], [-1, 1], color='0.75', lw=0.8, ls='--')
    # las dos líneas de rueda casi coinciden
    for a in (CORTO, LARGO + math.pi):
        ax.plot([-1.25 * math.cos(a), 1.25 * math.cos(a)], [-1.25 * math.sin(a), 1.25 * math.sin(a)], color='0.55',
                lw=0.7, ls='-.')
    ax.text(-1.55, -1.45, 'Las dos puntas son casi la MISMA línea de rueda (punteadas): +79.4° y −104.4° + 180° = 75.6°.\n'
                          'Recorrido total 184°: el «modo 180°» del manual, corrido para un lado.',
            fontsize=8, color='0.25')
    ax.set_xlim(-1.6, 1.9); ax.set_ylim(-1.55, 1.4); ax.set_aspect('equal'); ax.axis('off')


def panel_equipo(ax):
    ax.set_title('El equipo y las dos hipótesis de dónde va la motriz', fontsize=10)
    equipo(ax, color='0.88', ec='0.4', lw=0.8)
    for y in (Y_CARGA, -Y_CARGA):
        ax.add_patch(plt.Rectangle((-0.064, y - 0.046), 0.128, 0.092, color='0.3'))
    ax.plot(0, 0, 'k+', ms=10)
    ax.text(0.05, 0.05, 'medio del\neje de carga', fontsize=7)
    for e, col, h in ((E, '#2ca02c', 'H1'), (-E, '#9467bd', 'H2')):
        ax.add_patch(plt.Circle((-WB, e), 0.085, color=col, zorder=5))
        ax.text(-WB - 0.13, e, f'{h}: motriz\nacá', color=col, fontsize=8, ha='right', va='center')
    ax.annotate('', xy=(-WB, 0), xytext=(-WB, E), arrowprops=dict(arrowstyle='<->', color='0.3'))
    ax.text(-WB + 0.04, E / 2, 'e ≈ 0.325', fontsize=7)
    ax.annotate('', xy=(-WB, -0.85), xytext=(0, -0.85), arrowprops=dict(arrowstyle='<->', color='0.3'))
    ax.text(-WB / 2, -0.95, 'entre ejes 1.69', fontsize=7, ha='center')
    ax.text(-0.7, 0.80, 'H1: la motriz del lado hacia donde apunta la rueda en el tope CORTO\n'
                        'H2: del otro lado. La cinta dijo 0.325 «del lado del timón», no qué tope es ese lado.\n'
                        'Prueba con un HILO: rueda en el tope corto, hilo a lo largo del eje de la rueda.\n'
                        'H1: pasa por el medio del eje de carga. H2: cae a 64 cm, junto a una pata',
            fontsize=8, ha='center', color='0.25')
    ax.set_xlim(-2.6, 1.2); ax.set_ylim(-1.1, 1.45); ax.set_aspect('equal'); ax.axis('off')


def panel_giro(ax, e, d, titulo, col):
    yc = e - WB * math.cos(d) / math.sin(d)
    c = np.array([0.0, yc])
    sentido = -math.copysign(1, math.sin(d))                 # Δθ = −(ds/WB)·sin δ
    for k in np.linspace(0, math.pi / 2, 46):
        equipo(ax, sentido * k, c, color='0.80', lw=0)
    equipo(ax, 0.0, (0, 0), fc='none', ec='0.35', lw=1)
    equipo(ax, sentido * math.pi / 2, c, fc='none', ec=col, lw=1.4)
    r_culo = np.hypot(*(CUERPO - c).T)[CUERPO[:, 0] < -1.0].max()
    ax.add_patch(plt.Circle(c, r_culo, fill=False, color=col, ls='--', lw=1))
    ax.add_patch(plt.Circle((0, 0), 1.929, fill=False, color='0.5', ls=':', lw=1))
    ax.plot(*c, 'o', color=col, ms=7, zorder=8)
    ax.plot(0, 0, 'k+', ms=9, zorder=8)
    rueda(ax, -WB, e, d, col)
    ax.plot([-WB, 0], [e, yc], color=col, lw=0.8, ls=':')          # la línea del eje de la rueda hasta el centro
    ax.set_title(titulo, fontsize=9.5, color=col)
    ext = rot(CUERPO, sentido * math.pi / 2, c)
    ancho = max(CUERPO[:, 1].max(), ext[:, 1].max()) - min(CUERPO[:, 1].min(), ext[:, 1].min())
    ax.text(0.02, 0.02, f'centro de giro a {yc * 100:+.0f} cm del medio del eje\n'
                        f'el culo barre un radio de {r_culo:.3f} m  ({(r_culo - 1.929) * 100:+.1f} cm vs centrada a 90°)',
            transform=ax.transAxes, fontsize=8, va='bottom',
            bbox=dict(fc='white', ec='0.8', alpha=0.9))
    ax.set_xlim(-2.9, 2.9); ax.set_ylim(-2.9, 2.9); ax.set_aspect('equal'); ax.axis('off')
    return r_culo


def main():
    fig = plt.figure(figsize=(14, 17))
    gs = fig.add_gridspec(3, 2, height_ratios=(0.8, 1, 1), hspace=0.12, wspace=0.04)
    panel_topes(fig.add_subplot(gs[0, 0]))
    panel_equipo(fig.add_subplot(gs[0, 1]))
    res = {}
    for fila, (e, h, col) in enumerate(((E, 'H1', '#2ca02c'), (-E, 'H2', '#9467bd')), start=1):
        for colu, (d, nom) in enumerate(((CORTO, 'tope corto +79.4°'), (LARGO, 'tope largo −104.4°'))):
            res[(h, nom)] = panel_giro(fig.add_subplot(gs[fila, colu]), e, d,
                                       f'{h} (motriz en y = {e:+.3f}) · {nom} · gira 90°', col)
    fig.suptitle('La sombra del giro de 90° con la motriz corrida (v4, 24-nov)\n'
                 'gris = todo lo que pisa el equipo (vacío, con uñas) · contorno de color = al terminar · '
                 'cruz = medio del eje de carga · punto = centro de giro\n'
                 'punteado gris = el círculo del culo del modelo v3 (rueda centrada a 90°: 1.929) · '
                 'rayado de color = el que barre ahora',
                 fontsize=11, y=0.995)
    sal = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'v4_sombra_h1_h2.png')
    fig.savefig(sal, dpi=110, bbox_inches='tight')
    for k, v in res.items():
        print(k, round(v, 3))
    print(sal)


if __name__ == '__main__':
    main()
