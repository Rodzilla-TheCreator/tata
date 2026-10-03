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
  alimentación** del multipiloto. Falta anotar si la masa fue chasis o negativo de batería
