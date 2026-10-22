# Gameplan de la intervención — sensores, multipiloto, pedal y timón

**Escrito el 02-oct-2026.** Cómo se ejecuta lo de `docs/20` (qué reglas respetar al simular
cada mando). Cuatro secciones, en el orden en que conviene hacerlas.

---

## Lo que dijo el chino el 02-oct, y lo que cambia

Se le preguntó específico. Respuesta: **en los EDR18N2 usaba ese cable FTDI**, y el DB9
**no sirve para manejar, pero sí para leer los sensores**.

Eso le da de nuevo peso a la lectura **serie** del DB9 en este modelo, y pone en tensión el
pinout CAN `X200`, que salió de **otro** modelo (el ECR). No se tira ninguno: el `pin 3 ↔ pin 8`
lo decide para este equipo.

**Y hay una hipótesis que une todo**, anotada como hipótesis:

> El DB9 de este equipo dependía de un **módulo** que lo alimentaba y le daba tierra — el
> manual nombra el módulo de acceso **`6U10`** (conectores `X680`/`X681`), con un pin
> *«U-ISM out (24V) for JUDIT»*, y el pin 6 del DB9 cuelga justo del fusible **`4F15`,
> «autorización de acceso»**. **Si ese módulo se canibalizó entre el 18 y el 30 de
> septiembre**, explica a la vez: el −14.6 V de un transmisor vivo el 18-sep, el silencio y
> la falta de tierra el 30-sep, y que el cable del chino funcione en los otros EDR18N2.

**Cómo se prueba, barato:** preguntar qué se sacó de esta máquina después del 18-sep, y buscar
el `6U10` y sus conectores `X680`/`X681`. Si están vacíos, ya se sabe por qué el DB9 calla.

---

## 1 · Leer los sensores — las maneras que hay

| # | Manera | Qué da | Qué cuesta | Estado |
|---|---|---|---|---|
| a | **El DB9, como el chino** (serie, protocolo de Judit) | todo lo que Judit ve | que esté vivo el módulo de atrás, y descifrar un protocolo cerrado | mudo en este equipo |
| b | **Escuchar el bus CAN** (por una toma del bus: DB9 si es CAN, conector del `1U16`, o el del CanCode) | velocidad, ángulo y altura **si viajan por el bus**, y lo que manda el operador | encontrar el par CAN; solo escuchar | `escucha_can.ino` listo |
| c | **La pantalla, en *Diagnose*** | los valores, ya en unidades | grabarla con el teléfono o una cámara | **funciona hoy** |
| d | **En paralelo, en el conector de cada sensor** (ADC del ESP32 en un arnés en Y) | la señal cruda, sin intermediarios | un arnés por sensor; entrada de alta impedancia | se arma con las secciones 3 y 4 |
| e | **Sensores propios** (encoder de rueda, IMU, sensor de altura) | lo que haga falta, sin depender del equipo | comprar y montar | para la autonomía, no para el hito |

**Para el hito del teleop no hace falta leer sensores**: lo maneja un humano mirando. La
lectura es para **validar** lo que hacemos (que el timón simulado mueve la rueda lo que
pedimos) y para la autonomía después.

**El orden que conviene:** **c** ya, como verdad de referencia → **d** con cada intervención
(sale casi gratis, porque el arnés en Y es el mismo) → **b** cuando se encuentre el par CAN
→ **a** si se resuelve lo del módulo → **e** para la autonomía.

---

## 2 · El multipiloto — primero, porque hay uno de repuesto

### 2.0 · Antes del repuesto: leer el que ya está puesto (agregado el 03-oct)

maje preguntó si no se podía averiguar todo del multipiloto instalado, e incluso enchufar
su conector directo al ESP32. **Lo primero sí, y va antes. Lo segundo todavía no.**

**Lo que se sabe de su conexión, del manual:** que es el **nodo 2**, CANopen a 250 k, y que
va al lado del `1U16`. **No se sabe** qué conector es, cuántos pines tiene, de cuánto se
alimenta, ni si lleva el **terminador** del bus adentro.

