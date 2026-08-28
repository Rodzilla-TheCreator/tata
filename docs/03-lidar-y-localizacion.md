# Localización: ArUco, cámaras y el papel del LiDAR

> **Cómo leer este archivo.** Arriba está lo que se decidió y por qué. Abajo, bajo
> «El camino que nos trajo acá», queda intacto lo que creíamos antes y qué lo tumbó.
> No se borra: si más adelante aparece un error, queremos poder volver al punto donde
> se tomó el desvío, y o retomarlo con correcciones o cambiarlo por otro.

---

# Lo vigente

*Decidido el 27-ago-2026.*

## La decisión

**El LiDAR no navega. Localizan las cámaras con ArUco más la odometría.**

Al LiDAR le queda un solo trabajo: **ver lo que no debería estar ahí**. No es redundancia ni
respaldo — es el único sensor que hace ese trabajo, porque el mapa acierta con los racks y se
equivoca todos los días con lo que hay en el pasillo.

## Por qué el LiDAR no navega acá

El almacén **no cambia de forma**. Los racks están anclados, las posiciones son fijas, el
layout se levanta una vez. No hay nada que mapear en operación: así trabajan los AGV
industriales de verdad, siguiendo un mapa conocido, sin SLAM en vivo.

Botoni ya demostró que localizar con ArUco y odometría funciona, y nunca chocaron. El código
está en `puzzlebot_ros/poseKalman` y `nav_pkg/nav_node_pb.py`, y verificado línea por línea:
el scan **nunca entra al filtro**. Ver «Lo que hicimos en Botoni», abajo.

### Qué pasa con el análisis de degeneración

`analisis/analisis_degeneracion.py` respondía «si el LiDAR localizara, ¿qué haría falta?».
Si el LiDAR no localiza, **la pregunta deja de hacerse**. El script se archiva, no se borra.

No es que estuviera mal: es que su pregunta salió del alcance. Y de paso queda anotado que
su tabla nunca reprodujo lo que estaba escrito acá — metía paredes a 4.5 m de cada extremo
incluso en el caso «abierto», y la restricción longitudinal la da **la pared del fondo, no
los montantes**.

Lo mismo aplica a la firma de ocupación de `analisis/firma_ocupacion.py`: resolvía el
reconocimiento de lugar entre pasillos idénticos. Con un ArUco de identidad en cada cabecera,
ese problema no existe. Queda como carta guardada si algún día la identidad visual falla.

## Dos cámaras USB, y por qué

**En cada ángulo del arco hay al menos una cámara con un ArUco a la vista.**

Con el equipo avanzando por el pasillo, la frontal ve la cabecera y la lateral ve la cara del
rack. Cuando gira 90° para encarar la bahía, **intercambian papeles**: la frontal pasa a ver
la bahía y la lateral queda mirando a lo largo del pasillo. El giro de salida es simétrico.

Con una sola cámara se pierde la referencia exactamente cuando más se necesita — en el giro —
y hay que confiar en odometría ciega justo en el momento de peor deriva.

**Esto importa más acá que en Botoni.** El PuzzleBot es diferencial, con encoders calibrados
sobre piso liso. El EDR tiene rueda motriz orientable, ruedas de carga que arrastran en el
arco, piso manchado de aceite, la rejilla de drenaje que cruza la boca del pasillo
(`fotos/IMG_0208`) y 1.58 t que cambian la deformación de la llanta según vaya cargado. Entre
ArUco y ArUco se deriva más. Verlos casi continuamente deja de ser lujo.

### Regla: no fusionar imágenes para sacar pose

El *image merging* deforma la geometría en las costuras, y la pose del ArUco sale
precisamente de la geometría de sus cuatro esquinas. Una costura mete error de milímetros a
centímetros justo donde se necesitan milímetros.

- **Cada cámara calibrada por separado.** Se detecta en cada imagen cruda.
- **Se fusionan las poses, no los píxeles.** Cada detección es una estimación; el filtro las
  combina.
- El panorama sirve, pero para la pantalla del operador y para la consola. Vista para humanos
  por un lado, matemática por el otro.

### Especificación de cámara

