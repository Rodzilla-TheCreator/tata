# Rutas entre bahías — resultados (05-nov-2026, en la i3)

Encargo: `tarea_rutas_bahias.md`. Código: `bahias.py` (direcciones `x y s`), `planificador_rutas.py`
(Hybrid A* con uñas). Todo sale de `py analisis/planificador_rutas.py --v1` (~5 min en la i3), que escribe
`rutas_tabla.json` (lo lee la FSM) y `ruta_3L_5R.png`.

> **Rehecho el mismo 05-nov (tarea de visibilidad).** La primera versión **pegaba piezas con
> saltos escondidos**. El traslado cerraba con una recta sobre el rumbo que traía, con hasta 2–3°
> de error, y `unir()` arrancaba la pieza siguiente desde su pose exacta. Reproducidas de forma
> continua, las rutas llegaban corridas de 17 cm (mediana) a **1.28 m** (`barrido_7Lb`).
>
> **Ahora el traslado cierra exacto:**
> - una curva en S de dos arcos (Newton sobre la cinemática exacta) más una recta;
> - si la meta viene inclinada, un arco final en forma cerrada;
> - `unir()` falla si hay un salto, y cada ruta reporta `salto_max_m`. El máximo hoy es **8e-6 m**.
>
> **Los números de abajo son los nuevos.** Cambiaron poco en las idas, y más en las rutas que dan
> la vuelta en la zona: **la vuelta pasa a costar 3 cambios de sentido**. Lo que no cambió: el
> ancho a rumbo, la asimetría a/b, los controles y los barridos de XPIV y de profundidad.

```
py analisis/bahias.py                 # direcciones → pose objetivo y altura
py analisis/planificador_rutas.py --v1  # casos 1–3, controles, barridos → rutas_tabla.json + la figura
py percepcion/sim_coordinacion.py     # la FSM, con tabla fija y con direcciones; termina en PASA/FALLA
```

## Lo que ordena todo: con uñas, ni el 90° ni el 180° caben en 3.00 m con todo dentro del pasillo

Lo que la silueta ocupa a lo ancho del pasillo **depende solo del rumbo**, no de dónde esté el
equipo: trasladarlo no lo cambia. Girar de 0° a 90° obliga a pasar por todos los rumbos del medio.

| Rumbo respecto del eje | 0° | 45° | 60° | 65° | **70–75°** | 80° | 85° | 90° |
|---|---|---|---|---|---|---|---|---|
| con uñas, vacío (m) | 1.32 | 2.69 | 2.96 | 3.01 | **3.03** | 3.01 | 2.97 | 2.90 |
| con uñas y el IBC (m) | 1.32 | 2.78 | 3.03 | 3.07 | **3.08** | 3.04 | 2.98 | 2.90 |
| sin uñas, chasis + patas (m) | 1.32 | 2.38 | 2.48 | 2.48 | 2.46 | 2.35 | 2.28 | 2.18 |

- **Con uñas el máximo es 3.036 m a 73°**. Con 5 cm de holgura por lado (2.90 útiles) **no cabe
  ningún rumbo entre 56° y 89.5°**. Con el IBC el máximo sube a **3.078 m** y la franja a 51–89.5°.
- Por lo tanto **ningún** giro de 90° (ni de 180°) existe con el equipo entero dentro del pasillo,
  por ningún camino. El Hybrid A* lo confirma por su cuenta: 0 de 10 carriles (control abajo).
- **El operador gira 90° todos los días. El modelo está incompleto, no la máquina.** Lo que falta
  modelar es la bahía: **al girar, las uñas (y el cubo) pasan la cara del rack**, dentro de la luz
  de la bahía a la que se entra o de la que se sale. El chasis nunca. `sec/gen_svg.py` ya dibujaba
  «uñas N cm dentro de la bahía al girar» con el modelo viejo.
- Cuánto pasan es **`PROF_BAHIA`, SUPUESTO = 0.20 m**. Por geometría hacen falta al menos 8.6 cm
  vacío y 12.8 cm cargado. Por búsqueda: **con 10 cm no gira nada, desde 15 cm sí** (tabla abajo).

**Lo que se mide para cerrarlo** (sin preguntarle a nadie): filmar desde arriba al operador
entrando a una bahía en N1 y en N3. Hay que ver **a qué altura van las uñas mientras gira**,
**cuánto pasan la cara** y **qué hay en la luz a esa altura**. Y medir el **radio del culo**: un
culo redondeado baja el ancho a rumbo. El modelo lo tiene en ángulo recto.

## Corregido (decía / es / qué lo tumbó)

| Decía | Es | Qué lo tumbó |
|---|---|---|
| «Girar cargado es igual que girar vacío» (`CLAUDE.md`, El giro) | **Solo para el chasis.** Con las uñas modeladas, el IBC (1.00 de ancho contra 0.73 de las uñas) suma **4 cm** al ancho a rumbo: 3.078 contra 3.036 | `ancho_a_rumbo()` con y sin `cargado` |
| El 180° no entra (chasis + uñas, 3.14 m a 75°), el 90° sí | **Los dos fallan dentro del pasillo**: es la misma franja de rumbos. Lo que separa al 90° del 180° es que el 90° termina en una bahía y usa su luz | el ancho a rumbo no depende del camino |
| La punta de uña a 8–15 cm de la cara, como `meta()` de `almacen-nuevo/` | **0–5 cm** (meta 3). De frente al rack, el equipo mide 2.90 de culo a punta y sobran **10 cm en total**; con 5 cm de holgura en el culo, a la punta le quedan 5 | `bahias.GAP_OBJ` |
| Solo chasis, peor caso 2.31 m | **2.48 m** con `L_ANCHO = 0.48` medido y las patas delante de la torre | la silueta del 318 con el dato del 18-sep |
| Las rutas compuestas son continuas (primera versión de este archivo) | **Tenían saltos escondidos entre piezas: hasta 1.28 m.** Ahora el cierre es exacto y el salto máximo es 8e-6 m | reproducir las primitivas de forma continua para la visibilidad: las llegadas no caían en el hueco. `saltos()` y el `assert` de `unir()` lo vigilan |
| Entrar a una bahía es lo mismo venga de donde venga | **Depende de la posición y del rumbo de viaje.** A la `a` (pegada al poste del lado de la descarga) solo se entra y se sale con las **uñas hacia adentro**; a la `b`, solo con las **uñas hacia la descarga**; por el **centro** de la bahía, en los dos sentidos | las uñas necesitan la luz a mitad del giro y el poste de al lado se la quita. Simétrico: la `b` es el espejo de la `a` |

