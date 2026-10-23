# Dónde está cada cosa — «Arreglo de componentes»

Páginas 3 a 5 del manual de servicio (`herramientas/Codigos de error reach color_*.pdf`,
edición 12.14, ETR 335D / 340 / 345), sacadas como imagen con `pdftoppm`.

| Archivo | Pos. | Componente |
|---|---|---|
| `arreglo-003.png` | 1 | Controlador de elevación `2U1` |
| | 2 | Controlador de tracción `1U1` |
| | **3** | **Maestro MCF / módulo I-O `1U16`** |
| | 4 | Bloque de válvulas |
| | 5 | ventilador |
| | 6 | multipiloto (la palanca) |
| `arreglo-004.png` | 7 · 8 | motor hidráulico · motor de dirección |
| `arreglo-005.png` | 9 | controlador de dirección |
| | 10 · 11 · 12 | motor de tracción · claxon · caja de cambios |
| | **13** | **caja de fusibles** (donde está el DB9) |

## Cómo está armado el cerebro

Los sensores **no** van a la pantalla. Cada uno va a **su** controlador, y los controladores
hablan entre sí por el bus CANopen. La pantalla es otro nodo del bus (el nodo 3): cuando
se abre *Diagnose*, le **pide** los valores a los otros por el bus y los muestra.

El que coordina es el **Maestro** (nodo 1), que físicamente es el **`1U16`, «maestro MCF /
módulo I-O»**: la caja con conectores en el centro de la foto `arreglo-003.png`, al lado de
la base del multipiloto. El manual lo confirma por otro lado: el autotest «lo coordina el
maestro», los eventos van a su «libro de registro maestro», y hay un «ordenador de
seguridad» que compara contra él.

Los demás cerebros, cada uno con lo suyo:

| Nodo CAN | Qué | Dónde |
|---|---|---|
| 1 | **Maestro** | `1U16`, pos. 3 |
| 3 | Pantalla | en el tablero |
| 4 / 5 / 6 | Dirección / ruedas de carga | pos. 9 |
| 7 | Elevación | `2U1`, pos. 1 |
| 8 / 9 | Tracción | `1U1`, pos. 2 |
| 11 / 12 | MFC frenos / MFC hidráulica | ligados al `1U16` |

**Para el proyecto:** si *Diagnose* muestra los sensores, esos valores **ya viajan por el
bus**. Es la mejor señal hasta ahora de que la retroalimentación de velocidad, ángulo y
altura se puede leer sin tocar un cable. Es el paso C de `herramientas/pendientes.md`:
escuchar el bus **mientras** la pantalla pide datos.

## El multipiloto instalado — foto del 03-oct

`multipiloto_instalado.jpg`. Palanca con funda de fuelle, botonera de 4 flechas arriba,
montada sobre placa con cuatro tornillos. Abajo:

- **Un conector redondo** con los números **2 · 4 · 6 · 8 · 10 · 12 · 14** visibles en la
  cara (los impares quedan del otro lado): **unos 14 pines, y muchos cables poblados**
- **Un conector blanco chico, de 2 vías**, aparte, al costado. No se sabe qué es

**Dato en tensión:** un nodo CAN necesita **4 hilos** (CANH, CANL, + y −). Este trae muchos
más. Dos lecturas, sin elegir:

1. **En este equipo la palanca es analógica/discreta** y la lee el `1U16`, el «módulo I-O»
   que está justo al lado. El «nodo 2» de la tabla del manual sería la variante CAN de otros
   equipos de la familia
2. **Es nodo CAN y además lleva señales cableadas aparte** (botones de seguridad dobles,
   claxon, alimentación de sensores)

**Lo decide:** contar los pines poblados, foto de frente del conector suelto, y la etiqueta
de la palanca (fabricante y número de parte, debajo de la placa).

### La etiqueta — 03-oct (`multipiloto_etiqueta.jpg`, `multipiloto_cabezal.jpg`)

