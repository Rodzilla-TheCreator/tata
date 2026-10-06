# Pendientes del puerto — cierre del 30-sep-2026

Lo vigente arriba. El detalle de cada cosa está en `serie/tabla_fusibles_de9.md`,
`manuales_scribd.md` y `docs/16`.

## ▶ SIGUIENTE PASO — la primera escucha en el equipo (06-oct-2026, para el próximo chat)

**Estado:** la cadena ESP32 + TJA1050 está **validada para escuchar** (ver `can/LEEME.md`,
sección 02 al 06-oct). `escucha_can.ino` **ya está cargado** en el ESP32. El plano vigente es
`can/armado_escucha.svg`. maje sale al equipo con este cable.

**Revisar en la mesa (USB desconectado, Ω):**
```
pin 6 del DB9 macho ↔ cualquier cable nuestro   → ABIERTO
pin 3 ↔ pin 8                                   → decenas de kΩ, nunca ~100/120
pin 8 ↔ CANH del módulo · pin 3 ↔ CANL          → ~0
TX del módulo ↔ GPIO 21                         → ABIERTO
```

**En el equipo:**
1. Laptop a **batería**. Llave en **OFF**. DB9: solo **8 (CANH) y 3 (CANL)**, **sin GND**,
   sin terminador, cables ≤ 30 cm
2. USB del ESP32 a la i3 (aparece como **COM6**, CP210x)
3. Grabar 10 min (abrir el puerto reinicia el ESP32: arranca de cero con el barrido
   250k / 500k / 125k):
   ```python
   import serial, time
   s = serial.Serial("COM6", 115200, timeout=0.5)
   f = open("escucha_equipo.log", "w", encoding="utf-8"); t = time.time()
   while time.time() - t < 600:
       d = s.read(8192)
       if d: f.write(d.decode("utf-8", "replace")); f.flush()
   ```
4. Paro de emergencia **arriba**, llave a **ON**. 30 s quieto → un **ciclo de llave** →
   menú de servicio → **Diagnose** (el display pide valores por el bus: deberían verse SDO
   `0x6xx` / `0x5xx`)

5. **Si a 250k entran tramas: el diccionario del multipiloto** (paso 2.0 de `docs/21`).
   Con la escucha corriendo, **un mando por vez**, anotando la **hora del reloj de la i3**
   de cada uno, y **10 s quieto** entre mando y mando:
   palanca adelante despacio y vuelta · atrás y vuelta · cada botón de la empuñadura,
   apretar y soltar. Eso, cruzado con el log, dice **qué ID y qué bytes** son de cada mando
6. Foto de la **etiqueta de la batería** (¿36 o 48 V nominales? el pin 8 midió 39.2 V)

**Cómo leer el resultado:**

| Sale | Qué significa | Qué sigue |
|---|---|---|
| tramas a 250k, pocos errores | el bus se oye. **Primer objetivo cumplido** | identificar nodos con la tabla de `manuales_scribd.md` (1 master, 3 display, 4 dirección, 7 elevación, 8 tracción…) |
| 0 tramas y **0 errores** | no llega señal | masa: **negativo de batería** con un cable aparte al GND del ESP32 (nunca del pin 2, 5, 6 ni 9). Después, CANH/CANL invertidos |
| 0 tramas y **muchos errores** | llega señal, no se decodifica | otra velocidad, o CANH/CANL invertidos (en listen-only cambiarlos no daña nada) |
| tramas con errores altos | ramal o terminación | cables más cortos; recién ahí evaluar 120 Ω en el DB9 (decisión de maje) |

**Lo que NO se hace:** transmitir, conectar los pines 5, 6 o 9, agregar terminador sin
decidirlo, cargar `prueba_can.ino` con el cable en el equipo (ese SÍ transmite).

**Datos de hoy que el próximo chat necesita:**
- El multipiloto **no trae terminador** (H–L abierto). El 120 Ω del bus está en otro lado
- `arduino-cli` de la i3: `C:/Users/Rodz/AppData/Local/Programs/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe`,
  placa `esp32:esp32:esp32` (core 3.3.11). Si COM6 da «Access denied», está abierto el
  monitor serie del IDE. Si la carga falla con «No serial data received», apretar BOOT

