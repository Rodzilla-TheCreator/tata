# LiDAR, marcadores y localización

## El punto de partida equivocado

La hipótesis inicial fue que un pasillo largo y uniforme degeneraría el emparejado de escaneos:
el SLAM se desliza a lo largo del eje del pasillo porque no hay geometría que lo restrinja.

**El cálculo lo desmintió.** Está en `analisis/analisis_degeneracion.py`.

| Caso | σ a lo largo | σ a lo ancho | Relación |
|---|---|---|---|
| Rack típico, relieve 8 cm | 0.20 cm | 0.07 cm | 2.7× |
| Rack casi liso, relieve 2 cm | 0.41 cm | 0.07 cm | 5.9× |
| Paredes perfectamente lisas | **singular** | 0.07 cm | ∞ |

**Lo que salva al SLAM son los montantes del rack**: cada 1.20 m hay una cara perpendicular al
pasillo. Con 17 bahías por lado hay restricción longitudinal de sobra. El eje del pasillo queda
**mal condicionado (2.7×), no indeterminado**.

La singularidad sólo aparece con paredes realmente lisas: bahía vacía sin carga que dé relieve,
carga emplayada tapando montantes, o LiDAR montado tan alto que sólo ve por encima de la estructura.

## El riesgo real es otro

**Los 10 pasillos son geométricamente idénticos entre sí.** Eso es reconocimiento de lugar, no
degeneración geométrica, y es el problema mayor.

## La salida: la ocupación como firma

Cálculo en `analisis/firma_ocupacion.py`.

Los pasillos son idénticos, pero el **patrón de bahías llenas y vacías no lo es** — y el WMS ya
sabe cuál es. No hay que aprenderlo, hay que consultarlo.

Con ocupación del 82.2%, cada bahía carga **0.68 bits**. Distinguir 10 pasillos pide 3.32 bits.
Un pasillo de un nivel, ambos lados, son 34 bahías = **23 bits**. Sobra por factor siete.

| Bahías vistas | WMS al día | 10% viejo | 20% viejo |
|---|---|---|---|
| 8 | 56% | 39% | 26% |
| 17 | 90% | 72% | 49% |
| 34 | **99.6%** | 94% | 76% |

### El discriminador

| Situación | Coincidencia esperada |
|---|---|
| Pasillo equivocado | 70.7% (azar entre dos patrones al 82%) |
| Correcto, WMS 5% viejo | 90.5% |
| Correcto, WMS 10% viejo | 86.0% |

Con 34 bahías la desviación es ~7.8%: **el umbral cae cerca del 78%**. Por debajo estás en otro
pasillo; por encima estás bien y lo que falla es el inventario.

**El mismo dato que localiza audita el inventario.** Una bahía que no coincide es error de
inventario; el patrón entero que no coincide es error de localización.

## El rol que le queda al LiDAR

En un ambiente controlado donde se pueden poner los marcadores que uno quiera, **el LiDAR deja de
ser el que sabe dónde estás**. Eso lo resuelve un AprilTag en papel laminado en la cabecera de
cada fila: posición absoluta, sin deriva, sin ambigüedad entre pasillos, por centavos.

Al LiDAR le quedan dos trabajos, y los dos son más chicos:

1. **Ver lo que no debería estar ahí** — una persona, un cubo caído, un patín cruzado, un montante
   golpeado que ya no está donde el mapa dice. Ningún marcador hace eso.
2. **Sostener la operación cuando el marcador falla** — se despega, lo tapa un maxicubo, lo raya
   un golpe. Degradación elegante, no redundancia de lujo.

**Eso cambia el requisito de compra.** Para localizar hace falta precisión y densidad. Para
detectar un bulto en un pasillo de 3 m a 8 km/h alcanza con 10 m de rango y decenas de haces.
El Livox Mid-360 de $749 sobra, y probablemente sobre bastante.

**El orden se invierte:** marcadores primero, LiDAR de apoyo. Más barato, más robusto y más fácil
de explicar.

## Lo que hay que probar en Isaac

Cuántos marcadores y a qué separación, antes de que la deriva entre uno y otro se salga de los
**±4.5 cm** que deja la bahía.
