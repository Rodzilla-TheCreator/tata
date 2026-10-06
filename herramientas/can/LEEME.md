# La cadena CAN — el cableado del DB9

**Actualizado el 01-oct-2026.** Los tres planos de esta carpeta (`armado_can.svg`,
`protoboard_can.svg`, `cadena_can_tja1050.svg`) se dibujaron el 22-sep con el pinout
**CiA-303** supuesto. Llevan una franja roja arriba: **su cableado del DB9 quedó superado.**

## Lo vigente

```
TJA1050 CANH  →  DB9 pin 8
TJA1050 CANL  →  DB9 pin 3
GND común     →  DB9 pin 2
pines 5, 6 y 9: NO SE CONECTAN
```

Es el pinout del conector de servicio `X200` de Jungheinrich (ver
`herramientas/manuales_scribd.md`). **Es hipótesis**: la tabla sale de otro modelo, el ECR.
Lo mismo dice `escucha_can.ino` en su encabezado.

## Decía / es / qué lo tumbó

| Pin | Decía (22-sep, CiA-303) | Es | Qué lo tumbó | Firmeza |
|---|---|---|---|---|
| **6** | **GND** del TJA, del conversor y del ESP32 | **+24 V detrás del fusible `4F15`** | 30-sep: con el fusible puesto el FTDI lee DSR = 1; pin 6 ↔ negativo ≈ 216 Ω, que es la carga del riel; maje trazó la pista del 4F15 al pin 6; el manual de operador dice que el 4F15 es «autorización de acceso», 2 A | **medido** |
| 2 | CAN_L | CAN 0 V | pinout del `X200` | hipótesis |
| 7 | CAN_H | sin conectar | pinout del `X200` | hipótesis |
| 3 | sin usar | CAN_L | pinout del `X200` | hipótesis |
| 8 | sin usar | CAN_H | pinout del `X200` | hipótesis |

**Lo del pin 6 no depende de la hipótesis.** Aunque el `X200` resulte equivocado, el pin 6
lleva tensión: un GND ahí une la tierra del ESP32 y de la laptop con +24 V del equipo.

**El error del pin 6 fue de quien hizo los planos**, no de quien soldó: el pin 6 se tomó
como masa porque CiA-303 lo define así, y nunca se había medido.

## Y el argumento viejo del «2 ↔ 7 abierto» estaba mal

`CLAUDE.md` decía que el 2 ↔ 7 abierto no descartaba CAN porque «un stub de diagnóstico
normalmente no lleva terminador». **Eso es falso.** Los terminadores están en las puntas
del bus, no en el stub: midiendo CANH ↔ CANL en cualquier punto de un bus terminado, con
todo apagado, se ven los dos 120 Ω en paralelo, **≈ 60 Ω**. Un abierto entre 2 y 7 sí era
evidencia de que ahí no había CAN. Cuadra con el `X200`.

## 02-oct · «probé todos los pines a GND y ninguno pitó»

Cuadra con el 30-sep: ningún pin tiene tierra. **No tumba el `X200`**, por dos razones:

- **El pitido no ve 60 Ω ni 216 Ω.** El modo continuidad de casi todos los multímetros pita
  por debajo de ~30–50 Ω. El 30-sep el pin 6 ↔ negativo dio **216 Ω** en escala de ohmios,
  y con el pitido no habría sonado. **Las dos mediciones que importan van en la escala de
  200 Ω, no en el pitido**
- **El CAN 0 V puede no estar unido a batería −** con el equipo apagado: puede pasar por la
  electrónica de un módulo, o estar aislado. Es la tensión que ya estaba anotada abajo

Si se probó contra **chasis**, tampoco dice nada: en este equipo el chasis no es el negativo.

**Consecuencia para el cable:** si el 3 ↔ 8 confirma el bus, la primera escucha va **sin GND
conectado** — CANH y CANL solos, laptop a batería, todo flotando. El TJA se auto-polariza
contra el bus por su impedancia de entrada, y en solo-escucha eso suele bastar. Si no
entra ninguna trama, recién ahí se prueba el GND al pin 2.

## 03-oct · MEDIDO: pin 3 ↔ pin 8 ≈ 120 Ω, y la carcasa no es masa

maje, en el equipo, llave OFF, escala de ohmios:

