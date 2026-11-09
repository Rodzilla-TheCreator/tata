# Percepción y localización — el stack que corre en maquinón, sin montacargas

**La mayor parte del kit no necesita el equipo para avanzar.** El fierro bloquea probar
marcha/dirección y **capturar odometría real** del bus — nada más. La percepción, el filtro de
pose, la planificación y la simulación se construyen y se validan en **maquinón** (RTX 4070 8 GB,
32 GB; ver `docs/14`) con webcams, marcas ArUco impresas y Isaac Sim. Esta carpeta es ese stack.

> **Corrección de rumbo (31-oct-2026).** Esto se pudo empezar hace semanas. El Jetson Orin es
> **empaque de despliegue** (cómputo a bordo del equipo en movimiento), **no** un requisito para
> prototipar. Hasta que el equipo se mueva solo y sin cable, maquinón hace todo mejor y a $0.

## Qué hay

| Archivo | Qué hace |
|---|---|
| `detector_aruco.py` | **Detecta ArUco en vivo con una webcam** y mide distancia, corrimiento lateral, yaw y error de reproyección. El par de campo de `analisis/aruco_precision.py` (que da la teoría). Loguea a CSV |
| `generar_aruco.py` | **Genera las marcas ArUco imprimibles**, en negro, del mismo diccionario que el detector, con **ID conocido** (para mapear cada marca a una ubicación). Round-trip validado: generar → detectar = 8/8 con el ID correcto |

> **Las marcas del RoboMaster S1 NO sirven.** Son marcas de visión **propietarias de DJI**, no
> ArUco: el detector de OpenCV no las lee. Generá las propias con `generar_aruco.py` e imprimilas
> en **negro** (el rojo da poco contraste en gris y es frágil con luz mala). Imprimí al 100% y
> **medí el lado negro con regla** — ese número va en `detector_aruco.py --marca`.

## El detector, ya

```bash
pip install opencv-contrib-python numpy
python percepcion/detector_aruco.py --marca 0.15          # marca de 15 cm
python percepcion/detector_aruco.py --calib calib.npz --log corrida.csv
```

- Imprimí una marca ArUco (diccionario `4x4_50` por defecto), medila con regla y pasá el lado real
  en `--marca` (metros).
- **Sin `--calib`** sintetiza los intrínsecos desde `--fov`: sirve para ver que detecta y el rango.
  Para precisión de verdad, **calibrá** con un tablero de ajedrez y pasá el `.npz`
  (`camera_matrix`, `dist_coeffs`).
- Comparar lo medido contra la tabla de `analisis/aruco_precision.py`: ¿da la marca el ±4.5 cm
  lateral que deja la bahía, a la distancia del pasillo? Esa es la pregunta que cierra.

## Lo que sigue en esta carpeta (todo sin montacargas)

1. **EKF odometría + ArUco** — el filtro que fusiona la odometría (predicción) con la pose ArUco
   (corrección). Se prueba contra **Isaac Sim** generando odometría y observaciones sintéticas:
   lazo cerrado sin fierro.
2. **Modelo de odometría** — bicicleta, de velocidad de tracción (nodo 8) + ángulo de dirección
   (nodo 4). Se construye y testea contra sim ahora; cuando haya bus real, solo se calibra.
3. **Lazo completo en Isaac** — percepción → localización → planificación (`analisis/planificador_giro.py`)
   → control.

El montacargas vuelve a hacer falta al final: para **capturar la odometría real** del bus y para
las pruebas de movimiento. No para construir nada de lo de arriba.


## EKF odometría + ArUco — hecho y validado en sintético (02-nov-2026, en la i3)

`odometria.py` · `ekf.py` · `sim_sintetico.py` · figura `ekf_sintetico.png`. Solo numpy +
matplotlib, portable. Encargo original: `tarea_ekf.md`.

```
py percepcion/sim_sintetico.py      # ~15 s en la i3; termina con RESULTADO: PASA / FALLA
```

| Corrida | Resultado (semilla 0) | 30 semillas más |
|---|---|---|
| A · ArUco encendido | lateral RMS **0.63 cm**, máx 1.54 cm (requisito ±4.5) · rumbo RMS 0.20° | 30/30 |
| B · solo odometría (**control**) | 18 cm al tercio → **77 cm** al final; deriva visible | 30/30 |
| C · oclusión de 5 s | 0 marcas aceptadas · σ lateral 0.49 → 2.36 cm · error dentro de 3σ · se reengancha (0.69 cm) | 30/30 |

**Control del control:** el mismo test con la estimación de sesgos apagada (la v1) da A 0/31 y
C 0/31. El test detecta el bug que tuvo.

**Lo que se aprendió armándolo (decía / es / qué lo tumbó):**

| Decía | Es | Qué lo tumbó |
|---|---|---|
| estado `[x, y, θ]` (el encargo) | **`[x, y, θ, b, s]`**: sesgo de dirección y escala de velocidad. La pose de afuera sigue siendo `[x, y, θ]` | un sesgo de dirección deriva el rumbo **linealmente**; ruido aleatorio crece como √t. Tras 5 s de oclusión la v1 decía σθ 0.23° con 1.75° reales, rechazaba toda marca y **no se reenganchaba nunca** (183 rechazos). Con b y s estimados: +0.50° estimado vs +0.50° real |
| error de colocación de la marca = ruido de medición | es el **mismo en cada vista**: `ColocacionMarcas` le baja el peso a cada vista repetida | sumado como ruido blanco, 20 vistas de una marca mal puesta contaban como 20 marcas: 5.6σ de error en la oclusión; con colocación perfecta, 0.55σ |
| control de oclusión: «error > máximo de la corrida A» | cero marcas + σ que crece + error dentro de 3σ + reenganche | con el sesgo estimado el filtro bueno deriva 1–3 cm en 5 s; el máximo de A cae en el giro. El criterio viejo medía otra cosa |

