# Emulador del sensor del volante (dirección)

Reemplaza el sensor seno/coseno del volante para **comandar la dirección** en teleop/autonomía.
La dirección **no es CAN** —el nodo 4 no tiene RPDO de giro y el sensor no cuelga del bus
(ver `docs/21` §4 y `componentes/LEEME.md`, 24-oct)— así que la única entrada es **emular el
sensor** en su conector. node 4 hace el resto: integra, clampea, recorta por velocidad y cierra
el lazo con la rueda. Somos un drop-in de la mano del operador.

## El sensor que emulamos (medido en banco, 24-oct)

- **Seno/coseno absoluto, single-turn.** `verde = Vo + Va·cos θ`, `café = Vo + Va·sin θ`.
- **Vo = 2.47 V, Va = 1.98 V.** Círculo (amplitudes iguales a 0.5 %). Radio ≈ 1.95, constante.
- **Independiente del supply:** variado 9–13 V, verde/café/ángulo no se movieron → node 4 chequea
  **amplitud absoluta** → el emulador necesita amplitud **estable** y **tierra común** con node 4.
- 4 cables: **blanco** +supply (~11 V del equipo), **amarillo** GND, **verde** y **café** las dos señales.
- **Invariante que chequea node 4: el RADIO** `√((verde−Vo)²+(café−Vo)²)`, NO la suma (la suma
  varía 2.3–7.6 V).
- node 4 deriva **velocidad** del cambio de θ → para girar, θ debe **barrer**; θ quieto = recto.

## El circuito

**Diagrama de conexionado: [`armado_emulador.svg`](armado_emulador.svg).** Abajo el mismo en texto.

Versión **LM358** (lo que hay en C&D). El LM358 **no es rail-to-rail**, así que el op-amp va a
**+11 V** (no a 5 V): a 5 V no llegaría a los 4.5 V que node 4 necesita.

```
 [POWER BANK USB 5V] ── ESP32 (5V + DAC a 0-3.3V)
 [+11 V del BLANCO]  ── Vcc del LM358 (pin 8)   ← el blanco queda libre: el sensor real se desconecta

  ESP32  (θ comandado por SOFTWARE / teleop por USB-serial; SIN pote)
   GPIO25 (DAC verde) ──► U1a (G_V=1.39) ──►[R 100Ω]──┬──► pin VERDE → node 4
   GPIO26 (DAC café ) ──► U1b (G_C=1.43) ──►[R 100Ω]──┤     cada salida: [zener 5.1V a GND]
                                                         └──► pin CAFÉ  → node 4

  Por canal:  IN+ = DAC ;  Rg de IN− a GND ;  Rf de IN− a OUT ;  G = 1+Rf/Rg (verde 5.1k/2k=1.39 · café 100k/43k=1.43)
  Clamp:      R 100Ω en serie + zener 5.1V de la salida a GND (protege node 4)

  LM358 (8 pines):  Vcc(8)=+11V blanco · V−(4)=GND · VERDE: IN1+ 3, IN1− 2, OUT1 1 · CAFÉ: IN2+ 5, IN2− 6, OUT2 7

  TIERRA COMÚN:  power bank(−) = ESP GND = LM358 V−(4) = amarillo del conector (= GND de node 4).
  SIN RELÉ: el sensor REAL se DESCONECTA; el emulador va DIRECTO al conector de node 4.

  Si conseguís un op-amp RAIL-TO-RAIL (LMV358 / TLV2372 / MCP602): corrélo a 5 V del power bank
  y quitá el +11 V y el zener (el propio riel de 5 V hace de clamp).
```

**Alimentación (dos fuentes, tierra común):**
- **ESP32: power bank USB 5 V.** Flota (sin tierra física → sin ground loop) y da el 3.3 V que es
  la referencia del DAC.
- **LM358: +11 V del BLANCO del conector.** El LM358 no es rail-to-rail; a 5 V no llega a 4.5 V,
  necesita más riel. El blanco (supply del sensor de node 4, ~11 V) **queda libre** porque el
  sensor real se desconecta, y el op-amp solo chupa ~2 mA (dentro de su presupuesto de ~15 mA).
- **NO** alimentar nada de la batería (~39-48 V) directo ni por el DROK (lo quema: pasa de su
  máximo de ~30 V).
- En el kit integrado todo sale del **DC-DC del kit** (batería → bus de 5 V), que el Orin ya necesita.
- Con un op-amp **rail-to-rail** (LMV358 / TLV2372 / MCP602) el op-amp corre a **5 V** del power
  bank y **no hace falta el +11 V ni el zener**.

## Componentes (BOM)

