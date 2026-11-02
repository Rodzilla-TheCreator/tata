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
py percepcion/sim_coordinacion.py     # ~2 s; termina con RESULTADO: PASA / FALLA
```

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
