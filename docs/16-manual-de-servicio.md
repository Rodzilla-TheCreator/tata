# El manual de servicio — qué es, qué dice y qué cambia

> **Archivo:** `herramientas/Codigos de error reach color_240709_165336.pdf`
> 259 páginas, 21.5 MB, escaneado en un equipo Samsung y **traducido a máquina por Google**.
> Cada página lleva el sello «Machine Translated by Google». La traducción es mala: las tablas
> se desarman y hay palabras absurdas («Sistemas de AUTOBÚS» por *bus systems*, «õUNGHEINRICH»
> por *JUNGHEINRICH*). **Cuando algo suene raro, hay que ir al PDF original y mirar la página.**

El nombre del archivo dice «códigos de error». **No es solo eso.** Es el manual de servicio
completo del equipo.

---

## Lo primero, y lo más grande

La portada dice **ESR20N2 / ESR23N2 / EDR18N2**. El cuerpo del documento habla todo el tiempo
de **ETR 335d / 340 / 345**.

**Son la misma máquina.** El EDR18N2 es un **Jungheinrich ETR** con placa de Mitsubishi.

Eso cierra de una vez la discusión de Judit: **el chino tenía razón, y por una razón más fuerte
de la que se había supuesto.** No es que MCFA distribuya también Jungheinrich y por eso él
tenía la herramienta a mano — es que **el equipo es Jungheinrich**. Judit es su herramienta
nativa, no una prestada de otra marca.

**Consecuencia práctica:** toda la documentación Jungheinrich de la familia **ETR 335d/340/345**
aplica a este equipo. Eso abre una fuente de información que estaba cerrada.

---

## El bus

De la tabla «Sistemas de BUS utilizados», página 256 del PDF, leída sobre la imagen porque el
texto extraído se desarma:

```
ETR 335d/340/345 (05.14-)   →   CANopen,  250 kbaud
```

Sin ambigüedad: hay una sola X y está en la columna de CANopen 250 kbaudios.

### La tabla de nodos — páginas 247 a 249

| ID | Nodo | Componentes con ese ID |
|---|---|---|
| 1 | Maestro | |
| 2 | MULTIPILOT / SOLOPILOT 1 | controles de reposabrazos, CANDIS, JULIA |
| 3 | Pantalla 1 | ordenador de a bordo, pantalla de reposabrazos |
| 4, 5, 6 | Dirección 1, 2 (rueda de carga DER), 3 (rueda de carga IZQ) | procesador de control |
| 7 | Elevación | |
| 8, 9 | Tracción 1, Tracción 2 | |
| 11–14 | Interfaz 1–4 | MFC1 (frenos), MFC2 (hidráulica), interruptor de viaje, MFC 05 |
| 16, 17 | Controlador de batería, Cargador | |
| 19 | Pantalla 3 | selección de altura del estante |
| 28, 29 | Acceso 1, Acceso 2 | CanCode, ISM |
| **30** | **PC de servicio** | ← **aquí entra Judit** |
| **31** | **APM +** | ← **«Interfaz de automatización (PLC)»** |

**Dos hallazgos de peso, en una sola tabla.**

### 1 · Judit entra como nodo CAN

El «PC de servicio» tiene **ID de nodo CAN fijo, el 30**. No es un periférico serie: es un
**nodo más del bus CANopen**. Eso significa que Judit **habla CANopen**, y que la conexión que
usaba el chino tenía que llegar, de una forma u otra, al bus CAN de 250 kbaud.

### 2 · Existe un nodo de automatización, de fábrica

El **nodo 31, APM+, descrito como «Interfaz de automatización (PLC)»**. El fabricante ya
contempló que algo externo maneje este equipo por el bus, y le reservó un ID.

**Esto no estaba en ningún supuesto del proyecto.** Todo el `docs/10` se escribió asumiendo que
la única forma de entrar era interceptar señales eléctricas — cortar Hall, inyectar con un DAC
de cuatro canales, relés en el hombre-presente. Si el APM+ está implementado en este equipo y se
sabe su protocolo, **hay una puerta de fábrica**.

> **Ojo con el entusiasmo.** Que exista el ID no significa que esté implementado en esta
> máquina, ni que su protocolo sea público, ni que Jungheinrich lo habilite sin licencia. Es una
> **pista fuerte y una pregunta nueva**, no una solución. Lo que sí cambia hoy: la pregunta
> «¿hay una interfaz de automatización?» dejó de ser especulación y tiene un nombre — **APM+** —
> con el cual buscar y con el cual preguntarle al chino y a Jungheinrich.

