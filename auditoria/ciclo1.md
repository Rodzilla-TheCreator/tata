# Auditoría del repo — ciclo 1 (20-nov-2026)

Sin encargo previo: se revisó todo el repo (186 commits, 350 archivos). Se corrieron las pruebas, se
probaron los builds, se revisó el firmware del pie línea por línea y el dibujo del CAN aislado pata por
pata, se buscaron referencias rotas y se cruzaron los documentos entre sí. **No se cambió nada**, salvo
este archivo.

## Lo que está bien (verificado, no supuesto)

| Qué | Cómo se comprobó |
|---|---|
| EKF con rueda motriz | `percepcion/prueba_ekf_rueda.py`: **PASA** las 3 pruebas, con sus controles |
| FSM y coordinación A/B | `percepcion/sim_coordinacion.py`: **PASA** (22 etapas, vuelta donde la da el planificador) |
| Simulación sintética | `sim_sintetico.py` pasa; solo revienta al final por la figura (aquí no hay matplotlib) |
| Simulación del pasillo | `sim/build.py` reproduce `simulacion.html` byte a byte |
| Pages | los 20 enlaces de `index.html` existen |
| Simulador web | 5 de 6 pruebas de `sim-web/tests` sin errores (ver la 10) |
| `pie.ino` (i3, 19-nov) | **bien hecho**: arranca suelto, watchdog de 200 ms, rearme manual con latido fresco y paro liberado, `esp_task_wdt`, lee el paro por GPIO35 para que **destrabar el hongo no vuelva a pisar solo**. Pruebas de control pensadas en las mismas compilaciones |
| `protoboard_aislado.svg` (i3) | **correcto pata por pata**: GPIO22→VIB→VOB→TX, RX→VIA→VOA→GPIO21, VDD1 a 3V3, B0505S 1-GND 2-Vin 3-0V 4-+Vo, ninguna conexión cruza la barrera salvo el DC-DC y el ADuM |
| Emulador del pedal | banco del 19-nov: suelto sin alimentación, en reset y con el ESP desenchufado; pisa con 3V3; el paro suelta |

## Hallazgos, de más a menos grave

### Alta

1. **El repo es público y tiene cosas que probablemente no deberían estarlo.** El correo personal de
   maje (`docs/08`, `docs/14`), el **manual de servicio de Jungheinrich completo** (21 MB, con derechos) y
   las páginas escaneadas del manual de operador, los nombres de clientes (RETHINK/ELCATEX, Agrolibano),
   los costos y el caso de negocio que se le presentó a Omar, y nombres de personas. Decisión de maje:
   volver privado el repo (Pages desde un repo privado pide plan pago de GitHub) o separar lo público.
   Borrar un archivo no lo saca del historial.
2. **Las capturas CAN del equipo no están en el repo.** `.gitignore` excluye `*.log`, así que
   `can/logs/escucha_equipo_20261006-*.log`, citados en `multipiloto.md`, `pendientes.md` y
   `banco_imitador/LEEME.md`, existen solo en el disco de la i3. Son la única evidencia cruda del bus.
   Respaldarlos: `!herramientas/can/logs/*.log` en `.gitignore` y commit.
3. **Contradicción en las reglas del firmware.** `tarea_firmware.md`, regla 8: «el firmware no ve el paro
   ni lo necesita; no metas lógica que dependa de él». `pie.ino` ahora lo lee (GPIO35), y está bien que lo
   lea: sin eso, destrabar el hongo volvía a pisar solo (ISO 13850). Hay que reescribir la regla: **el
   paro corta por hardware siempre; el firmware lo lee solo para no re-pisar sin rearme**, nunca para
   cortar.
4. **`pie.ino` viene con `REARME_POR_SERIE 1` por defecto** (la laptop puede rearmar). El comentario dice
   que en el equipo va en 0, pero un flag que hay que acordarse de cambiar se olvida. Mejor al revés: 0 por
   defecto y 1 solo en una compilación de banco, o que `pie.py` lo pida y el ESP lo anuncie fuerte al
   arrancar. **Y falta la prueba que `docs/17` §1.1 llama «la que de verdad importa»:** el proceso
   **congelado sin morir** (no matado). En `pie.py` es una tecla que bloquee el lazo 1 s.

