**Proyecto TaTa — Tecnología Avanzada de Transporte Autónomo**

Cuestionario de levantamiento para el rundown del almacén ·
Automatización con montacargas autónomos

Sitio / Cliente:
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Fecha:
\_\_\_\_\_\_\_\_\_\_\_\_ Anfitrión:
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

*Objetivo: entender el flujo completo de material (de dónde llega, dónde
se descarga, qué se le hace, a dónde va, dónde se guarda y con qué
lógica) para dimensionar la solución de montacargas autónomos: rutas,
número de equipos, integración con sistemas e infraestructura
necesaria.*

1\. Contexto general de la operación

| **Pregunta**                                                                                                                             | **Respuesta / Notas** |
|------------------------------------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Qué producto(s) maneja el almacén? ¿Familias, categorías, valor aproximado?                                                             |                       |
| ¿Cuál es el rol del almacén en la cadena? (centro de distribución, materia prima de planta, producto terminado, cross-dock, e-commerce…) |                       |
| ¿Superficie total (m²), altura libre y número de naves/niveles?                                                                          |                       |
| ¿Cuántas posiciones de tarima tiene y qué % de ocupación promedio maneja?                                                                |                       |
| ¿Cuántas tarimas entran y salen por día? (promedio y pico)                                                                               |                       |
| ¿Horario de operación y turnos? ¿Operan fines de semana?                                                                                 |                       |
| ¿Estacionalidad? ¿Cuáles son los meses/semanas pico y cuánto sube el volumen?                                                            |                       |
| ¿Cuál es el dolor principal que quieren resolver con la automatización? (costo, escasez de operadores, daños, seguridad, throughput…)    |                       |

2\. Recepción — ¿dónde cargan y descargan?

