# El viaje al taller — plan y datos de campo

Taller Montasa, colonia Las Palmas. **Escrito el 11-sep-2026, para el viaje del 12.**

Dos objetivos en el mismo viaje, y **el primero va antes que el segundo aunque
el segundo sea más entretenido**: dos medidas con flexómetro cierran el bloqueo
número uno del proyecto, y el puerto de servicio se puede comer el día entero.

> **Actualizado el 25-sep-2026.** Apareció el cable de Judit y el chino lo confirmó.
> Cambia la herramienta, cambia el cableado y se levanta el techo de 14400. Ver
> **«Actualización del 25-sep-2026»** más abajo: **manda sobre todo lo de este documento**,
> incluida la sección «Lo que ya se sabe del puerto», que se conserva como historial.

---

## La máquina

| | |
|---|---|
| Modelo | Mitsubishi **EDR18N2** |
| Serie | **82824121** |
| Fabricante | Mitsubishi Caterpillar Forklift America · Houston, TX · hecho en EE.UU. |
| Equipo (config) | SSINT2RCH1 |
| Horómetro | **11,663 h** |
| Peso sin batería | 3,186 kg |
| Batería | 36 V · 1120 Ah · 1,050 a 1,180 kg |
| Falla activa | **E2320.01** |
| Clasificación | tipo **E / EE**, NO es EX |

**Peso total vacío: 4,240 a 4,370 kg.** No estaba en el repo; la capacidad de
carga de 1.58 t es otra cosa. Cargado pasa de 5.9 t, y esa es la energía
cinética que la capa de seguridad de `docs/04` tiene que detener.

**Tipo E/EE y no EX** quiere decir que este equipo **hoy ya no debería entrar a
una zona clasificada**, con o sin TaTa. La pregunta abierta de `docs/03` sobre
el área de mixers deja de bloquear el BOM y pasa a ser tema existente del
cliente.

**Le quitaron una válvula hidráulica: el equipo NO se mueve. Sí enciende.**
Eso no es una capa de seguridad — no tratarlo como si lo fuera.

---

## Qué llevar

```
□ Laptop cargada + cargador          □ Multímetro
□ CABLE FTDI DB9→USB (el de Judit)   □ Flexómetro
□ ESP32 + T132 (respaldo)            □ Plomada: cordón y una tuerca
□ Null-modem (respaldo, NO se usa)   □ Masking tape + lapicero
□ Cadena CAN armada (2º instrumento) □ Papel · Jumpers
```

### Antes de salir · 5 min

```
□ Loopback del FTDI: jumper pin 2–3, probador.py
  → leer la línea LOOPBACK, NO el veredicto «ESTE SIRVE»
□ Cargar escucha_edr.ino al ESP32 (respaldo)
□ QUITAR EL JUMPER del DB9 y guardarlo aparte
```

---

## A · Sin encender — esto primero

### A1 · Ancho total, pata a pata

```
Ancho máximo (estación 102 a 150) = ______ cm
```

Flexómetro cruzado por fuera de las dos patas portantes. Como el ancho es
constante en esos 48 cm, no hay que atinarle a un punto exacto.

**Por qué importa:** la silueta medida el 8-sep tiene la forma completa pero su
escala lateral está anclada al `W_MAX = 1.315` del repo, que nunca se midió. Con
un solo lado medido, la simetría da la forma pero no el ancho. Este número la
vuelve 100% medida.

### A2 · XPIV — el bloqueo número uno

```
Estación del centro de la rueda de carga, desde el culo = ______ cm
```

Plomada desde el perno central del eje. Si no se ve el perno: plomada en el
punto más adelantado de la rueda y en el más atrasado, y se toma el medio.

**Por qué importa:** `XPIV` sigue **derivado del radio de ficha, no medido**.
Y hay una contradicción abierta: la llanta medida en la estación 282, si fuera
la motriz y el entre-ejes fuera 156.2, daría `XPIV = 1.862 m`. Pero la cota dura
que sale de `Wa = 1.797` con el ancho medido exige `XPIV < 1.672 m`. Uno de los
tres números miente.

### A3 · El culo, con plomada

```
Perpendicular estricta del culo al flexómetro = ______ cm
```

Los 95 cm del 8-sep dan semiancho negativo — 5.25 cm del otro lado del eje.
Imposible. O se midió en diagonal, o el flexómetro se abrió ~1° en 3 m.

### A4 · La masa del puerto

