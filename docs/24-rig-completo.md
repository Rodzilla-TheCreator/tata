# El rig completo — DB9 (CAN) + timón, para probar todo en un equipo que funcione

Las dos mitades ya están **validadas por separado** en banco (la cadena CAN pasa `prueba_can`
20/20, 14-oct; el emulador del timón reproduce el sensor, 27-oct). Esto las junta en **un rig**
que se arma y valida **en el banco ahora**, sin montacargas, y queda listo para enchufar al
primer equipo que encienda. Convive con `docs/20` (arneses enchufables), `docs/21` (gameplan),
`docs/23` (runbook del equipo de cliente) y `herramientas/emulador_timon/runbook_prueba_equipo.md`.

> **Qué prueba el rig completo:** la **marcha y las funciones** (por el bus, emulando el
> multipiloto) y la **dirección** (emulando el sensor del volante). Los dos canales de mando
> del teleop, en una sola salida al equipo.

---

## Las dos mitades

**Mitad A — DB9 / CAN · marcha y funciones**
- ESP32 + **TJA1050** (el nuevo, 20/20). TWAI: **TX = GPIO22, RX = GPIO21**.
- Al **DB9**: **CANH = pin 8, CANL = pin 3** (`herramientas/can/`). El bus tiene **120 Ω** (un
  solo terminador; no agregar otro).
- Escucha pasiva con `escucha_can.ino` (LISTEN_ONLY); inyección del **multipiloto (nodo 2)** con
  el **repuesto** abierto y cableado (`docs/20` §ruta B, `docs/21` §2), nunca el multipiloto
  original.

**Mitad B — Timón · dirección**
- ESP32 + **LM358 a +11 V** (del **blanco** del conector, libre al desconectar el sensor real).
- DAC: **GPIO25 = verde, GPIO26 = café** → etapa op-amp → conector del sensor sin/cos del **nodo 4**.
- **amarillo = GND** del emulador. Calibrado (`emulador_timon.ino`: `Vo=2.47`, `Va=1.98`;
  verde `k=1.381 o=0.131`, café `k=1.386 o=0.115`).

---

## El tema que las une: las tierras

Medido (03-oct): el **amarillo** (referencia del nodo 4) da **~0 V contra el negativo de
batería, pero sin continuidad** — es una tierra de señal **aislada**. Y:

- **Mitad A** necesita su GND dentro del **común-modo del bus** (negativo de batería).
- **Mitad B** necesita su GND **= amarillo**.

Son **dos referencias que el equipo mantiene separadas**. Por eso:

| Etapa | Cómo se resuelve |
|---|---|
| **Primera prueba en equipo** | **Dos rigs independientes, dos tierras, NO unidas.** Se prueba **un canal a la vez**: marcha con la Mitad A (el timón **no** conectado), dirección con la Mitad B (el TJA **no** conectado al bus). No necesitan compartir tierra si corren por separado |
| **Kit integrado** (después) | **Transceptor CAN aislado** (ADM3053 o CA-IS3050G): el lado lógico queda en la tierra del emulador (amarillo) y el lado CAN flota al común-modo del bus. Así **un solo cerebro** (ESP, o maquinón por USB-CAN) maneja las dos mitades con una tierra |

**Pendiente que decide el integrado (5 min en el equipo):** continuidad **amarillo ↔ negativo de
batería**. Si están unidos, basta una tierra; si no (lo esperado), va el transceptor aislado.

---

## BOM del rig

| Mitad | Pieza | Nota |
|---|---|---|
| A | ESP32-WROOM | TWAI 22/21 |
| A | TJA1050 (el nuevo) | 20/20; el viejo solo para escuchar |
| A | Multipiloto **de repuesto** | abierto y cableado, enchufable (`docs/20`) |
| A | Power bank USB 5 V | flota, sin ground loop |
| B | ESP32-WROOM | DAC 25/26 |
| B | LM358 (DIP) | a **+11 V** del blanco; no rail-to-rail |
| B | 2×10k, 2×5.1k, 2×100 Ω, 2× zener 5.1 V | ganancia + clamp (`emulador_timon/LEEME.md`) |
| B | Power bank USB 5 V | flota |
| Integrado | ADM3053 / CA-IS3050G | **transceptor CAN aislado** (etapa 2) |

---

## Aislar el DB9 — el camino discreto (opción 3)

Esquemático: [`herramientas/can/armado_aislado.svg`](../herramientas/can/armado_aislado.svg).
Aísla el **lado CAN** (digital, fácil), no el timón (analógico, difícil). El ESP se queda con
**GND = amarillo**; el lado del bus flota al **negativo de batería**. Tres piezas:

