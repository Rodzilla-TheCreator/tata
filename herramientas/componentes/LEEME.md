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
