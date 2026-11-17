# Emulador del pedal de hombre muerto (el cilindro del `51297587`)

Reemplaza el **cilindro** del pedal doble en el conector suelto del equipo (`XS160`, pines 1–4) para que
el rig «pise» el hombre muerto. Es el **pie** de `docs/24` («El pie (watchdog)»): el mismo relé, con la
misma lógica de latido, paro de hongo y rearme manual. Lo que cambia es **a qué se conecta**, porque el
pedal resultó no ser un interruptor seco sino un sensor activo de 4 hilos (medido 13 a 16-nov, `docs/24`).

**La caja** (pines 5–10) queda fuera: sería el sentido de marcha por pedal (`1.13`, válido en 0/0). Se
comprueba en el equipo (`docs/24`, 16-nov).

## Lo que se emula (medido en banco, `docs/24`)

| Pin | Color | Qué es |
|---|---|---|
| 1 | café | + alimentación del sensor (la da el equipo) |
| 2 | blanco | salida A |
| 3 | azul | − |
| 4 | negro | salida B |

- **Dos salidas complementarias, todo o nada.** Con 11.2 V: una a **10.7 V**, la otra a **0.3 V**. El
  `1.06` solo acepta 0/1 y 1/0; 0/0 o 1/1 por **más de 2000 ms** da falla que **solo se borra
  reiniciando**.
- Apagado: **47 k** entre café y cada salida (94 k entre salidas). Lo más probable: cada salida tiene 47 k
  al + y un transistor que la jala al −. **No confirmado** (se saltó la prueba de carga).
- **No se sabe qué estado es «pisado».** El sensor real quedó clavado en blanco alto / negro bajo y no
  cambia con nada. Se decide en el equipo (paso 3 de abajo).

## El circuito

```
                   +5V ── PARO de hongo (NC) ──┬── bobina relé DPDT ──┐
                                               └── 1N4148 (cát. a +) ─┤
   GPIO27 ──[1 kΩ]── base 2N2222 ─ colector ─────────────────────────┘
                                   emisor ── GND del ESP (amarillo)

   lado del equipo (aislado del ESP por el relé):

   pin 1 (+) ──┬── [J1] ── ALTO_A ── NA1        COM1 ── pin 2 (blanco)
               │                     NC1 ── pin 3 (−)
               │
               └── [J2] ── ALTO_B ── NC2        COM2 ── pin 4 (negro)
                                     NA2 ── pin 3 (−)

   J1, J2 = puente de 3 pines:  «directo» (pin 1 al contacto)  ·  «47k» (pin 1 por 47 kΩ al contacto)
```

| Relé | Blanco (2) | Negro (4) | Estado |
|---|---|---|---|
| **sin bobina** (ESP muerto, paro, sin latido, booteando) | bajo (−) | alto | **tiene que ser «suelto»** |
| **con bobina** | alto | bajo (−) | «pisado» |

- **Cada salida va al COM de su polo**, así que en ningún estado del relé el + toca el −. Un corto + / −
  solo puede venir de un error de cableado: por eso la prueba 1 de abajo.
- **Nunca voltaje nuestro:** el alto y el bajo salen de los pines 1 y 3 del propio equipo. El relé aísla:
  la tierra del ESP (amarillo) no toca el conector.
- **El cambio dura milisegundos** (el relé abre un contacto y cierra el otro): durante ese instante la
  salida queda al aire, muy por debajo de los 2000 ms del `1.06`.
- **J1/J2 en «47k»** copia lo que se midió en el sensor (47 k al +). **«Directo»** sirve si el equipo
  espera que el sensor empuje el alto. Se elige en el equipo (paso 2). Empezar en **«47k»**: si está mal,
  el equipo lee un alto flojo y da `1.06`, pero no se rompe nada.
- **Si en el equipo «sin bobina» resulta ser «pisado»:** se cruzan los hilos de los pines 2 y 4 en la
  bornera. Nunca se deja así: sin bobina tiene que ser «suelto» (a prueba de fallas).