**Supuestos marcados en `sim_sintetico.py`** (no son de campo): sesgos de odometría, montaje y
alcance de las cámaras, una marca por bahía, colocación σ 1 cm. **Pendiente para datos reales:**
verificar los signos de `lateral` y `yaw` de `pose_desde_marca` contra `detector_aruco.py` con una
marca real, y capturar odometría del bus con el equipo andando (nodo 8 velocidad, nodo 4 ángulo).

**Dato que dejó la prueba — consistente no es lo mismo que preciso:** en la oclusión de 5 m el
error lateral máximo da mediana 1.9 cm, p90 4.6 cm, máximo 7.0 cm, y **pasa los 4.5 cm en 4 de 31
semillas** (dentro de su 3σ: el filtro lo sabe). Con estos supuestos de odometría, **5 m sin marcas
es demasiado** para la bahía. Es la respuesta parcial a la clase 2 (separación máxima entre ArUcos);
el número firme sale con odometría real del bus. La clase interactiva: `clases/ekf.html`.


## FSM de coordinación A/B — reserva, deadlock y falla (02-nov-2026, en la i3)

`fsm_estados.py` · `reserva.py` · `fsm_falla.py` · `sim_coordinacion.py`. Python puro, sin
dependencias. Encargo: `tarea_fsm.md`. No toca `sim-web/` (integrar es después).

```
py percepcion/sim_coordinacion.py     # ~17 s en la i3; termina con RESULTADO: PASA / FALLA
```

> **05-nov: con direcciones de bahía** (`fsm_rutas.py`, encargo `analisis/tarea_rutas_bahias.md`).
> Las cuatro pruebas corren dos veces: con la tabla fija `TICKS`, que es la de la tabla de abajo y
> la de `clases/fsm.html` y no se movió, y con huecos `x y s` + `a`/`b`. En el segundo modo
> CARRIL, RECTA, GIRO, RETROCEDE, DESGIRA, ELEVA y TRANSITO duran lo que dice
> `analisis/rutas_tabla.json`, y el equipo lleva su x, su carril y su rumbo de viaje.
> - **Resultados con direcciones:** pasan las cuatro. Deadlock tardío en el tick 164; operación al
>   azar: buena 0/0, tardía 19/20, tonto con choques en 19/20.
> - **La quinta es el caso de maje** (3L → 5 3 Ra / Rb → descarga): las 22 etapas en orden, la
>   vuelta solo donde la da el planificador, y el tiempo a ±25 % del planificador parando entre
>   maniobras. Tiene su control: con rutas «sin rumbo» desaparece la vuelta.
> - **El rumbo de viaje manda:** a la `a` se entra con las uñas hacia adentro y a la `b` hacia la
>   descarga. Si el equipo viene al revés, paga una vuelta (dos 90° por el centro de la bahía, o
>   la zona de descarga), que va anotada en `Equipo.maniobras` y se cuenta dentro de RECTA. `PASOS`
>   no cambió.
> - **Pendiente:** elegir `a` o `b` según el rumbo con que llega, para no pagar la vuelta. Ver
>   `analisis/rutas_resultados.md`.

| Prueba | Con lo bueno | Control |
|---|---|---|
| 1 · carrera por la última posición de trasbordo, mismo tick | gana uno solo (A); B queda en `ESPERA_TRASBORDO`; 0 choques | `GestorTonto`: los dos la creen suya; sin cámara, **1 cubo chocado** |
| 2 · deadlock de `sec/gen_fsm.py:40` (un trasbordo, dos PASE cruzados) | progresa: 4 tareas, todo en casa | reserva tardía: **deadlock en el tick 128** — B con el cubo de A en las uñas frente a un trasbordo lleno con **su propio** cubo |
| 3 · PARO con el pantógrafo afuera en altura | `FALLA` congelada → rearme → `DESHACE_TOMA → RETRAE → RETROCEDE → TRANSITO → PARADA`, todo en 0, nunca baja con el pantógrafo afuera; en TOMA el cubo no se suelta a ciegas | falla ingenua: cede el control con **0.41 m afuera a 2.76 m**, y al rearmar retoma EXTIENDE desde la mitad |
| 4 · operación al azar, 20 semillas × 3000 ticks | 0 deadlocks, 0 choques, 62 tareas/corrida (y 0/200 en 4 configuraciones más) | tardía: deadlock 20/20 · tonto: choques 19/20 |

**La regla anti-deadlock:** reservar destino + origen **todo o nada, antes de tocar el cubo**,
en orden total (huecos antes que trasbordo). Mata retener-y-esperar (nunca se espera con algo en
las uñas) y la espera circular. Las uñas son un recurso más: el deadlock real de la línea 40 es
ese. Por qué no timeout: quitarle la reserva a quien ya tiene el cubo lo deja sin dónde soltarlo.

