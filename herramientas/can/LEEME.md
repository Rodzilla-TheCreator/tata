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
