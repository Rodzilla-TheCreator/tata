# Plan de diagnóstico — la visita antes de intervenir

**Este documento va antes que [`10-intervencion-electrica.md`](10-intervencion-electrica.md).**
Los tres planes de intervención tienen bifurcaciones que no se pueden resolver desde acá.
Esta visita las cierra.

Regla de la visita: **no se corta ni un cable.** Todo se mide con el conector puesto.
Salís con datos, no con un equipo intervenido.

---

## 1 · Las doce preguntas

El entregable de la visita es esta tabla llena. Si volvés con las doce, los tres planes
quedan determinados y no hay que volver.

| # | Pregunta | Por qué decide algo | Respuesta |
|---|---|---|---|
| 1 | ¿Hay CAN accesible, y las consignas de marcha viajan por ahí? | Si sí, puede que no haya que cortar nada | |
| 2 | ¿La referencia de los sensores es 5 V o 12 V? | Fija el búfer del DAC y si hace falta adaptar nivel | |
| 3 | Mando de mano: ¿cuántos hilos, y cuáles se mueven al revés? | Confirma el par redundante. **Sin esto no se inyecta nada** | |
| 4 | Valores del mando: reposo / full adelante / full reversa | Son los extremos que el DAC tiene que reproducir | |
| 5 | ¿Existe señal analógica de freno? | Decide entre caso A / B / C del Plan 1 | |
| 6 | Hombre-presente: ¿NC o NO? ¿a qué tensión? | Es el relé del freno binario | |
| 7 | ¿Cuánto tarda en caer el freno al soltar el hombre-presente? | Es la latencia real de tu parada | |
| 8 | Dirección: ¿analógica, encoder en cuadratura, o CAN? | **La bifurcación del Plan 3** | |
| 9 | ¿Cómo se leen y cómo se borran los códigos de falla? | Vas a provocar fallas. Sin esto se te muere la demo | |
| 10 | ¿De dónde salen 12 V utilizables? | Alimentación del Arduino | |
| 11 | ¿El motor de tracción ya trae sensor de velocidad accesible? | Odometría gratis si sí | |
| 12 | Largo de patas portantes, ancho del cuerpo superior, radio de la esquina trasera | Cierra el modelo del giro, que hoy da negativo contra la realidad | |

La **9 es la que todos olvidan.** Vas a disparar códigos de falla haciendo esto. Si no
sabés borrarlos, el equipo queda bloqueado y el día se acabó.

---

## 2 · Herramientas

### Lo que decide si la visita sirve

| Herramienta | Para qué | Sin esto |
|---|---|---|
| **Puntas de retro-sondeo** (back-probe) | medir con el conector puesto | tenés que desconectar o pinchar cable — inaceptable |
| **Analizador lógico 8 canales** | preguntas 1, 8, 11 | no distinguís encoder de analógico y el Plan 3 queda abierto |
| **Multímetro con captura mín/máx** | preguntas 2, 4, 5, 6 | el promedio te miente en señales que se mueven |
| **Celular con cámara lenta** | pregunta 7 | la latencia del freno no se mide a ojo |

Las **puntas de retro-sondeo** son la herramienta clave y la que nadie lleva. Son pines
finos que entran por atrás del conector, hacen contacto con el terminal y te dejan medir
con todo conectado y el equipo funcionando. Si no las conseguís: alfileres de costura de
los gruesos y termorretráctil. Funciona.

### Lo demás

| | |
|---|---|
| Analizador USB-CAN (CANable / Korlan) | pregunta 1, si resulta que hay CAN |
| AS5600 + Arduino armado y probado en casa | pregunta 8, pegado a la columna con cinta |
| Caimanes, banana, cable de prueba | |
| Cinta de enmascarar y marcador | etiquetar **cada** cable antes de tocarlo |
| Flexómetro y calibrador | pregunta 12 |
| Linterna de cabeza | vas a estar debajo del equipo |

### Lo que NO llevás

El cautín, la placa perforada y los DAC. Si los llevás, los vas a usar, y todavía no sabés
en qué.

---

## 3 · El procedimiento, en orden

El orden importa: va de lo que no toca nada, a lo que toca poco. **Cada etapa tiene una
condición de parada.**

### Etapa 0 · Antes de encender (30 min)

1. **Foto de cada conector**, con etiqueta de papel visible en la foto. Antes de nada.
2. Foto de la placa de datos: modelo exacto, número de serie, año, voltaje de batería.
3. Foto del tablero de instrumentos con el equipo apagado.
4. **Buscá el conector de diagnóstico.** Casi siempre hay uno. Fotografialo.
5. Con el equipo **apagado**, medí resistencia entre los pines candidatos a CAN:
   **120 Ω entre CANH y CANL es la firma inconfundible.** Si aparece, hay bus.

