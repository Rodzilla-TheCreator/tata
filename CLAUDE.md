# TaTa — contexto para Claude Code

Kit de retrofit que vuelve autónomos, por etapas, los montacargas que un almacén ya opera.
Proyecto interno de **Montasa** (distribuidor de montacargas en San Pedro Sula, Honduras).

**Los detalles completos están en `docs/`.** Este archivo es el mapa; ahí está el territorio.

| Documento | Qué contiene |
|---|---|
| `docs/01-hallazgos-rethink.md` | Lo que encontramos en el almacén del cliente |
| `docs/02-maquina-y-geometria.md` | El EDR18N2 y si cabe el giro en 3 m |
| `docs/03-lidar-y-localizacion.md` | **Localizan las cámaras con ArUco. El LiDAR no navega** |
| `docs/04-seguridad-y-normativa.md` | Por qué la capa de seguridad va aparte |
| `docs/05-producto-y-negocio.md` | Escala de madurez, costos, retorno |
| `docs/06-simuladores.md` | Los dos simuladores y cómo se usan |
| `docs/07-estado-y-siguientes-pasos.md` | Qué falta, en orden, con puertas de decisión |
| `docs/08-setup-git-agente.md` | Cómo dejar la máquina lista para empujar y cómo trabajar con git |
| `docs/09-briefing-secuencia.md` | La simulación de secuencia: qué es y qué falta |
| `docs/10-intervencion-electrica.md` | Los tres planes de intervención: freno, tracción, dirección. **Y el watchdog de 200 ms** |
| `docs/11-plan-de-diagnostico.md` | **La visita de medición. Va ANTES del doc 10** |
| `docs/12-medicion-de-la-sombra.md` | **Una hora con flexómetro y papel. Cierra el bloqueo 1** |
| `docs/13-timeline-antes-de-la-semana.md` | **Todo lo que va antes, por dependencia. El bloque 0 corre desde hoy** |
| `docs/14-maquinas-y-entorno.md` | **i3, maquinon y superspeed: cómo están armadas y las trampas** |
| `docs/15-viaje-al-taller.md` | **El plan del viaje, la placa de datos y todo lo del puerto de servicio** |
| `docs/16-manual-de-servicio.md` | **El manual de servicio: el equipo es un Jungheinrich, el bus es CANopen, y existe el APM+** |
| `docs/17-hito-teleop.md` | **El plan de acción del hito del teleop, por bloques. El bloque 1 se puede empezar hoy** |

| Carpeta | Qué contiene |
|---|---|
| `herramientas/serie/` | **Los sketches y el banco de pruebas del puerto de servicio.** Ver la sección del DE-9 |
| `herramientas/can/` | **La cadena de escucha CAN.** `protoboard_can.svg` es el plano de armado, cable por cable. `armado_can.svg` tiene los módulos y la tabla; los `cadena_can_*.svg` son los diagramas de bloques |
| `herramientas/Codigos de error reach color_*.pdf` | **El manual de servicio completo, 259 pág.** Leerlo con `pdftotext -layout`. Ver `docs/16` |
| `analisis/` | El cálculo detrás de casi todo lo de `docs/`. Si vas a contradecir un número, corré el script |

> **Aviso a quien lea `docs/01` a `docs/07`:** se escribieron antes de la medición de campo
> del 24-ago-2026 y varios números quedaron desmentidos. La sección «Corregido en campo» de
> abajo manda sobre ellos. Todavía no se reescribieron uno por uno.

---

## Lo mínimo para no meter la pata

**Máquina objetivo:** Mitsubishi **EDR18N2**, reach truck pantográfico de operador parado.
Entre ejes 1.562, radio de giro 1.797, pantógrafo 0.61, desplazador ±0.12.
Velocidad de trabajo **7.9 km/h**, no los 12 de catálogo. Sobre de velocidad: **1.5 m/s**.

**El pasillo mide 3.00 m** y no cambia. Es dato de campo, no de plano.

**La unidad de carga es un IBC de 1000 L**, jaula galvanizada sobre base de tarima:
**1200 × 1000 × 1160 mm**. En el rack presenta su cara de **1.00 m al pasillo** y entra
**1.20 m al fondo** — lo fija la bahía de 2.35 m, donde entran dos con 35 cm sobrantes.

**Se dice ArUco.** No "marcadores", no "etiquetas", no "AprilTag". Es el término del proyecto
y viene de Botoni, donde el equipo definió cuáles y dónde iban.

**El LiDAR no navega.** Localizan **dos cámaras USB con ArUco** más la odometría. Al LiDAR le
queda un solo trabajo — ver lo que no debería estar ahí — y no es redundancia: el mapa acierta
con los racks y se equivoca todos los días con lo que hay en el pasillo. Detalle en `docs/03`.

**La seguridad va aparte por norma**, no por recorte. ISO 3691-4 exige que la capa
certificada esté aislada de la navegación.

**Nunca llamar "freno automático" a nada en hardware de nivel Ingenio.** Es asistencia de
frenado en modo demostración, teleoperado con un dedo sobre un paro físico.

**El watchdog de 200 ms lo cuenta el ESP32, nunca la Jetson.** Linux no garantiza tiempo. Si
pasan 200 ms sin latido, el ESP32 corta el hombre-presente y cae el freno de resorte. El rearme
es **manual**. Y **no es la capa de seguridad certificada** — es supervisión de disponibilidad.
Detalle en `docs/10`.

