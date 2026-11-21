# 21-nov-2026 · Banco del rig: pedal, timón, CAN y los tres juntos

**Sin montacargas.** Un ESP32 con los tres circuitos ya conectados. Cuatro pruebas, en orden; cada una
tiene un **control** (si la prueba no puede fallar, no midió nada). Los números van a `resultados.md`.

## Antes de empezar (10 min)

| ✔ | Qué | Por qué |
|---|---|---|
| ☐ | `git pull` | trae `rig.ino` y la GUI de hoy |
| ☐ | **10 kΩ de IN a DC−** en los módulos del pedal | que el IN nunca quede al aire mientras el ESP arranca o se carga |
| ☐ | **Divisor 10 k / 20 k** del VCC de los módulos (después del pulsador) al **GPIO35** | `rig.ino` lo lee: sin él no deja rearmar nunca |
| ☐ | **Dos fuentes separadas**, o pruebas una a la vez: la del «equipo» del pedal (12 V en pin 1 / pin 3) **no comparte tierra** con el ESP. La del LM358 del timón (+11–12 V) **sí** va con la GND del ESP (amarillo) | si una sola fuente alimenta las dos, une las tierras que el relé separa |
| ☐ | El cable del pin 3 del pedal (− del equipo) **en azul**, no amarillo | amarillo es la GND del ESP |
| ☐ | Ningún programa con el puerto abierto (monitor serie del IDE cerrado) | un solo programa por puerto |

Pines del ESP: CAN 22 (TX) / 21 (RX) · DAC 25 verde / 26 café · pie 27 · rearme 32 · paro 35 · LED 2.

---

## Prueba 1 · Pedal (pie.ino + pie.py)

Cargar `herramientas/rig/pie/`. Fuente de 12 V: **+ al pin 1, − al pin 3**. Multímetro: pin 2 (blanco) y
pin 4 (negro) **contra el pin 3**. Pulsador apretado (módulos con 5 V).

```
py herramientas\rig\pie.py COM6          (Windows)      python3 herramientas/rig/pie.py /dev/ttyUSB0
```

| # | Hacés | Tiene que dar |
|---|---|---|
| 1.1 | nada (recién cargado) | blanco **≈ 0 V**, negro **≈ 12 V** (suelto). El ESP dice `SIN_ARMAR` |
| 1.2 | `p` (sin rearmar) | **sigue suelto** |
| 1.3 | `r` y después `p` | **clic**: blanco ≈ 12, negro ≈ 0. LED fijo |
| 1.4 | `m` (mata el latido) | suelta; el ESP imprime `EV P2 suelta: N ms` si hay puente 27→34 → **N ≤ 200**. LED parpadea |
| 1.5 | `v` (vuelve el latido) | **sigue suelto** (no re-pisa solo) |
| 1.6 | `r` | vuelve a pisar |
| 1.7 | soltar el pulsador (paro) | suelta, `DISPARADO`. Apretarlo otra vez: **sigue suelto** hasta `r` |
| 1.8 | carga 10 kΩ de la salida alta al pin 3 | **≈ 2.1 V** (es la 47 kΩ en el camino) |

**Control:** compilar `pie.ino` con `WATCHDOG_MS 5000` → en 1.4 tarda ~5 s: la prueba tiene que dar FALLA.
Volver a 200 después.

## Prueba 2 · Timón (emulador_timon.ino + rueda_timon.py)

Cargar `herramientas/emulador_timon/`. LM358 a +11–12 V, **GND común con el ESP**. Multímetro: verde y
café **contra el amarillo** (GND del ESP).

```
py herramientas\emulador_timon\rueda_timon.py COM6
```

| # | Volante en | Verde | Café |
|---|---|---|---|
| 2.1 | 0° | **4.45** | **2.47** |
| 2.2 | 90° | 2.47 | 4.45 |
| 2.3 | 180° | 0.49 | 2.47 |
| 2.4 | 270° | 2.47 | 0.49 |

Tolerancia ±0.05 V (lo calibrado el 26-oct). Si no da: re-calibrar con el caracterizador, no tocar a ojo.
**Control:** desconectar el cable del GPIO25 → el verde se va lejos de su valor y el café no cambia.

## Prueba 3 · CAN aislado (prueba_can.ino)

Cargar `herramientas/can/prueba_can.ino` (modo self-test: no necesita otro nodo). Monitor serie.
**El divisor 1k/2k que menciona su comentario NO va**: el RX del TJA va directo a VIA del ADuM.

| # | Qué | Tiene que dar |
|---|---|---|
| 3.0 | óhmetro, todo apagado: **GND del ESP ↔ GND_bus** | **abierto** (aislado) |
| 3.1 | B0505S con todo armado: patas 4–3 | **4.75–5.25 V** (si da más, 470 Ω de 4 a 3) |
| 3.2 | VOA (al GPIO21) contra GND del ESP, en reposo | **≈ 3.3 V**, nunca 5 |
| 3.3 | correr `prueba_can` | **20/20** |
| 3.4 | **control:** sacar VDD2 del ADuM y correr otra vez | **0 recibidas** |

## Prueba 4 · Los tres juntos (rig.ino + rig_gui.py)

Cargar `herramientas/rig/rig/`. Al arrancar tiene que decir `EV OJO: REARME_POR_SERIE = 1 (BANCO)`.

```
py herramientas\rig\rig_gui.py COM6
```

**Regla nueva (21-nov):** el CAN y el timón **solo obedecen con el pie ARMADO**. Después de un watchdog o
del paro, nada vuelve solo: hay que rearmar.

| # | Hacés | Tiene que pasar |
|---|---|---|
| 4.1 | «Rearmar (R)» → botón del pedal a PISADO | clic; blanco ≈ 12 / negro ≈ 0 |
| 4.2 | ángulo del sensor `0` → «Armar timón (T)» → «ir a» 90 | el punto verde llega a 90 en ~¼ s; verde ≈ 2.47 / café ≈ 4.45 |
| 4.3 | arrastrar el volante y soltar | el ESP lo sigue con rampa, sin saltos |
| 4.4 | **CAN (si el SH-C30G anda):** SH-C30G a CANH/CANL, **su GND a GND_bus**, R120 ON (≈ 60 Ω apagado). `py herramientas\rig\master_falso_can.py --slcan COMx` (o `--gsusb`). En la GUI «Armar CAN», Enter en el master | en el master: `702 00` → `582 43…` → NMT → cada mando decodificado (`y +100 x -40…`) |
| 4.5 | **desmarcar «latido»** | en ≤ 200 ms: pie suelto, el master ve **182 en cero**, el timón **se queda** |
| 4.6 | marcar «latido» de nuevo y mover el joystick | **nada se mueve**: pie suelto, 182 en cero, timón quieto. «Rearmar» → vuelve todo |
| 4.7 | soltar el pulsador (paro) con el joystick adelante | pie suelto **y 182 en cero** (la hidráulica también para) |
| 4.8 | cerrar la ventana de golpe (o matar el proceso de Python) | lo mismo que 4.5 |
| 4.9 | desenchufar el USB | los relés sueltan |

Si el SH-C30G no anda en Windows, 4.4 queda pendiente (en maquinon es directo: `can0`). El resto de la
prueba 4 se hace igual.

## Lo que se probó antes de cargar nada

`herramientas/rig/prueba_host/` corre la lógica de `rig.ino` con el ESP imitado: **23/23 PASA**. Con
`WATCHDOG_MS 5000` fallan 5; sin la regla del pie ARMADO fallan 3. **No se compiló con el core del
ESP32**: si el IDE o `arduino-cli` tira error, va a `resultados.md` tal cual.
