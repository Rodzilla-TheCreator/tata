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
| **22** | ADuM1201 `VIB` (3) → `VOB` (6) → TJA `TXD` | TWAI TX |
| **21** | ADuM1201 `VOA` (2) ← `VIA` (7) ← TJA `RXD` | TWAI RX, **3.3 V** gracias a `VDD1` = 3.3 V |
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

### El pedal es infrarrojo — dato en tensión (02-nov)

Los mecánicos dicen que el pedal que se quitó está «roto del infrarrojo, no detecta», y que lo
van a dejar en el equipo de maje en Las Palmas. **Si es infrarrojo, no es un interruptor
mecánico**: es un sensor óptico con salidas **electrónicas** (transistor). `docs/20` dedujo
«NC + NA» del evento `1.06` (*interruptor de seguridad*), que dice cómo lo **lee** el
controlador, no cómo está **hecho** el pedal. Las dos cosas pueden ser ciertas a la vez: un
sensor óptico con dos salidas complementarias se ve igual que un NC + NA.

| Si las salidas resultan… | El pie es… |
|---|---|
| contacto seco, o transistor que conecta a + o a − sin importar la corriente | el **DPDT** de arriba sirve tal cual |
| transistor que el controlador lee con cierta corriente o voltaje | dos **transistores u optoacopladores** (6N137/TLP281 ya ubicados en C&D) en vez del relé. El watchdog no cambia: el GPIO27 sigue mandando y el paro sigue cortando la alimentación de la salida |

**Que esté roto no importa: no lo vamos a usar, lo vamos a emular.** Lo que da es el
**conector macho y hembra** para el arnés en Y (`docs/21` §3.3), la **foto** y el **número de
parte** (el manual dice `51297587`).

**El relé no se compra hasta medir el pedal.** De todas formas se consigue en C&D.

Martes, con el pedal enfrente, **nada se alimenta en banco sin saber el voltaje**:

```
□ foto de frente del conector y de la etiqueta; número de parte
□ batería fuera, óhmetro entre todos los pines, pisado y suelto
     si NADA cambia al pisar → es electrónico (no hay contacto que medir apagado)
□ ¿cuántos hilos? 3 = alimentación + GND + 1 salida · 4 = dos salidas (NC/NA electrónico)
□ en el equipo, llave ON, pedal conectado: voltaje de cada pin contra negativo de batería,
     pisado y suelto (con retro-sondeo, sin desconectar)
□ si está roto «del infrarrojo»: igual se mide la alimentación que le llega; eso es lo que hay
     que darle al emulador
```

### El sensor en mano — 13-nov

maje ya tiene el sensor que se quitó del pedal. **Ojo: maje lo trabaja desde maquinon, con fotos
del celular.** Lo que se sabe, y qué es dato y qué es suposición:

| Qué | Dato | De dónde |
|---|---|---|
| Etiqueta | `JUNGHEINRICH 51297587-D 800053 02/26 2412714` | la pieza |
| Número de parte | **`51297587`**: pieza 12 del «pedal doble», «Montaje; **sensores**» (plural), 10 −2 Nm | manual de servicio, *Especificaciones técnicas* pág. 10 (06.14); `herramientas/componentes/pedal_doble-015.png` |
| `-D` · `02/26` · `2412714` | probablemente revisión · fecha de fabricación (feb-2026) · serie | **suposición**, no verificado |
| Conector | **`XS160`**, enchufa en el **conector suelto del EDR** | la pieza y maje |
| Forma | **dos sensores en un arnés**: un **bloque rectangular** (cable negro, dos agujeros de montaje) y un **cilindro** tipo sensor de proximidad (cable gris), los dos a una ficha negra de dos filas | foto de internet buscando `51297587-D` (no se versiona: es de un vendedor) |
| Estado | «roto, le falta algo» (mecánicos); antes: «roto del infrarrojo, no detecta» | testimonio, sin medir |

**Lo que eso cierra o mueve:**

- **Dos sensores = los dos canales del `1.06`.** El evento pide combinaciones `0/1` o `1/0`; con
  `0/0` o `1/1` durante 2 s marca `E0106.02`, que **solo se borra reiniciando**. Lo más probable
  es un canal por sensor; **no está medido** (puede ser que un sensor dé los dos).
