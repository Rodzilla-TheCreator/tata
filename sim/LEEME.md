# La simulación del pasillo — un turno del EDR18N2 (09-nov-2026)

`simulacion.html` es un solo archivo: abrilo en el navegador. Junta en una línea de tiempo todo lo que el
repo sabe hoy del pasillo de 3.00 m:

| Qué | De dónde |
|---|---|
| Rutas (Hybrid A*, modelo **v3b**: 2.91 m, culo de la ficha, timón a 90°, postes cada 2.47 con 6 cm de retranqueo) | `analisis/planificador_rutas.py` |
| Etapas de la FSM (RECTA → GIRO → ELEVA → APROXIMA → EXTIENDE → TOMA o DEPOSITA → RETRAE → RETROCEDE → BAJA → DESGIRA → TRANSITO → DEJA) | `percepcion/fsm_rutas.py`, `fsm_estados.py` |
| Elevación 0.84 / 0.55 m/s, descenso 0.57 / 0.53, empuje 0.30 / 0.28 m/s, pantógrafo 1.067 | ficha VDI del ETR 335d (`herramientas/fichas/`) |
| Margen al poste o a la cara del cubo de N1, en cada instante, y qué parte lo da | la misma geometría del `Mundo` v2/v3 |
| Qué ArUco ve cada cámara (montaje A2, marcas cada 2 bahías) | `percepcion/visibilidad.py` |
| El rig: latido de la laptop, watchdog de 200 ms, pie, paro de hongo, rearme manual | `docs/24`, `herramientas/rig/tarea_firmware.md` |

**El pasillo es el B de RETHINK según el DXF** (`datos/sectorA.json`, filas verde | azul), no el tramo
de 7 bahías que usaba el planificador hasta ahora: **7 bahías, un hueco de 2.66 m sin rack, 6 bahías** por
lado, y **3.05 m** del último poste a la pared del fondo. Ahí, **junto al último rack del lado R, está la
zona de carga** (maje, 09-nov): el montacargas humano deja los cubos que entran. Los que salen los recoge en
el principio del pasillo (`docs/09`). Se activa con `bahias.geometria('dxf')`; sin eso, todo el repo sigue
con la geometría de siempre y da los mismos números.

El turno son cuatro pedidos con ese flujo:

| # | Tipo | Qué hace |
|---|---|---|
| 1 | salida | el caso de maje: el equipo en 3L va a **5 3 Ra** y lo deja en el principio |
| 2 | entrada | del principio a la zona de carga, toma el cubo y lo deja en **11 2 Lb** (tramo 2) |
| 3 | salida | de 11 2 Lb a **9 5 Rb** (N5) y al principio |
| 4 | entrada | del principio a la zona de carga y a **3 1B La** (sobre el cubo de N1) |

## Regenerar

```
python sim/exportar.py      # ~15 min: 8 rutas del planificador
python sim/build.py         # escribe sim/simulacion.html con los datos adentro
```

## Lo que es SUPUESTO (no medido)

- Marcha: **`VMAX` 1.5 m/s no es supuesto**: es el sobre del kit (`CLAUDE.md`) y cae dentro de los
  **5–8 km/h (1.4–2.2 m/s) que dicen los operadores de RETHINK**. Sí son supuestos `VMAN` 0.35 m/s con mucho
  timón y `ACC` 0.9 m/s² (los del planificador).
- Freno al soltar el pie: **1.2 m/s²** (solo en la página).
- Altura de viaje de las uñas 0.05 m; cada etapa quieta dura al menos 0.8 s.
- APROXIMA / RETROCEDE: el equipo avanza 0.163 m para que las uñas entren los 1.20 del IBC (1.067 de
  pantógrafo no alcanzan con la punta a 3 cm de la cara).
- `X0` 3.00 m (del punto donde se deja la salida al primer poste) y la zona del principio (6 × 3 m): el DXF
  tiene muros con aberturas a 3.07 m del primer poste y no se sabe por dónde pasa el humano.
- El hueco de 2.66 m entre tramos se trata como si fuera cara de rack (conservador): no se sabe si es un
  pasillo cruzado o una columna. El segundo tramo mide 14.94 en el modelo y 14.91 en el DXF.
- `PX_MIN` 20 px, `ANG_MAX` 60°.

## Lo que la simulación no hace

- **No re-planifica.** Las rutas están calculadas de antemano; la página las reproduce. El paro y el
  rearme frenan y retoman la misma ruta.
- Al rearmar en EXTIENDE, TOMA o RETRAE vuelve al principio de EXTIENDE. Es un atajo: la FSM real deshace
  en orden (`fsm_falla.py`) y no reanuda sola.
- Un solo equipo en un solo pasillo: la coordinación A/B y la reserva están en `percepcion/sim_coordinacion.py`.
- El margen se calcula en planta, con las uñas al piso. No ve alturas.
