# El manual impreso de operación — índice

**Fotos del 30-sep-2026.** Es el mismo manual de donde salieron las páginas de fusibles
(`herramientas/serie/manual_fusibles_p142.jpg` y `_p143.jpg`). El pie de página dice
`04.17 US_ES`.

| Archivo | Páginas del índice |
|---|---|
| `indice_p7.jpg` | A a E 2.3: normativa, uso previsto, datos técnicos, placas, manejo |
| `indice_p8.jpg` | E 2.4 a G 5.2: display, conducción, hidráulica, **acceso sin llave**, batería, mantenimiento |
| `indice_p9.jpg` | G 5.3 a H: fusibles, puesta fuera de servicio, transporte |

## Qué manual es

**Es un manual de operador**, no el de taller: los capítulos son de manejo, mantenimiento
de rutina y batería, sin parámetros ni códigos de falla. Su lista de chequeo de
mantenimiento dice **«ESR 15N2 - ESR 23N2»**.

> **Dato en tensión con `CLAUDE.md`:** el manual de operador que figura como pendiente es
> el **O&M ESR20N2 · ESR23N2 · EDR18N2, edición 01/2022**. Este es `04.17`, que parece una
> edición anterior, y el índice no nombra al EDR18N2. **Puede ser una edición vieja del
> mismo manual, o el de la familia ESR sin el EDR.** No se da por conseguido el de la
> lista. Lo que sí se sabe: su tabla de fusibles coincide posición por posición con la
> tarjeta del equipo, así que al menos esa parte aplica.

El manual de **taller**, `WENBM8550-01`, sigue sin conseguirse.

## El índice, transcrito

Los números de página de `indice_p8.jpg` se leyeron de una foto inclinada. **Pueden estar
corridos ±1.**

```
A    Cumplimiento de las normativas                                    11
B    Reconocer y evitar peligros                                        13
C    Uso previsto y apropiado                                           15
     1 Generalidades 15 · 2 Aplicación prevista 15 · 3 Condiciones de
     aplicación 15 · 4 Obligaciones del empresario 16 · 5 Montaje de
     implementos y equipamientos adicionales 17 · 6 Indicaciones 18 ·
     7 Estabilidad 20
D    Conozca su carretilla industrial                                   21
     1   Elementos de indicación y de mando                             21
     2   Cuadro sinóptico de los grupos constructivos                   23
     3   Unidad de indicación (display)                                 24
     4   Datos técnicos                                                 26
     4.1 Prestaciones 26 · 4.2 Pesos 29 · 4.3 Ruedas 29
     4.4 Dimensiones                                                    30
     4.5 Batería 34 · 4.6 Normas EE.UU. 35 · 4.7 Condiciones de
     aplicación 37 · 4.8 Requisitos eléctricos 37
     5   Señalizaciones y placas 38 · 5.2 Placa de características 40 ·
         5.3 Placa de capacidades de carga 41
E    Manejo                                                             43
     1   Aspectos generales 43 · 1.1 Formación y autorización 43 ·
         1.2 Daños y reparaciones 46 · 1.3 Carga 47 · 1.4 Entorno 48 ·
         1.5 Dispositivos de seguridad y placas de advertencia 52
     2   Configurar display 53 · 2.1 Dispositivo de indicación
         (4 pulgadas) 53 · 2.2 Asignación de teclas 55 · 2.3 Símbolos 57 ·
         2.4 Configurar hora 58
     3   Preparar para el servicio 59 · 3.1 Verificaciones diarias 59
     4   Poner en servicio                                              60
     4.1 Normas de seguridad 60 · 4.2 Trabajar 66 · 4.3 Carga y
         transporte 69 · 4.4 Peligro de vuelco 72 · 4.5 Vigilancia 74 ·
         4.6 Preparar 75
     4.7  Parada de emergencia                                          77
     4.8  Definición del sentido de marcha                              78
     4.9  Marcha                                                        79
     4.10 Frenos                                                        82
     4.11 Dirección                                                     85
     4.12 Ajuste de los brazos de horquilla 86 · 4.13 Elevación 87 ·
          4.14 Inclinación 89 · 4.15 Desplazador lateral 90 ·
          4.16 Extensión/retracción 91 · 4.17 Elevación, transporte y
          depósito 93 · 4.18 Implementos 97 · 4.19 Pantógrafo 98
     4.20 Descenso de emergencia                                        99
     4.21 Aparcamiento 100
     5    Equipamiento opcional                                         101
     5.1  Sistemas de acceso sin llave                                  101
     5.2  Generalidades del acceso sin llave                            101
     5.3  Manejo del teclado                                            102
     5.4  Manejo de la unidad de indicación                             109
F    Batería: mantenimiento, carga, cambio                              113
G    Mantenimiento de la carretilla                                     119
     3.1 Lista de chequeo ESR 15N2 - ESR 23N2 125 · 4 Fluidos y
         lubricación 131 · 5.2 Nivel de aceite hidráulico 138
     5.3 Comprobar los fusibles eléctricos                              141
     6   Desconexión por largo periodo 144 · 6.3 Nueva puesta en
         servicio 147 · 7 Desmontaje y eliminación 148
H    Transporte y primera puesta en servicio                            149
     1 Grúa 149 · 2 Transporte 150 · 3 Primera puesta en servicio 151
```

## Qué páginas fotografiar después, y para qué

En orden de lo que más destraba:

| Páginas | Sección | Para qué |
|---|---|---|
| **101–109** | **Sistemas de acceso sin llave, teclado** | **El pin 6 del DB9 cuelga del fusible `4F15`, «autorización de acceso».** Esta sección dice qué es ese sistema y si se conecta ahí. Es la pista más directa hacia «a dónde iba la masa del puerto» |
| **77–86** | Parada de emergencia, sentido de marcha, marcha, frenos, dirección | Cómo lo maneja un operador de verdad. El mapeo del control en `docs/19` tiene que copiar esto, no inventarlo |
| **30–33** | Dimensiones | Puede traer el ancho entre patas, el `W_MAX` que **nunca se ha medido** |
| **24, 53–58** | Display y configuración | La deuda del menú de servicio que nunca se documentó |
| **99** | Descenso de emergencia | Entra en la pregunta abierta de `docs/10`: frenar con carga en alto |
| **37** | Requisitos eléctricos | Tensión de trabajo y referencias |
| **40** | Placa de características | Qué dice la placa, para cruzar con la del equipo |
