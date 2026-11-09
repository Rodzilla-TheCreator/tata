# Encargo — el firmware del rig integrado: un solo ESP32 con CAN, timón y pie

**Para la sesión de i3.** Leé antes, enteros: `docs/24-rig-completo.md` (sobre todo «El circuito del
ESP, pin por pin» y «El pie»), `docs/20-simular-mandos.md`, `docs/19-control-teleop.md`,
`herramientas/can/multipiloto.md`, `herramientas/can/banco_imitador/LEEME.md` y
`herramientas/emulador_timon/LEEME.md`. Y los dos sketches que se juntan:
`herramientas/can/banco_imitador/multipiloto_campo/multipiloto_campo.ino` (nodo 2 falso, ya
aceptado por el Master el 22-oct) y `herramientas/emulador_timon/emulador_timon.ino` (sin/cos, ya
calibrado el 26-oct).

**Las piezas del CAN aislado llegan el 11-nov.** El firmware tiene que estar escrito, compilado y
con sus pruebas listas para correr ese día. Lo que se pueda probar antes, se prueba antes.

## Qué es

Un sketch, `herramientas/rig/rig/rig.ino`, que hace en un solo ESP32 lo que hoy hacen dos:

| Parte | Viene de | Pines (`docs/24`) |
|---|---|---|
| **Multipiloto** (nodo 2 falso, `0x182` + latido `702`) | `multipiloto_campo.ino`, sin cambiar la lógica de arranque | TWAI TX 22 / RX 21, por el ADuM1201 |
| **Timón** (sensor sin/cos del nodo 4) | `emulador_timon.ino`, con su calibración `kV oV kC oC` | DAC 25 (verde) / 26 (café) |
| **Pie** (el relé que hace de pedal de hombre presente) | nuevo | GPIO27 → relé (o PhotoMOS); GPIO32 rearme; GPIO2 LED |

Y un programa en la laptop, `herramientas/rig/rig.py`, que junta `campo_nodo2.py` y `rueda_timon.py`.

## Las reglas (no negociables; cada una tiene su prueba abajo)

1. **Un solo latido manda las tres partes.** `rig.py` manda **una línea de estado completo cada
   50 ms**, que es a la vez el mando y el latido. Ejemplo: `L a=0 t=0 i=0 d=0 b=0 r=0 th=12.5 pie=1`.
   Línea completa e idempotente: si se pierde una, la siguiente repone todo.
2. **200 ms sin línea válida → watchdog**, y hace las tres cosas a la vez:
   - el `0x182` vuelve a cero;
   - **el pie suelta** (GPIO27 a bajo);
   - **el timón se queda donde está**: mantiene el último ángulo, sin saltar a cero. Un salto de
     ángulo es un giro de la rueda.
3. **Rearme manual del pie.** Después de un watchdog o al arrancar, el pie queda suelto aunque vuelva
   el latido, **hasta que se apriete GPIO32 con latido fresco**. Nunca se re-pisa solo. LED: fijo =
   pisando · parpadeo = disparado, esperando rearme · apagado = sin armar.
4. **Armado del CAN como en `multipiloto_campo`.** Arranca en LISTEN_ONLY y no manda ni un bit hasta
   `A`. `X` vuelve a solo escucha. Toda la secuencia de arranque (boot-up, `0x1000`, NMT START, `0x182`
   en cero hasta el primer mando) **se copia, no se reescribe**: ya funcionó en el equipo.
5. **Arranque seguro.** GPIO27 queda en bajo desde el reset. **Los DAC se escriben al ángulo inicial
   en las primeras líneas de `setup()`**, antes de `Serial` y del TWAI, para achicar la ventana de
   0 V (`docs/24`, «Detalle a saber del timón»: 0 V queda fuera del círculo y el nodo 4 marca falla).
   **Medí cuánto dura esa ventana** con el osciloscopio o con un segundo ESP, y anotala.
6. **El ángulo inicial lo da `rig.py`** al armar el timón (`T <grados>`): tiene que ser el del sensor
   real en ese momento, para que el cambio de sensor no gire la rueda. Antes de `T`, el timón no sale
   del ángulo con que arrancó.
7. **Nada bloquea el `loop()`.** El TWAI, el serie y los DAC sin esperas largas. **Reportá el peor
   período del loop** en 10 minutos de corrida con todo activo. Activá además el watchdog de tareas
   del ESP32 (`esp_task_wdt`, ~1 s): si el firmware se cuelga con GPIO27 en alto, el reset lo baja.
8. **El paro de hongo es hardware** (corta la bobina, `docs/24`) y el firmware no lo ve ni lo
   necesita. No metas ninguna lógica que dependa de él.

## Qué hacer