---

## Los parámetros — capítulo completo, páginas 21 a 35

Vienen con su **índice del diccionario de objetos CANopen** (`0x2100`, `0x2414`, …), que es
exactamente lo que un maestro CANopen usa para leerlos y escribirlos por SDO.

### Tracción

| Índice | Parámetro | Mín | Máx | Fábrica |
|---|---|---|---|---|
| `0x2100` / `0x2110` / `0x2120` | aceleración, programas 1/2/3 | 0.15 | 1 m/s² | **0.7 / 0.85 / 1.0** |
| `0x2108` / `0x2118` / `0x2128` | velocidad sentido tracción, prog. 1/2/3 | 5 | 12.9 km/h | **9 / 10.5 / 12.9** |
| `0x210C` / `0x211C` / `0x212C` | velocidad sentido horquilla, prog. 1/2/3 | 5 | 12.9 km/h | **9 / 10.5 / 12.9** |
| `0x2109` / `0x210D` | velocidad de arrastre | 1.4 | 7 km/h | **3** |
| `0x2104` / `0x2114` / `0x2124` | deceleración, programas 1/2/3 | 0.3 | 2 m/s² | **1.0 / 1.5 / 2.0** |
| `0x2106` / `0x2116` / `0x2126` | rampa de inversión, programas 1/2/3 | 0.5 | 2 m/s² | **1.0 / 1.5 / 2.0** |
| `0x2107` / `0x2117` / `0x2127` | rampa de reducción, programas 1/2/3 | 0.3 | 1.75 m/s² | **1.5 / 1.6 / 1.75** |
| `0x219F` | retardo de caída del freno al parar | 0.1 | 20 s | **2 s** |

**Los tres programas P1/P2/P3 son esto**, y son parámetros escribibles, no modos fijos.

**Y calza con el campo.** Los **7.9 km/h medidos** están justo debajo del programa 1 (9 km/h) y
lejos de los 12.9 de catálogo, que es el programa 3. Ya no hay que explicar la diferencia entre
ficha y realidad: **el equipo está en un programa conservador**, y el número de catálogo es el
tope del programa 3.

### Dirección

| Índice | Parámetro | Mín | Máx | Fábrica |
|---|---|---|---|---|
| `0x2414` | **relación de dirección** — vueltas de volante de tope a tope | 4 | 8 | **5.5** |
| `0x2415` | posición de inicio del sistema | 0 = última conocida | 1 = centrada | 0 |
| `0x2416` | sentido de la dirección | 0 = invertido | 1 = directo | 0 |

> **Esto desmiente un número del visor.** El **control Obed usa 2.6 vueltas de tope a tope**.
> El parámetro de fábrica es **5.5**, con rango de 4 a 8. **El timón del simulador es más del
> doble de rápido que el real.** No se corrige a ciegas: el valor real de esta máquina se lee
> del equipo (es `0x2414`) o se cuenta a mano girando el volante tope a tope. Pero el 2.6 queda
> marcado como **sospechoso, sin respaldo**.

### Parámetros de desarrollo — páginas 34 y 35

Sin índice CANopen listado, pero con nombres que importan:

```
Vstart_of_reduction_steer_ratio     5 … 12.9 km/h    fábrica 8 km/h
reduced_steer_ratio                 relación de dirección a velocidad máxima
Presión_Reducción_start             1 … 150 bar      fábrica 44
Presión_Reducción_fin              20 … 200 bar      fábrica 116
Presión_Reducción_Min_Velocidad     1 … 12.9 km/h    fábrica 11
rampa de freno interruptor tracción paso 1   0.3 … 3 m/s²   fábrica 2
```

**El recorte de ángulo de dirección con la velocidad, que el control Obed implementa, es real y
es parámetro.** Empieza a los **8 km/h** de fábrica. El simulador lo modela; ahora se sabe que
existe y cómo se llama.

Y aparece algo que **no está en ningún modelo de TaTa**: la velocidad se reduce **por presión
hidráulica** — o sea, **por peso de la carga**. Entre 44 y 116 bar la velocidad baja hasta 11
km/h. El supuesto de que cargado y vacío se mueven igual vale para la **geometría del giro**
(eso se confirmó en campo), pero **no para la velocidad**.

### Otros que sirven