## Caso 1 · el de maje: frente a 3L, uñas hacia la descarga; el cubo de 5R (N3) a la descarga

![ruta](ruta_3L_5R.png)

**¿Va de reversa?** **Sí.** Viene mirando a la descarga y el hueco está más adentro: hace el
traslado en reversa, con el culo primero. Lo que cambia todo es **cuál de los dos IBC de la 5R**.

| Hueco | Ida (vacío) | Vuelta a la descarga (con el IBC) | Total |
|---|---|---|---|
| **5 3 Rb** | **6.1 m · 0 cambios · 11 s**: un solo tramo en reversa; se corre al carril de giro (85 cm del rack L) y gira 90° metiendo las uñas a la 5R | **14.5 m · 0 cambios · 17 s**: sale girando con las uñas hacia la descarga y va de frente | **20.6 m · 28 s** |
| **5 3 Ra** | **12.1 m · 2 cambios · 26 s**: entra en reversa al **centro** de la 5R (8.2 m), sale de frente girando hacia adentro, y entra en reversa a la `a` | **19.9 m · 4 cambios · 27 s**: sale con las uñas hacia adentro (la `a` no deja otra), va en reversa hasta la zona, da la vuelta ahí (2 cambios) y llega de frente | **32.0 m · 52 s** |

Arriba van los vertical de la tabla de `CLAUDE.md`: ELEVA a 3.947 m, unos **7.2 s** a 0.55 m/s
(SUPUESTO). Después EXTIENDE, TOMA +6 cm, RETRAE y TRANSITO: bajar de 4.007 m, unos **7.3 s**.

**Lo que esto le dice a la FSM:** elegir `a` o `b` según el rumbo con que llega el equipo ahorra la
vuelta, que cuesta más que el traslado entero. **No está hecho.** Hoy el destino es el primer hueco
libre; la FSM paga la vuelta y la deja anotada en `maniobras`.

## Caso 2 · barrido: desde la descarga, uñas hacia adentro, a cada bahía

Pose de arranque (0, 0, 0°). Siete bahías por lado (SUPUESTO, del DXF). El lado L y el R dan lo mismo.

| Bahía | Llega a `a` | Llega a `b` | Sale de `a` | Sale de `b` |
|---|---|---|---|---|
| 1 | 4.5 m · 1 cambio · 8 s | 9.4 m · 3 · 17 s, **vuelta en la zona** | solo **al fondo** (1 cambio) | solo **a la descarga** (0) |
| 2 | 11.3 · 1 · 16 s | 10.2 · 3 · 18 s, vuelta en la zona | solo al fondo (0) | solo a la descarga (0) |
| 3 | 13.8 · 1 · 17 s | 12.7 · 3 · 19 s, vuelta en la zona | ídem | ídem |
| 4 | 16.1 · 1 · 19 s | 15.1 · 3 · 21 s, vuelta en la zona | ídem | ídem |
| 5 | 18.7 · 1 · 21 s | 17.6 · 3 · 23 s, vuelta en la zona | ídem | ídem |
| 6 | 21.2 · 1 · 23 s | 20.1 · 3 · 25 s, vuelta en la zona | ídem | ídem |
| 7 | 23.7 · 1 · 24 s | 22.5 · 3 · 26 s, vuelta en la zona | ídem | ídem |

Las 28 llegan. Las salidas de la `a` hacia la descarga y de la `b` hacia el fondo **no existen**
con `PROF_BAHIA = 0.20`. La vuelta en la zona cuesta **2 cambios de sentido** y unos **2–4 s** más
que ir directo a la `a` de la misma bahía.

## Caso 3 · el 180°

| | Resultado |
|---|---|
| 180° dentro del pasillo, **con uñas** | **no existe**: franja de 56–89.5° fuera de 2.90 m; la búsqueda agota 15 000 expansiones |
| 180° dentro del pasillo, sin uñas (control) | sí: 1.2 m, 1 cambio. El chasis solo cabe a todo rumbo (máx. 2.48 m) |
| **Dos 90° por el centro de una bahía** (`4 Lc`) | **sí: 7.8 m, 2 cambios, 18 s**. Entra en reversa con las uñas hacia adentro, sale de frente con las uñas hacia la descarga. Cambia el sentido de viaje sin 180° |

## Controles de falsación