**Por qué enchufar su conector al ESP32 no es tan simple.** Eso es el peldaño 5 de
`herramientas/pendientes.md`, y para que el maestro lo acepte el ESP32 tendría que imitar
todo, no solo las palancas:

- **El maestro interroga al multipiloto al arrancar.** El evento `6.71` sub 2: «el maestro
  lee […] el **tipo de piloto** de la EEPROM del piloto»; el sub 1 revisa las **versiones de
  software**. Hay una conversación SDO al encender, y el imitador tiene que contestarla
  igual
- **Las tramas tienen que llegar a tiempo**: si no llega un PDO en 3.5 ciclos, hay falla
  (evento `8.08`, el de recepción)
- **Y si el terminador está en el multipiloto**, desenchufarlo deja el bus con un solo
  120 Ω y empieza a fallar todo, no solo el mando

Nada de eso se adivina. **Se graba del multipiloto instalado, solo escuchando** — y la
conversación del arranque **solo se puede grabar de ese**, porque hace falta el maestro
para que exista.

```
□ 2.0.1  Foto del conector del multipiloto, de frente. Contar pines, buscar número de parte
□ 2.0.2  Batería fuera, escala de 200 Ω, por atrás del conector puesto:
           buscar el par que dé ≈ 60 Ω → ese es CANH / CANL
           desenchufado, del lado del multipiloto: ¿≈ 120 Ω? → lleva terminador adentro
□ 2.0.3  Llave ON, puntas de retro-sondeo contra el NEGATIVO DE BATERÍA:
           alimentación (¿24 V? ¿12 V?) y CANH / CANL en reposo ≈ 2.5 V
□ 2.0.4  Escucha CAN (LISTEN_ONLY) en ese par, y RECIÉN AHÍ dar llave:
           → boot-up 0x702, NMT del maestro, y el intercambio SDO 0x602 / 0x582
□ 2.0.5  Con la escucha corriendo, un mando por vez, anotando la hora de cada uno:
           cada palanca de tope a tope, cada botón, y nada por 10 s entre uno y otro
           → qué ID cambia (0x182, 0x282…), qué bytes, y cada cuánto se repite
□ 2.0.6  Diagnose del multipiloto en la pantalla, grabada, para cruzar valores
```

Esto **no necesita pedales ni que el equipo ande**: el multipiloto transmite igual con los
`E0106` activos. Y **no transmite nada**: es el peldaño 1.

**Qué cambia en el plan:** el repuesto sigue sirviendo para la ruta B (inyectar por
adentro), pero **ya no hace falta para hacer el diccionario** — sale del instalado. Con la
grabación del 2.0 se decide la ruta: si la conversación de arranque es corta y las tramas
son pocas, el imitador (peldaño 5) es más limpio que abrir el repuesto. Si es un enredo, ruta B.

### 2.0b · La palanca es Hall, sin contacto (05-oct) — propuesta, no decisión

Al abrir el repuesto apareció un **imán en el pivote** y la tarjeta encima: la palanca se lee
por **sensores Hall soldados**, no por un potenciómetro con cables. Los «2 canales de DAC por
palanca» del 2.6 **no tienen dónde enchufarse**. Lo que queda, ordenado:

| Ruta | Qué es | A favor | En contra |
|---|---|---|---|
| **A · Servo en la palanca** | un actuador mueve el mango; los botones, por un arnés en el conector de la empuñadura | **cero riesgo de plausibilidad**: los sensores reales, con su redundancia, miden un movimiento real. Reversible. Sirve hasta con el multipiloto original | montaje mecánico; si se corta la energía, la palanca **tiene que poder volver sola al centro** (servo que no frene, o acople que se suelte) |
| **B · Imitar al nodo por el bus** (peldaño 5) | el ESP32 manda las tramas del multipiloto, y el multipiloto se desenchufa | lo más limpio y lo que escala (NRE una vez por modelo). No toca el fierro | necesita la grabación del 2.0 y contestar la consulta de arranque (`6.71`). Es transmitir en el equipo |
| **C · Inyectar en la salida del Hall** | levantar la pata de salida del sensor e inyectar ahí | en el repuesto se permite | **depende del chip**: si la salida es digital (SPI, PWM, SENT) no hay DAC que valga. Se decide leyendo la marca |

