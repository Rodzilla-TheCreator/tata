# Resultados · banco del 21-nov-2026

Lo llena el Claude de campo con maje. Un número por fila. «—» = no se hizo; «pendiente» = no se pudo.

## Preparación

| Qué | Resultado |
|---|---|
| 10 kΩ IN → DC− | |
| Divisor 10k/20k al GPIO35 | |
| Fuentes separadas / una a la vez | |
| Puerto del ESP | |
| Cómo se cargó (arduino-cli / IDE) y versión del core | |

## Prueba 1 · Pedal

| # | Medido | ¿Pasa? |
|---|---|---|
| 1.1 | blanco / negro: | |
| 1.2 | | |
| 1.3 | blanco / negro: | |
| 1.4 | N = ms | |
| 1.5 | | |
| 1.6 | | |
| 1.7 | | |
| 1.8 | V con 10 kΩ: | |
| control (WATCHDOG_MS 5000) | | |

## Prueba 2 · Timón

| # | Verde | Café | ¿Pasa? |
|---|---|---|---|
| 2.1 · 0° | | | |
| 2.2 · 90° | | | |
| 2.3 · 180° | | | |
| 2.4 · 270° | | | |
| control (sin GPIO25) | | | |

## Prueba 3 · CAN aislado

| # | Medido | ¿Pasa? |
|---|---|---|
| 3.0 GND ESP ↔ GND_bus | maje: «ya quedaron todas», sin números | sí, sin números |
| 3.1 B0505S 4–3 | maje: «ya quedaron todas», sin números | sí, sin números |
| 3.2 VOA | maje: «ya quedaron todas», sin números | sí, sin números |
| 3.3 prueba_can | **20/20** transmitidas, recibidas e idénticas; errores TX 0 / RX 0 (21-nov, COM6) | sí |
| 3.4 control sin VDD2 | recibidas: **0** (transmitió 1 de 20, errores TX 128: nadie confirma la trama) | sí, el control falla como debe |

## Prueba 4 · Los tres juntos

| # | Qué pasó | ¿Pasa? |
|---|---|---|
| compila rig.ino | | |
| 4.1 | | |
| 4.2 | | |
| 4.3 | | |
| 4.4 (CAN con master falso) | | |
| 4.5 watchdog | | |
| 4.6 sin rearme no vuelve | | |
| 4.7 paro: 182 a cero | | |
| 4.8 ventana cerrada | | |
| 4.9 USB fuera | | |

## Notas / errores tal cual

- **G1, comparado con los logs anteriores (`herramientas/can/logs/`):** ningún ID nuevo. Los 38 de hoy están
  todos en los del 06-oct (56). Mismos nodos que transmiten: 1, 2, 3, 4, 7, 8, 30. **5, 6 y 10 siguen sin
  transmitir nada en un equipo completo**: solo aparecen los PDO que el Master les manda (`205/206/20A`,
  `305/30A/40A`). Lo que faltó hoy y estaba el 06-oct es de arranque o de fallas (NMT `000`, boot-ups `704/707/708/71E`,
  EMCY `084/087/088/09E`, SDO del arranque `602/61E`, `6E3/6E9/6EF/6F1/69D`): hoy se empezó a escuchar con el equipo
  ya prendido, y en ~85 s **no hubo ningún EMCY**.

- **Compilación con esp32 3.3.12 (21-nov, antes de ir al equipo):** `pie.ino`, `escucha_can.ino` y
  `multipiloto_campo.ino` compilan. **`rig.ino` no compilaba:** `'EstPie' was not declared in this scope`
  y `'nPie' cannot be used as a function` (el prototipo automático de Arduino queda arriba del `enum`).
  Corregido: `nPie(EstPie e)` → `nPie(int e)`. Solo el nombre del estado para imprimir; la lógica no cambia.
  Ahora compila (307 KB).
- **`herramientas/emulador_timon/` no compila como carpeta:** tiene dos `.ino` (`caracterizador_timon` y
  `emulador_timon`) y Arduino los junta (`redefinition of 'void setup()'`). `emulador_timon.ino` solo, en
  su propia carpeta, compila. Para cargarlo: copiarlo a una carpeta `emulador_timon/` aparte.

## Equipo (EQUIPO_HOY.md)

| # | Resultado |
|---|---|
| A1 estado del equipo | |
| A2 placa / serie | |
| A3 foto del conector | |
| B1 pines 1–4 ubicados | |
| B2 pin 3 ↔ negativo de batería | |
| C1 pin 1 vs 3 | V |
| C2 pin 2 vs 3 | V |
| C3 pin 4 vs 3 | V |
| D1 eventos con todo original | |
| D2 al pisar | |
| D3 sin pisar: pin 2 / pin 4 · pisado: pin 2 / pin 4 | |
| E1 entre ejes izq / der | |
| E2 sensores en ruedas de carga | |
| E3 vueltas tope a tope | |
| G1 CAN aislado escuchando (errores) | **pasa.** `escucha_can.ino` (LISTEN_ONLY, 250k) por la cadena aislada, equipo prendido: **err RX 0 · perdidas 0** en 4 resúmenes seguidos (70–85 s); 38 identificadores; ~1 090 tramas/s (21 861 en 20 s). Nodos vistos: 1 Master, 2 Multi-Pilot 1, 3 Display, 4/5/6 Dirección, 7 Elevación, 8 Tracción, 10 Multi-Pilot 2, 30 PC de servicio; SYNC 080 a ~50 Hz |
| G2 multipiloto: E4809 se va / a 100 → E1903 | |
| G3 pedal emulado: suelto = real suelto / pisado sin 1.06 / m suelta | |
| G4 timón emulado: nodo 4 acepta / sentido | |
