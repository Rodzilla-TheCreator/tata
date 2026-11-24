# El rig integrado — un ESP32 con multipiloto (CAN), timón y pie

| Archivo | Qué es |
|---|---|
| `rig/rig.ino` | **el firmware integrado** (21-nov). Junta sin cambiar su lógica `multipiloto_campo`, `emulador_timon` y `pie`. Un latido y un watchdog de 200 ms para los tres |
| `rig_gui.py` | **la consola**: timón que se arrastra o se manda a un ángulo exacto, multipiloto con joystick, palanca, N S E W y pito, y el pedal con su rearme |
| `master_falso_can.py` | el Master del EDR, de mentira, en el SH-C30G: para probar el CAN del rig en el banco |
| `prueba_host/` | prueba la **lógica** de `rig.ino` en la compu, con el ESP imitado: 23 pruebas, y dos controles |
| `pie/pie.ino`, `pie.py` | el pie solo (19-nov) · `pedal_n/` el pedal con una tecla, sin watchdog (solo banco) |
| `tarea_firmware.md`, `tarea_banco_19nov.md` | los encargos |

## Estado (21-nov)

| Qué | Resultado |
|---|---|
| `rig.ino` contra la API del ESP32 imitada (`g++ -Wall -Wformat`) | sin errores. **No se compiló con el core del ESP32** (la sesión no podía bajarlo): compilarlo en maquinon es el primer paso |
| `prueba_host/correr.sh` | **23/23 PASA** (21-nov, con la regla del pie ARMADO): arranque suelto, sin armar no transmite, el pie no pisa sin rearme, boot-up 702 / 0x1000 / NMT / 182 decodificado, timón con rampa e ignorado antes de `T`, **watchdog: pie suelto ≤ 200 ms, 182 a cero, timón quieto**, no re-pisa solo, paro, `X` |
| control (`correr.sh control`, `WATCHDOG_MS` 5000) | **FALLA** 11, 12, 14, 14b, 14c, como debe. Sin la regla del pie ARMADO fallan 14b, 14c y 16b |

> **21-nov, segunda vuelta — decía / es:** decía que el watchdog y el paro **soltaban el pie y ponían el
> 182 en cero**, y que al volver el latido el 182 volvía a mandar solo. **Es:** el CAN y el timón obedecen
> **solo con el pie ARMADO**: después de un watchdog o del paro nada vuelve sin rearme manual. **Qué lo
> tumbó:** el hongo solo corta los relés del pedal; si la hidráulica del ETR no pide el pedal, un mando de
> elevar seguía saliendo con el hongo apretado.
| `rig_gui.py --demo` | abre y dibuja (Xvfb) |
| En banco con el hardware | **pendiente**: lo de abajo |

## Hoy

Las pruebas del 21-nov, paso a paso y con sus controles: **`campo/2026-11-21/LEEME.md`**.

## En maquinon

Preparar (una vez):
```bash
cd ~/tata && git pull origin main
sudo apt install python3-tk && pip install pyserial python-can
sudo usermod -aG dialout $USER          # y volver a entrar a la sesión
# arduino-cli con el core esp32 3.3.12 (el mismo de la i3, docs/14):
arduino-cli core install esp32:esp32@3.3.12
```
Cargar un sketch: `arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 <carpeta>`.
**Antes de abrir cualquier programa de Python, cerrá el monitor serie**: un solo programa por puerto.

### 1 · Cada circuito por separado (con sus sketches de siempre, ya validados)

