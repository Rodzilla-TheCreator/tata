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
- **`XPIV = l2 + x = 1,801 = Wa`.** El eje de carga queda a 1.80 m del culo, no a 1.50. Que coincida
  con `Wa` dice que el culo es un arco alrededor del eje de carga: lo más lejano está atrás, en el eje.
- **El largo culo → punta estándar es 1,582 + 1,067 = 2,649**; con uñas de 1.20, 2,782. **Los 2.91
  medidos cuadran con el compartimento de batería largo (+126) y uñas de 1.20: 1,708 + 1,200 = 2,908.**
  La placa (batería de 1,050–1,180 kg, más que los 907–1,050 de la ficha) apunta a lo mismo. Si es así,
  `XPIV` y `Wa` de **este** equipo son ~13 cm más que los de la ficha. Se confirma midiendo el
  compartimento o pidiendo la configuración por la serie `82824121`.