1. **Aislador digital de 2 canales** (1 forward + 1 reverse) — cruza TXD y RXD la barrera.
2. **Transceptor CAN** en el lado del bus — el TJA1050 que ya tenés.
3. **DC-DC aislado 5 V→5 V** — alimenta el lado del bus flotante. **Es lo que de verdad separa
   las tierras:** sin él, alimentar el TJA con el 5 V del ESP vuelve a unirlas.

### Cableado (pines)

| Señal | De | A |
|---|---|---|
| TXD | ESP GPIO22 → aislador `VIA` (3) | `VOA` (6) → TJA `TXD` (1) |
| RXD | TJA `RXD` (4) → aislador `VIB` (7) | `VOB` (4) → ESP GPIO21 |
| +5 V lado ESP | power bank → aislador `VDD1` (1) | y → DC-DC `Vin+` |
| GND = amarillo | ESP GND → aislador `GND1` (2) | y → DC-DC `Vin−` |
| +5 V aislado | DC-DC `Vout+` → aislador `VDD2` (8) | y → TJA `VCC` (3) |
| GND_bus | DC-DC `Vout−` → aislador `GND2` (5) | y → TJA `GND` (2), TJA `S` (8), y **negativo de batería** |
| CAN | TJA `CANH` (7) → DB9 **pin 8** | TJA `CANL` (6) → DB9 **pin 3** |

Decoupling: 0.1 µF en cada par VCC/GND (VDD1, VDD2, TJA); en el DC-DC, ~1–2.2 µF a la entrada y
10 µF + 0.1 µF a la salida. **No agregar 120 Ω** (el equipo ya tiene un terminador).

### Qué buscar en C&D

| Qué | Buscar | Alternativa |
|---|---|---|
| Aislador digital 2 canales | **`ADuM1201`** (o `ADUM1201ARZ`) | `ISO7721` · o "aislador digital 2 canales" (1 fwd + 1 rev) |
| DC-DC aislado 5V→5V 1W | **`B0505S`** (o `B0505S-1WR2`) | `IB0505S` · `A0505S` · "convertidor DC-DC aislado 5V 1W" |
| Transceptor CAN | ya tengo **TJA1050** | `SN65HVD230` (3.3 V → usar DC-DC `B0503S`) · `MCP2551` |
| Capacitores | 0.1 µF cerámico (×5), 10 µF (×2), 2.2 µF (×1) | — |

> **Atajo si no querés armar el discreto:** un **módulo CAN aislado** ya hecho — buscar
> **`CTM1051`** / `CTM8251` / "módulo CAN aislado" — trae transceptor + aislador + DC-DC aislado
> en un solo SIP. Es el ADM3053/opción 3 enlatado.

---

## Reversibilidad — nada irreversible

Todo **enchufable**, no se corta ni se empalma (regla dura en equipo de cliente, `docs/23`):
- **CAN:** al DB9; para inyectar, se cambia el multipiloto original por el **repuesto**.
- **Timón:** se desconecta el sensor sin/cos y se enchufan los **4 cables** (verde, café, amarillo,
  y tap de +11 V del blanco).
- **Paro físico en mano. Rueda en gato para la prueba de dirección. Hombre-muerto sin puentear
  hasta mover.**

---

## Orden de prueba en un equipo que funcione

Un canal a la vez; restituir entre cada uno. Los pasos detallados están en `docs/23` (Track A/B)
y en el runbook del emulador; acá el orden:

1. **Baseline** con el equipo original: el timón real mueve la rueda; el multipiloto real maneja.
2. **Escucha CAN** 0 errores (Mitad A, LISTEN_ONLY) antes de transmitir.
3. **Marcha** (Mitad A): conectar el repuesto, inyectar; el equipo debe **pedir el hombre-muerto**;
   mover suave y barrer el vocabulario de funciones (lift/sideshift/reach/tilt).
4. **Restituir** la Mitad A (multipiloto original de vuelta).
5. **Dirección** (Mitad B): desconectar el sensor, enchufar el emulador, **ver la rueda girar**
   con la GUI del timón.
6. **Restituir** la Mitad B (sensor original de vuelta).
7. **Checklist de salida**: conectores originales, sin códigos activos, equipo como llegó.

> **Ante cualquier falla:** la pieza original (multipiloto o sensor) vuelve de inmediato. En
> equipo de cliente, recordá que **los códigos no se borran todavía** (`docs/23`).

---

## Qué se puede armar YA (sin montacargas)

- **Armar y validar las dos mitades en el banco**, cada una con su control de falsación:
  Mitad A `prueba_can` 20/20 (quitar el puente → falla); Mitad B el caracterizador (círculo
  radio ≈ 1.95, nrad ≈ 1; quitar el puente → sin eco).
- **Dejar los arneses enchufables listos** (repuesto del multipiloto cableado; los 4 cables del
  timón con su conector).
- Con eso el rig queda **completo y probado**, esperando solo el equipo que encienda — que es el
  único faltante, no la ingeniería.