**Dónde se trabaja: el taller Las Palmas de Montasa, sobre un EDR18N2 que está fuera de
operación.** Montasa no pierde dinero prestándolo — ya estaba en cero. Eso baja el costo de
equivocarse, pero **no cambia las reglas cuando se toque el equipo del cliente.**

**El Aula** es el laboratorio que se va a construir ahí — un pasillo con estantes, dentro del
taller. El nombre honra al mismo maestro que le da nombre al proyecto. **Va después del hito
del teleop**, no antes.

**Pasillo 0** es el pasillo de adentro de El Aula, y es **variable de operación**: los sectores
reales del cliente son A y B, y este es el que va antes. Nada entra al pasillo A sin haber
pasado el Pasillo 0.

**Piezas y ingeniería son cosas distintas.** El NRE es descubrir qué señal es cada cable, y
eso se paga una vez para todo el modelo, no por unidad.

---

## Corregido en campo — 24-ago-2026

Todo esto contradice lo que estaba escrito antes. **Manda esta sección.**

### Geometría del equipo

| Cota | Decía | Es | Cómo se supo |
|---|---|---|---|
| `XPIV` culo → eje de ruedas de carga | 1.91 | **1.50** | con 1.91 la esquina trasera queda más lejos del centro de giro que el propio radio de ficha (1.797). Imposible |
| Ancho | 1.054 | **1.315** en el punto más ancho | medido. Los 1.054 eran el capó |
| Silueta | rectángulo | **forma de L** | el 1.315 son las **patas portantes**, cortas y adelante. El capó atrás mide ~1.065 |
| `FLEN` uña útil | 1.21 | **1.20** | punta a torre |

`XPIV = 1.50` da δmax **78°**, coherente con la ficha y con el 76° que ya usaba el visor web
por dos caminos independientes. **Sigue siendo derivado, no medido.**

### El giro

**La carga nunca es la restricción.** El IBC mide 1.00 de ancho y el equipo 1.315: retraído
queda *dentro* de la silueta. En todas las corridas el punto que traba fue el chasis, jamás
el cubo. **Girar cargado es igual que girar vacío**, tal como se observó en campo.

Eso deja sin efecto todo lo que se había planteado de sideshift activo durante el arco y de
maniobra multipunto por culpa de la carga. Eran problemas inventados por un modelo malo.

**El planificador correcto es Hybrid A\***, no un barrido de arcos. El equipo es no holónomo
con radio mínimo; los caminos óptimos son curvas de Reeds-Shepp. Un PuzzleBot de eje
diferencial gira en el sitio y por eso planificar ahí es trivial — acá no. Está en
`analisis/planificador_giro.py`.

Resultado con la silueta corregida, girando desde el **carril del rack opuesto**:

| Desde el rack opuesto | Completa 90° | Cambios de sentido |
|---|---|---|
| 75 cm — la línea que usa el operador | sí | **1** |
| 90 a 150 cm | sí | 0 |

La maniobra de dos tiempos que hace el operador sale sola del planificador, sin programarla.
La línea recomendada es **85 cm**: sigue en un movimiento y deja 20 cm de holgura en vez de
los 10 justos.

### El rack

De las medidas de maje: luz de 2.43 m en N1 con dos cubos apilados, plataforma del 2° a
2.545, plataforma del 3° a 1.495 del techo de N1.

```
grosor de plataforma      0.115 m
paso entre plataformas    1.380 m   (del 2° en adelante)
luz libre por nivel       1.265 m
altura del cubo           1.160 m   ← DEDUCIDA, no medida
```

La altura del cubo sale del propio dato: con 1.20 quedarían 3 cm de juego en N1 y nadie
estiba así; con 1.16 quedan 11. Es el IBC estándar.

**Alturas de uña**, medidas al fondo de la uña. Hueco del IBC 0.32 × 0.08, uña 0.036 en el
talón → ventana vertical de 0.044, centro en **0.022**. Agarre a **+0.06**, que es lo que
sube el operador.

| Posición | Base | Entrada | Agarre |
|---|---|---|---|
| N1-A al piso | 0.000 | 0.022 | 0.082 |
| N1-B sobre cubo | 1.160 | 1.182 | 1.242 |
| N2 | 2.545 | 2.567 | 2.627 |
| N3 | 3.925 | 3.947 | 4.007 |
| N4 | 5.305 | 5.327 | 5.387 |
| N5 | 6.685 | 6.707 | 6.767 |

**Elevación necesaria hasta N5: 6.77 m.** Ese es el `h3` que se le pide a Fabrizio.

### Los pasillos que dábamos por perdidos

Los dos pasillos que usa la secuencia separan filas por **4.10 y 4.20 m entre centros**, o
sea **3.00 y 3.10 m libres** con racks de 1.10 de fondo. El análisis viejo los descartó
porque comparaba contra el `Ast` de 3.82 del Baoli contrabalanceado — máquina que ya no es
la nuestra. Con el reach truck que el cliente ya opera, entran.

Su topología calza exacto con la simulación de secuencia sin que nadie la forzara:

```
-817.1 │ pasillo 3.10 │ -812.9 ‖ -811.5 │ pasillo 3.00 │ -807.4
 rojo  │      A       │ amarillo‖verde  │      B       │  azul
```

