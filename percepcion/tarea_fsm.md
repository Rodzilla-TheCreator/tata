# Encargo — FSM de coordinación: estados de bloqueo, reserva y falla/reanudación

**Para la sesión que corre en i3.** Autocontenido: no necesitás el chat donde se originó.
Implementá y validá **en i3**, con **simulación en memoria** — NO hace falta el montacargas, ni
Isaac, ni GPU, ni el bus. Solo `python` puro (sin dependencias; `pytest` opcional para los tests).
Lenguaje y comentarios en **español**, al estilo del repo.

Esto es la **otra mitad del software del kit**, a la par del EKF (`percepcion/tarea_ekf.md`): el
EKF dice *dónde estoy*; esta FSM dice *qué hago y cuándo puedo hacerlo sin chocar con el otro
equipo*. Son los puntos **#3 y #4** de `CLAUDE.md` → "Lo que falta, en orden".

## El problema que resuelve

Hoy la FSM del simulador (`sim-web/actual_tpl.html`) usa **`LIBRE` de comodín**: cuando un equipo
no tiene tarea, "está libre", y nada modela que esté **esperando** algo concreto. Y el selector de
tarea (`sec/gen_fsm.py`) ya tiene anotado a mano el agujero (línea 40):

> *trasbordo lleno → A se bloquea: no puede soltar lo que no es suyo*

Dos equipos (sector **A** y sector **B**) comparten dos recursos finitos: las **posiciones de
trasbordo del fondo** y los **huecos de rack**. Sin coordinación, dos cosas malas pasan:

1. **Carrera por el recurso:** A y B deciden a la vez usar la **última** posición de trasbordo. Hoy
   nada lo impide: los dos creen que es suya.
2. **Deadlock:** A no puede soltar lo que no es suyo porque el trasbordo está lleno; B no vacía el
   trasbordo porque está esperando a que A libere un hueco. Se quedan viéndose.

Y aparte, la **reanudación tras falla** no existe: si entra un paro con el **pantógrafo extendido en
altura**, ese paso **no se puede reanudar a la mitad** — hay que retraer primero, en orden.

## Entregables (en `percepcion/` — portable, corre en maquinón en producción)

1. **`fsm_estados.py`** — la máquina de estados de **un** equipo, con los estados de espera como
   estados **de verdad**, no como `LIBRE`:
   - `LIBRE` (sin tarea, evaluando el selector) — se conserva, pero deja de ser comodín.
   - `ESPERA_PEDIDO` — hay trabajo pero falta la orden/el pedido.
   - `ESPERA_HUECO` — tiene carga, pero no hay hueco destino libre (o no se lo reservaron).
   - `ESPERA_TRASBORDO` — tiene que soltar en el trasbordo y está lleno / sin reserva.
   - más los estados de movimiento que ya existen (`CARRIL`, `RECTA`, `GIRO`, `ELEVA`, `APROXIMA`,
     `EXTIENDE`, `TOMA`, `RETRAE`, `RETROCEDE`, `DESGIRA`, `TRANSITO`) — reusá los nombres del
     simulador (ver referencias), no inventes otros.
   - Transiciones explícitas: de un estado de espera **solo se sale** cuando el recurso que se
     esperaba quedó disponible **y reservado a mi nombre**.

2. **`reserva.py`** — el **protocolo de reserva** (exclusión mutua) sobre los recursos compartidos:
   - Un `GestorDeReservas` con pool de posiciones de trasbordo y de huecos.
   - `reservar(equipo, recurso) -> bool`: **atómico**. Si dos equipos piden el mismo recurso, **gana
     exactamente uno**; el otro recibe `False` y se queda en su estado de espera.
   - `liberar(equipo, recurso)`, y una regla **anti-deadlock**: definí un **orden total** de petición
     de recursos (p.ej. siempre reservar *hueco-destino* antes de tocar el trasbordo) o un
     mecanismo de **expropiación/timeout** con justificación escrita. Documentá cuál elegiste y por
     qué rompe el ciclo de espera.

3. **`fsm_falla.py`** (o dentro de `fsm_estados.py`, como prefieras) — **falla y reanudación**:
   - Marcá cada paso de movimiento como **reanudable** o **NO reanudable a la mitad**
     (`EXTIENDE`/`TOMA` en altura = no reanudable; hay que **retraer en orden** antes de rendirse).
   - Ante un evento `PARO` o `ARUCO_PERDIDO` o `HUECO_OCUPADO`, la FSM entra en un estado de falla y
     sabe **a qué estado seguro volver** y **qué secuencia de deshacer** correr primero (nunca
     bajar/soltar a ciegas; nunca retraer saltándose pasos).

