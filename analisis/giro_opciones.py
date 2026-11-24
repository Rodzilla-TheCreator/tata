# ─────────────────────────────────────────────────────────────────────────────
# Todas las formas de salir de (o entrar a) una bahía con un giro de 90°, con la geometría v4 (24-nov)
#
#   python3 analisis/giro_opciones.py            → giro_opciones.json, giro_opciones.png, y la tabla en pantalla
#
# Geometría v4 (analisis/rutas_resultados.md): entre ejes 1.688, motriz corrida e = +0.325 bajo el timón,
# topes −104.4° / +79.4°, culo de la ficha, 2.91 m culo → punta, retranqueo 6 cm, pasillo 3.00.
#
# LA IDEA. Con la rueda fija, el equipo gira sobre un centro que está en la línea del eje de carga, en
# y_c = e − WB / tan δ (marco del equipo, desde el medio del eje). Con estos topes, δ ∈ [−104.4°, +79.4°] cubre
# TODA la línea: δ > 0 da y_c ≤ +0.009, δ < 0 da y_c ≥ −0.108 (se solapan en el medio). El sentido de giro lo
# pone el multipiloto (adelante o atrás). Así que un giro de un solo movimiento a timón fijo se describe con
# dos números:
#   y_c   dónde está el centro de giro (0 = pivota sobre el medio del eje de carga; ±∞ = recto)
#   d     cuánto retrocede recto, con la rueda derecha, antes de girar (saca las uñas de la bahía)
# Para cada (y_c, d) se mide, con la misma regla del Mundo v2/v3 (cara del poste fuera de la luz, cara del
# cubo de N1 6 cm atrás dentro de la luz):
#   margen del chasis   lo más cerca que pasa el cuerpo (culo, capó, patas) de cualquier cara
#   margen de las uñas  lo mismo para uñas (y el cubo, cargado); arranca en 3 cm (la punta frente al cubo)
#   tiempo              poner la rueda (desde recta, a 50 °/s) + retroceder + girar 90° (rueda a 0.35 m/s)
# Y aparte, el A* libre del planificador (sin reversa, y con reversa permitida) en los mismos casos.
#
# Limitación: la regla del Mundo mide la distancia en y (a la cara), no en x al canto del poste. Es la misma
# que usa el planificador y la sim; las cifras se comparan entre sí, no son distancias euclídeas al poste.
# ─────────────────────────────────────────────────────────────────────────────
import json
import math
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import bahias as B                    # noqa: E402
import planificador_rutas as P        # noqa: E402

WB, E = P.WB_V4, P.E_V4
TOPE_NEG, TOPE_POS = P.TOPES_V4                 # magnitudes: δ < 0 hasta 104.4°, δ > 0 hasta 79.4°
W_RUEDA = math.radians(50.0)                    # medido el 23-nov (teleop)
V_GIRO = P.VMAN                                 # 0.35 m/s con mucho timón (supuesto del planificador)
REC = B.REC_L
CASOS = [(d, r) for d in ('4 La', '4 Lb', '4 Ra', '4 Rb') for r in (0.0, math.pi)]
YC = np.round(np.arange(-2.0, 2.0001, 0.02), 3)
DS = (0.0, 0.05, 0.10, 0.20, 0.30)


def delta_para(yc):
    """Las δ (rad) que ponen el centro de giro en y_c, dentro de los topes. Puede haber dos (el solape)."""
    out = []
    # y_c = e − WB·cot δ  →  cot δ = (e − y_c)/WB  →  δ = atan2(WB, e − y_c) (en (0, π)) o esa − π
    d1 = math.atan2(WB, E - yc)                 # en (0, π)
    for d in (d1, d1 - math.pi):
        if -TOPE_NEG - 1e-9 <= d <= TOPE_POS + 1e-9:
            out.append(d)
    return out


def r_rueda(yc):
    """Distancia de la rueda motriz (−WB, e) al centro de giro (0, y_c): lo que recorre por radián."""
    return math.hypot(WB, yc - E)


