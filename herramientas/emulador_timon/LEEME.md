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

```
 [POWER BANK USB 5V] (+)──┬──────────────── +5V ──┬── Vcc MCP6002 (op-amp RRIO)
                          │                        │   (op-amp a 5V = CLAMP: la salida
                      ESP32 (5V/VIN)               │    nunca pasa de 5V → protege node 4)
                          │
  ESP32
   GPIO34  ◄── pote 10k (0-3.3V) = VELOCIDAD de giro (centro = quieto)
               [en campo; en el kit lo reemplaza la Jetson/gamepad]
   GPIO25 (DAC verde, 0-3.3V) ──► U1a no-inversor, G=1.36 ──► NO ┐
   GPIO26 (DAC café , 0-3.3V) ──► U1b no-inversor, G=1.36 ──► NO ┤
   GPIO27 ──1k──►│ B 2N2222 ; C──bobina relé──+5V ; 1N4148 flyback sobre la bobina
                                 (energiza el relé SOLO en teleop; arranca en LOW)

  RELÉ DPDT (señal, contactos de oro):
     polo 1:  COM → pin VERDE de node 4 │ NC → verde del sensor REAL │ NO → salida op-amp verde
     polo 2:  COM → pin CAFÉ  de node 4 │ NC → café  del sensor REAL │ NO → salida op-amp café
     BOBINA DESENERGIZADA = NC = sensor REAL  (fail-safe)

  Ganancia de cada canal:  G = 1 + Rf/Rg = 1.36    (Rg = 10k ;  Rf = 3.6k, en trimpot de 5k)

  TIERRA COMÚN (un solo nodo):
     power bank(−) = ESP GND = MCP6002 GND = emisor del 2N2222 = retorno de la bobina = amarillo
     → el **amarillo del sensor** es la ÚNICA conexión de masa al equipo.

  El sensor REAL queda SIEMPRE alimentado por el equipo (blanco = +11V, amarillo = GND).
  El relé solo conmuta cuáles 2 señales le llegan a node 4: las del sensor o las nuestras.
```

**Por qué power bank y no el DROK a los 12 V del equipo:**
- El riel de 11 V del sensor es de node 4 (~15 mA): colgarle el circuito lo sobrecarga.
- La batería es ~39–48 V: pasa del máximo de entrada de casi todo DROK (~30 V) → lo quema.
- El emulador solo necesita **5 V** (riel del op-amp + ESP por USB). Un power bank los da, **flota**
  (sin tierra física → sin ground loop) y deja al equipo fuera del lazo de potencia. En el kit
  integrado la energía sale del DC-DC del kit (batería → bus de 5 V), que el Orin ya necesita.

## Componentes (BOM)

| Qué | Para | Nota |
|---|---|---|
| Power bank USB 5 V | alimentar todo | flota, sin ground loop |
| ESP32 | cómputo de θ + 2 DAC | del kit |
| **MCP6002** (dual RRIO, salida 0-5V) | las 2 etapas de salida | o MCP6004 (quad) si después se agregan los 2 canales de la palanca |
| Relé **DPDT de señal**, bobina 5 V, contactos de oro | handoff real/teleop | ej. OMRON G6K-2P-Y; NO de potencia (EMF térmica) |
| 2N2222 + 1N4148 + R 1k | driver de la bobina | base del transistor |
| 2× 10k (Rg), 2× trimpot 5k (Rf) | ganancia 1.36 | afinable |
| Pote 10k | entrada de velocidad (campo) | lo reemplaza la Jetson/gamepad |

## Función de transferencia y software

- `out = G·Vdac`, con **G = 1.36** → `Vdac = out / 1.36`.
- El software computa `verde = Vo + Va·cos θ`, `café = Vo + Va·sin θ` (0.49–4.45 V) y escribe
  `aDac(out) = (out/G)/3.3·255` en cada DAC. **El centro (Vo) y la amplitud (Va) los pone el
  software; la etapa analógica solo es ganancia + buffer.**
- **Afinar:** mové el trimpot Rf hasta que un `out` comandado de 4.45 V **lea 4.45** en el
  caracterizador. La precisión de amplitud sale de ahí (la ref del DAC nativo es el riel de
  3.3 V del ESP, ±1-2 %; con MCP4728 después, su ref interna es más estable).

## Seguridad

- **Relé desenergizado = sensor real (fail-safe):** corte de energía o ESP colgado → el relé cae
  solo y el operador recupera la dirección. Arranca en LOW; se energiza SOLO con el comando `e`.
- **Op-amp a 5 V = clamp inherente:** la salida nunca pasa de 5 V (protege la entrada de node 4);
  un valor fuera del círculo lo lee node 4 como falla y deshabilita la dirección.
- Equipo **en gato**, **paro físico en mano**, hombre-muerto **sin puentear** hasta la prueba de
  movimiento. Energizar el relé solo con todo lo anterior.

## Validación — ANTES de tocar node 4

Salida del op-amp → de vuelta al **caracterizador (A0/A1)**. Si ves el **mismo círculo**
(radio ≈ 1.95, nrad ≈ 1), el emulador reproduce al sensor. Afiná la ganancia ahí. **Recién
después**, por el relé, al conector del equipo.

## Archivos

| Archivo | Qué hace |
|---|---|
| `armado_emulador.svg` | Diagrama de conexionado (power bank, ESP32, op-amp, relé, conector, sensor real) |
| `caracterizador_timon.ino` | Arduino Uno/Nano: mide Vo/Va por canal, confirma cuadratura (radio normalizado ≈ 1), cuenta vueltas, log CSV. Es el que sacó Vo=2.47 / Va=1.98 |
| `emulador_timon.ino` | ESP32: genera seno/coseno por los 2 DAC, entrada de velocidad por pote, control del relé (`e`/`d`) |

## Estado / pendientes

- Afinar **G** con el trimpot leyendo de vuelta con el caracterizador.
- Confirmar el **signo**: qué sentido de θ = izquierda/derecha, contra node 4 (vigilar `0x284` y
  los eventos `1.54`/`1.55`/`1.56`).
- Resolución 8-bit del DAC nativo: OK para la prueba (~0.45°/paso). Para el kit, **MCP4728**
  (12-bit, I²C, ya está en el hardware de `docs/21`).
- El sensor **no tiene número de parte** en el cuerpo.
