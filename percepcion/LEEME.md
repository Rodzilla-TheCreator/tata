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
