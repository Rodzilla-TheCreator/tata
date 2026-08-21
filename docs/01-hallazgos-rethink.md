# Hallazgos en el almacén RETHINK

Todo lo de aquí salió de `RETHINK_2026.dwg`, reconstruido y medido. Los cálculos están en
`analisis/`, la geometría cruda en `datos/`.

## El plano no es un piso: son tres propuestas

| Sector | Qué es | Ubicaciones |
|---|---|---|
| A · Actual | LAYOUT RETHINK, 1er nivel (nov-2024) | 930 |
| B · Ampliación | Naves L4-A/B/C, 1,736.64 m² proyectados | 1,208 |
| C · Propuesta IT | Bodega sin racks diseñados | — |

## La unidad de carga es un maxicubo, no una tarima

**1.00 × 1.20 m.** El plano lo dice: "RACK MAXICUBOS A 4 Y 5 NIVELES". Hay circuito de retorno
de vacíos — lavado, sucios, limpios. Cualquier robot tiene que manejar el retorno, no sólo el
producto.

## Los pasillos no dan para un contrabalanceado

Medidos sobre la geometría real, vecino más cercano, cara de carga a cara de carga:

| | |
|---|---|
| Mediana | 3.17 m |
| 25 de 29 pasillos | 3.07 – 3.35 m |
| 4 pasillos | 4.40 – 4.48 m (circulación, no almacenaje) |
| Medido en sitio | **3.00 m** |

Un Baoli KBE 20 necesita **3.82 m** de pasillo de estiba (Ast, VDI 2198). Un KBE 18 pide 3.55 m.
Ninguno entra.

**Conclusión:** el layout está diseñado para reach truck. 3.0–3.2 m es exactamente su pasillo.
Por eso la máquina objetivo pasó a ser el EDR18N2.

## El plano está en metros

Verificado por tres vías, porque la duda era razonable:

1. `$INSUNITS = 6` en la cabecera del DXF — el código de "metros", escrito por el CAD del proyectista.
2. Un recinto rotulado **"82.00 M2"** mide **81.32 unidades²**. Error de 0.8%, que es lo que se
   explica por dibujar la polilínea sobre el eje del muro en vez de la cara.
3. Las cotas se agrupan en redondos métricos: 0.15, 0.90, 1.20, 1.50, 2.00, 3.00, 3.50, 4.00.
   El 1.20 es exactamente el ancho del maxicubo.

El archivo trae además `$MEASUREMENT = 0`, que dice "imperial" — pero esa bandera sólo elige la
tabla de rayados y tipos de línea, no toca la geometría. Desajuste común en plantillas heredadas.
Si alguien lo saca como argumento, ahí está la respuesta.

## Racks a los que no se puede llegar

Encontrados manejando el simulador, no mirando el plano.

- **Muro divisorio en x≈868** parte la bodega del sector C en dos naves. La nave oeste queda
  encerrada: el único paso está detrás de las filas de rack.
- **Pasillos sin salida.** Filas de pared a pared sin transversal: no hay forma de pasar de un
  pasillo al de al lado. El operador tendría que salir 25 m en reversa.

## Nuestra propuesta para el sector C

Generada paramétricamente respetando muros reales.

| Nave | Dimensiones | Filas × bahías | Pasillo |
|---|---|---|---|
| Este | 27.5 × 26.3 m | 6 × 17 | 5.54 m |
| Oeste | 23.3 × 20.0 m | 4 × 14 | 6.34 m |

**790 ubicaciones**, transversal de 4.50 m, 5 niveles a 0.70 / 2.15 / 3.60 / 5.05 / 6.50 m.

## Lo que se observó en el taller

Los operadores **chocan a voluntad**. Los racks están anclados y llevan cubiertas de protección
en los tubos justamente para aceptar golpes. No hay un solo montacargas del taller con las
esquinas del chasis intactas.

Eso no es un problema del kit: es una línea base. Hoy nadie sabe cuántos golpes hay al mes.
El nivel 1 los cuenta desde el primer día, y ese número solo puede justificar la compra.
