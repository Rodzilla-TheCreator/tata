# Encargo — rutas entre bahías (Hybrid A* general, con uñas) y la FSM con direcciones de bahía

> **HECHO 05-nov-2026 en la i3.** Resultados, controles y lo que se apartó del encargo en
> **`rutas_resultados.md`**. Lo principal:
> - **Con uñas, ningún 90° cabe con todo el equipo dentro de 3.00 m** (ancho a rumbo 3.04 m). Se
>   modela que las uñas pasan la cara dentro de la luz de la bahía (`PROF_BAHIA`, SUPUESTO).
> - **Punta de uña a 0–5 cm de la cara, no a 8–15:** sobran 10 cm entre culo y punta.
> - **La `a` se entra con las uñas hacia adentro, la `b` hacia la descarga.**
> - **Caso de maje:** sí, va de reversa. A la 5 3 Rb, 6.1 m sin cambios de sentido; a la 5 3 Ra,
>   11.5 m con 2.
> - **La FSM con direcciones pasa** las 4 pruebas viejas y la del caso de maje.

**Para la sesión que corre en i3.** Autocontenido. Corre en i3, **sin montacargas**: Python
(`numpy`, `matplotlib`). Lenguaje y comentarios en **español**, al estilo del repo. Leé
`CLAUDE.md` primero: manda sobre todo lo de abajo.

## Por qué

Hoy `analisis/planificador_giro.py` resuelve **un solo caso**: carril → giro de 90°. Y su
`silueta()` **no tiene uñas** (defecto anotado en `CLAUDE.md`). La FSM de coordinación
(`percepcion/fsm_estados.py`, hecha el 02-nov) maneja huecos como IDs abstractos y duraciones
fijas por paso. Falta lo que une las dos cosas: **ir de cualquier pose a cualquier bahía, con la
silueta real**, y que la FSM hable en **direcciones de bahía**.

La pregunta que lo disparó (maje, 05-nov): el equipo está frente a la bahía `3L`, mirando hacia
la zona de descarga; la tarea es llevar un cubo de la `5R` a la descarga. ¿Cómo se mueve?
¿Va de reversa? La respuesta tiene que salir **del planificador**, no de razonarla.

## 1 · Direcciones de bahía: `x y s`

Notación de maje: **`x` = posición horizontal** (bahía contada desde la zona de descarga hacia
adentro del pasillo, 1, 2, 3…), **`y` = nivel** (altura), **`s` = lado**, `L` o `R`, **visto desde
la zona de descarga mirando hacia adentro del pasillo**.

- **Ojo:** en cada bahía de **2.35 m** entran **dos** IBC por nivel (cara de 1.00 m al pasillo, 35
  cm sobrantes, `CLAUDE.md`). Agregá un subíndice de posición dentro de la bahía (p. ej. `a` =
  la más cercana a la descarga, `b` = la más lejana), **sin romper** la notación `x y s` de maje.
  Documentá la decisión.
- **Alturas por nivel:** usá la tabla de `CLAUDE.md` (Corregido en campo → El rack): N1-A al piso,
  N1-B sobre cubo, N2…N5, con **Base / Entrada / Agarre**. `y` tiene que mapear a esas filas.
- **Parámetros que no están medidos** (márcalos `SUPUESTO` y hacelos configurables): dónde está la
  zona de descarga respecto de la bahía 1 (`X0`), cuántas bahías tiene el pasillo (`N`), velocidad
  de elevación.
- Función: `pose_de(direccion) -> (x, y, θ, altura_uña)`: la **pose objetivo** del equipo para
  esa bahía: uñas encarando el rack `s`, punta de uña a 8–15 cm de la cara del rack (como `meta()`
  en `almacen-nuevo/planificar_giro_318.py`), alineado al centro de la posición `a`/`b`.

## 2 · Los tres carriles

| Carril | Dónde | Para qué |
|---|---|---|
| **giro hacia R** | eje de carga a **85 cm del rack L** | entrar a bahías del lado R |
| **giro hacia L** | eje de carga a **85 cm del rack R** | entrar a bahías del lado L |
| **central** | eje del pasillo (1.50 m) | traslado |

85 cm es la línea recomendada; 75 cm es la que usa el operador y da 1 cambio de sentido
(`CLAUDE.md`, El giro). Que ambos sean parámetro. El cambio de carril es la curva en S del paso
`CARRIL` (`sec/gen_fsm.py`).

## 3 · El planificador general — Hybrid A*, con uñas

Entregable: **`analisis/planificador_rutas.py`**.

- **Pose inicial y pose final cualquiera** `(x, y, θ)`, con cambios de sentido permitidos (el
  costo de cada cambio es parámetro). Devuelve la secuencia de tramos: sentido (adelante = uñas
  primero / reversa), largo, cambios de sentido, y una estimación de tiempo con el sobre de
  **1.5 m/s** (`CLAUDE.md`).