| **Pregunta**                                                                                                  | **Respuesta / Notas** |
|---------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Cuántos muelles/andenes de recepción hay y dónde están en el plano?                                          |                       |
| ¿Los muelles son exclusivos de recepción o compartidos con embarques? ¿Cambia por turno?                      |                       |
| ¿Qué tipo de vehículos llegan? (trailer 53', torton, contenedor, camioneta…)                                  |                       |
| ¿Con qué se descarga hoy? (montacargas contrabalanceado, patín, mano) ¿Cuántos equipos y personas por camión? |                       |
| ¿Cuánto tarda en promedio descargar un camión completo?                                                       |                       |
| ¿Hay citas programadas para llegadas o es a demanda? ¿Cuántos camiones por día?                               |                       |
| ¿Se descarga tarima completa, o hay carga suelta/a piso que se paletiza al recibir?                           |                       |
| ¿Hay rampas niveladoras, sellos de andén, topes? ¿Estado y dimensiones?                                       |                       |
| ¿Existe patio de maniobras? ¿Quién controla el orden de llegada de camiones?                                  |                       |

3\. Proceso de la carga — ¿qué se hace al recibirla?

| **Pregunta**                                                                              | **Respuesta / Notas** |
|-------------------------------------------------------------------------------------------|-----------------------|
| Después de bajar la tarima del camión, ¿dónde se coloca primero? (zona de staging/recibo) |                       |
| ¿Qué inspección se hace? (conteo, calidad, temperatura, daños) ¿Cuánto tarda?             |                       |
| ¿Se etiqueta o re-etiqueta? ¿Con qué? (etiqueta de tarima, LPN, código de barras, RFID)   |                       |
| ¿Se re-paletiza o re-estiba? ¿Se emplaya? ¿Hay estación de emplayado?                     |                       |
| ¿En qué momento se registra la entrada en el sistema? ¿Escaneo o captura manual?          |                       |
| ¿Cuánto tiempo permanece la carga en staging antes de guardarse (putaway)?                |                       |
| ¿Hay mercancía que se cruza directo a embarques sin almacenarse (cross-dock)? ¿Qué %?     |                       |
| ¿Qué pasa con rechazos, devoluciones o material dañado? ¿A dónde van?                     |                       |

4\. Almacenamiento — ¿a dónde va y dónde se guarda?

| **Pregunta**                                                                                                    | **Respuesta / Notas** |
|-----------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Qué tipos de almacenamiento hay? (rack selectivo, drive-in, push-back, a piso/bloque, mezzanine, cámara fría…) |                       |
| ¿Cuántos niveles de rack y a qué altura está la última viga? ¿Altura máxima de guardado?                        |                       |
| ¿Ancho de pasillos entre racks? (medir: ¿3.0 m, 3.5 m, angosto VNA?)                                            |                       |
| ¿Quién decide a qué ubicación va cada tarima: el sistema (WMS) o el operador?                                   |                       |
| ¿Las ubicaciones están identificadas y codificadas? (etiquetas, nomenclatura de pasillo-bahía-nivel)            |                       |
| ¿Manejan ubicaciones fijas por SKU o ubicación caótica/aleatoria?                                               |                       |
| ¿Una tarima = un SKU, o hay tarimas mixtas?                                                                     |                       |
| ¿Qué distancia promedio recorre un montacargas del muelle a la ubicación?                                       |                       |
| ¿Hay zonas especiales? (temperatura controlada, inflamables, alto valor, cuarentena)                            |                       |

5\. Lógica de acomodo — ¿cómo escogen el orden del almacén?

| **Pregunta**                                                                                        | **Respuesta / Notas** |
|-----------------------------------------------------------------------------------------------------|-----------------------|
| ¿Con qué criterio se asigna la ubicación? (rotación ABC, familia, cliente, tamaño, peso, caducidad) |                       |
| ¿Manejan FIFO, FEFO o LIFO? ¿Quién lo garantiza: sistema o memoria del operador?                    |                       |
| ¿Los productos de alta rotación están cerca de los muelles? ¿Se re-slotea periódicamente?           |                       |
| ¿Hay reglas de apilado? (tarimas dobles, peso máximo por nivel, productos que no pueden ir arriba)  |                       |
| ¿Cómo encuentran hoy una tarima específica? ¿Qué tan seguido “se pierde” producto?                  |                       |
| ¿Con qué frecuencia hacen inventarios cíclicos/físicos y qué exactitud tienen?                      |                       |
| ¿Qué % del acomodo es criterio del operador vs. dirigido por sistema? (clave para automatizar)      |                       |

6\. Picking, reabastecimiento y surtido

| **Pregunta**                                                                          | **Respuesta / Notas** |
|---------------------------------------------------------------------------------------|-----------------------|
| ¿Se surte tarima completa, cajas (layer/case picking) o piezas?                       |                       |
| ¿Dónde se hace el picking: en niveles bajos de rack, zona dedicada, mezzanine?        |                       |
| ¿Cómo se reabastecen las posiciones de picking y quién lo dispara?                    |                       |
| ¿Cuántas líneas/tarimas se surten por día? ¿Olas de surtido u órdenes en tiempo real? |                       |
| ¿Se consolida y emplaya el pedido antes de embarcar? ¿Dónde?                          |                       |

7\. Despacho (embarques) — ¿por dónde sale?

| **Pregunta**                                                                 | **Respuesta / Notas** |
|------------------------------------------------------------------------------|-----------------------|
| ¿Cuántos muelles de embarque y dónde están en el plano?                      |                       |
| ¿Hay zona de staging de embarques? ¿Cuántas posiciones de tarima por camión? |                       |
| ¿Cómo se ordena la carga del camión? (por ruta, por parada, por peso)        |                       |
| ¿Quién carga el camión y con qué equipo? ¿Tiempo promedio de carga?          |                       |
| ¿Se valida la carga al salir? (escaneo, checklist, fotos, sello)             |                       |
| ¿Cuántos embarques por día y en qué horarios se concentran?                  |                       |

8\. Unidad de carga — tarimas y producto

| **Pregunta**                                                                      | **Respuesta / Notas** |
|-----------------------------------------------------------------------------------|-----------------------|
| ¿Qué tarimas usan? (medidas: 48x40", 1200x1000, europea; madera/plástico; estado) |                       |
| ¿Peso mínimo, promedio y máximo por tarima cargada?                               |                       |
| ¿Altura de la tarima cargada (con y sin emplayado)? ¿Es estable la estiba?        |                       |
| ¿La entrada de la tarima es a 2 o 4 vías? ¿Estado de los patines (rotos, clavos)? |                       |
| ¿Hay cargas no paletizadas? (rollos, tambos, súper sacos, carga larga)            |                       |

9\. Flota actual y personas

| **Pregunta**                                                                                                            | **Respuesta / Notas** |
|-------------------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Cuántos montacargas tienen hoy y de qué tipo/marca/capacidad? (contrabalanceado, reach, order picker, patín eléctrico) |                       |
| ¿Combustión o eléctricos? ¿Dónde cargan/cambian baterías o gas?                                                         |                       |
| ¿Cuántos operadores por turno? ¿Rotación y dificultad para contratar?                                                   |                       |
| ¿Horas de uso por equipo por día? ¿Renta o propios?                                                                     |                       |
| ¿Historial de incidentes/accidentes con montacargas? ¿Daños a producto o racks por año?                                 |                       |

10\. Infraestructura del edificio (crítico para robots)

| **Pregunta**                                                                                                            | **Respuesta / Notas** |
|-------------------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Estado del piso: material, planicidad, grietas, juntas, rampas y pendientes?                                           |                       |
| ¿Hay desniveles, rejillas, guarniciones o cambios de superficie en las rutas?                                           |                       |
| ¿Ancho y altura de puertas y cortinas entre zonas? ¿Puertas rápidas o manuales?                                         |                       |
| ¿Cobertura WiFi/red en todo el almacén? ¿Hay zonas muertas? ¿Es posible instalar 5G privado?                            |                       |
| ¿Dónde hay tomas eléctricas disponibles para estaciones de carga de robots? ¿Capacidad eléctrica del sitio?             |                       |
| ¿Iluminación por zona? ¿Trabajan zonas a oscuras?                                                                       |                       |
| ¿Tráfico mixto: personas, montacargas manuales, camiones dentro de la nave? ¿Pasillos peatonales marcados?              |                       |
| ¿Obstáculos temporales frecuentes? (tarimas en piso, basura, emplaye suelto)                                            |                       |
| ¿El plano DWG que nos compartieron está actualizado vs. la realidad? Pedir versión DXF/PDF y fecha del último as-built. |                       |

11\. Sistemas y datos

| **Pregunta**                                                                                                     | **Respuesta / Notas** |
|------------------------------------------------------------------------------------------------------------------|-----------------------|
| ¿Qué WMS/ERP usan? (SAP, Oracle, Dynamics, propio…) ¿Versión y quién lo administra?                              |                       |
| ¿El WMS dirige tareas a los operadores (RF/handheld) o se trabaja en papel?                                      |                       |
| ¿Existe API o interfaz para integrar un sistema de gestión de flota de robots?                                   |                       |
| ¿Pueden compartir datos históricos: movimientos por día, entradas/salidas por SKU, mapa de calor de ubicaciones? |                       |
| ¿Maestro de SKUs con dimensiones y pesos? ¿Qué tan confiable es?                                                 |                       |
| ¿Quién sería el responsable de IT del lado del cliente para el proyecto?                                         |                       |

12\. Operación y KPIs

| **Pregunta**                                                                             | **Respuesta / Notas** |
|------------------------------------------------------------------------------------------|-----------------------|
| ¿Qué KPIs miden hoy? (tarimas/hora, costo por movimiento, exactitud de inventario, OTIF) |                       |
| ¿Cuál es el costo actual por operador y por equipo (renta, mantenimiento, energía)?      |                       |
| ¿Cuáles son los cuellos de botella actuales y en qué horarios ocurren?                   |                       |
| ¿Qué procesos consideran intocables y cuáles están dispuestos a cambiar?                 |                       |
| ¿Expectativa de fases? (piloto en una zona, un flujo específico, todo el almacén)        |                       |
| ¿Tienen fecha objetivo o presupuesto asignado para el proyecto?                          |                       |

13\. Seguridad y normativa

| **Pregunta**                                                                               | **Respuesta / Notas** |
|--------------------------------------------------------------------------------------------|-----------------------|
| ¿Protocolos de seguridad actuales? (velocidades, cinturones, semáforos, espejos)           |                       |
| ¿Normas internas o de corporativo que un robot deba cumplir? (auditorías, certificaciones) |                       |
| ¿Rutas de evacuación y zonas donde un robot no debe entrar u obstruir?                     |                       |
| ¿Sindicato o temas laborales a considerar en la automatización?                            |                       |

14\. Durante el recorrido: observar, medir y fotografiar

- Fotos/video de: muelles en operación, zona de staging, pasillos, racks
  (frente y perfil), piso, puertas, tarimas típicas.

- Medir: ancho de pasillos, altura de última viga, ancho/alto de
  puertas, pendiente de rampas, espacio libre en muelles.

- Cronometrar un ciclo real: descarga → staging → putaway; y picking →
  staging → carga de camión.

- Contar equipos y personas activas por zona en ese momento.

- Observar el estado real de tarimas y estibas (lo que dicen vs. lo que
  se ve).

- Detectar obstáculos y desorden en rutas: tarimas a piso, cables,
  charcos, emplaye.

- Probar señal de celular/WiFi en distintos puntos de la nave.

- Identificar dónde podrían ir estaciones de carga y zona de
  mantenimiento de robots.

15\. Documentos y datos a solicitar

- Plano actualizado en DWG/DXF y PDF (as-built), con capas de racks,
  muelles y oficinas.

- Datos de 6–12 meses: entradas/salidas diarias por muelle, movimientos
  por SKU, picos.

- Maestro de SKUs con dimensiones, peso y rotación (ABC).

- Layout de ubicaciones del WMS (nomenclatura y capacidad por posición).

- Especificación de la flota actual de montacargas y sus horas de uso.

- Estudio de piso (si existe) y planos eléctricos/de red.

- Reportes de incidentes y daños del último año.

Notas del plano RETHINK_2026.dwg

El archivo es AutoCAD 2018+ (guardado con AutoCAD 2027, junio 2026,
autor: edy.estevez). Del contenido se identifican capas como “MAXICUBO”,
“paleteira” (patín/paleteira), “oficinas IT” y “planta”, lo que sugiere
un layout de planta con racks y oficinas. Para el análisis completo de
rutas conviene pedir el archivo en formato DXF o PDF, y confirmar en
sitio que el plano refleje la realidad actual.
