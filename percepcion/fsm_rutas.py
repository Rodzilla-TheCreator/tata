# ─────────────────────────────────────────────────────────────────────────────
# Duraciones de la FSM sacadas del planificador, no de la tabla fija TICKS
#
# Fuente: analisis/rutas_tabla.json → 'tabla_fsm', que escribe analisis/planificador_rutas.py
# (regenerar con `py analisis/planificador_rutas.py` si cambia la geometría o un SUPUESTO).
#
# Qué sale de dónde, por paso (1 tick = 0.5 s, como el resto de la FSM):
#   CARRIL     cambio de carril al de giro del lado `s` (Hybrid A*: curva en S)
#   RECTA      traslado por el pasillo con el sobre de 1.5 m/s y aceleración, MÁS la vuelta si el
#              rumbo de viaje no es el que pide la entrada (ver abajo)
#   GIRO       la ENTRADA al hueco (= la salida invertida, mismo tiempo)
#   ELEVA      la altura de ENTRADA del nivel (tabla de CLAUDE.md) a VEL_ELEV (SUPUESTO, sim-web)
#   RETROCEDE  el primer tramo de la SALIDA
#   DESGIRA    el resto de la salida, hasta quedar alineado al pasillo
#   TRANSITO   uñas abajo a VEL_ELEV
#   APROXIMA, EXTIENDE, TOMA, RETRAE siguen con TICKS: son del pantógrafo, no de la ruta
#
# EL RUMBO DE VIAJE IMPORTA (analisis/rutas_resultados.md): con las uñas hasta PROF_BAHIA dentro
# de la bahía al girar, a la posición `a` solo se entra con las uñas hacia ADENTRO y a la `b` solo
# hacia la DESCARGA. Si el equipo viene con el rumbo contrario, tiene que dar la VUELTA: dos 90°
# por el centro de la misma bahía (SUPUESTO: su luz libre a la altura de las uñas, como al girar). Eso no es un paso de la FSM (PASOS no cambia, la
# usan fsm_falla.py y la clase): se cuenta dentro de RECTA y queda anotado en `maniobras`.
#
# Lo que es SUPUESTO acá, además de lo del planificador: las maniobras se midieron VACÍO en la
# bahía 4 y se usan para todas (no dependen de x lejos de la boca y del fondo); cargado se asume igual.
# ─────────────────────────────────────────────────────────────────────────────
import json
import math
import os
import sys

_AN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analisis')
sys.path.insert(0, _AN)
import bahias as B                                             # noqa: E402

ADENTRO, DESCARGA = 'adentro', 'descarga'
X_FONDO_TRASBORDO = B.fin_rack() + 1.0          # SUPUESTO: el trasbordo a 1 m del último poste
X_DESCARGA = B.pose_descarga()[0]