| # | Circuito | Sketch + programa | Pasa si | Control |
|---|---|---|---|---|
| 1 | **Pedal** (fuente de 12 V en pin 1 / pin 3) | `pie/` + `python3 pie.py /dev/ttyUSB0` | `r` + `p`: blanco ≈ 12 / negro ≈ 0 · `m`: suelta (el ESP imprime `EV P2 suelta` ≤ 200 ms si puenteaste 27→34) · `v`: **sigue suelto** · `r`: vuelve a pisar | el pulsador sin apretar: suelta y queda DISPARADO |
| 2 | **Timón** (LM358 a +11–12 V de la fuente; GND común) | `../emulador_timon/` + `python3 ../emulador_timon/rueda_timon.py /dev/ttyUSB0` | multímetro, verde y café contra el amarillo: **0°** verde 4.45 / café 2.47 · **90°** 2.47 / 4.45 · **180°** 0.49 / 2.47 · **270°** 2.47 / 0.49 (±0.05) | sacar el cable de un DAC: ese canal se va a ~0 y el otro no cambia |
| 3 | **CAN aislado** | `../can/prueba_can.ino` (modo self-test, no necesita otro nodo) | **20/20** eco | **sacar VDD2 del ADuM: 0 recibidas** |

El comentario de `prueba_can.ino` todavía habla del divisor 1k/2k: **en el armado aislado no va** (el RX
del TJA va directo a VIA).

### 2 · Todo junto

1. Cargar `rig/` (`arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 rig`).
2. `python3 rig_gui.py /dev/ttyUSB0`.
3. **Pie:** «Rearmar (R)» → botón SUELTO → PISADO. Relés: clic.
4. **Timón:** ángulo del sensor `0` → «Armar timón (T)» → arrastrar el volante, o «ir a» un ángulo. El punto
   verde es dónde está de verdad el ESP (sigue con rampa de 360°/s). Verificar con el multímetro.
5. **CAN:** SH-C30G a CANH/CANL y su GND a **GND_bus**, R120 encendido (~60 Ω medido con todo apagado).
   En otra terminal `python3 master_falso_can.py` (o `--slcan /dev/ttyACM0`). En la GUI «Armar CAN», y
   Enter en el master falso. Tiene que verse: `702 00` → `582 43…` → NMT → y cada mando de la GUI
   decodificado (`y +100 x -40…`).
6. **Las pruebas que importan:**
   - desmarcar «latido» → en ≤ 200 ms: pie suelto, el master falso ve el 182 en cero, el timón **se queda**;
   - volver a marcar «latido» → el pie **sigue suelto** hasta «Rearmar»;
   - soltar el pulsador (paro) → pie suelto y DISPARADO;
   - cerrar la ventana de golpe (o `kill -STOP` al proceso de Python: la laptop congelada) → lo mismo;
   - desenchufar el USB → los relés sueltan.

## Lo que NO está listo para el montacargas

- `REARME_POR_SERIE` está en **1** (banco): para el equipo se compila con **0** y el rearme es el botón del
  GPIO32 en el fierro.
- La **palanca trasera** (`b2`, bits `0x40`/`0x20`) sale de la tabla de `can/multipiloto.md` pero **nunca
  se mandó al Master**. Probar primero joystick y botones, que sí se probaron el 22-oct.
- El **ángulo de rueda** que muestra la GUI es **estimado** (5.5 vueltas = 180°). Lo que se emula es el
  volante; la rueda la decide el nodo 4.
- En el equipo: `docs/25` y el orden del `LEEME.md` del emulador del pedal (paso 0: el conjunto real
  enchufado). La rueda en el aire y el hongo en la mano antes de cualquier mando.

## Teleop por teclado y odometría de giros (23–24-nov)

- `teleop_wasd/teleop_wasd.ino` + `teleop_wasd.py`: el teleop del 23-nov (`campo/2026-11-23/resultados.md`). Desde el
  24-nov la ventana integra la odometría en vivo con `percepcion/odometria.py` (entre ejes 1.688, motriz corrida 0.325),
  tiene **MARCA (M)** para poner la pose en cero y dejar la marca en el log, y botones de rueda para la prueba de
  giros (recta del modelo +1.2, topes, la receta del pasillo, arco).
- `odometria_log.py`: los tramos entre MARCAs de un log del teleop, lo que da la tiza (seis distancias), la comparación
  de las dos y lo que ajusta (recta del `0x184`, escala de la marcha, `e`). `--objetivo` dice dónde deberían caer las
  marcas antes de mover el equipo. `--prueba` se prueba con controles. Protocolo: `campo/giros_odometria/LEEME.md`.