| Qué | Para | Nota |
|---|---|---|
| Power bank USB 5 V | alimentar el ESP (el op-amp va a +11 V) | flota, sin ground loop |
| ESP32 | cómputo de θ + 2 DAC | del kit. θ por software/teleop, **sin pote** |
| **1× LM358** (dual; DIP mejor para protoboard) | las 2 etapas de salida | C&D lo tiene. NO rail-to-rail → va a +11V. Si hay **LMV358 / TLV2372 / MCP602** (rail-to-rail), mejor: corre a 5V y se quita el zener |
| **6 resistencias** (por canal): verde Rg 5.1k + Rf 2k, café Rg 100k + Rf 43k, 2× 100Ω (serie) | ganancia por canal + serie del clamp | lo que importa es **G = 1+Rf/Rg ≥ 1.35**; con otros valores se calibra G **por canal** en el sketch (ej. verde 5.1k/2k=1.39, café 100k/43k=1.43). La R serie no es crítica: cualquier **100-330 Ω** |
| **2× zener 5.1V** (1W) | clamp de salida (protege node 4) | del kit de zener 28 valores de C&D |

## Función de transferencia y software

- `out = G·Vdac`, con **G por canal** (`G_V`, `G_C`) → `Vdac = out / G`.
- El software computa `verde = Vo + Va·cos θ`, `café = Vo + Va·sin θ` (0.49–4.45 V) y escribe
  `aDac(out, G)` con la G de cada canal. **El centro (Vo) y la amplitud (Va) los pone el software**,
  así que **resistencias dispares entre canales dan igual amplitud** (círculo, no elipse): la etapa
  analógica solo es ganancia + buffer, y el software compensa la ganancia de cada una.
- **Afinar:** el sketch tiene **G por canal** (`G_V`, `G_C`). Medí la **G real** de cada canal
  leyendo la salida con el caracterizador y ajustá `G_V`/`G_C` hasta que el círculo dé radio ≈ 1.95 /
  nrad ≈ 1. (Con resistencias iguales en ambos canales, `G_V = G_C`. Si usás trimpot, lo ajustás por
  hardware.) La ref del DAC nativo es el riel de 3.3 V del ESP (±1-2 %).

## Seguridad

- **Sin relé de handoff** (quitado a pedido): el emulador va **cableado directo** a node 4 y el
  sensor real queda **desconectado**. En el EDR **parado de desarrollo** está bien (no hay
  operador). Si el ESP se cuelga, node 4 lee una señal inválida → **falla y deshabilita la
  dirección** (seguro en parado). Para un equipo **en operación** habría que volver a poner un
  selector/handoff.
- **Clamp: R 150 Ω en serie + zener 5.1 V** de cada salida a GND. Si el op-amp (a 11 V) se
  dispara, la salida queda clampeada a ~5.1 V y protege la entrada de node 4; un valor fuera del
  círculo lo lee node 4 como falla y deshabilita la dirección. (Con op-amp rail-to-rail a 5 V, el
  propio riel ya es el clamp y el zener sobra.)
- Equipo **en gato / parado**, **paro físico en mano**, hombre-muerto **sin puentear** hasta la
  prueba de movimiento.

## Validación — ANTES de tocar node 4

Salida del op-amp → de vuelta al **caracterizador (A0/A1)**. Si ves el **mismo círculo**
(radio ≈ 1.95, nrad ≈ 1), el emulador reproduce al sensor. Afiná la ganancia ahí. **Recién
después**, por el relé, al conector del equipo.

## Archivos

| Archivo | Qué hace |
|---|---|
| `armado_emulador.svg` | Diagrama de conexionado (power bank, ESP32, op-amp, relé, conector, sensor real) |
| `caracterizador_timon.ino` | Arduino Uno/Nano: mide Vo/Va por canal, confirma cuadratura (radio normalizado ≈ 1), cuenta vueltas, log CSV. Es el que sacó Vo=2.47 / Va=1.98 |
| `emulador_timon.ino` | ESP32: genera seno/coseno por los 2 DAC. Velocidad de giro por **serial** (deg/s), sin pote. Salida directa a node 4 (sin relé) |

## Estado / pendientes

- Afinar **G** con el trimpot leyendo de vuelta con el caracterizador.
- Confirmar el **signo**: qué sentido de θ = izquierda/derecha, contra node 4 (vigilar `0x284` y
  los eventos `1.54`/`1.55`/`1.56`).
- Resolución 8-bit del DAC nativo: OK para la prueba (~0.45°/paso). Para el kit, **MCP4728**
  (12-bit, I²C, ya está en el hardware de `docs/21`).
- El sensor **no tiene número de parte** en el cuerpo.
