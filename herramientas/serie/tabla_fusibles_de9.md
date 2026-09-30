# La tabla de fusibles y el DE-9 — foto de campo

**Fotos:** tomadas el 26-sep-2026 en el taller Las Palmas, sobre el EDR18N2 fuera
de operación.

| Archivo | Qué muestra |
|---|---|
| `tabla_fusibles_de9.jpg` | vista general: el DE-9, la regleta completa y la etiqueta |
| `tabla_fusibles_de9_detalle.jpg` | el extremo derecho de cerca: cola de la etiqueta y la serigrafía de la tarjeta |
| `de9_conector.jpg` | el DE-9 de cerca, y el extremo izquierdo de la regleta |
| `modulo_jungheinrich.jpg` | **la placa de un módulo Jungheinrich, atrás de la misma caja.** Ver la sección propia, abajo |
| `tarjeta_fusibles_reverso.jpg` | **la tarjeta desmontada, lado de soldadura.** Las pistas a la vista. Ver la sección propia, abajo |
| `conector_te_tarjeta.jpg` | el conector TE de la tarjeta, de cerca y de frente. Es el que lee bien el número |
| `conector_te_1-965484-1.jpg` | el segundo conector de la tarjeta, de frente. **Confirma el `1-965484-1` que ya estaba en `docs/15`** |
| `manual_fusibles_p142.jpg` · `manual_fusibles_p143.jpg` | **la tabla de fusibles del manual impreso.** Dibujo de la tarjeta con el DB9, y qué es cada fusible con su amperaje. Ver la sección del 30-sep, al final |

Primera foto del DE-9 **en su lugar**, con la tabla de fusibles y su etiqueta en
el mismo cuadro. Hasta ahora el conector solo estaba descrito por texto.

---

## Lo que se ve

- **El DE-9 hembra, arriba a la izquierda, montado sobre una tarjeta verde**, no
  colgando de un mazo suelto. Comparte placa con la regleta de fusibles
- **Está hundido**, con la carcasa metálica de la tabla pasando por enfrente. Eso
  confirma por qué el cable de Judit tenía capuchón delgado y por qué un DB9 de
  bornera no entra
- Los tornillos hexagonales del conector están a la vista, o sea que se puede
  atornillar el capuchón si hace falta
- **Faltan dos fusibles.** Dos posiciones vacías en la regleta

### La etiqueta, transcrita

Se lee de corrido, rotada 90°.

**La cola está confirmada** por la segunda foto, `tabla_fusibles_de9_detalle.jpg`,
tomada de cerca sobre el extremo derecho:

```
… 1F13   4F10   2F18   F27
  7.5A   2A     10A    5A
```

**El resto es lectura de la foto lejana y NO está confirmado:**

```
F17  4F15  5F3  F4    5F2   3F11  4F9  5F7  3F14  6F9
5A   2A    2A   7.5A  7.5A  2A    2A   2A   2A    ?
```

`6F9` es el que queda sin resolver: es la bisagra entre el tramo leído de lejos y
la cola confirmada. Necesita su propia foto de cerca.

#### Corrección — 26-sep-2026

| Decía | Es | Qué lo tumbó |
|---|---|---|
| `6F9` 7.5A · `1F13` 2A · `4F10` 10A · `2F18` 5A | **`1F13` 7.5A · `4F10` 2A · `2F18` 10A · `F27` 5A** | la foto de cerca del extremo derecho |

La primera lectura salió de la foto lejana, con la etiqueta rotada, y **se corrió
una posición**: le faltaba un valor a la fila de abajo y todo lo de la derecha
quedó desplazado. Se conserva el error acá porque explica por qué **no se debe
confiar en un mapeo leído de lejos**, que es justo lo que más abajo queda
pendiente de resolver.

**Todo es de 2 a 10 A.** Eso es circuito de control, no de potencia — coherente
con que el DE-9 viva en esta misma placa y cuelgue del bus de control, que es uno
de los argumentos de `docs/15` para creer que es el puerto de servicio.

### Los fusibles puestos, de arriba hacia abajo en la foto

```
5 · VACÍO · 10 · 7.5 · 7.5 · 10 · 2 · 2 · 2 · VACÍO · 7.5 · 10 · 10 · 5
```