### Localización

**Lo que restringe el eje del pasillo es la pared del fondo, no los montantes del rack.**
Con las tapas a la vista el relieve casi no importa: de 15 cm a 0 cm el sigma longitudinal
apenas va de 0.14 a 0.18 cm. Sin tapas y con relieve bajo, la matriz de información se
vuelve **singular**.

`analisis/analisis_degeneracion.py` mete paredes a 4.5 m de cada extremo incluso en el caso
"abierto", y por eso **no reproduce la tabla que quedó escrita en `docs/03`**.

**El precipicio está entre 15 y 12 m de alcance efectivo.** Arriba de 15 m no pasa nada con
ningún relieve.

> **Superado el 27-ago-2026.** Todo este análisis contestaba «si el LiDAR localizara, qué haría
> falta». Se decidió que **el LiDAR no localiza**, así que la pregunta salió del alcance. Con
> ella se va también la recomendación de blancos retrorreflectivos: son otro canal de sensado,
> no un sustituto del ArUco, y se tapan igual de fácil. Se archiva, no se borra — vuelve a la
> mesa sólo si la oclusión de ArUco resulta frecuente en campo. Ver `docs/03`.

### Eléctrica

- El **EDR es EPS** (steer-by-wire): la dirección se puede interceptar eléctricamente.
  Los contrabalanceados de renta son **hidráulicos** y ahí no hay nada que interceptar.
- **El EDR no tiene pedal de acelerador.** Hay pedal de **hombre-presente** que habilita
  pero no dosifica; la velocidad sale de un **mando de mano**.
- El freno de servicio es **regenerativo por el controlador**. La capa que sí frena siempre
  es cortar el hombre-presente con un relé y dejar caer el freno electromagnético de resorte.
- Los controladores esperan **doble señal Hall redundante**. Inyectar una sola dispara falla
  y bloquea la marcha. De ahí que el DAC sea de cuatro canales.
- Mapeo del control: **RT y LT dosifican, B/O alterna sentido**, y el cambio de sentido solo
  se acepta con ambos gatillos en cero y el equipo detenido.

### Isaac Sim

| Decía | Es |
|---|---|
| ~30 GB | zip de **10.6 GB** |
| driver 535+ | **595.97** en Windows |
| RTX con 8 GB VRAM mínimo | **RTX 4080 · 16 GB VRAM · 32 GB RAM** |

La máquina de maje tiene 8 GB — la mitad del mínimo. **Correr headless y un LiDAR por
corrida, nunca varios simultáneos.** Se va a instalar en **Linux**; la descarga en Windows
se abortó y se borró.

Bug corregido en `sim-isaac/`: las 513 `PhysicsCollisionAPI` estaban aplicadas al `Xform` y
no al Gprim. UsdPhysics construye el collider a partir de la geometría, así que **piso, muros
y racks eran atravesables**. No afectaba al LiDAR RTX, que traza geometría de render.

---

## Corregido y aprendido — 18-sep-2026 · el taller y el puerto

Sesión larga. Dos frentes: se **midió la sombra** en un EDR parado en el taller de
Montasa Las Palmas, y se abrió el **puerto de servicio DE-9**. Manda sobre lo anterior.

### La sombra, medida — Las Palmas

Se midió **un solo lado** y se asumió simetría. No se pudo mover el equipo ni marcar el
piso. Estaciones tomadas desde el culo hacia la torre.

| Cota | Decía (repo) | Se midió | Veredicto |
|---|---|---|---|
| `W_RESTO` ancho del capó | 1.065 | **1.065** | confirmado |
| escalón capó → patas | 0.25 | **0.25** | confirmado |
| `L_ANCHO` largo del tramo ancho | 0.20 | **0.48** | **desmentido**, más del doble |
| `W_MAX` ancho pata a pata | 1.315 | *no se midió* | sigue siendo del repo, nunca verificado |

**Lo que ancla toda la escala lateral es `W_MAX`, y sigue sin medirse.** Con un solo lado
medido, la simetría da forma pero no da ancho. Esa medida es la número uno del próximo viaje.

**Cota dura que salió de la ficha más el ancho:**

```
XPIV < sqrt(Wa² − (W/2)²) = sqrt(1.797² − 0.6575²) = 1.6724 m
```

Si `XPIV` fuera mayor, la esquina trasera quedaría más lejos del centro de giro que el propio
radio de ficha. Imposible, igual que el 1.91 que se tumbó en agosto.

**Y hay una contradicción viva, sin resolver:** la rueda de carga cayó en la estación 282; con
`WB = 1.562` eso implica `XPIV = 1.862`, que viola la cota de arriba. Una de tres está mal:
el `Wa = 1.797` de ficha, la identificación de esa rueda, o la alineación de la cinta.
**No se resolvió. Es la pregunta que va con flexómetro al próximo viaje.**

### El giro, con la silueta medida

Se corrió `analisis/planificador_giro.py` con el `L_ANCHO = 0.48` medido, barriendo `XPIV`
entre 1.30 y 1.60 para cubrir la incertidumbre:

| | Resultado |
|---|---|
| Ventana de carriles para 90° | **75–150 cm, estable en todo el rango de `XPIV`** |

