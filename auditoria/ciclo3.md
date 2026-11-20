# Auditoría — ciclo 3 (20-nov-2026): cuánto falta, qué tan sólido está, y cómo ir más rápido

## 1. El ritmo, medido (no sentido)

| Dato | Valor |
|---|---|
| Inicio del repo | 21-ago-2026 (hace 13 semanas) |
| Días con commits desde el 13-oct | **26 de 39** (~4.7 por semana) |
| Picos | 14-oct (18 commits), 02-nov (20), 19-nov (12) |
| Hitos | 03-oct el DB9 es CAN · 14-oct TJA 20/20 · **22-oct el Master acepta nuestro nodo 2** · 26-oct timón calibrado · 11-nov piezas · 16-nov sensor del pedal entendido · 19-nov emulador + firmware del pie en banco |

**Lectura:** el ritmo no es malo. En tres meses, de «no sabemos qué es este conector» a «los tres mandos
emulados en banco y el de marcha probado en el fierro». Lo que muestran los datos es **ráfagas**: días de
12 a 20 commits y huecos entre medio. Los picos coinciden con **una fecha física** (piezas que llegan, día
de equipo) o con **maje en el banco y un agente guiando paso a paso** (19-nov). Ese es tu modo más rápido.

**«Lo único que me detiene soy yo»: no del todo.** La ruta crítica hoy pasa por **la reparación del EDR**,
que no depende de vos. Lo que sí depende de vos es llegar a ese día con todo lo de banco cerrado.

## 2. Lo que falta para el hito del teleop, paso por paso

Dificultad de 1 (trámite) a 5 (puede tumbar el plan). Días = días de trabajo **enfocado**, no de calendario.

| # | Paso | Depende de | Dif. | Días | Estado |
|---|---|---|---|---|---|
| 1 | Cerrar el banco del emulador del pedal (0b, 1, 4, 6) | nada | 1 | 0.5 | casi |
| 2 | `pie.ino` P1–P6, más la prueba de la laptop congelada | 1 | 2 | 1 | código listo |
| 3 | CAN aislado armado y medido (C0–C4) | piezas en mano | 3 | 1–2 | hay dibujo |
| 4 | `rig.ino` integrado (CAN + timón + pie) + `rig.py` + `prueba_rig.py` | 2, 3 | 4 | 3–5 | sin empezar |
| 5 | Alimentación del rig desde la batería (DC-DC aislado), caja, arnés con conectores | 4 · compra del DC-DC (LCSC, 2–3 semanas) | 3 | 2–3 | sin pedir |
| 6 | Mando con control de juego (`docs/19`) | 4 | 2 | 1–2 | diseño hecho |
| 7 | **Equipo reparado.** Paso 0: conjunto real, eventos; pines del XS160; entre ejes; ruedas de carga; vueltas de volante | Miguel, repuestos | 2 | 1 | **esperando** |
| 8 | Emulador del pedal en el equipo («suelto» confirmado con `E1903.01`) | 1, 7 | 3 | 1 | — |
| 9 | Timón emulado en el equipo, y **cómo se borra la falla del nodo 4** | 7 | **5** | 1–3 | el riesgo más grande |
| 10 | Rig integrado en el equipo, rueda en el aire | 4, 5, 8, 9 | 3 | 1–2 | — |
| 11 | Arrastre, las tres pruebas de paro, dirección, con un operador en el hongo | 10 | 4 | 2 | — |
| 12 | El hito: pasillo, grabado, con distancia de paro y dispersión medidas | 11 | 3 | 2 | — |

**Total: ~17–25 días enfocados.** Al ritmo de ahora, **6 a 8 semanas de calendario**, contadas desde que
el EDR anda. Si el EDR está listo a mediados de diciembre, **el hito cae entre fines de enero y febrero de
2027**. El paso 9 es el único que puede mover eso semanas.

**Después del hito** (estimación gruesa, con más incertidumbre):

| Etapa | Qué incluye | Calendario |
|---|---|---|
| El Aula + Pasillo 0 | estantes, ArUco puestos, cámaras montadas | 2–4 semanas |
| Autonomía al piso (N1 y zonas) | odometría real, EKF con datos reales, seguimiento de ruta, FSM en el fierro | 2–4 meses |
| **Demo autónoma en Pasillo 0** | | **~mitad de 2027** |
| Altura (N2–N5) | encoder de altura, sensor en las uñas, control de mástil | +3–6 meses |
| Operación en cliente | seguridad certificada, escáner, contrato | +6–12 meses, **no una persona sola** |

## 3. Lo que dejamos sin completar

