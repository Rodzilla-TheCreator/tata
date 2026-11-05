# Encargo — visibilidad de ArUco a lo largo de las rutas: cuándo ve cada cámara y qué espaciado hace falta

**Para la sesión de i3, DESPUÉS de `analisis/tarea_rutas_bahias.md`** (usa sus recorridos).
Autocontenido. Python (`numpy`, `matplotlib`), sin montacargas ni Isaac. Español, al estilo del
repo. Leé `CLAUDE.md` y `percepcion/LEEME.md` primero.

## La idea (maje, 05-nov)

- **No hay ArUco en los extremos del pasillo**: quedarían demasiado lejos. Las marcas van **solo en
  las caras de los racks**, de los dos lados.
- Las **dos cámaras no son "una al lado y una al frente"**: son **más de 90° de cobertura** para el
  EKF. Una lateral y otra hacia el lado de la tracción (no hacia las uñas: el IBC y el mástil
  tapan; hacia las uñas está la cámara de uña de fábrica).
- **Carril central para tránsito, dos carriles de giro para alinearse** (`tarea_rutas_bahias.md`
  §2). En la alineación es aceptable quedarse con **una** cámara viendo marcas.

Lo que hay que contestar con números: **cuándo ve marcas cada cámara, cuándo ven las dos, si hace
falta que las dos vean durante el giro, y con qué espaciado de marcas.**

## Qué construir — `percepcion/visibilidad.py`

1. **Mapa:** marcas en las dos caras del rack (pasillo de 3.00 m), a una altura, con espaciado
   `S` y lado `L` (15 cm de base) configurables. Bahías de 2.35 m (`CLAUDE.md`).
2. **Cámaras:** montaje configurable por cámara: posición respecto del eje de carga, ángulo de
   guiñada (yaw) y FOV. Arrancá con la **C920 calibrada**: FOV horizontal **54.3°**, `fx = 623.4`
   (`percepcion/LEEME.md`, 03-nov). Montajes a comparar como mínimo:
   - A · lateral + trasera (la idea de maje)
   - B · dos laterales, una a cada lado (lo que supuso `sim_sintetico.py`)
   - C · lateral alta en la jaula, inclinada hacia abajo (gana distancia a la cara del rack)
3. **Cuándo se ve una marca:** dentro del FOV, completa en la imagen, a una distancia donde mida
   al menos `PX_MIN` píxeles, y con un ángulo de incidencia menor que `ANG_MAX`. **`PX_MIN` y
   `ANG_MAX` no están medidos todavía**: parámetro `SUPUESTO`, y que el resultado diga cuánto
   depende de ellos. maje los va a medir en casa (sección de abajo).
4. **Recorridos:** los de `analisis/planificador_rutas.py` (caso `3L → 5R → descarga` y el barrido
   de bahías), con la pose a lo largo del tiempo.
5. **Salida por recorrido y por montaje:**
   - % del tiempo con 0, 1 y 2 cámaras viendo al menos una marca, **separado por tramo**:
     tránsito (central), cambio de carril, giro, alineación final;
   - el **tramo ciego más largo**, en metros y en segundos;
   - una figura del recorrido coloreada por cuántas cámaras ven (0/1/2).

## La pregunta que cierra: qué espaciado hace falta

**Barré el espaciado `S`** (y el lado de la marca) y, para cada valor, corré el **EKF**
(`percepcion/ekf.py`) a lo largo del recorrido con esas observaciones (odometría ruidosa como en
`sim_sintetico.py`). El criterio no es "ver siempre", es que **el EKF llegue alineado a la bahía**
dentro del requisito: **±4.5 cm lateral** (`analisis/aruco_precision.py`).

Entregá: el **espaciado máximo** que cumple el requisito, por montaje, y si la alineación aguanta
con una sola cámara o necesita las dos durante el giro.

**Controles de falsación:**
- Espaciado enorme (una marca por pasillo) → **tiene que fallar** el requisito. Si pasa, el EKF no
  está dependiendo de las marcas.
- FOV de 5° → tiene que haber tramos ciegos largos. Si no, la visibilidad no se está calculando.

## Lo que mide maje en casa (y alimenta los SUPUESTOS)

Con la C920 calibrada y una marca de 15 cm:
- **Distancia máxima de detección** de frente → da `PX_MIN` (`fx · L / d`).
- **Ángulo máximo**: a ~1.5 m, girar la marca hasta que deje de detectarse → `ANG_MAX`.
- Y el error de distancia y lateral en esos bordes.

Cuando lleguen esos números, se reemplazan los `SUPUESTO` y se vuelve a correr.

## Entregables

- `percepcion/visibilidad.py`, figuras por montaje, y una sección en `percepcion/LEEME.md` con la
  tabla montaje × espaciado → ¿cumple ±4.5 cm?, tramo ciego más largo, % con 0/1/2 cámaras.
- Si algo contradice `docs/03` (frontal + lateral), anotalo con decía / es / qué lo tumbó.
- Commit y push a `main`.

## Lo que NO es esta tarea

- No es Isaac/Gazebo: esto es la primera pasada en 2D. Isaac viene después, para luz y oclusiones
  reales, con los montajes que salgan de acá.
- No es medir nada: lo que no esté en el repo es `SUPUESTO`.