**La forma domina al pivote.** Eso baja la urgencia del bloqueo 1 *para factibilidad* — el
giro entra sea cual sea el `XPIV` dentro del rango. No la baja para **control fino**: el
controlador sí necesita el número real.

**El 180° en el pasillo:**

| Caso | Ancho barrido | ¿Entra en 3.00 m? |
|---|---|---|
| Solo chasis, peor caso | 2.31 m | sí, 69 cm de sobra |
| Chasis **+ uñas**, a 75°/105° | 3.14 m | **no, faltan 14 cm** |

Lo que lo mata es el **largo**, no el ancho de las uñas. Conclusión: el 180° en pasillo **no
es confiable, y tampoco hace falta** — el reach truck maneja igual en ambos sentidos.

> **Defecto conocido, anotado y NO corregido:** `silueta()` en `planificador_giro.py`
> **no modela las uñas**. Abarca ~2.02 m (culo a cara de torre) cuando el equipo real mide
> 2.91 m con uñas. Por eso sus resultados de 90° y 180° son **solo chasis**. El 3.14 de
> arriba se calculó aparte, por geometría directa, no con el planificador.

---

## El puerto de servicio DE-9

El chino encontró un **DE-9 hembra en la tabla de fusibles** del EDR. Dice que por ahí
controlaba el equipo con **Judit**: veía sensores y movía parámetros. Se le venció la licencia.
Ese es el camino que se tomó.

### Medido, con multímetro, en el equipo

```
Óhmetro, apagado, sin adaptador:
  pin 2 ↔ pin 7   ABIERTO       → no es un bus CAN *terminado*

Voltímetro DC, encendido, negra a chasis, sin adaptador:
  1, 4, 5, 7, 9   0 V firme
  6               +0.1 V   flotante
  8               −0.1 V   flotante
  2               −5 a −12 V     VARIABLE
  3               −14.6 V estable, luego −5 a −9 V   VARIABLE
```

**Pines 2 y 3 vivos, a niveles RS-232, con actividad.** Un puerto muerto no transmite. Es la
evidencia más fuerte que ha producido cualquier punto de entrada en esta investigación.

**Por qué no es CAN:** por el **−14.6 V**, no por el 2↔7 abierto. Un stub de diagnóstico
normalmente **no lleva terminador**, así que el 2↔7 abierto no descarta nada. CAN diferencial
nunca llega a −14.6 V. *(Esto corrige un razonamiento previo de esta misma sesión.)*

**Por qué el multímetro da valores variables:** un multímetro DC promedia. Una línea que está
transmitiendo tiene su promedio corrido hacia cero desde el nivel de marca (−5 a −15 V).
El −14.6 V estable es la línea **en reposo**; el −5/−9 V es la misma línea **hablando**.

### Descartado, y por qué

| Hipótesis | Qué la tumbó |
|---|---|
| Bus CAN terminado | −14.6 V en pin 3 |
| Adaptador roto (CH340) | **loopback 37/37 perfecto** en banco. Está bueno |
| VGA / video | 9 pines en 2 filas (5+4), no 15 en 3 |

### La causa del silencio, y cómo se arregló

El cable USB-serie es **DTE**. El puerto del equipo, si es de servicio, también es **DTE**.
DTE↔DTE **directo no habla**: TX contra TX, RX contra RX. Hace falta un **null-modem**, que
cruza 2↔3.

Se compró. **Al null-modem le falta el pin 9 del lado macho — no importa**: el pin 9 es RI,
no se usa en este enlace.

### Lo que NUNCA se probó de verdad, en el equipo

- Cualquier velocidad **arriba de 14400**
- Cualquier encuadre que **no sea 8N1**

El barrido de `escucha_edr.ino` cubre 9 velocidades × 6 encuadres = **54 combinaciones**,
~3 min por pasada. Eso es lo que va al próximo viaje.

### El cable de fábrica que apareció en el taller

Un cable ethernet-a-DB9, 4 conductores, mapeo por continuidad:

```
amarillo → pin 6      café   → pin 9
naranja  → pin 2      rojo   → pin 7
```

Eso es **exactamente el pinout CiA-303 de CAN sobre DE-9** (2=CAN_L, 6=GND, 7=CAN_H, 9=V+).
**Su procedencia no está confirmada** — puede no ser de esta máquina. Es dato en tensión con
lo medido, **no una conclusión**. Se conserva. Si mañana el DE-9 resulta ser CAN después de
todo, este cable es la pista que lo anticipó.

### El cable de solo-escucha — especificación correcta

Para escuchar sin transmitir nunca:

```
equipo pin 3  →  adaptador pin 2      (su TX a nuestro RX)
equipo pin 5  →  adaptador pin 5      (tierra de señal)
adaptador pin 3   SIN CONECTAR        (nuestro TX al aire)
```

Una versión anterior decía "solo pines 2 y 5" — **está mal**, eso deja nuestro RX contra su RX.

### Judit, y de dónde salen los manuales

**Judit = JETI JUDIT**, herramienta de concesionario **Jungheinrich**, que entra por la
**Incado Box** con cable de 9 pines. Parece contradicción con una máquina Mitsubishi, y no lo
es: **MCFA distribuye Mitsubishi, Cat y Jungheinrich**. El chino tenía Judit legítimamente.
*(Esto le dio la razón al chino contra una objeción mía. Ver la regla de abajo.)*