| Índice | Parámetro | Nota |
|---|---|---|
| `0x23BB` | altura de elevación libre | 60–5000 mm, fábrica **2500**. Dónde pasa de elevación libre a mástil |
| `0x23BA` | altura de elevación | 0 = no instalado · 1 = indicador · **2 = preselector de altura instalado** |
| `0x23D1` | peso de carga | 0 = no instalado · 1…2040 = peso de calibración y **pantalla de peso instalada** |
| `0x2612` | unidades | 0 = pulgada/mph · 1 = métrico |
| `0x2620` | idioma | 0 = inglés · **1 = español** · 2 = francés · 3 = portugués |
| `0x2621` | **Monitor / Clave** | 0–9999, **fábrica 4444** |

**`0x23BA = 2` es interesante para TaTa.** Si esta máquina trae **preselector de altura de
estante**, ya existe de fábrica la noción de «ir al nivel N» — y el nodo 19 de la tabla CAN es
justamente «Pantalla 3 — selección de altura del estante». Hay que verificar si esta unidad lo
trae.

**El `0x2621` con fábrica 4444** parece la clave de acceso del monitor. **No se ha probado y no
se va a probar sin permiso** — es equipo de un cliente.

---

## Los códigos de error

214 páginas, de la 36 a la 249. Es la mayor parte del documento. Formato de cada fila:

```
F  E  XX  S   Estado operacional   Descripción   Causa / Evento desencadenante   Acción
```

No se transcriben acá: son miles. **Se consultan con grep sobre el texto extraído.** Para
extraerlo:

```bash
pdftotext -layout "herramientas/Codigos de error reach color_240709_165336.pdf" codigos.txt
grep -n -i "lo que sea" codigos.txt
```

Lo que sí conviene saber de entrada: **la acción recomendada dice «JUDIT» por todos lados.**
Teach-in de sensores, ajuste de altura de elevación libre, verificación de salidas, lectura del
libro de registro de errores. Confirma que Judit no es opcional para el servicio de este equipo.

---

## Lo que el PDF NO trae

**Los diagramas eléctricos no están.** La página 20 es solo el índice de dibujos:

```
Sistema eléctrico    dibujo nº 99515375    esquema eléctrico
Hidráulico           dibujo nº 99520170    esquema hidráulico
```

**Esos dos números son lo que hay que pedir.** Son la referencia exacta para solicitarlos por
Montasa. Sin el 99515375 no se sabe a qué va cada cable del DE-9, y esa es la pregunta abierta
más cara del proyecto.

---

## Lo que cambia sobre el puerto DE-9 — y la tensión que abre

Hasta ahora se había concluido: **no es CAN**, por el −14.6 V estable medido en el pin 3.

El manual empuja en la dirección contraria: **el PC de servicio es un nodo CANopen**, y ese es
el camino que el chino usaba.

**Las dos cosas no pueden ser ciertas a la vez, y no se resuelve adivinando.** Hay tres salidas
posibles, todas vivas:

| # | Salida | Qué la haría cierta |
|---|---|---|
| 1 | El DE-9 **sí es CAN**, y la medición está referida mal | Si el **chasis no es el negativo de batería**, todo lo medido con la punta negra a chasis está corrido. Un bus CAN de 0–5 V referido a batería podría leerse negativo contra un chasis flotante |
| 2 | El DE-9 **no es el puerto de Judit** | Sería un puerto de otra cosa — tablero, telemetría — y el de servicio está en otro lado |
| 3 | El DE-9 **lleva las dos cosas** | Algunos pines CAN, otros serie. Pasa en conectores de servicio |

**El cable de fábrica del taller sube de categoría.** Mapeaba a pines **2, 6, 7, 9** —
exactamente **CiA-303, el pinout estándar de CAN sobre DE-9** (2 = CAN_L, 6 = GND, 7 = CAN_H,
9 = V+). Cuando se midió, era un dato en tensión con procedencia sin confirmar. Con el manual
diciendo que el bus es CANopen, **ese cable ahora parece exactamente lo que aparenta ser.**

Y el **2↔7 abierto** sigue sin descartar nada: un stub de diagnóstico normalmente **no lleva
terminador**. Nunca fue evidencia contra CAN.

### La medición que lo resuelve, y va primero

**Antes de cualquier otra cosa en el equipo:**

```
1.  negativo de batería  ↔  chasis        ¿son el mismo punto o hay voltaje entre ellos?
2.  pin 6 del DE-9       ↔  negativo de batería
3.  pin 3 del DE-9       ↔  negativo de batería      ← el −14.6 V, bien referido
4.  pin 2 y pin 7        ↔  negativo de batería      ← CAN_L y CAN_H en reposo ≈ 2.5 V
```

