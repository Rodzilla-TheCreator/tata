# El control del teleop — qué puede hacer el montacargas y cómo se maneja

**Escrito el 27-sep-2026.** Diseño, no implementación. Lo que se pidió:

> Poder manejarlo con un control de PS4, o cualquier control genérico — no sabemos cuál va a
> ser. Lo que sí sabemos: tiene que ser tan fácil como conectar el cable.

Este documento contesta tres cosas: **cómo se logra que cualquier control sirva**, **qué
funciones del equipo se manejan y en qué orden**, y **qué reglas tiene el mando** para que
un control de videojuego pueda mandar sobre 4 toneladas sin que eso sea una locura.

Se apoya en lo que ya está decidido: el mapeo de `CLAUDE.md` (RT y LT dosifican, B/O alterna
sentido), el watchdog de `docs/10` y el plan por bloques de `docs/17`.

---

## La idea central: el control nunca habla con el montacargas

```
 control  ──USB──▶  compu / Jetson  ──USB serie──▶  ESP32  ──▶  fierro
 (botones)          (INTENCIONES)                  (reglas,       (lo que
                                                    watchdog)      resulte)
```

La compu **no manda botones, manda intenciones**: *avanzar 0.4*, *frenar 0*, *timón a −30°*,
*sentido atrás*. Qué botón produjo cada intención es asunto de la compu y de nadie más.

Eso compra dos independencias, y las dos importan porque hay dos cosas que hoy **no se saben**:

| No sabemos… | …y no importa, porque |
|---|---|
| qué control va a ser | cambiar de control no toca el firmware del ESP32 ni el equipo |
| cómo se va a actuar sobre el equipo — cables de Hall de `docs/10`, o el bus CANopen, o el APM+ de `docs/16` | cambiar la actuación no toca nada del control |

**El control se puede decidir el último día.** Y el día que aparezca un volante de PC, un
joystick industrial o una consola de radio, es otra fuente de las mismas intenciones.

---

## «Tan fácil como conectar el cable» — cómo se logra

### Una base de datos de controles, no un mapeo por marca

Del lado de la compu se lee el control con **SDL2**, la biblioteca que usan casi todos los
juegos de PC (en Python se usa a través de `pygame`). SDL trae una **base comunitaria con
cientos de controles ya mapeados** — PS4, PS5, Xbox, Switch Pro, 8BitDo, Logitech y los
genéricos chinos más comunes — y los presenta todos con **el mismo diseño estándar**:

```
        LB/L1                    RB/R1
        LT/L2                    RT/R2
   ┌─────────────────────────────────────┐
   │   ↑                          Y/△    │
   │ ←   →   BACK  START      X/□   B/○  │
   │   ↓                          A/✕    │
   │      (stick izq)   (stick der)      │
   └─────────────────────────────────────┘
```

El código nombra los botones **por posición**, no por el dibujo. «B» es *el botón de la
derecha*: en Xbox dice B, en PS4 es el círculo ○. Por eso `CLAUDE.md` ya decía **B/O**.

**Resultado: se conecta, SDL lo reconoce, y funciona.** Sin configurar nada.

### Y si el control no está en la base

Un control chino sin marca puede no estar. Entonces la primera vez corre un **asistente de
asignación** de un minuto:

```
  Control nuevo: "USB Gamepad 0079:0006"
  Apretá el botón que quieras para HOMBRE-PRESENTE…   ✓
  Apretá el gatillo de AVANZAR…                       ✓
  …
  Guardado. La próxima vez se reconoce solo.
```

Queda guardado por el identificador del control, en un JSON del repo. **La segunda vez es
enchufar y listo**, igual que uno reconocido.

### Con cable

**Para el hito, el control va con cable USB.** No por la latencia — Bluetooth anda en 10 a
20 ms, bastante adentro de los 200 — sino porque **Bluetooth se corta**: pila baja,
interferencia, el control que se duerme. Cada corte es un paro (ver abajo), que es seguro pero
te para la prueba. Bluetooth se puede habilitar después, sin cambiar nada del diseño: su corte
ya está cubierto.

**Nunca wifi entre la compu y el ESP32.** Eso ya lo decidió maje: agrega latencia sin cota
dentro de un presupuesto de 200 ms.

---

## Qué puede hacer el montacargas — por fases

No todo va el primer día. El orden sigue el de `docs/17`: primero lo que para, después lo que
mueve, después lo que levanta.

| Función | Qué hace | Fase |
|---|---|---|
| **Hombre-presente** | Habilita todo. Soltarlo = el equipo se detiene | **Hito** |
| **Tracción** | Avanza en el sentido elegido, dosificado | **Hito** |
| **Freno** | Frena, dosificado | **Hito** |
| **Sentido** | Adelante / atrás | **Hito** |
| **Dirección** | El timón | **Hito** |
| **Claxon** | Avisar | **Hito** |
| Elevar / bajar | Las uñas | 2 |
| Pantógrafo | Afuera / adentro, los 0.61 | 2 |
| Desplazador | Lateral, ±0.12 | 2 |
| Inclinación | De las uñas | 2 |