```
JUNGHEINRICH          Made in Germany
M.Nr.     51232662    ← número de material Jungheinrich (el que se pide)
Index     H           ← revisión
Lief.Nr.  1848        ← código del proveedor
S.Nr.     P5134200084H
W.Nr.     S170100312096
```

- **Es pieza Jungheinrich original**, no Mitsubishi. Cuadra con que el equipo sea un ETR
- `51232662` **no aparece en el manual de servicio** ni en una búsqueda web rápida
- El cabezal desenchufado es **macho, dos filas de ~7 pines**, en carcasa ovalada con dos
  tornillos. Al costado de la carcasa hay una **lengüeta faston metálica**: candidata a masa
  de carcasa / blindaje, sin medir
- **Para el repuesto:** comparar su `M.Nr` e `Index`. Si no son `51232662 H`, cuidado con el
  evento `6.71` sub 2 — «tipo de piloto incompatible» — que el maestro revisa al arrancar
- **Ficha del mazo, contada por maje el 03-oct: 11 de 14 posiciones con cable.** Vacías:
  **11, 12 y 14**. Un nodo solo-CAN usaría 4; once hilos dicen que por ahí viajan señales
  cableadas además (o en vez) del bus
- ~~**El conector blanco chico del costado es masa**~~ (maje, 03-oct, dicho antes de medir).
  **Corregido el mismo día por maje, midiendo:** con el pitido, el blanco **no pita a masa**.
  Queda **sin identificar**; falta medirlo en escala de 200 Ω (el pitido no ve más de ~50 Ω)
- **Pin 7 de la ficha: continuidad (pitido) con masa.** Candidato a **negativo de
  alimentación** del multipiloto. Medido **contra el negativo de batería**

### Voltajes de la ficha del multipiloto — 03-oct, llave ON, contra negativo de batería

| Pin | Escala | Lectura | Lectura probable |
|---|---|---|---|
| 1 | 2 V | 0.022 | ~0 |
| 2 | 200 V | 2.3 | **zona CAN (~2.5 V)** |
| 3 | 200 V | 2.3 | **zona CAN** |
| 4 | 200 V | 2.4 | **zona CAN** |
| 5 | 200 V | 2.1 | **zona CAN** |
| 6 | 2 V | 0.016 | ~0 |
| 7 | — | continuidad a batería − | **negativo de alimentación** |
| 8 | 200 V | **39.2** | **positivo de alimentación — tensión de BATERÍA, no 24 V** |
| 9 | 2 V | 0.014 | ~0 |
| 10 | 2 V | 0.016 | ~0 |
| 13 | 2 V / 200 V | 0.016 / oscila 2–10 | **inconsistente**: ¿señal pulsada, o flotante? |

**Lectura, sin cerrar:**

- **Cuatro pines en ~2.3 V** son el aspecto de un bus CAN en reposo/actividad. Cuatro y no dos
  sugiere **dos pares**: el bus entra al multipiloto y sale hacia el siguiente nodo
  (encadenado), o hay dos buses. Se decide con óhmetro (abajo)
- **Pin 8 a 39.2 V:** el multipiloto toma la tensión de batería directo. **El equipo no es de
  24 V de batería**: 39.2 V cuadra con una batería de **36 V** cargada o de **48 V**
  descargada. Los «24 V» del manual son la lógica interna regulada (evento con `V24V`).
  **Todo lo que se conecte al equipo tiene que aguantar la tensión de batería**
- Con esto **gana la lectura 2**: el multipiloto es **nodo CAN**, más señales aparte en
  1, 6, 9, 10 y 13

**Pendiente:** 2–5 en escala de 20 V; con llave OFF, resistencia entre cada par de 2, 3, 4, 5
en 200 Ω; el pin 13 otra vez; la etiqueta de la batería; y si la ficha estaba enchufada o no.

**Segunda pasada, mismo día:**

```
20 V, llave ON:   2 = 2.3   3 = 2.3   4 = 2.3   5 = 2.0   13 = 0.015 (quieto, no oscila)
200 Ω, llave OFF: 2 ↔ 3 = 80 Ω        4 ↔ 5 = abierto
```

