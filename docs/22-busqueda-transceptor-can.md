# La búsqueda del transceptor CAN — para transmitir al bus

**Escrito el 13-oct-2026.** Lo vigente arriba; el historial de opciones y por qué cada una
quedó donde quedó, abajo.

## Por qué hace falta

La ruta B de `docs/21` es que un ESP32 **se haga pasar por el multipiloto** (nodo 2) en el bus
CANopen del equipo. Escuchar ya funciona (06-oct, `can/multipiloto.md`). **Transmitir no**: el
transceptor que tenemos, un módulo TJA1050, tarda **~15 µs en soltar el bus**, y a 250k un bit
dura 4 µs. Transmitir con él mete tramas corruptas en el bus y las sufren todos los nodos.

**El requisito, medido con `can/diagnostico/retardo`:** subida (TX alto → RX alto) **< 1 µs**,
con 120 Ω entre CANH y CANL. Después, `prueba_can.ino` 20/20 a 250k y su control (sin RX → 0).
**Ningún transceptor va al equipo sin pasar eso**, sea de marca o no.

## Estado al 13-oct

| Opción | Estado | Siguiente paso |
|---|---|---|
| **El TJA1050 que ya tenemos** | sospecha nueva: el lento **no sería el chip, sino la falta de terminador** | medir y repetir `retardo` (abajo) |
| **Módulo MCP2515 + TJA1050 de C&D Tecnología, L230** | **disponible en Honduras.** maje va a comprar **uno** | banco de dos nodos con nuestro TJA (abajo) |
| **Waveshare SN65HVD230 ×2**, Amazon, US$16.99 | visto; **compra sin confirmar**. Entrega en EE.UU. ~18-oct + courier | si se compra, es el candidato más limpio: 3.3 V directo al ESP32 |
| **Chip suelto** (MCP2562, MCP2551, SN65HVD230…) | preguntado a Sam Electronic; búsqueda en `herramientas/can/donde_conseguir.md` | talleres de electrónica automotriz y yonkes |
| **MCP2551 del ELM327 de Montasa** | identificado, **no se toca**: no es nuestro | si hace falta, comprar un ELM327 propio (C&D, L290) para desarmar |
| Banco de diodos, sin transceptor | código listo (`can/banco_imitador/`) | **solo mesa, nunca el equipo** — sirve para avanzar el imitador mientras tanto |

## El TJA1050 que tenemos — qué tiene

Fotos `herramientas/can/tja1050_modulo_frente.jpg` y `_reverso.jpg` (13-oct).

- **La posición `R3`, junto a CANH/CANL, está vacía**: es donde iba el terminador de 120 Ω del
  módulo, que maje quitó. Cuadra con lo que dijo
- Bornes de VCC/TX/RX/GND con soldadura abundante y resto de flux; CANH/CANL soldados por
  ambas caras, con cables sueltos

**La hipótesis, con el número:** al soltar el bus, la línea vuelve a recesivo descargándose por
lo que haya entre CANH y CANL. **Sin terminador** solo queda la entrada del propio chip (25–75 kΩ
según la hoja): 50 kΩ × ~300 pF de módulo y cables ≈ **15 µs**, que es justo lo medido. **Con
120 Ω**: 120 Ω × 300 pF ≈ **0.04 µs**. El `LEEME` del 05-oct dice «igual con o sin
terminación», lo que no cuadra con la física: puede que la resistencia del banco no hiciera
contacto. **No se da por cierto: se mide.**