- **Silueta con uñas:** portá la de `almacen-nuevo/planificar_giro_318.py` (largo total 2.90 con
  uñas, uñas de 0.13 de ancho a ±0.30) a **pasillo de 3.00 m**. Usá **`L_ANCHO = 0.48`** (medido
  el 18-sep; `planificador_giro.py` todavía tiene 0.20, desmentido). `XPIV = 1.50` es derivado:
  barré **1.30–1.60** como se hizo el 18-sep.
- **Misma cinemática** que `planificador_giro.py` / `percepcion/odometria.py` (eje de carga como
  referencia, rueda directriz atrás a `WB = 1.562`). Si algo contradice al planificador viejo,
  **anotalo** con tabla decía / es / qué lo tumbó.

## 4 · Los casos que tiene que contestar

1. **El de maje:** inicio en `3L` (en el carril central, a la altura de la bahía 3), **mirando
   hacia la zona de descarga**, vacío. Tarea: tomar el cubo de `5R` (nivel a elección, p. ej. N3)
   y dejarlo en la descarga. Imprimí la secuencia completa: tramos, sentido de cada uno, cambios de
   carril, giros, cambios de sentido, largo y tiempo. Y una **figura** del recorrido
   (`analisis/ruta_3L_5R.png`).
2. **Barrido:** desde una pose canónica (en la descarga mirando hacia adentro), para **cada bahía
   x = 1…N y cada lado** → ¿llega?, cambios de sentido, largo. Y la salida: desde cada bahía
   alineada, salir **hacia la descarga** y **hacia el fondo**.
3. **El 180°:** confirmá con la silueta con uñas que el 180° **dentro del pasillo** no entra
   (`CLAUDE.md`: 3.14 m barrido > 3.00), y mostrá que **dos 90° (entrar alineado a una bahía y
   salir hacia el otro lado) dan el mismo resultado**: cambiar el sentido de viaje sin 180°.

**Controles de falsación** (regla dura del repo — la prueba tiene que poder fallar):
- **Quitar las uñas** de la silueta → tiene que volver a lo de solo chasis (ventana de carriles
  75–150 cm). Si quitar las uñas no cambia nada, no se están modelando.
- **Pasillo de 2.80 m** → tiene que fallar o necesitar más cambios de sentido. Si sale igual, el
  pasillo no está restringiendo.

## 5 · La FSM con direcciones de bahía

En `percepcion/fsm_estados.py` (y lo que toque de `reserva.py` / `sim_coordinacion.py`):

- Los huecos pasan a ser **direcciones `x y s`** (+ `a`/`b`), con su altura de la tabla.
- `CARRIL` elige el carril según `s` (giro hacia R o hacia L); el traslado va por el central.
- Las duraciones de `RECTA`, `GIRO`, `DESGIRA`, `RETROCEDE` y `ELEVA` salen del planificador y de
  la tabla de alturas, **no** de la tabla fija `TICKS`. Lo que no esté medido, `SUPUESTO`.
- **Las pruebas que ya pasan tienen que seguir pasando** (carrera, deadlock de `gen_fsm.py:40`,
  paro en altura, operación al azar, con sus controles). Agregá una que corra el caso de maje
  (`3L` → `5R` → descarga) por la FSM y verifique la secuencia de estados.

## Entregables

- `analisis/bahias.py` — direcciones `x y s` (+ `a`/`b`) → pose objetivo y altura.
- `analisis/planificador_rutas.py` — Hybrid A* general con uñas.
- `analisis/ruta_3L_5R.png` y `analisis/rutas_resultados.md` con las tablas de los casos 1–3 y
  los controles.
- `percepcion/fsm_estados.py` (+ lo que toque) actualizado, con sus pruebas pasando.
- Una línea en `CLAUDE.md` (tabla de carpetas o «Lo que falta») apuntando a lo nuevo.
- Commit y push a `main` con mensajes claros.

## Lo que NO es esta tarea

- No es tocar `sim-web/` ni el fierro (integrar va después).
- No es el EKF ni las cámaras.
- No es medir nada: los números de campo salen de `CLAUDE.md`; lo que falte es `SUPUESTO`.

## Referencias

- `CLAUDE.md` — geometría, El giro, El rack (alturas), sobre de velocidad, el 180°.
- `analisis/planificador_giro.py` — Hybrid A* actual (solo chasis, un caso).
- `almacen-nuevo/planificar_giro_318.py` — silueta **con uñas** y `meta()` frente al rack.
- `percepcion/odometria.py` — la misma cinemática, comprobada contra el planificador.
- `percepcion/fsm_estados.py`, `reserva.py`, `sim_coordinacion.py`, `percepcion/LEEME.md`
  (sección FSM) — la FSM hecha el 02-nov.
- `sec/gen_fsm.py` — el diagrama de la FSM (selector de tarea + secuencia de movimiento).