- **El `XS160` va directo al conector suelto:** para la primera prueba no hace falta arnés en Y
  ni selector. El Y sigue haciendo falta para el rig (manual ↔ teleop).
- **«Le falta algo» — hipótesis, sin verificar:** estos sensores no se pisan, detectan la
  **placa del pedal** que el pie mueve frente a ellos. Lo que falta puede ser esa placa (o el
  pedal entero). Para probar no hace falta: al cilindro un **fierro** (si es inductivo), al
  bloque una **tarjeta o la mano** (si es óptico).
- **El `XS160` no está en el manual** que tenemos: los esquemas no vienen. El pinout sale de
  medir (o del `99515375`, que sigue pedido).

**Seguridad:** este sensor es lo único que faltaba para que el equipo se mueva con nuestro nodo 2
(22-oct: el Master toma el `0x182` y solo pide el pedal). **Conectarlo con la rueda en el aire,
el paro a mano y `campo_nodo2.py` cerrado.** Pisarlo con mando es el paso 5, no esta medición.

**Orden de medición** (las fotos van al celular y de ahí a maquinon):

```
1. BANCO, sin alimentar
   □ foto de frente del XS160 (cara de los pines) y de la etiqueta
   □ cuántos pines; qué hilos y colores van al bloque y cuáles al cilindro
     (un sensor de 3 hilos suele ser café = +, azul = −, negro = salida; se confirma midiendo)
   □ óhmetro entre todos los pines, con y sin fierro / tarjeta enfrente
       si nada cambia → es electrónico, no hay contacto que medir apagado
2. EQUIPO, llave ON, sensor DESCONECTADO (retro-sondeo en el conector suelto del EDR)
   □ voltaje de cada pin contra NEGATIVO DE BATERÍA (no chasis)
     → cuál alimenta y a cuánto, cuáles son entradas y a qué voltaje quedan sueltas
3. ¿PRENDE EL INFRARROJO?
   □ sensor conectado y alimentado: mirar el bloque con la cámara del celular
     (la trasera; algunas frontales filtran el IR). Si no se ve la luz, ahí está lo «roto»
   □ el cilindro suele tener un LED que prende al detectar: anotar si prende con el fierro
4. EQUIPO, rueda en el aire, sensor CONECTADO, sin mando
   □ retro-sondeo: voltaje de cada salida sin objetivo y con objetivo
   □ en la pantalla: ¿se va el E0106 cuando las dos salidas quedan opuestas?
       sigue 0/0 o 1/1 → el canal que no cambia es el roto
       se va → el sensor sirve y lo que faltaba era la placa
```

**13-nov, más tarde: lo que falta en el cilindro (maje, con foto).** El chino dice que al cilindro le
falta algo. Las fotos del `51297587` en internet no traen tuercas. La punta hoy es un cilindro de **dos
escalones, el segundo con la punta redondeada, no plana**.

- **Las tuercas no faltan:** un sensor cilíndrico roscado (parece M12) siempre trae dos, una a cada lado
  de la placa donde se monta, y sirven para ajustar a qué distancia queda del objetivo. Los vendedores
  suelen fotografiarlo sin ellas.
- **Hipótesis, sin verificar:** es un sensor **inductivo «no enrasado» al que se le salió la tapa de la
  cara**. Esa tapa es plana, de plástico, sobresale de la rosca y cubre la bobina; sin ella queda la bobina
  en su resina, escalonada y redonda. Sin la tapa puede seguir detectando, o la bobina puede estar dañada.

**Prueba de banco del cilindro** (multímetro, 9–12 V, 100 Ω, 10 kΩ, un destornillador de acero, un imán):

```
1. cuántos hilos van al cilindro y de qué color (café +, azul −, negro salida, lo típico)
2. 2 hilos → pasivo: óhmetro (decenas de Ω a kΩ = bobina); imán → abierto/cerrado = reed;
   bobina: mV AC moviendo el imán rápido delante
3. 3 hilos → activo:
   a. SIN alimentar: modo diodo entre pares → + y − (0.5–0.7 V en un solo sentido)
   b. alimentar: + por 100 Ω en serie (protege si la polaridad estaba mal), − directo
   c. salida con 10 kΩ a + (NPN) o a − (PNP)
   d. salida sin nada enfrente y con el destornillador a < 4 mm; ¿prende un LED?
4. el bloque, igual; si es IR, la cámara trasera del celular ve la luz
```

