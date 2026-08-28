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
| `docs/10-intervencion-electrica.md` | Los tres planes de intervención: freno, tracción, dirección |
| `docs/11-plan-de-diagnostico.md` | **La visita de medición. Va ANTES del doc 10** |
| `docs/12-medicion-de-la-sombra.md` | **Una hora con flexómetro y papel. Cierra el bloqueo 1** |
| `docs/13-timeline-antes-de-la-semana.md` | **Todo lo que va antes, por dependencia. El bloque 0 corre desde hoy** |

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

## Qué se construyó en esta sesión

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

### 1 · Las tres medidas de la silueta ← bloquea todo lo demás

`XPIV` sigue **derivado del radio de ficha, no medido**, y la silueta es hipótesis. Cada vez
que cambia una suposición, la ventana de carriles se mueve entera. Con flexómetro:

1. Culo → centro de las ruedas de carga
2. Ancho del capó trasero en su punto más ancho
3. Dónde está el punto de 1.315 medido desde el culo, cuánto dura, y el radio de la esquina

Y una de operación que vale igual: **tiza en el piso donde el operador para de verdad, cinco
veces.** Esa dispersión es literalmente el requisito de precisión que el kit debe superar.

### 2 · La visita de diagnóstico

`docs/11`, doce preguntas. No se corta ni un cable. La herramienta que decide si sirve son
las **puntas de retro-sondeo**. La pregunta que todos olvidan es **cómo se borran los códigos
de falla** — sin eso el equipo queda bloqueado y se acaba el día.

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
- **Botoni es mapa, no repuesto.** Sus decisiones se tomaron para un PuzzleBot de eje
  diferencial que gira en el sitio; esta máquina es no holónoma con radio mínimo. Copiar una
  decisión de allá es heredar una restricción que acá no aplica. Las huellas sirven para
  saber la dirección, no para pisarlas encima. Antes de traer algo de Botoni, decir **qué
  problema resolvía allá** y si ese problema existe acá. El caso ya pagado está más arriba,
  en el planificador: en Botoni girar en el sitio hacía trivial la planificación, y acá esa
  suposición no existe.
- **Este proyecto no arranca resuelto.** Tratar a Botoni como una solución que solo hay que
  comprar y adaptar convierte la adaptación en el trabajo más caro del proyecto, y encima
  invisible en el presupuesto. Es el supuesto que infla o desinfla el nivel Piloto de
  `docs/05`.

## Quién es quién

**El equipo TaTa es maje, y nadie más — por ahora.** Todo lo que sigue son personas reales
con relaciones reales al proyecto, pero **ninguna de ellas está en el equipo**. Escribir o
hablar como si lo estuvieran infla el proyecto y compromete tiempo ajeno que nadie prometió.

- **maje** — el equipo. Lidera, construye todo, habla con operadores y mecánicos

**Consultables — no son equipo, no tienen tareas asignadas acá:**

- **Pato** — meses de LiDAR y SLAM en Botoni. **No es parte del equipo TaTa.** Lo valioso
  no son sus parámetros sino **por qué llegó a ellos**: qué probó, qué descartó y contra
  qué. Se le llama y se le pregunta. No se importa su stack
- **Marcelo** — localización y alineación en Botoni. Su matemática es adaptable y señala
  dónde están los problemas y dónde las soluciones. Igual que Pato: consultable, no copiable

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