**El firmware no cambia:** es el pie de `herramientas/rig/tarea_firmware.md` (GPIO27, latido de 200 ms,
rearme con GPIO32). Para el banco no hace falta ESP: la bobina se prende con 5 V a mano.

## Con dos módulos de relé de 1 canal (revisado 16-nov)

**Esquema: `circuito_modulos.svg`** (y `.png`; lo dibuja `dibujar_circuito.py`).

Es lo más fácil de conseguir. Un polo por módulo, las dos entradas juntas:

| Módulo | COM | NC (sin activar) | NO (activado) |
|---|---|---|---|
| A | bornera **2** (blanco) | bornera **3** (−) | centro de **J1** |
| B | bornera **4** (negro) | centro de **J2** | bornera **3** (−) |

- `IN` de A y B juntos a **GPIO27** (en el banco, 5 V a mano). `VCC` de los dos módulos **a través del paro de
  hongo** (NC): apretarlo suelta los dos. `GND` de los módulos = GND del ESP (amarillo).
- J1/J2: un extremo directo a la bornera **1**, el otro a la bornera 1 por **47 kΩ**; el jumper elige.

> **Ojo, no estaba en el diseño: muchos módulos son «activos en bajo»** (`IN` en 0 = relé activado). Con
> uno así, **un ESP muerto, reiniciando o con GPIO27 al aire deja el relé ACTIVADO = «pisado»**: lo
> contrario de a prueba de fallas. Usar solo módulos **activos en alto** (jumper H/L en **H**), y
> comprobarlo antes de cablear: `IN` al aire y `IN` a GND tienen que dejar el relé **sin activar**. Si el
> módulo no tiene jumper y activa en bajo, no sirve: relé suelto con el 2N2222 (el circuito de arriba).
> **Control:** con todo cableado, desenchufar el ESP (o dejar `IN` al aire) tiene que dar la fila «sin
> bobina» de la tabla (blanco bajo, negro alto).

## Piezas

| Pieza | Nota |
|---|---|
| Relé **DPDT, bobina 5 V**, contactos de señal (HK19F-DC5V, G2RL-2-5V o similar) | contactos ≥ **60 V DC** si el pin 1 del equipo resulta ser tensión de batería (~40 V); si es ≤ 24 V, cualquiera. Alternativa: **dos módulos de relé SPDT** (1 canal, 5 V) con la entrada en paralelo, un polo por módulo; la mayoría aguanta 30 V DC |
| 2N2222, 1 kΩ, 1N4148 | si se usan módulos de relé, ya los traen |
| 2 × 47 kΩ | J1/J2 en «47k» |
| 2 × tira de 3 pines + 2 jumpers | J1, J2 |
| Bornera de 4 (pines 1–4) | ahí se cruzan 2 y 4 si hace falta |
| Paro de hongo NC | ya en el BOM del rig (`docs/24`) |
| **Clavija para el conector suelto** | ver «El conector» |

### En C&D (sps.cdtechnologia.net, revisado 16-nov; precios de la web, inventario sin confirmar)

| Qué | Producto | Precio |
|---|---|---|
| 3 × módulo de relé (2 + repuesto) | «Modulo Rele 5-24V 10A 1 - 8 canales», variante **1 CANAL 5V**. La foto muestra relé SRD-05VDC-SL-C, optoacoplador y **jumper H/L**: verificarlo en la tienda | L80 c/u |
| 47 kΩ | «Resistencias de Filamento de Carbon 1/4W 1 Valor (10 Unidades)», valor 47-K | L31 |
| J1/J2 | «Pines de conexion macho - hembra 2.54mm» + «Mini Jumpers 2.54mm 2 pin (Set de 10)» | L50 + L30 |
| Bornera de 4 | «Borneras de 4 - 5 y 12 Canales», 4 canales | ~L100 |
| Paro de hongo (si no está ya) | «Boton industrial parada de emergencia rojo tipo hongo». **Tiene que traer contacto NC** (bornes 11–12); verificarlo en la tienda | L150 |