## Dónde quedó

- **El DB9 probablemente es CAN, no serie.** El pinout del conector de servicio
  `X200` de Jungheinrich (sacado de un ECR) cuadra con lo medido: pin 6 = +24 V por el
  fusible 4F15, pin 5 = GND conmutado (abierto con batería fuera). CAN_L en el 3,
  CAN_H en el 8, tierra del bus en el 2. **Es hipótesis: la tabla es de otro modelo.**
- Eso explica el silencio del FTDI, el eco deformado y el «no tiene tierra».
- **El menú de servicio del display funciona** (Settings → Settings + P-arriba → PIN).
  *Diagnose* muestra sensores en vivo. El PIN no se anota en el repo.
- Códigos activos: `E2325.01` temp. aceite, `E2320.01` sensor de presión A,
  `E2504.01/.02` salidas del control hidráulico, `E0106.01/.02` hombre muerto (pedal),
  `E0106.16` sin documentar.
- Fusibles: **5 A temporales en 4F15 y 6F9** (van 2 A). **10 A en 5F3, 3F11 y 4F10**
  (van 2 A según el manual; 3F11 es el control de dirección).

### Medido el 04-oct-2026 en el DB9 hembra del equipo

**Pin 3 ↔ pin 8 = 120 Ω.** Es una terminación CAN entre los pines que la tabla del `X200`
asigna a CAN_LOW (3) y CAN_HIGH (8). La hipótesis X200 pasa de «pinout de otro modelo» a
**medida en este equipo**. 120 y no 60: desde el puerto se ve un solo terminador (¿ramal?
¿bus con una sola terminación?) — anotado, sin elegir.

Consecuencia: **el cable de escucha no lleva terminador**. La 100 Ω es solo de banco.

### La cadena CAN en banco — 02/03-oct

- Sin conversor de nivel: TX directo (el TJA1050 acepta 2.0 V como alto) y RX por divisor 1k/2k
- El lazo funciona: self-test **10/10 a 25k**, 8/10 a 50k, 0/10 desde 100k
- Medido con el contador de ciclos: **bajada TX→RX 0.36 µs, subida ~15 µs**, igual con o sin
  terminación y con o sin conversor. A 250k el bit dura 4 µs: así no transmite
- El chip dice `TJA1050 NXP SX XJ D408`, pin S en 0 V (modo normal). Según la hoja de NXP el
  RXD empuja activo hacia arriba: 15 µs está fuera de lo que el chip debería hacer
- Pendiente: mediciones l–p (¿algo del módulo en las patas 1 o 4?) o cambiar a SN65HVD230
- Bug corregido en `prueba_can.ino`: faltaba `tx.self = 1` (Self Reception Request)
- La prueba de «lazo de pines» con TX pegado en bajo NO vale: el TJA1050 suelta el bus a los
  250–750 µs (time-out de dominante). Se mide con pulsos cortos

### La cadena queda validada PARA ESCUCHAR — 05-oct-2026

- **Control: el ESP32 solo.** GPIO21 → GPIO22 con un cable: 0.16 µs los dos flancos. La
  medición y el ESP32 están bien; los ~15 µs de subida los pone el módulo
- **Control positivo, el receptor.** GPIO25/26 → 100 Ω → CANH/CANL simulan otro nodo, con
  el TX del TJA1050 quieto: reposo RX = 1, dominante RX = 0, **bajada 0.40 µs, subida
  0.24 µs**, 500/500. El receptor sirve a 250k; lo lento es solo el transmisor del módulo
- **Control negativo.** `escucha_can.ino` en la mesa, sin bus: 5 min, **0 tramas, 0 errores**
- `prueba_can.ino` (self-test) **no va a pasar con este módulo**: necesita su transmisor.
  Eso ya no bloquea, porque en el equipo no se transmite
- **En el equipo, el TX del TJA1050 va SIN CONECTAR.** Su pull-up interno lo deja en
  recesivo: el módulo físicamente no puede transmitir, haga lo que haga el software
- Cadena final, **sin conversor de nivel**: RX por divisor 1k/2k a GPIO22, VCC desde VIN
  (4.7 V, apenas bajo el mínimo de 4.75 V de la hoja — anotado)

## Banco, en la i3 — antes de ir al equipo