**Control:** alimentado y sin objetivo, la salida no cambia sola; si cambia, mide ruido. **Nada al ESP ni
a la batería del equipo** hasta tener el pinout.

**El `XS160` por colores (maje, 13-nov):** 10 pines, todos con hilo.

| Pin | Color | Va a | Lo más probable (código estándar de sensores de 4 hilos; **sin medir**) |
|---|---|---|---|
| 1 | café | cilindro | + alimentación |
| 2 | blanco | cilindro | salida 2 (complementaria) |
| 3 | azul | cilindro | − (0 V) |
| 4 | negro | cilindro | salida 1 |
| 5 | café | caja | ? |
| 6 | amarillo | caja | ? |
| 7 | negro | caja | ? |
| 8 | verde | caja | ? |
| 9 | naranja | caja | ? |
| 10 | rojo | caja | ? |

**Lo que sugiere:** un cilindro de 4 hilos con **salidas complementarias** (NO + NC) da justo lo que pide
el `1.06`: dos canales siempre opuestos, 0/1 o 1/0. **Probablemente los dos canales del pedal salen del
cilindro solo**, y la caja es otra cosa. Se confirma en el banco: café a +12 V por 100 Ω, azul a −, 10 kΩ de
cada salida al azul (PNP; si las dos dan 0 V siempre, al café: NPN). Sin objetivo una salida alta y la otra
baja; con el destornillador a < 4 mm, **se invierten**. Las dos iguales = una salida muerta = el `E0106`.

**13-nov, medido (maje): pin 1 (café) ↔ pin 3 (azul), sin continuidad.** Sin alimentar, con el
multímetro. **Dato, no conclusión:**

- en un sensor activo es común que el modo diodo dé abierto en los dos sentidos: un diodo de protección
  en serie con el + bloquea un sentido, y en el otro los ~2 V del multímetro no alcanzan para que
  conduzca la electrónica;
- también puede ser un hilo cortado adentro del cilindro, o que 1 y 3 no sean + y −.

**Siguiente, en este orden:** (1) modo diodo, **en los dos sentidos**, entre todos los pares del cilindro
(1-2, 1-3, 1-4, 2-3, 2-4, 3-4) y anotar cuál da 0.4–0.8 V. Las salidas suelen mostrar una juntura
contra el − o el +, y eso ubica los rieles. (2) Recién ahí, la prueba alimentada de arriba (café a +12 V
por 100 Ω, azul a −): es la que decide. Si con 12 V la corriente es **0 mA** (se mide como caída en los
100 Ω) y ningún par mostró juntura, el cilindro está abierto por dentro.

**13-nov, medido (maje), cilindro sin alimentar:**

| Par | Ohmios (escala 200k) | Modo diodo |
|---|---|---|
| café (1) – blanco (2) | **47 k** | rojo en café, negro en blanco/negro: **la lectura varía**, no pita · al revés: **nada** |
| café (1) – negro (4) | **47 k** | (idem) |
| blanco (2) – negro (4) | **94 k** = 47 + 47 | — |
| café (1) – azul (3) | sin continuidad (medida anterior) | — |

**Lo que dicen los números (dato):** cada salida llega al café por **47 k**, y entre las dos salidas
solo hay camino **a través del café** (94 = 47 + 47). Las dos ramas son iguales: ninguna está en corto
ni abierta contra el café. Y el modo diodo es **asimétrico**, así que no es solo una resistencia:
hay algo con polaridad (una juntura, o un capacitor que carga y hace variar la lectura).

**Sospechosos, sin elegir:**

1. **Salidas NPN con resistencia de pull-up interna de 47 k al +** (café = +, como se suponía). Es un
   armado común. Si es esto, las salidas están sanas y el problema, si lo hay, está en el lado del azul.
2. **Azul abierto adentro** (hilo o tierra de la electrónica cortados). Casi todo sensor activo muestra
   *algo* entre + y −. Si el azul no conecta con nada, el sensor no tiene tierra: no funciona, y las dos
   salidas quedan altas por los 47 k = **1/1 = el `E0106`**. Cuadraría con «roto».
3. 47 k medido a través de junturas y no de resistencias: se descarta o confirma con la polaridad
   invertida (abajo).

**Siguiente, sin alimentar (5 min):**