- **2 y 3 son un par CAN terminado.** 80 Ω y no 60: fuera del «60 Ω ± 10 %» del manual.
  Dato en tensión: puede ser un terminador más otra impedancia en paralelo (120 ∥ 240 = 80),
  la ficha enchufada o no, o la medición. No cambia que sea el par
- **4 y 5 no son un par terminado.** Siguen en ~2 V. Quedan sin identificar: otro bus sin
  terminar, o entradas del `1U16` polarizadas
- El 13 de la primera pasada era lectura mala; está en ~0

## El multipiloto de repuesto, abierto — 05-oct

`multipiloto_repuesto_tarjeta.jpg`, `_costado.jpg`, `_iman.jpg`. Leído de foto; las
marcas de los chips todavía no se leen.

| Qué se ve | Lectura | Firmeza |
|---|---|---|
| Tarjeta redonda, serigrafía «EB 111A» | la electrónica del nodo | foto |
| Bobina Würth («WE 400»), ferritas `FE1`/`FE2`, diodos `D1`/`D2`, dos electrolíticos «33 / 2A» | **fuente conmutada** que baja la tensión de batería; los «2A» serían 100 V. Cuadra con los 39 V del pin 8 | probable |
| Chip de 8 patas (SO-8) junto a `R17`/`C16` | **candidato a transceptor CAN** | falta leer la marca |
| `IC6`, chip grande de ~24 patas | microcontrolador o conversor | falta leer la marca |
| `LED1`, `LED2` | estado | foto |
| `X1` «**Pruef 2**», ~8 vías | **conector de prueba / programación de fábrica**. No se toca | foto |
| `X2`, ~14 vías | hacia el conector exterior de la carcasa | probable |
| Conector con **~12 hilos de colores** que bajan de la empuñadura | **los botones del mango** | foto |
| **Arco imantado** en el pivote de la palanca, debajo de la tarjeta | **la palanca se lee SIN CONTACTO, por efecto Hall**: un imán que se mueve sobre sensores en la cara de abajo | probable |

**Qué cambia en la ruta B (`docs/21`, 2.6):**

- **Botones: más fácil de lo pensado.** Llegan por un conector enchufable. Se puede hacer un
  arnés que se enchufe ahí, sin soldar en la tarjeta
- **Palanca: más difícil.** No hay potenciómetro con cables donde meter dos canales de DAC.
  Las salidas son de sensores Hall soldados en la tarjeta. Opciones: levantar la salida del
  sensor (en el repuesto se permite), o **mover la palanca mecánicamente** (servo sobre el
  mango, sin tocar electrónica)
- **El imitador del bus (peldaño 5) gana puntos**: el nodo es «inteligente» de punta a punta

### Terminador del repuesto — 06-oct

maje, flex enchufado a `X2`, sin alimentar, 200 Ω, pines 2 ↔ 3 del conector de afuera:
**abierto** («¿capaz?»). Lectura provisoria: **el multipiloto no trae terminador.** Falta el
control de falsación: en escala de 20 k / 200 k el mismo par debería dar **algo finito** (la
entrada del transceptor). Si da abierto en todas las escalas, puede ser que el flex no esté
bien asentado y la medición no haya llegado a la tarjeta.

Si se confirma, el **80 Ω** medido en el equipo no lo explica el multipiloto y queda en tensión
con los 120 Ω del DB9.

## 07-oct · con el multipiloto desenchufado, la PANTALLA NO PRENDE

maje: con la ficha del multipiloto desenchufada, la pantalla (la única, nodo 3, la del mismo
mazo que el DB9) queda **totalmente oscura**: con el paro levantado, con la llave en ON, y con
las dos cosas. No es un código de falla: no hay pantalla que lo muestre.

**Lectura, sin confirmar:** algo de la alimentación o la habilitación del sistema **pasa a
través del multipiloto**. Un nodo que falta en el bus da una falla, pero la pantalla prende.
Candidatos: un puente interno entre pines de la ficha (1, 4, 5, 6, 9, 10, 13 sin
identificar), o una salida activa del multipiloto.