**Lo que se aprendió (decía / es / qué lo tumbó):**

| Decía | Es | Qué lo tumbó |
|---|---|---|
| el selector toma la primera tarea por prioridad | toma la primera que **se puede hacer** (destino libre); si ninguna, espera la de más prioridad | con el rack lleno, A esperaba para siempre un hueco para su TRASBORDO teniendo 2 PEDIDOS que lo habrían liberado: inanición por prioridad (1–3 de 20 corridas «bloqueadas» con la política buena) |
| «de una espera solo se sale con el recurso reservado» (encargo) | con las uñas vacías la espera vuelve a correr el selector; con el cubo en las uñas, al pie de la letra | sin eso, A espera trasbordo para un PASE y lo que lo llena es un cubo SUYO que solo él puede sacar |
| prueba 4 con racks vacíos | inventario inicial revuelto (el día uno) | con racks vacíos B nunca tiene un cubo ajeno: no hay PASE cruzado y **los dos controles pasaban** — la prueba no discriminaba |
| (reporte) | el estado del perdedor se lee en el tick de la carrera; el deshacer se registra al empezar cada paso | el primer reporte decía `ESPERA_PEDIDO` (lo leía 400 ticks después) y escondía `DESHACE_TOMA` (dura un tick) |

**Supuestos:** ticks ≈ DUR del simulador / 0.5 s; mundo chico (1–2 trasbordos, 6 huecos por
sector, niveles a 1.38 m); la cámara verifica el hueco antes de extender (`verificar_hueco`).


## Imprimir y calibrar (02-nov-2026)

- `marcas/aruco_4x4_50_id{0..3}_15cm_carta.pdf`: cuatro ArUco de 15 cm, una por hoja carta, con regla de 10 cm. Validado: cada PDF rasterizado se detecta con su ID y 15.01 cm; página en blanco, nada.
- `marcas/tablero_9x6_22mm_carta.pdf` + `calibrar_camara.py`: el tablero y el script que guarda el `calib.npz` de `detector_aruco.py --calib`. Validado en sintético con dos cámaras distintas (fx 600 y 900): recupera cada una a < 0.1 %.

```
python percepcion/calibrar_camara.py --cuadro-mm 22      # el cuadro MEDIDO con regla
python percepcion/detector_aruco.py --calib calib.npz --marca 0.15
```


## Primera prueba con cámara real — 03-nov-2026, en superspeed

Primera corrida de `detector_aruco.py` y `calibrar_camara.py` contra hardware de verdad (antes
todo estaba validado solo en sintético). Cámara **Logitech C920** (`/dev/video4`, índice 4 de
dos detectadas; la otra es una USB2.0 FHD genérica en índice 0). `python3-opencv` del sistema
es 4.5.4 (sin `ArucoDetector`); se armó `.venv` con `opencv-contrib-python` 5.0.0 — necesario en
cualquier máquina nueva antes de correr nada de esta carpeta.

**Calibración** (tablero 9×6, cuadro medido 22.0 mm):

| Intento | Vistas | RMS | Veredicto |
|---|---|---|---|
| 1 | 15 | 3.873 px | **malo** — poca variedad de pose, `cx` corrido 75 px del centro esperado |
| 2 | 15 | 0.724 px | aceptable (no <0.5 ideal, pero `fx≈fy` 623.4/623.5 y `cx,cy` cerca del centro) |

`calib.npz` final: fx 623.4 · fy 623.5 · cx 349.1 · cy 252.4 · FOV horizontal 54.3°. La primera
corrida se repitió variando más la distancia, la inclinación (~30-45°) y cubriendo las cuatro
esquinas del cuadro — ahí bajó el RMS.

**Detección y escala**, marca de 15.00 cm (medida con regla, coincide con el nominal), a 1.00 m
real (medida con cinta): el detector reportó **1.00 m exacto**.

**Control de falsación** (misma marca, sin moverla de 1.00 m real):

| Variante | Predicho | Medido |
|---|---|---|
| sin `--calib` (FOV sintético 70°, más ancho que el real 54.3° → foco más corto) | ~0.73 m | **0.73 m** |
| con `--calib`, `--marca 0.30` (el doble del real) | ~2.00 m | **1.99 m** |

Los dos controles cambiaron en la dirección predicha. La prueba mide lo que dice medir.

**Signos para el EKF — prueba de 3 pasos, marca a ~1 m, cámara C920 fija:**

| Paso | Maniobra | `lateral_m` / `yaw_deg` medido |
|---|---|---|
| 1 | marca a la derecha de la cámara | lateral **+0.288** |
| 2 | marca a la izquierda | lateral **−0.446** |
| 3 | marca girada sobre su eje vertical, borde derecho (visto desde la cámara) alejándose, bisagra en el borde izquierdo | yaw **−42.4°** |

**Lateral: coincide** con la convención documentada ("+ a la derecha") en `detector_aruco.py` y
`ekf.py`. No se tocó.

**Yaw: NO coincidía.** `pose_desde_marca`/`marca_vista_desde` (antes del fix) predicen **+α**
para la maniobra del paso 3 (borde derecho alejándose); el detector real da **−42.4°**. Se
corrigió el signo en `percepcion/ekf.py`:

