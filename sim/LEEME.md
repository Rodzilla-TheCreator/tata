# La simulación del pasillo — un turno del EDR18N2 (09-nov-2026)

`simulacion.html` es un solo archivo: abrilo en el navegador. Junta en una línea de tiempo todo lo que el
repo sabe hoy del pasillo de 3.00 m:

| Qué | De dónde |
|---|---|
| Rutas (Hybrid A*, modelo **v3b**: 2.91 m, culo de la ficha, timón a 90°, postes cada 2.47 con 6 cm de retranqueo) | `analisis/planificador_rutas.py` |
| Etapas de la FSM (RECTA → GIRO → ELEVA → APROXIMA → EXTIENDE → TOMA → RETRAE → RETROCEDE → BAJA → DESGIRA → TRANSITO → DEJA) | `percepcion/fsm_rutas.py`, `fsm_estados.py` |
| Elevación 0.84 / 0.55 m/s, descenso 0.57 / 0.53, empuje 0.30 / 0.28 m/s, pantógrafo 1.067 | ficha VDI del ETR 335d (`herramientas/fichas/`) |
| Margen al poste o a la cara del cubo de N1, en cada instante, y qué parte lo da | la misma geometría del `Mundo` v2/v3 |
| Qué ArUco ve cada cámara (montaje A2, marcas cada 2 bahías) | `percepcion/visibilidad.py` |
| El rig: latido de la laptop, watchdog de 200 ms, pie, paro de hongo, rearme manual | `docs/24`, `herramientas/rig/tarea_firmware.md` |

El turno son cuatro pedidos: el caso de maje (equipo en 3L → **5 3 Ra** → descarga), y desde la descarga
**2 1A Lb** (N1 al piso), **7 5 Rb** (N5, al fondo) y **4 2 La**.

## Regenerar

```
python sim/exportar.py      # ~11 min: 8 rutas del planificador de ~80 s
python sim/build.py         # escribe sim/simulacion.html con los datos adentro
```

## Lo que es SUPUESTO (no medido)

- Marcha: `VMAX` 1.5 m/s recto, `VMAN` 0.35 con mucho timón, `ACC` 0.9 m/s² (los del planificador).
- Freno al soltar el pie: **1.2 m/s²** (solo en la página).
- Altura de viaje de las uñas 0.05 m; cada etapa quieta dura al menos 0.8 s.
- APROXIMA / RETROCEDE: el equipo avanza 0.163 m para que las uñas entren los 1.20 del IBC (1.067 de
  pantógrafo no alcanzan con la punta a 3 cm de la cara).
- Geometría del rack (7 bahías, zona de descarga de 6 × 3 m), `PX_MIN` 20 px, `ANG_MAX` 60°.

## Lo que la simulación no hace

- **No re-planifica.** Las rutas están calculadas de antemano; la página las reproduce. El paro y el
  rearme frenan y retoman la misma ruta.
- Al rearmar en EXTIENDE, TOMA o RETRAE vuelve al principio de EXTIENDE. Es un atajo: la FSM real deshace
  en orden (`fsm_falla.py`) y no reanuda sola.
- Un solo equipo en un solo pasillo: la coordinación A/B y la reserva están en `percepcion/sim_coordinacion.py`.
- El margen se calcula en planta, con las uñas al piso. No ve alturas.
