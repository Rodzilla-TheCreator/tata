# Estado y siguientes pasos

## Hecho

- Almacén de RETHINK reconstruido y medido desde el DWG
- Simulador web funcionando y desplegado, con dos vistas
- Escena USD del sector C lista para Isaac Sim
- Cinemática de tracción trasera validada contra ficha VDI 2198
- Modo Obed con timón por velocidad, pantógrafo y desplazador
- BOM del EDR con escala de madurez y NRE separada
- Los dos decks: RETHINK y caso de negocio para Omar
- Análisis: degeneración, firma de ocupación, geometría de giro, campo de protección, retorno

## Pendiente, en orden

### 1 · Validación en taller — sin costo
Probar el bus del EDR con un equipo del piso. Es la puerta que va **antes** de comprar nada.
Si el controlador expone comunicación abierta, se caen los encoders propios y buena parte de la
ingeniería inversa.

### 2 · Articulación en Isaac Sim
Dirección trasera, mástil prismático con las cinco alturas, uñas y pantógrafo. La cinemática ya
está validada en el visor web — es portarla, no inventarla.

### 3 · Deriva ida y vuelta con el OS0-128
Esperado: **2–8 cm de error de cierre** sobre 25 m. Más de 15 cm y los marcadores dejan de ser
opcionales.

### 4 · Cuántos marcadores
Sembrar AprilTags y bajar la cantidad hasta que la deriva entre uno y otro se salga de los
**±4.5 cm** que deja la bahía. Sale un número, no una opinión.

### 5 · Confusión entre pasillos
Mismo recorrido en dos pasillos distintos, mezclar nubes, ver si los distingue. **Correrlo con y
sin la firma de ocupación** — es la prueba de si el enlace al WMS resuelve el problema sin
hardware extra.

### 6 · Bahías vacías al 30%
Donde desaparece el relieve del rack y se acerca al caso singular.

### 7 · Prototipo físico
Después de la puerta 1 y con presupuesto aprobado.

## Puertas de decisión

| Puerta | Cuándo | Criterio |
|---|---|---|
| 1 | Antes de comprar | ¿El Baoli/EDR expone bus abierto? Si no, se recotiza. |
| 2 | Mes 3 | El kit lee una ubicación de rack a 6 m y registra un ciclo completo solo. Si no, se para. |
| 3 | Mes 11 | Con datos del cliente se decide si se sube de nivel. |

## Riesgos vivos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| El controlador no expone bus abierto | Media | Alto | Validar en taller antes de comprar |
| Bus del Mid-360 caro de simular | Alta | Bajo | Empezar con OS0-128 |
| Marcadores se despegan o se tapan | Media | Medio | LiDAR como respaldo, degradación elegante |
| WMS desactualizado rompe la firma de ocupación | Media | Alto | Umbral de 78%, y el desajuste es dato de inventario |
| Sobre-prometer plazos en la primera instalación | Alta | Medio | Cotizar al triple del tiempo estimado |
| Dependencia de una sola persona | Alta | Alto | Documentar desde el día uno |

## Notas de trabajo

- Responder en **español**, tono directo y conciso.
- **Máximo 400 palabras** de prosa por respuesta salvo que se pida más. Tablas, código y listas de
  archivos no cuentan.
- No adular ni rellenar. Si algo está mal, decirlo de frente.
- Cuando un cálculo contradiga una afirmación previa, **corregirla explícitamente**. Ya pasó dos
  veces en este proyecto y las dos veces mejoró el resultado.
