# Encargo 19-nov — banco con maje: emulador del pedal, firmware del pie y CAN aislado

**Para la sesión de i3, con maje en el banco.** No es una tarea de escritorio: maje arma y mide, vos
guiás paso a paso, escribís el firmware y anotás. **Una prueba a la vez**, esperando su número antes de
pasar a la siguiente. Nada de esto va al montacargas.

Leé antes: `herramientas/emulador_pedal/LEEME.md` (entero, con `circuito_modulos.png`),
`herramientas/rig/tarea_firmware.md` (las 8 reglas), `docs/24-rig-completo.md` («El circuito del ESP,
pin por pin», «Aislar el DB9», «LLEGÓ 11-nov») y `herramientas/can/LEEME.md`.

**Regla de este encargo:** cada prueba tiene su control de falsación. Si el control no se hizo, la prueba
**no pasó**. Lo que no se pudo probar queda «pendiente de banco», nunca como pasado.

---

## Parte 1 — el emulador del pedal, sin ESP (15 min)

maje ya lo armó: **dos módulos de relé de 1 canal 5 V** (SRD-05VDC, jumper H/L), 47 kΩ fija en cada
salida, y un **pulsador** en lugar del paro de hongo (sirve para el banco; para mover el equipo va el
hongo de verdad).

Corré con él las pruebas **0a, 0b y 1 a 6** de la tabla del `LEEME.md`, en ese orden. La fuente de
12 V hace de equipo (+ al pin 1, − al pin 3); los 5 V de los módulos, de un cargador USB.

- **0a es la que más importa:** IN al aire y a DC− → relé **suelto**. Si hace clic, el jumper está en
  L o el módulo es activo en bajo: **no sigas** hasta resolverlo.
- Antes de la 0a, preguntale qué pulsador tiene (con traba / NA / NC, se ve con continuidad) y anotalo.

**Entregable:** los números de cada prueba en `docs/24` (sección del sensor del pedal, fecha 19-nov) y
la tabla del `LEEME.md` con una columna de resultado.

## Parte 2 — el firmware del pie (lo primero de `tarea_firmware.md`)

El pie es la parte de `rig.ino` que se puede probar **hoy**, con el emulador. Hacela como módulo que
después entra tal cual en `rig.ino`.

**Cambio de hardware respecto de `docs/24`:** con módulos de relé ya no van el 1 kΩ, el 2N2222 ni el
1N4148: **GPIO27 va directo al IN de los dos módulos** (que ya trae optoacoplador y transistor).
Recomendado: **10 kΩ de IN a DC−**, para que el IN nunca quede al aire mientras el ESP arranca o se
carga el firmware. Anotalo en `docs/24` como «decía / es».

Qué hacer:

1. `herramientas/rig/pie/pie.ino`: las reglas **2, 3, 5 y 7** de `tarea_firmware.md`, solo para el pie:
   - latido por serie (la misma línea `L ... pie=1` de la regla 1, para no inventar otro protocolo);
   - **200 ms sin línea válida → GPIO27 a bajo**;
   - **rearme manual**: después de un watchdog o al arrancar, el pie queda suelto hasta GPIO32 a GND
     **con latido fresco**. Nunca se re-pisa solo;
   - LED GPIO2: fijo = pisando · parpadeo = disparado, esperando rearme · apagado = sin armar;
   - GPIO27 en bajo desde la primera línea de `setup()`; `esp_task_wdt` de ~1 s.
2. `herramientas/rig/pie.py`: manda la línea cada 50 ms; `p` pisa, `s` suelta, `Ctrl-C` = pie suelto
   y cierra. Es el embrión de `rig.py`: escribilo para que crezca, no para tirarlo.
3. Compilar y cargar con `arduino-cli` (si no está, instalalo y anotá cómo en `docs/14`).

Pruebas (con el emulador conectado y la fuente de 12 V; maje mide pin 2 y pin 4 contra pin 3):