```
pin 5 ↔ chasis = ______        pin 6 ↔ chasis = ______
```

Se asume que el pin 5 es la masa de señal, pero el cable de fábrica que apareció
en el taller usaba el **pin 6**. Si el 5 da abierto y el 6 da ~0, el null-modem
no conecta referencia y no se recibe nada aunque todo lo demás esté bien.

---

## B · Encendido — el puerto de servicio

DE-9 hembra en la placa de fusibles. Herramienta: **el cable FTDI directo**,
sin null-modem, como lo conectaba el chino. El ESP32 + T132 queda de respaldo.

```
□ Vuelta 1 · FTDI directo, barrido completo
□ Vuelta 2 · navegando Settings → Menu → Drive → diagnóstico
             mientras se escucha
□ Vuelta 3 · solo si 1 y 2 dan silencio: ESP32 + T132, con y sin null-modem
```

Cada vuelta son ~3 min: 9 velocidades × 6 framings. **Con el FTDI el barrido puede
subir arriba de 14400 por primera vez** — el tope era del CH340, no del equipo.

La vuelta 2 es la que prueba la hipótesis viva más fuerte: que el puerto solo
hable mientras el display habla.

---

## C · Gratis, mientras está encendido

```
□ Fotos de TODO el árbol del menú — lift, drive, steer
□ ¿Hay valores en vivo? velocidad, ángulo de dirección, corriente, temperaturas
□ ¿Se cambia P1..P5 desde el teclado?
□ Fotos de las etiquetas de los controladores
□ A los mecánicos: ¿qué es E2320.01?
                   ¿CÓMO SE BORRAN LOS CÓDIGOS DE FALLA?
```

La última es la que `CLAUDE.md` marca como la que hunde el día si falta, y hay
una falla activa ahora mismo para probarlo.

Si el menú de diagnóstico muestra velocidad, ángulo y altura en vivo, ahí está
la mitad de retroalimentación que `docs/10` daba por perdida — **sin cortar un
solo cable**.

---

## Reglas

- **Jumper fuera** antes de conectar al equipo. Puentear el pin 2 con el 3 del
  montacargas es cortocircuitar dos líneas que el controlador maneja
- El ESP32 **solo escucha**. No transmitir sin consultarlo antes
- Si aparece un código de falla nuevo en el display: parar y avisar
- Equipo de un cliente en un taller ajeno. Nada irreversible

---

## Lo que ya se sabe del puerto

Para no repetir pruebas que ya se hicieron.

> **Historial.** Escrito el 11-sep. La lectura de estos datos cambió el 25-sep —
> ninguna medición se cayó, el modelo sí. Ver la actualización al final.

### Medido

```
Óhmetro, apagado, sin adaptador:
  pin 2 ↔ pin 7   ABIERTO       → no es un bus CAN terminado

Voltímetro DC, encendido, negra a chasis, sin adaptador:
  1, 4, 5, 7, 9   0 V firme
  6               +0.1 V   flotante
  8               −0.1 V   flotante
  2               −5 a −12 V    VARIABLE
  3               −14.6 V estable, luego −5 a −9 V   VARIABLE
```

**Los −14.6 V estables son la firma de un transmisor RS-232 en reposo**, y que
después bajen a −5/−9 variable es tráfico: el multímetro promedia, y una línea
que conmuta entre marca y espacio corre el promedio hacia cero. **Los pines 2 y
3 tienen actividad.**

### Descartado, y por qué

| | |
|---|---|
| CAN | los −14.6 V. CAN va de 0 a 5 V, nunca negativo. El `2↔7` abierto **no** lo descarta por sí solo: un ramal de diagnóstico normalmente no lleva terminador |
| Señal en CTS/DSR/CD/RI | dos corridas idénticas dieron resultados distintos. Es la entrada del adaptador flotando |

### Lo que NUNCA se probó de verdad

Todas las corridas de escucha previas se hicieron con un adaptador CH340
defectuoso —tope en 14400, rechazaba toda paridad— **y** con cableado recto
DTE contra DTE, donde nuestro RX quedaba amarrado a su RX. **Ninguna dice nada
sobre el equipo.**

Nunca se escuchó ni un segundo arriba de 14400, ni con paridad.

### El cable de fábrica que apareció en el taller

Modular de 8 posiciones con 4 hilos, mapeado con óhmetro:

```
naranja → pin 2      amarillo → pin 6
rojo    → pin 7      café     → pin 9
```

