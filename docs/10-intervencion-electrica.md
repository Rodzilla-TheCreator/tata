# Intervención eléctrica del EDR18N2 — tres planes

Objetivo: teleoperar el equipo con un control de videojuego. **RT** acelera, **LT** frena,
**B/O** alterna el sentido y la dirección va en el stick. Nivel Ingenio: demostración
teleoperada con un dedo humano sobre un paro físico. **Nunca se le llama "freno automático" a nada de esto.**

**Antes de aplicar cualquiera de estos planes hay que hacer la visita de diagnóstico:
[`11-plan-de-diagnostico.md`](11-plan-de-diagnostico.md).** Los tres tienen bifurcaciones
que solo se cierran midiendo en el equipo.

Los tres planes comparten la misma topología. Vale la pena entenderla una vez.

---

## La topología común

El equipo ya tiene sensores analógicos que le dicen a su controlador qué quiere el
operador. No inventamos señales nuevas: **nos metemos en medio del cable que ya existe**.

```
   sensor original ──────────┐
                             ├── [SW] ── entrada del controlador del equipo
   DAC del Arduino ──[buf]───┘
                       ▲
                       └── [aislador] ── Arduino
```

Cuatro reglas que no se negocian:

1. **`SW` en reposo entrega el sensor original.** Sin alimentación, sin Arduino, sin
   firmware: el humano manda. Si algo se cuelga, el equipo vuelve solo a manual.
2. **Nunca un pin del Arduino directo al controlador.** Siempre DAC + búfer. Un pin
   digital conmutando a 5 V mete escalones que el controlador lee como falla.
3. **Todo aislado.** El bus del equipo es de 24–48 V con picos feos. Un ADUM1201 entre
   el Arduino y cualquier línea del equipo cuesta $2 y te salva la placa.
4. **El paro físico va en la cadena eléctrica, no en software.** Un hongo NC en serie
   con el hombre-presente. Si el Arduino se cuelga, el hongo igual detiene.

### El detalle que rompe todo si no lo sabés

Los controladores de montacargas casi siempre esperan **doble señal redundante**: dos
Hall en el mismo pedal, uno que sube y otro que baja, y comparan. Si vos inyectás una
sola y la otra no concuerda, **el controlador entra en falla y bloquea la marcha**.

Por eso el DAC tiene que ser de varios canales y hay que reproducir el par completo.
**Medí las dos señales antes de tocar nada** — si al mover el mando hay dos cables que se
mueven en sentido contrario, ahí está.

---

## El watchdog de 200 ms — quién vigila a quién

> **Esta sección se escribió el 18-sep-2026 para rescatar una decisión que se había tomado en
> conversación y no estaba en ningún archivo.** Lo único que existía era una línea de costo en
> `analisis/escala_edr.py`: «Custom con watchdog y doble bus, 1400». Los 200 ms, el latido y
> quién frena no estaban escritos. Lo que sigue tiene **lo decidido** y, marcado aparte, **lo
> que falta decidir**.

### La regla

**La Jetson le manda un latido al ESP32. Si pasan 200 ms sin latido, el ESP32 frena.**

### Por qué el ESP32 y no la Jetson

**Linux no garantiza tiempo.** El planificador del kernel, el recolector de basura de Python,
un swap, una ráfaga de carga del procesamiento de cámaras — cualquiera de esos mete cientos de
milisegundos sin avisar y sin que nada falle formalmente. Un sistema operativo de propósito
general no es determinista, y no se lo puede volver determinista a fuerza de cuidado.

Un microcontrolador sin sistema operativo corre el mismo lazo, siempre, en el mismo tiempo.
**El que cuenta los 200 ms tiene que ser él.**

Y la asimetría importa: el ESP32 **no confía** en la Jetson, la Jetson **sí depende** del
ESP32. El lado tonto vigila al lado listo, porque el lado tonto es el que se puede auditar
línea por línea.

### Las tres capas, que no se confunden