| # | Prueba | Esperado | Control de falsación |
|---|---|---|---|
| P1 | Arranque y carga de firmware | en el reset, el boot y **mientras se carga el sketch**, el relé no hace clic (fila «sin activar» del `LEEME.md`) | quitar la 10 kΩ y repetir: anotá si cambia algo (si no cambia, la 10 k es seguro extra, no la causa) |
| P2 | Watchdog | `pie.py` pisando → se mata `pie.py` → GPIO27 baja en **≤ 200 ms**. Medilo con el propio ESP: GPIO27 puenteado a GPIO34, que marque el tiempo y lo imprima | compilación con `WATCHDOG_MS = 5000`: la prueba tiene que dar FALLA |
| P3 | Rearme | vuelve `pie.py` → el pie sigue suelto; pisa solo con GPIO32 **y** latido | GPIO32 apretado sin latido: no pisa |
| P4 | Pulsador / paro | pisando, se aprieta el pulsador → fila «sin activar», aunque GPIO27 siga en alto | soltarlo: vuelve a pisar (si el firmware no se disparó) |
| P5 | Cuelgue | una compilación de prueba con `while(1);` después de pisar → `esp_task_wdt` resetea y el pie queda suelto | sin `esp_task_wdt` en esa compilación: el pie se queda pisado (por eso existe) |
| P6 | 10 min | `pie.py` pisando 10 min: **ningún watchdog falso**; peor período del loop reportado | matar `pie.py` al final: suelta en ≤ 200 ms |

## Parte 3 — el CAN aislado, armado en protoboard

Las piezas llegaron el 11-nov: **ADuM1201 (módulo CJMCU) + B0505S-1WR3 + el TJA1050 nuevo** (el que
pasó 20/20). El circuito es `herramientas/can/armado_aislado.svg` con la corrección del 02-nov
(**`VDD1` a 3.3 V del ESP, no a 5 V**: con 5 V, GPIO21 recibe 5 V).

> **Si lo que maje tiene en la mano es otra pieza** (un `TD301DCANH3`, un `CTM1051` u otro módulo CAN
> aislado), pará: foto, número de parte, y el pinout **de la hoja de datos del fabricante**, no de la
> foto de Amazon. Anotalo en `docs/24` y adaptá esta parte antes de cablear.

1. **Dibujá el armado en protoboard**, `herramientas/can/protoboard_aislado.svg` (como
   `protoboard_can.svg`): dónde va cada módulo, cada cable con su color, y las **dos tierras pintadas
   distinto** (amarillo = ESP; `GND_bus` = negativo de batería). Que se pueda armar mirándolo, sin
   leer nada más.
2. Armalo con maje **por etapas, midiendo antes de seguir**:

| # | Etapa | Esperado | Control de falsación |
|---|---|---|---|
| C0 | **SH-C30G**: óhmetro carcasa USB ↔ borne `GND` | abierto = aislado; ~0 Ω = **no aislado** (anotalo: en el equipo solo con la laptop a batería) | puntas juntas: ~0 Ω |
| C1 | B0505S solo, 5 V del ESP en Vin, **con el TJA de carga** | Vout **4.75–5.25 V**; óhmetro Vin− ↔ Vout− (sin alimentar) **abierto** | medir Vin− ↔ Vin−: ~0 Ω |
| C2 | ADuM1201: VDD1 = 3.3 V, GND1 = amarillo, VDD2 = Vout+, GND2 = Vout− | GND1 ↔ GND2 **abierto**; VOA (al GPIO21) **≤ 3.3 V** | — |
| C3 | Cadena entera: GPIO22 → VIB → VOB → TJA TXD; TJA RXD → VIA → VOA → GPIO21 | `prueba_can.ino` contra otro nodo (el SH-C30G en la laptop o un segundo ESP+TJA), bus con 120 Ω en cada punta (≈ 60 Ω medido): **20/20** | **desconectar VDD2**: sin tramas. Si pasan tramas, algo puentea el aislamiento |
| C4 | Las dos tierras, con todo armado y alimentado | GND del ESP ↔ GND_bus **abierto** (o > 1 MΩ) | — |

**Pines:** TX 22, RX 21 (los mismos de siempre). **Terminación:** en el equipo se mide, no se pone por
ficha (`docs/24`, «La terminación»).

**Entregable:** `protoboard_aislado.svg`, los resultados C0–C4 en `docs/24` (después de «LLEGÓ
11-nov») y una línea en `herramientas/can/LEEME.md` apuntando al armado.

---

## Lo que NO es esta tarea

- No va al montacargas. El emulador va al equipo solo después de pasar la parte 1 y la P1–P6, y con el
  orden del `LEEME.md` (paso 0: el conjunto real enchufado).
- No es `rig.ino` completo: timón y CAN dentro del mismo sketch siguen en `tarea_firmware.md`. El pie y
  el CAN aislado probados hoy son sus dos primeras piezas.
- No se corta el cable del cilindro.

## Al terminar

Marcá en `CLAUDE.md` la sección de la tarea como **✔ Hecha** con una línea de resultado (o qué quedó
pendiente de banco y por qué), y commit + push a `main`.
