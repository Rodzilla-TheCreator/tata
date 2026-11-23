# Qué es lo que vemos en el bus (23-nov-2026)

## Una trama

El bus CAN es un par de cables (CAN_H y CAN_L, en el DB9 los pines 8 y 3) que comparten **todos** los
controladores del equipo. Cada uno habla mandando **tramas**: mensajes cortos que oyen todos.

```
   1234567   182  [8] 64 00 00 00 08 00 00 00   TPDO1 nodo 2
   ───────   ───  ───  ───────────────────────
   ms del    ID   bytes  hasta 8 bytes de datos
   ESP       (quién y qué)
```

- El **ID** (11 bits) dice **quién habla y qué tipo de mensaje es**. En CANopen el ID = tipo + número de
  nodo: `0x182` = `0x180` (TPDO1, «datos que publico») + nodo **2**.
- Los **datos** son hasta 8 bytes. Qué significa cada byte **no lo dice el estándar**: lo decide el
  fabricante. Eso es lo que hay que descifrar (y lo que ya hicimos con el multipiloto).

## Los tipos de mensaje (CANopen)

| ID | Tipo | Qué es |
|---|---|---|
| `000` | NMT | el Master ordena: arrancá, pará, reiniciate |
| `080` | SYNC | el «tic» del Master. Medido: **~50 por segundo**. Muchos nodos publican detrás de cada SYNC |
| `080 + n` | EMCY | un nodo avisa una falla. **El 21-nov: ninguno** en ~85 s |
| `180/280/380/480 + n` | TPDO 1–4 | **datos que el nodo n publica**: posiciones, velocidades, estados |
| `200/300/400/500 + n` | RPDO 1–4 | **datos que el nodo n recibe** (normalmente del Master): consignas |
| `580 + n` / `600 + n` | SDO | preguntas y respuestas puntuales a un objeto del diccionario (`0x2414`…) |
| `700 + n` | latido | «sigo vivo» + mi estado (`05` operacional, `7F` preoperacional) |

## Los nodos de este equipo

| Nodo | Quién | Notas |
|---|---|---|
| 1 | **Master** (`1U16`) | el cerebro: lee los sensores y manda a los demás |
| 2 | **Multipiloto** | publica el joystick y los botones en el `0x182`. **Ya lo imitamos y movió el equipo (21-nov)** |
| 3 | Display | la pantalla; pide datos por el bus (el Diagnose sale de ahí) |
| 4 | **Dirección** (`APS36M`) | publica `0x184` (estado) y `0x284` (velocidad del volante en b3–b4). **No tiene entrada de consigna de giro**: el volante le llega por cable |
| 5, 6 | dirección 2 y 3 | no publican nada; solo reciben |
| 7 | **Elevación** (bomba) | `0x187`: estado + **tensión de batería** (b4–b5 ×0.01 V: 36.46 V). La altura de uña **no** sale (no tiene el sensor) |
| 8 | **Tracción** | `0x188` lo escucha el nodo 4 (la velocidad, para recortar la dirección) |
| 10 | Multipiloto 2 | no publica; recibe `0x20A` |
| 30 | PC de servicio | el lugar de Judit |

**En números (21-nov, equipo funcional):** ~**1090 tramas por segundo**, **38 IDs distintos**, 0 errores.

## Lo que ya está descifrado

| ID | Qué | Cómo se supo |
|---|---|---|
| `0x182` | el **multipiloto** completo: b0 adelante/atrás, b1 izquierda/derecha, b2 palanca trasera, b4 bits de sentido + pito, b5 botones N S E W | grabado con marcas el 06-oct; **imitado y movió el equipo el 21-nov** |
| `0x187` b4–b5 | tensión de batería | SDO del mapeo, 23-oct |
| `0x284` b3–b4 | velocidad del volante | 22-oct |

## Lo que falta, y para qué

| Buscamos | Dónde puede estar | Para qué |
|---|---|---|
| **el bit del pedal** | algún PDO del Master (`0x181`, `0x281`…) o de tracción | probar el emulador del pedal **sin mover el equipo** |
| **el ángulo de la rueda** | `0x284` (los `2028.x`) u otro del nodo 4 | cerrar el lazo del timón emulado; odometría |
| **la velocidad de tracción** | `0x188` (`2160.x`) u otro del nodo 8 | odometría |

La técnica es la del 06-oct: **hacer una cosa a la vez, marcarla, y ver qué byte cambió exactamente ahí.**
Eso es `grabar_can.py … diagnostico` + `descifrar.py` (`DIAGNOSTICO.md`).