| Control | Esperado | Dio |
|---|---|---|
| **Quitar las uñas** (giro de 90° desde el carril, meta vieja de `planificador_giro.py`) | volver a la ventana de solo chasis, 75–150 cm | **75–150 cm, todos con 0 cambios**; 70 cm choca al arrancar (patas a 2 cm). El viejo daba 1 cambio en 75 cm, con otra silueta de patas |
| Las mismas uñas, **sin bahía abierta** | ningún carril | **0 de 10** (la búsqueda coincide con la prueba de forma) |
| Con uñas **y** la bahía abierta | algún carril | **75–150 cm**, 0 cambios, a `4 La` y a `4 Lb` |
| **Pasillo de 2.80 m** | fallar o más cambios | **las 6 salidas fallan** (`4 La/Lb/Lc`, los dos rumbos) |
| FSM con rutas «sin rumbo» (a la `a` se entra de cualquier lado) | sin vuelta en el caso de maje | sin vuelta: la prueba 5 sí mira el rumbo |

## Barridos de lo que no está medido

**`XPIV`** (cambia el tope de dirección: 69.5° a 1.30, 84° a 1.60):

| XPIV | `a` sale adentro / descarga | `b` adentro / descarga | centro, los dos |
|---|---|---|---|
| 1.30 | 3 cambios / **no** | **no** / 3 cambios | 3 cambios |
| 1.40 | 1 / **no** | **no** / 1 | 1 |
| 1.50 | 0 / **no** | **no** / 0 | 0 |
| 1.60 | 0 / 1 | 1 / 0 | 0 |

La asimetría a/b se mantiene hasta 1.50. Con 1.60 desaparece, a costa de un cambio de sentido.
El 18-sep, solo chasis, «la forma domina al pivote». **Con uñas ya no**: el `XPIV` decide
cuántos cambios cuesta cada giro. Medirlo con plomada vuelve a ser necesario para planificar,
no solo para el control fino.

**`PROF_BAHIA`**: con 0.05 y 0.10 no sale nada. De 0.15 a 0.30, lo de la tabla de arriba. Con 0.40,
la `a` también sale hacia la descarga (1 cambio). **El resultado de la sección «Corregido» depende
de este número, que no está medido.**

## La FSM con direcciones (`percepcion/fsm_rutas.py`)

`py percepcion/sim_coordinacion.py` corre las 4 pruebas **dos veces**: con la tabla fija (los
números de `clases/fsm.html` no se movieron: deadlock en el tick 128, 62 tareas por corrida) y con
direcciones de bahía, donde las duraciones salen de `rutas_tabla.json`. Con direcciones también
pasan las cuatro: deadlock tardío en el tick 164, 19/20 en la operación al azar, tonto con choques en
19/20 y la buena en 0/0. La quinta es el caso de maje: las 22 etapas en orden, el cubo en la descarga,
la vuelta en la ida a la Ra y no a la Rb, y el tiempo de movimiento:

| | FSM | Planificador parando entre maniobras | Planificador sin parar |
|---|---|---|---|
| 5 3 Ra | 60 s | 54 s | 52 s |
| 5 3 Rb | 34 s | 31 s | 28 s |

La prueba 5 al principio **fallaba** (69 s y 40 s). Había dos causas:
1. **Un bug:** la RECTA volvía a contar los ~4 m que el CARRIL ya avanza mientras cambia de carril.
2. **Una comparación mal hecha:** la FSM termina cada paso quieta y se comparaba contra el plan
   continuo. Ahora se compara contra el planificador parado entre las mismas maniobras, con el
   mismo ±25 %, sin mover el umbral.

Lo que queda (+10 a +11 %) es redondeo a ticks y los pasos de 1 tick. **Parar entre pasos es lo que
cuesta la FSM por pasos:** hasta un 20 % contra el movimiento continuo.

## SUPUESTOS (todos parámetro)

| | Valor | De dónde |
|---|---|---|
| `N` bahías por lado | 7 | fila de 17.41 m del pasillo B en `datos/sectorA.json` (14 posiciones de piso) |
| `POSTE` | 0.12 m | el mismo DXF: 17.41 = 7 × 2.35 + 8 × 0.12 |
| `X0`, descarga → primer poste | 3.00 m | inventado |
| reparto de los 35 cm sobrantes | tres huelgos iguales | inventado |
| `PROF_BAHIA` | 0.20 m | inventado; ver la tabla |
| zona de descarga | 6 m de ancho, 3 m detrás del punto | inventado |
| `VEL_ELEV`, `VMAN`, `ACC` | 0.55 m/s, 0.35 m/s, 0.9 m/s² | `sim-web` |
| patas | 1.315 de ancho, 0.48 de largo **delante de la torre** | la del 318 con el `L_ANCHO` medido |
| `XPIV` | 1.50 | derivado (barrido arriba) |
| maniobras de la FSM | medidas vacío en la bahía 4, usadas para todas | `fsm_rutas.py` |

## Cómo está hecho, y por qué no es un solo A*

Es Hybrid A* (primitivas de 10 cm, 7 ángulos, dos sentidos, costo por cambio de sentido 1 m) con
**el mismo `step()`** de `planificador_giro.py` y `percepcion/odometria.py`, y la silueta muestreada
cada 5 cm.

Una sola búsqueda de 5 m de pasillo más un giro de pocos centímetros de huelgo **no salió en
80 000 expansiones** (un minuto en la i3). Por eso se compone, igual que maniobra el operador:
- **SALIDA:** de la bahía hasta quedar alineado.
- **ENTRADA:** es una salida invertida, y `step()` con punto medio es exactamente reversible.
- **TRASLADO:** cambio de carril más la recta.
- **VUELTA:** dos 90° por el centro de una bahía, o maniobra libre en la zona.

Cada combinación posible se evalúa y se elige la más barata. **No es óptimo globalmente:** es el
mejor de los planes armados con esas piezas.


## Dato de campo — el video del operador (maje, 05-nov-2026)

