# La simulación del pasillo — un turno del EDR18N2 (09-nov-2026)

> **24-nov · ahora con el modelo v4.** `simulacion.html` usa las rutas del planificador con la geometría medida:
> entre ejes **1.688**, la rueda motriz **corrida 0.325 bajo el timón** (a la izquierda mirando hacia las uñas) y
> topes **−104.4° / +79.4°** (`analisis/rutas_resultados.md`, v4). En el plano se dibuja la motriz en su lugar, la
> rueda de apoyo en la otra esquina y, cuando la rueda va cruzada, **el centro de giro** (punto celeste): donde la
> línea del eje de la rueda corta la del eje de carga.
>
> | Decía (09-nov, v3b) | Es (24-nov, v4) | Qué lo tumbó |
> |---|---|---|
> | rueda en el centro, entre ejes 1.562, timón a ±90° | corrida 0.325, 1.688, topes −104.4 / +79.4 | medidas del 23-nov |
>
> La del 09-nov sigue en **`simulacion_v3b.html`** (datos en `sim_datos_v3b.json`, que es lo que usa
> `percepcion/visibilidad_v3.py`). Regenerar: `python sim/exportar.py` + `python sim/build.py` (v4);
> `python sim/exportar.py --v3b` + `python sim/build.py v3b` (la vieja).

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
lado, **cerrado con pared en las dos puntas**: 3.07 m antes del primer poste y 3.05 m después del último.
En esos dos huecos, **del lado R**, están las zonas del montacargas humano (maje, 09-nov):

- **zona de descarga**, junto al primer rack: ahí TaTa deja lo que sale y el humano lo recoge;
- **zona de carga**, junto al último rack, del mismo ancho: ahí el humano deja lo que entra.

Se activa con `bahias.geometria('dxf')`: la descarga es la «bahía» 0 y la carga la 14, las dos al piso.
Sin eso, todo el repo sigue con la geometría de siempre y da los mismos números.

**Lo que sale del modelo:** en la zona de descarga el equipo **solo entra y sale con las uñas hacia la
pared del principio**. Girando al revés, el culo (a 1.93 m del eje de carga) pega en la pared, que está a
1.5 m del centro del cubo. El planificador lo encuentra solo.

El turno son cuatro pedidos con ese flujo:

| # | Tipo | Qué hace |
|---|---|---|
| 1 | salida | el caso de maje: el equipo en 3L va a **5 3 Ra** y lo deja en la zona de descarga |
| 2 | entrada | de la zona de descarga a la de carga, toma el cubo y lo deja en **11 2 Lb** (tramo 2) |
| 3 | salida | de 11 2 Lb a **9 5 Rb** (N5) y a la zona de descarga |
| 4 | entrada | de la zona de descarga a la de carga y a **3 1B La** (sobre el cubo de N1) |

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
  pantógrafo no alcanzan con la punta a 3 cm de la cara). **No es supuesto, es regla (maje, 24-nov):** entra el
  1.20 entero porque el cubo es de químicos y va asentado contra el carro.
- **INCLINA / NIVELA (24-nov):** tomado el cubo, 4° hacia atrás (el máximo de la ficha) a 2.5 °/s (programa 1 de
  fábrica, `0x233A`/`0x233B`), para que el peso lo asiente contra el carro y la curva de las uñas; se viaja así y se
  nivela antes de dejar. En el panel del mástil la inclinación se dibuja ×3 para que se vea.
- **El pantógrafo va a 0.30 / 0.28 m/s (ficha), pero el programa 1 de fábrica lo limita a 0.12 (elevación libre) y
  0.10 m/s (mástil arriba)** (`0x2336`, `0x23A0`/`0x23A1`). Si el equipo está en el programa 1, cada extender o
  retraer tarda ~11 s, no ~4: la sim es optimista en ~25–30 s por pedido. Sin confirmar en qué programa está.
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