**Propuesta:** **A para el hito del teleop**, porque funciona sin entender ningún protocolo, y
**B en paralelo** con la grabación del 2.0, para reemplazar a A cuando se entienda el bus. **C
solo si la marca del chip dice salida analógica.**

### 2.1 en adelante · El repuesto

**Objetivo:** que el ESP32 apriete los botones y mueva las palancas **del repuesto**, por
adentro, y que su electrónica siga armando las tramas CAN. Ruta B.

**Ventaja enorme de empezar acá:** **todo se hace en el banco**, sin el montacargas. Y en el
banco se puede transmitir: es nuestro repuesto, no el equipo.

```
□ 2.1  Traerlo de Las Palmas. Fotos de todo antes de abrir
□ 2.2  Abrirlo. Foto de la tarjeta por los dos lados
□ 2.3  Encontrar en la tarjeta:
         · el TRANSCEPTOR CAN (chip de 8 patas: 82C250, TJA1050, SN65…).
           Sus patas 6 y 7 son CANL y CANH: seguir la pista hasta el conector
         · el REGULADOR: por dónde entra la alimentación, y de cuánto
         · cada BOTÓN: confirmar que es doble, NC + NA (regla 1 de docs/20)
         · cada PALANCA: cuántos cables y qué tipo de sensor. Si son dos señales,
           medirlas: ¿suman ~5 V? (regla 2)
□ 2.4  Alimentarlo en el banco (fuente regulada, al voltaje que diga el regulador,
       con límite de corriente bajo)
□ 2.5  Conectarle la cadena CAN del TJA + 120 Ω en cada punta
       · si solo manda un «boot-up» (0x702) y heartbeat: está en pre-operacional.
         Mandarle NMT START desde el ESP32 — en el banco se puede
       · mover cada palanca y botón: anotar QUÉ TRAMA CAMBIA y CÓMO
       → Eso es el diccionario del multipiloto. Sirve también para el plan del bus
□ 2.6  Inyectar por adentro, en paralelo, SIN quitar nada:
         · botones: relé DPDT o par de interruptores analógicos complementarios
         · palancas: 2 canales de DAC por palanca, V2 = 5 V − V1
       y verificar en el log CAN que la trama es IGUAL a la de la mano
□ 2.7  Recién ahí, al equipo: se cambia el original por el repuesto
```

**Control de falsación del 2.6:** con el ESP32 apagado, el repuesto tiene que seguir
funcionando con la mano. Si no, la inyección está mal hecha.

---

## 3 · El pedal — hombre muerto

> **Corrección del mismo día: probablemente no es UN pedal.** Esta sección se escribió con
> lo que decía `CLAUDE.md` («hay pedal de hombre-presente»). maje preguntó si no son dos, y
> el manual de servicio del ETR le da la razón al menos en la pieza: en *Especificaciones
> técnicas* (pág. 10, edición 06.14) aparece un **«pedal doble»** — un solo conjunto con dos
> placas y **sensores** propios (`herramientas/componentes/pedal_doble-015.png`). Y el evento
> `1.13` nombra el «pedal doble» entre los mandos de **sentido de marcha**.
>
> **Qué hace la segunda placa no se sabe todavía.** Candidatos, sin elegir: freno dosificado
> (sería analógico, regla 2 de `docs/20`), un segundo contacto de hombre muerto, o sentido de
> marcha. **Se decide mirando el equipo**, no el manual:
>
> ```
> □ Preguntarle a un operador qué hace cada pedal
> □ Diagnose con cada pedal pisado y suelto: qué valor cambia
> □ En el conector, batería fuera: ¿contactos (NC/NA) o dos voltajes que suman ~5 V?
> ```
>
> Lo de abajo vale para la placa de **hombre muerto**. La otra se planifica cuando se sepa
> qué es.