**No sirve de ahí:** el G2RL-2 DPDT solo viene con bobina de 12 o 24 V. No hacen falta 2N2222 ni 1N4148: los
trae el módulo. El SRD dice 10 A / 30 V DC, que es para cortar carga; acá pasa menos de 1 mA, así que con ~40 V
en el pin 1 sirve igual (aislamiento de 250 V AC).

## El conector

El emulador tiene que enchufar en el `XS160` suelto del equipo. Dos caminos:

1. **El enchufe del sensor real.** El cilindro no detecta y no se va a arreglar. Se corta su cable de 4
   hilos cerca del cilindro y los 4 hilos van a la bornera; la caja queda conectada a su enchufe. **Es
   irreversible para el cilindro: lo decide maje, y solo después de la prueba del sensor real en el
   equipo** (paso 0), que necesita el conjunto entero.
2. **Terminales sueltas** hembra en los pines 1–4 del conector del equipo. No corta nada, pero hay que
   saber el tipo de terminal y quedan flojas.

## Pruebas en el banco (la fuente de 12 V hace de equipo)

Fuente + a la bornera **1**, − a la **3**. Las conexiones son a la bornera, no a pines del sensor.

| # | Prueba | Esperado | Control de falsación |
|---|---|---|---|
| 1 | **Fuente apagada**, óhmetro entre bornera 1 y 3, relé sin bobina y con bobina (5 V a mano) | **abierto** (o > 40 k) en los dos | puentear 1–3 con un cable: tiene que dar ~0 Ω |
| 2 | Fuente a 12 V, sin bobina: voltaje 2–3 y 4–3 | 2 ≈ 0 V · 4 ≈ 12 V | — |
| 3 | Con bobina | 2 ≈ 12 V · 4 ≈ 0 V | quitar la bobina: vuelve a la fila 2 |
| 4 | J en «47k», 10 kΩ de la salida alta al 3 | ≈ 2.1 V (12 × 10/57) | J en «directo»: ≈ 12 V. Si las dos dan igual, el puente no está cableado |
| 5 | Paro de hongo apretado con la bobina alimentada | vuelve a la fila 2 | soltarlo: vuelve a la fila 3 |
| 6 | Prender y apagar la bobina 20 veces | siempre una alta y una baja, nunca las dos iguales al quedar quieto | — |

## En el equipo — orden

0. **Antes de cortar nada**, con el conjunto real enchufado, llave en ON, rueda en el aire, sin pedir
   movimiento: anotar los eventos (¿desaparece el `1.06`? ¿aparece el `1.13`?). Con el conector de la
   caja, accionarla y mirar qué cambia en el diagnóstico (`docs/24`, 16-nov).
1. **Conector suelto, llave en ON, sin nada enchufado:** pin 1 contra pin 3 (¿12, 24, ~40 V?) y pines 2 y 4
   contra pin 3. Decide los contactos del relé (≥ 60 V DC si da ~40 V) y J1/J2: **0 V → «directo» posible;
   con voltaje propio → «47k»**.
2. Emulador enchufado, **relé sin bobina**, llave en ON. Si quedó el `1.06` de antes, **reiniciar** (no se
   borra solo). Ver que no vuelva.
3. **Qué estado es «suelto»:** rueda en el aire, mano en el paro, relé **sin bobina**, mandar `a 100` por el bus
   (`herramientas/can/multipiloto.md`) o mover el multipiloto. Tiene que aparecer el aviso de hombre
   muerto **`E1903.01`** y la rueda no gira. **Control:** con bobina, el aviso desaparece. Si es al revés,
   cruzar 2 y 4 en la bornera y repetir.
4. Recién ahí, el watchdog con el ESP (`tarea_firmware.md`, pruebas 2 y 3) enchufado al equipo.