`de9_conector.jpg` confirma de cerca el extremo izquierdo: **la primera posición
vacía es la segunda de la fila**, y el portafusible sigue ahí — se sacó el fusible,
no se desmontó nada.

### El DE-9, de cerca

`de9_conector.jpg` es la mejor vista del conector hasta ahora:

- **9 pines en dos filas, 5 arriba y 4 abajo. Hembra.** Descarta VGA sin discusión
- **Con tornillos de fijación a los dos lados** — el capuchón se puede atornillar
- **Montado pasante en la misma tarjeta verde**, justo debajo de la regleta. No
  cuelga de un mazo: es parte de la placa
- Se le ven **dos islas de soldadura sueltas** en la tarjeta, a la derecha del
  conector. Sin identificar

### La tarjeta, serigrafiada

De la foto de cerca:

```
Littelfuse                 ← logo del fabricante
P/N : 852-023              ← número de parte de la tarjeta
UL94V-0                    ← clase de inflamabilidad del laminado
```

**`Littelfuse 852-023` es número de parte buscable.** Es la tarjeta porta-fusibles,
no el montacargas, pero da la hoja de datos de la regleta: cuántas posiciones
tiene, cómo van numeradas de fábrica y cómo se reparten los rieles de
alimentación. Eso es justamente lo que hace falta para el mapeo pendiente.
**Buscarlo es gratis y se hace desde la compu, sin el equipo enfrente.**

---

## El dato en tensión que salió de la foto de cerca

En el extremo derecho, la etiqueta y los fusibles puestos **no calzan posición
por posición**:

```
etiqueta    1F13 7.5A   4F10 2A   2F18 10A   F27 5A
fusibles     7.5         10        10         5
                         ↑
                    la etiqueta pide 2A y hay un 10A
```

Dos lecturas posibles, y **no se elige ninguna todavía**:

1. **La etiqueta no está alineada con la regleta.** Es un rótulo de referencia, no
   un mapa posicional. Sería lo más común
2. **Está alineada y alguien puso un fusible que no corresponde.** En una máquina
   que están canibalizando, eso no es descabellado

La segunda importa más de lo que parece: un 10 A donde el fabricante pide 2 A deja
un circuito de control sin su protección. **No se toca** — se anota y se le
pregunta al chino.

Cualquiera de las dos que sea, **refuerza lo de abajo**: el mapeo se verifica con
el óhmetro, no leyendo la etiqueta.

---

## Lo que NO se sabe todavía

**Cuál posición física corresponde a cuál etiqueta.** La etiqueta está rotada y
puede correr en sentido contrario a la regleta. **No se asume el mapeo** — se
verifica con el óhmetro o con una foto más abierta que agarre la etiqueta y la
regleta alineadas.

**Cuáles dos faltan, por nombre.** Es lo que importa, y sale de lo de arriba.

---

## Por qué esto importa hoy, y no mañana

> **Hipótesis viva: si uno de los fusibles que faltan alimenta esta placa o el
> riel del que cuelga el DE-9, el puerto se queda mudo y el barrido de las 54
> combinaciones no dice nada del equipo — dice del fusible.**

Cuesta dos minutos descartarlo y, si no se descarta, se puede quemar el día
entero buscando en el lugar equivocado. **Va antes de concluir «SILENCIO».**

Cómo se descarta, sin meterle nada al equipo:

```
1. Identificar por nombre los dos que faltan (mapeo etiqueta ↔ regleta)
2. Con el equipo encendido, medir tensión en los dos bornes de cada
   posición vacía. Si un lado tiene tensión y el otro no, ese circuito
   está cortado por el fusible que falta
3. Continuidad entre el pin 5 del DE-9 y la masa de la placa
```

**No se pone un fusible.** El equipo está siendo canibalizado y no sabemos por qué
se sacaron. Poner uno es meter corriente a un circuito que alguien abrió a
propósito, y eso rompe la regla de «nada irreversible». Si hace falta, lo decide
el chino.

---

## Lo que sigue pendiente de esta misma vista

Con los paneles abiertos y esta placa a la vista:

```
□ Foto del REVERSO de la placa: a dónde sale el mazo del DE-9
□ Foto más abierta, con la etiqueta y la regleta alineadas, para cerrar el mapeo
□ Foto de cerca del tramo de 6F9 hacia la izquierda, para cerrar la etiqueta
□ Buscar la hoja de datos de la tarjeta Littelfuse 852-023  ← gratis, desde la compu
□ ¿Hay número de parte serigrafiado en la tarjeta verde?
```