> **Y el 02-oct: a este equipo le sacaron los pedales.** Explica los códigos activos
> **`E0106.01/.02`, hombre muerto**, que ya estaban en `herramientas/pendientes.md`: no hay
> pedal, así que el equipo ve el hombre muerto como no plausible. Lo que cambia:
>
> - **No se puede medir el pedal acá.** Se mide en otro EDR18N2 (los del chino), o se
>   recupera el pedal de donde haya ido
> - **El conector del lado del equipo quedó libre.** Es justo donde se enchufa nuestro relé:
>   para el hombre muerto no hace falta arnés en Y ni selector, se enchufa directo
> - **El pinout del lado del equipo** (cuál pin alimenta, cuáles son las entradas NC y NA) se
>   saca midiendo con la llave en ON y comparando con un EDR18N2 que tenga pedal
> - El sensor del pedal doble tiene número de parte en el manual: **`51297587`**. Sirve para
>   buscarlo o pedirlo

**Objetivo:** que el «pie» sea un **relé DPDT** manejado por el ESP32, y que **ese relé sea
el watchdog**: si se corta el latido, cae, y el equipo ve «pedal suelto».

```
□ 3.1  Foto de frente del conector del pedal
□ 3.2  Batería fuera, conector suelto, óhmetro (escala, no pitido):
         pisar y soltar → identificar el par NC y el par NA
□ 3.3  Conseguir el par de conectores (macho y hembra) del mismo modelo
□ 3.4  Arnés en Y con SELECTOR FÍSICO manual / teleop:
         manual  → el pedal real pasa directo, el equipo queda de fábrica
         teleop  → el relé DPDT reemplaza los dos contactos
□ 3.5  Banco: watchdog del bloque 1.1 de docs/17 manejando el relé.
         Sus seis pruebas de falsación, incluido SIGSTOP
□ 3.6  Equipo, selector en MANUAL: arranca y no aparece ningún evento nuevo
□ 3.7  Equipo, selector en TELEOP: el ESP32 «pisa»; matar el latido →
         tiene que volver a «suelto» antes de 200 ms, sin evento 1.06
```

**El evento a vigilar es el `1.06`.** Si aparece, el relé tardó más de lo permitido o los
contactos quedaron en `0/0` o `1/1`. En el hombre muerto **solo se borra reiniciando**.

---

## 4 · El timón — seno / coseno

**Objetivo:** dos canales de DAC que generan `A = Vo + Va·sen θ` y `B = Vo + Va·cos θ`, con θ
acumulándose como el control Obed.

**Buena noticia:** la dirección es eléctrica (EPS). **El equipo no anda, pero el timón sí
gira la rueda.** Toda esta sección se valida con el equipo quieto.

```
□ 4.1  Foto de frente del conector del sensor del volante
□ 4.2  Llave ON, arnés en Y o puntas de retro-sondeo, ADC del ESP32 grabando
       (con divisor si la señal pasa de 3.3 V), contra el negativo de batería:
       girar el volante DESPACIO de tope a tope
         → Vo, Va, si de verdad es seno/coseno, y cuántas vueltas son
       (corrige el 2.6 del simulador; el manual dice 5.5)
□ 4.3  Mismo giro con la pantalla en STEER → Diagnose, grabada:
       qué número muestra contra lo que mide el ADC
□ 4.4  Banco: el DAC genera seno/coseno y el ADC lo lee de vuelta.
       Verificar el círculo: (A−Vo)² + (B−Vo)² constante
□ 4.5  Arnés con SELECTOR manual / teleop, igual que el pedal
□ 4.6  Equipo, selector en TELEOP, volante real sin tocar:
       mover θ despacio → la rueda tiene que girar lo mismo que con el volante
       vigilar los eventos 1.54, 1.55 y 1.56
□ 4.7  Recién con el 4.6 limpio, subir la velocidad de giro
```