4. **`sim_coordinacion.py`** — simulación en memoria de **A y B a la vez** pidiendo tareas contra un
   mapa de recursos chico, con el reloj por `tick`. Corre varios escenarios y **compara** con y sin
   el gestor de reservas.

## Criterio de aceptación — con control de falsación (regla dura del repo)

Cada prueba tiene que **poder fallar**. Imprimí el resultado de las tres:

- **Carrera por la última posición de trasbordo:** lanzá a A y B a reservarla **en el mismo tick**.
  - *Con* `GestorDeReservas`: **exactamente uno** la obtiene; el otro queda en `ESPERA_TRASBORDO`.
  - *Control (sin gestor, o con un gestor "tonto" que siempre dice sí):* **los dos** creen que es
    suya → colisión detectada. Si quitar el gestor **no** produce la colisión, el test no probó
    nada: revisá.
- **Deadlock A↔B:** armá el ciclo (A espera hueco que tiene B, B espera trasbordo que necesita A).
  - *Con* la regla anti-deadlock: el sistema **progresa** (alguien avanza, nadie se queda infinito).
  - *Control (sin la regla):* detectá el **deadlock** (ningún equipo avanza en N ticks) y reportalo.
- **Paro con pantógrafo extendido en altura:** inyectá `PARO` en estado `EXTIENDE`/`TOMA`.
  - La FSM **no** rinde el control sin antes correr la secuencia de **retraer en orden**; termina en
    un estado seguro (`TRANSITO`/`PARADA`) con el pantógrafo a 0.
  - *Control:* si permitís reanudar desde la mitad de `EXTIENDE`, mostrá por qué es inseguro
    (quedaría el pantógrafo afuera en altura). El test confirma que la FSM lo impide.

## Convenciones y límites

- Python puro de la stdlib. `pytest` solo si querés; si no, un `if __name__ == "__main__"` que corra
  los tres escenarios y los imprima sirve igual.
- **No toques `sim-web/actual_tpl.html` todavía.** Esto es el modelo de referencia, limpio y
  testeable, en `percepcion/`. Integrarlo al simulador web (o al fierro) es un paso posterior.
- Reusá los **nombres de estado y de paso** del simulador para que después empalme sin renombrar.
- Si algo contradice lo escrito, **anotalo** (regla "no se borra el camino" de `CLAUDE.md`): lo
  vigente arriba, qué lo tumbó, abajo.

## Referencias en el repo

- `sim-web/actual_tpl.html` — la FSM viva. `est` es el estado; mirá la lista de `PASOS` (línea ~319)
  y el gran `if (u.est===...)` (línea ~370 en adelante). De ahí salen los nombres de los estados de
  movimiento. `LIBRE` es el comodín que hay que descomponer.
- `sec/gen_fsm.py` — el **diagrama** de la FSM en dos capas: el **selector de tarea**
  (`TRASBORDO`/`PEDIDO`/`ENTRADA`/`PASE`/`REUBICAR`, evaluado en orden) y la **secuencia de
  movimiento**. La línea 40 es el peligro que este encargo resuelve.
- `CLAUDE.md` → "Lo que falta, en orden" **#3** (estados de bloqueo y deadlock, protocolo de
  reserva) y **#4** (estados de falla y reanudación; "pasos que no se pueden reanudar a la mitad").
- `datos/sectorA.json` — el mapa real del sector A (huecos, niveles) por si querés un mapa de
  recursos realista en vez de uno de juguete; no es obligatorio.

## Lo que NO es esta tarea

- No es tocar el simulador web ni el fierro (integración = después).
- No es la planificación de trayectoria (ya está en `analisis/planificador_giro.py`).
- No es el EKF (ese es `percepcion/tarea_ekf.md`). Esta FSM **consume** la pose, no la calcula.


---

**HECHO 02-nov-2026 en la i3.** Las tres pruebas y sus controles pasan, más una cuarta de operación al azar que discrimina (tardía: deadlock 20/20; tonto: choques 19/20; buena: 0/0). Resultados y lo que cambió respecto del encargo (selector «primera que se puede», espera con uñas vacías re-evalúa): `percepcion/LEEME.md`, sección «FSM de coordinación A/B».
