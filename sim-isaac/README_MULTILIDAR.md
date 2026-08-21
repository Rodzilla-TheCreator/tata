# Banco comparativo de LiDAR — instrucciones

## 1 · Qué descargar

| Qué | Dónde | Peso |
|---|---|---|
| **Isaac Sim 6.0** | `developer.nvidia.com/isaac/sim` — descarga directa o por el Omniverse Launcher | ~30 GB |
| Driver NVIDIA | 535+ (Linux) / 537+ (Windows) | — |
| *(opcional)* ROS 2 Humble o Jazzy | sólo si vas a cerrar el lazo con Nav2 | — |

**Requisitos reales:** GPU RTX con 8 GB+ de VRAM (mejor 12+ si vas a montar los cinco
LiDAR a la vez), 32 GB de RAM, 50 GB de disco. Corre en Windows y en Linux; en Linux
el bridge de ROS 2 es menos peleado.

Isaac Sim es gratis para uso individual.

## 2 · Cómo correrlo

Poné `PropuestaIT_RETHINK.usda` y `tata_multilidar.py` en la misma carpeta.
Desde la raíz de la instalación de Isaac Sim:

```bash
./python.sh /ruta/a/tata_multilidar.py                    # todos, pasillo 0
./python.sh /ruta/a/tata_multilidar.py --pasillo 2 --vel 0.8
./python.sh /ruta/a/tata_multilidar.py --solo os0_128 --headless
```

La trayectoria es **guionada, no manejada**: el montacargas recorre el pasillo de
punta a punta y regresa, a velocidad constante. Eso es a propósito — si el piloto
mete ruido, la comparación entre sensores deja de ser limpia.

## 3 · Qué trae de fábrica y qué hay que escribir

| Clave | Sensor | Estado |
|---|---|---|
| `os0_128` | Ouster OS0-128 | ✓ incluido |
| `os1_64` | Ouster OS1-64 | ✓ incluido |
| `hesai_xt32` | Hesai XT32 | ✓ incluido |
| `rotativo_generico` | Example Rotary | ✓ incluido |
| `nanoscan3_*` | 2D de seguridad | ✓ vía Example Rotary 2D |
| `mid360` | **Livox Mid-360** | ✗ perfil propio |

El Mid-360 tiene patrón **no repetitivo**: una roseta que va llenando cobertura en
vez de barrer parejo. Isaac lo soporta con `emitterStateArrays`, pero hay que sacar
el patrón real de disparo de una grabación del sensor físico, encontrar el período
del ciclo y armar los arrays — y hay tope de 5 MB por prim, así que se parte en 4.
**Es un proyecto, no un archivo de configuración.** Por eso no va primero.

## 4 · Qué resultados esperar

Antes de instalar nada ya calculamos la geometría de tu pasillo (`analisis_degeneracion.py`,
no necesita Isaac). Esto es lo que dice:

| Caso | σ a lo largo | σ a lo ancho | Relación |
|---|---|---|---|
| Rack típico, relieve 8 cm | **0.20 cm** | 0.07 cm | 2.7× |
| Rack casi liso, relieve 2 cm | 0.41 cm | 0.07 cm | 5.9× |
| Paredes perfectamente lisas | **∞ — singular** | 0.07 cm | ∞ |

**Corrección honesta a lo que te dije antes:** el pasillo *no* está degenerado. Yo lo
planteé más grave de lo que es. Lo que te salva son los montantes del rack: cada 1.20 m
hay una cara perpendicular al pasillo, y con 17 bahías por lado eso da suficiente
restricción longitudinal. El eje del pasillo está ~2.7 veces peor restringido que el
transversal, pero eso es **mal condicionado, no indeterminado**.

La degeneración pura sólo aparece si las paredes quedan lisas de verdad. Eso pasa
cuando: la bahía está vacía y no hay carga que dé relieve, la carga va emplayada y
lisa tapando los montantes, o el LiDAR va montado tan alto que sólo ve por encima
de la estructura.

### Entonces qué hay que medir de verdad

1. **Deriva acumulada en ida y vuelta.** El número de arriba es de *una* pose. Lo que
   mata es la integración: el eje malo acumula error 2.7× más rápido. Al volver al
   punto de partida el error de cierre te lo dice sin discusión.
2. **Confusión entre pasillos.** Tus 10 pasillos son geométricamente idénticos. Ese es
   un problema de *reconocimiento de lugar*, no de degeneración — y probablemente sea
   el riesgo mayor. Correr el mismo recorrido en el pasillo 0 y en el 3, mezclar las
   nubes y ver si el algoritmo las distingue.
3. **Bahías vacías.** Correr con el rack al 30% de ocupación. Ahí es donde el relieve
   desaparece y te acercás al caso singular.

Rango esperable de deriva sobre 25 m ida y vuelta, con un LiDAR decente y SLAM bien
tuneado: **2–8 cm de error de cierre**. Si te da más de 15 cm, los marcadores fiduciales
dejan de ser opcionales.

## 5 · El orden

1. `os0_128` solo — el sensor optimista. Si con éste hay problema, es geometría, no sensor.
2. Agregar `hesai_xt32` y `rotativo_generico` — ¿cuánto se degrada al bajar de gama?
3. Bahías vacías al 30%.
4. Pasillo 0 contra pasillo 3 — la prueba de confusión.
5. Recién ahí, armar el perfil del Mid-360 y ver si el barato aguanta.
6. Al final, la ablación de los 2D de seguridad.