| Manual | Qué es | Cómo se consigue |
|---|---|---|
| O&M ESR20N2 · ESR23N2 · **EDR18N2**, 01/2022 | operador | MCF Parts Client vía Montasa |
| **WENBM8550-01** | taller: códigos de falla y parámetros | igual, y es el que de verdad sirve |

**Pendientes los dos.** Ninguno se ha conseguido.

### ¿Es el DE-9 el puerto correcto?

**Sí, hasta donde se sabe.** Lo sostienen: actividad RS-232 real en 2 y 3; el testimonio del
chino; Judit entrando por 9 pines; y su ubicación en la tabla de fusibles, colgado del bus de
control y no de un periférico.

**La única sombra:** el único conector de servicio Mitsubishi/Cat documentado públicamente es
el **GSE**, un plug **cuadrado** bajo el portavasos — y eso en montacargas de combustión, no en
reach trucks. Ningún documento público muestra un DE-9 en un ESR/EDR.

**Lo que lo cierra, barato, con los paneles ya abiertos:** seguir **a dónde va el mazo del
DE-9**. El arnés es **TE 1-965484-1** (AMP Timer, automotriz wire-to-device). Si llega al
controlador de tracción, el DE-9 es el puerto de servicio y se acabó. Si llega solo al
tablero, es un puerto de display y el bus bueno está más adentro. Candidatos de reserva, en
orden: detrás del display; el puerto propio del controlador de tracción (ZAPI o Curtis, cada
uno con su consola); el puerto del cargador.

### Reglas del puerto — no negociables

- **La primera visita solo se escucha. Nunca se transmite.**
- **Jumper fuera antes de conectar al equipo.** Puentear pin 2 con pin 3 en el equipo es
  cortocircuitar dos líneas manejadas por el controlador.
- No se corta ni un cable. Es equipo de un cliente en un taller ajeno. **Nada irreversible.**

---

## El instrumento, validado antes de viajar

Primer instrumento de todo este hilo que se verificó **antes** de usarlo en el equipo.

**Cadena:** ESP32-WROOM → módulo **T132 (SP3232)** → null-modem → DB9. El SP3232 se alimenta a
**3.3 V, nunca 5 V**: su swing RS-232 sigue al VCC. UART2 en **GPIO16 (RX) / GPIO17 (TX)** para
dejar libre el USB.

| Prueba | Resultado |
|---|---|
| `prueba_cadena.ino`, 6 casos (1200/9600/38400/115200 8N1, más 9600 8E1 y 7E1) | **6 de 6 eco perfecto** |
| Control de falsación: se quita el puente | **SIN ECO en los 6** |

Los dos controles pasaron. La cadena mide lo que dice medir.

### Herramientas nuevas en el repo

| Archivo | Qué hace |
|---|---|
| `herramientas/serie/prueba_cadena.ino` | valida la cadena ESP32+T132 contra sí misma, con auto-reintento RX/TX cruzados |
| `herramientas/serie/escucha_edr.ino` | barrido pasivo 9 bauds × 6 encuadres. Tiene `MODO_FIJO` para clavar una combinación |
| `herramientas/serie/probador.py` | banco tkinter azul retro para calificar un cable USB-serie: velocidad, paridad, loopback |

> **Defecto conocido de `probador.py`:** el veredicto «ESTE SIRVE» solo exige velocidad y
> paridad, y ninguna de esas dos toca los pines del DB9. Un cable puede aprobar y fallar
> loopback completo — **pasó exactamente eso** con el CH340 de reemplazo. **Solo el loopback
> prueba que el conector pasa datos.** Arreglar el veredicto o leerlo con esa advertencia.


## El manual de servicio — 18-sep-2026

Apareció el **manual de servicio Jungheinrich completo**, 259 páginas, traducido a máquina por
Google. Está en `herramientas/`. **Todo el detalle en `docs/16`.** Lo que manda desde ya:

**El EDR18N2 es un Jungheinrich ETR 335d/340/345 con placa de Mitsubishi.** La portada dice
ESR20N2/ESR23N2/EDR18N2 y el cuerpo habla de ETR. Son la misma máquina. Por eso el chino tenía
Judit: **es la herramienta nativa del equipo**, no una prestada de otra marca. Y por eso toda la
documentación Jungheinrich de la familia ETR aplica.

**El bus es CANopen a 250 kbaud.** Tabla «Sistemas de BUS utilizados», sin ambigüedad.

**El «PC de servicio» es el nodo CAN 30.** Judit habla CANopen, no serie.

**Existe el nodo 31, APM+, «Interfaz de automatización (PLC)».** El fabricante reservó un ID de
nodo para que algo externo maneje el equipo por el bus. **Eso no estaba en ningún supuesto del
proyecto** — todo `docs/10` se escribió asumiendo que la única entrada era cortar cables. No es
una solución todavía: hay que confirmar si está implementado acá y si su protocolo se puede
obtener. Pero la pregunta dejó de ser especulación y **tiene nombre**.

**Los parámetros vienen con su índice del diccionario de objetos CANopen** (`0x2100`, `0x2414`,
…), que es exactamente lo que un maestro CANopen necesita para leerlos y escribirlos por SDO.

### Lo que desmiente

