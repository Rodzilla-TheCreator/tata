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
| 3.0 GND ESP ↔ GND_bus | | |
| 3.1 B0505S 4–3 | | |
| 3.2 VOA | | |
| 3.3 prueba_can | /20 | |
| 3.4 control sin VDD2 | recibidas: | |

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