```
DB9 hembra del equipo:  pin 3 ↔ pin 8   ≈ 120 Ω
                        carcasa ↔ negativo de batería: NO es masa
```

| Decía | Es | Qué lo tumbó |
|---|---|---|
| el `X200` (CANL 3, CANH 8) era hipótesis sacada del ECR | **hay un par terminado entre 3 y 8**: el `X200` queda **muy reforzado** en este equipo | 120 Ω medidos |
| esperábamos ≈ 60 Ω (dos terminadores) | **≈ 120 Ω: se ve UN solo terminador** | — |
| la tierra podía estar en la carcasa | **la carcasa no es masa** | medido |

**Dato en tensión:** en la ficha del multipiloto, el par CAN (pines 2 y 3) dio **80 Ω**. Si
el DB9 y el multipiloto estuvieran en el mismo bus, los dos puntos darían lo mismo (el cable
casi no suma). **120 contra 80 dice que son redes distintas, o que una de las dos mediciones
está corrida.** Se resuelve con un cable largo y el óhmetro, llave OFF:

```
DB9 pin 8 ↔ multipiloto pin 2  y  DB9 pin 3 ↔ multipiloto pin 3   (y cruzados)
≈ 0 Ω → mismo bus;  abierto → buses separados
```

**Para el cable soldado:** TJA CANH → 8, CANL → 3 queda como estaba. **La masa no sale de la
carcasa ni de ningún pin confirmado del DB9.** Si hace falta, se toma del **negativo de
batería** con un cable aparte (o del pin 7 de la ficha del multipiloto, que es negativo
confirmado). La primera escucha sigue siendo **sin GND**.

### Resuelto el mismo día: el DB9 y el multipiloto están en EL MISMO bus

maje, cable largo, llave OFF:

```
DB9 pin 3 ↔ multipiloto pin 3   0.2 Ω    ← mismo hilo
DB9 pin 8 ↔ multipiloto pin 2   0.1 Ω    ← mismo hilo
DB9 pin 3 ↔ multipiloto pin 2   120 Ω    ← cruzado: el terminador
DB9 pin 8 ↔ multipiloto pin 3   120 Ω
```

| Pin DB9 | Pin multipiloto | Señal (nombre según `X200`) |
|---|---|---|
| **8** | **2** | **CAN_H** |
| **3** | **3** | **CAN_L** |

- **Escuchar en el DB9 es escuchar el bus del multipiloto.** El cable soldado sirve tal cual
- **El bus tiene UN solo terminador** (120 Ω, no 60). Un CANopen bien armado lleva dos.
  **Falta uno.** Candidato natural: estaba en un componente que se canibalizó (la misma
  hipótesis del `6U10`). El bus anda igual — la pantalla muestra sensores —, pero con
  márgenes peores. **No se agrega un 120 Ω por nuestra cuenta**: se anota y se decide después
- El **80 Ω** de la ficha del multipiloto queda como lectura en tensión. Hay que repetirlo
  igual que estos, sabiendo si la ficha estaba enchufada

## Corrección del 02-oct: el borne «GND» probablemente es el PIN 5, no la carcasa

La sección de abajo supuso que el borne GND iba a la carcasa. **La foto del reverso de la
tarjeta de maje no lo muestra así:** las pistas sugieren que el borne **GND** y el borne
**5** comparten pista hasta el pin 5 del conector, y **no se ve ninguna pista hacia las
lengüetas de la carcasa**. Leído de foto; se confirma en diez segundos con el óhmetro:

```
borne GND ↔ borne 5      ≈ 0 Ω  → GND es un duplicado del pin 5
borne GND ↔ borne 9      ____
borne GND ↔ carcasa      ____
```

Si es el pin 5, **el borne GND también queda vacío en el equipo**, por la misma razón que el
5: en el `X200` es «GND conmutado» y no se sabe qué hay ahí.

## (superado) El borne «GND» del DB9 macho de bornera es la CARCASA, no un pin

El DB9 macho comprado tiene 10 bornes: los 9 pines y uno marcado **GND**. Ese GND va a la
**carcasa metálica** del conector. Al enchufarlo, esa carcasa toca la carcasa del DB9 hembra
del equipo. **Lo que se cablee a ese borne queda unido a lo que sea que tenga la carcasa del
equipo.**