```
1. HONGO FÍSICO       NC en serie con el hombre-presente.  Puramente eléctrico.
                      Detiene aunque todo lo demás esté muerto o colgado.

2. WATCHDOG ESP32     Cuenta 200 ms sin latido → corta el hombre-presente con relé
                      → cae el freno electromagnético de resorte.
                      Supervisión de disponibilidad.

3. SOFTWARE JETSON    Percepción, localización, planificación, teleoperación.
                      Puede fallar, colgarse o mentir. Por eso existen 1 y 2.
```

> **El watchdog NO es la capa de seguridad certificada.** `CLAUDE.md` y `docs/04` lo dicen:
> **ISO 3691-4 exige que la capa certificada esté aislada de la navegación.** Un ESP32 con
> firmware nuestro no es un dispositivo de seguridad funcional y no se puede presentar como
> tal. Es **supervisión de disponibilidad** — vigila que el cerebro esté vivo, no que la
> maniobra sea segura. Confundir las dos cosas mete al proyecto en un problema de
> certificación que hoy no tiene.

### Cómo frena

Por la vía que `CLAUDE.md` ya identificó como **la que frena siempre**: cortar el
hombre-presente con un relé y dejar caer el **freno electromagnético de resorte**. No se usa
el freno regenerativo del controlador, porque ese depende de que el controlador esté sano — y
si el watchdog saltó, sano es justo lo que no sabemos que esté.

Es un freno **normalmente aplicado**: sin corriente, frena. Eso lo vuelve a prueba de que se
caiga la alimentación, y es lo que se quiere.

### Lo que falta decidir — marcado, para que no se pierda otra vez

| Pregunta | Estado |
|---|---|
| **Período del latido** | Abierto. Los 200 ms son el vencimiento, no el período. Regla de pulgar: latido cada 50 ms deja margen para perder tres seguidos antes de frenar |
| **Contenido del latido** | Abierto. ¿Basta un byte? ¿Lleva contador de secuencia para detectar mensajes viejos o repetidos? ¿Lleva CRC? Un latido sin contador no distingue «vivo» de «pegado» |
| **Por dónde va el latido** | Abierto. USB serie es lo simple. CAN es lo robusto y ya va a haber bus. Decidir después del diagnóstico |
| **Rearme** | **Decidido: manual.** Si vuelve el latido, el equipo **no reanuda solo**. Un sistema que se recupera solo de una falla que nadie diagnosticó vuelve a fallar con alguien adelante |
| **Qué más vigila el ESP32** | Abierto. Candidatos: hongo, hombre-presente, y si el bus CAN sirve, plausibilidad de velocidad contra lo comandado |
| **Frenar con carga en alto** | **Abierto, y es el más serio.** Soltar el freno de resorte a velocidad con el pantógrafo extendido en altura no es obviamente lo más seguro. Puede haber que rampar, o que el watchdog primero corte tracción y aplique el freno escalonado. **Requiere criterio mecánico — es pregunta para el Chino**, y se cruza con `docs/11` §4, los pasos que no se pueden reanudar a la mitad |

### Qué cambia si el puerto de servicio resulta ser CAN

**Nada de esto.** Sigue siendo el ESP32 el que cuenta y el que corta.

Lo único que cambia es **de dónde saca la información**: en vez de leer Hall crudos
interceptados, podría leer tramas CANopen del propio equipo. Eso lo abarata y lo hace menos
invasivo, pero **no mueve el watchdog a la Jetson ni lo vuelve software**.

---

## Plan 1 · Freno → LT

### Qué vas a encontrar

En un reach truck de operador parado el freno **casi nunca es un potenciómetro**. Lo más
probable es una de estas tres:

| Caso | Cómo se ve | Qué hacer |
|---|---|---|
| **A** · pedal de hombre-presente | interruptor digital, 2 hilos | relé en serie: soltar = frena |
| **B** · freno por el controlador | no hay sensor de freno; frena bajando el acelerador | LT actúa sobre el canal del acelerador |
| **C** · pedal analógico real | 3 hilos, señal 0.5–4.5 V | interceptar como el acelerador |

**El caso B es el más probable.** En ese equipo el freno de servicio es regenerativo: el
controlador frena cuando la consigna de tracción baja o se invierte. No hay nada analógico
que interceptar.

### El circuito — dos capas

