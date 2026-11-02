# ─────────────────────────────────────────────────────────────────────────────
# FSM de un equipo — con los estados de espera como estados DE VERDAD, no `LIBRE` de comodín
#
# Estados:
#   LIBRE              transitorio: corre el selector de tarea
#   ESPERA_PEDIDO      no hay trabajo posible (falta orden, entrada, o lo que hay es de otro)
#   ESPERA_HUECO       hay tarea, falta un hueco destino libre Y reservado a mi nombre
#   ESPERA_TRASBORDO   hay tarea, falta una posición de trasbordo libre Y reservada a mi nombre
#   los 11 PASOS del simulador (sim-web/actual_tpl.html, PASOS) — dos veces por tarea:
#     fase ORIGEN (toma) y fase DESTINO (deja)
#   FALLA, PARADA, y DESHACE_TOMA durante el deshacer (fsm_falla.py)
#
# Selector de tarea — el orden de sec/gen_fsm.py, gana la primera que se cumple:
#   TRASBORDO (un cubo mío espera en el fondo) · PEDIDO · ENTRADA (solo A) · PASE (lo que hay en
#   mi rack no es mío → al trasbordo). REUBICAR no se modela.
#
# Política de reserva:
#   'ordenada' (la buena)  reserva destino + origen, todo o nada, ANTES de salir a recoger
#   'tardia'   (CONTROL)   reserva el origen, recoge, y busca destino recién al llegar con el
#                          cubo. Es el comportamiento ingenuo y produce el deadlock de la línea 40
#                          de sec/gen_fsm.py: «trasbordo lleno → A se bloquea: no puede soltar lo
#                          que no es suyo»
#
# Una decisión que se aparta del encargo, a propósito: el encargo dice que de una espera «solo se
# sale cuando el recurso esperado quedó reservado a mi nombre». Con las uñas VACÍAS, la espera
# vuelve a correr el selector en cada tick y puede cambiar de tarea. Sin eso hay un bloqueo que la
# reserva sola no evita: A espera trasbordo para un PASE, y lo que llena el trasbordo es un cubo
# SUYO que solo él puede sacar. Con las uñas vacías no retiene nada, así que cambiar de tarea no
# rompe ninguna exclusión. Con el cubo en las uñas sí se cumple el encargo al pie de la letra.
# ─────────────────────────────────────────────────────────────────────────────
from fsm_falla import NO_REANUDABLES, PASOS, plan_deshacer, seguro_para_ceder

ESPERAS = ('ESPERA_PEDIDO', 'ESPERA_HUECO', 'ESPERA_TRASBORDO')
EXT_MAX = 0.61          # pantógrafo (CLAUDE.md)
SUBE_TOMA = 0.12        # ORIGEN: sube 12 cm para cargar (sec/gen_fsm.py)
BAJA_DEJA = 0.04        # DESTINO: baja 4 cm para soltar
VEL_ALTURA = 0.25       # m por tick
TICKS = {'CARRIL': 2, 'RECTA': 5, 'GIRO': 6, 'APROXIMA': 2, 'EXTIENDE': 3, 'TOMA': 2,
         'RETRAE': 3, 'RETROCEDE': 2, 'DESGIRA': 5, 'TRANSITO': 2, 'DESHACE_TOMA': 2}
# ≈ DUR del simulador (s) / 0.5 s por tick; ELEVA y TRANSITO duran lo que tarde la altura


class Slot:
    def __init__(self, tipo, sector=None, altura=0.0, cubo=None):
        self.tipo, self.sector, self.altura, self.cubo = tipo, sector, altura, cubo


class Mundo:
    """Los lugares físicos y qué cubo hay en cada uno. cubo = dueño ('A'/'B'), None, o '?'."""

    def __init__(self, slots):
        self.slots = slots
        self.colisiones = []           # se puso un cubo donde ya había otro

    def tipos(self):
        return {k: s.tipo for k, s in self.slots.items()}

    def quitar(self, sid):
        c = self.slots[sid].cubo
        self.slots[sid].cubo = None
        return c

    def poner(self, sid, cubo, quien, t):
        if self.slots[sid].cubo is not None:
            self.colisiones.append((t, sid, quien))
        self.slots[sid].cubo = cubo