- Se pone en posición retrocediendo, y **una vez que empieza el giro no retrocede: solo mueve el
  timón**, de forma continua. Entra al mismo hueco al que se iba a alinear.
- Las uñas van a **pocos cm del piso** durante el giro (lo justo para no rozar). **No entran a los
  huecos del IBC** ni al girar ni al terminar, pero sí quedan **un poco dentro de la bahía**.
- El equipo queda **pegado a las dos bahías**: la de entrada y la de enfrente.
- **Los 3.00 m del pasillo se miden entre los postes de seguridad**, que son los puntos más
  angostos. Entre poste y poste, la cara de los cubos queda más atrás.

**Qué cambia en el modelo:** el pasillo no es una pared de 3.00 m. Son **postes cada 2.35 m** con
un **retranqueo entre postes, en los dos lados**, y las uñas (al piso) y posiblemente el culo
pueden usar ese retranqueo. `PROF_BAHIA` deja de ser un supuesto de "cuánto pasan la cara del
rack": es **la distancia del frente del poste al frente del cubo**, y se mide con cinta.

**Medir:** ancho y fondo de cada poste, su altura, la separación entre postes a lo largo del
pasillo, y el retranqueo del poste al frente del cubo a nivel del piso, en los dos racks.

**Afinado (maje, 05-nov):** el retranqueo poste → cara del cubo es de **~6 cm**, no 20. El cubo
de N1 al piso depende de dónde lo dejó el operador (**error humano**). El de N1-B, encima,
queda alineado con el de abajo. En N2 y más arriba el cubo se mete **hasta el fondo**.

**La cuenta con 6 cm en los dos lados:** entre postes quedan **3.00 + 0.06 + 0.06 = 3.12 m**. El
ancho a rumbo máximo es **3.036 m vacío** y **3.078 m cargado** (tabla de arriba), así que el giro
cabe **solo si las dos puntas (uñas y culo) quedan entre postes**, no frente a uno. Sobran unos 8 cm
vacío y unos 4 cm cargado. Eso calza con el video: el operador queda pegado a las dos bahías.

**Consecuencias:**
- Con un margen de 4 cm cargado, un cubo de N1 que el operador dejó 4 cm más afuera mata el
  giro. **Cuando los cubos de N1 los deja el kit, que los deje siempre a la misma profundidad.**
  Si quedan cubos dejados a mano, hay que saber dónde están: medirlos o verlos.
- **Para correr de nuevo:** `PROF_BAHIA = 0.06` **en los dos lados**, postes cada 2.35 m, y exigir
  que en los rumbos de 56° a 89.5° las dos puntas queden entre postes. El caso del video tiene que
  salir sin reversa después de arrancar.


## v2 — postes, retranqueo de 6 cm y el giro sin reversa del video (05-nov-2026, tarde, en la i3)

Encargo: `tarea_rutas_v2.md`. `py analisis/planificador_rutas.py --v2` corre la batería v2 (sin flag era v2 hasta v3)
(~2 min) y escribe `rutas_v2.json`. `--v1` reproduce todo lo de arriba. La FSM sigue leyendo
`rutas_tabla.json` (v1); ver «Pendiente» al final.

**Lo que se metió al modelo** (`Planificador(modelo='v2')`):
- **Postes y retranqueo.** Los 3.00 m son de cara de poste a cara de poste. En la luz de cada
  bahía, en los **dos** lados, cualquier punto del equipo (uñas al piso y culo) puede llegar
  **6 cm** más allá. El poste mide 0.12 de ancho.
  - **Reconciliado con `visibilidad.py`:** 2.35 m es la **luz** entre caras de poste y 2.47 m es
    el **paso** entre centros de poste (2.35 + 0.12). Son el mismo rack.
- **El hueco.** La punta de uña queda a 3 cm de la **cara del cubo**, es decir 3 cm dentro de la
  luz, sin entrar a los huecos del IBC.
- **Resolución del giro.** Timón de 15 ángulos en vez de 7, primitivas de 3 cm, silueta muestreada
  cada 2 cm (con 5 cm la esquina de un poste se colaba) y grilla de 1 cm y 1°.
- **Giro sin reversa, como en el video.** La salida del hueco se busca **solo en reversa**. Una
  salida sin cambios de sentido es una entrada que, una vez que arranca el giro, ya no retrocede.
  Posicionarse antes, retrocediendo, está permitido.
- **Carril central** (`central=True`): tránsito por el eje, bajando al carril de giro 4 m antes.
- **Holgura de 1 cm al girar**, contra los 5 cm de v1. Es el margen que deja el giro cargado
  (abajo).

### La cuenta y lo que dice el planificador

Entre postes caben **3.12 m**. El ancho a rumbo máximo es 3.036 vacío y 3.078 cargado: sobran
**8.4 cm** vacío y **4.2 cm** cargado **en total**. La cuenta dice que cabe, pero no mira la
cinemática.

**Con XPIV 1.50 (δmax 78°), el giro sin reversa NO existe: 0 de 12** (a/b/c × los dos sentidos ×
vacío/cargado), ni con holgura 0. Por qué:
- saliendo en reversa del hueco, el eje de carga solo puede alejarse del rack;
- con δmax 78° el centro de giro queda a 33 cm del pivote, y girar 25° cuesta al menos 14.5 cm
  de recorrido;
- pero entre 65° y 80° la ventana para el pivote mide 8 cm.

El 90° entra **solo si el equipo casi rota en el lugar**. Con XPIV 1.30 o 1.40 (δmax 69.5° y
73°), tampoco sale ninguno.

**El umbral** (holgura 0; «S» = sale, en el orden La con uñas hacia adentro, La hacia la descarga,
Lc hacia adentro):

