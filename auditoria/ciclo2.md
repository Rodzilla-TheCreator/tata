# Auditoría — ciclo 2 (20-nov-2026): dónde estamos parados de verdad

maje pidió franqueza: en qué está corto, qué mérito es de quién, dónde apunta muy alto, qué se le pasa,
qué estamos subestimando, y si la odometría y las cámaras alcanzan. Lo que se afirma acá sale del repo y
del manual de servicio (`pdftotext`); donde es opinión, se dice.

## 1. Méritos: de maje y del agente

**De maje, y no los podía hacer nadie más:**
- **Las mediciones que tumbaron modelos:** el pasillo de 3.00, el rack, la sombra; la matriz de ohmios del
  03-oct que encontró el CAN en 3↔8 cuando el agente llevaba semanas empujando la hipótesis serie.
- **El 22-oct:** el nodo 2 falso aceptado por el Master en el equipo real. Es el riesgo que podía matar el
  proyecto y lo cerró con las manos (el puente en el mazo, el TJA soldado y cambiado, el R3 quitado).
- **Detectar los errores del agente:** el «azul abierto» de la i3, las velocidades «supuestas» que eran
  de los operadores, las zonas de carga que faltaban, el culo «custom» que no existía.
- **El acceso:** el Chino, Miguel, el manual de servicio, el equipo prestado y **Omar comprando los
  repuestos sin pedírselo dos veces**. Eso es confianza ganada, no suerte.
- **La disciplina del control de falsación** («si la prueba no puede fallar, no midió nada»).

**Del agente (Claude, i3 incluida):**
- Volumen de análisis rápido: el planificador Hybrid A*, el culo desde los vectores de la ficha, el EKF
  con rueda motriz, la FSM, la simulación, el firmware, la lectura de 259 páginas de manual.
- Atrapar riesgos de diseño antes del banco: la regla del `1.06` (salidas siempre complementarias), los
  módulos de relé activos en bajo, el paro que re-pisaba solo (este último lo vio la i3).

**Y los errores del agente, que también hay que contar:** la teoría de la Incado Box que nunca existió;
semanas defendiendo «es serie» por el −14.6 V; el culo con esquinas de 0.17; los rodeos con el sensor del
pedal. El patrón es el mismo cada vez: **un modelo seguro de sí mismo sobre un dato no medido**. Y una
parte de lo que el repo marca «PASA» es **validación contra sí mismo**: el EKF se probó contra una
simulación escrita por el mismo agente, con el ruido que el agente supuso.

## 2. Dónde maje está corto (dicho con respeto, porque se puede cubrir)

| Área | Por qué importa | Cómo se cubre |
|---|---|---|
| **Seguridad funcional** (ISO 3691-4, ISO 13849 PL d, validación) | Es lo que separa una demo de algo que un cliente pueda tener operando. Nadie en el equipo la ha hecho | Un consultor por horas para revisar la arquitectura antes del nivel Piloto, no después |
| **Auditar el firmware que escribe el agente** | El watchdog es una función de seguridad escrita por una IA y revisada por otra IA. maje prueba que **se comporta** bien, pero no puede revisar que **esté** bien por dentro | Que las pruebas de banco sean el contrato (ya va así) y, más adelante, una revisión humana de un tercero |
| **Control de un vehículo pesado no holónomo** (seguimiento de trayectoria, carga, mástil) | Planificar es la parte fácil; seguir la ruta a ±3 cm con 1 t líquida arriba no lo es | Marcelo (consultable) para la matemática; mucho tiempo de fierro |
| **Lo contractual** (responsabilidad, seguro, qué pasa si cae un IBC de 6.7 m) | Antes de que el cliente opere solo | Omar y un abogado cuando llegue el Piloto |

## 3. Dónde se apunta muy alto

- **Autonomía completa hasta N5 (6.77 m) en 3.00 m de pasillo**, con márgenes de **3 a 7 cm por lado**
  según la ficha. Es el caso más difícil que existe en montacargas, con un solo equipo, que hoy está en
  reparación.
- **Todo en paralelo:** LiDAR + Jetson + SLAM, Isaac Sim con 8 GB de VRAM, coordinación de dos equipos, el
  simulador web, cinco decks, El Aula. Para un equipo de una persona más agentes, cada frente nuevo le
  quita horas de fierro al frente que decide.
- **Síntoma:** 25 documentos y un `CLAUDE.md` de 59 KB para un equipo que todavía no se ha movido un metro
  con nuestro mando. La documentación va más rápido que el fierro.

## 4. Lo que se está pasando por alto

1. **No hay sensor de altura de uña.** `0x23BA = 0` en este equipo y la altura no viaja en ningún PDO
   (`componentes/LEEME.md`, 23-oct). Sin altura medida no hay toma ni depósito arriba de N1: la ventana del
   hueco del IBC es de **4.4 cm vertical**. Hace falta un encoder de hilo (draw-wire) en el mástil, y no
   está en ningún BOM ni plan.
2. **Nadie ve las uñas en la toma.** El propio análisis de visibilidad da **0 %** de marcas visibles en la
   alineación y en la toma. Para meter las uñas en un hueco a 6.7 m hace falta un sensor en el carro:
   cámara o ToF mirando hacia adelante desde las uñas.
3. **El IBC lleva 1000 L de líquido.** Se mueve al frenar y al girar, y más arriba es peor. Ningún modelo
   tiene oleaje ni el balanceo del mástil a 6.7 m con el pantógrafo extendido.
