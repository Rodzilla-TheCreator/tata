# ─────────────────────────────────────────────────────────────────────────────
# Coordinación de A y B en memoria — reserva, deadlock y paro, cada uno con su control
#
#   py percepcion/sim_coordinacion.py        # termina con RESULTADO: PASA / FALLA
#
# Prueba 1 · CARRERA por la última posición de trasbordo, A y B en el mismo tick
#            con gestor: gana exactamente uno, el otro queda en ESPERA_TRASBORDO
#            CONTROL GestorTonto: los dos creen que es suya, y sin cámara chocan los cubos
# Prueba 2 · DEADLOCK de la línea 40 de sec/gen_fsm.py (un solo trasbordo, dos PASE cruzados)
#            con la política 'ordenada': todos los cubos llegan a su dueño
#            CONTROL política 'tardia': uno queda con un cubo en las uñas frente a un trasbordo
#            lleno con SU propio cubo. Nadie avanza → deadlock detectado
# Prueba 3 · PARO con el pantógrafo extendido en altura (EXTIENDE y TOMA)
#            la FSM no cede sin retraer en orden; termina en PARADA con todo en 0
#            CONTROL falla 'ingenua': cede el control tal cual y retoma desde la mitad
# Prueba 4 · operación al azar, 20 semillas × 3000 ticks: colisiones y deadlocks por política
#
# Las cuatro corren DOS veces: con la tabla fija TICKS (los números de clases/fsm.html) y con
# DIRECCIONES DE BAHÍA y duraciones del planificador (fsm_rutas.py). Y una quinta, solo con
# direcciones:
# Prueba 5 · EL CASO DE MAJE: el equipo frente a 3L, uñas hacia la descarga; pedido del cubo de
#            5 3 Ra (y de 5 3 Rb) a la descarga. Secuencia de estados, maniobras, y que el tiempo
#            de movimiento de la FSM dé lo mismo que el planificador PARADO ENTRE MANIOBRAS (±25 %),
#            que es como se mueve la FSM: un paso termina quieto antes de que empiece el otro.
#            Corregido 05-nov: se comparaba contra el plan continuo y daba +30–43 %; la mitad era
#            un bug (la RECTA contaba de nuevo lo que avanza el CARRIL) y el resto es parar entre
#            pasos, que se reporta aparte como lo que cuesta la FSM por pasos
# ─────────────────────────────────────────────────────────────────────────────
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fsm_estados import ESPERAS, Equipo, Mundo, Slot          # noqa: E402
from reserva import GestorDeReservas, GestorTonto             # noqa: E402
import fsm_rutas                                               # noqa: E402

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PASO_NIVEL = 1.38        # m entre plataformas (CLAUDE.md, el rack)
MODO = {'rutas': None}   # None = tabla fija TICKS · fsm_rutas.Rutas() = direcciones de bahía
NIVELES = ['1A', '2', '3', '4']


def nuevo(nombre, **kw):
    return Equipo(nombre, rutas=MODO['rutas'], **kw)


def dir_de(i):
    """Hueco i → dirección: bahías 1, 1, 2, 2, 3, 3… alternando L/R, posición a/b alternada por
    bahía, niveles 1A, 2, 3, 4 (el mismo i % 4 de la versión con alturas fijas)."""
    return f"{1 + i // 2} {NIVELES[i % 4]} {'L' if i % 2 == 0 else 'R'}{'a' if (i // 2) % 2 == 0 else 'b'}"


def hueco(sector, i, cubo=None, nivel=None):
    if MODO['rutas'] is None:
        return Slot('hueco', sector, (i % 4 if nivel is None else nivel) * PASO_NIVEL, cubo)
    d = dir_de(i) if nivel is None else f"{1 + i} {NIVELES[nivel]} La"
    return Slot.hueco_en(sector, d, cubo)


def lugar(tipo, sector=None, cubo=None):
    if MODO['rutas'] is None:
        return Slot(tipo, sector, 0.0, cubo)
    return Slot.lugar(tipo, sector, cubo)