```
□ 1. (opcional, 10 s) Apagado. Continuidad entre bornes vecinos: VCC–TX, TX–RX, RX–GND.
     maje objetó con razón: este módulo ya escuchó el equipo (06-oct, 0 errores a 250k) y el
     retardo midió la bajada en 0.36 µs. Eso prueba VCC, GND, RX, CANH/CANL y que el TX baja
     el bus. Un puente de estaño no explica una SUBIDA lenta con todo lo demás sano
     **13-oct, medido:** VCC–GND ≈ 1570 Ω, RX–GND ≈ 1600 Ω, el resto abierto; nada pitó.
     Es lo normal en un circuito con chips (diodos de protección internos, y lo que cuelgue
     del ESP32); un puente daría ~0 Ω. **Sin puentes**
□ 2a. **13-oct, medido:** CANH↔CANL sin nada puesto, apagado → solo da lectura en la escala de
     2 MΩ (cientos de kΩ o más). **El módulo no tiene terminador.** Con eso, al soltar el bus la
     línea se descarga por cientos de kΩ: unos pocos cientos de pF bastan para los ~15 µs
□ 2. Apagado. CANH ↔ CANL en las patas del módulo, escala de ohmios:
       sin nada puesto → decenas de kΩ (confirma que no hay terminador)
       con la 120 Ω del banco puesta → ~120 Ω. Si no da eso, la resistencia no hace contacto
□ 3. Con ~120 Ω confirmados: retardo. Subida < 1 µs → el chip está sano
□ 4. Si sigue lento: alimentarlo con 5.0 V firmes (no del pin del ESP32), medir VCC durante
     la prueba (la hoja pide 4.75–5.25 V), repetir
□ 5. Si sigue lento: es el chip. Se descarta
```

**En el equipo el terminador sigue fuera**: el bus ya tiene el suyo (120 Ω medidos entre los
pines 3 y 8 del DB9). Ponerle otro es modificar el bus, y eso es decisión aparte.

## El banco de dos nodos: MCP2515 + nuestro TJA

Con un solo MCP2515 y el TJA ya arreglado, quedan dos nodos de verdad que se dan ACK entre sí:

```
ESP32 A + TJA1050 (TWAI)  ──CANH/CANL──  MCP2515 (SPI) + ESP32 B
   120 Ω en el lado del TJA                 J1 puesto (su 120 Ω)
                  → 60 Ω en total, como un bus real
```

- Prueba: tramas en los dos sentidos, 20/20. **Control:** quitar CANH de un lado → 0
- **El MCP2515 va por SPI**, no por el TWAI: hace falta librería (ACAN2515 o mcp_can) y adaptar
  el imitador
- **Cristal de 8 MHz** (se ve «8.000» en la foto de la tienda): hay que declararlo en el
  código, o la velocidad sale mal
- **Las salidas SO (MISO) e INT del módulo salen a 5 V**: divisor hacia el ESP32
- **J1 es su terminador**: puesto en la mesa, **fuera en el equipo**
- Su transceptor también es un TJA1050: es el mismo modelo, de otro lote. Si este banco falla,
  no se sabe de cuál de los dos es la culpa; si pasa, valida a los dos

## Historial — lo que se evaluó y por qué quedó así

| Opción | Veredicto | Por qué |
|---|---|---|
| Convertidor serie TTL → CAN (C&D, L500) | **descartado** | un microcontrolador con firmware cerrado en el medio decide cómo arma las tramas; casi seguro manda ACK al escuchar (rompe el solo-escucha); un DIP suele ser el terminador; más caro que lo que el ESP32 ya hace adentro |
| Transceptor hecho con transistores y resistencias | **descartado** | si falla en dominante, cae el bus entero (master, dirección, tracción); no tiene la protección de dominante por tiempo de un chip; el problema que ya tenemos es justamente soltar el bus a tiempo |
| Bus de diodos entre dos ESP32 | **solo banco** | una línea de 3.3 V, no diferencial; sirve para escribir y probar el imitador, **nunca va al equipo** |
| Usar el ELM327 entero como interfaz | **descartado** | firmware de clon, dudoso al escuchar, y por serie no alcanza para ~1000 tramas/s |
| Desoldar el MCP2551 del ELM327 | **en pausa** | el ELM es de Montasa; «no lo ocupan» no es permiso para romperlo. Si hace falta, se compra uno propio |
| Módulo MCP2515 | **primero «no», después «sí»** | se descartó por traer otro TJA1050 y por los 5 V. Se corrigió: miles lo usan a 500k en carros, lo más probable es que nuestro TJA sea una unidad mala o mal probada, y está en Honduras |
| Comprar dos MCP2515 | **uno** | decisión de maje: el segundo nodo es nuestro TJA |

## Dónde se busca en Honduras

`herramientas/can/donde_conseguir.md`: qué pedir por número completo, talleres de electrónica
automotriz, yonkes del Barrio Medina, car audio, y las tiendas preguntadas. Las tiendas de
electrónica de acá venden LED, Arduino y repuestos de TV; **los transceptores CAN viven en los
carros**, y de ahí es más fácil sacarlos.