```
□ 1. 100–120 Ω TEMPORAL entre CANH y CANL en la protoboard (sin soldar) — solo banco
□ 2. prueba_can.ino corrida 1  → ECO COMPLETO 20/20
       30-sep sin terminador: 0/20 y 135 errores RX. Sospecha: el terminador
□ 3. prueba_can.ino corrida 2, sin el cable RX (LV2 → GPIO22) → CERO RECIBIDAS
□ 4. QUITAR el 120 Ω temporal
□ 5. Re-soldar el DB9 macho:  CANH → 8 · CANL → 3 · nada en 2, 5, 6, 9
       (06-oct: el 2 va VACÍO en la primera escucha — no está confirmado como masa. Ver can/LEEME.md)
       Hoy está como CiA-303 (CANH 7, CANL 2). ⚠ Si el GND quedó en el pin 6,
       NO se conecta al equipo: ahí hay +24 V
□ 6. Cargar escucha_can.ino (LISTEN_ONLY, compila con esp32 3.3.11)
```

## En el montacargas

```
□ A. (1 min, recomendado antes de enchufar) confirmar X200:
       batería fuera:  pin 3 ↔ pin 8  ≈ 60 Ω
       llave ON, negra al pin 2:  pin 3 y 8 ≈ 2.5 V · pin 9 ≈ 12 V
□ B. escucha_can.ino — laptop a BATERÍA, conectar con llave OFF,
       después llave ON y paro arriba:
       · 60 s quieto · un ciclo de llave OFF→ON grabado desde el arranque
□ C. Con la escucha corriendo, entrar a Diagnose en el display:
       ¿aparece tráfico SDO (0x600/0x580) cuando el display pide valores?
□ D. STEER → Diagnose + escucha, girando el timón tope a tope, en video:
       · valores de los sensores de ángulo · qué PDO cambia
       · contar vueltas tope a tope (el simulador usa 2.6; fábrica 5.5)
□ D2. LATENCIA, con el mismo log de D (escucha_can.ino imprime marca de tiempo):
       mover la palanca de un golpe y el timón de un golpe, y medir en el log
       cuánto pasa entre la trama del mando (multipiloto, nodo 2) y la primera
       trama del controlador que responde (tracción 8/9, dirección 4).
       Ese número es el retardo de la cadena DEL OPERADOR. Si lo mandamos por el
       mismo camino, no puede ser más lento que eso. Comparar contra los 200 ms
□ E. Fotos de TODAS las pantallas de Diagnose y Parameter, solo leer.
       Buscar: relación de dirección, P1/P2/P3, retardo de freno
□ F. Buscar el conector del CanCode (12 pines, Mini-Mate-N-Lok) junto a la llave. Foto
□ G. Foto del conector del módulo KD Medi CO 250K (51540777): ¿puesto?
□ H. Cuando lleguen: fusibles de 2 A en 4F15, 6F9, 5F3, 3F11, 4F10 — con el chino
```

□ I. Si el DB9 no llega al bus: escuchar en el conector del MAESTRO 1U16
       (ver herramientas/componentes/). El bus pasa sí o sí por ahí.
       Sin cortar ni pinchar aislante: puntas de retro-sondeo por detrás del conector.
       Cómo encontrar el par CAN sin esquema:
         · batería fuera, escala 200 Ω: el par que da ≈ 60 Ω entre sí
         · llave ON, contra batería −: los dos ≈ 2.5 V en reposo;
           con tráfico, CANH promedia algo arriba y CANL algo abajo
       Alternativa más chica, si existe: el conector del CanCode junto a la llave (F)

## El DB9 no maneja — 02-oct-2026

El equipo **no viene preparado para teleop**. El DB9 es de **servicio**: leer sensores,
leer y cambiar parámetros. **Nunca se vio que sirva para manejar**, y no hay que esperarlo.

| | El DB9 / el bus | El teleop |
|---|---|---|
| Qué da | **ver**: sensores, mandos del operador, latencias, parámetros | **mandar**: velocidad, sentido, timón, hidráulica |
| Por dónde | el conector de servicio (o una toma del bus) | **los mandos del operador**, reemplazados: multipiloto, timón, pedal |
| Quién lo construye | ya existe | **nosotros** |

