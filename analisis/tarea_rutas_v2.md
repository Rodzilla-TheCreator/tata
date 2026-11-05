# Encargo — rutas v2: postes, retranqueo de 6 cm y carril central; validar contra el video del operador

> **HECHO 05-nov-2026 en la i3.** Sección «v2» de `rutas_resultados.md`.
> - **Con XPIV 1.50 (δmax 78°) el giro sin reversa NO existe:** la cuenta (3.12 m entre postes)
>   no alcanza, porque falta la cinemática.
> - **Aparece con XPIV ≥ 1.58 (δmax ≥ ~83°).** Se trabaja con 1.60, como SUPUESTO tomado del video.
> - **Ahí sale para `a`, `b` y centro, en los dos sentidos:** margen de 2 cm vacío y 1 cm cargado,
>   retranqueo mínimo de 4–5 cm. El control con retranqueo 0 da 0/12.
> - **El giro arranca a 5 cm del eje:** la regla del carril central sale sola. El caso de maje
>   y las 28 del barrido salen como el video.
> - **Visibilidad con las rutas v2:** A2 cada 2 bahías, B cada 1 (cada 2 con marcas alternadas).
> - **La FSM sigue con la tabla v1** (anotado como pendiente).

**Para la sesión de i3.** Sigue a `tarea_rutas_bahias.md` y a `percepcion/tarea_visibilidad.md`,
los dos hechos el 05-nov. Leé `CLAUDE.md`, `analisis/rutas_resultados.md` (sobre todo las
secciones «Dato de campo» y «Afinado» del final) y la sección de visibilidad de
`percepcion/LEEME.md`.

## Lo nuevo que hay que meter al modelo (datos de campo de maje, 05-nov)

1. **Los 3.00 m son de poste de seguridad a poste de seguridad**, el punto más angosto. Hay un
   poste en cada borde de bahía (cada 2.35 m de luz; `visibilidad.py` usó 2.47 entre postes:
   reconciliá y anotá).
2. **Entre postes, la cara del cubo queda ~6 cm más atrás, en los dos racks.** En N1 al piso
   depende de dónde lo dejó el operador (error humano); N1-B queda alineado con el de abajo;
   de N2 para arriba, al fondo. Las uñas giran a pocos cm del piso, así que lo que manda es la
   cara del cubo de N1. `PROF_BAHIA = 0.06` **en los dos lados**, sin uñas en los huecos del IBC.
   Tamaño y altura del poste: `SUPUESTO`, configurables (maje los mide).
3. **El video:** el operador se posiciona retrocediendo y, **una vez que arranca el giro, no
   retrocede: solo mueve el timón, en continuo**. Queda pegado a las dos bahías. Entra al hueco
   que se iba a alinear, con las uñas hacia la carga.
4. **Tránsito por el carril central, carril de giro solo para alinearse** (idea de maje). Hoy el
   planificador transita por el carril de giro (punto 5 de la visibilidad): hay que forzarlo, o
   costearlo, y reportar las dos variantes.

La cuenta a mano: entre postes caben 3.12 m; el ancho a rumbo máximo es 3.036 vacío y 3.078
cargado. **Solo cabe si las dos puntas (uñas y culo) quedan entre postes en los rumbos de
56–89.5°.** Comprobalo con el planificador, no con la cuenta.

## Qué hacer

- `planificador_rutas.py`: postes como obstáculos, retranqueo de 6 cm en los dos lados, timón
  más fino o continuo (los 7 ángulos fijos fabrican cambios de sentido), y la regla del carril
  central para el tránsito.
- **Validación contra el video:** el giro a un hueco desde el carril de giro tiene que salir
  **sin cambios de sentido después de arrancar**, como lo hace el operador. Reportá para qué
  huecos (`a`/`b`) y sentidos de viaje sale y para cuáles no, y **cuánto margen queda**, vacío y
  cargado.
- **Sensibilidad:** retranqueo de 3, 6 y 9 cm (el error humano en N1), y `XPIV` 1.30–1.60. ¿Con
  cuánto retranqueo deja de existir el giro sin reversa?
- **Control de falsación:** con retranqueo 0 en los dos lados, el giro tiene que desaparecer
  (como el 05-nov). Si sigue saliendo, los postes o el retranqueo no están restringiendo.
- Con los recorridos nuevos, **volvé a correr `percepcion/visibilidad.py`** para A2 y B (los dos
  mejores) y decí si cambia el espaciado máximo.

## Entregables

- `planificador_rutas.py` y `bahias.py` actualizados, `rutas_resultados.md` con una sección nueva
  (tabla decía / es / qué lo tumbó contra la del 05-nov), y la sección de visibilidad de
  `percepcion/LEEME.md` actualizada si cambia algo.
- Una línea en `CLAUDE.md` si cambia una conclusión.
- Commit y push a `main`.

## Lo que NO es esta tarea

- No es medir: retranqueo, postes, `PX_MIN` y `ANG_MAX` los mide maje; mientras tanto son `SUPUESTO`.
- No es tocar `sim-web/` ni el fierro.