Y eso abre una medición que no se hizo nunca: **la carcasa del DB9 del equipo**. Va
atornillada a la tarjeta, y en muchos diseños la carcasa es la masa. Si ningún pin tiene
tierra, la tierra puede estar ahí.

```
batería desconectada, escala de 200 Ω:
  carcasa del DB9 del equipo (o su tornillo hexagonal) ↔ negativo de batería = ____
  carcasa ↔ pin 2 = ____        carcasa ↔ pin 5 = ____
```

Hasta medirla, **el borne GND de la bornera queda vacío.**

## La medición que confirma antes de soldar

Un minuto, con óhmetro, **batería desconectada**:

```
pin 3 ↔ pin 8   ≈ 60 Ω   →  X200 confirmado: soldar 8 / 3 (y el 2, solo si hace falta)
                (ESCALA DE 200 Ω, no el pitido: el pitido no suena con 60 Ω)
                abierto  →  X200 tumbado: no soldar nada, volver a pensar
```

Es el paso A de `herramientas/pendientes.md`. Con eso el resto del cableado deja de ser
hipótesis.

## Dato en tensión, anotado

- El módulo de acceso ISM dice (manual del ECR, pág. 360) que **en equipos CANopen 250k
  el 0 V no está separado de batería −**. Si el pin 2 fuera el CAN 0 V, debería tener
  continuidad con el negativo. **El 30-sep no la tuvo.** Puede ser que el 0 V llegue por
  un camino que necesita el equipo energizado, o que el pin 2 no sea eso
- **El chino reconoció el cable FTDI como el de Judit** (25-sep). Un cable USB-serie no habla
  con un bus CAN. Las dos cosas no se resuelven adivinando: hay que preguntarle **con qué
  software y qué caja usaba ese cable**, y en qué equipo

## Banco, antes de ir

El orden de `herramientas/pendientes.md`: 120 Ω **temporal** en la protoboard para la
autoprueba (sin terminador el TWAI da errores, porque las líneas no vuelven a recesivo),
`prueba_can.ino` con sus dos corridas, **quitar** el 120 Ω, recablear el DB9 y cargar
`escucha_can.ino`.

---

# 02 al 06-oct · la cadena final, cómo se validó, y por qué no daña el equipo

**Manda sobre los planos viejos.** El plano vigente es **`armado_escucha.svg`**.

## La cadena final

```
ESP32 5V/VIN  → TJA1050 VCC        ESP32 GND → TJA1050 GND
ESP32 GPIO 21 → NADA. El TX del TJA1050 queda AL AIRE
TJA1050 RX    → 1 kΩ → GPIO 22 ;  GPIO 22 → 2 kΩ → GND      (divisor 5 V → 3.3 V)
TJA1050 CANH  → DB9 pin 8          TJA1050 CANL → DB9 pin 3
DB9 pin 2     → sin conectar en la primera escucha
DB9 5, 6, 9   → nunca
sin terminador · laptop a batería · conectar con la llave en OFF
```

| Decía | Es | Qué lo tumbó |
|---|---|---|
| conversor de nivel (BSS138/TXS) entre ESP32 y TJA1050 | **sin conversor**: TX directo, RX por divisor | sacarlo no cambió nada medible, y la hoja de NXP dice que la entrada TXD acepta 3.3 V (`VIH` mín 2.0 V). maje había propuesto el divisor desde el principio |
| TX del TJA1050 conectado al GPIO 21 | **al aire** en el equipo | su transmisor es lento (abajo) y así el módulo no puede transmitir aunque falle el software |
| `prueba_can.ino` valida la cadena | **no pasa con este módulo**, y no hace falta para escuchar | ver abajo |

## Cómo se validó — `diagnostico/`

| Prueba | Sketch | Resultado |
|---|---|---|
| self-test CAN a varias velocidades | `multibaud` | **10/10 a 25k**, 8/10 a 50k, **0/10 desde 100k** |
| qué hace el controlador con 1 trama | `diag_twai` | 396 pérdidas de arbitraje en 50 ms: lee dominante cuando pone recesivo |
| retardo de cada flanco, contador de ciclos | `retardo` | con el módulo: **bajada 0.36 µs, subida ~15 µs**, igual con o sin conversor y con o sin terminación |
| **control: el ESP32 solo**, GPIO21 → GPIO22 | `retardo` | **0.16 µs los dos flancos**: el ESP32 y la medición están bien |
| **receptor del TJA**, otro nodo simulado por GPIO25/26 → 100 Ω → CANH/CANL | `receptor` | reposo RX = 1, dominante RX = 0, **bajada 0.40 µs, subida 0.24 µs**, 500/500 |
| **control negativo**: escucha en la mesa sin bus | `../escucha_can.ino` | 5 min, **0 tramas, 0 errores** |

