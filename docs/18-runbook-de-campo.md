# Runbook de campo — el día del puerto

**Escrito el 26-sep-2026, para correrlo en el taller, en la i3 (Windows).**

Este documento es para seguirlo con la máquina enfrente. No explica por qué —
eso está en `docs/15` y `docs/16`. Acá solo va qué se teclea, en qué orden, y
qué se anota.

**Lo que ya no se discute:** el cable es el FTDI DB9→USB que apareció en el
taller. El chino lo confirmó por foto el 25-sep. Va **directo**, sin null-modem
y sin ESP32.

---

## Reglas, antes de tocar nada

- **SOLO SE ESCUCHA.** El script no transmite y deja DTR/RTS en bajo
- **Jumper fuera** antes de acercarse al equipo. Puentear 2 con 3 en el
  montacargas es cortocircuitar dos líneas que maneja el controlador
- **La laptop a batería, desenchufada de la pared.** Laptop en el tomacorriente
  + USB al equipo + masa a la batería = lazo de tierra sobre un bus de 36 V
- No se corta ni un cable. **Nada irreversible**

---

## Paso 0 · Preparar la i3 · 5 min, se puede hacer antes de llegar

```
git pull
py -m pip install pyserial
cd herramientas\serie
py escucha_edr.py --listar
```

El `--listar` tiene que mostrar el FTDI. Si no aparece: es driver, no es el
equipo. Windows normalmente pone el VCP de FTDI solo; si no, se baja de FTDI.

---

## Paso 1 · Validar el cable · 5 min, ANTES de conectarlo al montacargas

Jumper entre el **pin 2 y el pin 3** del DB9 del cable. Después:

```
py probador.py
```

Se lee la línea **LOOPBACK**. **No se lee el veredicto «ESTE SIRVE»** — ese
veredicto solo mira velocidad y paridad, ninguna de las dos toca los pines del
conector. Un cable puede aprobar y fallar loopback: ya pasó con el CH340.

```
□ LOOPBACK pasó       → seguir
□ LOOPBACK falló      → el cable no pasa datos. Nada de lo que siga sirve
```

**QUITAR EL JUMPER Y GUARDARLO APARTE.** Con el jumper puesto no se acerca al
equipo.

---

## Paso 2 · El barrido · ~3 min

Equipo **encendido**. Cable al DE-9 de la tabla de fusibles.

```
py escucha_edr.py --barrido
```

54 combinaciones: 9 velocidades × 6 encuadres. **Primera vez arriba de 14400** —
ese techo era del CH340, no del equipo.

Al final imprime una de dos cosas:

| Sale | Qué significa | Qué sigue |
|---|---|---|
| **HABLÓ** + ranking | el puerto transmite | Paso 3 con la combinación de arriba |
| **SILENCIO EN LAS 54** | nada salió | el propio log imprime la lista de sospechosos, en orden |

El ranking **no** se lee como «el que más bytes da gana». Una velocidad
equivocada puede escupir más basura que la correcta datos buenos. Gana el que
repite estructura: mucho legible, poco bit7, varios valores distintos.

Todo queda en `herramientas\serie\logs\`.

---

## Paso 3 · Confirmar y provocar

Primero clavar la combinación ganadora y ver si repite:

```
py escucha_edr.py --fijo 9600 8N1
```

(cambiando 9600 8N1 por lo que haya ganado). **Se corre dos veces.** Si la
segunda no se parece a la primera, no era la combinación.

Después, la pregunta que de verdad importa:

```
py escucha_edr.py --estimulo 9600 8N1
```

Guía seis pasos y se marca cada uno con ENTER. El log queda con marca de tiempo,
así que después se cruza cada acción contra lo que salió:

```
1. línea base, quieto 30 s      ← ¿habla solo, o solo contesta?
2. girar el timón tope a tope   ← EPS, anda aunque el equipo no ruede
3. subir y bajar las uñas
4. pisar y soltar hombre-presente
5. Settings → Menu → Drive → diagnóstico
6. provocar/leer el código de falla del display
```

**Si el flujo se mueve con una acción y la línea base no**, el puerto es
telemetría viva y `docs/10` se abarata entero: velocidad, ángulo y altura
salen leídas, sin cortar un cable.

### Las fallas son ventaja, no estorbo

A esta máquina la están canibalizando y le falta la válvula de temperatura de
aceite, así que va a mostrar errores. **Eso sirve:** el display da el código y
el log da los bytes del mismo momento. Buscar el código en el flujo es lo que
separa «salió algo» de «entendemos el protocolo».

Anotar el código exacto que muestre el display, con la hora.

---

## Paso 4 · Lo que se cierra ahora o se pierde

Los paneles están abiertos por la canibalización. Esta ventana no se repite.

```
□ Seguir A DÓNDE VA EL MAZO del DE-9 (arnés TE 1-965484-1)
    → al controlador de tracción = es el puerto de servicio, se acabó la duda
    → solo al tablero            = es puerto de display, el bus bueno va más adentro
□ Foto de la etiqueta de cada controlador
□ Foto de la placa de datos (número de serie → configuración por MCF Parts Client)
□ Foto de cualquier OTRO conector que aparezca
```

---

## Paso 5 · Con flexómetro, si sobra tiempo

Sigue siendo lo más valioso del día después del puerto. Detalle en `docs/15`.

```
□ W_MAX, ancho pata a pata          ← nunca se ha medido. Ancla toda la escala lateral
□ XPIV, culo → centro rueda de carga, CON PLOMADA
□ Vueltas de volante tope a tope, contadas a mano
```

El `W_MAX` es **opción de pedido** y toma valores discretos de media pulgada,
así que basta con acercarse y ajustar al valor de tabla. El 1.315 del repo es
un valor válido (51.75").

Las vueltas de volante corrigen el 2.6 del control Obed: el manual dice que de
fábrica son **5.5** (parámetro `0x2414`). Si son 5.5, el simulador tiene el
timón más del doble de rápido que el real.

---

## Al chino, mientras esté cerca

```
□ APM+, por nombre. ¿Lo conoce? ¿Judit se lo mostraba? ¿Lo trae esta máquina?
□ ¿CÓMO SE BORRAN LOS CÓDIGOS DE FALLA?   ← sin esto el equipo queda bloqueado
□ ¿Qué es E2320.01?
```

---

## Qué traer de vuelta

```
1. Los logs de herramientas\serie\logs\   ← commitear o copiar, no dejarlos en la i3
2. Las fotos del mazo del DE-9
3. El número de serie
4. W_MAX y XPIV
5. Lo que dijo el chino del APM+
```

---

## Si algo no calza

La regla del proyecto: **cuando la realidad contradice al cálculo, gana la
realidad.** Un dato raro no revienta el modelo — se anota como dato en tensión
y se sigue con lo que sí se sabe. Y antes de declarar algo imposible, preguntar
si alguien ya lo está haciendo.