| Decía | Es | Qué lo tumbó |
|---|---|---|
| `cam_th = mth − π − yaw` (en `pose_desde_marca`) | `cam_th = mth − π + yaw` | la maniobra del paso 3 da yaw negativo en el detector real; con el signo viejo la fórmula pedía positivo para ese mismo giro |
| `yaw = mth − π − cam_th` (en `marca_vista_desde`) | `yaw = π + cam_th − mth` | es la misma corrección, por el lado inverso — las dos funciones son álgebra inversa entre sí |
| `sim_sintetico.py` iba a agarrar este bug | **no lo agarra, y no podía**: genera la medición sintética con `marca_vista_desde` y la consume con `pose_desde_marca`/EKF — cualquier convención consistente entre las dos pasa el sintético aunque esté al revés respecto del detector real | por eso el encargo pedía explícitamente este chequeo contra hardware antes de confiar en el EKF con datos de verdad |

`lateral` no se tocó porque la medición real confirmó que ya estaba bien.

Tras el fix, `sim_sintetico.py` sigue dando **PASA** (A 30/30, B 30/30, C 30/30 — mismos números
que antes, porque el sintético es autoconsistente respecto del signo: lo que cambia es que ahora
esa convención interna coincide con la realidad, no solo consigo misma).

**Pendiente:** esto corrige el signo de la fórmula geométrica 2D. Falta repetir una prueba
equivalente con **dos** cámaras montadas en el equipo real (el `montaje` de cada una) para
confirmar que `cth` (ángulo de montaje) también se combina con el signo correcto — hoy solo se
probó con la cámara haciendo de "equipo" directamente (`montaje` trivial).


## Dato en tensión — dónde van las dos cámaras (05-nov-2026)

| Fuente | Dice |
|---|---|
| `docs/03` §«Dos cámaras USB» | **una frontal + una lateral.** En el pasillo la frontal ve la cabecera y la lateral la cara del rack; en el giro de 90° intercambian papeles |
| `sim_sintetico.py` (EKF, 02-nov) | **dos laterales** a ±0.55 m del eje de carga, una mirando a cada rack — marcado como SUPUESTO |

No se contradicen en lo que el EKF validó (el filtro no depende de dónde esté la cámara), pero el
número de marcas visibles y los tramos ciegos sí. **Manda `docs/03`.** Pendiente: correr el
sintético con frontal + lateral, con marcas también en la cabecera del pasillo.

Para la frontal, la cabecera puede estar a 6 m: una marca de 15 cm ahí son ~16 px con la C920
(fx 623), en el límite de detección. **En la cabecera, marcas de 30 cm.**

> **Actualizado el 05-nov con `visibilidad.py` (sección siguiente).** maje descartó las marcas en
> las cabeceras: van solo en las caras de los racks. Sin cabecera, la frontal de `docs/03` ve las
> caras siempre de refilón y **es el peor montaje** de los cinco. Ver la tabla decía/es abajo.


## Visibilidad de ArUco a lo largo de las rutas — 05-nov-2026, en la i3

`visibilidad.py` · `rutas_densas.py` · figuras `visibilidad_<montaje>.png` · números en
`visibilidad_resultados.json`. Encargo: `tarea_visibilidad.md`. Primera pasada en 2D con altura:
sin luz, sin desenfoque por movimiento, sin oclusión por gente o por el mástil.

```
py percepcion/rutas_densas.py    # una vez, ~2.5 min: los 30 recorridos del planificador, primitiva por primitiva
py percepcion/visibilidad.py     # ~21 min en la i3
```

**Cómo está hecho:**
- **Recorridos:** los de `analisis/planificador_rutas.py`. El caso de maje (3L → 5 3 Ra / Rb →
  descarga) y el barrido (descarga → 7 bahías × L/R × a/b), reproducidos pieza por pieza (1 cm)
  con el perfil de velocidad del planificador. La llegada cae a 0.02 cm de la meta.
- **Marcas:** sobre los postes de las dos caras, cada N bahías (2.47 m entre postes; ½ = también a
  mitad de bahía), a 1.00 m de altura (SUPUESTO), de 15 cm.
- **Cámara:** la C920 calibrada (fx 623.4, 640×480, FOV 54.3°), en 3D con pitch.
- **Se ve una marca si:** entra **completa** en la imagen, mide ≥ `PX_MIN` = 20 px y la incidencia
  es ≤ `ANG_MAX` = 60°. Los dos son SUPUESTO; los mide maje.
- **EKF:** el de `ekf.py`, con la odometría sesgada de `sim_sintetico.py` (escalada para dar el
  mismo ruido por segundo) y ruido de medición que crece con la distancia.
- **Criterio:** error lateral **al llegar al hueco** < 4.5 cm en **todas** las llegadas. Son 2
  recorridos de maje + 12 del barrido (bahías 2, 4 y 6), × 6 semillas = **84 llegadas** por celda.

**Montajes** (posición respecto del eje de carga; altura 1.0 m salvo donde se indica):

| | Cámaras |
|---|---|
| **A** | lateral izquierda en la capota (−0.75, +0.53, 90°) + **trasera derecha hacia atrás** en el culo (−1.50, 0, 180°). La idea de maje |
| **A2** | la misma lateral + **trasera en diagonal** (−135°, hacia atrás y a la derecha) |
| **B** | dos laterales, una a cada lado (lo de `sim_sintetico.py`) |
| **C** | dos laterales **altas en la jaula** (2.2 m, ±0.40), inclinadas 47° hacia abajo |
| **D** | **frontal** en el mástil (2.2 m, mirando a las uñas, −10°) + lateral izquierda (`docs/03`) |

