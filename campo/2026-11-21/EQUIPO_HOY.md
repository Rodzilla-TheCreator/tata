# 21-nov · maje está en el EQUIPO (con la i3, sin maquinon). Solo medir, mirar y escuchar

> **Corregido (maje, 21-nov):** decía «las 4 pruebas de banco no están hechas». **Es:** el timón (26-oct),
> el pedal (19-nov, con el paro) y el circuito del CAN aislado ya están hechos y probados por separado. Lo
> único sin probar en hardware es **`rig.ino`** (el integrado): ese **no** va hoy. Cada pieza con **su
> sketch de siempre**, sí, en el orden de la sección G.

**Regla de hoy:** primero medir y mirar (A–E, nivel 1 de `docs/25`). Después, si el equipo prende, cada
pieza **por separado** (G). **Nada se mueve hoy:** para movimiento (nivel 3) hace falta el hongo NC de
verdad (no el pulsador) y la rueda en el aire. Nada irreversible, no se corta nada. Los números van a
`resultados.md`, sección «Equipo».

Para el Claude de campo: **una medición a la vez**, esperá el número, anotalo, commit cada tanto.

## A · Antes de tocar (5 min)

| # | Qué | Anotar |
|---|---|---|
| A1 | ¿Qué le falta al equipo («x y y»)? ¿Batería conectada? ¿Prende? | texto |
| A2 | **Foto de la placa de datos** (número de serie) | foto |
| A3 | **Foto de frente del conector del pedal en el equipo** (cara de los pines, con los números grabados) y de la etiqueta | foto. **Mandarla al repo: `campo/2026-11-21/`** |

## B · El conector del pedal, llave OFF

Desconectar el pedal **con la llave en OFF**.

| # | Qué | Para qué |
|---|---|---|
| B1 | Con los **números grabados**, ubicar los pines 1–4 del lado del equipo (la cara está en espejo respecto del sensor) | que el emulador vaya al pin correcto |
| B2 | Óhmetro: pin 3 del equipo ↔ **negativo de batería** | ¿el pin 3 es el − de batería? |

## C · El conector del pedal, llave ON, sensor desconectado (2 min y apagar)

Llave ON con el pedal **desconectado**. Va a saltar la falla del pedal (`1.06`). Es esperable y se borra
apagando. Punta negra en el **pin 3**:

| # | Pin | Esperado | Decide |
|---|---|---|---|
| C1 | 1 | el + del sensor (~11–12 V, o lo que dé) | si los relés aguantan: **≤ 30 V** = los módulos SRD sirven tal cual |
| C2 | 2 | ~0 V, o un voltaje propio | si da voltaje propio, el equipo tiene su propia resistencia al +: la 47 k sigue sirviendo |
| C3 | 4 | igual que C2 | |

Apagar, **reconectar el pedal real**.

## D · El paso 0: el pedal real, montado (si el equipo prende)

| # | Qué | Anotar |
|---|---|---|
| D1 | Llave ON con todo original. ¿Qué eventos hay en la pantalla? | códigos |
| D2 | Pisar el pedal con la mano (con su plato). ¿Cambia algo en la pantalla? ¿Aparece o desaparece `E1903.01` o `1.06`? | sí/no y códigos |
| D3 | Con el pedal sin pisar y pisado: pin 2 y pin 4 contra el 3 (retro-sondeo por atrás del conector, **sin desconectar**) | 4 números |

Con D3 se sabe **qué estado es «suelto»**: el emulador sin bobina tiene que dar lo mismo que el pedal sin
pisar. Si sale al revés, se cruzan los cables 2 y 4 del emulador.

## E · Medidas del fierro (flexómetro, llave OFF)

| # | Qué | Por qué |
|---|---|---|
| E1 | **Entre ejes**: centro de la rueda motriz ↔ centro de las ruedas de carga, de los dos lados | ¿1.562 o 1.688? 8 % de error en cada giro (`auditoria/ciclo2.md`) |
| E2 | **¿Las ruedas de carga tienen sensor?** Mirar en el brazo o el cubo de cada rueda de carga: un sensor con cable, o imanes. Foto | odometría que no patina (manual: eventos `1.41.x`) |
| E3 | Si el equipo prende y la dirección funciona: **vueltas de volante de tope a tope**, contadas a mano | el `0x2414` (fábrica 5.5) |

## F · (reemplazado por G)

## G · Si el equipo prende: cada pieza por separado, con su sketch de siempre

Una pieza a la vez; **restituir lo original entre una y otra**. Si aparece una falla que no se borra
apagando y prendiendo, **parar** y anotarla.

| # | Pieza | Sketch | Antes | Qué se busca | Nivel |
|---|---|---|---|---|---|
| G1 | **CAN aislado, escuchar** | `escucha_can.ino` (LISTEN_ONLY) | `prueba_can` 20/20 + control sin VDD2 = 0 (si no tiene números, 5 min en una mesa). CANH → DB9 8, CANL → DB9 3, **GND_bus → negativo de batería**. ≈ 60 Ω entre 8 y 3, llave OFF | el bus por la cadena aislada, 0 errores | 1 |
| G2 | **Multipiloto** (nodo 2 falso) | `multipiloto_campo.ino` + `campo_nodo2.py` | lo del 22-oct: CAN del multipiloto real FUERA, el puente en el mazo, el repuesto solo para alimentar | `E4809` desaparece; `a 100` → `E1903.01` (pide el pedal). **Con el pedal real sin pisar: nada se mueve** | 2 |
| G3 | **Pedal emulado** | `pie.ino` + `pie.py` (con watchdog; **no** `pedal_n`) | C y D hechos (qué estado es «suelto»). Cables a los pines 1–4 **por número grabado**. Multipiloto **real** puesto, sin tocarlo | sin pisar: lo mismo que el pedal real suelto en D3. `r` + `p`: lo mismo que el real pisado, sin `1.06`. `m`: vuelve a suelto | 2 |
| G4 | **Timón emulado** | `emulador_timon.ino` + `rueda_timon.py` | **rueda motriz en el aire**. `docs/23` Track B: saber cómo se borra una falla del nodo 4 (¿apagar y prender?) antes de enchufar | el nodo 4 acepta el sensor emulado sin falla; mover despacio y ver el sentido de la rueda | 2 |

**G2 + G3 juntos = movimiento. Hoy no.**