**Capa 1 · freno proporcional (solo si es caso C)**

```
  pedal freno ─── señal ──┬──── DG419 (NC) ────── controlador
                          │
  MCP4728 canal C ──[MCP6002 seguidor]── DG419 (NO)
                                            ▲
                          Arduino D5 ──[ADUM1201]──┘
```

**Capa 2 · freno binario (siempre, en cualquier caso)**

Esta es la que de verdad frena, y es la más confiable que vas a tener:

```
  línea de hombre-presente ──── relé SPST NC ──── controlador
                                    ▲
                 Arduino D6 ──[ADUM1201]── driver ULN2003
```

Cortás esa línea y el freno electromagnético de resorte cae solo. Es el mismo mecanismo
que usa el equipo cuando el operador se baja. **No lo estás inventando: lo estás usando.**

Mapeo: `LT > 90%` corta el relé. Debajo de eso, proporcional si hay caso C.

---

## Plan 2 · Tracción → RT

### Corrección al plan original

**El EDR no tiene pedal de acelerador.** Es operador parado: hay un **pedal de
hombre-presente** (habilita, no dosifica) y la velocidad sale de un **mando de mano** en
la cabeza de control. En el video se ve al operador con la mano ahí, sin pisar nada.

La señal que buscás sale del mando, y es **bidireccional con neutro al centro**: típicamente
0.5 V full reversa, 2.5 V neutro, 4.5 V full adelante.

### El mapeo

| Control | Función |
|---|---|
| **RT** | acelerador, proporcional |
| **LT** | freno, proporcional |
| **B** (Xbox) / **O** (PS) | alterna sentido: adelante ↔ atrás |
| Hongo físico | paro, fuera del control |

El sentido es un **estado**, no un eje. Se alterna con un botón y se muestra en pantalla;
los dos gatillos siempre dosifican magnitud. Eso deja los dos ejes analógicos para lo que
de verdad necesita resolución, y evita el modo de falla de mapear reversa a un gatillo que
el pulgar puede rozar.

Regla de firmware: **el cambio de sentido solo se acepta con RT y LT en cero y el equipo
detenido.** Nunca invertir en movimiento.

### El circuito

```
  mando de mano ─┬─ señal A ──┬──── DG419 #1 (NC) ──── controlador
                 │            │
                 │  MCP4728 A ─[buf]─ DG419 #1 (NO)
                 │
                 └─ señal B ──┬──── DG419 #2 (NC) ──── controlador
                              │
                    MCP4728 B ─[buf]─ DG419 #2 (NO)
                                         ▲
                    Arduino D4 ──[ADUM1201]──┘  (una sola línea conmuta los dos)
```

**Las dos señales conmutan juntas, con el mismo pin.** Si conmutás una sola, el controlador
ve discrepancia y bloquea.

Rampa obligatoria en firmware: de neutro a full en no menos de 1.5 s. El DAC puede saltar
en un ciclo; el equipo no debe.

---

## Plan 3 · Dirección EPS

### Por qué este es distinto

El EDR sí es EPS, y eso lo hace viable eléctricamente — a diferencia de los
contrabalanceados de renta, que son hidráulicos y ahí no hay nada que interceptar con
cables.

EPS en reach truck es **steer-by-wire**: el volante tiene un sensor, el controlador lee esa
consigna y mueve un motor de dirección con su propia realimentación. O sea que no peleás
contra el motor, **suplantás la consigna del volante**.

Pero hay una bifurcación:

| Si el sensor del volante es | Entonces |
|---|---|
| **analógico** (pot o Hall, 3 hilos) | mismo circuito que el acelerador. Fácil |
| **encoder en cuadratura** (A/B) | hay que sintetizar pulsos y seguir la cuenta interna. Difícil |
| **CAN** | mandás tramas. Necesitás haber decodificado el bus primero |

**Averiguar cuál es, es el trabajo del primer día.** No compres nada específico de dirección
hasta saberlo.

### Circuito si es analógico

Idéntico al Plan 2, canal D del MCP4728, con una diferencia importante:

**Tope de consigna en firmware.** La dirección a 78° con el equipo en movimiento vuelca
carga. Limitá el ángulo comandado en función de la velocidad — sobre de velocidad de
1.5 m/s como dice el `CLAUDE.md`, y ángulo máximo inversamente proporcional.

### Circuito si es encoder o CAN — la salida mecánica

Si resulta encoder o CAN, la ruta más corta **no es electrónica, es un motor en la columna**:

```
  motor 24 V con reductora ── polea dentada ── columna del volante
             ▲
  BTS7960 ──┴── Arduino (PWM + dirección)
  AS5600 en la columna ── realimentación de ángulo real
```

Ventajas que no son obvias:

- **No tocás nada del equipo.** Ni un cable cortado, ni la certificación comprometida,
  ni Fabrizio enojado.
- **El humano gana siempre**: agarrar el volante vence al motor. Es una anulación física,
  no una lógica que puede fallar.
- Funciona igual sea analógico, encoder o CAN, porque no le importa.

Para demostración vale más que la intercepción eléctrica. Para producción no, pero
producción no es este año.

---

## Qué comprar

### En Steren (andá con esta lista)

| Cosa | Cantidad | Nota |
|---|---|---|
| Protoboard | 2 | una para banco, una para el equipo |
| Placa perforada | 3 | lo del equipo va soldado, no en protoboard |
| Relés SPDT 5 V señal | 4 | para el hombre-presente |
| Bornera de tornillo | 10 | nada de jumper suelto en una máquina que vibra |
| Termorretráctil surtido | 1 | |
| Diodos 1N4148 y 1N4007 | 20 c/u | volante de relés |
| Resistencias 1 k / 10 k | 30 c/u | divisores y pull-ups |
| Capacitores 100 nF y 10 µF | 20 c/u | desacople, obligatorio |
| Cable calibre 22 multifilar | varios m | multifilar, no rígido: vibración |
| Fusibles 2 A + portafusible | 5 | |

### Pedir en línea — lo que Steren no va a tener

| Módulo | Cant | Para qué | Crítico |
|---|---|---|---|
| **MCP4728** DAC 4 canales I²C | 2 | acelerador (par), freno, dirección | **sí** |
| **ADUM1201** aislador digital | 4 | Arduino ↔ equipo | **sí** |
| **DG419** switch analógico | 4 | conmutar humano ↔ robot | **sí** |
| **AS5600** encoder magnético | 3 | ángulo de columna, odometría | **sí** |
| MCP6002 opamp rail-to-rail | 4 | búfer del DAC | sí |
| DC-DC aislado 48→12 y 12→5 | 2 | alimentación | sí |
| **BNO085** IMU | 1 | rumbo con fusión a bordo | recomendado |
| Analizador lógico 8 canales | 1 | decodificar lo desconocido | **el que más te va a servir** |
| MCP2515 + TJA1050 | 2 | CAN, si resulta que hay | según lo que encuentres |
| Diodos TVS SMBJ | 10 | picos del bus | sí |
| Hongo de paro NC | 1 | no negociable | **sí** |

El **MCP4728 en vez de varios MCP4725**: un solo chip te da los cuatro canales que
necesitás, y el par redundante del acelerador te obliga a tener al menos dos que se muevan
juntos. Con MCP4725 sueltos hay que malabarear direcciones I²C.

---

## El primer día: no cortés nada

Llegá con los circuitos armados y **no los conectes todavía.** El primer día es medir:

1. **AS5600 pegado con cinta** a la columna del volante. No toca nada del equipo.
2. **Multímetro en el mando de mano**, con captura mín/máx. Anotá: reposo, full adelante,
   full reversa. Buscá el segundo hilo que se mueve al revés.
3. **Analizador lógico** en cualquier par que no sea claramente analógico. Si ves cuadratura,
   la dirección es encoder y ya sabés que vas por la ruta mecánica.
4. **Fotos de cada conector** antes de desconectarlo. Con el celular, con etiqueta.

Con eso volvés y en una tarde sabés cuál de los tres casos de cada plan te tocó. Ahí sí
cortás, y cortás una sola vez.

**Lo que no querés es llegar con el cautín caliente y descubrir que la dirección era CAN.**