**La fase 2 no entra al hito**, y tiene una regla propia mientras se aprende: **la hidráulica
solo se acepta con el equipo detenido.** En manos de un operador el reach mueve uñas andando;
en teleop, al principio, no. Se relaja cuando haya horas de manejo encima, no antes.

### Lo que el control NO hace, nunca

| | Por qué |
|---|---|
| **Rearmar después de un corte del watchdog** | El rearme es **manual y físico**, en el equipo (`docs/10`). Un rearme desde el control es un rearme que se puede apretar sin ver |
| **Ser el paro de emergencia** | El paro es el **hongo físico**, cableado. Un botón de un control es software, y el software es justo lo que puede estar colgado |
| Cambiar parámetros o programas de velocidad | Eso es Judit / servicio, no manejo |
| Borrar códigos de falla | Igual |
| Usar el botón PS / Xbox / Home | El sistema operativo lo captura. No es confiable |

---

## El mapeo

Por posición estándar. Entre paréntesis, cómo se ve en un control de PS4.

| Control | Qué hace | Fase |
|---|---|---|
| **LB (L1), sostenido** | **Hombre-presente.** Mientras se sostiene, el equipo puede moverse. Se suelta → se detiene | Hito |
| **RT (R2)** | Avanzar, dosificado | Hito |
| **LT (L2)** | Frenar, dosificado | Hito |
| **B (○)** | Alternar sentido adelante / atrás | Hito |
| **Stick izquierdo, horizontal** | Timón | Hito |
| **Y (△)** | Claxon | Hito |
| **START (OPTIONS)** | Modo: arrastre ↔ trabajo. Solo detenido | Hito |
| Stick derecho, vertical | Elevar / bajar | 2 |
| Stick derecho, horizontal | Desplazador | 2 |
| Cruceta ↑ ↓ | Pantógrafo afuera / adentro | 2 |
| Cruceta ← → | Inclinación | 2 |
| A (✕), X (□), RB (R1), BACK (SHARE) | **Libres.** Sin asignar a propósito | — |

**Por qué el hombre-presente es LB y no un gatillo:** un botón sostenido con el dedo índice
no se confunde con dosificar. Y replica exactamente el pedal del equipo real: el operador del
EDR tiene que tener el pie en el pedal para que algo se mueva. **En teleop, el pedal es el
índice izquierdo.** Soltarlo hace lo mismo que levantar el pie: cae el freno de resorte.

---

## Las reglas del mando

Estas son las que hacen la diferencia entre un juguete y algo que se puede poner sobre una
máquina de verdad. Todas corren en **dos lugares**: en la compu, para que el mando se sienta
bien, y **otra vez en el ESP32**, que no le cree a la compu.

### 1 · Arranque en cero

**Al conectar un control, o al volver de cualquier corte, nada se mueve hasta ver los dos
gatillos en cero, los sticks al centro y LB apretado desde suelto.**

Es la regla que hace seguro el «conectar y listo»: sin ella, un control que se enchufa con un
gatillo trabado a medias arranca el equipo solo. Pasa con controles gastados más de lo que
uno cree.

### 2 · Frenar gana

Si LT pasa del 5 %, la tracción es cero, apriete lo que apriete RT. Nunca se suman.

### 3 · El sentido solo cambia detenido

Lo que ya decía `CLAUDE.md`: **B solo se acepta con los dos gatillos en cero y el equipo
detenido.**

> **Abierto:** «detenido» requiere leer la velocidad real del equipo. Hasta tener esa lectura
> — del bus o de los Hall — la compu no sabe si está detenido, y la regla no se puede cumplir
> de verdad. Mientras tanto, lo más cercano es exigir gatillos en cero **y** dos segundos
> quieto. Es un sustituto, no la regla, y así se anota.

### 4 · El timón se queda donde se deja

Es el **control Obed** del simulador: el stick no pone el ángulo, lo **mueve**. Se suelta el
stick y el timón se queda donde estaba, como el volante real. Para enderezar, se lleva de
vuelta.

- Tope a tope en **5.5 vueltas** equivalentes — el `0x2414` de fábrica, no las 2.6 que usa hoy
  el simulador (`docs/16`)
- **A más velocidad, menos ángulo útil**, hasta un recorte del 45 %. Ya está en código en el
  visor del sector A

### 5 · Zonas muertas y curva

- Sticks: se ignora el primer **12 %** del recorrido. Los sticks de control nunca vuelven
  exactos al centro