---

## El hardware que hace falta

| Qué | Para | Nota |
|---|---|---|
| **MCP4728** | DAC de 4 canales, 12 bits, I²C | 2 para el timón + 2 para la palanca de traslación. Es el «DAC de cuatro canales» de `CLAUDE.md` |
| Relés **DPDT** | pedal, sentido, claxon | uno por mando doble |
| Pares de conectores originales | arneses en Y | identificar por foto, de frente |
| Fuente de banco con límite de corriente | alimentar el multipiloto suelto | |
| Puntas de retro-sondeo | medir sin pinchar aislante | ya las pedía `docs/11` |

## Reglas que no cambian

- **El hongo físico siempre en serie**, y alguien al lado
- Laptop **a batería** cuando el ESP32 esté conectado a señales del equipo
- **Nada se corta**: arneses enchufables y selector manual / teleop
- **En el equipo no se transmite por el bus.** En el banco, con el repuesto, sí
- Un mando a la vez. No se pasa al siguiente con un evento sin explicar

---

## 19-oct · Runbook para i3 — del log al equipo, en orden

Consolida la sesión del 19-oct. **Reencuadra la ruta:** el DB9 es CAN y el comando del
multipiloto viaja por PDO (`0x182`), así que **tracción + sentido de marcha + hidráulica se
comandan imitando el nodo 2 por el bus**, no cortando Hall. La sección 2 de arriba (DAC sobre
Hall para la palanca) queda como **plan B** para lo que resulte NO ser CAN. El enable del pedal
se resuelve con el **puente de Miguel** (ver `componentes/LEEME.md`), no emulando el sensor.

**Equipo en gato, sin mangueras. El hombre-muerto SIN puentear en los pasos 0–3: nada se
mueve. El puente solo entra en el paso 5, con paro en mano.** Cada paso trae su control de
falsación: si la prueba no puede fallar, no midió nada.

```
0 · LAPTOP — el período real (no necesita el equipo)
  □ periodo_182.py sobre el .log del 06-oct → período del 0x182, del heartbeat, veredicto SYNC
  □ hornear esos números en banco_imitador/multipiloto_falso.ino (reemplazan los supuestos)

1 · ESCUCHA, joystick intacto (LISTEN_ONLY en el DB9)
  □ escucha_can + grabar_can, mover el joystick con acciones marcadas → línea base
  □ confirmar el decode de multipiloto.md y QUÉ nodos reaccionan (tracción, 0x20A, 0x303)
  □ ¿el master lee 0x1018 (identidad) en el boot además de 0x1000? decide si hay que
    falsificar identidad, no solo el tipo de equipo

2 · CORTAR 2/3, multipiloto enchufado (los 5 cables intactos = variable congelada)
  □ prender y anotar: ¿prende el equipo? ¿la pantalla vive? ¿sale 8.08 / EMCY 8250?
    ¿el resto del bus sigue hablando en el DB9?
  □ LECTURA: el 8.08 confirma que el PDO del joystick era COMANDO, no telemetría — el manual
    dice que un consumidor falla + emergencia si no recibe el PDO en 3.5× su ciclo
  □ control de ramal vs eslabón: si el bus queda MUDO, el multipiloto era eslabón del tronco
    (no ramal) → resoldar y repensar. Si el bus sigue → era ramal, vas bien
  □ si NO prende NADA → el boot por CAN está enredado con el arranque; el paso 3 pasa a ser
    necesario para encender, no solo para limpiar la falla

3 · NUESTRO NODO imita al multipiloto (TJA nuevo, lado MASTER del corte)
  □ multipiloto_falso con el período real y arranque-en-cero (regla 4 de docs/20)
  □ power-cycle con el nodo presente desde el boot (así cacha la lectura de 0x1000)
  □ ¿se limpia el 8.08? ¿Diagnose muestra los valores que inyectás (a 100, n...)?
  □ control: desconectar nuestro TX → el 8.08 tiene que VOLVER

4 · LA DIRECCIÓN — ¿CAN o Hall? (la incógnita que falta de los actuadores)
  □ ANTES del DAC seno/coseno de la sección 4 de arriba: escucha en el bus mientras alguien
    gira el volante DESPACIO (equipo habilitado). ¿Aparece una trama que cambia con el ángulo?
      sí  → la dirección es CAN, se inyecta como el multipiloto. La sección 4 (Hall) NO aplica
      no  → es Hall; recién ahí vale el DAC seno/coseno de la sección 4
  □ vigilar los eventos 1.54 / 1.55 / 1.56

5 · RUEDA EN EL AIRE (la prueba del comando) — solo con 0–3 limpios
  □ puente del pedal PUESTO (diagrama de Miguel; respeta NC+NO, NO es un corto bruto)
  □ paro físico en mano, gato verificado, despejado de la rueda motriz
  □ inyectar tracción pequeña (marcha lenta) → ¿gira la rueda en el aire?
      sí → CAN es el actuador de tracción, confirmado en el fierro
  □ sacar el puente al terminar: puesto, es el interlock gratis que se va
```

