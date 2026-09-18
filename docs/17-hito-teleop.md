# El hito del teleop — plan de acción

**El hito:** manejar el EDR18N2 con un control de videojuego, en un espacio abierto, con un
dedo humano sobre un paro físico. Nivel **Ingenio** de `docs/05`.

**Lo que NO es el hito:** que navegue, que se localice, que decida. Eso es Piloto. Acá el
cerebro sigue siendo un humano; lo único que se prueba es **que la cadena de mando llega al
fierro y que la cadena de paro llega antes.**

---

## La pregunta del adaptador, primero

Preguntaste si conviene armar ya `DE-9 hembra ↔ CAN ↔ ESP32 ↔ compu` (y después Jetson), o si
el `DE-9 ↔ CAN ↔ USB` es crucial.

**Los dos, y no compiten: son herramientas de etapas distintas.**

| | USB-CAN | ESP32 + SN65HVD230 |
|---|---|---|
| Para qué | **Diagnosticar.** Descubrir qué hay en el bus | **Volar en el equipo.** Watchdog y control |
| Cuándo | Ahora, en el viaje | Después, cuando ya sepamos qué hablar |
| Software | `candump`, SavvyCAN, cansniffer — **maduros, de terceros** | firmware nuestro, que hay que escribir |
| Vida útil | se usa siempre, en cada diagnóstico futuro | queda a bordo |

**El USB-CAN sí es crucial, y la razón es la lección que ya pagamos caro en el hilo del serie.**

El CH340 estuvo mudo semanas y no se sabía si era el puerto o el adaptador. Se resolvió recién
cuando hubo un **instrumento validado contra sí mismo**. Si armás el ESP32 con transceptor y no
ves tramas, volvés al mismo callejón: ¿el bus no habla, o mi cadena no escucha?

El USB-CAN con `candump` es **instrumento de referencia**: si hay tráfico a 250 kbaud, lo ves,
y no hay firmware tuyo en el medio que pueda ser el culpable. Cuesta entre $15 y $40 y te ahorra
la posibilidad de repetir esa semana.

Hay una segunda razón, menos dramática: **decodificar CANopen desde cero en el ESP32 es trabajo
real.** SDO, PDO, heartbeat, emergency. SavvyCAN ya lo hace.

**Entonces:** comprá el USB-CAN para el viaje. El ESP32 con transceptor lo vas a necesitar
igual — el watchdog de `docs/10` lo exige — pero se arma **después de saber qué hay en el bus**,
no antes.

> **Y cuando armes la cadena del ESP32, validala igual que la de serie.** El TWAI del ESP32
> trae **modo self-test / loopback** en silicio: puede mandarse tramas a sí mismo sin nadie más
> en el bus. Es el equivalente exacto del `prueba_cadena.ino`, y hay que correrlo antes de cada
> salida. Y su control de falsación: desconectá el transceptor y confirmá que **no** hay eco.

---

## Bloque 0 · Lo que va antes, y no se salta

| # | Qué | Por qué bloquea |
|---|---|---|
| 0.1 | **Viaje al taller.** `docs/15`, actualizado por `docs/16` | Sin saber qué es el DE-9, no se sabe si el kit lee del bus o corta cables |
| 0.2 | **Visita de diagnóstico.** `docs/11`, doce preguntas, con el Chino | Los tres planes de `docs/10` tienen bifurcaciones que solo se cierran midiendo |
| 0.3 | **Cómo se borran los códigos de falla** | Sin eso, la primera falla bloquea el equipo y se acaba el día. Es la pregunta que todos olvidan |
| 0.4 | **Permiso explícito de Montasa** para intervenir un equipo | Hasta hoy todo fue medir y escuchar. Teleoperar es otra cosa. Es el momento en que Omar entra |
| 0.5 | **El dibujo `99515375`**, esquema eléctrico | Dice qué es cada cable. Sin él se adivina con multímetro |

**0.4 no es trámite.** Todo lo hecho hasta hoy fue reversible y pasivo. El teleop es la primera
vez que el proyecto **manda** sobre una máquina de 2 toneladas. Eso se pide por escrito.

---

## Bloque 1 · En la mesa, sin montacargas

Todo esto se hace en casa y **no depende de nada de arriba**. Se puede empezar hoy.

### 1.1 · El watchdog, solo

Antes que el control, antes que el gamepad: **el que frena.**

```
compu (haciendo de Jetson)  ──latido──▶  ESP32  ──▶  relé  ──▶  LED grande
```

El LED hace de freno. Encendido = hombre-presente cerrado = el equipo andaría.

**Las pruebas que tiene que pasar, y son de falsación, no de demostración:**

| Prueba | Debe |
|---|---|
| Latido normal | LED encendido, estable |
| Se mata el proceso de la compu | **LED apaga antes de 200 ms** |
| Se desconecta el cable del latido | LED apaga |
| Se congela el proceso sin matarlo (`SIGSTOP`) | LED apaga — **esta es la que de verdad importa**, porque es como se cuelga Linux de verdad |
| Vuelve el latido | **LED NO enciende solo.** Rearme manual |
| Se desalimenta el ESP32 | LED apaga |

**Medir el tiempo real de corte, no suponerlo.** Con osciloscopio o con el propio ESP32
registrando. Si da 260 ms, el número del documento está mal y se corrige el documento.

