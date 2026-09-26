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

Marcado en el cuerpo, de esta foto:

```
ASSY  1-957281-1
>PBT/ASA-GF30<          ← el material del plástico, no un número de parte
```

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

| Número | Dónde se vio | Fuente |
|---|---|---|
| `1-965484-1` | anotado como «el arnés del DE-9» | `docs/15`, origen no re-verificado |
| `1-962353-1` | conector que entra al módulo Jungheinrich | `modulo_jungheinrich.jpg` |
| `1-957281-1` | conector de la tarjeta de fusibles | `tarjeta_fusibles_reverso.jpg` |

Lo más probable es que sean **tres conectores distintos de la misma zona**, no tres
lecturas del mismo. Pero eso también es suposición.

---

## Nota de nombres — DE-9, DB9, macho y hembra

Para no perder tiempo en esto nunca más:

- **DE-9 es el nombre correcto.** La letra del medio es el tamaño de la carcasa, y
  la de 9 pines usa carcasa **E**. «DB9» es el error común y universal: la carcasa
  **B** es la de 25 pines. Si alguien dice DB9, se entiende igual y no pasa nada
- **En el montacargas es HEMBRA** — tiene los huequitos. Se ve en `de9_conector.jpg`
- **En el cable de Judit es MACHO** — tiene los pines
- Regla para no pensarlo: **el que entrega, entrega pines.**

El nombre no cambia una sola medición. Lo que importa es de qué lado está cada
cosa, y eso está bien en todo el repo.