def mundo_chico(trasbordos, huecosA, huecosB, entrada=False):
    s = {}
    for i, c in enumerate(trasbordos):
        s[f"T{i}"] = lugar('trasbordo', None, c)
    for i, c in enumerate(huecosA):
        s[f"HA{i}"] = hueco('A', i, c)
    for i, c in enumerate(huecosB):
        s[f"HB{i}"] = hueco('B', i, c)
    if entrada:
        s["E"] = lugar('entrada', 'A')
        s["SA"] = lugar('salida', 'A')
        s["SB"] = lugar('salida', 'B')
    return Mundo(s)


def creen_suyo(equipos):
    """Lugares que más de un equipo cree tener reservados al mismo tiempo."""
    vistos, dobles = {}, set()
    for e in equipos:
        for r in e.reservas:
            if r in vistos and vistos[r] != e.nombre:
                dobles.add(r)
            vistos[r] = e.nombre
    return dobles


def correr(m, g, equipos, ticks, eventos=None, ventana_deadlock=60):
    """Devuelve (tick del deadlock o None, conjunto de dobles creencias vistas)."""
    firma_vieja, quieto, dobles = None, 0, set()
    for t in range(ticks):
        for e in equipos:
            e.tick(t, m, g)
        if eventos:
            eventos(t, m, g)
        dobles |= creen_suyo(equipos)
        firma = tuple((e.est, e.paso_t, e.carga, e.modo) for e in equipos)
        esperando = any(e.carga is not None or e.est in ('ESPERA_HUECO', 'ESPERA_TRASBORDO')
                        for e in equipos)
        quieto = quieto + 1 if (firma == firma_vieja and esperando) else 0
        firma_vieja = firma
        if quieto >= ventana_deadlock:
            return t, dobles
    return None, dobles


def en_casa(m):
    """Todos los cubos A/B están en un hueco de su dueño."""
    return all(s.cubo is None or s.cubo == '?' or (s.tipo == 'hueco' and s.sector == s.cubo)
               for s in m.slots.values())


# ── Prueba 1 · carrera ───────────────────────────────────────────────────────
def prueba_carrera():
    print("1 · CARRERA por la última posición de trasbordo (T1), A y B en el mismo tick")
    res = {}
    for nombre, Gestor, verif in (("con GestorDeReservas", GestorDeReservas, True),
                                  ("CONTROL GestorTonto", GestorTonto, False)):
        m = mundo_chico(['?', None], ['B', None], ['A', None])     # T0 ocupado por otra cosa
        g = Gestor(m.tipos())
        A, B = nuevo('A', verificar_hueco=verif), nuevo('B', verificar_hueco=verif)
        A.tick(0, m, g); B.tick(0, m, g)
        duenios = [e.nombre for e in (A, B) if 'T1' in e.reservas]
        perdedor = [e.est for e in (A, B) if 'T1' not in e.reservas]
        _, dobles = correr(m, g, [A, B], 400)
        res[nombre] = dict(duenios=duenios, estB=perdedor[0] if perdedor else None,
                           colisiones=len(m.colisiones), dobles=sorted(dobles), en_casa=en_casa(m))
        print(f"    {nombre:<22} tick 0: T1 la creen suya {duenios or 'nadie'}"
              + (f" · el otro queda en {res[nombre]['estB']}" if len(duenios) == 1 else "")
              + f" · cubos chocados {len(m.colisiones)} · todo en casa al final: {'sí' if en_casa(m) else 'no'}")
    bueno, tonto = res["con GestorDeReservas"], res["CONTROL GestorTonto"]
    ok = (len(bueno['duenios']) == 1 and bueno['estB'] == 'ESPERA_TRASBORDO' and bueno['colisiones'] == 0 and not bueno['dobles'] and bueno['en_casa']
          and len(tonto['duenios']) == 2 and tonto['colisiones'] >= 1)
    print(f"    → {'PASA' if ok else 'FALLA'}: el gestor da el lugar a uno solo; sin gestor chocan"
          f"{'' if len(tonto['duenios']) == 2 else ' (OJO: el control NO produjo la colisión: la prueba no probó nada)'}")
    return ok