| XPIV (δmax) | 1.50 (78°) | 1.52 | 1.54 | 1.56 (81.5°) | **1.58 (82.8°)** | 1.60 (84.1°) | 1.62 | 1.64 | 1.66 (88°) |
|---|---|---|---|---|---|---|---|---|---|
| retranqueo 3 cm, vacío | ··· | ··· | ··· | ··· | ··· | ··· | SSS | ··· | SSS |
| retranqueo 3 cm, cargado | ··· | ··· | ··· | ··· | ··· | ··· | ··· | ··· | ··· |
| **retranqueo 6 cm**, vacío y cargado | ··· | ··· | ··· | ·SS | **SSS** | SSS | SSS | SSS | SSS |
| retranqueo 9 cm, vacío y cargado | ·SS | ·SS | SSS | SSS | SSS | SSS | SSS | SSS | SSS |

**El video del operador es evidencia de que δmax ≥ ~83°**: XPIV ≥ 1.58 por la fórmula de ficha
(cota dura 1.6724). Con 3 cm, lo que sale suelto (1.62 y 1.66, no 1.64) está en el borde de la
resolución de la búsqueda: no es un resultado, es ruido de ese borde. Desde acá se trabaja con
**XPIV 1.60** (`XPIV_V2`), SUPUESTO tomado del video.

### Validación contra el video (XPIV 1.60, retranqueo 6 cm)

| Hueco y sentido de viaje | Vacío | Cargado |
|---|---|---|
| `a`, `b` y centro, con uñas hacia adentro y hacia la descarga (las 6) | **sale sin reversa, margen 2 cm** | **sale sin reversa, margen 1 cm** |

- **El margen es la holgura por lado**, contra poste y contra cara de cubo, con la que todavía
  sale. La cuenta a mano daba 4.2 y 2.1 como techo, y la cinemática se come la mitad.
- **El giro es casi una rotación sobre el eje de carga:** el pivote recorre **0.27 m** para
  87–89°, con el timón a fondo. Arranca a **5 cm del eje del pasillo**, no a 85 cm del rack. El
  «carril de giro» y el carril central casi coinciden: por eso el operador queda pegado a las dos
  bahías.
- **Retranqueo mínimo para el giro sin reversa** (XPIV 1.60): **4 cm vacío, 5 cm cargado**. Con
  XPIV 1.50 no alcanza ningún retranqueo hasta 9 cm para la `a`; el centro sale recién con 9.
  **Un cubo de N1 dejado 2 cm más afuera mata el giro cargado.** La consecuencia del afinado se
  confirma con el planificador: si el kit deja los cubos de N1, que los deje siempre a la misma
  profundidad.
- **Control: retranqueo 0, con XPIV 1.60, no sale ninguno (0/12).** Lo que restringe son los
  postes y el retranqueo.

### El caso de maje y el barrido, v2

| | Ida (vacío) | Vuelta a la descarga (con el IBC) |
|---|---|---|
| 5 3 **Ra** | **4.8 m · 1 cambio · 6 s**: 4.6 m en reversa posicionándose, y entra **hacia adelante girando 89° sin retroceder** | 13.3 m · 1 cambio · 12 s: sale girando en reversa, y de frente a la descarga |
| 5 3 **Rb** | **6.0 m · 1 cambio · 7 s**, igual | 14.5 m · 1 cambio · 12 s |

**Es lo que hace el operador en el video:** se posiciona retrocediendo, y desde que gira ya no
retrocede. **Barrido** desde la descarga: **las 28 llegan sin ningún cambio de sentido** (en v1:
1 a la `a`, 3 a la `b`). **Con o sin la regla del carril central, las rutas son idénticas:** el
giro arranca desde el eje, así que el tránsito ya va por el central sin forzarlo.

### Decía / es / qué lo tumbó (contra lo de esta mañana)

| Decía (05-nov, v1) | Es (v2) | Qué lo tumbó |
|---|---|---|
| El pasillo es una pared de 3.00 m; las uñas pasan la cara hasta `PROF_BAHIA` = 0.20 (SUPUESTO), solo en la bahía objetivo | Postes cada 2.47 m; **entre postes, 6 cm de retranqueo en los dos lados**, para uñas y culo | el video y la medición de maje |
| A la `a` solo con uñas hacia adentro, a la `b` solo hacia la descarga | **Las dos en los dos sentidos** (con XPIV ≥ 1.58) | el retranqueo del lado opuesto deja pasar el culo; la asimetría venía del poste vecino con las uñas solas |
| Al giro le cuesta 0 a 3 cambios de sentido, y dar la vuelta 2 más | **Sin cambios de sentido una vez que arranca**, en las 28 bahías | el video: el operador no retrocede después de empezar a girar |
| XPIV 1.50 alcanza («la forma domina al pivote», 18-sep, solo chasis) | **Con uñas y sin reversa, XPIV 1.50 no gira.** Hace falta δmax ≥ ~83° (XPIV ≥ 1.58) | el giro del video existe; con 78° la cinemática no lo permite |
| Holgura de 5 cm por lado | **2 cm vacío y 1 cm cargado** es lo que hay | ancho a rumbo 3.036/3.078 contra 3.12 entre postes, más la cinemática |
| Carril de giro a 85 cm del rack opuesto | El giro sin reversa arranca **a ~5 cm del eje** | casi una rotación sobre el eje de carga |

### Lo que hay que medir, en orden

1. **El ángulo de tope de la rueda de dirección** (δmax), directo con transportador, o el `XPIV`
   con plomada. Decide si el giro del video sale en el modelo. Hoy es una inferencia.
2. **El retranqueo** poste → cara del cubo de N1, en varios huecos de los dos racks. Con menos de
   5 cm, el giro cargado no sale.