El reverso es el que decide la pregunta cara: si el mazo llega al controlador de
tracción, el DE-9 es el puerto de servicio y se acabó la duda. Ver `docs/15`.

---

# El módulo Jungheinrich — 26-sep-2026

`modulo_jungheinrich.jpg`. Atrás de la misma caja, una **placa de fabricante
Jungheinrich** sobre un módulo negro. En el borde izquierdo de la foto asoma una
tarjeta verde.

```
JUNGHEINRICH
F.Nr:  51540777
Bez.   KD Medi CO 250K Jr.
S-Nr.  802O6202                    DSE
```

Y el conector que le entra, de unos 9 conductores, marcado:

```
TE  1-962353-1        ← AMP Junior Power Timer
```

## Por qué esto importa

**Hasta hoy, que el EDR18N2 fuera un Jungheinrich era una inferencia de
documento.** Salía del manual de servicio, cuyo cuerpo habla de ETR aunque la
portada diga Mitsubishi. Buen argumento, pero papel.

**Ahora está en el fierro, con marca de fábrica, en la máquina que tenemos
enfrente.** Eso deja de ser lectura y pasa a ser observación. Y con ello:

- Toda la documentación Jungheinrich de la familia ETR aplica a este equipo, sin
  el asterisco
- El chino tenía **la herramienta nativa del equipo**, no una prestada de otra
  marca. Otra vez tenía razón
- **`F.Nr 51540777` es número de parte Jungheinrich**, buscable en catálogo. Es la
  vía limpia para saber qué es exactamente este módulo

## La lectura del `Bez.`, que es una hipótesis fuerte y NO una conclusión

`Bez.` es *Bezeichnung*, «denominación» en alemán. Desarmando
`KD Medi CO 250K Jr.`:

| Trozo | Lectura propuesta | Confianza |
|---|---|---|
| `CO 250K` | **CANopen 250 kbaud** | alta — es exactamente el bus que declara el manual |
| `Jr.` | **Junior**, por el conector AMP Junior Power Timer que tiene puesto | alta — el conector está a la vista y es de esa familia |
| `KD` | **Kundendienst**, «servicio al cliente» en alemán | media |
| `Medi` | sin resolver. ¿*Medium*? ¿mediador, o sea pasarela? | **baja. No inventar** |

> **Si `KD` es Kundendienst y `CO 250K` es CANopen 250 kbaud, este módulo es
> «servicio, CANopen 250K» — que es la descripción de la pasarela que se propuso
> el 25-sep para explicar cómo un DE-9 serie convive con el nodo 30 del manual.**

Eso encajaría demasiado bien, y por eso mismo hay que desconfiar: es la
explicación que uno *quiere* encontrar. **Se anota como hipótesis con nombre, no
como hallazgo.**

## Qué la confirma o la tumba, en orden de qué tan barato es

```
1. Buscar F.Nr 51540777 en catálogo Jungheinrich     ← gratis, desde la compu
2. Preguntarle al chino qué es esa caja               ← gratis, y él la ha visto
3. Seguir si la tarjeta verde del DE-9 es de ESTE módulo o de otro
4. Continuidad: ¿los pines del DE-9 llegan al conector 1-962353-1?
```

El punto 3 es el que puede cerrar la pregunta más cara del proyecto. En la foto
asoma una tarjeta verde pegada a este módulo; **si es la misma placa donde está
montado el DE-9, entonces el puerto cuelga directamente de un módulo Jungheinrich
de servicio y la duda de `docs/15` se acaba.** No se afirma todavía: hace falta
una foto que agarre el DE-9 y esta placa en el mismo cuadro.

## Dato en tensión con el repo

`docs/15` y `CLAUDE.md` dicen que el arnés del DE-9 es **TE 1-965484-1**. Este
conector es **TE 1-962353-1**. Son distintos, los dos de la familia AMP Timer.

Puede ser que sean dos conectores diferentes de la misma zona, o que el número
viejo estuviera mal anotado. **No se corrige ninguno de los dos todavía** — se
deja el par a la vista hasta que alguien lea la marca de los dos conectores con la
pieza en la mano.

