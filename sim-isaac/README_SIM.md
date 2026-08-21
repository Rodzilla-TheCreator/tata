# TaTa · banco de pruebas Isaac Sim — Propuesta IT

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `PropuestaIT_RETHINK.usda` | La bodega del sector C en USD: 10 filas de rack, 790 ubicaciones, 790 maxicubos y 293 muros reales del DWG. Z-up, metros, con colisión. |
| `tata_sim.py` | Script de arranque de Isaac Sim 6.0 con la suite de sensores parametrizada por nivel de BOM. |

Geometría verificada contra el visor web: Nave este 6 filas × 17 bahías (pasillo 5.54 m), Nave oeste 4 filas × 14 bahías (pasillo 6.34 m), transversal 4.50 m.

## La regla del banco

**En simulación los sensores no cuestan dinero, cuestan GPU.** Por eso el banco no
simula un nivel de BOM: simula el conjunto completo y va apagando sensores hasta que
algo se rompe. El sensor que rompe la misión es el que hay que comprar.

Eso invierte la pregunta: en vez de que el BOM limite la simulación, la simulación
dicta el BOM. Y el cuadro de ablación resultante es la justificación de cada línea
frente a Omar y frente al cliente.

## Modelar geometría en producción, ruido en scrappy

El error clásico es simular sensores perfectos y creerse el resultado. La escena se
modela con la resolución del sensor de producción, pero el **ruido** se ajusta al
sensor que de verdad vas a comprar primero:

```
--nivel produccion --ruido alto     # geometría buena, señal fea = el caso honesto
```

## Orden de experimentos, por riesgo retirado

### 1. Deriva longitudinal en pasillo uniforme  ← EMPEZAR AQUÍ
Un pasillo de 17 bahías es un túnel de rack idéntico. Un LiDAR 3D tiene mucha
restricción lateral y **casi ninguna a lo largo del pasillo**: el SLAM se desliza.
Es el modo de falla clásico de almacén y el que puede matar todo el diseño de
navegación.

- Correr sólo con `lidar3d`, recorrer un pasillo completo ida y vuelta
- Medir el error de posición contra la verdad de la simulación
- **Si deriva más de ~15 cm**, los marcadores fiduciales dejan de ser opcionales

Este experimento vale más que todos los demás juntos porque decide si el kit navega
con $749 de LiDAR o necesita infraestructura en el almacén.

### 2. Cuántos marcadores hacen falta
Si el 1 falla: sembrar AprilTags en cabecera de fila y repetir bajando la cantidad
hasta que vuelva a derivar. Sale un número, no una opinión: la diferencia entre
$180 de etiquetas impresas y $1,200 de reflectores certificados.

### 3. Lectura de ubicación a 6 m con la cámara de mástil
Con `--ruido alto` para meter desenfoque de movimiento. Decide si alcanza la Basler
de $520 o hay que subir al lector industrial de $900.

### 4. Alineación al maxicubo
`cam_uñas` + `cam_frontal`. Mide a cuántos centímetros y grados llega la aproximación.
Es el requisito de la toma automática.

### 5. Ablación de los LiDAR 2D  ← DEJAR PARA EL FINAL
Correr la misma misión con y sin `lidar2d_izq` / `lidar2d_der` y medir qué cambia.
Son $2,400 y hoy el argumento para quitarlos es teórico. Este experimento lo vuelve
un dato.

## Fases del código

1. Escena + sensores estáticos ← **ya está**
2. Articulación: dirección trasera, mástil prismático, uñas
3. SLAM y el experimento de deriva
4. Ablación completa en los 4 niveles
5. ROS 2 + Nav2

## Requisitos

Isaac Sim 6.0, GPU RTX. El script usa `isaacsim.sensors.experimental.rtx`, que es
el namespace de la 6.0 — en versiones anteriores el import cambia.

```bash
./python.sh tata_sim.py --nivel produccion --ruido real
./python.sh tata_sim.py --nivel scrappy    --ruido alto
```