- Gatillos: se ignora el primer **3 %**
- RT con **curva cuadrática**: la primera mitad del gatillo da un cuarto de la tracción. Es
  donde se hace el trabajo fino, a baja velocidad

Los tres números son los del simulador y quedan como punto de partida. Se ajustan con el
control real en la mano.

### 6 · El sobre de velocidad por modo

| Modo | Techo | De dónde sale |
|---|---|---|
| **Arrastre** — arranca siempre acá | **3 km/h** | `0x2109`, velocidad de arrastre de fábrica. Es el bloque 3.1 de `docs/17` |
| Trabajo | **1.5 m/s** | el sobre de `CLAUDE.md` |

**El sistema arranca siempre en arrastre**, cada vez. Pasar a trabajo es una decisión que se
toma con el equipo detenido, apretando START.

### 7 · Qué pasa cuando algo se corta

| Se corta | Qué pasa | Quién lo hace |
|---|---|---|
| Se suelta LB | Se abre el hombre-presente → cae el freno de resorte | ESP32, de inmediato |
| Se desconecta el control | La compu manda un cuadro con hombre-presente abierto → igual que soltar LB | compu, y ESP32 lo ejecuta |
| Se cuelga o se muere la compu | Dejan de llegar cuadros → a los **200 ms** corta | **ESP32, watchdog** |
| Se muere el ESP32 | El relé cae sin corriente → corta | el relé, por diseño |
| Todo lo anterior falla | **El hongo** | un humano |

Cada fila tiene la de abajo como respaldo. **Y después de un corte del watchdog, el equipo no
vuelve solo**: rearme manual, físico, como ya decidió `docs/10`.

---

## Lo que viaja de la compu al ESP32

**Propuesta.** Contesta tres preguntas que `docs/10` dejó abiertas — período, contenido y
por dónde va el latido — pero no las cierra: se cierran en la mesa, en el bloque 1.

**El cuadro de mando ES el latido.** No hay un latido aparte.

La razón: un latido separado puede seguir llegando perfecto mientras los mandos están
congelados en el último valor — el proceso que late está vivo y el que lee el control se
colgó. Si el latido es el mismo cuadro que lleva los mandos, **un mando viejo es un latido
muerto.**

```
 50 veces por segundo (cada 20 ms), por USB serie:

 ┌──────┬────────┬──────────┬───────┬────────┬───────┬─────────┬───────┐
 │ seq  │ hombre │ tracción │ freno │ sentido│ timón │ hidráu. │ CRC16 │
 │ u16  │ 1 bit  │  u8      │  u8   │ 1 bit  │  i16  │ (fase 2)│       │
 └──────┴────────┴──────────┴───────┴────────┴───────┴─────────┴───────┘
```

El ESP32 **rechaza** el cuadro — y lo cuenta como latido perdido — si:

- el CRC no cierra
- el `seq` no avanzó: un cuadro repetido es una compu pegada que sigue mandando lo mismo
- pide algo que rompe una regla de arriba: sentido cambiado con tracción, hidráulica
  andando en fase de arranque, velocidad por encima del modo

A 50 Hz, los 200 ms son **diez cuadros perdidos seguidos**. Deja margen para ruido sin
dejar pasar un cuelgue real.

---

## Cómo se prueba sin montacargas

Es el **bloque 1.2 de `docs/17`**, y no depende de nada:

1. **Probador del control**, en la compu sola. Se conecta cualquier control y muestra: si SDL
   lo reconoció, el nombre, y las intenciones en vivo. Ahí se prueba la regla de **arranque
   en cero** — enchufar con un gatillo apretado tiene que dar *bloqueado*
2. **Contra el simulador**, el visor del sector A, que ya lee el control con el mismo mapeo.
   Con el `0x2414` corregido a 5.5 vueltas, para que la mano se entrene con el número real
3. **Contra el ESP32 con el LED** del bloque 1.1. Las mismas pruebas de falsación del
   watchdog, ahora con el control: desenchufarlo, soltar LB, congelar el proceso. El LED
   tiene que apagar en las tres

---

## Lo que queda abierto

| Pregunta | Depende de |
|---|---|
| Cómo se lee la velocidad real, para que «detenido» sea verdad | el bus o los Hall — `docs/15`, `docs/10` |
| Qué hace exactamente la intención «freno»: ¿regenerativo dosificado, o solo el de resorte? | cómo se actúe sobre el equipo — `docs/10` plan 1 |
| Frenar con carga en alto | **pregunta para el Chino**, abierta en `docs/10`. No afecta al hito, que es vacío |
| Si la hidráulica se maneja por el bus o por válvulas | fase 2. No bloquea nada hoy |
| Números finales de zona muerta y curva | el control real en la mano |
