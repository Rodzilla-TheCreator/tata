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