Lo que manda a 1.5 m/s es el **desenfoque de movimiento**, no los megapíxeles. Obturador
global le gana a más resolución. Y ojo con el ancho de banda si las dos cuelgan del mismo
controlador USB: MJPEG o buses separados.

La tercera cámara —la de uña, que viene de fábrica— es la del ajuste final en la bahía. Antes
de contar con ella hay que saber **qué señal se le puede sacar**; ver `docs/11`.

## Lo que hicimos en Botoni, verificado en el código

Repo: `github.com/MDLTE/Autonomous-Warehouse-Forklift`. Lo que arranca
`botoni_main/launch/botoni_main.launch.py`:

`poseKalman` (EKF) · `aruco_detector` · `qr_detector` · `qr_alignment_node` · `door_align` ·
`nav_node_pb.py` · `voice_node.py` · la UI · y el `botoni_fsm` como maestro.

| Hallazgo | Detalle |
|---|---|
| No arranca simulador | Ni Gazebo ni Isaac Sim. Es el launch del robot real |
| `slam_pkg` **no se usa** | Está en el repo con `MCL.py`, `slam_node.py`, mapas — el launch no lo llama. Fue exploración que no llegó al stack |
| El LiDAR no localiza | `scan_cb` solo guarda ángulos y rangos; el scan jamás entra al filtro |
| El LiDAR hace dos cosas | `_obstacle_in_arc(arc, dist)` para proximidad, y alimenta la DWA para evasión local |
| El A\* planifica sobre grid precargado | Mapa estático, con `corridor_painter.py` y `search_waypoints.json` — pasillos y waypoints a mano |
| Nadie usa `intensities` | Cero. Pura geometría |
| Wart de portabilidad | `nav_node_pb.py` y `voice_node.py` se lanzan por ruta absoluta a `/home/marcelo/ros2_ws/` |

### La solución de Marcelo para la alineación

Su cabecera lo dice textual: integra los encoders **localmente** y *no usa `/odom` global, que
frente al estante no se ubica*. O sea que **separó** la alineación de la localización global a
propósito.

1. Mide la pose del QR **desde lejos**, donde todavía se ve bien
2. Calcula un punto **G** sobre la normal a la cara del pallet, a 0.50 m de standoff
3. Maniobra hasta G con giro-avance-giro **a ciegas**, sobre odometría local de encoders
4. Ajuste visual final a 0.27 m, y 0.22 m de empuje ciego para meter las horquillas

Lo elegante no es que el QR entre al mapa. Es que **el QR se convierte en un objetivo
geométrico una sola vez**, y de ahí en adelante ya no hace falta verlo.

### Lo que de esto NO transfiere

Ese esquema descansa en que la odometría ciega aguante medio metro. En el EDR no aguanta igual,
por las razones de arriba.

**Y no hace falta que aguante.** El EDR no se alinea manejando: tiene **desplazador de ±12 cm**
y pantógrafo. La secuencia de `docs/02` ya lo dice — parar el chasis donde diga la marca,
anular el error lateral con el desplazador sin mover el chasis, subir, extender, bajar.

Botoni resolvió con maniobra lo que TaTa resuelve con actuadores. Es el ejemplo más limpio de
la regla del `CLAUDE.md`: **Botoni es mapa, no repuesto.**

## El LiDAR de navegación: qué comprar

Un LiDAR 2D ve **una sola rebanada horizontal**, a la altura donde se monte. Eso no es un
detalle de calidad: es lo que lo define.

A la altura del chasis, esa rebanada corta exactamente lo que puede golpear: la fila de IBC del
nivel de piso, **piernas de personas**, tarimas, los tambores estacionados en el pasillo
(`fotos/IMG_0212`), los IBC que sobresalen de la línea amarilla (`fotos/IMG_0209`).

Lo que **no** ve: nada por encima de ese plano. Una uña afuera a 2 m, un IBC mal puesto colgando
en el nivel 4, el mástil de otro equipo.

