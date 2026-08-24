# TaTa · briefing para Claude Code — Montasa, mañana temprano

Leé esto completo antes de escribir nada. No inventes medidas: las que faltan las trae
maje hoy y se meten como constantes con nombre, nunca hardcodeadas a mitad de una función.

---

## 1. Qué es esto

TaTa es un kit de retrofit que vuelve autónomo un montacargas que ya existe. Máquina
objetivo: **Mitsubishi EDR18N2**, reach truck de operador parado. Proyecto interno de
Montasa (distribuidor de montacargas, San Pedro Sula). El cliente piloto es RETHINK.

Lo que está corriendo ahora es **la simulación de secuencia**: dos TaTa de línea, uno por
pasillo, moviendo maxicubos entre racks. No es un juego de manejo — es la maqueta ejecutable
de la lógica que después va al fierro.

### Disposición del almacén simulado

```
          rojo      │ PASILLO A │  amarillo ‖ verde  │ PASILLO B │      azul
   z = -2.05        │  z = 0    │  2.05 ‖ 3.15       │  z = 5.20 │   z = 7.25
```

- Amarillo y verde van **pegados de culo**; el plano donde se tocan es `z = 2.60`.
- Pasillos de **3.00 m** de luz. Racks de 1.10 m de fondo, 12 columnas × 5 niveles.
- El pasillo **abre a la izquierda** (principio) y **muere contra la pared a la derecha** (final).
- El montacargas **humano** no entra al pasillo. Deja los cubos que entran **al final del rack
  rojo** y recoge lo que sale **al principio del pasillo**.
- Por eso todo lo que va a verde/azul lo tiene que pasar TaTa A a un **trasbordo** en el fondo,
  sobre el plano `z = 2.60`, donde llegan los dos equipos sin salirse de su pasillo.
- Esto hace de A un cuello de botella. Es a propósito: hay que medirlo, no esconderlo.

---

## 2. Archivos

| archivo | qué es |
|---|---|
| `sec_tpl.html` | **la fuente**. Plantilla con el marcador `__THREE__`. Todo el código vive acá. |
| `build_sec.py` | inyecta `node_modules/three/build/three.min.js` y escribe `TaTa_Secuencia.html` |
| `TaTa_Secuencia.html` | el build, ~650 KB. **Nunca lo edites a mano.** |
| `giro.py` | replica el planificador de giro en Python y saca los números |
| `gen_svg.py` | dibuja la geometría del giro a SVG desde `giro.json` |
| `gen_fsm.py` | dibuja la máquina de estados a SVG |

Flujo: editar `sec_tpl.html` → `python3 build_sec.py` → abrir el HTML.
`#turbo` en la URL corre a ×8. La tecla `F` alterna ×1 / ×4.

QA headless (hay Playwright y Chromium instalados):
```js
chromium.launch({ args:['--use-gl=swiftshader','--enable-unsafe-swiftshader'] })
```
Siempre revisar `pageerror` antes de dar algo por bueno.

---

## 3. Constantes que van a cambiar hoy con las medidas de maje

Todas están juntas arriba de `sec_tpl.html`, en el bloque `/* geometría */` y en `const T`.
Cuando maje dé un número, cambiá **la constante** y volvé a construir. Si un número no
está en esta lista, preguntá antes de inventarlo.

| constante | valor hoy | qué es | qué se rompe si cambia |
|---|---|---|---|
| `AISLE` | 3.00 | luz del pasillo | el planificador de giro entero |
| `RACKD` | 1.10 | fondo del rack | `zin`, profundidad de estiba |
| `BAY` | 1.30 | luz entre parales | espaciado de columnas, margen lateral |
| `NCOL` / `NLVL` | 12 / 5 | columnas y niveles | tamaño del almacén y del widget |
| `LVL[]` | 0.15 … 5.95 | altura de viga por nivel | tiempos de elevación |
| `CUBE` | 1.20 × 1.00 × 1.20 | maxicubo | `zin`, holgura lateral en bahía |
| `WALL_GAP` | **4.20** | fondo libre entre fin de rack y pared | **cuántas posiciones de entrada y trasbordo caben** |
| `ZHAND` | 2.60 | plano amarillo‖verde | dónde va el trasbordo |
| `T.LTOT` | 2.91 | culo → punta de uñas | todo |
| `T.LCH` | 1.70 | culo → cara del mástil | envolvente del chasis |
| `T.W` | 1.054 | ancho | holgura del giro |
| `T.WB` | 1.562 | distancia entre ejes | radio de giro |
| `T.XPIV` | **1.91** | eje de ruedas de carga desde el culo | radio de giro, `zin` |
| `T.FLEN` | 1.21 | largo de uña | alcance |
| `T.REACH` | 0.61 | carrera del pantógrafo | `zin` |
| `T.SSHIFT` | 0.12 | sideshift | tolerancia lateral |
| `T.VMAX` / `T.VMAN` | 1.50 / 0.35 | velocidad de tránsito / maniobra | tiempo de ciclo |

