# El multipiloto en el bus — diccionario y arranque · 06-oct-2026

Grabado en el equipo con `escucha_can.ino` (LISTEN_ONLY, RX en GPIO 21 en esa copia de
campo), 921600 baud, guion con temporizador de `grabar_can.py` (`multipiloto_tiempo`).
Log local: `logs/escucha_equipo_20261006-120519.log` (los .log no se versionan).
Nombres de botones puestos por maje: north/south arriba-abajo; east/west la inclinación
(west hacia arriba, east hacia abajo); «trasero» el botón de atrás.

## Trama `0x182` — TPDO1 del nodo 2 (multipiloto), 8 bytes

| Byte | Qué es | Valores |
|---|---|---|
| b0 | joystick **adelante/atrás**, magnitud | 0–255 |
| b1 | joystick **izquierda/derecha**, magnitud | 0–255 |
| b2 | **palanca trasera**, magnitud (continua: parece potenciómetro/Hall) | 0–255 |
| b3 | 255 mientras **east o west** están apretados | |
| b4 | **bits**: `0x08` joystick adelante · `0x10` joystick atrás · `0x04` izquierda · `0x02` derecha · `0x40` palanca trasera adelante · `0x20` palanca trasera atrás · `0x01` **botón trasero** | bits |
| b5 | **botones de arriba**: `0x08` north · `0x04` south · `0x02` east · `0x01` west | bits |
| b6 | sin cambios | |
| b7 | 255 mientras **north o south** están apretados | |

**La magnitud va en un byte y el sentido en un bit.** Ejemplo: joystick atrás a fondo →
`b0 = 255`, `b4 = 0x10`.

Junto con el multipiloto cambian `0x303 b7` (139) y `0x20A` b2/b4/b6 (RPDO del nodo 10,
Multi-Pilot 2). Lectura sin confirmar: el display y el master reaccionando a la palanca.

## El arranque (llave OFF → ON)

```
703 7F                        display en pre-operacional (antes de la llave)
6EF/6F1/69D/6E9/6E3  0E 00…   ¿?  sin identificar
704 00 · 71E 00 · 707 00 · 708 00 · 701 00 · 702 00     boot-ups (702 = multipiloto)
602 40 00 10 00 …             master lee 0x1000 (tipo de equipo) del nodo 2…
602 80 00 10 00 00 00 04 05   …ABORTA por tiempo (el multipiloto bootea tarde)
604/584, 61E/59E, 607/587, 608/588   misma lectura a los nodos 4, 30, 7, 8
602 40 00 10 00 → 582 43 00 10 00 00 00 00 00     reintento: el multipiloto contesta 0
000 01 1C · 01 02 · 01 03 · 01 04 · 01 1E · 01 07 · 01 08    NMT START, nodo por nodo
080 …  y empiezan los PDO
```

**Para imitar al multipiloto (ruta B de `docs/21`):** boot-up `702 00`, contestar la lectura
de `0x1000` con `43 00 10 00 00 00 00 00`, y tras el NMT START mandar `0x182` + heartbeat
`702 05`. **La conversación es corta.** Es observación, no decisión: falta el ciclo de
`0x182` (cada cuánto) y lo que haga el master si los valores no son plausibles.

## Otros datos del bus

- **El nodo 30 existe y arranca** (`71E`, `61E/59E`, `19E…49E`). Candidato: el `KD Medi CO 250K`
- El master manda NMT START al nodo 28 (CanCode) aunque no haya teclado
- Con la llave en ON hay ~1000 tramas/s y 39–53 identificadores
- **Sin el pedal de hombre muerto el timón no publica nada** y el Diagnose de STEER no cambia
- **Pérdidas:** a 921600 se perdieron 23 252 tramas con el bus más cargado. El diccionario no se
  afecta (cada acción ×3), pero para grabar todo hace falta un formato binario o solo resumen