### El resultado: espaciado máximo que llega al hueco a ±4.5 cm

| Montaje | **Espaciado máximo** | Error máx. ahí | Tramo ciego más largo (1 bahía) | 0 / 1 / 2 cámaras (1 bahía, en movimiento) | En el giro | En la alineación | **Una sola cámara en el giro** |
|---|---|---|---|---|---|---|---|
| A · lateral + trasera | **2 bahías (4.94 m)** | 3.99 cm | 4.3 m · 8.3 s | 58 / 32 / 10 % | 42 / 36 / 22 | 92 / 8 / 0 | **no alcanza:** baja a 1 bahía con cualquiera de las dos |
| **A2 · lateral + trasera diagonal** | **3 bahías (7.41 m)** | 3.85 cm | 4.2 m · 7.8 s | 35 / 49 / 16 % | 35 / 49 / 16 | 92 / 8 / 0 | **alcanza con la lateral** (3); con la diagonal sola, 2 |
| B · dos laterales | 2 bahías (4.94 m) | 2.30 cm | 3.3 m · 6.0 s | 42 / 45 / 12 % | 28 / 56 / 16 | 88 / 12 / 0 | alcanza (2 con cualquiera) |
| C · laterales altas | 2 bahías (4.94 m) | 2.66 cm | 4.5 m · 8.9 s | 38 / 52 / 10 % | 30 / 54 / 16 | 93 / 7 / 0 | alcanza (2 con cualquiera) |
| D · frontal + lateral | **1 bahía (2.47 m)** | 2.78 cm | 3.8 m · 5.5 s | 61 / 39 / 0 % | 50 / 50 / 0 | 92 / 8 / 0 | la frontal sola: ½ bahía |

El EKF por espaciado (error máximo sobre 84 llegadas, en cm; lo que pasa de 4.5 cm va en negrita):

| | ½ (1.24 m) | 1 (2.47 m) | 2 (4.94 m) | 3 (7.41 m) | 4 (9.88 m) | una por cara (control) |
|---|---|---|---|---|---|---|
| A | 1.2 | 2.3 | 4.0 | **5.7** (2/84) | **6.4** (6/84) | **25.1** (24/84) |
| A2 | 1.4 | 2.2 | 2.7 | 3.9 | **6.2** (3/84) | **25.1** (27/84) |
| B | 1.3 | 1.9 | 2.3 | **4.7** (1/84) | **5.1** (1/84) | **25.1** (24/84) |
| C | 1.8 | 2.3 | 2.7 | **11.9** (5/84) | **7.1** (3/84) | **25.1** (26/84) |
| D | 2.1 | 2.8 | **4.6** (1/84) | **6.5** (5/84) | **6.4** (9/84) | **25.1** (23/84) |

### Lo que dicen los números

1. **Al llegar frente al hueco, nadie ve marcas: alrededor del 90 % de la alineación va ciega con
   los cinco montajes.**
   - La lateral queda mirando a lo largo del pasillo.
   - La trasera queda a centímetros del rack de enfrente: la marca no entra entera.
   - El EKF llega bien porque **trae la pose del giro**; la alineación final es navegación por
     odometría de 1 a 3 m.
   - Por eso el espaciado manda: con marcas cada 3 o 4 bahías, el último arreglo puede quedar
     demasiado lejos del hueco.
2. **La trasera derecha hacia atrás (A, la idea de maje) no ve nada en el tránsito.**
   - Con 54° de FOV, mirando a lo largo del pasillo, las caras quedan siempre con más de 63° de
     incidencia, por encima de `ANG_MAX`.
   - **Girada 45° hacia el costado (A2) se vuelve el mejor montaje:** 3 bahías, 82–90 % de
     cobertura en recta, y la lateral sola alcanza en el giro.
   - La idea de maje sirve: hace falta la diagonal.
3. **¿Hace falta que las dos vean durante el giro?**
   - **Con A2, B y C, no:** una cámara en el giro da el mismo espaciado, salvo la diagonal sola
     de A2, que baja a 2 bahías.
   - **Con A, sí:** sin las dos en el giro baja de 2 bahías a 1.
   - Las dos a la vez en el giro pasan solo el 16–22 % del tiempo en cualquier montaje.
4. **La cámara cerca de la cara ve una franja angosta.**
   - A 0.97 m de la cara (lateral en el carril central), la C920 cubre 0.99 m de rack: con una
     marca por bahía ve algo el 35–39 % del recorrido recto.
   - En el carril de giro, la lateral del lado lejano (a 1.5 m) sube al 61 %, y la del lado
     cercano (a 0.40 m) baja al 8 %.
   - Por eso **la marca de 30 cm no ayuda a las laterales:** no entra entera en la imagen. Con A,
     un recorrido llega a 21 m ciegos.
   - Con 30 cm, B pasa de 2 a 3 bahías y A queda en 2.