class Caso:
    def __init__(self, direccion, rumbo, cargado):
        self.d = B.leer(direccion)
        self.rumbo, self.cargado = rumbo, cargado
        self.pl = P.Planificador(modelo='v3', d_lim=P.TOPES_V4, rec=(REC, REC), holgura=0.0, max_exp=6000)
        self.eq = self.pl.eq_giro[cargado]
        x, y, th, _ = self.pl.pose_hueco(self.d)
        self.p0 = (x, y, th)
        self.dth = P.angdif(rumbo, th)          # ±π/2
        self.lado = 1 if self.d.s == 'L' else -1

    def margenes(self, X, Y, frente):
        """Margen (m) por punto con la regla del Mundo v2: fuera de la luz, cara del poste (±1.50); en la luz,
        cara del cubo (±1.56). Devuelve tres mínimos:
          chasis   el cuerpo contra cualquier cara
          postes   uñas (y cubo cargado) contra todo MENOS el cubo de la bahía de la que sale
          cubo     uñas contra el cubo de su bahía: arranca en 3 cm (la punta) y no tiene que bajar de 0"""
        luz = B.en_luz(X)
        sup = np.where(luz, B.HALF + REC, B.HALF)
        inf = np.where(luz, -(B.HALF + REC), -B.HALF)
        m = np.minimum(sup - Y, Y - inf)
        x0, x1 = B.bahia_x(self.d.x)
        propia = (X >= x0) & (X <= x1) & (Y * self.lado > 0) & luz
        fr = np.broadcast_to(frente, X.shape)
        mc = float(m[~fr].min())
        mp = m[fr & ~propia]
        mq = m[fr & propia]
        return mc, (float(mp.min()) if mp.size else 9.0), (float(mq.min()) if mq.size else 9.0)

    def poses_fijo(self, yc, d_atras, paso_grados=1.0):
        x, y, th = self.p0
        # retroceder recto d (alejándose del rack: sentido −1 en el marco del equipo)
        tramo = [(x - s * math.cos(th), y - s * math.sin(th), th) for s in np.linspace(0, d_atras, max(2, int(d_atras / 0.02) + 1))]
        x1, y1, _ = tramo[-1]
        cx, cy = x1 - yc * math.sin(th), y1 + yc * math.cos(th)    # el centro de giro en el mundo
        out = list(tramo)
        n = int(round(abs(math.degrees(self.dth)) / paso_grados))
        for k in range(1, n + 1):
            a = self.dth * k / n
            ca, sa = math.cos(a), math.sin(a)
            rx, ry = x1 - cx, y1 - cy
            out.append((cx + rx * ca - ry * sa, cy + rx * sa + ry * ca, th + a))
        return out

    def evaluar(self, yc, d_atras):
        poses = self.poses_fijo(yc, d_atras)
        S = self.eq.sil
        c = np.array([math.cos(p[2]) for p in poses])[:, None]
        s = np.array([math.sin(p[2]) for p in poses])[:, None]
        X = np.array([p[0] for p in poses])[:, None] + S[:, 0] * c - S[:, 1] * s
        Y = np.array([p[1] for p in poses])[:, None] + S[:, 0] * s + S[:, 1] * c
        mc, mp, mq = self.margenes(X, Y, self.eq.frente)
        return mc, mp, mq, poses[-1]


def tiempo(yc, d_atras):
    """Retroceder d con la rueda recta, poner la rueda (desde recta) y girar 90°. Sin aceleraciones."""
    ds = delta_para(yc)
    poner = min(abs(d) for d in ds) / W_RUEDA if ds else float('nan')
    return d_atras / V_GIRO + poner + (r_rueda(yc) * math.pi / 2) / V_GIRO


