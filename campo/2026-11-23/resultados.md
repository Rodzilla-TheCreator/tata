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

## Pendiente

- Palanca trasera atrás sin pedal: no aparece en el `182`; mirarla a mano en el log.
- Repetir el paso 25 solo, en un espacio libre.
- Lo que hicieron el parking y la tortuga: un paso marcado para cada uno la próxima vez.