**`WALL_GAP` es el supuesto más caro que hay.** De ahí sale `HANDX`, y de `HANDX` salen las
posiciones de entrada y de trasbordo. Con menos fondo, A se bloquea seguido; con más, deja
de ser problema. Es lo primero que hay que corregir cuando llegue la medida.

---

## 4. La matemática del giro — lo que hay que estudiar

### Lo que ya está resuelto

Dirección por **rueda trasera**, punto de referencia en el eje de ruedas de carga:

```
dθ = −(ds / WB) · tan δ
```

`planTurn(side)` hace una **búsqueda numérica bruta**: barre carril ∈ [0, 0.95] cada 2.5 cm
× ángulo de dirección δ ∈ [46°, 88°] cada 1°, integra el giro completo de 90° con paso de
1.5 cm, y evalúa la envolvente de las cuatro esquinas del chasis y de las dos puntas de uña.
Restricción dura: el **chasis** no puede salirse de ±1.50; las **uñas** sí pueden entrar al
hueco de la bahía objetivo.

Resultado con los números de hoy:

| | |
|---|---|
| carril | 0.575 m |
| dirección | 73° (no es el tope) |
| radio del pivote | 0.478 m |
| barrido del chasis | 2.20 m |
| holgura | 39 cm / 40 cm |
| uñas dentro de la bahía | 0.58 m |
| saliente en X delante del pivote | 0.79 m |

### Lo que falta — esto es el trabajo de mañana

1. **Forma cerrada.** Hoy es fuerza bruta. Dado `AISLE`, `LTOT`, `LCH`, `W`, `WB`, `XPIV`,
   ¿existe expresión analítica para el carril y el δ óptimos? ¿Y una condición de
   existencia — cuándo simplemente *no* cabe? Eso convierte "probamos y salió" en
   "sabemos por qué sale", que es lo que se le enseña a un cliente.
2. **La carga no está en la envolvente.** El planificador gira el equipo **vacío**. Con un
   maxicubo de 1.20 × 1.20 en las uñas, la envolvente cambia y probablemente la holgura se
   come. **Esto es un hueco real y es lo más urgente de los siete.**
3. **Contraste con VDI 2198.** El `Ast` de catálogo del EDR debería coincidir con este
   barrido. Si no coincide, hay que entender por qué antes de creerle a ninguno de los dos.
4. **Sensibilidad.** ∂holgura/∂carril y ∂holgura/∂δ. Traduce a: cuánto error de posición
   tolera la traza antes de rayar un rack. Ese número es el requisito de navegación.
5. **Maniobra multipunto.** Si con carga no cabe de una pasada, hace falta el giro en dos o
   tres tiempos (arco adelante, arco atrás). El código no lo tiene.
6. **Tiempo del giro.** Hoy son 3.4 s fijos, inventados. Deben salir del largo de arco
   dividido por `T.VMAN`.
7. **Sentido de entrada.** El equipo siempre entra al pasillo con las uñas hacia +X y
   regresa en reversa. Confirmar que eso es lo que hace un reach de verdad y que no hay
   una maniobra mejor.

---

## 5. La máquina de estados — hay que definirla bien

### Lo que hay hoy

**Capa 1 — selector de tarea.** Corre cada vez que el equipo queda libre. Orden fijo, gana
el primero que se cumple:

| prioridad | tarea | condición |
|---|---|---|
| 1 | `TRASBORDO` | hay un cubo mío esperando en el fondo |
| 2 | `PEDIDO` | me pidieron un color que tengo en rack |
| 3 | `ENTRADA` | el humano dejó un cubo (sólo lo ve A) |
| 4 | `PASE` | lo que cargo no es mío → al trasbordo |
| 5 | `REUBICAR` | cubo mal ubicado en uno de mis racks |
| — | `LIBRE` | ninguna se cumple |

**Capa 2 — secuencia de movimiento.** Once pasos, siempre los mismos, ejecutados dos veces
por tarea (una en el origen para tomar, otra en el destino para dejar):

```
CARRIL → RECTA → GIRO 90° → ELEVA → APROXIMA → EXTIENDE
       → SUBE/BAJA → RETRAE → RETROCEDE → DESGIRA → TRÁNSITO
```

Profundidad de estacionamiento: `zin = |Δz| + 0.60 − 1.00 − 0.61`
→ **1.04 m** para un rack, **1.59 m** para el trasbordo del fondo.
El cubo nunca se arrastra: entra alto, baja sobre la viga, sale.

### Lo que falta definir

1. **Estados de espera y bloqueo explícitos.** Hoy `blocked` es un string suelto. Deben ser
   estados de verdad, con condición de entrada y de salida: `ESPERA_TRASBORDO`,
   `ESPERA_HUECO`, `ESPERA_PEDIDO`.
2. **Reservas y deadlock.** Si A y B reservan la última posición de trasbordo al mismo
   tiempo, hoy no hay nada que lo impida. Hace falta un protocolo de reserva y una prueba
   que intente romperlo.
3. **Estados de falla.** Qué pasa si el ArUco no se ve, si el hueco estaba ocupado, si la
   cámara de uñas no confirma carga, si entra un e-stop a mitad de una extensión. Hoy no
   existen y en el fierro son la mitad del código.
4. **Precondiciones y postcondiciones por tarea.** Contrato explícito de cada una, para poder
   escribir pruebas que verifiquen la secuencia en vez de mirarla correr.
5. **Reanudación.** Después de una pausa o un e-stop, ¿desde qué paso retoma? Hay pasos que
   no se pueden reanudar a la mitad (pantógrafo extendido en altura).
6. **Prioridad configurable.** El orden de arriba es una decisión, no una ley. Debería ser un
   parámetro para poder comparar políticas con el mismo lote.

Producto de mañana: **un diagrama de estados formal y una tabla de transiciones** que sirvan
de especificación para el código del fierro, no sólo para la simulación.

---

## 6. La presentación

Antes de escribir una lámina, definir con maje **a quién va**. Hay dos vivas:

- **RETHINK** — conversacional. Ya existe `TaTa_Presentacion_RETHINK.pptx`. Lo nuevo que
  aporta la simulación de secuencia: el trasbordo, el cuello de botella de A, y qué medidas
  del almacén hacen falta para dimensionarlo.
- **Omar** — caso de negocio formal. Ya existe `TaTa_Caso_Negocio_Omar.pptx` con las 5 gradas
  del kit y la comparación de costos. Lo nuevo: la secuencia como evidencia de que la lógica
  existe y corre.

En cualquiera de los dos casos: la figura del giro y el diagrama de estados salen de
`gen_svg.py` y `gen_fsm.py`, y se regeneran solos cuando cambian los números. No dibujar
nada a mano que un script pueda generar.

---

## 7. Orden de la mañana

1. Meter las medidas que trae maje. Constante por constante, reconstruir y verificar
   contra la vista de planta que el almacén sigue cerrando.
2. Meter la **carga** en la envolvente del giro. Volver a correr `planTurn` y ver si los
   39 cm sobreviven. Si no sobreviven, cambia el diseño, no el número.
3. Formalizar la máquina de estados: diagrama y tabla de transiciones.
4. Atacar la forma cerrada del giro con los números ya corregidos.
5. Presentación, con las figuras regeneradas.

---

## 8. Reglas de la casa

- **Ninguna medida inventada.** Si falta un número, se pregunta. Si igual hay que asumirlo,
  se marca como supuesto en el código y en el texto.
- **Nunca editar el HTML construido.** Sólo `sec_tpl.html`.
- **Nada de exagerar el riesgo.** Si algo cabe con 39 cm, cabe. No se dramatiza un margen
  normativo como si fuera cero.
- Respuestas cortas. maje no lee textos largos.