def astar(caso, sentidos, holguras=(0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)):
    """El A* del planificador desde la bahía hasta alinearse (como Planificador.salida), con margen por
    escalera de holgura (igual que margenes_v4). Devuelve el mejor margen y la forma del giro."""
    mejor, res = None, None
    for h in holguras:
        pl = P.Planificador(modelo='v3', d_lim=P.TOPES_V4, rec=(REC, REC), holgura=h, max_exp=6000,
                            gap=max(B.GAP_OBJ, h + 0.005))
        x, y, th, _ = pl.pose_hueco(caso.d)
        meta = P.MetaRumbo(caso.rumbo, 0.0, pl.tol_carril, k_th=pl.k_th)
        r = P.planificar((x, y, th), meta, pl.eq_giro[caso.cargado], pl.mundo([(caso.d.x, caso.d.s)]),
                         max_exp=6000, sentidos=sentidos, res_xy=0.01, res_th=1.0)
        if not r['ok']:
            break
        mejor, res = h, r
    if res is None:
        return dict(ok=False)
    dm = caso.pl.eq_giro[caso.cargado].dmax
    sent = [s for s, _, _ in res['prims']]
    angs = sorted({round(math.degrees(fr * dm)) for _, fr, _ in res['prims']})
    a, b = res['poses'][0], res['poses'][-1]
    # el mismo camino medido con la regla de los giros fijos (punta a 3 cm al arrancar): se lo corre a la pose
    # real de arranque para que se compare parejo (la escalera arranca con la punta a h + 0.5 cm)
    dx, dy = caso.p0[0] - a[0], caso.p0[1] - a[1]
    densas = []
    for (sg, fr, ds), q in zip(res['prims'], res['poses']):
        m = max(1, int(math.ceil(ds / 0.01)))
        r_ = q
        for _ in range(m):
            r_ = P.step(r_, sg * ds / m, fr * dm, True)
            densas.append((r_[0] + dx, r_[1] + dy, r_[2]))
    S_ = caso.eq.sil
    c = np.array([math.cos(p_[2]) for p_ in densas])[:, None]
    s_ = np.array([math.sin(p_[2]) for p_ in densas])[:, None]
    X = np.array([p_[0] for p_ in densas])[:, None] + S_[:, 0] * c - S_[:, 1] * s_
    Y = np.array([p_[1] for p_ in densas])[:, None] + S_[:, 0] * s_ + S_[:, 1] * c
    mc, mp, mq = caso.margenes(X, Y, caso.eq.frente)
    return dict(ok=True, margen_cm=round(100 * mejor), mismo_metro=dict(chasis=round(mc, 4), postes=round(mp, 4),
                cubo=round(mq, 4), margen=round(min(mc, mp), 4)), cambios=sum(1 for u, v in zip(sent, sent[1:]) if u != v),
                timones=angs, eje_m=round(math.hypot(b[0] - a[0], b[1] - a[1]), 3),
                rueda_m=round(sum(ds for _, _, ds in res['prims']), 2))


def sin_acercar(caso, ds=np.round(np.arange(0, 0.161, 0.01), 2), ycs=np.round(np.arange(-0.8, 0.8001, 0.01), 3)):
    """Los giros fijos que NUNCA acercan las uñas al cubo de su bahía más que los 3 cm de arranque (químicos: el
    cubo no se toca), y el margen que dejan al chasis y a las otras caras. Por retroceso d: la ventana de centros
    que sirve y el mejor."""
    filas = []
    for d in ds:
        for yc in ycs:
            if not delta_para(float(yc)):
                continue
            mc, mp, mq, _ = caso.evaluar(float(yc), float(d))
            if mq >= B.GAP_OBJ - 1e-4 and min(mc, mp) >= 0:
                filas.append(dict(m=round(min(mc, mp), 4), yc=float(yc), d=float(d), chasis=round(mc, 4),
                                  postes=round(min(mp, 9.0), 4), t=round(tiempo(float(yc), float(d)), 2),
                                  delta=[round(math.degrees(x), 1) for x in delta_para(float(yc))]))
    por_d = {}
    for f in filas:
        por_d.setdefault(f['d'], []).append(f)
    return dict(mejor=max(filas, key=lambda f: (f['m'], -f['t'])) if filas else None,
                por_d={f"{d:.2f}": dict(yc_min=min(f['yc'] for f in L), yc_max=max(f['yc'] for f in L),
                                         mejor=max(L, key=lambda f: f['m'])) for d, L in sorted(por_d.items())})