class Tarea:
    def __init__(self, tipo, origen, tipo_destino):
        self.tipo, self.origen, self.tipo_destino, self.destino = tipo, origen, tipo_destino, None

    def __repr__(self):
        return f"{self.tipo}({self.origen}→{self.destino or '?' + self.tipo_destino})"


def espera_para(tipo_destino):
    return 'ESPERA_TRASBORDO' if tipo_destino == 'trasbordo' else (
        'ESPERA_HUECO' if tipo_destino == 'hueco' else 'ESPERA_PEDIDO')


class Equipo:
    def __init__(self, nombre, politica='ordenada', falla='correcta', verificar_hueco=True):
        self.nombre, self.politica, self.politica_falla = nombre, politica, falla
        self.verificar_hueco = verificar_hueco
        self.est, self.paso_t, self.fase, self.tarea = 'LIBRE', 0, None, None
        self.carga, self.ext, self.altura, self.alt_toma0 = None, 0.0, 0.0, None
        self.reservas = set()
        self.pedidos = 0
        self.completadas = 0
        self.modo, self.cola, self.al_terminar = None, [], None
        self.est_antes, self.pausa = None, 0
        self.historial = []
        self.log_deshacer = []          # cada paso de deshacer al empezar (algunos duran un tick)

    # ── selector ─────────────────────────────────────────────────────────
    def candidatas(self, m, g):
        """Las tareas posibles por su ORIGEN, en el orden del selector (sec/gen_fsm.py)."""
        mi, out = self.nombre, []
        def ok(sid):
            return g.libre_para(mi, sid)
        for sid, s in sorted(m.slots.items()):
            if s.tipo == 'trasbordo' and s.cubo == mi and ok(sid):
                out.append(Tarea('TRASBORDO', sid, 'hueco')); break
        if self.pedidos > 0:
            for sid, s in sorted(m.slots.items()):
                if s.tipo == 'hueco' and s.sector == mi and s.cubo == mi and ok(sid):
                    out.append(Tarea('PEDIDO', sid, 'salida')); break
        if mi == 'A':
            for sid, s in sorted(m.slots.items()):
                if s.tipo == 'entrada' and s.cubo in ('A', 'B') and ok(sid):
                    out.append(Tarea('ENTRADA', sid, 'hueco' if s.cubo == mi else 'trasbordo')); break
        for sid, s in sorted(m.slots.items()):
            if s.tipo == 'hueco' and s.sector == mi and s.cubo in ('A', 'B') and s.cubo != mi and ok(sid):
                out.append(Tarea('PASE', sid, 'trasbordo')); break
        return out

    def elegir_tarea(self, m, g):
        """«Gana el primero que se CUMPLE»: la primera candidata que además tiene destino libre.
        Si ninguna lo tiene, se espera por la de mayor prioridad.

        Corregido el 02-nov: la primera versión devolvía la primera candidata aunque no tuviera
        destino. Con el rack lleno, A esperaba para siempre un hueco para su TRASBORDO teniendo
        2 PEDIDOS pendientes que lo habrían liberado: inanición por prioridad (1–3 de 20 corridas
        de la prueba 4 «bloqueadas» con la política buena)."""
        cands = self.candidatas(m, g)
        for c in cands:
            if self.elegir_destino(m, g, c.tipo_destino):
                return c
        return cands[0] if cands else None

    def elegir_destino(self, m, g, tipo_destino):
        for sid, s in sorted(m.slots.items()):
            if s.tipo != tipo_destino or s.cubo is not None or not g.libre_para(self.nombre, sid):
                continue
            if tipo_destino in ('hueco', 'salida') and s.sector != self.nombre:
                continue
            return sid
        return None

    # ── un tick ──────────────────────────────────────────────────────────
    def tick(self, t, m, g):
        if self.est == 'FALLA' or self.est == 'PARADA':
            pass
        elif self.pausa > 0:
            self.pausa -= 1
        elif self.modo == 'deshacer':
            self._paso_deshacer(m, g)
        elif self.est == 'LIBRE' or self.est in ESPERAS:
            self._decidir(t, m, g)
        else:
            self._paso(t, m, g)
        self.historial.append((t, self.est, round(self.ext, 4), round(self.altura, 4), self.modo))

    def _arrancar(self, fase):
        self.fase, self.est, self.paso_t = fase, 'CARRIL', 0

    def _decidir(self, t, m, g):
        if self.carga is None:                        # uñas vacías: el selector manda (ver arriba)
            if self.tarea is None or self.est in ESPERAS:
                self.tarea = self.elegir_tarea(m, g)
            if self.tarea is None:
                self.est = 'ESPERA_PEDIDO'
                return
            if self.politica == 'ordenada':
                dest = self.elegir_destino(m, g, self.tarea.tipo_destino)
                if dest and g.reservar_todo(self.nombre, [dest, self.tarea.origen]):
                    self.tarea.destino = dest
                    self.reservas = {dest, self.tarea.origen}
                    self._arrancar('ORIGEN')
                else:
                    self.est = espera_para(self.tarea.tipo_destino)
            else:                                     # 'tardia': solo el origen, destino después
                if g.reservar(self.nombre, self.tarea.origen):
                    self.reservas = {self.tarea.origen}
                    self._arrancar('ORIGEN')
                else:
                    self.est = 'ESPERA_PEDIDO'
        else:                                         # con el cubo en las uñas: hace falta destino
            dest = self.elegir_destino(m, g, self.tarea.tipo_destino)
            if dest and g.reservar(self.nombre, dest):
                self.tarea.destino = dest
                self.reservas.add(dest)
                self._arrancar('DESTINO')
            else:
                self.est = espera_para(self.tarea.tipo_destino)

    def _objetivo(self, m):
        sid = self.tarea.origen if self.fase == 'ORIGEN' else self.tarea.destino
        return sid, m.slots[sid]

    def _paso(self, t, m, g):
        e = self.est
        self.paso_t += 1
        sid, s = self._objetivo(m)
        if e == 'ELEVA':
            self.altura = _hacia(self.altura, s.altura, VEL_ALTURA)
            listo = abs(self.altura - s.altura) < 1e-9
        elif e == 'APROXIMA':
            listo = self.paso_t >= TICKS[e]
            if listo and self.fase == 'DESTINO' and self.verificar_hueco and s.cubo is not None:
                self.evento('HUECO_OCUPADO', m, g)    # la cámara ve el lugar ocupado
                return
        elif e == 'EXTIENDE':
            self.ext = min(EXT_MAX, self.ext + EXT_MAX / TICKS[e])
            listo = self.ext >= EXT_MAX - 1e-9
        elif e == 'TOMA':
            if self.paso_t == 1:
                self.alt_toma0 = self.altura
            d = SUBE_TOMA if self.fase == 'ORIGEN' else -BAJA_DEJA
            self.altura = self.alt_toma0 + d * min(1.0, self.paso_t / TICKS[e])
            listo = self.paso_t >= TICKS[e]
            if listo:
                if self.fase == 'ORIGEN':
                    self.carga = m.quitar(sid)
                else:
                    m.poner(sid, self.carga, self.nombre, t)
                    self.carga = None
                self.alt_toma0 = None
        elif e == 'RETRAE':
            self.ext = max(0.0, self.ext - EXT_MAX / TICKS[e])
            listo = self.ext <= 1e-9
        elif e == 'TRANSITO':
            self.altura = _hacia(self.altura, 0.0, VEL_ALTURA)
            listo = self.altura <= 1e-9 and self.paso_t >= TICKS[e]
        else:
            listo = self.paso_t >= TICKS[e]
        if not listo:
            return
        i = PASOS.index(e)
        if i < len(PASOS) - 1:
            self.est, self.paso_t = PASOS[i + 1], 0
        elif self.fase == 'ORIGEN':
            if self.politica == 'ordenada':
                self._arrancar('DESTINO')
            else:
                self.est = 'LIBRE'                    # 'tardia': recién ahora busca destino
        else:
            if self.tarea.tipo == 'PEDIDO':
                self.pedidos -= 1
            g.liberar_todo(self.nombre)
            self.reservas, self.tarea, self.fase = set(), None, None
            self.completadas += 1
            self.est = 'LIBRE'

    # ── fallas ───────────────────────────────────────────────────────────
    def evento(self, tipo, m=None, g=None, pausa=5):
        if tipo == 'PARO':
            self.est_antes = (self.est, self.paso_t)
            if self.politica_falla == 'ingenua':      # CONTROL: rinde el control como esté
                self.est = 'PARADA'
            else:
                self.est = 'FALLA'
        elif tipo == 'ARUCO_PERDIDO':
            if self.est not in NO_REANUDABLES:
                self.pausa = pausa
            else:
                self._empezar_deshacer(self.est, al_terminar='REINTENTA')
        elif tipo == 'HUECO_OCUPADO':
            sid = self.tarea.destino
            if g is not None:
                g.liberar(self.nombre, sid)
            self.reservas.discard(sid)
            self.tarea.destino = None
            self._empezar_deshacer(self.est, al_terminar='OTRO_DESTINO')

    def rearme(self):
        """El rearme es manual (docs/10). La FSM correcta deshace antes de ceder."""
        est, paso_t = self.est_antes
        if self.politica_falla == 'ingenua':          # CONTROL: retoma desde la mitad
            self.est, self.paso_t = est, paso_t
            return
        self._empezar_deshacer(est, al_terminar='PARADA')

    def _empezar_deshacer(self, est, al_terminar):
        self.cola = plan_deshacer(est, self.ext, self.altura, self.alt_toma0)
        self.al_terminar = al_terminar
        if not self.cola:
            self._fin_deshacer()
            return
        self.modo = 'deshacer'
        self.est, self.paso_t = self.cola.pop(0), 0
        self.log_deshacer.append((self.est, round(self.ext, 4), round(self.altura, 4)))

    def _paso_deshacer(self, m, g):
        e = self.est
        self.paso_t += 1
        if e == 'DESHACE_TOMA':
            self.altura = _hacia(self.altura, self.alt_toma0, SUBE_TOMA / TICKS['TOMA'])
            listo = abs(self.altura - self.alt_toma0) < 1e-9
        elif e == 'RETRAE':
            self.ext = max(0.0, self.ext - EXT_MAX / TICKS[e])
            listo = self.ext <= 1e-9
        elif e == 'TRANSITO':
            self.altura = _hacia(self.altura, 0.0, VEL_ALTURA)
            listo = self.altura <= 1e-9
        else:
            listo = self.paso_t >= TICKS[e]
        if listo:
            if self.cola:
                self.est, self.paso_t = self.cola.pop(0), 0
                self.log_deshacer.append((self.est, round(self.ext, 4), round(self.altura, 4)))
            else:
                self._fin_deshacer()

    def _fin_deshacer(self):
        self.modo, self.alt_toma0 = None, None
        if self.al_terminar == 'PARADA':
            self.est = 'PARADA'
        elif self.al_terminar == 'REINTENTA':
            self._arrancar(self.fase)
        else:                                          # OTRO_DESTINO
            self.est = espera_para(self.tarea.tipo_destino)

    def seguro(self):
        return seguro_para_ceder(self.est, self.ext, self.altura)


def _hacia(x, objetivo, paso):
    if abs(objetivo - x) <= paso:
        return objetivo
    return x + paso if objetivo > x else x - paso
