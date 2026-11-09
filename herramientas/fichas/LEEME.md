# Fichas técnicas del EDR18N2 (= Jungheinrich ETR 335d)

| Archivo | Qué es |
|---|---|
| `mitsubishi_esr15n2_edr18n2_brochure.pdf` | Brochure MCFA 03/2022 (`MEHN0300-03`). Columna **EDR18N2 «Double Deep Reach»** |
| `jungheinrich_etr_hoja_tecnica.pdf` | Hoja técnica VDI 2198, ETR 230/235/340/345/**335d**, 04/2016 |

El EDR18N2 es el **ETR 335d** (doble profundidad): las dos fichas coinciden fila por fila.

## Lo que dicen (EDR18N2 / ETR 335d)

| Cota | Valor | Fila |
|---|---|---|
| Entre ejes `y` | **1,562** | VDI 1.9 · MCFA 38 |
| Distancia a la carga `x` (eje de carga → dorso de uñas, retraído) | **219** | VDI 1.8 |
| Largo hasta el dorso de las uñas `l2` | **1,582** | VDI 4.20 · MCFA 16 |
| Largo sobre los brazos porteadores `l7` | **1,983** | VDI 4.37 · MCFA 15 |
| Ancho del chasis `b2` | **1,054** | VDI 4.21 · MCFA 17 |
| Ancho sobre los brazos `b1` (con 1,067 entre brazos) | 1,321 | VDI 4.21 |
| Ancho del brazo porteador | 127 (5") | MCFA 14 |
| Uñas `s/e/l` | 36 / 100 / **1,067** | VDI 4.22 |
| Ancho exterior sobre uñas `b5` | 305 / 802 | VDI 4.25 |
| **Empuje (pantógrafo) `l4`** | **1,067** | VDI 4.28 · MCFA 12a |
| Radio de giro `Wa` | 1,801 (VDI) · 1,797 (MCFA) | VDI 4.35 · MCFA 23 |
| Pasillo `Ast`, palet 1000×1200 transversal / 800×1200 transversal / 800×1200 longitudinal | 2,986 / 2,836 / 3,060 | VDI 4.33 |
| Compartimento de batería | 413 (16.25"); nota 7: **539 (21.25")** estándar con elevación > 8,430 | MCFA 51 |

## La fórmula de pasillo del fabricante (VDI 2198), comprobada

```
Ast = Wa + √((l6 − x)² + (b12/2)²) + a        a = 200 mm de margen de seguridad
```

Reproduce **exacto** las tres filas de la ficha (2,986 · 2,836 · 3,060). Supone que el equipo
**rota sobre el centro del eje de carga** (rueda motriz a 90°) y que todo el culo queda dentro de `Wa`.

Para el IBC (1.20 de fondo sobre las uñas, 1.00 de cara): **3,102 con el margen, 2,902 sin él**.
Vacío, uñas de 1,067 abiertas a 802: 2,739 sin margen. Uñas de 1,200 a 700: 2,843.

## Lo que corrige o pone en tensión

- **El empuje del EDR18N2 es 1,067 mm, no 0.61.** El 0.61 es el de los ESR (simple profundidad).
  `CLAUDE.md` y `percepcion/fsm_estados.py` (`EXT_MAX`) usan 0.61.
- **`XPIV = l2 + x = 1,801`.** El eje de carga queda a ~1.80 m del culo (ficha estándar), no a 1.50.
  ~~Que coincida con `Wa` dice que el culo es un arco alrededor del eje de carga~~ **Corregido abajo:**
  el dibujo muestra esquinas redondeadas, no un arco; la coincidencia con `Wa` es aproximada.
- **El largo culo → punta estándar es 1,582 + 1,067 = 2,649**; con uñas de 1.20, 2,782. **Los 2.91
  medidos cuadran con el compartimento de batería largo (+126) y uñas de 1.20: 1,708 + 1,200 = 2,908.**
  La placa (batería de 1,050–1,180 kg, más que los 907–1,050 de la ficha) apunta a lo mismo. Si es así,
  `XPIV` y `Wa` de **este** equipo son ~13 cm más que los de la ficha. Se confirma midiendo el
  compartimento o pidiendo la configuración por la serie `82824121`.

## Dato de campo (maje, 06-nov): las uñas son adaptadas

Las uñas de este equipo **no son las de fábrica (1,067)**: son **adaptadas, casi del largo del IBC
(~1.20 m)**. Confirma el `FLEN = 1.20` medido. Quedan **13 cm** sin explicar entre la ficha con uñas
de 1.20 (1,582 + 1,200 = 2,782) y los 2.91 medidos → la hipótesis del **compartimento de batería
largo (+126)** sigue en pie, y es lo que falta confirmar.

Si se confirma (`l2` = 1,708 → `XPIV` ≈ 1,927, culo en arco con ese radio):

| | Ancho que pide el giro (rotando sobre el eje de carga) | En 3.00 m |
|---|---|---|
| vacío (uñas de 1.20, abiertas a ~0.70) | 1.927 + √(0.981² + 0.35²) = **2.97** | cabe, sobran ~3 cm |
| con el IBC (1.00 de cara) | 1.927 + √(0.981² + 0.50²) = **3.03** | **no cabe entre postes**; cabe con el retranqueo (3.12) |

Eso es justo lo que se ve en el video: cargado, el operador usa el espacio entre postes.

## La curva del culo, del dibujo de la ficha (06-nov)

`vista_superior_etr335d.png` es la vista de arriba de la hoja VDI (pág. 2), ampliada. Escala sacada
del ancho del chasis `b2` = 1,054 mm (303 px → 1 px = 3.48 mm). El dibujo es esquemático: tomar
±3 cm.

| | Del dibujo |
|---|---|
| Forma del culo | **rectángulo con las esquinas redondeadas**, no un semicírculo |
| Radio de la esquina (ajuste de círculo a 8 puntos del contorno, rms 4 mm) | **≈ 0.17 m** |
| Culo → eje de carga (línea de las ruedas de carga) | ≈ 1.77 m (la ficha: `l2 + x` = 1.80) |
| `Wa` | medido del centro del eje de carga a la esquina del culo |

**Corrige lo de arriba:** el culo no es un arco de radio `Wa`. La tabla de «si se confirma»
(2.97 / 3.03) suponía ese arco y queda reemplazada por la cuenta con el largo medido:

| Silueta: 2.91 culo → punta (medido), capó 1.065, uñas a ±0.365 | Vacío | Con el IBC |
|---|---|---|
| culo en ángulo recto | 3.045 m | 3.088 m |
| esquina de 0.10 m | 3.021 m | 3.061 m |
| **esquina de 0.17 m (ficha)** | **3.005 m** | **3.043 m** |

**Con la esquina de la ficha, vacío gira justo en 3.00, y cargado necesita ~2 cm por lado del
retranqueo entre postes (hay 6).** Calza con el video.

## El culo, de los VECTORES de la hoja (07-nov) — reemplaza el ajuste de arriba

La pág. 2 de `jungheinrich_etr_hoja_tecnica.pdf` **no es una imagen: es dibujo vectorial, y está a
escala.** El ancho del chasis `b2` (1,054) y `Wa` (1,801) dan la misma escala con 0.1 %
(24.13 mm/pt). `culo_de_la_ficha.py` saca las curvas del contorno del culo tal cual las dibujó
Jungheinrich y escribe `culo_ficha.csv`.

| | Del vector |
|---|---|
| Forma del culo | **la cara es un arco de R = 1.747 m** (centro 5 cm detrás del eje de carga), con dos esquinas de transición hasta los lados |
| Retiro del contorno respecto del punto del eje | 12 mm a ±0.20 · 26 a ±0.30 · 46 a ±0.40 · 65 a ±0.45 · 113 a ±0.50 · 166 a ±0.52 |
| Distancia máxima del culo al eje de carga | **1.801 = `Wa`, sobre el eje**: el culo está diseñado para quedar dentro del círculo de `Wa` |
| Culo → eje de la rueda motriz | **240** (cota del dibujo de costado) |
| Culo → eje de carga, de serie | **240 + `y` 1,562 = 1,802**, y `l2` + `x` = 1,582 + 219 = **1,801**: dos caminos, mismo número |

**Ancho a rumbo** con la silueta v3 (2.91 de culo a punta, capó 1.065), cambiando solo el culo
(`python herramientas/fichas/culo_de_la_ficha.py --ancho`):

| Culo | Vacío | Con el IBC |
|---|---|---|
| ángulo recto | 3.045 | 3.088 |
| esquinas de 0.17 (ajuste del píxel, 06-nov) | 3.005 | 3.042 |
| **el de la ficha, del vector** | **2.967** | **3.005** |

**Vacío gira dentro de los 3.00 sin usar el retranqueo (sobran 1.6 cm por lado). Cargado pide
3 mm por lado** de los 6 cm que hay entre postes.

### Decía / es / qué lo tumbó

| Decía | Es | Qué lo tumbó |
|---|---|---|
| 06-nov, primero: el culo es un arco de radio `Wa` | **casi**: la cara es un arco de 1.747 centrado 5 cm detrás del eje de carga, y todo el culo cabe en el círculo de `Wa` | los vectores |
| 06-nov, después: rectángulo con esquinas de 0.17 (ajuste de círculo a 8 puntos de la imagen) | **un arco en todo el ancho**, no esquinas: a ±0.40 ya retrocede 46 mm, y en la esquina 166 | el ajuste de 8 puntos no podía ver la curva de la cara; el vector sí |
| vacío 3.005, cargado 3.043 | **vacío 2.967, cargado 3.005** | la forma del culo |

### Lo que queda en tensión

- **Es el dibujo del modelo de serie.** Si el equipo tiene el compartimento de batería largo (los
  13 cm), la batería está entre la rueda motriz y la torre: el culo (la forma de atrás) no cambia,
  pero `y` sí (1,562 + 126 = 1,688) y con ella `XPIV` (240 + 1,688 = **1,928**, el mismo 1.93 que
  sale del largo). Confirmar midiendo **culo → eje de la rueda motriz (240)** y **entre ejes**.
- **El dibujo es de catálogo**, no un plano de fabricación. Pero está a escala con 0.1 %, y lo que
  dice coincide con `Wa`. Una foto desde arriba del culo con una cinta lo confirma.

## Escaneo completo de las dos fichas (09-nov)

`escaneo_fichas.py` mide las cotas en los **dibujos vectoriales** y las cruza con las tablas. Las dos
fichas son vectoriales: la hoja Jungheinrich (pág. 2) y también el brochure Mitsubishi (pág. 7, la
vista del ESR15N2–EDR18N2).

### 1 · El culo lo confirman los dos dibujos

El contorno del culo de Mitsubishi, escalado al mismo ancho, **calza con el de Jungheinrich con 0–4 mm
de diferencia** hasta ±0.50 m del eje (3/3 · 12/12 · 26/26 · 46/48 · 65/68 · 113/117 mm). El culo es
de serie (maje, 09-nov: no es custom), así que **el contorno de `culo_ficha.csv` es el del equipo**.

La vista de arriba de Mitsubishi **no** sirve para largos: es un dibujo genérico de la familia y sus
cotas `l2`/`l7` no salen a la misma escala que su `b2` (±4 %). Solo se usa su forma.

### 2 · La vista de costado de Jungheinrich, cota por cota (escala por `y`)

| Cota | Dibujo | Tabla |
|---|---|---|
| culo → eje de la rueda motriz | 241 | 240 |
| `l2` culo → dorso de uñas | 1,587 | 1,582 |
| `x` dorso de uñas → eje de carga | 215 | 219 |
| `l7` culo → punta de las patas | 1,985 | 1,983 |
| **`l1` culo → punta de uñas** | **2,658** | **2,999** |

**El `l1` = 2,999 de la tabla está mal** para ETR 235/340/345/335d: es un copiar-pegar. El dibujo da
2,658 = `l2` + uñas de 1,067 (2,649), y el ETR 230 sí cumple esa suma en la tabla (1,315 + 1,067 =
2,382). **De serie, culo → punta = 2.65 m.**

### 3 · Los 13 cm son el compartimento de batería, y eso mueve el entre ejes

Las dos fichas muestran que **el compartimento de batería se suma tal cual al entre ejes**:

| Modelo | Compartimento (MCFA 51) | Entre ejes `y` | `Wa` |
|---|---|---|---|
| ESR15N2 / ETR 230 | 362 | 1,511 | 1,746 / 1,750 |
| ESR18N2 · EDR18N2 / ETR 235–335d | 413 | 1,562 | 1,797 / 1,801 |
| diferencia | **+51** | **+51** | **+51** |

La ficha MCFA da compartimentos de 413, 463 y **539** («estándar con elevación > 8,430», nota 7). Con
el culo de serie y uñas de 1.20, el 2.91 medido pide **+128 mm**: el de 539 da **+126**. Si es ese:

| | De serie (413) | Con 539 (lo que pide el 2.91) |
|---|---|---|
| `l2` culo → dorso de uñas | 1,582 | **1,708** |
| culo → punta (uñas de 1.20) | 2,782 | **2,908** ✓ medido 2,91 |
| entre ejes `y` | 1,562 | **1,688** |
| culo → eje de carga (240 + `y`) | 1,802 | **1,928** (= el `XPIV` 1.93 derivado por otro camino) |

La placa (batería de 1,050–1,180 kg, más que el máximo de 1,050 de la ficha para 413) apunta a lo mismo.
**No cambia el giro** (el ancho a rumbo es forma: 2.967 / 3.005); cambia `WB` en la cinemática y los
tiempos (v3b: ≤ 1 s). **Se confirma midiendo el entre ejes**: 1.56 o 1.69.

### 4 · Lo que corrige de `CLAUDE.md`

La «cota dura» de septiembre, `XPIV < √(Wa² − (W/2)²) = 1.672`, **suponía esquinas en ángulo recto**.
Con el culo de la ficha (todo dentro del círculo de `Wa`), la distancia máxima al eje de carga es la
del punto del eje: **`XPIV` = `Wa`**. La cota no existe, y la estación 282 (`XPIV` 1.862) deja de ser
una contradicción: queda entre 1.80 (de serie) y 1.93 (batería larga).

### 5 · Otros datos de las fichas, para no volver a buscarlos

| | Valor | Fuente |
|---|---|---|
| Rueda motriz | **343 × 140** (perímetro 1.078 m: la escala de la odometría) | VDI 3.2 · MCFA 41 |
| Rueda estabilizadora (caster) | 180 × 100 | VDI 3.4 · MCFA 42 |
| Ruedas de carga | 127 × 92; trocha **966** (335d) | VDI 3.3, 3.7 |
| Patas | 127 de ancho (5"), 127 de alto (`h8`); entre patas 1,067 de serie → **`b1` 1,321** (el repo usa 1.315, sin medir) | VDI 4.10, 4.21 · MCFA 14 |
| Batería (de serie) | 968 × 404 × 782, 36 V 775 Ah, 907 kg | VDI 6.4–6.5 |
| Compartimento | 413 × 976 × 804 (opciones 463 / 539) | MCFA 51–53 |
| Velocidad de empuje (pantógrafo) | **0.28 / 0.30 m/s** con / sin carga → 1.067 m en ~3.6–3.8 s | VDI 5.4 |
| Elevación / descenso | 0.55 / 0.84 · 0.53 / 0.57 m/s | VDI 5.2–5.3 |
| Marcha | 12.1 / 12.9 km/h (catálogo; en campo 7.9) | VDI 5.1 |
| Tejadillo | alto 2,413; ancho 1,043 | VDI 4.7 · MCFA |
| Chasis | alto 1,270; escalón 250; despeje 51–61 | MCFA · VDI 4.8, 4.32 |
| Carro portahorquillas | 826 de ancho; uñas abiertas 305–802 | VDI 4.24–4.25 |
| Dirección | eléctrica | VDI 8.6 |
