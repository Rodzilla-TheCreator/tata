# Banco del imitador — el multipiloto falso, sin transceptor · 07-oct-2026

**Para qué:** programar y probar la ruta B de `docs/21` (un ESP32 que se hace pasar por el
nodo 2) **antes** de tener un transceptor que sirva para transmitir. El TJA1050 que tenemos
escucha bien pero tarda ~15 µs en soltar el bus (`can/LEEME.md`), y en Honduras no aparece un
SN65HVD230 de estante.

## ⚠ Esto NUNCA va al montacargas

El bus de diodos es **de una sola línea, a 3.3 V**. El del equipo es **diferencial**
(CANH/CANL) y comparte cable con el master, la dirección, la tracción y la elevación. Al
equipo solo se va con un **transceptor de verdad**, con su protección de dominante por
tiempo, y con el multipiloto real **desenchufado**. Y con las condiciones del peldaño 5 de
`pendientes.md`.

## El cableado — CAN sin transceptor

```
ESP32 A  GPIO21 (TX) ──|◄── 1N4148 ──┐
ESP32 B  GPIO21 (TX) ──|◄── 1N4148 ──┤
                                     ├──── LÍNEA ──── 4.7 kΩ ──── 3.3 V
ESP32 A  GPIO22 (RX) ────────────────┤
ESP32 B  GPIO22 (RX) ────────────────┤
(ESP32 C GPIO22, si hay un tercero escuchando) ┘

GND de todas las placas unidos
```

El diodo apunta **hacia el TX** (cátodo, la raya, del lado del ESP32): cada TX solo puede
**bajar** la línea (dominante) y la resistencia la devuelve a alto (recesivo). Cables cortos.

## Las placas

| Placa | Sketch | Para qué |
|---|---|---|
| A | `master_falso/` | hace del master: espera el boot-up, lee `0x1000`, manda NMT START y vigila el `0x182` |
| B | `multipiloto_falso/` | hace del nodo 2: boot-up, contesta, y manda `0x182` + heartbeat con lo que se le escriba por serie |
| C (opcional) | `../escucha_can.ino` | tercer testigo en LISTEN_ONLY, el mismo instrumento del equipo |

**Con dos alcanza.** El tercero sirve para que lo que se ve en la mesa salga del mismo
programa que se usó en el equipo, y así compararlo con `multipiloto.md` línea por línea.

## La prueba, con sus controles

1. Encender A, después B. En A tiene que salir, en orden: `702 00 boot-up` → `582 … OK` →
   `NMT START` → tramas `182`
2. En el monitor de B escribir `a 100`: en A, `adelante/atras 100 ADEL`. Escribir `n`: en A,
   `botones N`, y el byte 7 en `FF`
3. **Control del watchdog:** dejar de escribir en B. En 200 ms B avisa `WATCHDOG` y en A el
   `182` vuelve a todo cero
4. **Control del 8.08:** desconectar el diodo de B. A tiene que avisar `8.08 SIMULADO`. Si
   no avisa, el vigilante de A no vigila nada
5. **Arranque en cero:** reiniciar B. Hasta el NMT START no debe salir ningún `182`, y el
   primero tiene que venir en cero aunque antes se haya escrito `a 100` (regla 4 de `docs/20`)

Qué pasa si el master real se reinicia con el multipiloto andando **no se sabe**: el sketch
sigue operacional. Se ve en un log del equipo con un ciclo de llave.

## Lo que todavía es SUPUESTO

`PERIODO_182_MS = 20` y `PERIODO_HB_MS = 500` **no están medidos**. Salen del log del 06-oct
(`can/logs/escucha_equipo_20261006-120519.log`): cada cuánto aparece `182` y cada cuánto
`702 05`. Hasta reemplazarlos, el imitador no se parece al real en el tiempo.
