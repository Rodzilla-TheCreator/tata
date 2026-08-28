# Localización: ArUco, cámaras y el papel del LiDAR

> Reescrito el 27-ago-2026. La versión anterior concluía «marcadores primero, LiDAR de apoyo»
> y esa dirección se sostiene, pero casi todos sus números y su recomendación de compra
> quedaron desmentidos. Lo que sigue reemplaza a esa versión completa.

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