**Lo lento es el transmisor del módulo al soltar el bus. El receptor es rápido.** Para
escuchar a 250k (bit de 4 µs) sirve; para transmitir no. El chip dice `TJA1050 NXP SX XJ
D408`; según la hoja de NXP no debería tardar 15 µs. Candidatos sin elegir: clon, chip
dañado, VCC en 4.7 V (la hoja pide 4.75–5.25 V).

**Trampa que costó una tarde:** una prueba de lazo con TX pegado en bajo da siempre RX = 1,
porque el TJA1050 suelta el bus solo a los **250–750 µs** (time-out de dominante). El lazo
se mide con **pulsos cortos** (`lazo_pulsos`), nunca con niveles fijos.

**Bug corregido:** a `prueba_can.ino` le faltaba `tx.self = 1` (Self Reception Request).

## Por qué conectar esto no daña el equipo

Todo con fuente: la hoja de datos de NXP del TJA1050 y lo medido.

**1 · No puede transmitir — tres capas independientes**
- **Hardware:** el TX del TJA1050 va al aire. Su pull-up interno (la hoja: −200 µA con TXD
  en 0 V) lo deja en alto = **recesivo**. Sin un nivel bajo en TXD el chip no maneja el bus
- **Software:** `TWAI_MODE_LISTEN_ONLY` no manda tramas, ni ACK, ni tramas de error. El
  sketch no llama a `twai_transmit()`
- **El propio chip:** aunque TXD quedara en bajo por un corto, la hoja garantiza que suelta
  el bus a los **250–750 µs** (TXD dominant time-out). No puede trabar el bus

**2 · La carga que agrega es despreciable**
- Resistencia diferencial de entrada: **25–75 kΩ** (hoja). En paralelo con los 120 Ω del bus:
  120 → 119.7 Ω
- Capacitancia de entrada: **7.5 pF** típico por línea
- La hoja: **«at least 110 nodes can be connected»** y **«an unpowered node does not disturb
  the bus lines»** — ni apagado molesta
- **No se agrega terminador**: el bus queda con lo que tiene

**3 · No toca nada de potencia**
- Solo van los pines 3 y 8, que son el par CAN **medido** (120 Ω entre ellos, mismo hilo que
  el multipiloto)
- **Pin 6 (+24 V del 4F15), 5 (GND conmutado) y 9 (+12 V): sin conectar.** No se toma
  corriente del equipo; el ESP32 se alimenta del USB de la laptop
- **Pin 2: sin conectar**, porque no está confirmado que sea masa

**4 · No hay lazo de tierra**
- Laptop a **batería** y sin GND hacia el equipo: no hay camino para que circule corriente
  entre la laptop y el montacargas. El receptor se polariza contra el bus por su propia
  impedancia de entrada

**5 · Ya pasó algo peor y el bus lo aguantó**
- El 30-sep el cable FTDI estuvo minutos metiendo **−6 V de RS-232 en el pin 3 (CAN_L)**, más
  DTR/RTS en el 4 y el 7, y tramas de saludo. **El display no mostró ningún código de bus** (los
  de CAN serían grupo de evento 8). Lo de ahora mete **nada**

**Lo que NO cubre esto — el riesgo real está en el cable, no en el diseño.** Antes de enchufar,
con el USB desconectado y en Ω:

```
DB9 macho pin 6 ↔ cualquier cable nuestro     → ABIERTO   (lo único que de verdad daña)
DB9 macho pin 3 ↔ pin 8                       → decenas de kΩ (el TJA), NUNCA ~100/120 Ω
DB9 macho pin 8 ↔ CANH del módulo             → ~0
DB9 macho pin 3 ↔ CANL del módulo             → ~0
TX del módulo   ↔ GPIO 21                     → ABIERTO
```
