# La tabla de fusibles y el DE-9 — foto de campo

**Foto:** `tabla_fusibles_de9.jpg` · tomada el 26-sep-2026 en el taller Las Palmas,
sobre el EDR18N2 fuera de operación.

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

Se lee de corrido, rotada 90°. Transcripción literal de lo legible:

```
F17  4F15  5F3  F4   5F2   3F11  4F9  5F7  3F14  6F9   1F13  4F10  2F18  F27
5A   2A    2A   7.5A 7.5A  2A    2A   2A   2A    7.5A  2A    10A   5A    ?
```

El último valor queda cortado por el borde de la foto. **Verificar el de `F27`.**

**Todo es de 2 a 10 A.** Eso es circuito de control, no de potencia — coherente
con que el DE-9 viva en esta misma placa y cuelgue del bus de control, que es uno
de los argumentos de `docs/15` para creer que es el puerto de servicio.

### Los fusibles puestos, de arriba hacia abajo en la foto

```
5 · VACÍO · 10 · 7.5 · 7.5 · 10 · 2 · 2 · 2 · VACÍO · 7.5 · 10 · 10 · 5
```

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
□ Foto del borde derecho de la etiqueta, para el valor de F27
□ ¿Hay número de parte serigrafiado en la tarjeta verde?
```

El reverso es el que decide la pregunta cara: si el mazo llega al controlador de
tracción, el DE-9 es el puerto de servicio y se acabó la duda. Ver `docs/15`.