**Pega en la ruta B:** el imitador por el bus exige desenchufar el multipiloto. Lo que sea que
el multipiloto le da al sistema, el reemplazo lo tiene que dar también.

**Cómo se resuelve:**
1. En el repuesto, sin alimentar: **continuidad entre todos los pares** de los 11 pines del
   conector de afuera. Un par que pite es un puente → el reemplazo lleva el mismo puente
2. En el equipo: voltajes de los 11 pines **con el multipiloto enchufado** (por atrás de la
   ficha) contra la tabla de abajo. **Un pin en ~0 V desenchufado y en ~39 V enchufado es una
   alimentación que vuelve del multipiloto**
3. En el equipo, multipiloto desenchufado, escucha en el DB9: **¿hay tráfico CAN?** Si hay
   cero tramas, se apaga todo el sistema; si hay tráfico, solo la pantalla
4. Anotar si la tabla de voltajes del 03-oct se tomó con la ficha enchufada o desenchufada

## 17-oct · Hipótesis: el multipiloto es un eslabón de la cadena hacia la pantalla

**De dónde sale (pista, no dato):** el manual de Scribd que dio el `X200` (`manuales_scribd.md`)
muestra que el módulo ISM (`X680`, pág. 360) lleva **CAN de entrada y CAN de salida** (va *en* el
bus, encadenado) y una **alimentación de salida** («U-ISM out (24V)»). Si el multipiloto sigue
el mismo patrón de Jungheinrich:

| Pin | Hipótesis | Estado |
|---|---|---|
| 2 / 3 | CAN de entrada (desde el master) | **medido**: CAN_H / CAN_L, mismo hilo que el DB9 |
| 4 / 5 | CAN de salida, hacia el siguiente nodo | ~2 V desenchufado, 4↔5 abierto. Sin confirmar |
| 8 | alimentación de entrada | **medido**: +39.2 V |
| 7 | negativo | **medido** |
| uno de 1, 6, 9, 10, 13 | **alimentación de salida** hacia el siguiente módulo | a buscar |

Explicaría que **la pantalla no prenda sin el multipiloto**: estaría aguas abajo, y le llegarían
la alimentación y el bus a través de él.

**Lo que lo confirma o lo tumba:**
- Equipo, llave ON, multipiloto **enchufado**: el pin de «salida» pasa de ~0 V a tensión
- Repuesto, sin alimentar: continuidad **2↔4 y 3↔5** (bus que pasa por adentro), **4↔5** (¿trae
  terminador para el tramo de salida?), y **8↔cada pin** (salida pasiva)
- En la i3, del mismo PDF: págs. **25–30** (esquema del ETR 320, que es reach truck con
  Multi-Pilot: puede traer el pinout de su conector) y **352–355** (pines del display CANDIS)

## 19-oct · MEDIDO: ficha del multipiloto ENCHUFADO, llave ON, contra negativo de batería

| Pin | Desenchufado (03-oct) | **Enchufado (19-oct)** | Lectura |
|---|---|---|---|
| 1 | 0 | **16–17 V** | **se enciende con el multipiloto** |
| 2 | 2.3 | 3 | CAN_H con tráfico |
| 3 | 2.3 | 3.3 | CAN_L (lectura en escala de 200, gruesa) |
| 4 | 2.3 | 2.4 | igual |
| 5 | 2.0 | 2.1 | igual |
| 6 | 0 | **varía 0.05–12, se asienta en 0.7–0.9** | **señal activa** |
| 7 | negativo | 0.012 | negativo |
| 8 | 39.2 | 38–48 (saltos) | batería |
| 9 | 0 | **~9 V** | **se enciende con el multipiloto** |
| 10 | 0 | **5.2 V** | **se enciende** — parece una alimentación de 5 V |
| 13 | 0 | **12–22 V, variando** | **señal activa** |