### Paso 0 y la pregunta del paso 1 — HECHOS en la i3, 19-oct

`periodo_182.py` sobre los logs del 06-oct (5 logs a 921600 con el joystick, ~600 s; el de
115200 perdía tramas y se descarta):

| Trama | Período (mediana) | Medio | Lectura |
|---|---|---|---|
| `0x182` TPDO1 multipiloto | **20 ms** | 20.04–20.17 ms | 49.8 Hz |
| `0x080` SYNC | **20 ms** | 20.02–20.13 ms | el Master lo manda |
| `0x702` latido multipiloto | **100 ms** | 100.0–102.1 ms | **no 500** como se supuso |

**99–100 % de los `0x182` salen dentro de 3 ms detrás de un SYNC: el PDO es SÍNCRONO.**
`multipiloto_falso.ino` ya lo hace así (`POR_SYNC = true`: manda `0x182` al recibir cada
`080`, latido cada 100 ms). Sin SYNC no sale ningún `0x182`, igual que el real: en el banco,
`master_falso` con **`y 20`** (no `y 10`: el equipo usa 20 ms).

**¿El Master lee `0x1018` (identidad) en el arranque? NO.** En los 3 arranques grabados, lo
único que el Master le pide al nodo 2 es `0x1000`, y siempre igual:

```
602 40 00 10 00 …        lee 0x1000
602 80 00 10 00 00 00 04 05   el Master aborta: timeout SDO (el multipiloto bootea tarde)
602 40 00 10 00 …        reintenta
582 43 00 10 00 00 00 00 00   responde: tipo de equipo = 0x00000000
702 00                   boot-up
000 01 02                NMT START
```

3 de 3 arranques idénticos. **No hay que falsificar identidad**, solo `0x1000 = 0`, que
`multipiloto_falso` ya contesta. (Con ~23k tramas perdidas por el serie es posible que se
escape algo; tres arranques iguales lo hacen poco probable.)


### 22-oct · Paso 2 en el equipo: el corte del 2/3 y el multipiloto de repuesto

Cable del DB9 con `escucha_can` (LISTEN_ONLY). Logs `escucha_equipo_20261022-100420` (corte) y
`-101009` (repuesto completo).

**Con el repuesto enchufado y los pines 2/3 DOBLADOS:** pantalla oscura. En el bus:

| s (ESP32) | Qué | Lectura |
|---|---|---|
| 144–152 | solo `703` (pantalla), ~1540/s | sola en el bus, sin ACK, reintenta |
| 152 | boot-up de 4, 7, 8, 30 (+4 tramas `6xx 0E 00…` sueltas, basura del encendido) | llegan nodos; `703` baja a cada 100 ms |
| 153–176 | solo `703 7F` | **ni Master (701), ni SYNC, ni NMT** |
| 177 | `703` vuelve a reintentar sola | los otros nodos se apagaron a los ~25 s |