**Del banco:** emulador 0b/1/4/6 · `pie.ino` P1–P6 · CAN aislado C0–C4 · el SH-C30G (¿aislado o no?) ·
`rig.ino` (encargo del 09-nov, nunca hecho) · `sdo_lee` sin probar en banco · el DC-DC de batería sin pedir
· la regla 8 del firmware contradicha.

**Del equipo, esperando al EDR:** qué estado del pedal es «suelto» · el conector XS160 · la falla del
nodo 4 · el entre ejes · las ruedas de carga · las vueltas de volante contadas a mano · mapear qué `E190x`
dispara cada mando · la palanca trasera (`b2`) · la tensión real del pin 1 del pedal.

**De papel:** `CLAUDE.md` «Lo que falta» (septiembre), `README.md`, `docs/07`, `pendientes.md`, la fila del
emulador, `docs/24` sin el hardware del 19-nov · los logs CAN fuera del repo · el repo público.

## 4. Qué tan sólido está cada pilar

| Pilar | Solidez | Por qué |
|---|---|---|
| Marcha e hidráulica por CAN (nodo 2) | **fuerte** | probado en el fierro el 22-oct, con control |
| Dirección (emulador sen/cos) | media | calibrado en banco el 26-oct; **nunca movió la rueda**; la falla del nodo 4 sin resolver |
| Pedal (hombre muerto) | media | sensor entendido y emulador en banco; falta saber qué es «suelto» en el equipo |
| Watchdog y paro | media | firmware bien hecho, banco a medias; falta el hongo real y medir en el equipo |
| Integración (un ESP con todo) | **débil** | no empezó |
| Geometría y rutas | media | sólidas en la ficha; el pasillo real nunca se midió con el equipo adentro |
| Localización (EKF + ArUco) | **débil** | solo sintético; cero datos reales |
| Altura, uñas, seguridad certificada | **no existe** | ver ciclo 2 |
| Relación con Montasa | **fuerte** | Omar compró los repuestos sin que se lo pidieras dos veces |

## 5. Cómo ir más rápido (proyecto)

1. **Una sola lista visible con las próximas 3 acciones físicas.** Hoy el repo ofrece 25 frentes; cada vez
   que abrís `CLAUDE.md` la mente tiene que elegir entre todos. El resto existe, pero no a la vista.
2. **Llegar al día del EDR con todo el banco cerrado** (pasos 1–6). Cada hora de fierro es la más cara.
3. **Pedir ya lo que tarda en llegar:** el DC-DC de batería (LCSC), el hongo NC, la caja, los conectores.
4. **Recortar alcance:** el hito es teleop vacío. LiDAR, Isaac, flota y altura se congelan hasta después.
5. **Menos documento por cada cosa hecha.** Los agentes escriben mucho; pedirles respuestas cortas y
   actualizar solo lo que cambia.

## 6. Cómo ir más rápido (vos)

No es un diagnóstico; es lo que muestran tus propios datos y lo que suele funcionar con atención que va y
viene:

- **Repetí el formato del 19-nov:** vos en el banco, un agente guiando **una prueba a la vez** y anotando
  por vos. Fue tu día más productivo de la semana. El agente hace de «compañero de banco».
- **Bajá la energía de arranque:** dejá el banco armado la noche anterior, con la primera prueba escrita en
  un papel encima. Arrancar es lo difícil; seguir sale solo.
- **Bloques cortos con cierre visible:** 30–45 min, y cada bloque termina en algo que se ve (una foto, un
  número anotado, un commit). Perderse entre bloques no cuesta nada si cada bloque cerró.
- **Fechas externas:** el día con el Chino, el día del EDR, una fecha para Omar. Tus picos coinciden con
  fechas físicas; ponete más.
- **«Perder el ego»:** el proyecto ya tiene la cultura para eso: *decía / es / qué lo tumbó*. Equivocarse y
  anotarlo es exactamente cómo avanzó cada vez. Las tres veces que el modelo estuvo mal, encontrarlo mejoró
  el resultado.
- Si el TDAH está diagnosticado y no lo estás tratando, hablalo con tu médico: es de lo que mejor responde
  a tratamiento, y vos sos el recurso más escaso del proyecto.

## 7. Las próximas 4 semanas, si el EDR vuelve a mediados de diciembre

| Semana | Foco | Termina en |
|---|---|---|
| 1 (24–30 nov) | pasos 1–3 + pedir el DC-DC y el hongo | emulador y pie cerrados, CAN aislado 20/20 |
| 2 (1–7 dic) | paso 4 con un agente guiando | `rig.ino` pasando 1–8 en banco |
| 3 (8–14 dic) | pasos 5–6 | rig en caja, con mando, alimentado como irá en el equipo |
| 4 (15–21 dic) | pasos 7–8 si el EDR está | paso 0 hecho y medidas tomadas |