**Cinco pines (1, 6, 9, 10, 13) solo tienen tensión con el multipiloto puesto.** Son **salidas que
genera su electrónica**, con valores distintos entre sí (5.2, ~9, 16–17, variables): no son
puentes pasivos del pin 8. Cuadra con la hipótesis del eslabón y con que la pantalla no prenda
sin él.

**Consecuencia para la ruta B:** un reemplazo tendría que generar esas cinco salidas. Lo simple
es **dejar el multipiloto real enchufado** (sigue dando las salidas) y **cortar solo su par CAN
(2 y 3) en un arnés**, con nuestro nodo en su lugar.

## 19-oct · placa de datos (`placa_datos.jpg`)

```
MODELO          EDR18N2
NÚMERO DE SERIE 82824121
Centro de carga A/B 600 mm (24"), desplazamiento 0
Altura máx horquilla 6858 mm (270") · capacidad 1600 kg / 3500 lb · mástil vertical
placa SP 51369424
```

- **Nº de serie `82824121`** — es el que va a MCF Parts Client para pedir la configuración
  (ancho entre patas `b1`, parámetros, esquema `99515375`)
- **Altura de horquilla 6858 mm.** El repo pedía `h3 = 6.77 m` hasta N5; la placa da **6.858 m**,
  un poco más. Holgado para el rack
- **Capacidad 1600 kg**, cuadra con que el IBC de 1000 L lleno pesa ~1.0–1.1 t

## 19-oct · el volante gira libre, no topa

maje: el volante del equipo **no tiene topes** — da vueltas sin fin. Es coherente con EPS
(steer-by-wire): no hay unión mecánica a la rueda, el sensor es **absoluto por vuelta** (el
seno/coseno) y el controlador cuenta vueltas. Por eso **no se puede «contar vueltas tope a
tope»**: ese método era de un volante mecánico. El 2.6 vs 5.5 del control Obed se resuelve de
otra forma: leer el parámetro `0x2414` por el bus (Diagnose o SDO), o mirar cuántas vueltas de
volante mueven la rueda de tope a tope **mirando la rueda**, no el volante.

## 19-oct · El conector de pedales (SAAB 6114013) y el sensor que falta

Fotos del 19-oct (conector en situ y en mano). Marca: **`SAAB 6114013`, `>PBT/ASA-GF30<`** —
housing automotriz TE/Tyco (SAAB fue el cliente original; Jungheinrich reusa la carcasa). **Dos
filas, 10 vías (2×5), traba secundaria roja (CPA). 10/10 pobladas** (maje; primero contó 8,
recontó 10 — el arnés está completo).

**Lo que falta no es el arnés sino un SENSOR que va entre este conector y la placa de pedales.**
Por eso el equipo no habilita marcha: sin sensor válido, el pedal está muerto. Reconcilia el
«hombre-muerto faltante» de sesiones previas: lo que quitaron fue el sensor, no el arnés.

**Qué vive en esta interfaz, del manual de servicio — dos bestias, dificultad opuesta:**

| Función | Evento | Qué es | Emular |
|---|---|---|---|
| Hombre-muerto (interruptor de pie) | `1.06` | switch de seguridad **NC + NO complementario**: solo valen 0/1 y 1/0; 0/0 o 1/1 por 500 ms = falla | **fácil**: dos contactos complementarios |
| Sensor de posición del pedal (freno) | `1.2x`/`1.7x` | **doble canal analógico**: Vf1 + Vf2 debe sumar **4.5–5.5 V**; posición en % | difícil: dos analógicas con suma fija |
| Rango del pedal | `1.36` | el rango se **aprende por TEACH-IN vía Judit** | bloqueante si se emula el analógico |

**Los dos pedales son iguales — hay que pisar ambos para que ande** (maje, vía Miguel): dos
canales de presencia, no freno + acelerador. El «acelerador» de este equipo es la palanca de
mano; el manual dice «pedal acelerador / palanca del timón» según variante.

