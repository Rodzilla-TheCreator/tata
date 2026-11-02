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

## El rig integrado — un solo ESP (decidido 02-nov-2026)

Esquema del sistema: [`herramientas/rig_completo.svg`](../herramientas/rig_completo.svg).

**Decisión:** un **solo ESP32** es el cerebro del rig, con **GND = amarillo**, haciendo las tres
cosas — **CAN** (por el transceptor **aislado**), **timón** (DAC → LM358) y **watchdog**
(GPIO → relé). El aislamiento del CAN es lo que habilita esa única tierra: el lado del bus flota
al negativo de batería y nunca toca el amarillo.

**Por qué NO un USB-CAN a la laptop.** Se consideró reemplazar el ESP por un adaptador USB-CAN
aislado enchufado a la laptop. **Se descartó:** el **watchdog de 200 ms tiene que vivir en un
micro** (regla dura, `docs/10`), nunca en Linux, que no garantiza tiempo; y el timón sigue
necesitando el ESP. El USB-CAN queda como instrumento de **banco/diagnóstico** en superspeed
(leer y loguear el bus con `python-can`), no como el rig de operación.

**El watchdog** (nuevo en el rig): GPIO → transistor → **relé DPDT que hace de pie** sobre los
dos contactos del pedal (NC y NA, `docs/20` §1). Mientras llega el latido, el relé «pisa»; si
pasan 200 ms sin latido, suelta, el equipo ve «pedal suelto» y frena. **A prueba de fallas**
(sin corriente = suelto). Rearme manual. Es **supervisión de disponibilidad**, no la capa de
seguridad certificada (`docs/10`). Pin por pin, en la sección de abajo.

---

## El circuito del ESP, pin por pin (02-nov-2026)

### Corregido al cerrar el circuito

| Decía | Es | Qué lo tumbó |
|---|---|---|
| `armado_aislado.svg`: `VDD1` del ADuM1201 a **+5 V** | **`VDD1` a 3.3 V del ESP** | con `VDD1` a 5 V, `VOB` saca 5 V directo a GPIO21 y **el ESP32 no tolera 5 V**. El ADuM corre cada lado a su propio voltaje (2.7–5.5 V), así que traduce 3.3 ↔ 5 sin más piezas: **el divisor 1k/2k del armado viejo sobra** |
| `rig_completo.svg`: relé con **contacto NA en serie** con el hombre-presente | **relé DPDT que reemplaza los dos contactos** (NC y NA) del pedal | `docs/20` §1: el pedal es un interruptor doble NC+NA, y `0/0` o `1/1` por más de 2000 ms da el evento **`1.06`, que solo se borra reiniciando**. Un NA en serie deja el NC del pedal real cerrado = «suelto» siempre. Ya estaba escrito; el esquema del rig lo ignoró |

### Mapa de pines del ESP32

| GPIO | Va a | Nota |
|---|---|---|
| **22** | ADuM1201 `VIA` (3) → TJA `TXD` | TWAI TX |
| **21** | ADuM1201 `VOB` (4) ← TJA `RXD` | TWAI RX, **3.3 V** gracias a `VDD1` = 3.3 V |
| **25** | LM358 `IN1+` (3) → verde | DAC 1 |
| **26** | LM358 `IN2+` (5) → café | DAC 2 |
| **27** | 1 kΩ → base del 2N2222 | relé del pie. No es pin de arranque: **queda en bajo al bootear** → relé suelto |
| **32** | botón de rearme a GND | pull-up interno. Pulsado = rearmar |
| **2** | LED de la placa | estado: fijo = pisando · parpadeo = disparado, esperando rearme |
| **3V3** | ADuM `VDD1` (1) | unos mA |
| **5V/VIN** | power bank | también alimenta `Vin+` del B0505S y la bobina del relé |
| **GND** | **amarillo** | la única tierra del lado ESP |

Libres para después: 33, 34–39 (solo entrada; el sensor de altura de El Aula), 18/19/23 (I²C o
SPI si entra el MCP4728). **No usar** 0, 12, 15 (arranque) ni 6–11 (flash).

### El pie (watchdog) — circuito

```
+5V ── PARO de hongo (NC) ──┬── bobina del relé DPDT ──┐
                            └──── 1N4148 (cátodo a +) ─┘
                                                       │
GPIO27 ──[1 kΩ]── base 2N2222 · colector ──────────────┘ · emisor ── GND (amarillo)

polo 1:  COM1 ── NC1   ↔ en lugar de la línea NC del pedal
polo 2:  COM2 ── NA1   ↔ en lugar de la línea NA del pedal

sin bobina:  NC cerrado · NA abierto   = «pedal suelto»   (ESP muerto, paro, sin latido, booteando)
con bobina:  NC abierto · NA cerrado   = «pedal pisado»
```

- **El paro de hongo corta la bobina, no la señal.** Es un camino de hardware que no depende del
  ESP: apretado, el relé cae aunque el firmware esté colgado con el GPIO en alto.
- Un DPDT mueve los dos polos juntos: la transición `NC→NA` dura milisegundos, lejos de los
  2000 ms del `1.06`.
- **Rearme manual en el firmware:** al dispararse, el relé queda suelto aunque vuelva el latido,
  hasta que alguien aprieta GPIO32 **y** hay latido fresco. Nunca se re-pisa solo.
- El relé va en el **arnés en Y con selector manual/teleop** (`docs/21` §3.4): en manual, el pedal
  real pasa directo y el equipo queda de fábrica. No se corta nada.

### Lo que falta medir para cerrar el relé — 5 min en el equipo

| Qué | Por qué |
|---|---|
| **Voltaje entre los contactos del pedal**, llave ON, pedal suelto y pisado | define el voltaje nominal de los contactos. Si conmuta los ~40 V de batería, el relé tiene que aguantar **≥ 60 V DC**; si es una entrada lógica del controlador, cualquier relé de señal sirve |
| **Corriente** por el contacto (amperímetro en serie, o V/R) | casi seguro mA (entrada de controlador), pero se mide |
| Par NC y par NA con el óhmetro, batería fuera | `docs/21` §3.2: ya estaba en la lista |

Hasta medirlo, el relé que se compra es un **DPDT de bobina 5 V con contactos de señal** (tipo
HK19F-DC5V, G2RL-2-5V o similar) **y se confirma el voltaje de contacto antes de enchufarlo**.

### Detalle a saber del timón

Al **resetear** el ESP, los DAC caen a 0 V → la salida queda en ≈ `o` (0.13 V), **fuera del
círculo** → node 4 lo lee como falla y deshabilita la dirección. Es seguro (no gira), pero **la
falla del nodo 4 no se borra todavía** (`docs/23`). En banco no importa; en el equipo, no
resetear el ESP con el emulador conectado.

**El MCP2515 no entra:** es un controlador CAN por SPI (el ESP32 ya trae el suyo, el TWAI) y
**no es aislado**. Tampoco el TJA1050/MCP2551 pelados. La única vía aislada es el camino discreto
de abajo, o el módulo CTM1051 enlatado.

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
| Integrado | ADuM1201 + B0505S (o CTM1051) | **CAN aislado** discreto, con el TJA1050 que ya hay |
| Pie | relé **DPDT** bobina 5 V, 2N2222, 1 kΩ, 1N4148 | voltaje de contacto **se confirma midiendo** el pedal |
| Pie | paro de hongo NC, botón NA (rearme) | el paro corta la bobina |
| Pie | par de conectores del pedal + selector manual/teleop | arnés en Y, nada cortado (`docs/21` §3.3–3.4) |

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