## Lo que queda por leer de esta misma placa

```
□ El S-Nr. exacto: se leyó «802O6202» pero el cuarto carácter puede ser O o 0
□ Qué significa «DSE» a la derecha del código de barras
□ Foto que agarre el DE-9 y este módulo en el mismo cuadro
□ ¿Hay más placas Jungheinrich en otros módulos? Foto de cada una
```

---

# El reverso de la tarjeta — 26-sep-2026

`tarjeta_fusibles_reverso.jpg`. **maje sacó la tarjeta y fotografió el lado de
soldadura.** Las pistas quedan a la vista y se pueden seguir a ojo. Esto contesta
de una la pregunta del mapeo, que los dos días anteriores estaba trabada en
«no se adivina, se mide».

## Lo que maje trazó, con la tarjeta en la mano

> **El fusible que falta en la posición 2 va entre el pin 6 del DE-9 y el resto.
> Los demás fusibles van directo al conector TE que la tarjeta tiene por debajo.**

Eso es topología, no lectura de etiqueta. Y reordena varias cosas.

## El conector de la tarjeta

Marcado en el cuerpo:

```
ASSY  1-967281-1
>PBT/ASA-GF30<          ← el material del plástico, no un número de parte
```

**Corrección del mismo día:** primero se anotó `1-957281-1`, leído de la foto del
reverso donde el texto quedaba de canto. `conector_te_tarjeta.jpg`, de frente y
de cerca, lo lee **`1-967281-1`**. Manda esta.

Es un conector **grande, de dos hileras**, con traba roja de seguridad y un mazo
de más de veinte conductores. En la tarjeta corresponde a la doble hilera de
pines que se ve en el reverso. **Este es el mazo que entra al distribuidor.**

## Por qué el fusible faltante deja de ser una nota al pie

El pin 6 del DE-9 **está detrás de un fusible**. Un fusible no se pone en una línea
de señal ni en una masa: se pone en una **alimentación**. O sea que el pin 6 del
puerto **entrega corriente**, no datos.

Y eso reconcilia una medición vieja que estaba suelta:

| Medición del 18-sep | Se leyó como | Ahora |
|---|---|---|
| pin 6 = **+0.1 V, flotante** | «una entrada al aire, no importa» | **es la alimentación del puerto, y está muerta porque le falta el fusible** |

> **Hipótesis fuerte: el puerto no puede alimentar a la herramienta porque el
> fusible de su pin 6 no está puesto.**

Si el cable de Judit o la herramienta del otro extremo esperaban tomar corriente
de ahí, **el puerto puede estar mudo por esto y por nada más.** Deja de ser «una
cosa que hay que descartar antes de creerle al silencio» y pasa a ser **el primer
sospechoso**.

### Lo que NO se concluye todavía

- **Que poner el fusible lo arregla.** Alguien lo sacó. Puede haber sido para
  aislar una falla, y volver a energizar ese riel puede repetirla
- **Cuánta corriente y a qué tensión.** Sale del esquema `99515375`, que sigue sin
  conseguirse
- **Que el pin 6 sea masa.** El pinout CiA-303 pone masa en el 6, pero **esta
  tarjeta no está cableada como CiA-303**: una masa fusible no tiene sentido. Es
  un argumento más de que el DE-9 acá no es CAN

### Lo que lo confirma, por orden de qué tan barato es

```
1. Con la tarjeta afuera: continuidad del pin 6 del DE-9 al borne del
   portafusible 2. Es lo que maje ya trazó a ojo — confirmarlo con óhmetro
2. Del otro borne del portafusible 2, ¿a qué pin del conector TE llega?
3. Con todo montado y encendido: tensión en los dos bornes de esa posición
4. Preguntarle al chino por qué se sacó ese fusible
```

**No se pone el fusible hasta tener el 4.**

## Lo que esto le hace al resto de la investigación

- **El mapeo etiqueta ↔ regleta deja de bloquear.** Ya no hace falta para lo que
  importaba: la topología se sigue por cobre, que es mejor evidencia que un rótulo
- **El «10 A donde la etiqueta pide 2 A» sigue abierto**, y ahora se puede resolver
  por el mismo camino: seguir esa posición hasta su carga
