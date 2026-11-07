# Encargo — rutas v3b: el culo exacto de la ficha (vectores)

> **HECHO 07-nov-2026 en la i3.** Sección «v3b» de `rutas_resultados.md`; `rutas_v3b.json` y `ruta_3L_5R_v3b.png`.
> Confirma la cuenta: vacío gira con retranqueo 0, cargado con 1 cm; margen nominal 7 / 5 cm. El cambio de carril sale con ~20 000 expansiones.

**Para la sesión de i3.** Sigue a `tarea_rutas_v3.md` (hecho 06-nov). Leé la última sección de
`herramientas/fichas/LEEME.md` («El culo, de los VECTORES de la hoja») y corré:

```
py -m pip install pymupdf
py herramientas/fichas/culo_de_la_ficha.py --ancho
```

Tiene que dar **2.967 vacío / 3.005 cargado**. Si no da eso, pará y anotá por qué.

## Qué cambia

El culo de v3 era un rectángulo con esquinas de 0.17 (ajuste a 8 píxeles de una imagen). La hoja es
vectorial y a escala: **la cara del culo es un arco de R 1.747** con esquinas de transición, y todo
el culo cabe dentro del círculo de `Wa` (1.801). El contorno está en `herramientas/fichas/culo_ficha.csv`
(`a` desde el culo, `y`; semiancho del dibujo 0.522 → escalarlo en `y` al capó medido de 1.065).

## Qué hacer

1. En `planificador_rutas.py`: que `r_culo` acepte **`'ficha'`** y use el contorno del `.csv`
   (escalado al capó). Que sea el default de v3. **v1, v2 y v3 con `r_culo=0.17` tienen que seguir
   dando lo mismo** (comprobalo con los números de `rutas_resultados.md`).
2. `anchos_v3()` con la fila `ficha`: **2.967 / 3.005**.
3. **Sensibilidad con el culo de la ficha:** retranqueo 0 / 1 / 2 / 3 / 6 cm, vacío y cargado, en
   las combinaciones de `COMBOS3`. Predicción de la cuenta: vacío sale con 0; cargado no sale con 0
   (3.005 > 3.00) y sí con 1 cm o más. Decí si el planificador lo confirma, y el margen nominal (6 cm).
4. **Control de falsación:** culo en ángulo recto y retranqueo 0, cargado y vacío: **0/6**, como en v3.
5. **Caso de maje** (`3L → 5R → descarga`) y **barrido de las 28** con el culo de la ficha. Figura
   `ruta_3L_5R_v3b.png`, datos en `rutas_v3b.json`.
6. **El cambio de carril** que en v3 no salía con 15 000 expansiones: probalo de nuevo. Si sigue sin
   salir, decí si hace falta (con el giro casi en el lugar, ¿se usa?).
7. `clases/giro.html`: un tercer modo del deslizador del culo, «ficha (vectores)», con el contorno
   del `.csv` embebido, y en la sección 3 que vacío ya entra en 3.00.

## Entregables

- `planificador_rutas.py`, sección «v3b» en `rutas_resultados.md` (decía / es / qué lo tumbó contra
  v3), `rutas_v3b.json`, la figura, la clase.
- Una línea en `CLAUDE.md` si cambia una conclusión.
- Commit y push a `main`.

## Lo que NO es esta tarea

- No es medir. Lo que sigue en tensión: si el equipo tiene la batería larga, `y` (entre ejes) pasa
  de 1.562 a ~1.688. No cambia el ancho a rumbo (es forma), pero sí `WB` en la cinemática y los
  tiempos: **dejá `WB` como parámetro y reportá con 1.562 y 1.688** solo los tiempos del caso de maje.
- No es tocar `sim-web/` ni el fierro.