```
□ ohmios con la polaridad INVERTIDA: negro del multímetro en café, rojo en blanco y en negro
    da 47 k otra vez → son resistencias de verdad (sospechoso 1)
    da otra cosa u OL → hay junturas en serie (sospechoso 3)
□ azul contra café, blanco y negro, en LOS DOS sentidos, escalas 200k y 2M
    (dejar las puntas unos segundos: si hay un capacitor, la lectura sube y se va a OL)
    azul abierto contra todo, en las dos escalas → sospechoso 2
```

**Después, la prueba alimentada** (café a +12 V por 100 Ω, azul a −). **Si son pull-ups internos, no
hace falta poner 10 k:** se mide cada salida contra el azul con el multímetro solo.

| Resultado | Lectura |
|---|---|
| una salida ≈ 12 V y la otra ≈ 0, y se **invierten** con el destornillador | el cilindro sirve |
| las dos ≈ 12 V siempre, y **0 mA** en los 100 Ω | **no tiene tierra (azul abierto)**: es el roto |
| las dos ≈ 12 V, con corriente | la electrónica prende pero no conmuta (la cara dañada) |
| una fija, la otra conmuta | un canal muerto |

**Predicción que se puede tumbar:** si el azul resulta abierto, alimentado van a dar las dos salidas
altas sin importar el objetivo. Si en cambio conmutan, el sospechoso 2 queda descartado.

**Qué decide para el pie del rig** (la tabla de arriba): salidas que conmutan a + o a − sin
importar la corriente → el **DPDT** tal cual; salidas que el controlador lee con cierta corriente
o voltaje → **optoacopladores / transistores**. Con los voltajes del paso 2 se elige el relé
(si las entradas ven los ~40 V de batería, contactos de **≥ 60 V DC**).

**Control de falsación del paso 4:** con el sensor desconectado el equipo tiene que dar
`E0106` (es lo que da hoy). Si al conectarlo y poner el objetivo **no cambia nada**, o el sensor
está muerto o la medición no está leyendo lo que creemos: se mira el paso 3 antes de culpar al
sensor.

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
| TXD | ESP GPIO22 → aislador `VIB` (3) | `VOB` (6) → TJA `TXD` (1) |
| RXD | TJA `RXD` (4) → aislador `VIA` (7) | `VOA` (2) → ESP GPIO21 |

> **Corregido 02-nov:** la tabla tenía los canales del ADuM1201 al revés (TX por `VIA→VOA`). En el ADuM1201 el canal **B** va del lado 1 al 2 y el **A** del 2 al 1 (pines 2 `VOA`, 3 `VIB`, 6 `VOB`, 7 `VIA`). Cableado así, dos salidas quedaban enfrentadas.
| +5 V lado ESP | power bank → aislador `VDD1` (1) | y → DC-DC `Vin+` |
| GND = amarillo | ESP GND → aislador `GND1` (4) | y → DC-DC `Vin−` |
| +5 V aislado | DC-DC `Vout+` → aislador `VDD2` (8) | y → TJA `VCC` (3) |
| GND_bus | DC-DC `Vout−` → aislador `GND2` (5) | y → TJA `GND` (2), TJA `S` (8), y **negativo de batería** |
| CAN | TJA `CANH` (7) → DB9 **pin 8** | TJA `CANL` (6) → DB9 **pin 3** |

Decoupling: 0.1 µF en cada par VCC/GND (VDD1, VDD2, TJA); en el DC-DC, ~1–2.2 µF a la entrada y
10 µF + 0.1 µF a la salida. **No agregar 120 Ω** (el equipo ya tiene un terminador).

### Pedido a Miami — antes del 11-nov-2026

**Criterio (maje, 02-nov): se pide el módulo ENTERO, no piezas para armar.** Armar es solo si
es la única opción. Tiene que llegar a Miami antes del 11-nov: **pedir a más tardar el
miércoles 5**, con entrega garantizada.

Lo que hace falta es una sola pieza que traiga las tres cosas: **aislamiento de señal + DC-DC
aislado + transceptor**, con lógica **3.3 V** (el ESP no tolera 5 V en GPIO21) y entrada TX/RX
para el TWAI que ya está validado. El TJA1050 queda para escuchar y para el banco.