- **Los demás fusibles van al conector TE**, o sea que esta tarjeta es un
  distribuidor: entra un mazo por abajo, sale protegido a los consumidores. El
  DE-9 está injertado en ese mismo distribuidor

## Los tres números TE, todos observados, ninguno descartado

Van apareciendo marcas distintas en la misma zona. **No se elige una ni se corrige
el repo** hasta que alguien lea cada pieza con la marca enfrente:

| Número | Dónde se vio | Estado |
|---|---|---|
| `1-965484-1` | **segundo conector de la misma tarjeta** | **CONFIRMADO de frente**, `conector_te_1-965484-1.jpg`. Lleva además `3.2 B` en relieve |
| `1-967281-1` | primer conector de la tarjeta | **CONFIRMADO de frente**, `conector_te_tarjeta.jpg` |
| `1-962353-1` | conector que entra al módulo Jungheinrich | leído en ángulo. **Provisional** |

**La tarjeta tiene DOS conectores TE, no uno.** Eso resuelve la tensión que quedó
anotada ayer: no eran tres lecturas del mismo número, son piezas distintas. Y el
`1-965484-1` que `docs/15` traía anotado desde hace días **estaba bien** — la duda
que se le puso encima ayer queda levantada.

Lo más probable es que sean **tres conectores distintos de la misma zona**, no tres
lecturas del mismo. Pero eso también es suposición.

> **Lección barata:** el `1-957281-1` se anotó de una foto donde el relieve quedaba
> de canto, y estaba mal. Una foto **de frente y de cerca** de cada marca cuesta dos
> segundos y vale más que una toma general. Dos de los tres ya tienen la suya.

---

## Cómo se nombra acá — convención del proyecto

**Se dice `DB9`, y cuando importa, `DB9 macho` o `DB9 hembra`.** Decisión de maje,
26-sep-2026. Es la que usa todo el mundo en el taller y no hay por qué pelearla.

- **En el montacargas: DB9 hembra.** Se ve en `de9_conector.jpg`
- **El cable de Judit: DB9 macho**

`DE-9` es el nombre formal — la letra del medio es el tamaño de la carcasa, y la
de 9 pines usa carcasa **E**; la **B** es la de 25 pines. Se anota por si aparece
en una hoja de datos, **pero acá no se usa y DB9 no es un error a corregir.**

**El género nunca estuvo en la letra.** `DB`/`DE` es el tamaño de la carcasa;
macho y hembra es otra cosa, aparte. Eso era lo único que valía aclarar, y el
resto del repo siempre dijo bien de qué lado estaba cada cosa.

---

## Decisión — 26-sep-2026 · no se prueba hasta poner el fusible

**maje paró la prueba del puerto.** Correcto, y por la razón correcta: con el pin 6
sin alimentación, un silencio en el barrido **no mediría el puerto, mediría el
fusible que falta**. Correr las 54 combinaciones hoy habría gastado el día para
producir un dato falso.

Esto pasa a ser el bloqueo del hito del puerto, arriba del barrido.

### Antes de poner uno cualquiera

**No se adivina el amperaje.** Un fusible más grande del que va deja de proteger;
uno más chico se abre y manda a buscar una falla que no existe. En orden:

```
1. Preguntarle al chino: ¿por qué se sacó? ¿fue para aislar algo?
2. El valor, de la única fuente que lo sabe: el esquema 99515375
3. Si no aparece: la celda de la etiqueta que corresponde a esa posición,
   una vez cerrado el mapeo por continuidad — no leyéndola de lejos
```

Si hay que elegir a ciegas y ya se descartó que el riel esté en corto, **el valor
más chico de la regleta es el lado seguro del error**: se abre en vez de dejar
pasar. Pero eso es último recurso, no plan.

### Lo que esta visita sí produjo

Sin escuchar un solo byte:

- El DB9 está montado en el distribuidor de fusibles, con su topología trazada
- **Una placa Jungheinrich en el fierro**, que vuelve observación lo que era
  inferencia de manual
- La causa más probable de que el puerto no responda, con su prueba
- Dos números de conector confirmados de frente, y uno del repo validado

**Un viaje que encuentra por qué algo no iba a funcionar vale más que uno que lo
confirma sin saber por qué.**

---

# El puerto no tiene tierra — 30-sep-2026