3. **El ancho y el fondo del poste**: hoy 0.12 de ancho, del DXF.

**Pendiente:** la FSM (`percepcion/fsm_rutas.py`) sigue con la tabla de v1. Pasarla a v2 cambia
la prueba 5: con v2 ya no hay vuelta en la ida a la Ra, porque a la `a` se entra en los dos
sentidos. Su control («rutas sin rumbo») deja de discriminar y habría que rehacerlo. No se hizo
en esta tarea. `rutas_v2.json` → `rutas.central.tabla_fsm` tiene la tabla lista.


## Del manual y de la ficha (06-nov-2026)

**Manual de servicio** (`herramientas/Codigos de error reach color_*.pdf`, eventos `1.71`/`1.72`):
existe un **«cambio de modo de dirección de 180°/360°»**, con botón selector y entradas
redundantes. En **modo 180°** la rueda motriz va de −90° a +90°; en **360°** gira sin tope. O sea,
**δmax ≥ 90°**, no los 78° que salían de la fórmula de la ficha.

| Decía | Es | Qué lo tumbó |
|---|---|---|
| δmax 78°, derivado de `Wa` + `XPIV` 1.50 | **δmax ≥ 90°** (modo 180°/360°) | el manual de servicio; el video ya pedía ≥ 83° |
| `XPIV` sale de δmax | **Al revés:** con δ = 90° el equipo rota sobre el centro del eje de carga, y `Wa` es la distancia de ahí al punto más lejano del culo → `XPIV` sale de `Wa` y de la forma del culo | la fórmula de `planificador_giro.py` suponía un δmax que no es el real |

**Con δ = 90°, `Wa = 1.797` (ficha) da `XPIV` según la forma del culo** (si la rueda motriz va
centrada; si va corrida a un lado, cambia):
- culo en ángulo recto, capó de 1.065: `XPIV = √(1.797² − 0.5325²) = 1.716 m`
- culo en semicírculo completo: `XPIV = Wa = 1.797 m`
- la «cota dura» de 1.6724 usaba `W_MAX/2 = 0.6575` en el culo, pero el culo es el capó (1.065):
  con el ancho del capó la cota pasa a **1.716**

**Ficha comercial Mitsubishi ESR20N2/EDR18N2** (solo leída por resúmenes de búsqueda; el PDF no se
pudo bajar desde la sesión). Las cifras van por configuración:
radio de giro mínimo exterior **1,746–1,797 mm** · largo total **1,882–1,983 mm** · largo hasta la
cara de las uñas **1,321–1,582 mm** · ancho del chasis **1,054 mm**.
**Dato en tensión:** el modelo pone la cara de la torre a **1.70 m** del culo (`LCH`), más que el
máximo de la ficha (1.582). El 2.91 medido de culo a punta manda, pero hay que ver qué
configuración es este equipo (serie `82824121`).

**Pendiente para el planificador:** correr v2 con **δmax = 90°** y `XPIV` en 1.72–1.80. Con rotación
sobre el eje de carga la cinemática deja de ser el límite y queda solo el ancho a rumbo.


## Las fichas técnicas (06-nov-2026, `herramientas/fichas/LEEME.md`)

| Decía | Es | Qué lo tumbó |
|---|---|---|
| `XPIV` 1.50 (derivado), 1.60 (supuesto del video) | **≈ 1.80** (`l2 + x = 1,582 + 219`), igual a `Wa` | ficha VDI del ETR 335d |
| culo en ángulo recto a 1.50 del eje | el culo es un **arco** alrededor del eje de carga: su punto más lejano está a `Wa` | `XPIV = Wa` |
| el giro necesita 3.036 vacío / 3.078 cargado (silueta del 05-nov) | la fórmula del fabricante, con rotación sobre el eje de carga: **2.84 vacío (uñas 1.20) / 2.90 con el IBC**, sin el margen de 200 | VDI 2198, comprobada contra las 3 filas de `Ast` |
| pantógrafo 0.61 | **1.067** | ficha EDR18N2 (doble profundidad) |

**Dato en tensión:** con la ficha estándar el equipo mide 2.65–2.78 m de culo a punta; se midieron
**2.91**. Cuadra con el compartimento de batería largo (+126 mm), y entonces `XPIV`/`Wa` de este
equipo son ~1.93 y el IBC pide ~3.03 sin margen, lo que vuelve a necesitar el retranqueo entre postes.
**Lo que decide:** el largo del compartimento de batería de este equipo, o su configuración por la serie.

**Pendiente:** rehacer la silueta de `planificador_rutas.py` con los datos de la ficha (eje de carga a
1.80, culo en arco, uñas sobre los brazos) y volver a correr v2.

> **Hecho el 06-nov en v3** (abajo), con el culo de esquinas redondeadas que dio el dibujo (no en arco)
> y el largo medido.


## v3 — la silueta de la ficha: 2.91, culo redondeado, δmax 90° (06-nov-2026, en la i3)

Encargo: `tarea_rutas_v3.md`. `py analisis/planificador_rutas.py` corre la batería v3 (~11 min en la
i3) y escribe `rutas_v3.json` y `ruta_3L_5R_v3.png`. `--v2` y `--v1` reproducen lo de arriba sin
cambios (verificado: la misma salida de 4 La, 1.16 s y 0.27 m en v2, y 7.34 s y 2.60 m en v1).

**Lo que se metió al modelo** (`Planificador(modelo='v3')`; mundo y reglas de v2):