| Opción | Qué trae | Lo malo | Veredicto |
|---|---|---|---|
| ~~**MikroE CAN Isolator Click**~~ (`MIKROE-2627`) | placa completa con DB9 macho | su DB9 es CiA-303 y no calza con el del equipo: haría falta adaptador igual. Stock escaso | **descartado (maje, 02-nov):** si igual hay que poner el DB9, basta el transceptor solo |
| **`TD301DCANH3`** (Mornsun/VISOM) | módulo encapsulado con las tres cosas adentro, **3.3 V**. No se arma: son 4 cables del lado del ESP y 3 del lado del bus | es un bloque con patas, sin bornera ni conector: **el DB9 macho se lo ponemos nosotros** (bornera, repineado a 8/3). Vendedores sin marca en Amazon (uno sin stock); LCSC lo tiene pero tarda | **EL PEDIDO: ×2** (uno de repuesto) |
| **Waveshare 2-CH CAN HAT aislado** | aislado de verdad, DC-DC integrado, **jumper de 120 Ω**, jumper 3.3/5 V, borneras, probablemente en Amazon Prime | es para Raspberry Pi y usa **MCP2515 por SPI**: hay que reescribir el firmware del TWAI (validado 20/20 y en el equipo el 22-oct) a SPI | **respaldo**, solo si fallan las dos |
| Camino discreto (ADuM1201 + B0505S + TJA1050) | — | hay que armarlo | **solo si no llega nada** (piezas en C&D: 6N137 ubicado) |

> **COMPRADO 02-nov (Amazon, a Wellington, llega sáb 7-nov; viaja a Honduras el 11):**
>
> | Qué | Cant. | Precio | Para qué |
> |---|---|---|---|
> | HiLetgo ADuM1201 (módulo CJMCU) | 2 | $8.49 | aislador del camino armado |
> | Bridgold B0505S-1WR3 (K-CUT) | 2 | $7.99 | DC-DC aislado del camino armado |
> | DSD TECH SH-C30G (CANable 1.0 Pro aislado) | 1 | $19.99 | USB-CAN aislado para la laptop (capturar el bus sin perder tramas). Respaldo del rig: el truco del STM32 en reset y el ESP a TX/RX del transceptor |
>
> **El rig va por el camino armado:** ADuM1201 + B0505S + el TJA1050 que ya hay, cableado según
> `armado_aislado.svg` (canales corregidos el 02-nov). **El `TD301DCANH3` NO se compró:** el envío
> de LCSC a tiempo costaba $40 por un módulo de $8. Lo de abajo queda como el camino que se evaluó.
>
> Al llegar: salida del B0505S **4.75–5.25 V** con el TJA de carga (no es regulado; el ADuM
> aguanta 5.5); óhmetro GND1↔GND2 **abierto**; `prueba_can.ino` con su control; en el equipo,
> CANH↔CANL ≈ 60 Ω.

> **LLEGÓ 11-nov.** Las tres piezas, como se pidieron. La serigrafía del ADuM1201 (CJMCU) confirma los
> canales corregidos: lado 1 `VDD1 · VOA · VIB · GND1`, lado 2 `VDD2 · VIA · VOB · GND2`. El SH-C30G dice
> «Base on Canable 1.0» (v1.5-20241005), con interruptores **R120** y **BOOT**, bornera `GND · CAN-H · CAN-L`
> y cabezal SWD (`GND 3V3 NRST CLK DIO`).
>
> **En tensión: ¿el SH-C30G es aislado?** Acá quedó anotado como «CANable 1.0 Pro aislado», pero en la
> foto no se ve un transceptor aislado (SOIC-16 ancho) ni un DC-DC aislado. **Se cierra con el óhmetro,
> antes de enchufarlo al equipo:** carcasa del USB ↔ borne `GND`. Abierto = aislado. ~0 Ω = **no aislado**:
> en el equipo solo con la laptop a batería y sin nada más a tierra, o no se usa ahí.
>
> **El banco de hoy:** (1) aislamiento del DSD; (2) cómo aparece en Windows (COM = slcan; sin COM =
> candleLight); (3) B0505S con el TJA de carga, 4.75–5.25 V y pin 1 ↔ 3 abierto; (4) ADuM1201 cableado,
> `GND1` ↔ `GND2` abierto; (5) rig contra el DSD con `prueba_can.ino`, bus ≈ 60 Ω, y el control: sin
> `VDD2` no pasa nada.

