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