1. `rig.ino` con las 8 reglas. Compilalo con `arduino-cli` (placa `esp32:esp32:esp32`). Si no está
   instalado en la i3, instalalo y anotá cómo en `docs/14`.
2. `rig.py`: la línea de estado cada 50 ms, los mandos de `campo_nodo2.py` (los mismos nombres), la
   rueda de `rueda_timon.py` para el ángulo, el log en `herramientas/rig/logs/` con la misma idea de
   marcas, y **`Ctrl-C` = todo a cero + pie suelto** antes de cerrar. **El mando con control de juego
   (`docs/19`) queda para después**: dejá el lugar, no lo hagas ahora.
3. `herramientas/rig/prueba_rig.py`: las pruebas de abajo, automáticas en lo que se pueda, cada una
   con su **control de falsación**. Tiene que poder correrse con el rig enchufado a la i3 y decir
   PASA / FALLA por prueba.
4. `herramientas/rig/LEEME.md`: cómo se carga, cómo se corre, el protocolo de la línea serie, la
   tabla de pruebas con resultado, y el **orden de uso en el equipo** (arnés en Y en manual, armar CAN,
   `T` con el ángulo real, rearme del pie), apuntando a `docs/24` y `docs/25`.

## Las pruebas, en el banco, sin montacargas

| # | Prueba | Cómo se ve | Control de falsación |
|---|---|---|---|
| 1 | Arranque seguro | GPIO27 en bajo desde el reset (LED o multímetro en el colector); DAC al ángulo inicial; ventana de 0 V medida | arrancar con una versión que ponga GPIO27 en alto en `setup()`: la prueba tiene que fallar |
| 2 | Watchdog del pie | se corta `rig.py` → GPIO27 baja en **≤ 200 ms** (puenteá GPIO27 a GPIO34 y que el propio ESP marque el tiempo, o un segundo ESP) | `WATCHDOG_MS = 5000` en una compilación de prueba: la prueba tiene que dar FALLA |
| 3 | Rearme manual | vuelve el latido → el pie sigue suelto; solo pisa con GPIO32 **y** latido fresco | GPIO32 sin latido: no pisa |
| 4 | Timón en el watchdog | se corta `rig.py` con el timón girando → el ángulo queda fijo (caracterizador en otro ESP leyendo el LM358) | una compilación que vuelva a 0° en el watchdog: la prueba la detecta |
| 5 | Timón, el círculo | barrido de 360°: radio ≈ 1.95–1.98 y centro ≈ 2.47 con el caracterizador (`emulador_timon/LEEME.md`) | quitar el cable de un canal: el círculo se rompe |
| 6 | CAN, sin el aislador todavía | con el bus de diodos de `banco_imitador` y `master_falso` en otro ESP: los 5 pasos de su `LEEME.md` (boot-up → NMT START → `0x182`, mando `a 100`, watchdog a cero, arranque en cero) | los de ese `LEEME.md` (quitar el diodo → `8.08 SIMULADO`) |
| 7 | CAN aislado (**11-nov**, con las piezas) | la prueba 6 otra vez, ahora por ADuM1201 + TJA1050 contra un segundo ESP con su TJA; y `GND1`↔`GND2` abierto con el óhmetro | desconectar `VDD2` del ADuM: sin tramas |
| 8 | Las tres juntas, 10 min | timón barriendo + `0x182` con mandos + pie pisado; **ningún watchdog falso**, peor período del loop reportado | matar `rig.py` a mitad: las tres reaccionan en ≤ 200 ms |

Hasta el 11 se pueden hacer las pruebas 1–6 y la 8 con el bus de diodos. La 7 espera las piezas.
**Las que necesitan hardware que la i3 no tiene enchufado, dejalas escritas y listas para maje**, con
el paso a paso en el `LEEME.md`, y marcalas «pendiente de banco» en la tabla. No las des por pasadas.

## Entregables

- `herramientas/rig/rig/rig.ino`, `rig.py`, `prueba_rig.py`, `LEEME.md` con la tabla de pruebas.
- Una línea en `docs/24` (sección del rig integrado) apuntando a `herramientas/rig/`.
- Una fila en la tabla de carpetas de `CLAUDE.md` para `herramientas/rig/`.
- Commit y push a `main`.

## Lo que NO es esta tarea

- **No va al montacargas.** Nada de esto se conecta a un equipo hasta que maje pase las pruebas 1–8
  en el banco y se cumpla `docs/25`.
- No es el mando con control de juego ni la Jetson. El latido sale de la laptop por ahora.
- No es cambiar el circuito. Si el firmware pide un cambio de hardware, anotalo en el `LEEME.md` como
  propuesta, con el porqué.
- No se tocan `multipiloto_campo.ino` ni `emulador_timon.ino`: quedan como están, de referencia.