| Requisito | Valor | Por qué |
|---|---|---|
| Dimensión | **2D** | Las personas están en el piso, no montadas en el rack |
| Alcance | ~10 m | Es detección de bulto en un pasillo de 3 m, no localización |
| Intensidad | **no hace falta** | Sin retrorreflectivos, no hay nada que discriminar por reflectividad |
| Altura de montaje | por definir en campo | La única decisión de verdad, y se mide, no se calcula |

Cae la recomendación anterior del Livox Mid-360 de $749: era un 3D para un trabajo de
localización que ya no existe.

### Inspección en altura: no es este sensor

«Ver si un cubo quedó mal puesto» es **inspección, no navegación**, y no justifica un 3D:

- **El carro se mueve.** Un 2D montado en el carro barre verticalmente solo con el movimiento
  del mástil: nube 3D gratis.
- **La cámara de uña ya sube hasta la bahía.** La inspección sale como subproducto del ciclo.

Anotado como posible más adelante. **No es requisito de Piloto** — es de las metas que crecen
solas hasta comerse el proyecto.

## Lo que devolvería el LiDAR a la navegación

Que la oclusión de ArUco resulte frecuente: un IBC guardado chueco tapando uno, un equipo
parado enfrente. **Se mide, no se discute** — contar cuántas veces por ciclo se pierden ambas
cámaras. Si es raro, quedan las cámaras. Si es constante, vuelven los retrorreflectivos.

Un retrorreflectivo es cinta o cilindro que el LiDAR aísla **por intensidad**, sin identidad:
solo dice «punto brillante, este ángulo, esta distancia». No es un ArUco ni lo reemplaza; es
otro canal de sensado. Y se tapa igual de fácil, así que no resuelve la oclusión — resuelve la
deriva longitudinal en pasillos largos, que es otro problema.

## Lo que sigue abierto

- **La altura de montaje del LiDAR.** Se mide en campo.
- **Cuántos ArUco, a qué separación y a qué altura.** Botoni fijó los suyos mirando la cámara
  en muchos ángulos hasta decidir. Acá toca repetir ese ejercicio con la geometría del EDR.
- **Qué señal sale de la cámara de uña de fábrica.** `docs/11`.
- **Si hay zona clasificada** en el área de mixers. Cambia sensor, precio y proveedor por
  completo. Es pregunta para el cliente.


---

# El camino que nos trajo acá

*El documento tal como estaba antes del 27-ago-2026. **No manda.** Se conserva para poder
rastrear de dónde salió cada suposición.*

## Qué cambió, y qué lo tumbó

| Decía | Es | Qué lo tumbó |
|---|---|---|
| El LiDAR localiza; los marcadores asisten | **El LiDAR no localiza.** Localizan dos cámaras con ArUco más la odometría | El almacén no cambia de forma, y Botoni ya demostró que ArUco + odometría funciona sin chocar |
| «Marcadores», «AprilTag en papel laminado» | **ArUco**, y así se dice siempre | Es el término del proyecto y viene de Botoni, donde el equipo definió cuáles y dónde iban |
| Lo que salva al SLAM son los montantes, cada 1.20 m | **La restricción longitudinal la da la pared del fondo**, no los montantes | `analisis_degeneracion.py` mete paredes a 4.5 m incluso en el caso «abierto», y por eso **nunca reprodujo la tabla de abajo** |
| Un blanco retrorreflectivo por cabecera vale más que marcadores repartidos | Sale del alcance junto con la localización por LiDAR | Es otro canal de sensado, no un sustituto del ArUco, y se tapa igual de fácil |
| La firma de ocupación resuelve los pasillos idénticos | Ese problema **no existe** si cada cabecera tiene un ArUco con identidad | Queda como carta guardada, no como mecanismo primario |
| ±4.5 cm de holgura en la bahía | El IBC presenta 1.00 m al pasillo, y la bahía de 2.35 m lleva dos con 35 cm sobrantes | Medición de campo del 24-ago-2026 |
| Comprar un Livox Mid-360 de $749 | **2D, ~10 m, sin intensidad** | El 3D servía para localizar, y ya no se localiza con LiDAR |
| «Lo que hay que probar en Isaac» | Gazebo por defecto; Isaac tiene que justificarse | Donde Isaac gana es la física de retorno contra la jaula del IBC, y esa pregunta desaparece si el LiDAR no localiza |