**Si contra el negativo de batería los pines 2 y 7 dan ~2.5 V en reposo, es CAN y se acabó.**
Si el pin 3 sigue dando −14.6 V contra el negativo de batería, la medición estaba bien y la
respuesta está en las salidas 2 o 3.

**Es una medición de cinco minutos que puede reorientar el proyecto entero.** Va antes que las
tres pasadas de escucha del ESP32.

### Y si resulta CAN

El ESP32 que ya se tiene **no sirve solo** para CAN: hace falta un **transceptor CAN**
(MCP2515 con transceptor, o un ESP32 con TWAI y un SN65HVD230). Barato, pero es otra compra.

**La regla no cambia: solo se escucha.** Un transceptor CAN puede ponerse en **modo listen-only
/ silent**, que no manda ni siquiera los bits de reconocimiento. Es la única forma aceptable de
tocar un bus vivo en equipo ajeno. A 250 kbaud, escuchando, se ve todo el tráfico sin
participar.

---

## Lo que el manual NO resuelve

**El ancho entre patas, `b1`, no sale de acá.** La página 20 del PDF lo lista como
**opción de pedido**: «Ancho total entre patas de base b1», con valores de **838 a 1524 mm en
pasos de media pulgada (12.7 mm)**, según el tamaño de rueda de carga y la configuración BLO.
Depende de cada unidad, no del modelo.

Dos cosas se ganan igual:

1. **El 1.315 del repo es un valor válido de la tabla:** 51.75" = **1314.45 mm**. Deja de ser un
   número inventado y pasa a ser una opción real de catálogo — pero **sigue sin confirmarse que
   sea la de esta máquina**.
2. **Los valores son discretos.** Al medir con flexómetro no hace falta precisión de milímetro:
   se mide, se busca el valor de tabla más cercano y ese es el bueno.

Y el camino limpio: **con el número de serie de la placa, MCF Parts Client da la configuración
exacta de esa unidad.** Eso resuelve `b1` sin flexómetro.

---

## Qué hacer con esto, en orden

1. **Las cuatro mediciones contra negativo de batería.** Cinco minutos. Decide si el puerto es
   CAN y por lo tanto decide qué instrumento sirve
2. **Pedir el dibujo 99515375** (esquema eléctrico) por Montasa. Es el que dice qué es cada pin
3. **Preguntarle al chino por el APM+**, por nombre. ¿Lo conoce? ¿Judit lo muestra? ¿Esta
   máquina lo trae?
4. **Verificar `0x2414`** — la relación de dirección real. Se cuenta a mano girando el volante
   tope a tope, sin ninguna herramienta. Corrige el 2.6 del control Obed
5. **Verificar `0x23BA`** — si trae preselector de altura de estante
6. **Sacar el número de serie de la placa** y pedir la configuración por MCF Parts Client. Cierra
   `b1` sin medir

---

## Historial

| Decía | Es | Qué lo tumbó |
|---|---|---|
| El chino tenía Judit porque MCFA distribuye también Jungheinrich | **El equipo ES un Jungheinrich ETR** rebautizado | La portada y el cuerpo del propio manual |
| «Es imposible que sea CAN», por el −14.6 V | **Abierto.** El PC de servicio es nodo CANopen 30 | La tabla de nodos, páginas 247–249 |
| El cable ethernet-a-DB9 del taller es un dato raro sin procedencia | **Coincide con CiA-303 y el bus es CANopen.** Sube de categoría | La tabla de sistemas de bus, página 256 |
| El control Obed usa 2.6 vueltas de volante tope a tope | **Sospechoso.** El parámetro de fábrica es 5.5, rango 4–8 | `0x2414`, página 30 |
| Cargado y vacío se mueven igual | **Solo en geometría de giro.** La velocidad se recorta por presión hidráulica | Parámetros de desarrollo, páginas 34–35 |
| Los 7.9 km/h de campo contradicen los 12 de catálogo | **No se contradicen.** 7.9 es programa 1 (fábrica 9), 12.9 es programa 3 | `0x2108` / `0x2128`, páginas 21–23 |
| La única entrada es interceptar señales eléctricas (`docs/10`) | **Existe el nodo 31, APM+, «interfaz de automatización (PLC)»** | Tabla de nodos, página 249 |