> **Decidido 02-nov (maje): `TD301DCANH3` por LCSC, ×3, envío exprés a Wellington.**
> Descartados por precio: la placa `EVAL-ADM3053EBZ` de Mouser (~$100, hace lo mismo que el
> módulo de ~$4) y el `PCAN-USB` aislado (~$300; queda para capturar el bus completo cuando haya
> un equipo que se mueva). Mouser no tiene el `TD301`. En Wellington no hay tienda de componentes.
>
> **Lo demás del mismo pedido a LCSC** (el envío exprés ya está pagado):
>
> | Prioridad | Qué | Cant. | Por qué |
> |---|---|---|---|
> | **sí** | **PhotoMOS 1 Form A + 1 Form B, DIP8** (Panasonic serie GU; candidatos `AQW610`/`AQW614`, confirmar 1a1b en la hoja de datos) | 3 | **el pie que sirve sin importar cómo salga el pedal.** Sin corriente: A abierto, B cerrado = «suelto» (a prueba de fallas por física). Sin bobina, sin rebote; el GPIO27 enciende los dos LED con una resistencia, sin transistor. Sirve si el pedal es contacto seco y casi siempre si es salida de transistor. El paro de hongo va en serie con los LED |
> | recomendado | **`URB4805YMD-6WR3`** (Mornsun): DC-DC **aislado** 18–75 V → 5 V 1.2 A | 2 | para alimentar el rig de la batería (39–48 V) y **jubilar el power bank**. Aislado: el ESP sigue con GND = amarillo. Con fusible a la entrada. No se consigue en C&D |
> | opcional | **`MCP6002-I/P`** (o `MCP602`), op-amp rail-to-rail DIP8 | 4 | el timón a 5 V sin el tap de +11 V del blanco ni el zener (`emulador_timon/LEEME.md`). El LM358 ya está validado; esto es mejora, no bloqueo |
>
> **No se pide todavía:** conectores del pedal y del timón (no se conoce el modelo hasta el martes),
> relés mecánicos (C&D), `MCP4728` (en LCSC es chip suelto para soldar).

**La terminación.** Nada de lo de arriba se elige por traer 120 Ω: hoy el bus mide **120 Ω** y el
manual pide **60** (falta un terminador, `CLAUDE.md` 03-oct). Con un 120 nuestro quedaría en 60.
**No se decide por la ficha: se mide.** Llave OFF, rig conectado, óhmetro CANH↔CANL:
**≈ 60 Ω** está bien; **≈ 40 Ω** son tres terminadores y sobra el nuestro. (Esto matiza el «no
agregar 120 Ω» de arriba, que se escribió sin contar el terminador que falta.)

**El reductor de voltaje no entra.** Los módulos aislados se alimentan del lado del ESP, y el
lado del bus se alimenta solo por el DC-DC interno. El DROK no puede con los ~40 V de batería.

<details><summary>Primera versión de esta lista (02-nov, mañana), reemplazada</summary>

Pedía los dos caminos en piezas: `TD301DCANH3` ×2 como prioridad 1, y `ADuM1201` ×2 +
`B0505S-1WR3` ×3 como prioridad 2, para armar. **Qué la tumbó:** maje no quiere armar si se puede
comprar entero.
</details>

| Opcional, en el mismo pedido | Para qué |
|---|---|
| `MCP4728`, DAC de 4 canales I²C, ×1 | quitar el residuo de ~2 % del DAC nativo del timón, si el nodo 4 resulta quisquilloso |

**No sirve, aunque salga en la búsqueda:** el **Waveshare ESP32-S3-CAN-2CH**. Tiene el CAN
aislado y bien hecho, pero el **ESP32-S3 no tiene DAC**, y el timón usa los DAC de GPIO25/26. Lo
mismo para cualquier placa con S3, C3 o C6: el rig es un **ESP32 clásico (WROOM)**.

**Al llegar el módulo:** pinout y consumo **contra la hoja de datos de Mornsun**, no contra
la foto de Amazon. Si consume más de ~100 mA a 3.3 V, no se cuelga del regulador del ESP; va con
su propio regulador desde el power bank. Su tierra del lado del bus (`CANG`) va al **negativo de
batería**, igual que `GND_bus` en `armado_aislado.svg`.

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