# ── Prueba 2 · deadlock ──────────────────────────────────────────────────────
def prueba_deadlock():
    print("2 · DEADLOCK de sec/gen_fsm.py:40 — un solo trasbordo, A pasa un cubo de B y B uno de A")
    res = {}
    for pol in ('ordenada', 'tardia'):
        m = mundo_chico([None], ['B', None], ['A', None])
        g = GestorDeReservas(m.tipos())
        A, B = nuevo('A', politica=pol), nuevo('B', politica=pol)
        t_dl, _ = correr(m, g, [A, B], 600)
        res[pol] = dict(deadlock=t_dl, en_casa=en_casa(m), A=(A.est, A.carga), B=(B.est, B.carga),
                        T0=m.slots['T0'].cubo, hechas=A.completadas + B.completadas)
        if t_dl is None:
            print(f"    política {pol:<9} progresa: {res[pol]['hechas']} tareas, todos los cubos en casa: "
                  f"{'sí' if en_casa(m) else 'no'}")
        else:
            quien = A if A.carga else B
            print(f"    política {pol:<9} DEADLOCK en el tick {t_dl}: {quien.nombre} en {quien.est} con el cubo "
                  f"de {quien.carga} en las uñas; T0 tiene el cubo de {m.slots['T0'].cubo} (¡el suyo!), "
                  f"y solo él lo puede sacar")
    ok = res['ordenada']['deadlock'] is None and res['ordenada']['en_casa'] and res['tardia']['deadlock'] is not None
    print(f"    → {'PASA' if ok else 'FALLA'}: la regla todo-o-nada-antes-de-tocar rompe el ciclo; sin ella, deadlock"
          f"{'' if res['tardia']['deadlock'] is not None else ' (OJO: el control no produjo el deadlock)'}")
    return ok


# ── Prueba 3 · paro en altura ────────────────────────────────────────────────
def un_paro(falla, en_paso, fraccion_ext=0.5):
    """Un equipo lleva su cubo del trasbordo al hueco del 3er nivel; PARO en `en_paso` (fase DESTINO)."""
    m = Mundo({'T0': lugar('trasbordo', None, 'A'), 'HA0': hueco('A', 0, None, nivel=2)})
    g = GestorDeReservas(m.tipos())
    A = nuevo('A', falla=falla)
    t, marca = 0, None
    while t < 300:
        A.tick(t, m, g)
        if (marca is None and A.fase == 'DESTINO' and A.est == en_paso
                and (en_paso != 'EXTIENDE' or A.ext >= fraccion_ext * 0.61 - 1e-9)
                and (en_paso != 'TOMA' or A.paso_t >= 1)):
            A.evento('PARO')
            marca = t
            cedio = dict(est=A.est, ext=A.ext, altura=A.altura, seguro=A.seguro())
        if marca is not None and t == marca + 5:
            A.rearme()
        if marca is not None and t > marca + 5 and A.est in ('PARADA',) and A.modo is None:
            break
        if marca is not None and t > marca + 5 and falla == 'ingenua' and A.est not in ('PARADA',):
            pass
        t += 1
    tras = [h for h in A.historial if h[0] > marca + 5]
    return A, m, marca, cedio, tras


