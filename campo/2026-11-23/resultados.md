# 23-nov · Diagnóstico de tramas — resultados

Log: `herramientas/can/logs/escucha_equipo_20261123-111756.log` (676 237 tramas, 33 pasos, 11:18–11:28).
Salida completa de `descifrar.py`: `descifrado.txt`. Montaje: multipiloto original con su CAN, cadena aislada
al DB9, **GND_bus al pin 2 del DB9**, `escucha_can.ino` (LISTEN_ONLY).

## Lo que maje vio en el equipo (tal cual)

- **Adelante / atrás del joystick se hicieron mirando hacia la pantalla, no hacia las uñas.** Con esa
  referencia: **joystick atrás = uñas ARRIBA**, **joystick adelante = uñas ABAJO**, **joystick izquierda =
  marcha en sentido opuesto a las uñas**, **joystick derecha = marcha hacia las uñas**.
- **Palanca trasera** = pantógrafo adelante / atrás (bien nombrada en el guion).
- **N** = pantógrafo (desplazador) a la izquierda · **S** = a la derecha · **W** = inclina las puntas de las
  uñas hacia arriba · **E** = inclina las puntas hacia abajo.
- **Entre el paso 17 y el 18** (con el pie en el pedal, sin marca): apretó en la pantalla el botón que **quita
  el parking** y el de la **tortuga (marcha lenta)**. Lo que cambió por eso no está atribuido a ningún paso.
- **Paso 25 (joy izquierda con pedal, 37.5 s):** espacio reducido, tuvo que tocar otros mandos antes del Enter
  de fin. La lectura del joystick está, pero ese paso mezcla acciones.

## Lo que dice `descifrar.py` (dato, sin interpretar de más)

**El multipiloto (`182`, nodo 2), sin pedal, cada mando en su byte** (todos «vuelve», LIMPIO):

| Mando | Byte(s) del `182` |
|---|---|
| N / S | b5 bit `08` / `04`, y b7 = FF |
| E / W | b5 bit `02` / `01`, y b3 = FF |
| pito | b4 bit `01` |
| joy adelante / atrás | b0 (magnitud) + b4 bit `08` / `10` |
| joy izquierda / derecha | b1 (magnitud) + b4 bit `04` / `02` |
| palanca adelante | b2 (magnitud) + b4 bit `40` |
| palanca atrás | **no aparece en el `182`** (sí en `29E`/`39E` del nodo 30) — revisar a mano |

Coincide con la tabla de `herramientas/can/multipiloto.md`. **Lo nuevo es qué hace cada uno** (arriba): el eje
adelante/atrás (b0) es **elevación** y el izquierda/derecha (b1) es **marcha**. Con pedal, b0 mueve el nodo 7
(bomba: `187`, `207`, `387`) y b1 el nodo 8 (tracción: `188`, `208`, `288`), que lo confirma.

**Dirección (timón), pasos 13–15 y 29–31** (SE QUEDA, igual con y sin pedal):

| | `184` b3 (nodo 4) | `49E` b3 (nodo 30) | `205` b6 (Master → nodo 5) |
|---|---|---|---|
| centro → izquierda | 07 → 00 | 0D → 00 | 71 → 81 |
| izquierda → derecha | 00 → 0D | 00 → 19 | 81 → 41 |
| derecha → centro | 0D → 07 | 19 → 0C | 41 → 74 |

`184` b2 y `49E` b2 barren todo el rango a la par: **candidatos a un ángulo de 16 bits** (b2 bajo, b3 alto).

**El pedal** (candidatos de `descifrar.py`: cambian al pisar Y al soltar): `184 b2`, `187 b0`, `205 b6`,
`207 b0`, `208 b5`, `20A b0`, `49E b3`. Los que cambian **solo** con el pedal, de un valor a otro y de vuelta:

| Trama | Pisar | Soltar | Quién la manda |
|---|---|---|---|
| `187` b0 | 03 → 07 (bit `04`) | 07 → 03 | nodo 7 (elevación) |
| `207` b0 | 01 → 09 (bit `08`) | 09 → 01 | Master → nodo 7 |
| `207` b4, b5 | 00 → 32 | — (no listado al soltar) | Master → nodo 7 |
| `208` b5 | 20 → 08 | 08 → 20 | Master → nodo 8 (tracción) |
| `20A` b0 | 6A → 55 | 55 → 6A | Master → nodo 10 |

`184 b2`, `205 b6` y `49E b3` también se mueven con el timón: no son del pedal. **Ninguna trama es el sensor
del pedal en crudo**: lo que se ve es al Master habilitando elevación y tracción cuando el pedal está pisado.
Para probar el pedal emulado sin moverse, el testigo más limpio es **`207` b0 bit `08`** (y `208` b5).

## La velocidad y los sensores de las ruedas de carga (mirado a mano, paso 26)