## El documento anterior, íntegro

### El punto de partida equivocado

La hipótesis inicial fue que un pasillo largo y uniforme degeneraría el emparejado de escaneos:
el SLAM se desliza a lo largo del eje del pasillo porque no hay geometría que lo restrinja.

**El cálculo lo desmintió.** Está en `analisis/analisis_degeneracion.py`.

| Caso | σ a lo largo | σ a lo ancho | Relación |
|---|---|---|---|
| Rack típico, relieve 8 cm | 0.20 cm | 0.07 cm | 2.7× |
| Rack casi liso, relieve 2 cm | 0.41 cm | 0.07 cm | 5.9× |
| Paredes perfectamente lisas | **singular** | 0.07 cm | ∞ |

**Lo que salva al SLAM son los montantes del rack**: cada 1.20 m hay una cara perpendicular al
pasillo. Con 17 bahías por lado hay restricción longitudinal de sobra. El eje del pasillo queda
**mal condicionado (2.7×), no indeterminado**.

La singularidad sólo aparece con paredes realmente lisas: bahía vacía sin carga que dé relieve,
carga emplayada tapando montantes, o LiDAR montado tan alto que sólo ve por encima de la estructura.

### El riesgo real es otro

**Los 10 pasillos son geométricamente idénticos entre sí.** Eso es reconocimiento de lugar, no
degeneración geométrica, y es el problema mayor.

### La salida: la ocupación como firma

Cálculo en `analisis/firma_ocupacion.py`.

Los pasillos son idénticos, pero el **patrón de bahías llenas y vacías no lo es** — y el WMS ya
sabe cuál es. No hay que aprenderlo, hay que consultarlo.

Con ocupación del 82.2%, cada bahía carga **0.68 bits**. Distinguir 10 pasillos pide 3.32 bits.
Un pasillo de un nivel, ambos lados, son 34 bahías = **23 bits**. Sobra por factor siete.

| Bahías vistas | WMS al día | 10% viejo | 20% viejo |
|---|---|---|---|
| 8 | 56% | 39% | 26% |
| 17 | 90% | 72% | 49% |
| 34 | **99.6%** | 94% | 76% |

### El discriminador

| Situación | Coincidencia esperada |
|---|---|
| Pasillo equivocado | 70.7% (azar entre dos patrones al 82%) |
| Correcto, WMS 5% viejo | 90.5% |
| Correcto, WMS 10% viejo | 86.0% |

Con 34 bahías la desviación es ~7.8%: **el umbral cae cerca del 78%**. Por debajo estás en otro
pasillo; por encima estás bien y lo que falla es el inventario.

**El mismo dato que localiza audita el inventario.** Una bahía que no coincide es error de
inventario; el patrón entero que no coincide es error de localización.

### El rol que le queda al LiDAR

En un ambiente controlado donde se pueden poner los marcadores que uno quiera, **el LiDAR deja de
ser el que sabe dónde estás**. Eso lo resuelve un AprilTag en papel laminado en la cabecera de
cada fila: posición absoluta, sin deriva, sin ambigüedad entre pasillos, por centavos.

Al LiDAR le quedan dos trabajos, y los dos son más chicos:

1. **Ver lo que no debería estar ahí** — una persona, un cubo caído, un patín cruzado, un montante
   golpeado que ya no está donde el mapa dice. Ningún marcador hace eso.
2. **Sostener la operación cuando el marcador falla** — se despega, lo tapa un maxicubo, lo raya
   un golpe. Degradación elegante, no redundancia de lujo.

**Eso cambia el requisito de compra.** Para localizar hace falta precisión y densidad. Para
detectar un bulto en un pasillo de 3 m a 8 km/h alcanza con 10 m de rango y decenas de haces.
El Livox Mid-360 de $749 sobra, y probablemente sobre bastante.

**El orden se invierte:** marcadores primero, LiDAR de apoyo. Más barato, más robusto y más fácil
de explicar.

### Lo que hay que probar en Isaac

Cuántos marcadores y a qué separación, antes de que la deriva entre uno y otro se salga de los
**±4.5 cm** que deja la bahía.