def prueba_paro():
    h = hueco('A', 0, None, nivel=2).altura
    print(f"3 · PARO con el pantógrafo extendido en altura (fase DESTINO, hueco a {h:.2f} m)")
    oks = []
    for paso in ('EXTIENDE', 'TOMA'):
        A, m, marca, cedio, tras = un_paro('correcta', paso)
        exts = [h[2] for h in tras]
        monotono = all(b <= a + 1e-9 for a, b in zip(exts, exts[1:]))
        baja_afuera = any(h1[3] < h0[3] - 1e-9 and h0[2] > 1e-9 and h1[4] == 'deshacer' and h1[1] != 'DESHACE_TOMA'
                          for h0, h1 in zip(tras, tras[1:]))
        secuencia = [x[0] for x in A.log_deshacer]
        toma_antes = paso != 'TOMA' or (secuencia[:1] == ['DESHACE_TOMA'] and A.log_deshacer[1][2] == round(m.slots['HA0'].altura, 4))
        cubo = f"cubo en las uñas: {'sí' if A.carga else 'no'}, hueco {'vacío' if m.slots['HA0'].cubo is None else 'con cubo'}"
        ok = (A.est == 'PARADA' and A.seguro() and monotono and not baja_afuera and cedio['est'] == 'FALLA' and toma_antes
              and (paso != 'TOMA' or (A.carga == 'A' and m.slots['HA0'].cubo is None)))
        oks.append(ok)
        print(f"    PARO en {paso:<8} pantógrafo {cedio['ext']:.2f} m a {cedio['altura']:.2f} m · congelada en FALLA hasta el rearme")
        print(f"        deshacer: {' → '.join(secuencia)} → PARADA · final: pantógrafo {A.ext:.2f}, altura {A.altura:.2f}"
              f" · retrae monótono: {'sí' if monotono else 'NO'} · bajó con el pantógrafo afuera: {'SÍ' if baja_afuera else 'no'}"
              + (f" · {cubo}" if paso == 'TOMA' else ""))
    A, m, marca, cedio, tras = un_paro('ingenua', 'EXTIENDE')
    ext_tras = max(h[2] for h in tras) if tras else 0
    control_inseguro = not cedio['seguro']
    print(f"    CONTROL falla ingenua: al PARO cede el control en {cedio['est']} con {cedio['ext']:.2f} m de pantógrafo "
          f"afuera a {cedio['altura']:.2f} m → seguro: {'sí' if cedio['seguro'] else 'NO'}; al rearmar retoma EXTIENDE "
          f"desde la mitad (llega a {ext_tras:.2f} m) sin haber mirado nada")
    ok = all(oks) and control_inseguro
    print(f"    → {'PASA' if ok else 'FALLA'}: la FSM no cede sin retraer en orden; el control muestra por qué")
    return ok


def pruebas_extra():
    """No son del criterio del encargo; documentan los otros dos eventos."""
    print("   extra · ARUCO_PERDIDO en EXTIENDE y HUECO_OCUPADO al llegar")
    m = Mundo({'T0': lugar('trasbordo', None, 'A'), 'HA0': hueco('A', 0, None, nivel=1)})
    g = GestorDeReservas(m.tipos()); A = nuevo('A'); hecho = False
    for t in range(400):
        A.tick(t, m, g)
        if not hecho and A.est == 'EXTIENDE' and A.fase == 'DESTINO' and A.paso_t == 2:
            A.evento('ARUCO_PERDIDO'); hecho = True
    print(f"        ARUCO_PERDIDO: deshace, re-aproxima y termina → tareas hechas {A.completadas}, cubo en HA0: "
          f"{'sí' if m.slots['HA0'].cubo == 'A' else 'no'}")
    ok1 = A.completadas == 1 and m.slots['HA0'].cubo == 'A'
    m = Mundo({'T0': lugar('trasbordo', None, 'A'), 'HA0': hueco('A', 0, None, nivel=1),
               'HA1': hueco('A', 1, None, nivel=2)})
    g = GestorDeReservas(m.tipos()); A = nuevo('A'); puesto = False
    for t in range(500):
        A.tick(t, m, g)
        if not puesto and A.fase == 'DESTINO' and A.est == 'RECTA':
            m.slots[A.tarea.destino].cubo = '?'; puesto = True     # alguien dejó algo ahí
    print(f"        HUECO_OCUPADO: la cámara lo ve, suelta esa reserva y busca otro → cubo en HA1: "
          f"{'sí' if m.slots['HA1'].cubo == 'A' else 'no'} · chocados {len(m.colisiones)}")
    ok2 = m.slots['HA1'].cubo == 'A' and not m.colisiones
    return ok1 and ok2


