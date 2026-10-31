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