### 1.2 · El control, contra el simulador

El gamepad ya tiene mapeo definido en `CLAUDE.md`: **RT y LT dosifican, B/O alterna sentido**, y
el cambio de sentido **solo se acepta con ambos gatillos en cero y el equipo detenido**.

Se prueba contra el visor del sector A, que ya existe y ya tiene el control Obed. **No hace
falta fierro para encontrar los errores de lógica del mando.**

> **Y de paso se corrige el `0x2414`.** El control Obed usa **2.6 vueltas** de volante tope a
> tope; el parámetro de fábrica del equipo es **5.5**, rango 4 a 8 (ver `docs/16`). El simulador
> tiene el timón más del doble de rápido que el real. Si vas a entrenar la mano en el simulador
> antes de tocar el equipo, **entrenala con el número correcto** o vas a llegar con el reflejo
> equivocado.

### 1.3 · La cadena de paro, armada y probada en la mesa

Hongo NC en serie. Se prueba que **corta con el ESP32 colgado, con la compu apagada y con el
firmware en un bucle infinito**. Si no corta en los tres, no sale de la mesa.

---

## Bloque 2 · En el equipo, sin moverse

Primera vez en el fierro. **Las ruedas no giran.**

| # | Qué |
|---|---|
| 2.1 | Todo montado, **nada conectado al equipo**. Fotos de cada conector antes de tocarlo |
| 2.2 | Interceptar **una sola** señal — la de freno, plan 1 de `docs/10`. Es la menos peligrosa |
| 2.3 | Verificar que `SW` en reposo entrega el sensor original: **desalimentar todo y confirmar que el humano sigue manejando** |
| 2.4 | Comandar desde el gamepad y **ver la respuesta en el tablero**, no en el movimiento |
| 2.5 | Confirmar que **no aparecen códigos de falla.** Si aparecen, borrarlos con lo aprendido en 0.3 y entender por qué |

**La doble señal Hall redundante es el riesgo de esta etapa.** `docs/10` lo advierte: inyectar
una sola dispara falla y bloquea la marcha. Acá es donde se descubre si el par se reprodujo bien.

---

## Bloque 3 · Moviéndose, vacío, en espacio abierto

**No en pasillo.** Patio, o el área abierta del taller.

| # | Qué | Criterio de éxito |
|---|---|---|
| 3.1 | Tracción a velocidad de arrastre — el parámetro `0x2109`, **3 km/h de fábrica** | Arranca y para con el gatillo |
| 3.2 | **Prueba de paro, a propósito, tres veces:** hongo, corte de latido, y apagón del relé | Frena las tres. Se mide la distancia |
| 3.3 | Dirección, a velocidad de arrastre | Responde y **vuelve al centro** |
| 3.4 | Un recorrido de ida y vuelta, con giro | Completo, sin falla, sin intervención del operador |

**Con un operador de Montasa parado en el equipo, con el dedo en el hongo, todo el tiempo.**
No es ceremonia: es que el hongo funcione lo prueba alguien que sabe usarlo.

**Y la prueba 3.2 no se salta ni se hace al final.** Se hace apenas se mueve. Un sistema que
todavía no demostró que para, no debería estar moviéndose.

---

## Bloque 4 · El hito

Recorrido en pasillo, vacío, teleoperado, ida y vuelta con el giro de entrada. **Grabado.**

Ahí está el nivel Ingenio de `docs/05` y ahí se le enseña a Omar.

**Lo que se mide y queda escrito:**

- Distancia de paro a velocidad de trabajo, con los tres métodos de paro
- Tiempo real de corte del watchdog, medido
- Cuántos códigos de falla aparecieron y por qué
- **La dispersión de parada del teleop contra la del operador humano.** Esa comparación es el
  primer dato honesto de si el kit puede superar al humano, y es el requisito que `CLAUDE.md`
  viene pidiendo desde agosto

---

## Lo que puede tumbar el plan, dicho de frente

| Riesgo | Qué haría |
|---|---|
| El DE-9 no es el puerto y el bus no se alcanza | El teleop igual se hace, por el camino de `docs/10`: interceptar señales. Más caro y más invasivo, pero el hito no depende del bus |
| La doble Hall redundante no se reproduce bien | Bloquea el plan 2 (tracción). El plan 1 (freno) puede seguir. Es la razón de empezar por el freno |
| La dirección resulta ser CAN y no analógica | `docs/10` §Plan 3 ya contempla la ruta mecánica. Es más cara |
| Montasa no da permiso de intervenir | **Todo el bloque 1 se hace igual.** Nada de la mesa depende de eso |
| Frenar con carga en alto resulta inseguro | Abierto en `docs/10`. El hito se hace **vacío**, que lo esquiva — pero no lo resuelve |

---

## El orden corto, para llevarlo en la cabeza

```
0. Permiso · viaje al taller · diagnóstico · esquema eléctrico
1. Mesa:  watchdog primero, después control, después cadena de paro
2. Equipo quieto:  una señal, freno, sin mover ruedas
3. Moviéndose vacío:  arrastre, y la prueba de paro apenas se mueva
4. Pasillo, grabado
```

**El bloque 1 no depende de nadie y se puede empezar hoy.** Todo lo demás espera al 0.