# ── Prueba 4 · operación al azar ─────────────────────────────────────────────
def operacion(semilla, politica, Gestor, trasbordos=1, lleno=0.8, ticks=3000):
    r = random.Random(semilla)
    # el día uno el inventario está revuelto: cubos de A y de B en los dos racks. Sin eso B nunca
    # tiene un cubo ajeno y no hay PASE cruzado: ni el deadlock ni la carrera pueden pasar, y la
    # prueba no discrimina (corregido 02-nov: con racks vacíos los dos controles pasaban)
    ini = lambda: [r.choice('AB') if r.random() < lleno else None for _ in range(6)]
    m = mundo_chico([None] * trasbordos, ini(), ini(), entrada=True)
    g = Gestor(m.tipos())
    verif = Gestor is GestorDeReservas
    eq = [nuevo('A', politica=politica, verificar_hueco=verif), nuevo('B', politica=politica, verificar_hueco=verif)]

    def mundo_vivo(t, m, g):
        if m.slots['E'].cubo is None and g.es_de('E') is None and r.random() < 0.03:
            m.slots['E'].cubo = r.choice('AB')
        for sal in ('SA', 'SB'):
            if m.slots[sal].cubo is not None and g.es_de(sal) is None:
                m.slots[sal].cubo = None                       # despacho
        if r.random() < 0.02:
            e = r.choice(eq)
            if e.pedidos < 2:
                e.pedidos += 1
    t_dl, dobles = correr(m, g, eq, ticks, eventos=mundo_vivo, ventana_deadlock=200)
    return dict(deadlock=t_dl is not None, colisiones=len(m.colisiones), dobles=len(dobles),
                hechas=sum(e.completadas for e in eq))


def prueba_operacion(n=20):
    print(f"4 · operación al azar: inventario inicial revuelto (80 %), un trasbordo, entradas y pedidos,"
          f" {n} semillas × 3000 ticks")
    filas = [('ordenada', GestorDeReservas, 'la buena'), ('tardia', GestorDeReservas, 'control: reserva tardía'),
             ('ordenada', GestorTonto, 'control: gestor tonto, sin cámara')]
    res = {}
    for pol, G, nom in filas:
        rr = [operacion(s, pol, G) for s in range(n)]
        res[nom] = dict(dl=sum(x['deadlock'] for x in rr), col=sum(x['colisiones'] > 0 for x in rr),
                        hechas=sum(x['hechas'] for x in rr) / n)
        print(f"    {nom:<34} deadlock en {res[nom]['dl']:>2}/{n} · con cubos chocados {res[nom]['col']:>2}/{n} · "
              f"tareas por corrida {res[nom]['hechas']:.0f}")
    buena = res['la buena']
    discrimina = res['control: reserva tardía']['dl'] > 0 and res['control: gestor tonto, sin cámara']['col'] > 0
    ok = buena['dl'] == 0 and buena['col'] == 0 and buena['hechas'] > 0 and discrimina
    print(f"    → {'PASA' if ok else 'FALLA'}: la buena sin deadlocks ni choques, y cada control falla en lo suyo"
          + ("" if discrimina else " (OJO: algún control no falló: la prueba no discrimina)"))
    return ok


# ── Prueba 5 · el caso de maje ───────────────────────────────────────────────
ESPERADA = ['CARRIL', 'RECTA', 'GIRO', 'ELEVA', 'APROXIMA', 'EXTIENDE', 'TOMA', 'RETRAE', 'RETROCEDE',
            'DESGIRA', 'TRANSITO'] * 2


def _correr_maje(rutas, hueco_dir, x3):
    m = Mundo({'H': Slot.hueco_en('A', hueco_dir, 'A'), 'SA': Slot.lugar('salida', 'A')})
    g = GestorDeReservas(m.tipos())
    A = Equipo('A', rutas=rutas, pose=(x3, 0.0, 'descarga'))
    A.pedidos = 1
    t = 0
    while A.completadas == 0 and t < 2000:
        A.tick(t, m, g); t += 1
    return A, m, t