def figura(R, ruta):
    """Arriba: el mejor margen por retroceso (los 4 casos, con las uñas sin acercarse al cubo). Abajo: tres formas
    de hacer el mismo giro (4 La → adentro, cargado), con la sombra de lo que pisa."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15, 13))
    gs = fig.add_gridspec(2, 3, height_ratios=(0.8, 1.2), hspace=0.25, wspace=0.08)
    ax = fig.add_subplot(gs[0, :])
    estilos = {'vacío': '-', 'cargado': '--'}
    for k, v in R['casos'].items():
        if not k.startswith('4 La'):
            continue
        pd_ = v['sin_acercar']['por_d']
        dd = [float(x) * 100 for x in pd_]
        mm = [pd_[x]['mejor']['m'] * 100 for x in pd_]
        ax.plot(dd, mm, estilos['cargado' if 'cargado' in k else 'vacío'], marker='o', ms=3,
                label=k.replace('4 La → ', ''))
        a = v['astar_sin_reversa'].get('mismo_metro')
        if a:
            ax.plot([0], [a['margen'] * 100], 'x', ms=9, color=ax.lines[-1].get_color())
    ax.axhline(5, color='0.6', lw=0.8, ls=':')
    ax.set_xlabel('cuánto retrocede recto antes de girar (cm)')
    ax.set_ylabel('margen mínimo, chasis y postes (cm)')
    ax.set_title('Giro de un solo movimiento a timón fijo, sin acercar las uñas al cubo (> 3 cm): el mejor centro de '
                 'giro para cada retroceso.\nx = lo que hace hoy el A* (medido igual; deja la punta a 2.5 cm del cubo)',
                 fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    with P.con_geo(WB, E):
        caso = Caso('4 La', 0.0, True)
        sa = R['casos']['4 La → adentro cargado']['sin_acercar']
        opciones = [('sin retroceder, centro a +0.36 (lo del A*)', 0.36, 0.0),
                    (f"retrocede {sa['mejor']['d'] * 100:.0f} cm, centro a {sa['mejor']['yc']:+.2f} (el mejor)",
                     sa['mejor']['yc'], sa['mejor']['d']),
                    ('retrocede 12 cm, pivota sobre el medio del eje (centro 0)', 0.0, 0.12)]
        for j, (tit, yc, d) in enumerate(opciones):
            ax = fig.add_subplot(gs[1, j])
            poses = caso.poses_fijo(yc, d)
            x0 = caso.p0[0]
            for xp in B.postes():
                if abs(xp - x0) < 3.5:
                    for sgn in (1, -1):
                        ax.add_patch(plt.Rectangle((xp - B.POSTE / 2, sgn * B.HALF if sgn > 0 else -B.HALF - 0.3),
                                                   B.POSTE, 0.3, color='0.35'))
            for sgn in (1, -1):
                ax.plot([x0 - 3.5, x0 + 3.5], [sgn * B.HALF] * 2, color='0.6', lw=0.8)
                ax.plot([x0 - 3.5, x0 + 3.5], [sgn * (B.HALF + REC)] * 2, color='0.8', lw=0.8, ls=':')
            pols = [np.array(p_) for p_ in P.poligonos(caso.pl.xpiv, True, True, P.L_ANCHO, caso.pl.lch, caso.pl.r_culo)]
            for q in poses[::3] + [poses[-1]]:
                c, s_ = math.cos(q[2]), math.sin(q[2])
                for pol in pols:
                    ax.fill(q[0] + pol[:, 0] * c - pol[:, 1] * s_, q[1] + pol[:, 0] * s_ + pol[:, 1] * c,
                            color='0.75', lw=0, alpha=0.25)
            for q, col in ((poses[0], '0.3'), (poses[-1], '#2ca02c')):
                c, s_ = math.cos(q[2]), math.sin(q[2])
                for pol in pols:
                    ax.fill(q[0] + pol[:, 0] * c - pol[:, 1] * s_, q[1] + pol[:, 0] * s_ + pol[:, 1] * c,
                            fc='none', ec=col, lw=1.2)
            mc, mp, mq, _ = caso.evaluar(yc, d)
            ax.set_title(f"{tit}\nchasis {100 * mc:.1f} cm · uñas al cubo {100 * mq:.1f} cm · "
                         f"δ {', '.join(f'{x:.0f}°' for x in [math.degrees(v) for v in delta_para(yc)])}",
                         fontsize=8.5, color='#c62f2f' if min(mc, mp, mq - B.GAP_OBJ + 1e-4) < 0 else 'black')
            ax.set_xlim(x0 - 2.6, x0 + 2.6); ax.set_ylim(-1.95, 1.95); ax.set_aspect('equal'); ax.axis('off')
    fig.suptitle('Las formas de girar 90° hacia una bahía con la geometría v4 (entre ejes 1.688, motriz corrida 0.325, '
                 'topes −104.4 / +79.4)', fontsize=12)
    fig.savefig(ruta, dpi=100, bbox_inches='tight')


def main():
    t0 = time.time()
    with P.con_geo(WB, E):
        out = dict(supuestos=dict(WB=WB, E=E, TOPES=[-round(math.degrees(TOPE_NEG), 1), round(math.degrees(TOPE_POS), 1)],
                                  W_RUEDA_gs=50, V_GIRO=V_GIRO, REC=REC, XPIV=P.XPIV_V3, regla='Mundo v2: distancia en y'),
                   casos={})
        for d, r in CASOS:
            for cargado in (False, True):
                caso = Caso(d, r, cargado)
                k = f"{d} → {'adentro' if r == 0 else 'descarga'} {'cargado' if cargado else 'vacío'}"
                tabla = []
                for da in DS:
                    for yc in YC:
                        if not delta_para(yc):
                            continue
                        mc, mp, mq, fin = caso.evaluar(float(yc), da)
                        tabla.append(dict(yc=float(yc), d=da, chasis=round(mc, 4), postes=round(mp, 4),
                                          cubo=round(mq, 4), margen=round(min(mc, mp), 4),
                                          y_fin=round(fin[1], 3), t=round(tiempo(float(yc), da), 2),
                                          delta=[round(math.degrees(x), 1) for x in delta_para(float(yc))]))
                ok = [f for f in tabla if f['margen'] >= 0 and f['cubo'] >= 0]
                best = max(ok, key=lambda f: (round(f['margen'], 3), -f['t'])) if ok else None
                fila = dict(tabla=tabla, n_ok=len(ok), sin_acercar=sin_acercar(caso),
                            mejor=best,
                            astar_sin_reversa=astar(caso, (-1,)),
                            astar_con_reversa=astar(caso, (1, -1)))
                out['casos'][k] = fila
                rng = sorted({f['yc'] for f in ok if f['d'] == 0.0})
                print(f"[{time.time() - t0:5.0f} s] {k:28s} sin retroceder: centros que entran "
                      f"{(rng[0], rng[-1]) if rng else 'ninguno'} · mejor (y_c {best['yc'] if best else '-'}, d {best['d'] if best else '-'}): "
                      f"margen {100 * best['margen'] if best else 0:.1f} cm, {best['t'] if best else 0} s · A* sin reversa {fila['astar_sin_reversa'].get('mismo_metro', {}).get('margen')} m · "
                      f"con reversa {fila['astar_con_reversa'].get('mismo_metro', {}).get('margen')} m ({fila['astar_con_reversa'].get('cambios')} cambios)",
                      flush=True)
    for k, v in out['casos'].items():
        m = v['sin_acercar']['mejor']
        print(f"  {k:28s} sin acercar las uñas al cubo: mejor retrocede {100 * m['d']:.0f} cm y gira con centro "
              f"a {m['yc']:+.2f} (δ {m['delta']}) → {100 * m['m']:.1f} cm, {m['t']} s")
    with open(os.path.join(AQUI, 'giro_opciones.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    figura(out, os.path.join(AQUI, 'giro_opciones.png'))
    print('giro_opciones.png')
    print(f"giro_opciones.json ({time.time() - t0:.0f} s)")


if __name__ == '__main__':
    main()