| | v2 | **v3** | Fuente |
|---|---|---|---|
| Culo → punta de uña | 2.90 | **2.91** (`LCH_V3` 1.71 + uña 1.20) | medido por maje |
| Esquina del culo | ángulo recto | **radio 0.17** (`R_CULO_V3`) | dibujo de la ficha VDI, ±3 cm |
| δmax | 84.1° (supuesto del video) | **90°** | manual, modo 180°/360° |
| `XPIV` | 1.60 | **1.929** = 1.71 + 0.219 (`XPIV_V3`) | derivado de la ficha (`x`) |

**Lo que hubo que cambiar para que δ = 90° funcione:**
- **La cinemática.** Con δ = 90°, `tan δ` explota. En v3 los `ds` de las primitivas son el recorrido de
  la **rueda motriz** (`step(..., rueda=True)`): `ds_eje = ds·cos δ` y `Δθ = −(ds/WB)·sin δ`. Para
  δ < 90° es la misma cinemática; con 90° el eje de carga queda quieto y el equipo rota. Sigue siendo
  exactamente reversible, así que la ENTRADA sigue siendo la SALIDA invertida.
- **El largo y el tiempo.** El «largo» de un giro v3 es lo que recorre la rueda motriz: **2.4 m para
  88°** (WB·π/2 = 2.45), unos **7 s** a `VMAN`. En v2 el largo de un giro era lo que recorría el eje de
  carga (0.27 m). Comparar largos v2 contra v3 es comparar cosas distintas.
- **La heurística y el castigo del timón.** Con la heurística vieja (0.33 m por radián, el radio del
  eje de carga a 78°) y el castigo de 0.02 por primitiva a fondo, rotar en el lugar parecía casi el
  doble de caro de lo que es, y el giro **no salía en 6000 expansiones** (sí en 22 700). Con 1.562 m por
  radián (WB, el mínimo exacto) y castigo de 0.005, sale en 81.
- **La meta de la salida.** El giro v3 termina con el eje de carga a ~0.5 m del eje del pasillo, del
  lado de la bahía. La meta de v2 (el carril de giro del lado opuesto, ±0.80) lo rechazaba. En v3 vale
  cualquier `y` alineada (±1.00 del eje); el traslado acomoda el carril.
- **El margen tenía un tope falso.** La punta arranca a 3 cm de la cara del cubo (`GAP_OBJ`): con una
  holgura de 4 cm ya chocaba la pose de arranque y el margen salía siempre «3 cm». Para medirlo, la
  punta arranca a `holgura + 0.5 cm`.

### La cuenta: el planificador la reproduce

`anchos_v3()`: el ancho a rumbo máximo de la silueta. No depende de `XPIV`, solo de la forma.

| Culo | Vacío | Con el IBC |
|---|---|---|
| ángulo recto | 3.045 | 3.088 |
| 0.10 | 3.021 | 3.061 |
| **0.17 (ficha)** | **3.005** | **3.042** |
| 0.24 | 2.990 | 3.025 |

Es la tabla de `herramientas/fichas/LEEME.md` al milímetro (allá, 3.043 cargado).

### El giro sin reversa, contra el video (nominal: `XPIV` 1.93, culo 0.17, retranqueo 6 cm)

| Hueco y sentido de viaje | Vacío | Cargado |
|---|---|---|
| `a`, `b` y centro, con uñas hacia adentro y hacia la descarga (las 6) | **sale, margen 5 cm por lado** | **sale, margen 3 cm por lado** |

- **Es una rotación sobre el eje de carga.** La rueda motriz recorre 2.4 m a fondo (90°); el eje de
  carga se mueve **5 cm vacío y 10 cm cargado** (retrocede eso antes de rotar, para que la uña no
  toque el cubo).
- **El margen es casi toda la sobra de la cuenta**: 3.12 entre postes contra 3.005 y 3.042 deja 5.7 y
  3.9 cm por lado; el planificador da 5 y 3. **En v2 la cinemática se comía la mitad (2 y 1 cm); con
  90° ya no se come nada.**

### Sensibilidad (holgura 0; «S» = sale en La→adentro, La→descarga, Lc→adentro; Lb es espejo de La)

| Carga | Culo | Retranqueo 0 (todo dentro de 3.00) | 3 cm | 6 cm |
|---|---|---|---|---|
| vacío | 0.10 | ··· | SSS | SSS |
| vacío | 0.17 | ··· | SSS | SSS |
| vacío | **0.24** | **SSS** | SSS | SSS |
| cargado | **0.10** | ··· | **···** | SSS |
| cargado | 0.17 | ··· | SSS | SSS |
| cargado | 0.24 | ··· | SSS | SSS |

**Igual con `XPIV` 1.80 y 1.93**, celda por celda. Barrido aparte, con culo de 0.17: `XPIV` 1.80,
1.85, 1.90, 1.93 y 1.95 dan lo mismo (sale con 6 cm, no sale con 0, vacío y cargado).

- **Sale exactamente cuando la cuenta de ancho dice que cabe**, en las 36 combinaciones: vacío dentro
  de 3.00 solo con culo de 0.24 (2.990); cargado nunca dentro de 3.00 (el mínimo es 3.025); con 3 cm
  de retranqueo (3.06) cargado sale con 0.17 y 0.24 y no con 0.10 (3.061).
- **Con δmax = 90°, `XPIV` deja de decidir si gira.** Solo mueve dónde queda el eje de carga.
- **Lo que decide ahora es la forma: el radio del culo y el retranqueo.** Con el culo de la ficha,
  cargado necesita **más de 2 cm por lado** de retranqueo.

**Control de falsación: culo en ángulo recto, retranqueo 0, holgura 0 → 0/6 cargado (3.088 > 3.00) y
0/6 vacío (3.045).** Las búsquedas que no salen se agotan (66–360 expansiones, «sin camino»), no se
quedan sin presupuesto.