4. **El entre ejes no se sabe (1.562 o 1.688, un 8 %).** En la rotación sobre el eje de carga, el rumbo
   sale de `dθ = −ds / WB`. Con 8 % de error, **un giro de 90° sale con ~7° de error**, que en la entrada
   a la bahía son decenas de centímetros. El EKF estima la escala y el sesgo, pero **no el entre ejes**.
5. **La seguridad de personas.** «Sellado a humanos» no cubre al que entra a destrabar algo. El estándar
   de la industria es un **escáner láser de seguridad certificado** con campos que crecen con la velocidad.
   Una cámara nunca es un sensor de seguridad.
6. **Detectar hueco ocupado, rack torcido, IBC abombado:** están en la FSM como estados, pero ningún
   sensor del plan los mide.
7. **La operación:** carga de batería, cambios de turno, quién rearma y cómo se entrega el equipo de
   vuelta al operador humano.

## 5. Dónde se está subestimando

| Creemos que es… | En realidad… |
|---|---|
| Mandar marcha por el `0x182` = controlar la velocidad | El controlador tiene sus propias rampas y su freno regenerativo. **Parar a ±2 cm** comandando como un operador es otro problema. La dispersión de parada del operador (la prueba de la tiza) nunca se midió |
| Emular el sensor del volante = controlar la dirección | Es cerrar un lazo de posición **a través** del lazo del EPS, con 5.5 vueltas de tope a tope, recorte por velocidad y una latencia que no se conoce. Seguir una ruta con 3 cm de margen así es difícil |
| Márgenes de 3–7 cm por lado | Salen de la ficha y del DXF. Postes fuera de plomo, IBC abombado, desgaste de ruedas y el error de las marcas se comen eso rápido. **Hay que medir el pasillo real con el equipo adentro** |
| El EKF ya está «validado» | Validado en sintético. **No existe ni un metro de odometría real capturada** |
| El watchdog es lo simple | Es lo simple de la demo. Certificar la cadena de paro para operación es el trabajo más caro del Piloto |

## 6. ¿Creo en la odometría con los sensores de las ruedas?

**Para tramos ciegos cortos, sí. Para la rotación y la alineación final, todavía no.** Lo que hay:

- **Motor de tracción:** sensor de rodamiento de dos pistas (cuadratura), confirmado en el manual
  (`1.17.x`, «se cuentan ambas pistas»). Pero mide el **motor**, no el piso: la rueda motriz patina al
  acelerar y en el freno regenerativo, se arrastra a 90°, y su diámetro cambia con el desgaste (1–2 cm en
  su vida útil = 1–5 % de escala). El EKF estima la escala si hay marcas seguido.
- **Ángulo de la rueda:** el nodo 4 tiene sensor de realimentación, pero **no se confirmó que salga por el
  bus**: `0x284` es la velocidad del **volante**, no el ángulo de la rueda.
- **Nada de esto se ha decodificado en movimiento.** El `188` de tracción se vio solo quieto.
- **La pieza que más vale, descubierta hoy en el manual:** la familia ETR tiene un **sistema de sensores en
  las ruedas de carga** (eventos `1.17.19`–`22` y `1.41.1`–`6`: cuadratura en la izquierda y en la derecha,
  comparada contra la tracción, «cálculo de distancia»). Las ruedas de carga **no son motrices, no
  patinan**, y con izquierda y derecha dan también el rumbo. Es la odometría que usa el propio fabricante.
  **Mirar en el equipo si las trae** (sensor e imán en el cubo de cada rueda de carga, cables). Si no las
  trae, poner encoders nuestros en las ruedas de carga es la mejor inversión de sensado del proyecto.

**Antes que nada:** medir el entre ejes, confirmar el ángulo de la rueda en el bus y capturar la primera
odometría real contra una cinta en el piso.

## 7. ¿Alcanza solo con las cámaras?

**No.** Alcanzan para **el tránsito por el pasillo**, si las marcas están medidas al centímetro, hay buena
luz y se controla el desenfoque a 1.5 m/s. No alcanzan para:

| Qué | Por qué no | Qué hace falta |
|---|---|---|
| Alineación final y toma | 0 % de marcas visibles (análisis propio) | Cámara o ToF en el carro de las uñas |
| Altura | no hay sensor de altura | Encoder de hilo en el mástil |
| Distancia al rack en el giro (3–7 cm) | con las cámaras es una posición absoluta, y depende de que las marcas y los postes estén donde dice el mapa | **Medir la distancia al rack directamente**: el Unitree L2 que ya se compra lo hace, o dos sensores de distancia laterales |
| Personas | una cámara no es un sensor de seguridad | Escáner láser de seguridad certificado (nivel Piloto) |

## Lo que haría ya (sin agrandar el proyecto)

1. En el equipo reparado: **entre ejes con flexómetro**, si **las ruedas de carga traen sensor**, y una
   **captura del bus en movimiento** contra 10 m de cinta (velocidad de tracción y ángulo de la rueda).
2. Agregar a los planes el **encoder de altura** y **qué ve las uñas**. Sin eso, el producto llega solo
   hasta N1.
3. **Recortar el alcance del primer producto a N1 y a las zonas de carga y descarga** (piso, sin altura).
   Es el 80 % del valor de demostración con el 20 % del riesgo. La altura viene después, con sus sensores.