### Media — documentos que pueden hacer meter la pata

5. **«Lo que falta, en orden» de `CLAUDE.md` quedó en septiembre-octubre.** Su §2 («lo urgente») todavía
   pide las cuatro mediciones para saber si el DB9 es CAN y las pasadas de `escucha_edr` (resuelto el
   03-oct), y no menciona nada del camino actual (rig, reparación del EDR, hito del teleop). Igual de
   viejos: `docs/07` (21-ago), `README.md` (21-ago: «prototipo pendiente de aprobación», apunta al deck
   viejo de Omar, no lista `herramientas/`, `percepcion/`, `sim/`) y `herramientas/pendientes.md`, que
   `CLAUDE.md` marca como «empezar por acá» y está en el 14-oct.
6. **Filas viejas en `CLAUDE.md`:** `emulador_pedal/` dice «alto directo o por 47 k con un puente» (ahora
   47 k fija); la de `fichas/` dice «el culo tiene esquinas de ~0.17, no es un arco», al revés de lo
   medido el 07-nov; «Control Obed… 2.6 vueltas» (el simulador ya usa 5.5 desde el 23-oct); no hay fila
   para `herramientas/rig/`.
7. **`docs/24` no tiene el hardware del 19-nov.** «El pie — circuito» y el mapa de pines siguen con el
   DPDT + 2N2222; faltan los módulos de relé, **GPIO27 directo al IN con 10 kΩ a DC−**, y **GPIO35 leyendo
   el paro** (divisor 10 k / 20 k). El encargo pedía anotarlo como «decía / es».
8. **El cable amarillo del emulador en el banco es el pin 3 (− del equipo).** En el proyecto, «amarillo»
   es el GND del ESP. Son las dos tierras que **nunca** se tocan; con el mismo color, en el equipo es fácil
   unirlas. El pin 3 debería ir en azul, como el hilo del sensor.
9. **Pruebas sin correr**, para no darlas por pasadas: emulador 0b, 1 (con óhmetro), 4 y 6; `pie.ino`
   P1–P6 (código listo, sin resultados); CAN aislado C0–C4 (hay dibujo, no hay mediciones). La tarea de la
   i3 en `CLAUDE.md` sigue abierta.

### Baja — deuda

10. `sim-web/tests/*.js` apuntan a `/home/claude/rundown/…`, una ruta de una sesión vieja: no corren
    desde el repo. `tedr.js` falla (el selector `#seg-esq` ya no existe). `sim-web/build.py` tampoco corre
    como dice `CLAUDE.md`: busca `almacen3d.json` en `sim-web/` (está en `datos/`), escribe en la carpeta
    actual y no en `dist/`, y sigue con el bug de encoding.
11. `percepcion/odometria.py` imprime «tope de dirección 78°»: es la fórmula vieja. No afecta al EKF con
    `rueda=True`, pero confunde.
12. **`CLAUDE.md` pesa 59 KB (~15 000 tokens que carga cada sesión).** 175 líneas son la historia del DB9
    serie, resuelta el 03-oct. Se puede mover a un `docs/26` (sin borrar nada) y dejar un resumen de 10
    líneas.
13. Siguen abiertas de la lista de deuda: `--nivel scrappy` en `sim-isaac/tata_sim.py` y el veredicto de
    `probador.py`. La tabla de `docs/` en `CLAUDE.md` está desordenada (24 antes que 23, 25 antes que 22).
14. La ráfaga de basura en el serie al volver los 5 V (19-nov) es el arranque de los dos relés bajando el
    5 V del USB. En el equipo, ESP y relés comparten el power bank: un capacitor de 470 µF en el VCC de los
    módulos, o alimentarlos aparte.

## Lo que haría con los ciclos 2 y 3

- **Ciclo 2, correcciones sin riesgo:** 2, 3, 5–8, 10–13 (documentación, respaldo de logs, reglas). Lo
  1 es decisión de maje y lo 4 toca firmware: se proponen, no se hacen sin su visto bueno.
- **Ciclo 3, a fondo en lo que no se revisó aquí:** `docs/10`, `docs/19` a `docs/21`, `emulador_timon`,
  `multipiloto_campo` (el código que ya manda en el equipo) y `sim-isaac/`.