### El caso de maje y el barrido, v3

| | Ida (vacío) | Vuelta a la descarga (con el IBC) |
|---|---|---|
| 5 3 **Ra** | **7.8 m · 1 cambio · 15 s**: 5.4 m en reversa posicionándose (con el eje de carga a 0.50 m del eje del pasillo, lado R) y **rota 88° hacia adelante** (2.4 m de rueda, 7 s) | 16.3 m · 1 cambio · 20 s: rota en reversa y de frente a la descarga |
| 5 3 **Rb** | **8.9 m · 1 cambio · 16 s**, igual | 17.4 m · 1 cambio · 21 s |

- **Sigue siendo lo del video:** se posiciona retrocediendo y, desde que gira, no retrocede.
- **Barrido desde la descarga: las 28 llegan sin ningún cambio de sentido**, como en v2.
- **Con y sin la regla del carril central, las rutas son idénticas**, otra vez.
- **Los tiempos suben** (ida a la Ra: 6 s en v2, 15 s en v3) porque ahora la rotación tiene costo: la
  rueda motriz recorre 2.4 m. Es la diferencia de medir el giro con la rueda en vez del eje de carga, y
  `VMAN` (0.35 m/s) es SUPUESTO.
- Saltos entre piezas: < 2 µm en todas las rutas.

**Dato para la FSM, no resuelto:** el cambio de carril de un carril de giro al otro (1.3 m de lado en
4 m de pasillo) **no sale con 15 000 expansiones**; con 60 000 sale, con 1 cambio de sentido. En la tabla
para la FSM queda `None`. La FSM sigue con la tabla v1, así que hoy no la usa nadie; si se pasa a v3,
hay que darle más presupuesto o revisar si con el giro v3 hace falta ese cambio de carril.

### El pantógrafo

`EXT_MAX` = **1.067** en `percepcion/fsm_estados.py` (decía 0.61), y donde se usaba el número suelto:
`sim_coordinacion.py` (prueba 3), el comentario de `fsm_falla.py` y `clases/fsm.html`. **Las cinco pruebas
de la FSM pasan**; la prueba 3 cambia solo sus números (paro en EXTIENDE con 0.71 m afuera, en TOMA con
1.07) y su control sigue fallando como debe (cede el control con el pantógrafo afuera).

### Decía / es / qué lo tumbó (contra v2)

| Decía (v2, 05-nov) | Es (v3) | Qué lo tumbó |
|---|---|---|
| δmax 84° (XPIV 1.60), supuesto del video | **90°**: rota sobre el eje de carga | el manual (modo 180°/360°) |
| `XPIV` 1.60 | **1.93**, derivado; y **ya no decide si gira** | la ficha (`x` = 0.219) y el largo medido |
| 2.90 de culo a punta, culo en ángulo recto | **2.91**, culo con esquinas de **0.17** | maje midió el largo; el dibujo VDI da la esquina |
| Margen 2 cm vacío, 1 cm cargado: la cinemática se come la mitad | **5 cm vacío, 3 cm cargado**: casi toda la sobra de la cuenta | con 90° la cinemática deja de restringir |
| Retranqueo mínimo 4 cm vacío, 5 cm cargado | **0 vacío solo con culo ≥ ~0.20; cargado > 2 cm por lado** con culo de 0.17 | lo decide solo el ancho a rumbo |
| El giro es casi una rotación de 0.27 m | **Es una rotación**: el eje de carga se mueve 5–10 cm; la rueda motriz recorre 2.4 m | δ = 90° |
| Ida a la Ra 4.8 m · 6 s | 7.8 m · 15 s (la rueda recorre 2.4 m en el giro) | el giro se mide con la rueda motriz |
| Pantógrafo 0.61 | **1.067** | ficha EDR18N2 / ETR 335d |

### Lo que hay que medir, en orden (reemplaza la lista de v2)

1. **El radio de las esquinas del culo**, desde arriba con escuadra o una foto con cinta. Es lo que más
   pesa: de 0.10 a 0.24 el cargado pasa de no salir a salir con 3 cm de retranqueo.
2. **El retranqueo** poste → cara del cubo de N1, en varios huecos de los dos racks. Con el culo de 0.17,
   cargado necesita más de 2 cm por lado.
3. **Que la rueda llegue a 90°** con el selector de modo, mirándola. Lo dice el manual; no se vio en
   este equipo.
4. **El compartimento de batería** (o la configuración por la serie `82824121`): explica los 13 cm de
   más del 2.91 y fija `XPIV`, que ya no decide si gira pero sí dónde queda el eje de carga.

## El culo exacto, de los vectores de la ficha (07-nov-2026)

La hoja VDI es dibujo vectorial a escala: el culo sale exacto (`herramientas/fichas/culo_de_la_ficha.py`,
`culo_ficha.csv`). **La cara es un arco de R 1.747, no un rectángulo con esquinas de 0.17.** Con la
silueta v3 cambiando solo el culo:

| | Decía (v3, esquinas de 0.17) | **Es (culo de la ficha)** |
|---|---|---|
| Ancho a rumbo vacío | 3.005 | **2.967**: cabe en 3.00 **sin retranqueo** |
| Ancho a rumbo cargado | 3.042 | **3.005**: pide **3 mm por lado** del retranqueo |

Falta correrlo en el planificador (encargo `tarea_rutas_v3b.md`). Si la regla de v3 se sostiene
(«sale exactamente cuando la cuenta de ancho dice que cabe»), vacío sale con retranqueo 0 y cargado
con cualquier retranqueo ≥ 1 cm.
