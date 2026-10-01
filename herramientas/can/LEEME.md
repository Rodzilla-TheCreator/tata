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

## La medición que confirma antes de soldar

Un minuto, con óhmetro, **batería desconectada**:

```
pin 3 ↔ pin 8   ≈ 60 Ω   →  X200 confirmado: soldar 8 / 3 / 2
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