| Decía | Es | Qué lo tumbó |
|---|---|---|
| El control Obed: **2.6 vueltas** de volante tope a tope | parámetro `0x2414`, fábrica **5.5**, rango 4–8 | El simulador tiene el timón **más del doble de rápido** que el real. Verificar contando a mano |
| Los 7.9 km/h de campo contradicen los 12 de catálogo | **no se contradicen.** 7.9 ≈ programa 1 (fábrica 9), 12.9 = programa 3 | `0x2108`/`0x2128` |
| Cargado y vacío se mueven igual | **solo en geometría de giro.** La velocidad se recorta por **presión hidráulica** entre 44 y 116 bar | Parámetros de desarrollo |
| «Es imposible que sea CAN» (por el −14.6 V) | **abierto otra vez** | El PC de servicio es nodo CANopen |

### La tensión con el DE-9, y la medición que la resuelve

El manual dice CANopen. La medición dijo −14.6 V, que CAN no da. **No se resuelve adivinando ni
tirando una de las dos.** La hipótesis más barata: **el chasis no es el negativo de batería**, y
todo lo medido con la punta negra a chasis está corrido.

**Va antes que cualquier otra cosa en el equipo, y son cinco minutos:**

```
1.  negativo de batería  ↔  chasis        ¿mismo punto, o hay voltaje entre ellos?
2.  pin 6  ↔  negativo de batería
3.  pin 3  ↔  negativo de batería         ← el −14.6 V, bien referido
4.  pin 2 y pin 7  ↔  negativo de batería ← CAN_L y CAN_H en reposo ≈ 2.5 V
```

Si 2 y 7 dan ~2.5 V contra el negativo de batería, **es CAN y se acabó la duda.**

Y el **cable ethernet-a-DB9 del taller sube de categoría**: mapeaba a pines 2/6/7/9, que es
**CiA-303 exacto**. Con el bus confirmado como CANopen, ahora parece justo lo que aparenta ser.

**Si resulta CAN, el ESP32 solo no basta:** hace falta un transceptor (SN65HVD230 con TWAI, o
MCP2515). Se pone en **modo listen-only**, que no manda ni los bits de reconocimiento. La regla
no cambia: **solo se escucha**.

### Lo que el manual no trae

**Los esquemas eléctricos no están.** Solo su número de dibujo. **Pedir el `99515375`**
(eléctrico) y el `99520170` (hidráulico) por Montasa. Sin el 99515375 no se sabe qué es cada
pin del DE-9, y esa es la pregunta abierta más cara del proyecto.