5. **El planificador hace el tránsito por el carril de giro, no por el central.** El traslado se
   corre de carril al principio de la recta. La idea de maje (central para tránsito, carril de giro
   solo para alinearse) **no está forzada en el planificador**, y con laterales eso cambia la
   cobertura en los dos sentidos (punto 4). Queda anotado; no se cambió.

### Cuánto depende de lo no medido

| | A: espaciado máximo | B: espaciado máximo | A: 0/1/2 a 1 bahía |
|---|---|---|---|
| pesimista: `PX_MIN` 30 px, `ANG_MAX` 45° | 1 bahía | 2 bahías | 64 / 34 / 2 % |
| **base: 20 px, 60°** | **2 bahías** | **2 bahías** | 58 / 32 / 10 % |
| optimista: 15 px, 75° | 3 bahías | 4 bahías | 33 / 44 / 23 % |
| marca de 30 cm (base) | 2 bahías | 3 bahías | 60 / 31 / 9 % |

**El resultado se mueve un factor de 2 a 3 con `PX_MIN` y `ANG_MAX`.** Es lo primero que hay que
medir.

### Controles

| Control | Tiene que | Dio |
|---|---|---|
| una marca por cara (a mitad del pasillo) | fallar | **falla en los 5 montajes**: 25 cm, 23–27 de 84 llegadas fuera |
| FOV de 5° (montaje A, 1 bahía) | tramos ciegos largos | **32 m y 57 s ciegos**, contra 4.3 m con 54.3°; 99.9 % del tiempo sin marcas |
| sin marcas (solo odometría) | fallar | **75 de 84 llegadas fuera**, máx. 40 cm |

### Decía / es / qué lo tumbó (contra `docs/03`)

| Decía | Es | Qué lo tumbó |
|---|---|---|
| Una frontal + una lateral; «en cada ángulo del arco hay al menos una cámara con un ArUco a la vista»; la frontal ve la cabecera en el pasillo y la bahía en el giro (`docs/03`) | **Sin marcas en la cabecera, la frontal ve las caras siempre de refilón: es el peor montaje** (1 bahía; sola en el giro, ½). Y en la **alineación final, ~90 % del tiempo no ve marcas ninguna cámara**, de ningún montaje | maje sacó las marcas de las cabeceras (lejos). `visibilidad.py`: la frontal del D nunca ve con las dos a la vez (0 %), y de frente al hueco las cámaras quedan pegadas o mirando a lo largo |
| La cámara trasera mirando hacia la tracción (idea de maje) | **Recta hacia atrás no ve nada en el tránsito; en diagonal (45° hacia un costado) es el mejor montaje** | con FOV 54° a lo largo del pasillo, la incidencia sobre las caras supera siempre 63° |
| `sim_sintetico.py`: dos laterales, «ven marcas entre 0.3 y 3 m, ±50°» | Ven una franja de ~1 m de rack: con una marca por bahía, el 35–39 % del recorrido recto en el carril central | el FOV real de la C920 (54.3°) y la distancia a la cara |
| 5 m sin marcas es demasiado (oclusión del EKF, 02-nov) | Coincide en el orden de magnitud: **con marcas cada 2 bahías (4.94 m) A, A2, B y C cumplen** (2.3–4.0 cm de máximo); **cada 3 bahías (7.4 m), solo A2** (3.9 cm), y D ya falla a 2 bahías | `visibilidad.py`, barrido de espaciado |

### Lo que mide maje en casa, y qué reemplaza

| Medición | Reemplaza |
|---|---|
| Distancia máxima de detección de frente, marca de 15 cm | `PX_MIN = fx · 0.15 / d_max` (hoy 20 px → d_max 4.7 m) |
| A ~1.5 m, girar la marca hasta que deje de detectarse | `ANG_MAX` (hoy 60°) |
| Error de distancia y lateral en esos bordes | `SIG_REF` (hoy el pesimista de `aruco_precision.py`) |

Con esos números: cambiar `PX_MIN`, `ANG_MAX` y `SIG_REF` al principio de `visibilidad.py` y
volver a correr.

**Supuestos además de esos:**
- **Geometría:** marcas a 1.00 m de altura; montajes y alturas de cámara inventados; las rutas
  heredan todos los SUPUESTOS de `analisis/rutas_resultados.md` (7 bahías, `PROF_BAHIA`).
- **Sin modelar:** la oclusión por el mástil o el IBC (la frontal del D es optimista) y la luz.
- **Odometría:** los sesgos de `sim_sintetico.py`.
- **Muestra:** 84 llegadas por celda. Un «cumple» es 84/84, no una garantía. Lo que pasa raspando
  (A2 a 3 bahías: 3.85 cm) **se confirma con más semillas antes de imprimir marcas**.

### Con las rutas v2 (postes, retranqueo, giro sin reversa) — 05-nov, tarde

`py percepcion/rutas_densas.py --v2` y `py percepcion/visibilidad.py --v2` (~5 min). Recorridos de
`analisis/planificador_rutas.py` modelo v2, con XPIV 1.60 (ver `analisis/rutas_resultados.md`, v2),
con y sin la regla del carril central. Solo A2 y B, los dos mejores. Números en
`visibilidad_v2.json`, figuras en `visibilidad_A2_v2.png` y `visibilidad_B_v2.png`.

**Sí cambia el espaciado máximo: baja.**