class Rutas:
    def __init__(self, archivo=os.path.join(_AN, 'rutas_tabla.json')):
        with open(archivo, encoding='utf-8') as f:
            self.T = json.load(f)['tabla_fsm']
        self.tick = self.T['TICK']

    def ticks(self, seg):
        return max(1, int(round(seg / self.tick)))

    def t_recta(self, d):
        """Arranca y para: trapecio con ACC hasta VMAX, triángulo si es corta."""
        v, a = self.T['VMAX'], self.T['ACC']
        if d <= 1e-9:
            return 0.0
        return 2 * math.sqrt(d / a) if d < v * v / a else d / v + v / a

    def salida(self, s, p, rumbo):
        return self.T['salidas'].get(f"{s}{p}|{rumbo}")

    def rumbos(self, s, p):
        return [r for r in (ADENTRO, DESCARGA) if self.salida(s, p, r)]

    def carril(self, desde, hasta):
        """(segundos, metros que avanza a lo largo del pasillo) del cambio de carril."""
        if abs(desde - hasta) < 0.05:
            return 0.0, 0.0
        c = self.T['carril giro→giro' if abs(desde - hasta) > 0.9 else 'carril central→giro']
        return c['tiempo'], c['largo']

    def recta(self, d, avance):
        """La RECTA descuenta lo que ya avanzó el CARRIL (la curva en S también recorre pasillo).
        Corregido 05-nov: la primera versión contaba esos ~4 m dos veces."""
        return self.t_recta(max(0.0, d - avance))

    def vuelta_bahia(self, s, r0, r1):
        """Dos 90° por el centro de una bahía: entra con r0, sale con r1."""
        a, b = self.salida(s, 'c', r0), self.salida(s, 'c', r1)
        return a['tiempo'] + b['tiempo'], a['dx_fin'], b['dx_fin']

    def plan(self, x, carril_y, rumbo, slot, x_siguiente=None):
        """Duraciones (s) de CARRIL, RECTA, GIRO, RETROCEDE, DESGIRA para ir de (x, carril, rumbo)
        al `slot`, y el estado al salir. Devuelve (seg, despues, maniobras)."""
        seg, man = {}, []
        if slot.dir is not None:                                  # hueco de rack
            d = B.leer(slot.dir)
            xc, y_giro = slot.x, B.carril(d.s)
            disp = self.rumbos(d.s, d.p)
            r_in = rumbo if rumbo in disp else disp[0]
            x_ini = xc + self.salida(d.s, d.p, r_in)['dx_fin']   # donde arranca la entrada
            seg['CARRIL'], av = self.carril(carril_y, y_giro)
            if r_in == rumbo:
                seg['RECTA'] = self.recta(abs(x_ini - x), av)
                man.append(f"RECTA {abs(x_ini - x):.2f} m con {_txt(rumbo)}")
            else:                                                 # vuelta por el centro de la misma bahía,
                vecina = d.x                                      # lo que eligió el planificador en el caso de maje
                xv = B.centro_posicion(vecina, 'c')
                tv, dx0, dx1 = self.vuelta_bahia(d.s, rumbo, r_in)
                dist = abs(xv + dx0 - x) + abs(x_ini - (xv + dx1))
                seg['RECTA'] = self.recta(abs(xv + dx0 - x), av) + tv + self.t_recta(abs(x_ini - (xv + dx1)))
                man.append(f"VUELTA por {vecina} {d.s}c (dos 90°): llega con {_txt(rumbo)}, "
                           f"la entrada a {d!r} pide {_txt(r_in)} · {dist:.2f} m de traslado")
            sal_in = self.salida(d.s, d.p, r_in)
            seg['GIRO'] = sal_in['tiempo']
            man.append(f"GIRO a {d!r} viniendo con {_txt(r_in)}: {sal_in['largo']:.2f} m, "
                       f"{sal_in['cambios']} cambios de sentido")
            pref = DESCARGA if (x_siguiente is None or x_siguiente < xc) else ADENTRO
            r_out = pref if pref in disp else disp[0]
            so = self.salida(d.s, d.p, r_out)
            seg['RETROCEDE'], seg['DESGIRA'] = so['primer_tramo'], so['resto']
            man.append(f"SALE de {d!r} con {_txt(r_out)}"
                       + ("" if r_out == pref else f" (quería {_txt(pref)}: desde la posición {d.p} no hay)"))
            despues = (xc + so['dx_fin'], y_giro, r_out)
        else:                                                     # trasbordo (fondo) / entrada y salida (descarga)
            al_fondo = slot.tipo == 'trasbordo'
            r_in = ADENTRO if al_fondo else DESCARGA              # uñas hacia el lugar
            seg['CARRIL'], av = self.carril(carril_y, 0.0)
            if r_in == rumbo:
                seg['RECTA'] = self.recta(abs(slot.x - x), av)
                man.append(f"RECTA {abs(slot.x - x):.2f} m con {_txt(rumbo)} hasta {slot.tipo}")
            elif al_fondo:
                tv, dx0, dx1 = self.vuelta_bahia('L', rumbo, r_in)
                xv = B.centro_posicion(B.N, 'c')
                seg['RECTA'] = self.recta(abs(xv - x), av) + tv + self.t_recta(abs(slot.x - xv))
                man.append(f"VUELTA por {B.N} Lc (dos 90°) para llegar al trasbordo con {_txt(r_in)}")
            else:
                vz = self.T['vuelta_zona']
                seg['RECTA'] = self.recta(abs(B.X0 - x), av) + vz['tiempo']
                man.append(f"VUELTA en la zona de descarga para llegar con {_txt(r_in)}")
            seg['GIRO'] = seg['RETROCEDE'] = seg['DESGIRA'] = 0.0
            despues = (slot.x, 0.0, r_in)
        return seg, despues, man


def _txt(r):
    return 'uñas hacia adentro' if r == ADENTRO else 'uñas hacia la descarga'