Los pines **2, 6, 7 y 9** son exactamente el pinout **CiA-303** — CAN_L, masa,
CAN_H y V+. Salta el 3 y el 5, que son los dos que un cable RS-232 no puede
omitir.

**Pero ese cable no está confirmado como de esta máquina.** Apareció en el
taller y entra mecánicamente, lo que un DE-9 hace en muchas cosas. Queda como
dato en tensión con los voltajes, no como conclusión.

---

## Qué traer de vuelta

```
1. Ancho total + XPIV          ← lo más valioso del día
2. Lo que salga del puerto
3. Fotos del menú de diagnóstico
4. Lo que digan los mecánicos sobre E2320.01 y el borrado de códigos
```

Con el 1 se corre `analisis/planificador_giro.py` con la silueta completamente
medida y sale la ventana de carriles real, sin una sola suposición.

---

## Herramientas

En `herramientas/serie/`:

| Archivo | Qué es |
|---|---|
| `prueba_cadena.ino` | Valida ESP32 + T132 + cableado + conector. Detecta solo si RX y TX están al revés. **Correr antes de cada salida** |
| `escucha_edr.ino` | Escucha pasiva del puerto. 9 velocidades × 6 framings. `MODO_FIJO` para el modo menú |
| `probador.py` | Interfaz para calificar un adaptador USB-serie en el mostrador. Velocidad, paridad y loopback, con veredicto en castellano |

Cableado del T132:

```
GND → ESP32 GND      TX → ESP32 GPIO16
VCC → ESP32 3V3      RX → ESP32 GPIO17
```

**3.3 V, nunca 5 V** — la salida TTL del SP3232 sigue al VCC, y el GPIO del
ESP32 no tolera 5.

---

## Actualización del 25-sep-2026 — apareció el cable y el chino lo confirmó

Manda sobre todo lo de arriba.

En una caja del taller apareció un **cable DB9 macho → USB, chip FTDI**, de capuchón
delgado. Se le mandó foto al chino por WhatsApp y contestó: **«si ese es»**. Es el cable
con el que operaba Judit, **sin caja de por medio**. Su memoria era literal.

### La lectura que deja válidas todas las mediciones

> **El DE-9 del equipo es un puerto SERIE.** Adentro hay una pasarela que traduce a
> CANopen. Judit habla serie con esa pasarela; la pasarela aparece en el bus interno
> como el **nodo 30**, el «PC de servicio» del manual.

| Medición | Se leía como | Ahora |
|---|---|---|
| −14.6 V en pin 3 | «raro, contradice el manual» | **RS-232 en reposo. Correcto** |
| actividad en 2 y 3 | evidencia suelta | **el par TX/RX del enlace serie** |
| pin 2 ↔ 7 abierto | «difícil de explicar si es CAN» | **no es CAN. Por eso está abierto** |
| nodo 30 = PC de servicio | «entonces el puerto tiene que ser CAN» | **es cómo se ve la pasarela desde el bus** |

**Ninguna medición estaba mal. El modelo estaba mal.**

### Qué cambia en el plan del viaje

| Punto del plan | Decía | Es |
|---|---|---|
| Herramienta | ESP32 + T132 | **cable FTDI**; el ESP32 queda de respaldo |
| Null-modem | obligatorio (DTE↔DTE) | **no se usa**: el chino conectaba directo |
| Techo de velocidad | 14400, tope del CH340 | **FT232 llega a 3 Mbaud** — el barrido completo por fin es real |
| Las 4 medidas contra negativo de batería | decidían si era CAN | **bajan de prioridad**, la pregunta ya se contestó por otro lado |
| Cable ethernet-a-DB9 (CiA-303) | dato en tensión | **archivado**: es un cable CANopen genérico, no el de Judit |
| Mecánica del conector | no se había visto | el DE-9 está **embutido** entre fusibles: solo entra un capuchón delgado. Por eso había un cable y no una caja |

### Lo que no cambia

- **Validar el FTDI antes de viajar**: jumper pin 2–3 y `probador.py`, leyendo la línea
  **LOOPBACK**, no el veredicto. **Jumper fuera antes de acercarse al equipo.**
- **Solo se escucha. No se transmite.**
- La cadena CAN (ESP32 + TJA1050) **se termina igual**: sirve para el bus interno y para
  el APM+ del nodo 31, que es otro frente.
- Las medidas A1 a A3 con flexómetro siguen siendo lo más valioso del día.