**Con los pines reparados (repuesto completo): pantalla prende.** El repuesto **funciona**:
boot-up `702 00`, `0x1000` abortado una vez y contestado `43 00 10 00 00 00 00 00` (idéntico
al original del 06-oct), latido 100 ms, `0x182` detrás del SYNC. El pito estaba trabado:
**bit `0x01` de b4 = pito** (antes «botón trasero»).

**Lo que no cuadra:** el Master manda su boot-up `701 00` ANTES de hablarle al multipiloto
(hoy: `701` a 282945, `602` a 282948). Con el corte no salió nunca → **el Master no estaba
encendido**, no esperando al multipiloto por el bus. Sospechosos:
1. **los pines doblados** — maje tuvo que repararlos; si tocaron otro pin, el corte no fue limpio
2. **el multipiloto apaga sus salidas (1, 6, 9, 10, 13) si queda solo en su lado del CAN**
   (sin ACK reintenta su boot-up sin fin y puede entrar en falla), y el Master cuelga de una

**Cómo se separan:** repetir el corte SIN doblar (cinta/funda en 2 y 3, o pigtail) y, llave ON,
medir 1, 6, 9, 10, 13 contra el negativo; comparar con el 19-oct (16–17 / ~0.8 / ~9 / 5.2 /
12–22 V). Salidas presentes y Master ausente → otra causa. Salidas ausentes → sospechoso 2, y
el arreglo es un nodo nuestro del lado del multipiloto que le dé ACK (la pasarela, con el
MCP2515 de ese lado).

> **Resuelto la misma tarde (ver abajo):** ninguno de los dos sospechosos. El mazo **no
> puentea** 2↔4 ni 3↔5: el tronco del bus pasa **solo por adentro del multipiloto**. Doblar
> 2/3 partía el bus en dos (DB9 + controladores de un lado, Master del otro). Por eso el DB9
> no veía al Master.


### 22-oct tarde · RUTA B: el Master acepta nuestro nodo 2 — teleop 1/3

**Topología** (medida por maje): el bus es una cadena; el multipiloto es un eslabón (entra por
2/3, sale por 4/5, puenteados por dentro). Segmento 2/3 = DB9 + controladores (3/4/7/8/30);
segmento 4/5 = Master (nodo 1). **El mazo no puentea 2-4 ni 3-5.**

**Armado:** multipiloto de **repuesto** enchufado solo para alimentar (1, 6, 7, 8, 9, 10, 13;
**2, 3, 4, 5 fuera**: su transceptor sale del bus) + **puente en la ficha hembra del mazo, 2↔4
y 3↔5** (verificado con óhmetro) + ESP32/TJA en el DB9. Equipo en gato, sin sensor de pedal.

**Prueba 1 — escucha** (`escucha_can`, fijo a 250k; log `escucha_equipo_20261022-140856`):

- **La pantalla prende** con las 5 salidas del multipiloto y su CAN fuera ✓
- **El Master aparece**: boot-up `701 00`, latido `701 05`, SYNC cada 20 ms, PDO de todos.
  **El puente reconecta el tronco ✓**
- Pide `0x1000` al nodo 2 dos veces y **aborta las dos** (`602 80 … 00 00 04 05`, timeout SDO);
  igual manda NMT START a 2
- **La pantalla muestra `E4809.01`**: lo manda el Master por `203` (texto ASCII). Es la familia
  del evento **8.09** («PDO no recibido en 3.5× su ciclo») = **falta el nodo 2**
- Una corrida anterior dio 0 tramas / 0 errores durante 5 min (log `-134922`, con barrido). **Sin
  explicar**; la repetición sin barrido y con la llave subida de nuevo oyó todo. Anotado

**Prueba 2 — nuestro nodo 2** (`multipiloto_campo` + `campo_nodo2.py`; log
`campo_nodo2_20261022-141854`). Armado con la llave OFF, power cycle con el nodo desde el boot:

| | Sin nuestro nodo (prueba 1) | **Con nuestro nodo** |
|---|---|---|
| `0x1000` al nodo 2 | 2 timeouts | 1.º timeout, el reintento **lo contestamos** `43 00 10 00 00…` |
| NMT START `01 02` | nadie | recibido → operacional; **TEC 0, REC 0**, ~4500 tramas aceptadas |
| Texto a la pantalla | `E4809.01` | **E4809: 0 veces** en todo el log |
| Mando `a 100` (`182 64 00 00 00 08 00 00 00`) | — | **aviso amarillo de hombre muerto** (`E1903.01`), solo mientras dura el mando |
| `a 0` | — | el aviso se va |

**El Master toma nuestro `0x182` como mando del operador**: pide el pedal igual que con el
multipiloto real. maje: sin el pedal el equipo da siempre `E190x`, con `x` según la función que
se intenta (en el manual: 9.02 elevación, 9.03 descenso, 9.04 viaje…). **La única razón por la
que no se mueve es el pedal.** El control de falsación es la prueba 1: la misma configuración
sin nuestro nodo da E4809.01.

**Siguiente (23-oct):** llega el sensor del pedal de hombre muerto → rueda en el aire (paso 5).
Antes de pisarlo, confirmar qué función hace cada mando (cada `E190x` lo dice: probar `a`, `t`,
`i`, `d` y botones sin pedal y anotar el código). La palanca trasera (`b2`, bits `0x40`/`0x20`)
todavía no tiene mando en `campo_nodo2.py`.


### 22-oct tarde · Paso 4: LA DIRECCIÓN ES CAN — `0x284` b3-b4

`visor_can.py` (tabla en su lugar, sobre `escucha_can`; log `direccion_20261022-150558`, 37 IDs,
0 errores, 0 perdidas). Mismo armado de la ruta B, **sin pedal, nada se mueve**: el volante
gira libre y solo mueve su sensor. Marcas: giro izq · centro (quieto) · giro der · centro.

| Ventana | `0x284` b3-b4 (int16 LE con signo) | Suma |
|---|---|---|
| reposo, 97 s | ±1 | 0 |
| **giro izq**, 23 s | **+9 … +27** (rampa suave: `0F 00`, `12 00`, `15 00`…) | **+8931** |
| quieto | ±1 | +3 |
| **giro der**, 28 s | **−8 … −40** (`DE FF`, `E0 FF`…) | **−21812** |

- **Un solo valor con signo, no seno/coseno en cuadratura.** Positivo = izquierda, negativo =
  derecha, el resto de los bytes en 0. Período ~20 ms (al ritmo del SYNC)
- **Es VELOCIDAD de giro, no ángulo:** vuelve a 0 apenas se suelta el volante, en cualquier
  posición. Cuadra con el volante sin topes (19-oct): el que integra es el controlador
- **Lo publica el nodo 4** (TPDO2, «Dirección 1»): el nodo 4 lee el volante. `0x184` del mismo
  nodo no reacciona (b4-b5 tiembla ±5 en reposo y girando). El RPDO `0x204` del Master al nodo 4
  queda fijo en `88 00 16 1A 00 00`
- **Corrige el 06-oct** («sin el pedal el timón no publica nada»): el `0x284` publica sin pedal.
  Lo que no cambiaba era el Diagnose de STEER
- **Consecuencia:** la sección 4 (DAC seno/coseno sobre Hall) **no aplica**; la dirección se
  inyecta por el bus, como el multipiloto. **Pregunta abierta:** el nodo 4 también publica
  `0x184` y otras tramas, y hay que saber quién consume el `0x284` (¿Master? ¿5/6?) antes de
  decidir si se imita el nodo 4 entero o se intercepta solo su TPDO2
- `0x2414` (vueltas de tope a tope) **no se leyó**: es SDO, o sea transmitir, y esta sesión era
  solo de escucha
