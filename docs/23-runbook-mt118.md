# Runbook del MT 118 (Agrolibano) · pruebas durante mantenimiento preventivo

**El MT 118 es equipo de un CLIENTE (Agrolibano).** No es el 122 de Las Palmas (ese es nuestro,
parado, canibalizado). Cuando el 118 entre a mantenimiento preventivo a Las Palmas, es la única
ventana para probar los dos canales de mando en un equipo **que enciende y se mueve** — algo que
el 122 hoy no da. Por eso vale, y por eso el margen de error es **cero**.

Todo acá es **enchufable y reversible**. Se piggybackea en el mantenimiento, se restituye idéntico,
y el equipo sale como llegó. Este runbook convive con `docs/11` (diagnóstico), `docs/20` (simular
mandos / arneses enchufables), `docs/21` (gameplan) y `herramientas/emulador_timon/runbook_prueba_equipo.md`.

---

## Regla cero — autorización, reversibilidad, y el riesgo que de verdad importa

- **Corre SOLO con autorización explícita de Montasa (Omar / Miguel)** y dentro de la ventana de
  mantenimiento, con el Chino presente. Es un activo de un cliente: si algo queda mal, el costo no
  es técnico, es de relación.
- **Nada irreversible.** Todo por conectores. No se corta, no se empalma, no se perfora, no se abre
  el multipiloto **original** (se usa un **repuesto**, `docs/20`). Se restituye idéntico.
- **Paro físico en mano.** Rueda directriz **en gato** para la prueba de dirección. Hombre-muerto
  **sin puentear** hasta la prueba de movimiento, y lo puentea el Chino, no maje.

> ### El riesgo que decide si esto se hace o no: las fallas enganchadas
> **Todavía no se pueden borrar códigos** (licencia de Judit vencida). En un equipo de cliente eso
> es el riesgo real: una falla que **se engancha** y el 118 regresa a Agrolibano **degradado**.
>
> Lo que sabemos (`docs/20`): la falla de **hombre-muerto (`1.06`) se borra reiniciando el equipo**
> — ésa es segura. Lo que **no** sabemos: si las fallas del **nodo 4 (dirección)** se borran con un
> ciclo de llave o exigen Judit.
>
> **Gate:** mientras no se sepa cómo se borra una falla de dirección, el **Track B (timón) solo se
> hace en el 122** (nuestro). En el 118 se hace **Track A (marcha)** —cuya falla peor, el
> hombre-muerto, se borra reiniciando— y **nada del timón**. Si antes de la visita se confirma cómo
> se borra la del nodo 4 (o que se va sola al apagar), entonces sí entra el Track B en el 118.

---

## Antes de tocar nada — baseline con el equipo ORIGINAL

Prueba que el equipo funciona HOY, para saber que lo que veamos después es nuestro, y para tener
contra qué restituir.

- [ ] **Foto de frente de cada conector** antes de desconectarlo: sensor del timón, multipiloto,
      pedal. Es el mapa para restituir idéntico.
- [ ] El **timón real mueve la rueda** (anotar sentido). El **multipiloto real maneja** marcha y
      funciones. Línea base.
- [ ] Escucha pasiva del bus **0 errores** antes de cualquier cosa (como siempre).
- [ ] Si no se hicieron en este equipo: las 4 mediciones de referencia contra **negativo de
      batería** (`docs/16`): negativo↔chasis, pin 6, CAN_H/CAN_L en reposo ≈ 2.5 V. 5 minutos.

---

## Track A — Multipiloto (marcha + funciones)   ← este sí en el 118

Comandar la marcha reemplazando el multipiloto real por el **repuesto instrumentado** (ESP32 + TJA,
impersona el nodo 2). El repuesto es el que ya se abre y se cablea en banco (`docs/20` §ruta B); su
conector enchufa en el zócalo del 118 sin tocar el mazo.

