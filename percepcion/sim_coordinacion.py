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
# ─────────────────────────────────────────────────────────────────────────────
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fsm_estados import ESPERAS, Equipo, Mundo, Slot          # noqa: E402
from reserva import GestorDeReservas, GestorTonto             # noqa: E402

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PASO_NIVEL = 1.38        # m entre plataformas (CLAUDE.md, el rack)


def mundo_chico(trasbordos, huecosA, huecosB, entrada=False):
    s = {}
    for i, c in enumerate(trasbordos):
        s[f"T{i}"] = Slot('trasbordo', None, 0.0, c)
    for i, c in enumerate(huecosA):
        s[f"HA{i}"] = Slot('hueco', 'A', (i % 4) * PASO_NIVEL, c)
    for i, c in enumerate(huecosB):
        s[f"HB{i}"] = Slot('hueco', 'B', (i % 4) * PASO_NIVEL, c)
    if entrada:
        s["E"] = Slot('entrada', 'A', 0.0, None)
        s["SA"] = Slot('salida', 'A', 0.0, None)
        s["SB"] = Slot('salida', 'B', 0.0, None)
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
        A, B = Equipo('A', verificar_hueco=verif), Equipo('B', verificar_hueco=verif)
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
        A, B = Equipo('A', politica=pol), Equipo('B', politica=pol)
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
    m = Mundo({'T0': Slot('trasbordo', None, 0.0, 'A'), 'HA0': Slot('hueco', 'A', 2 * PASO_NIVEL, None)})
    g = GestorDeReservas(m.tipos())
    A = Equipo('A', falla=falla)
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
    print("3 · PARO con el pantógrafo extendido en altura (fase DESTINO, hueco a 2.76 m)")
    oks = []
    for paso in ('EXTIENDE', 'TOMA'):
        A, m, marca, cedio, tras = un_paro('correcta', paso)
        exts = [h[2] for h in tras]
        monotono = all(b <= a + 1e-9 for a, b in zip(exts, exts[1:]))
        baja_afuera = any(h1[3] < h0[3] - 1e-9 and h0[2] > 1e-9 and h1[4] == 'deshacer' and h1[1] != 'DESHACE_TOMA'
                          for h0, h1 in zip(tras, tras[1:]))
        secuencia = [x[0] for x in A.log_deshacer]
        toma_antes = paso != 'TOMA' or (secuencia[:1] == ['DESHACE_TOMA'] and A.log_deshacer[1][2] == round(2 * PASO_NIVEL, 4))
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
    m = Mundo({'T0': Slot('trasbordo', None, 0.0, 'A'), 'HA0': Slot('hueco', 'A', PASO_NIVEL, None)})
    g = GestorDeReservas(m.tipos()); A = Equipo('A'); hecho = False
    for t in range(400):
        A.tick(t, m, g)
        if not hecho and A.est == 'EXTIENDE' and A.fase == 'DESTINO' and A.paso_t == 2:
            A.evento('ARUCO_PERDIDO'); hecho = True
    print(f"        ARUCO_PERDIDO: deshace, re-aproxima y termina → tareas hechas {A.completadas}, cubo en HA0: "
          f"{'sí' if m.slots['HA0'].cubo == 'A' else 'no'}")
    ok1 = A.completadas == 1 and m.slots['HA0'].cubo == 'A'
    m = Mundo({'T0': Slot('trasbordo', None, 0.0, 'A'), 'HA0': Slot('hueco', 'A', PASO_NIVEL, None),
               'HA1': Slot('hueco', 'A', 2 * PASO_NIVEL, None)})
    g = GestorDeReservas(m.tipos()); A = Equipo('A'); puesto = False
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
    eq = [Equipo('A', politica=politica, verificar_hueco=verif), Equipo('B', politica=politica, verificar_hueco=verif)]

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


def main():
    r = [prueba_carrera()]
    print(); r.append(prueba_deadlock())
    print(); r.append(prueba_paro()); r.append(pruebas_extra())
    print(); r.append(prueba_operacion())
    print("\nRESULTADO:", "PASA" if all(r) else "FALLA")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