def prueba_maje():
    import json
    import bahias
    print("5 · EL CASO DE MAJE: frente a 3L con las uñas hacia la descarga; el cubo de 5R a la descarga")
    tabla = json.load(open(os.path.join(fsm_rutas._AN, 'rutas_tabla.json'), encoding='utf-8'))['caso1']
    rutas = fsm_rutas.Rutas()
    x3 = sum(bahias.bahia_x(3)) / 2
    oks = []
    for hueco_dir in ('5 3 Ra', '5 3 Rb'):
        A, m, t = _correr_maje(rutas, hueco_dir, x3)
        estados = [h[1] for h in A.historial]
        seq = [e for i, e in enumerate(estados) if i == 0 or e != estados[i - 1]]
        mov = sum(1 for h in A.historial if h[1] in ('CARRIL', 'RECTA', 'GIRO', 'RETROCEDE', 'DESGIRA')) * rutas.tick
        plan = tabla[hueco_dir]
        t_cont = plan['ida']['tiempo'] + plan['vuelta']['tiempo']
        t_plan = sum(p['tiempo'] for _, p in plan['ida']['partes'] + plan['vuelta']['partes'])
        vuelta_ida = any(f == 'ORIGEN' and 'VUELTA' in x for f, _, x in A.maniobras)
        print(f"    {hueco_dir}: {' → '.join(seq)}")
        for fase, sid, txt in A.maniobras:
            print(f"        {fase:<7} {txt}")
        print(f"        cubo en la descarga: {'sí' if m.slots['SA'].cubo == 'A' else 'no'} · {t} ticks · "
              f"movimiento FSM {mov:.0f} s vs planificador {t_plan:.0f} s parando entre maniobras "
              f"({t_cont:.0f} s sin parar) "
              f"(ida {plan['ida']['largo']} m y {plan['ida']['cambios']} cambios de sentido, vuelta "
              f"{plan['vuelta']['largo']} m y {plan['vuelta']['cambios']})")
        oks.append(seq[:len(ESPERADA)] == ESPERADA and m.slots['SA'].cubo == 'A'
                   and abs(mov - t_plan) <= 0.25 * t_plan
                   and vuelta_ida == (hueco_dir == '5 3 Ra'))       # a la Ra se llega dando la vuelta; a la Rb no
    # CONTROL: rutas que dejan entrar a cualquier posición con cualquier rumbo. Si con ellas la Ra
    # TAMBIÉN diera la vuelta, la prueba no estaría mirando el rumbo
    falsa = fsm_rutas.Rutas()
    for k in list(falsa.T['salidas']):
        if falsa.T['salidas'][k] is None:
            otro = k.split('|')[0] + ('|adentro' if k.endswith('descarga') else '|descarga')
            falsa.T['salidas'][k] = falsa.T['salidas'][otro]
    A, m, t = _correr_maje(falsa, '5 3 Ra', x3)
    vuelta_falsa = any(f == 'ORIGEN' and 'VUELTA' in x for f, _, x in A.maniobras)
    print(f"    CONTROL rutas sin rumbo (a la Ra se entra de cualquier lado): vuelta en la ida: "
          f"{'sí (OJO: no discrimina)' if vuelta_falsa else 'no → la prueba sí ve el rumbo'}")
    ok = all(oks) and not vuelta_falsa
    print(f"    → {'PASA' if ok else 'FALLA'}: la FSM recorre las 22 etapas, da la vuelta donde la da el "
          f"planificador, y su tiempo de movimiento coincide con el del planificador")
    return ok


def correr_todas(titulo):
    print(f"══ {titulo} ══")
    r = [prueba_carrera()]
    print(); r.append(prueba_deadlock())
    print(); r.append(prueba_paro()); r.append(pruebas_extra())
    print(); r.append(prueba_operacion())
    print()
    return r


def main():
    MODO['rutas'] = None
    r = correr_todas("con la tabla fija TICKS (la de clases/fsm.html)")
    MODO['rutas'] = fsm_rutas.Rutas()
    r += correr_todas("con DIRECCIONES DE BAHÍA y duraciones del planificador (fsm_rutas.py)")
    r.append(prueba_maje())
    print("\nRESULTADO:", "PASA" if all(r) else "FALLA")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