Aunque el DB9 resulte ser CAN, mandar desde ahí no sirve: el multipiloto real sigue en el
bus mandando lo suyo, y dos nodos diciendo cosas distintas es una falla. El mando se mete
**donde está el mando**: en el conector del multipiloto (peldaño 5) o en sus botones (ruta B).

## El camino seguro hacia el maestro — escalera, un peldaño a la vez

Corrige lo que se dijo el 02-oct («escribirle por el bus, no»). Era demasiado amplio:
**Judit hace exactamente eso**, por el bus, y es la herramienta de fábrica. El camino seguro
no es no tocarlo: es tocarlo **en orden y con respaldo**.

| # | Peldaño | Qué arriesga | Se vuelve atrás |
|---|---|---|---|
| 1 | **Escuchar** el bus (LISTEN_ONLY) | nada | no hace falta |
| 2 | **Leer** por SDO (pedir objetos, sin escribir), como nodo 30 | carga mínima del bus | no cambia nada |
| 3 | **Respaldo**: leer y guardar TODOS los parámetros `0x2xxx` del maestro | nada | es el seguro de los que siguen |
| 4 | **Escribir UN parámetro documentado** (p. ej. `0x2414`, vueltas del timón), leerlo de vuelta, y **devolverlo** al valor del respaldo | una falla si el valor no cuadra | sí, con el respaldo |
| 5 | **Reemplazar el multipiloto** (nodo 2): desenchufarlo y que nuestro nodo mande sus mismas tramas. El maestro sigue aplicando sus propios límites | lo que mande nuestro nodo | sí, se vuelve a enchufar el original |
| 6 | APM+ (nodo 31), la interfaz de automatización oficial | — | — |

El 5 es el teleop por el bus **sin cortar un cable**: se cambia un conector por otro.

Condiciones para pasar del 2 en adelante:
- en el equipo de **Las Palmas**, que está fuera de operación. **Nunca en uno de RETHINK**
- **con el chino** al lado, y sabiendo **cómo se borran los códigos de falla**
- **con el respaldo del paso 3 guardado en el repo** antes de escribir nada
- un solo cambio por vez, y se lee de vuelta antes de seguir
- nunca los menús `STD-PARAMETER` ni `CONFIGURATION`, ni *Save* en el display

**No se hace:** abrir el 1U16 · reflashear firmware · FTDI al DB9 (mete tensión en CAN_L) · mover hidráulica (falta sensor,
riesgo de aceite) · *Save* en Parameter · entrar a STD-PARAMETER o CONFIGURATION.

## Fuera del equipo

```
□ MCF vía Montasa, serie 82824121: sección 002 «Electrical» 07.15 del ETR 335D
   + esquemas 99515375 / 99520170 / 99520663.  Alternativa: revendedor, 25 USD
□ Scribd: ETR335D Spare Parts Catalog 82822585 · ETR345A (teoría de operación, 13 p.)
□ De la Mitsubishi Publication List: todas las filas EDR18N2 / ESR20N2 / ESR23N2
□ Chino: ¿qué se sacó después del 18-sep? ¿también un sensor de presión (E2320)?
□ 02-oct, CONTESTADO: el chino usaba el cable FTDI en los EDR18N2. El DB9 sirve para
   LEER sensores, no para manejar. Hipótesis que lo une todo (docs/21): el DB9 dependía
   del módulo de acceso 6U10 (X680/X681, «24V for JUDIT», fusible 4F15), y se canibalizó
   entre el 18 y el 30 de septiembre. → Buscar el 6U10 y sus conectores
□ (viejo) Chino: ¿en QUÉ EDR18N2 usaba el cable FTDI? ¿En este (serie 82824121) o en otros?
   Si fue en otros, ese equipo es el CONTROL: misma medición que acá
   (pin 3↔8, pin 2↔7, foto de la tarjeta de fusibles y de su etiqueta, número de serie).
   Si allá el DB9 es serie y acá es CAN, la diferencia es de configuración o revisión
   del equipo, no de la tarjeta: la tarjeta es pasiva, solo une el DB9 con el mazo.
□ Reporte a Miguel: listo en Documents\TaTa\Reporte_EDR18N2_2026-09-30.docx, sin enviar
```