**El atajo de Miguel (19-oct):** en el taller **puentean este conector para simular el pedal
pisado**, y tienen el **diagrama** (pendiente de conseguir). Clave: el puente respeta la
complementariedad **NC + NO** del `1.06` — un corto bruto da 0/0 o 1/1 y tira la falla; por eso
«no es difícil» *con el diagrama* y sí lo es a ciegas. **Esto resuelve el enable sin emular el
sensor analógico ni tocar Judit:** el teach-in deja de bloquear la marcha. El sensor de posición
solo haría falta para modular freno/velocidad por pedal, que no es el caso (la velocidad sale de
la palanca).

> **Seguridad:** el puente puesto es exactamente lo que le quita al equipo su interlock gratis.
> Entra solo en gato, con paro en mano, y sale al terminar. Ver `docs/21` §Runbook paso 5.

**Pendiente:** el diagrama del puente (Miguel); número de parte del sensor faltante (el chino);
y de fallback la matriz de los 10 pines (batería fuera: continuidad entre pines y a masa; y con
el pedal **suelto vs pisado**, qué pares abren/cierran = los switches). Tabla para llenar:

| Pin | Continuidad a | V (llave ON, vs neg. batería) | Suelto/pisado | Lectura |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

## 19-oct · El conector del multipiloto — identidad (foto moldeado)

Foto de frente del moldeado del conector del multipiloto. Leído:

```
42125800      ← número moldeado (OEM, no es SKU de estante)
>PBT<         material
GERMANY
1/2  1013     cavidad de molde / fecha
```

Collar de pines: una cara **2 4 6 8 10 12 14** (pares), la otra **1 3 5 7 9 11 13**
(impares) → **14 vías, 2 filas (2×7)**. Cuadra con «cabezal macho, dos filas de ~7 pines».

**Pista fuerte de familia (búsqueda web, sin confirmar SKU):** **Amphenol serie 42** —
*radially sealed flat housing, traba secundaria, 1–14 pines*, con cross-ref de números
automotrices alemanes. El prefijo `42`, el housing plano sellado, las 14 vías y el `GERMANY`
calzan. Probablemente **Amphenol-Tuchel**. El `42125800` es molde OEM; el mate de reposición
sale del catálogo Amphenol (cross-ref) o del chino/Miguel.

**Consecuencia para no cortar 2/3:** los housings sellados planos de esta familia tienen
**terminales removibles detrás de la traba secundaria**. Se libera la traba, con un pick se
**extraen los terminales 2 y 3** sin cortar cable, reversible. Es la alternativa al corte y no
exige conseguir un conector nuevo. Herramienta: pick de extracción de la serie (o genérico).

**Pendiente:** confirmar la serie exacta por el cross-ref Amphenol o preguntando al chino; y el
estilo de traba, para el pick correcto.

## 22-oct · El conector del multipiloto es un eslabón del TRONCO

Medido por maje: el repuesto puentea por dentro **2↔4 y 3↔5**; **el mazo no** (abierto en la
ficha hembra). El bus entra por 2/3 (DB9 + controladores 3/4/7/8/30) y sale por 4/5 (Master,
nodo 1). Sacar el CAN del multipiloto **parte el bus**.

**Arnés de la ruta B, probado:** multipiloto enchufado solo para alimentar (1, 6, 7, 8, 9, 10,
13), **2-5 fuera**, y **puente 2↔4 / 3↔5 en la ficha hembra del mazo**. Con eso la pantalla
prende (las 5 salidas no dependen de su CAN), el Master arranca y el nodo 2 lo pone el ESP32
por el DB9. Ver `docs/21`, 22-oct tarde.

## 23-oct · Quién es cada nodo — leído por SDO (`0x1008`, `0x1000`, `0x1018`)