| Señal | Qué hace al marchar | Lectura |
|---|---|---|
| `188` b2–b3 (nodo 8, con signo) | sube con el joystick (hasta ~105), se va negativo al frenar (−16) y vuelve a 0 | **velocidad del motor de tracción**: el candidato a odometría |
| `19E` b2–b3, `19E` b4–b5, `49E` b4–b5 (nodo 30) | la misma curva, un poco corrida (hasta 102, −22) | copias de una velocidad |
| `288` b0 (nodo 8) | 0 → 134 → 0 mientras acelera | ¿corriente o par? |
| `188` b5 (nodo 8) | sube y queda en ~13 varios segundos | ¿corriente / temperatura? |

- **No apareció una señal propia de las ruedas de carga.** Los nodos 5 y 6 («Dirección 2/3, carga der/izq»)
  no transmiten nada; solo el Master les manda. Las dos velocidades de `19E` (b2–b3 y b4–b5) **son iguales en las
  295 muestras en movimiento**: si fueran rueda izquierda y derecha, al girar tendrían que diferir.
- **No concluye:** las marchas fueron cortas (~2 s) y casi rectas. Lo que lo decide: **marchar despacio
  girando** (timón a un lado, 5 s) y ver si `19E` b2–b3 y b4–b5 se separan; y **mirar las ruedas de carga**
  (E2 del 21-nov: ¿hay un sensor con cable o imanes en el cubo?).
- No hay un contador que acumule distancia: para odometría hay que integrar `188` b2–b3, y falta su escala
  (rpm → m/s) con una marcha medida con flexómetro.

## Escala del ángulo de la rueda de dirección (guion `timon`, 11:40, log `escucha_equipo_20261123-114014.log`)

maje: el timón sigue girando después del tope, la rueda no; no se pudo marcar un centro. Tope izquierdo → barrido
lento → tope derecho.

| | `184` b2–b3 (nodo 4, 16 bits con signo, b2 bajo) |
|---|---|
| tope izquierdo (5 s quieto) | **−10 320**, fijo |
| barrido (30 s, 1 541 muestras) | sube **sin un solo retroceso**, de −9 920 a +8 080 |
| tope derecho (5 s quieto) | **+8 060**, fijo |

- **Es el ángulo de la rueda**: valor estable en cada tope y continuo y monótono en el barrido.
- Recorrido tope a tope: **18 380 unidades**. Con los 180° del manual (±90°): **0.0098 °/unidad ≈ 0.01°** →
  izquierda −103.2°, derecha +80.6° (183.8° en total). **Lectura más probable: centésimas de grado.**
- **El cero no está en el medio** (el medio de los topes cae en −1 130, −11.3°). O el equipo no está centrado en
  0, o los topes no son simétricos. **Se cierra con un centro marcado** (rueda recta a ojo con una regla contra el
  chasis, 5 s quieto).
- **El centro (11:44, log `escucha_equipo_20261123-114444.log`, rueda recta a ojo, paralela a las uñas): +120**,
  fijo en 241 muestras. **El cero del equipo es la rueda recta** (+120 ≈ 1.2° con 0.01 °/unidad, dentro de «a ojo»).
- **Eso deja en tensión la escala:** con el cero en el centro, los topes quedan **asimétricos**: −10 440 a la
  izquierda y +7 940 a la derecha, medidos desde el centro. Con 0.01 °/unidad serían −104° y +79°, no ±90°.
  O los topes de este equipo son asimétricos de verdad, o la unidad no es 0.01°. **Se cierra midiendo un ángulo
  conocido:** la rueda en un tope, con transportador o la app de nivel del celular contra la rueda, y anotar
  los grados y el valor del `184` en ese momento.
- **Resuelto (maje, mirando la rueda):** desde el centro, **a la izquierda pasa de 90°, a la derecha se queda
  corta.** Es lo que da 0.01 °/unidad (−104° / +79°), así que **la escala queda en 0.01° por unidad** y la
  asimetría es del equipo.

  | Decía | Es | Qué lo tumbó |
  |---|---|---|
  | topes de ±90° (manual) | **−104° izquierda, +79° derecha** en este equipo | `184` en los topes + lo que vio maje |
  | escala en tensión | **0.01 °/unidad**, cero = rueda recta | idem. Visual, no medido con transportador: si un ángulo medido difiere, se revisa |

- `49E` b2–b3 (nodo 30) también barre (46 743 → 14 675 sin signo) pero con otra escala: no se usa.
- `205` b6 queda en 65 en los dos topes: no es el ángulo.

## Pendiente

- Palanca trasera atrás sin pedal: no aparece en el `182`; mirarla a mano en el log.
- Repetir el paso 25 solo, en un espacio libre.
- Lo que hicieron el parking y la tortuga: un paso marcado para cada uno la próxima vez.