**Y `b1`, el ancho entre patas, tampoco:** es **opción de pedido**, de 838 a 1524 mm en pasos de
media pulgada. Dos cosas se ganan igual: el **1.315 del repo es un valor válido de tabla**
(51.75" = 1314.45 mm), y los valores son **discretos**, así que al medir basta con acercarse y
ajustar al valor de tabla. El camino limpio es el **número de serie por MCF Parts Client**.

---

## Qué se construyó — sesiones de agosto

| Qué | Dónde |
|---|---|
| Repositorio público con Pages | `github.com/Rodzilla-TheCreator/tata` |
| Índice de visuales | `index.html` → `rodzilla-thecreator.github.io/tata/` |
| **Visor del sector A** con FSM, control Obed y consola de flota | `sim-web/actual_tpl.html` → `build_actual.py` |
| Datos del sector A filtrados | `datos/sectorA.json` |
| Planificador de giro Hybrid A\* | `analisis/planificador_giro.py` |
| Medidas de campo en la secuencia | `sec/sec_tpl.html` |
| Tres planes de intervención + plan de diagnóstico | `docs/10`, `docs/11` |
| Arreglos de Isaac Sim | `sim-isaac/` |

**Control Obed:** el timón acumula y **se queda donde se deja**, como el volante real —
2.6 vueltas de tope a tope. El ángulo útil se recorta hasta 45% con la velocidad; el sobre
de 1.5 m/s dejó de ser texto y es código.

**Botoni** es el proyecto de graduación de maje, Marcelo y Pato: cuatro meses sobre un
PuzzleBot. Lo único que cruzó a TaTa es la **consola de visualización**, traída a propósito
porque es a prueba de tontos — un botón verde grande que dice START, uno rojo que dice STOP,
y así. Esa parte se queda. Nada más de Botoni entra por defecto; ver la regla de abajo.

**Consola de flota:** rediseñada sobre la consola de Botoni. El mapa domina, la FSM es un
**anillo** (el ciclo es un lazo, no una tira con scroll), la cámara bajó a miniatura, y se
agregó tiempo:
ciclos, ciclo medio, tiempo en estado, % bloqueada y ocupación del cuello de botella de A.
La barra del cuello queda gris hasta tener 25 s de muestra — 100% a los tres segundos no es
un cuello, es no haber medido.

---

## Lo que falta, en orden

### 1 · Lo que falta de la silueta ← ya no bloquea la factibilidad

**Bajó de prioridad.** El barrido de `XPIV` entre 1.30 y 1.60 dejó la ventana de carriles
quieta en 75–150 cm: el giro entra sea cual sea el valor. Sigue haciendo falta para **control
fino**, no para saber si se puede.

Queda por medir, con flexómetro:

1. **`W_MAX`, ancho pata a pata.** Nunca se midió. Ancla toda la escala lateral
2. **`XPIV`**, culo → centro de las ruedas de carga, **con plomada** para el culo. Y resolver
   la contradicción: la rueda en la estación 282 implica 1.862, que viola la cota de 1.6724
3. La dispersión de parada: **tiza en el piso donde el operador para de verdad, cinco veces.**
   Esa dispersión es literalmente el requisito de precisión que el kit debe superar

Y en el planificador: **modelar las uñas en `silueta()`**, que hoy no existen.

### 2 · El puerto de servicio ← esto es lo urgente

El plan completo está en `docs/15`, actualizado por `docs/16`. Falta el viaje:

- **Primero: las cuatro mediciones contra el negativo de batería.** Deciden si el puerto es CAN
  y por lo tanto qué instrumento sirve. Cinco minutos, antes que nada más
- Seguir **a dónde va el mazo del DE-9**. Es lo que decide si es el puerto o no
- Preguntarle al chino por el **APM+**, por nombre. ¿Lo conoce? ¿Judit lo muestra? ¿Lo trae?
- Contar a mano las **vueltas de volante tope a tope**. Corrige el 2.6 del control Obed
- Sacar el **número de serie** de la placa, y pedir la configuración por MCF Parts Client
- Las **tres pasadas de escucha** con `escucha_edr.ino`. Nunca se probó arriba de 14400 ni
  fuera de 8N1
- Buscar físicamente **otro conector** con los paneles abiertos. Foto de cada uno
- Pines **5 y 6 a chasis**, que quedó pendiente
- Conseguir **WENBM8550-01** por MCF Parts Client vía Montasa

### 2b · La visita de diagnóstico al cliente

`docs/11`, doce preguntas. No se corta ni un cable. La herramienta que decide si sirve son
las **puntas de retro-sondeo**. La pregunta que todos olvidan es **cómo se borran los códigos
de falla** — sin eso el equipo queda bloqueado y se acaba el día.

> **Si el puerto habla, el `docs/10` se abarata entero.** La retroalimentación de velocidad,
> ángulo de dirección y altura que hoy se planea sacar cortando cables de Hall podría salir
> leída del bus, sin tocar un solo conductor.

### 3 · Estados de bloqueo y deadlock en la FSM

Hoy `LIBRE` hace de comodín. Faltan `ESPERA_TRASBORDO`, `ESPERA_HUECO`, `ESPERA_PEDIDO` como
estados de verdad, y un **protocolo de reserva** con una prueba que intente romperlo: si A y
B reservan la última posición de trasbordo a la vez, hoy nada lo impide.

### 4 · Estados de falla y reanudación

Qué pasa si el ArUco no se ve, si el hueco estaba ocupado, si entra un paro a mitad de una
extensión. Hay pasos que **no se pueden reanudar a la mitad** — pantógrafo extendido en
altura. En el fierro esto es la mitad del código y hoy no existe.

### 5 · Isaac Sim en Linux

Los arreglos ya están en el repo. Clonar y arrancar con `--sin-sensores`. Primera vez compila
shaders 10–40 min con la ventana aparentemente colgada; **no matarlo**.

### 6 · Deuda menor, anotada para que no se pierda

- `sim-web/build.py` tiene **el mismo bug de encoding** que se corrigió en `build_sec.py`:
  abre sin declarar utf-8 y revienta en Windows. No se tocó porque no se pidió.
- `sim-isaac/tata_sim.py` usa `--nivel scrappy|industrial|produccion|maximo`. El CLI
  **contradice la regla de este archivo** de no usar "scrappy".
- `docs/01` a `docs/07` no se reescribieron tras la medición de campo.
- El build `TaTa_Secuencia.html` **se versiona** porque lo sirve Pages: hay que reconstruir
  y commitear tras tocar `sec/sec_tpl.html`, o Pages muestra lo viejo.
- La canaleta de drenaje con rejilla que cruza el pasillo (foto IMG_0208) no está en ningún
  modelo. Para un humano es un bache; para navegación autónoma es un salto de rueda y una
  discontinuidad de odometría.
- `analisis/planificador_giro.py` → `silueta()` **no modela las uñas**. Sus números de 90° y
  180° son solo chasis. Detallado arriba.
- `herramientas/serie/probador.py` da «ESTE SIRVE» sin exigir loopback. Detallado arriba.
- El menú de servicio del display (`Settings → Menu → lift / drive / steer`) se encontró pero
  **no se documentó cómo se entra ni qué hay adentro**. Vale fotos si sobra tiempo; no es la
  prioridad, el conector sí.

---

## Cómo trabajar aquí

- Responder en **español**, directo y conciso. Máximo **400 palabras** de prosa salvo que se
  pida más; tablas, código y listas de archivos no cuentan.
- No adular ni rellenar. Si algo está mal, decirlo de frente.
- **Verificar antes de afirmar.** Casi todo lo de `docs/` tiene su cálculo en `analisis/`.
  Si vas a contradecir un número, corré el script primero.
- Cuando un cálculo contradiga algo escrito antes, **corregirlo explícitamente**.
- **Y cuando la realidad contradiga al cálculo, gana la realidad.** Pasó tres veces en esta
  sesión: el modelo decía que el giro con carga no existía y la máquina lo hace todos los
  días. Las tres veces el error estaba en el modelo, y encontrarlo mejoró el resultado.
  Antes de declarar algo imposible, preguntar si alguien ya lo está haciendo.
- **No se borra el camino.** Cuando una conclusión reemplaza a otra, la vieja **se conserva**
  junto con qué la tumbó — como hace la sección «Corregido en campo» de este archivo. Nunca
  reescribir un documento dejando sólo la versión buena: si después aparece un error, hay que
  poder volver al punto donde se tomó el desvío y decidir si se retoma con correcciones o se
  cambia por otro. Lo vigente arriba, el historial abajo, y una tabla de *decía / es / qué lo
  tumbó* en medio. `docs/03` es el modelo.
- **Botoni es mapa, no repuesto.** Sus decisiones se tomaron para un PuzzleBot de eje
  diferencial que gira en el sitio; esta máquina es no holónoma con radio mínimo. Copiar una
  decisión de allá es heredar una restricción que acá no aplica. Las huellas sirven para
  saber la dirección, no para pisarlas encima. Antes de traer algo de Botoni, decir **qué
  problema resolvía allá** y si ese problema existe acá. El caso ya pagado está más arriba,
  en el planificador: en Botoni girar en el sitio hacía trivial la planificación, y acá esa
  suposición no existe.
- **Un dato nuevo no revienta el modelo.** Cuando algo no calza, lo primero es el bloqueo
  obvio, no «todo lo que sabía ya no vale». Pasó con el cable ethernet-a-DB9: un mapeo raro
  de procedencia no confirmada no borra un voltaje medido. Se guarda como **dato en tensión**
  y se sigue con lo que sí se sabe. *Only a Sith deals in absolutes.*
- **Verificar antes de contradecir a quien lo hizo con las manos.** Se objetó que Judit no
  podía aplicar a un Mitsubishi. El chino tenía razón: MCFA distribuye las tres marcas. Quien
  operó el equipo tiene evidencia que ningún catálogo tiene.
- **Verificar antes de decir que algo no existe.** Antes de afirmar que un archivo no está en
  el repo: `git fetch`. Se declaró inexistente un `docs/14` que sí estaba.
- **Consultar el CLI y los docs antes de adivinar.** Cuatro adivinanzas seguidas sobre Remote
  Control costaron más que `claude rc --help`.
- **Validar el instrumento antes de viajar.** Toda medición trae su control de falsación: si
  la prueba no puede fallar, no midió nada. El eco 6/6 solo vale porque quitar el puente dio
  SIN ECO.
- **Este proyecto no arranca resuelto.** Tratar a Botoni como una solución que solo hay que
  comprar y adaptar convierte la adaptación en el trabajo más caro del proyecto, y encima
  invisible en el presupuesto. Es el supuesto que infla o desinfla el nivel Piloto de
  `docs/05`.

## Quién es quién

**El equipo TaTa es maje, más el Chino en lo mecánico y eléctrico.** Todo lo que sigue son personas reales
con relaciones reales al proyecto, pero **ninguna de ellas está en el equipo**. Escribir o
hablar como si lo estuvieran infla el proyecto y compromete tiempo ajeno que nadie prometió.

- **maje** — el equipo. Lidera, construye todo, habla con operadores y mecánicos

**Consultables — no son equipo, no tienen tareas asignadas acá:**

- **Pato** — meses de LiDAR y SLAM en Botoni. **No es parte del equipo TaTa.** Lo valioso
  no son sus parámetros sino **por qué llegó a ellos**: qué probó, qué descartó y contra
  qué. Se le llama y se le pregunta. No se importa su stack
- **Marcelo** — localización y alineación en Botoni. Su matemática es adaptable y señala
  dónde están los problemas y dónde las soluciones. Igual que Pato: consultable, no copiable

**Equipo de ingeniería — asignado a maje:**

- **el Chino** — técnico, mecánico y sub-jefe de taller bajo Miguel, pero opera y comanda.
  **Asignado a maje**: se le puede llamar en cualquier momento. Tiene un EDR en su taller, así
  que sirve para ir a ver la máquina antes del diagnóstico. Traduce lo mecánico del montacargas
  y apoya en lo eléctrico y electrónico. **Va a la visita de diagnóstico de `docs/11`.**
  Es apodo, así se presenta él y así se le dice.

**Montasa:**

- **Omar** — dirige Montasa. **Todavía no es parte del proyecto.** Se le va a pedir
  aprobación en algún punto cercano, y ese es el momento en que entra, no antes. Perfil
  financiero, poco contexto técnico
- **Christian** — captura y medición en campo
- **Fabrizio** — mediador y cara comercial

## Reconstruir los entregables

```bash
python build_sec.py                  # simulación de secuencia
python build_actual.py               # visor del sector A
python3 sim-web/build.py             # simulador completo  (ojo: falla en Windows)
python3 sim-web/build_operador.py    # vista de operador
python3 datos/extract3d.py           # re-extraer geometría del DXF (necesita el .dxf)
python3 sim-isaac/export_usd.py      # regenerar la escena USD
node presentaciones/deck_o2.js       # deck de Omar
node presentaciones/deck_r.js        # deck de RETHINK
```

`build_sec.py` y `build_actual.py` necesitan `node_modules/three/build/three.min.js`, que no
se versiona. Si no está, se extrae del `sim-web/dist/Almacen_RETHINK_3D.html` ya construido,
que lo trae inyectado — así se garantiza la misma revisión (r13x) que usa el resto.