| Nodo | Manual | `0x1008` nombre | `0x1000` | `0x1018` vendor / producto / rev / serie |
|---|---|---|---|---|
| 1 | Master `1U16` | **`VMC30`** (`1009`/`100A`: «Not used») | `0x04000000` | `0x99` / `05060708` / `090A0B0C` / `0D0E0F10` (relleno, no identidad real) |
| 2 | Multi-Pilot 1 | **`MP1`** | 0 | `0x102` / `0x4D` / `0x00011300` / **`0x00299094`** (serie 2723988) |
| 4 | Dirección 1 | **`APS36M-70C-35P`** | `0x03000000` | `0x99` (sin subs 2–4) |
| 7 | Elevación | **`ACS36L PUMP`** | `0x02000000` | `0x99` |
| 8 | Tracción 1 | **`ACS36S TRAC`** | `0x01000000` | `0x99` |
| 30 | «PC de servicio» | **`Supervisor 1.0`** | `0x0012D686` | `0x99` |
| 5, 6, 10 | Dirección 2/3, Multi-Pilot 2 | sin respuesta SDO | | |

- **Vendor `0x99` en todos los Jungheinrich**; el multipiloto es de otro fabricante (`0x102`)
- Nombres de controladores: `ACS36S TRAC` (tracción), `ACS36L PUMP` (bomba/elevación),
  `APS36M-70C-35P` (dirección). Sirven para buscar hojas de datos y repuestos
- **Dato en tensión:** el nodo 30 se llama «Supervisor 1.0», no algo de servicio. El manual lo
  pone como «PC de servicio» (Judit). ¿Es el `KD Medi CO 250K` haciendo de supervisor? Sin
  resolver
- 5, 6 y 10 no contestan SDO: o no tienen servidor SDO o no están (los PDO `205/206/20A` son
  del Master hacia ellos)

## 23-oct · Nodo 7 (Elevación, `ACS36L PUMP`): sus PDO, leídos por SDO

`sdo_inventario.py --pdos 7` (mapeo CiA 301 `0x1800`/`0x1A00`, `0x1400`/`0x1600`; log
`sdo_inventario_20261023-133951`). Qué objeto va en cada byte y su valor con la horquilla quieta:

| PDO | COB-ID · tipo | Contenido | Lectura |
|---|---|---|---|
| TPDO1 | `187` · 254 (por evento) | b0-1 `2001.01` = `0x3083` · b2-3 `2001.02` = 0 · b4-5 **`2030.02` = 3646** · b6-7 `2073.01` = 0 | `2001.01` = palabra de estado (su bit `0x80` alterna cada ~2 s, como un reloj). **`2030.02` = tensión de batería, ×0.01 V (36.46 V)** |
| TPDO2 | `287` · 10 (cada 10 SYNC) | b0 `2029.02` · b1-2 `2029.03` · b3-4 `2029.04` · b5 `2029.05` | todo 0 en reposo; a ráfagas sale `2029.04` ≈ 1001 con `2029.05` con signo, sin que nadie toque nada |
| TPDO3 | `387` · 10 | `2078.02` · `2096.01` · `2096.03` | siempre 0 en todos los logs |
| TPDO4 | `487` | — | **desactivado** |
| RPDO1 | `207` (del Master) | `2000.01` = `0xC1` · `2000.02` · `2000.05` · `2000.06` · `2029.01` · `2029.06` | palabra de mando del Master a la bomba + el grupo `2029` |
| RPDO2/3/4 | `307`/`407`/`507` | — | desactivados |

**La altura de uña no viaja en ningún PDO del nodo 7.** Cuadra con `0x23BA = 0` en el Master
(docs/16): la familia admite un **incrementador de altura** opcional (eventos `1.17.7`, `1.24`) y
esta unidad no lo trae. Lo que sí puede haber son **interruptores** (elevación libre NC+NO,
«altura superior/inferior», evento `1.24`), que serían bits de `2001.01`/`2001.02`. No se puede
confirmar sin subir la horquilla, y la hidráulica no se mueve (regla del repo).

**Consecuencia para TaTa:** la altura de uña necesita un **sensor nuestro** (de hilo o láser en el
mástil). Los índices `20xx` del nodo 7 no están en el manual: son internos del controlador ACS.
