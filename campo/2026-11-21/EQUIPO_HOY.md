# 21-nov · maje está en el EQUIPO (con la i3, sin maquinon). Solo medir, mirar y escuchar

**Regla de hoy:** el rig **no** se conecta al equipo. Las 4 pruebas de banco (`LEEME.md`) no están hechas,
`rig.ino` va con `REARME_POR_SERIE 1` y el equipo todavía no está completo. Es el **nivel 1** de
`docs/25`: medir y mirar. Nada irreversible, no se corta nada. Los números van a `resultados.md`, sección
«Equipo».

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

## F · CAN: solo si sobra tiempo, y solo escuchar

Solo si se hace antes, en una mesa ahí mismo, la **prueba 3** de `LEEME.md` (`prueba_can`, 20/20 y su
control) y pasa. Entonces se puede cargar `escucha_can.ino` (**LISTEN_ONLY**) y escuchar el DB9: CANH al
8, CANL al 3, **GND_bus al negativo de batería**. Si no se hizo la prueba 3, no se escucha hoy.