*Parada:* si no encontrás el conector de diagnóstico, seguí igual. No lo busques más de 20 min.

### Etapa 1 · Encendido, sin mover (45 min)

6. Referencia de sensores: medí entre el V+ del mando y masa. **5 o 12 V** → pregunta 2.
7. Con el equipo encendido y el operador **fuera**, retro-sondeá cada hilo del mando de mano.
   Anotá el valor en reposo de todos.
8. Que el operador mueva el mando **despacio**, a fondo adelante y a fondo atrás, sin
   habilitar marcha. Anotá mín y máx de cada hilo.
   → **Dos hilos que se mueven en sentido contrario = el par redundante.** Preguntas 3 y 4.
9. Lo mismo en el pedal de freno si existe. Si ningún hilo se mueve al pisarlo, es **caso B**
   y ya sabés que el Plan 1 va por el relé. Pregunta 5.
10. Hombre-presente: medí con el pie fuera y con el pie puesto. Anotá tensión y si es NC o NO.
    Pregunta 6.

*Parada:* si la referencia es de 12 V, tu búfer de 5 V no sirve. Anotalo y no improvises.

### Etapa 2 · Dirección (30 min)

11. **AS5600 pegado a la columna** con cinta de doble faz. No toca nada del equipo.
12. Retro-sondeá los hilos del sensor del volante. Girá despacio de tope a tope.
    - Si un hilo **barre suave** de un valor a otro → **analógico**. Plan 3 fácil.
    - Si ves **dos hilos conmutando en escalones desfasados** → **cuadratura**. Plan 3 mecánico.
    - Si no se mueve nada y hay CAN → la consigna va por el bus.
13. Enganchá el analizador lógico a esos dos hilos y girá otra vez. La captura te lo confirma.
    Pregunta 8.

*Parada:* con esto el Plan 3 queda decidido. Es la pregunta más cara de equivocar.

### Etapa 3 · En movimiento, con operador (45 min)

Área despejada, operador experimentado a los mandos, vos midiendo. **Dos personas, siempre.**

14. Analizador USB-CAN escuchando mientras el operador maneja normal. Grabá **todo**:
    marcha adelante, reversa, elevación, dirección. Guardá el log. Pregunta 1.
15. Cámara lenta del celular apuntando a la rueda mientras el operador suelta el
    hombre-presente a velocidad de trabajo. Contá cuadros hasta que se detiene. Pregunta 7.
16. Retro-sondeo en el motor de tracción buscando un sensor de velocidad. Pregunta 11.
17. Buscá de dónde sacar 12 V: luces, bocina, tomacorriente accesorio. Pregunta 10.

### Etapa 4 · Fallas y geometría (30 min)

18. Preguntale al mecánico de Montasa cómo se leen y borran los códigos. Si hay manual de
    servicio, fotografiá esa sección completa. Pregunta 9.
19. Las tres medidas de geometría de la pregunta 12:
    - **Patas portantes:** de la punta hacia atrás, dónde terminan
    - **Cuerpo superior:** ancho del capó verde en su punto más ancho
    - **Esquina trasera:** el radio de la curva. A ojo sirve — ¿10 cm o 20 cm?

---

## 4 · Lo que se hace y lo que no

| | |
|---|---|
| ✓ Retro-sondear con el conector puesto | |
| ✓ Pegar sensores propios que no tocan nada | AS5600, IMU |
| ✓ Escuchar el CAN en modo solo lectura | |
| ✗ Cortar, pinchar o desconectar cualquier cable | |
| ✗ Inyectar cualquier señal | |
| ✗ Probar qué pasa si desconecto una de las redundantes | **eso dispara falla y bloquea el equipo** |
| ✗ Trabajar solo | |
| ✗ Medir con el equipo en alto sin calzos | |

Esa penúltima da tentación. **No la hagas en esta visita.** Es información útil, pero se
prueba cuando ya sabés borrar los códigos — o sea, después de responder la pregunta 9.

---

## 5 · Lo que traés de vuelta

1. La tabla de doce preguntas, llena
2. El log del CAN, si había
3. Las capturas del analizador lógico de la dirección
4. Fotos de todos los conectores, etiquetadas
5. Las tres medidas de geometría
6. El video en cámara lenta del frenado

Con eso, en una tarde y sin volver al sitio, quedan cerrados los tres planes: qué caso es el
freno, cómo se mapea el mando y si la dirección va por cable o por motor en la columna.

**Recién ahí se calienta el cautín.**