Día de campo con los dos fusibles de 5 A que consiguió el taller. Manda sobre la
«Decisión — 26-sep-2026» de arriba: la prueba se destrabó, se corrió, y **el fusible
no era la causa**.

## Qué se hizo, en orden

| Paso | Resultado |
|---|---|
| 5 A en **4F15** (la del pin 6), temporal, con cinta | el cable lee **DSR = 1**: el pin 6 ya tiene tensión. El 26-sep leía DSR = 0 |
| `escucha_edr.py --barrido` y `--fijo` | 0 bytes. Igual que sin fusible |
| `lineas_edr.py` (DTR/RTS por fases) | 0 bytes. DSR cae tres veces ~0.2 s, sin patrón claro. Anotado, sin conclusión |
| `saludo_edr.py`, **primera transmisión del proyecto** (decisión de maje) | **eco deformado**: cada saludo vuelve con el mismo largo, el texto nuestro con bits cambiados, peor cuanto más lenta la velocidad. Ninguna respuesta propia |
| Control: el mismo saludo con el cable **al aire**, sin jumper | silencio total a 1200 y a 115200. **El eco sale del lado del equipo, no del cable** |
| 5 A también en **6F9** | el eco sale idéntico. El 6F9 tampoco alimenta el puerto |

## El mapa de pines, medido con batería desconectada

```
Continuidad:
  pin 5 ↔ chasis                NO pita
  negativo de batería ↔ chasis  NO pita   ← normal: la batería va aislada
  pin 1,2,3,4,5,7,8,9 ↔ negativo  NO pita
  pin 6 ↔ negativo              no pita, pero la lectura se mueve: carga normal de un riel

Ohmios, escala 200k:
  pin 6 ↔ pin 2    ~60 kΩ, IGUAL con las puntas invertidas → resistencia, no semiconductor
  pin 6 ↔ pin 3    abierto
  pin 6 ↔ pin 5    abierto
  pin 5 ↔ pin 2    abierto
  pin 5 ↔ pin 3    abierto
  pin 2 ↔ pin 3    abierto
```

### Control: paro de emergencia y llave

El paro de emergencia y la llave cortan circuito, y el paro puede cortar del lado del
negativo. Si hubieran estado abiertos, el negativo del conector no llegaría a la masa
interna y el «no pita» sería de la medición, no del equipo. Se repitió con **batería
desconectada, paro ARRIBA y llave en ON**:

```
pin 1,2,3,4,5,7,8,9 ↔ negativo   NO pita
pin 6 ↔ negativo                 ~216 Ω, estable  ← la carga del riel del 4F15. No es corto
```

**La conclusión sobrevive al control.** Y cuadra: el pin 2 cuelga del pin 6 por 60 kΩ,
así que el pin 2 llega al negativo por ~60 kΩ + 216 Ω — conectado al riel, no a una masa.

Las puntas sí entraban en el DB9 hembra: el pin 6 marcó contra el negativo y el
6 ↔ 2 dio 60 kΩ. Los «abierto» son reales.

## La conclusión

> **Ningún pin del DB9 tiene tierra.** El pin 5, que el cable FTDI usa como masa
> de señal, no está unido a nada. Sin masa común no hay RS-232, esté vivo o no el
> transceptor del otro lado.

Eso explica junto todo lo que se vio desde el 25-sep, sin forzar nada:

| Síntoma | Con «el puerto no tiene tierra» |
|---|---|
| silencio en las 54, en el arranque y navegando el menú | no hay referencia contra la cual recibir |
| eco deformado, peor a baja velocidad | nuestro TX se cuela al RX por conductores sin referencia |
| ningún fusible cambió nada | no era alimentación en esta tarjeta |

**Y queda en tensión con el 18-sep**, que no se borra: ese día el pin 3 daba
**−14.6 V estable** contra chasis. Una línea suelta no da −14.6 V estables. O sea que
**ese día había un transmisor alimentado del otro lado, y hoy no.** Algo cambió entre
las dos fechas, y no hay registro de qué.

## Lo que NO se concluye

- **Que el −14.6 V estuviera bien referido.** Hoy se supo que el chasis no es el
  negativo ni la masa del puerto. Lo medido contra chasis el 18-sep queda como dato
  válido de que *había tensión*, no de *cuánta* respecto a la masa real