1. [ ] Repuesto **validado en banco antes de viajar** (control de falsación: sin puente, sin eco).
2. [ ] Escucha previa 0 errores.
3. [ ] **Desconectar el multipiloto original** del 118. Guardarlo a la mano.
4. [ ] **Conectar el repuesto** (su conector al zócalo del equipo). Un solo nodo 2 en el bus a la vez.
5. [ ] Llave ON. ¿El Maestro acepta el nodo? ¿Pide el hombre-muerto? (En banco, al comando `a 100`
       el Maestro pidió el pedal — señal de que la orden se tomó como real.)
6. [ ] Con hombre-muerto habilitado por el Chino y equipo en condiciones: probar **marcha adelante/atrás**
       suave, y barrer el **vocabulario de funciones** que falta confirmar (lift / sideshift / reach /
       tilt) — cuál COB-ID/bit mueve cada una.
7. [ ] **Restituir:** quitar el repuesto, **reconectar el multipiloto original**, confirmar baseline
       otra vez (el multipiloto real vuelve a manejar). Si quedó alguna falla, **reiniciar** el equipo.

**Ante cualquier falla:** volver al multipiloto original de inmediato y anotar el código antes de
reiniciar.

---

## Track B — Timón (dirección)   ← solo si pasó el gate; si no, va al 122

Comandar la dirección desconectando el sensor del volante y enchufando los **4 cables** del emulador.
El detalle paso a paso está en **`herramientas/emulador_timon/runbook_prueba_equipo.md`**. Resumen:

1. [ ] Emulador **validado en banco** (ya lo está, 27-oct) y dando salida válida ANTES de desconectar.
2. [ ] Rueda directriz **en gato**.
3. [ ] **Desconectar el sensor del timón.** Enchufar: **verde** y **café** (señales), **amarillo** →
       GND común del emulador, y tomar **+11 V del blanco**. (El TJA/CAN **no** se conecta para esta
       prueba — la retroalimentación es la rueda y el display.)
4. [ ] Confirmar con retro-sondeo verde ≈ 4.45 V / café ≈ 2.47 V con la GUI en θ=0 **antes** de que
       el nodo 4 lea.
5. [ ] ¿El nodo 4 acepta sin falla? Si sí, mover el timón de la GUI despacio (θ barre) y **ver la rueda
       girar**. Comparar sentido contra el baseline.
6. [ ] **Restituir:** quitar los 4 cables, **reconectar el sensor original**, confirmar que el timón
       real vuelve a mover la rueda.

**Ante cualquier falla de dirección:** sensor original de vuelta **de inmediato** (puede engancharse
y no tenemos cómo borrarla — ver Regla cero).

---

## Orden dentro de la ventana

- Priorizar lo que **el 122 no puede dar**: un equipo que enciende y se mueve. Eso es, sobre todo,
  **marcha real del Track A** y el **vocabulario de funciones**.
- **Un track a la vez. Restituir entre cada uno.** Nunca dejar dos cosas desconectadas al mismo tiempo.
- Coordinar con los mecánicos: hacer las pruebas sin estorbar el preventivo, y dejar el equipo listo
  antes de que lo necesiten de vuelta.

---

## Restitución final — checklist de salida

- [ ] Multipiloto original reconectado · sensor del timón original reconectado · pedal intacto.
- [ ] Fotos de cada conector comparadas contra las del baseline: todo igual.
- [ ] **Sin códigos de falla activos.** Si quedó alguno, reiniciar; si no se va, avisar a Miguel
      ANTES de que el equipo salga — no se manda al cliente con una falla silenciada.
- [ ] Escucha final 0 errores. Equipo como llegó.

---

## Lo que esta visita deja (para registrar en el repo)

- Marcha comandada en equipo real (no solo banco): ¿se movió? ¿con qué comando?
- El vocabulario de funciones del multipiloto: qué mueve cada bit/COB-ID.
- Si entró el Track B: sentido timón↔rueda, ¿coincide el signo de θ?, y si el nodo 4 aceptó la señal.
- Vueltas de timón tope a tope contadas a mano (corrige el 5.5 de `0x2414` / el 2.6 del Obed).
- **Cómo se borra una falla del nodo 4** — si se averiguó, es lo que abre el Track B en equipos de cliente.
