# Encargo — rutas v3: la silueta de la ficha, con 2.91 de culo a punta

> **HECHO 06-nov-2026 en la i3.** Sección «v3» de `rutas_resultados.md`; `rutas_v3.json` y `ruta_3L_5R_v3.png`.

**Para la sesión de i3.** Sigue a `tarea_rutas_v2.md`. Leé `CLAUDE.md`, `herramientas/fichas/LEEME.md`
(entero) y las secciones del final de `analisis/rutas_resultados.md` («Del manual y de la ficha» y
«Las fichas técnicas»). Mirá `herramientas/fichas/vista_superior_etr335d.png`.

## Qué cambia en el modelo

El EDR18N2 es el **Jungheinrich ETR 335d**. Las fichas y el manual dan lo que antes era supuesto:

| | v2 (05-nov) | **v3** | Fuente |
|---|---|---|---|
| Largo culo → punta de uña | 2.90 (`LCH` 1.70 + `FLEN` 1.20) | **2.91**, fijo | **medido por maje. Manda** |
| Uñas | 1.20 | **1.20** (adaptadas, no las de fábrica de 1.067) | maje, 06-nov |
| Esquina del culo | en ángulo recto | **radio 0.17 m** (±3 cm) | dibujo de la ficha VDI, ajuste de círculo |
| Ancho del culo | 1.065 | 1.065 | medido (la ficha da 1.054) |
| Tope de dirección δmax | derivado, 78° → supuesto 84° | **90°** (modo de dirección 180°/360°) | manual de servicio, eventos `1.71`/`1.72` |
| `XPIV` (culo → eje de carga) | 1.50 → 1.60 | **2.91 − 1.20 + 0.219 = 1.93** | ficha: el eje de carga está 0.219 (`x`) delante del dorso de las uñas |
| Empuje del pantógrafo | 0.61 | **1.067** (doble profundidad) | ficha EDR18N2 / ETR 335d |
| Patas `W_MAX` | 1.315 | 1.315 (sin medir) | — |

**No busques más el largo en la ficha:** el 2.91 medido manda. La ficha estándar da 2.65–2.78; la
diferencia se explica con las uñas adaptadas y, probablemente, el compartimento de batería largo.
Anotalo como dato en tensión y seguí. `XPIV` = 1.93 queda **derivado**: barrélo **1.80–1.95**.

**La cuenta que tiene que reproducir el planificador** (ancho a rumbo, `herramientas/fichas/LEEME.md`):
con esquina de 0.17, **3.005 m vacío y 3.043 m con el IBC**. Entre postes caben 3.12.

## Qué hacer

1. **Silueta v3** en `planificador_rutas.py` (`modelo='v3'`), con lo de la tabla: esquinas del culo
   redondeadas, 2.91 de largo total, `XPIV` de la tabla, **δmax = 90°**. Mantené v1 y v2 reproducibles.
2. **Correr la batería v2 con v3:** postes cada 2.47, retranqueo de 6 cm en los dos lados, giro sin
   reversa (el del video), el caso de maje `3L → 5R → descarga` y el barrido de las 28.
3. **Sensibilidad:** radio del culo 0.10 / 0.17 / 0.24; `XPIV` 1.80 / 1.93; retranqueo 3 / 6 cm.
   ¿Con qué combinaciones sale el giro **vacío sin retranqueo** (todo dentro de 3.00)? ¿Y cargado?
4. **Control de falsación:** con culo en ángulo recto y retranqueo 0, el giro cargado **no** tiene
   que salir (3.088 > 3.00). Si sale, algo no está restringiendo.
5. **El pantógrafo a 1.067** en `percepcion/fsm_estados.py` (`EXT_MAX`) y donde se use. Las pruebas
   de la FSM tienen que seguir pasando.
6. **Actualizar `clases/giro.html`** (la clase 5): largo 2.91, esquina de 0.17 por defecto en el
   deslizador, y en la sección 5 que δmax = 90° salió del manual (la cuenta de los 83° queda como
   historia: lo que pedía el video).

## Entregables

- `planificador_rutas.py` con `modelo='v3'`, `rutas_resultados.md` con la sección v3 (tabla decía /
  es / qué lo tumbó contra v2), `rutas_v3.json`, y la figura del caso de maje.
- La FSM con `EXT_MAX` 1.067 y sus pruebas en verde; la clase 5 actualizada.
- Una línea en `CLAUDE.md` (fila de `analisis/` y la tabla de geometría de «Corregido en campo»:
  `XPIV`, δmax y pantógrafo, con decía / es).
- Commit y push a `main`.

## Lo que NO es esta tarea

- No es medir: el radio del culo de la ficha es esquemático (±3 cm). Si maje mide otro, se cambia
  el número y se vuelve a correr.
- No es tocar `sim-web/` ni el fierro.
