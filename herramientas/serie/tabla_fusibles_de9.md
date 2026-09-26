# La tabla de fusibles y el DE-9 — foto de campo

**Fotos:** tomadas el 26-sep-2026 en el taller Las Palmas, sobre el EDR18N2 fuera
de operación.

| Archivo | Qué muestra |
|---|---|
| `tabla_fusibles_de9.jpg` | vista general: el DE-9, la regleta completa y la etiqueta |
| `tabla_fusibles_de9_detalle.jpg` | el extremo derecho de cerca: cola de la etiqueta y la serigrafía de la tarjeta |

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