| Montaje | v1 (rutas por el carril de giro) | **v2** | v2 con marcas **alternadas** (cara R corrida medio paso) |
|---|---|---|---|
| A2 · lateral + trasera diagonal | 3 bahías (3.85 cm) | **2 bahías** (3.25 cm; a 3 bahías, 4.70 cm, 1/84) | 1 bahía (a 2 bahías, 4.86 cm) |
| B · dos laterales | 2 bahías (2.30 cm) | **1 bahía** (a 2 bahías, 5.02 cm, 1/84) | **2 bahías** (2.36–2.64 cm) |

Con y sin la regla del carril central da lo mismo, salvo décimas de milímetro: con el giro de v2
las rutas ya van por el eje.

**Por qué baja:**
- **El tránsito ahora va por el eje del pasillo.** Las dos laterales quedan a 0.97 m de su cara,
  donde la C920 cubre una franja de 0.99 m. En v1 iba por el carril de giro, y la lateral del
  lado lejano veía más (punto 4 de arriba).
- **El giro es casi una rotación en el lugar** (0.27 m): hay menos tiempo mirando marcas al girar.
- **Con las marcas a la misma x en las dos caras, las dos laterales de B ven juntas o ninguna.**
  En tránsito: 24 % las dos, 6 % una, **70 % ninguna**. Las cámaras se duplican en vez de
  complementarse.
- **Alternar las marcas de las dos caras arregla a B** (de 1 a 2 bahías; 1 bahía: 54 / 45 / 1 %)
  **y empeora a A2** (de 2 a 1), cuyas dos cámaras miran distinto.
- **Dónde van las marcas tiene que decidirse junto con el montaje**, no por separado.

Las diferencias entre celdas son de milímetros sobre 84 llegadas: un «1/84 fuera» es borde, no
veredicto. Con marcas cada **1 bahía, cumplen los dos montajes con cualquier disposición**
(1.7–2.6 cm). Hasta medir `PX_MIN` y `ANG_MAX`, esa es la recomendación segura.

| Decía (05-nov, v1) | Es (v2) | Qué lo tumbó |
|---|---|---|
| A2 llega a ±4.5 cm con marcas cada 3 bahías; B, cada 2 | **A2 cada 2, B cada 1** (cada 2 si las marcas se alternan entre caras) | las rutas v2 van por el eje y giran casi en el lugar |
| Las dos laterales de B son mejor que una (v1) | **Por el eje, con marcas a la misma x, son redundantes**: ven las dos o ninguna | la simetría del montaje y del mapa |

## Montajes de cámaras con el modelo v3b y el pasillo del DXF (09-nov, `visibilidad_v3.py`)

Pregunta de maje: ¿por qué las cámaras de A2 no están a 90° entre sí? Se rehizo la comparación con el
turno de `sim/sim_datos.json`: rutas del planificador v3b (2.91 m, culo de la ficha, timón a 90°), el
pasillo B del DXF (13 bahías por lado, pared en las dos puntas, zonas de descarga y carga del lado R), y
cuatro pedidos (2 salidas, 2 entradas, 430 s). Marcas sobre los postes reales. **Lo ciego se mide en
metros de rueda motriz y en grados girados**: con el giro sobre el eje de carga, ese eje casi no se mueve
y «metros» escondía 8–15 s girando sin ver nada.

Con marcas en cada poste (cada 1 bahía):

| Montaje | Entre sí | Sin marcas en el tránsito | Sin marcas en el giro | Tramo ciego más largo | Alineación y toma |
|---|---|---|---|---|---|
| **A2** · lateral izq. + trasera diagonal −135° | 135° | **19 %** | 53 % | 2.4 m de rueda · 75° · 7.9 s | nada (0 %) |
| A2 en espejo (diagonal +135°) | 45° | 40 % | 52 % | 2.7 m · 86° | nada |
| A2-der · lateral der. + diagonal +135° | 135° | 33 % | 56 % | **2.2 m** · 69° | nada |
| **A** · lateral + trasera recta (la idea original) | **90°** | 70 % | 57 % | 2.9 m · 65° | nada |
| A-der · lateral der. + trasera recta | **90°** | 56 % | 56 % | 3.1 m · 70° | nada |
| **V90** · dos traseras diagonales ±135° | **90°** | **12 %** | 53 % | 3.5 m · **115°** · 11 s | nada |
| B · dos laterales ±90° | 180° | 44 % | 59 % | 2.4 m · 75° | nada |
| **D** · frontal alta + lateral (`docs/03`) | **90°** | 73 % | 73 % | **7.0 m · 203°** · 21 s | nada |
| A2 + frontal en la torre, 54° | — | 17 % | 44 % | 2.4 m · 75° | nada |
| **A2 + frontal en la torre, gran angular 90°** | — | 15 % | **38 %** | 2.4 m · 75° | **ve el 35 % de la alineación y el 25 % de la toma** |

Con marcas cada 2 bahías todo empeora (A2: 55 % ciego en el tránsito, 4.6 m · 155°; el tramo ciego más
corto lo da A2 en espejo, 3.6 m · 118°). Números completos en `visibilidad_v3.json`.

### Lo que dice

- **Estar a 90° no es lo que importa; importa adónde miran respecto de las caras.** De los pares a 90°, el
  que tiene una cámara mirando a lo largo del pasillo (A y D: trasera recta o frontal) es de los peores,
  porque ve las caras de refilón. V90 (dos diagonales a 90°) es el que más ve en el tránsito, pero deja el
  tramo ciego más largo en el giro (115°).
