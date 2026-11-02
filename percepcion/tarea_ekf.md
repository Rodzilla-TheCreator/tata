# Encargo — EKF de localización (odometría + ArUco)

**Para la sesión que corre en i3.** Esto es autocontenido: no necesitás el chat donde se originó.
Implementá y validá el EKF **en i3**, con **datos sintéticos** — NO hace falta el montacargas, ni
Isaac, ni GPU. Solo `numpy` (+ `matplotlib` para una figura). Lenguaje y comentarios en **español**,
al estilo del repo.

## Qué es y para qué

TaTa vuelve autónomo un reach truck **EDR18N2**. La localización del kit es **odometría fusionada
con ArUco** por un filtro de Kalman. Esta es la pieza de software que lo hace, y es lo que más
avanza **sin equipo**. Corre en maquinón/superspeed en producción, así que escribilo **portable**
(Python puro, x86 y ARM). Lo probás en i3 contra una simulación sintética.

- **Odometría** = predicción de alta tasa. El equipo reporta en su bus **velocidad de tracción
  (nodo 8)** y **ángulo de dirección (nodo 4)**; con eso y el modelo de bicicleta se integra el
  desplazamiento. (Todavía no hay captura real del bus — por eso se simula.)
- **ArUco** = corrección absoluta. Las cámaras ven marcas en los racks; cada marca tiene una
  posición conocida en el pasillo. Da pose absoluta y mata la deriva de la odometría.
- **Oclusión de ArUco** (no se ve la marca): el filtro **navega con la odometría** hasta la próxima.

## Entregables (en `percepcion/`)

1. **`odometria.py`** — modelo cinemático de bicicleta. Entrada: velocidad `v` (m/s) y ángulo de
   dirección `delta` (rad); salida: incremento de pose `(dx, dy, dtheta)` en `dt`. **Usá la MISMA
   convención cinemática que `analisis/planificador_giro.py`** (no holónomo, radio mínimo; rueda
   directriz atrás). Entre ejes `WB = 1.562 m` (ver `CLAUDE.md`).
2. **`ekf.py`** — clase `EKF` con estado de pose `[x, y, theta]`:
   - `predict(v, delta, dt)` — propaga con el modelo de odometría y suma ruido de proceso `Q`.
   - `update_aruco(pose_medida, R)` — corrige con una pose absoluta medida (de una marca de id y
     posición conocidas). Maneja el ángulo con wrap correcto.
   - Matrices `Q`, `R` configurables; documentá los valores elegidos y por qué.
3. **`sim_sintetico.py`** — genera una **trayectoria verdadera** (ej. entrar a un pasillo, un giro
   de 90°, frenar), produce **odometría ruidosa** y **observaciones ArUco ruidosas** contra un
   **mapa de marcas** (id → `x, y, theta` conocidos), con **tramos de oclusión** (sin ArUco). Corre
   el EKF y **compara estimación vs verdad**. Saca una figura `percepcion/ekf_sintetico.png`
   (verdad, solo-odometría, y EKF) y un resumen de error (RMS lateral y de rumbo).

## Criterio de aceptación — con control de falsación (regla dura del repo)

El test tiene que **poder fallar**:

- **ArUco ENCENDIDO:** el error del EKF queda **acotado** y sigue la verdad (RMS lateral, pongamos,
  < unos cm a escala del pasillo). 
- **ArUco APAGADO (control):** con solo odometría, el error **crece sin cota** (deriva visible en la
  figura). Si apagar el ArUco **no** hace derivar, el test no probó nada — revisá.
- **Durante una oclusión:** el EKF **coast**ea con odometría y **se vuelve a enganchar** cuando
  reaparece una marca.

Imprimí los tres resultados (ArUco on / off / con oclusión) y dejá la figura.

## Convenciones y límites

- Solo `numpy` + `matplotlib`. Nada de ROS, ni Isaac, ni hardware.
- Marco del mundo = el del pasillo (x a lo largo, y lateral), como en los simuladores del repo.
- No inventes números de campo; si necesitás una cota, tomala de `CLAUDE.md` o `analisis/` y citala.
- Commiteá con mensajes claros. Si algo del modelo contradice al planificador, **gana el
  planificador** (es la cinemática ya acordada) — o anotá la discrepancia.

## Referencias en el repo

- `percepcion/detector_aruco.py` — de dónde vendrá la pose ArUco real (CSV: `t,id,dist_m,lateral_m,yaw_deg,reproj_px`). El `update_aruco` tendrá que convertir `(id, dist, lateral, yaw)` + mapa de marcas → pose absoluta del equipo. En el test sintético generás esto directo.
- `analisis/aruco_precision.py` — presupuesto de precisión del ArUco (ruido de medición `R` realista: ±4.5 cm lateral es la cota de la bahía).
- `analisis/planificador_giro.py` — la cinemática de bicicleta ya implementada; reusá su convención.
- `CLAUDE.md` — geometría (`WB`, radio de giro 1.797), y la regla de localización (cámaras + ArUco + odometría).

## Lo que NO es esta tarea

- No es capturar odometría real del bus (eso necesita un equipo que se mueva — después).
- No es el LiDAR/SLAM (fuera de alcance por ahora).
- No es Isaac Sim (ese es el lazo cerrado más rico, paso posterior en maquinón).