- **A dónde iba la masa.** No se adivina. Candidatos, sin elegir: el módulo
  Jungheinrich `KD Medi CO 250K Jr.`, un conector del mismo mazo que quedó suelto, o
  un segundo conector de servicio detrás del display
- **Qué son los 60 kΩ entre 6 y 2.** Una resistencia, pasiva. Para qué, no se sabe

## Dato del mismo mazo

**El display funciona, y va por el mismo mazo que el conector de la tarjeta.** El mazo
no está cortado entero: los conductores del DB9 van a otro destino dentro de él, y es
ese destino el que falta.

## Lo que sigue

```
□ Preguntarle al chino qué se desconectó o se sacó de esa zona después del 18-sep
□ ¿El módulo KD Medi CO 250K Jr. tiene su conector puesto?
□ ¿El display tiene atrás un segundo conector, suelto o vacío?
□ Seguir el mazo desde el conector TE de la tarjeta hasta el otro extremo
□ Esquema 99515375: a qué pin va la masa del puerto
□ Los dos fusibles de 5 A son TEMPORALES. Van de 2 A según la etiqueta
```

## Herramientas nuevas

| Archivo | Qué hace |
|---|---|
| `lineas_edr.py` | levanta DTR y RTS por fases y escucha. **Pone tensión en los pines 4 y 7** |
| `saludo_edr.py` | **transmite** una lista fija de saludos y lecturas CiA 309-3, sin escrituras. `--seco` muestra qué mandaría; `--banco` es el control con jumper; separa **eco deformado** de respuesta real |

**La regla «la primera visita solo se escucha» se levantó el 30-sep por decisión de
maje**, y solo para saludos y lecturas. Las escrituras siguen fuera.

---

# La tabla de fusibles del manual — 30-sep-2026

`manual_fusibles_p142.jpg` y `manual_fusibles_p143.jpg`. Páginas 142 y 143 de un
**manual impreso** que tiene maje, pie de página `04.17 US_ES`. **Cuál manual es
exactamente no está anotado todavía** — anotarlo.

Trae el **dibujo de la tarjeta**: los fusibles numerados **114 a 127 de izquierda a
derecha**, y el DB9 abajo a la izquierda. Es la misma tarjeta de las fotos.

## La tabla, transcrita

Los de la tarjeta (columna «caja de fusibles miniatura» marcada):

| Elem. | Fusible | Qué protege | A |
|---|---|---|---|
| 114 | F17 | equipo de radiotransmisión, **dispositivo de transmisión de datos** | 5 |
| 115 | **4F15** | **autorización de acceso** | **2** |
| 116 | 5F3 | control de la lámpara de marcha atrás | 2 |
| 117 | F4 | contactor del control maestro | 7.5 |
| 118 | 5F2 | control del convertidor CC-CC | 7.5 |
| 119 | 3F11 | **control de dirección de la rueda de tracción** | 2 |
| 120 | 4F9 | sistema electrónico de fusibles de control | 2 |
| 121 | 5F7 | opciones del tejadillo protector | 2 |
| 122 | 3F14 | dirección de rueda de carga RH | 2 |
| 123 | **6F9** | **cámara** | **2** |
| 124 | 1F13 | conducción MFC / control de frenado | 7.5 |
| 125 | 4F10 | ventilador | 2 |
| 126 | 2F18 | sistema hidráulico MFC | 10 |
| 127 | F27 | controlador de carga en marcha | 5 |

Y los grandes, fuera de la tarjeta:

| Elem. | Fusible | Qué protege | A |
|---|---|---|---|
| 108 | 3F6 | motor de dirección de la rueda de tracción (UL EE) | 50 |
| 109 | 3F6 | motor de dirección de la rueda de tracción (UL E) | 50 |
| 110 | F1 | control maestro | 30 |
| 111 | 4F11 | ordenador de a bordo | 2 |
| 112 | 2F1 | motor de la bomba | 800 |
| 113 | 1F1 | motor de tracción | 500 |

## Lo que esto cierra

### 1 · La etiqueta SÍ está alineada con la regleta

El dibujo numera las posiciones en el mismo orden que la etiqueta. El 26-sep quedaron
dos lecturas abiertas sobre el «10 A donde la etiqueta pide 2 A»:

| Decía | Es | Qué lo tumbó |
|---|---|---|
| «o la etiqueta no está alineada, o hay un fusible que no corresponde — no se elige» | **la etiqueta está alineada. Hay fusibles que no corresponden** | el dibujo del manual, 114 a 127 en orden |

### 2 · Lo que tiene puesto la tarjeta contra lo que pide el manual

Con la fila de fusibles leída el 26-sep, antes de poner los temporales:

| Elem. | Fusible | Pide | Tenía | |
|---|---|---|---|---|
| 114 | F17 | 5 | 5 | ✓ |
| 115 | 4F15 | 2 | **vacío** | faltaba |
| 116 | 5F3 | 2 | **10** | ✗ |
| 117 | F4 | 7.5 | 7.5 | ✓ |
| 118 | 5F2 | 7.5 | 7.5 | ✓ |
| 119 | 3F11 | 2 | **10** | ✗ |
| 120 | 4F9 | 2 | 2 | ✓ |
| 121 | 5F7 | 2 | 2 | ✓ |
| 122 | 3F14 | 2 | 2 | ✓ |
| 123 | 6F9 | 2 | **vacío** | faltaba |
| 124 | 1F13 | 7.5 | 7.5 | ✓ |
| 125 | 4F10 | 2 | **10** | ✗ |
| 126 | 2F18 | 10 | 10 | ✓ |
| 127 | F27 | 5 | 5 | ✓ |

**Tres posiciones de 2 A tienen fusible de 10 A.** Un fusible cinco veces más grande
del que pide el circuito deja de protegerlo: si ese circuito tiene un corto, se quema
el cable o la tarjeta antes que el fusible.

La que más importa es la **119, `3F11`, el control de la dirección.** Es justo el
circuito que el teleop va a tocar (`docs/10`, plan 3).

> **Lectura por color, no en mano.** Los «10» se leyeron en fotos: en fusibles
> miniatura el rojo es 10 A y el gris es 2 A, por norma. Es confiable pero no es
> leerlo con el fusible en la mano. **Confirmar los tres antes de cambiar nada.** Y no
> se cambian sin el chino: alguien los puso, y conviene saber por qué.

### 3 · Los fusibles que se pusieron el 30-sep son temporales, y ahora se sabe de cuánto

Los dos de **5 A** van en posiciones que piden **2 A**: 4F15 y 6F9. Ya estaba anotado
como temporal; el manual lo confirma. **Van de 2 A.**

## Lo que abre

### El pin 6 cuelga del fusible de «autorización de acceso»

El 26-sep maje trazó que el fusible de la posición 2 alimenta el pin 6 del DB9. La
posición 2 es el **115, `4F15`, «autorización de acceso»**. Y la posición 1, justo al
lado del conector, es el **`F17`, «dispositivo de transmisión de datos»**.

Eso sugiere, **sin concluirlo**, que el DB9 es el punto de conexión de un **accesorio
de control de acceso o de transmisión de datos** — un lector de clave o tarjeta, o un
equipo de telemetría — que toma alimentación del pin 6.

Cuadra con dos cosas medidas:

- **El pin 6 es alimentación**, no señal. Eso ya estaba
- **El puerto no tiene tierra propia.** Si el accesorio trae su masa por su propio
  mazo, el DB9 no necesita tenerla. Y si el accesorio ya no está, falta justo eso

Queda en tensión con lo que sí se sabe: **el chino entraba con Judit por ese mismo
DB9.** Las dos cosas pueden ser ciertas a la vez — un puerto de servicio que también
alimenta un accesorio — y no se elige ninguna todavía. Se suma como **candidato
nuevo** a la lista de «a dónde iba la masa»:

```
□ un accesorio de autorización de acceso o de transmisión de datos que ya no está
□ el módulo Jungheinrich KD Medi CO 250K Jr.
□ un conector del mismo mazo que quedó suelto
□ un segundo conector de servicio detrás del display
```

**Pregunta directa para el chino:** ¿este equipo tenía lector de clave, de tarjeta, o
algún aparato de telemetría conectado ahí?

### El 6F9 es el de la cámara

El otro fusible que faltaba, **123, `6F9`**, es el de la **cámara**. El 30-sep se probó
que no alimenta el puerto: el eco salió idéntico con y sin él. Queda anotado qué es.