- **A2 sigue siendo el mejor par en el balance**, y queda como está en la simulación. A2-der es casi igual,
  con el tramo ciego un poco más corto; se decide con las marcas reales y cuando el EKF corra con v3.
- **Ningún par de cámaras ve una marca en la alineación ni en la toma** (0 %, todos los montajes). Es lo
  que ya decía la visibilidad v1 (~90 %), ahora en 100 %. El equipo llega al hueco con lo que traiga la
  odometría desde la última marca, que se vio en el giro.
- **Lo único que ve algo frente al hueco es una tercera cámara en la torre con gran angular** (90°): un
  cuarto de la toma. Con la óptica de la C920 (54°) no alcanza: las marcas de los postes quedan a ~44° del
  eje.

### El EKF con la rueda motriz, y el error al llegar (09-nov, después)

`odometria.py` y `ekf.py` integraban con `tan(δ)` y la velocidad del eje de carga: con el timón a 90° (el
giro v3, rotación sobre el eje de carga) eso no sirve. **Ahora tienen un modo `rueda=True`**: la entrada es
la velocidad de la **rueda motriz** (lo que mide el encoder), `ds_eje = ds·cos δ`, `dθ = −(ds/WB)·sin δ`.
Por defecto todo sigue igual: **`sim_sintetico.py` da idéntico, línea por línea, y PASA 30/30**.

`prueba_ekf_rueda.py`, con sus controles:

| Prueba | Resultado | Control de falsación |
|---|---|---|
| odometría contra `planificador_rutas.step(rueda=True)` | 0.0 (idéntica); contra la vieja con v·cos δ, 4e−16 | la vieja en 90°: Δθ = 10¹⁴ rad |
| jacobianos F y G contra diferencias finitas, con δ = 90° | 6e−10 | con ∂/∂b de signo cambiado: 0.14 |
| giro de 90° a ciegas (8 s), sesgo 0.5° y escala 2 %, 30 semillas | máx **1.3 cm**, 100 % dentro de 3σ | el filtro viejo: mediana 17.8 cm, máx 33 cm |

**Dato en tensión con lo esperado:** el control del filtro viejo se escribió esperando que «no diera número».
Da número, pero se va 5–33 cm: cerca de 90° el término `1 + tan²δ` de su jacobiano vale ~10⁴, la covarianza
explota y deja de usar las marcas. El control se corrigió a «no cumple ±4.5 cm».

**El error al llegar a la bahía** (`visibilidad_v3.py --ekf`): el turno del DXF, 8 llegadas (4 tomas, 4
dejadas), 6 semillas = 48, medido al empezar EXTIENDE, a lo largo del pasillo (lo que alinea las uñas
con los huecos del IBC):

| Montaje | Marcas cada 1 bahía: máx · p95 | Cada 2 bahías: máx · p95 · fuera de ±4.5 |
|---|---|---|
| **A2** | 1.40 · 1.36 cm | 2.82 · 2.11 cm · 0/48 |
| A2-der | 2.16 · 1.68 | 2.45 · 2.08 · 0/48 |
| A2 en espejo | 1.80 · 1.37 | **6.24** · 1.59 · **1/48** |
| B (dos laterales) | 2.22 · 1.07 | **1.56 · 1.39** · 0/48 |
| V90 | 1.84 · 1.43 | 3.06 · 1.70 · 0/48 |
| A (a 90°) | 1.48 · 1.33 | 2.68 · 1.73 · 0/48 |
| D (a 90°) | 1.88 · 1.33 | 2.60 · 1.85 · 0/48 |
| A2 + frontal gran angular | 1.43 · 1.09 | 2.36 · 1.25 · 0/48 |

**Control de falsación: A2 con una sola marca por cara → máx 25 cm, 14/48 fuera.** La prueba sí puede fallar.
Con sesgos 4 veces mayores (2° de dirección, 5 % de escala), A2, B y D a 2 bahías siguen en 0/48 (máx 3.2 cm):
el EKF estima los sesgos mientras ve marcas.

### Lo que cambia

- **Con la odometría bien modelada, todos los montajes llegan dentro de ±4.5 cm con marcas cada 1 o 2
  bahías** (salvo A2 en espejo, 1/48 a 2 bahías). La cobertura decía que A y D eran de los peores, y lo son
  en *cuánto ven*; pero lo que se ve alcanza para estimar los sesgos, y los tramos ciegos (≤ 8 m de rueda)
  son cortos para que la odometría corregida se vaya.
- **El montaje deja de ser la decisión crítica para la precisión al llegar**; pasa a decidir por robustez
  (cuánto tiempo sin marcas, una cámara tapada) y por lo práctico de montarlo. A2 sigue siendo el mejor
  balance de cobertura; **B es el más preciso a 2 bahías**.
- **No hace falta la tercera cámara para llegar**, según este modelo. Sí sería la única que ve el hueco.
- **En tensión:** todo depende de supuestos (montajes, `PX_MIN`, `ANG_MAX`, ruido de la medición escalado con
  la distancia, sesgos). Y la verdad del recorrido se re-ancla a las muestras del planificador cada tramo
  (salto máx 3.9 mm), un error extra que la odometría no ve: hace el resultado un poco pesimista.
