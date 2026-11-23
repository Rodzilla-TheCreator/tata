# 23-nov · Diagnóstico de tramas: qué sensor es qué byte

**Para el Claude de campo (i3).** maje está en Las Palmas con el **equipo funcional**. Hoy **solo se
escucha** (`escucha_can.ino`, LISTEN_ONLY) mientras maje usa los **mandos reales** del equipo, y se marca
cada acción. Después, `descifrar.py` dice qué bytes cambiaron con cada una.

> **No es `escucha_edr`:** ese era el instrumento SERIE del puerto, de septiembre (la teoría serie). El
> bus es CAN; lo que va es **`escucha_can.ino` + `grabar_can.py`**.

## Montaje

- El **multipiloto REAL conectado normal, con su CAN** (hoy no va el nodo 2 falso).
- La cadena **aislada** al DB9: CANH → 8, CANL → 3, **GND_bus → negativo de batería** (pin 7 de la ficha
  del multipiloto). **Sin la R3 del TJA** si este equipo da 60 Ω entre 3 y 8 (el 21-nov dio 60).
- **Corregido (maje, 23-nov):** en este equipo el **GND_bus va al pin 2 del DB9**, como funcionó el 21-nov
  (decía: negativo de batería por el pin 7 de la ficha del multipiloto). El multipiloto original enchufado con su CAN.
- Cargar `herramientas/can/escucha_can/` en el ESP. **El ESP y el cable USB fijos** (el 21-nov los cortes
  fueron el cable flojo).

## Grabar

```
cd C:\Users\rodm_\Desktop\tata_repo
git pull origin main
py herramientas\can\grabar_can.py COM6 921600 diagnostico
```

La pantalla muestra **un paso a la vez**, 33 en total. En cada uno:
**Enter = EMPIEZO** → maje hace la acción → **Enter = TERMINÉ**. Entre pasos, **3 s quieto**: es la
referencia contra la que se compara.

| Bloque | Pasos |
|---|---|
| Sin pedal | referencia · N · S · E · W · pito · joystick adelante / atrás / izquierda / derecha · palanca trasera adelante / atrás · timón izquierda · timón derecha · timón centro |
| El pedal | **PISAR pedal** (maje se sube y se queda) · referencia con pedal |
| Con pedal | los mismos 14, **con maje parado en el pedal** |
| Final | **SOLTAR pedal** · referencia final |

**Seguridad, bloque «con pedal»:** con el pie en el pedal, el joystick **mueve el equipo** y los
botones y la palanca **mueven el mástil o las uñas**. **Toques cortos**, a media palanca, área despejada,
uñas abajo. Es manejo normal del equipo con sus mandos; maje es el operador.

Si algo sale mal en un paso (se equivocó de botón), seguir igual y escribir una marca libre
(texto + Enter: «el paso 9 fue a la derecha, no a la izquierda»).

## Después de grabar

```
py herramientas\can\descifrar.py herramientas\can\logs\escucha_equipo_<fecha>.log > campo\2026-11-23\descifrado.txt
git add herramientas\can\logs campo\2026-11-23
git commit -m "23-nov: diagnostico de tramas grabado y descifrado"
git push origin main
```

`descifrar.py` dice, por paso, qué bytes cambiaron (LIMPIO = estaban quietos antes), qué bits, y si
**vuelven** al soltar (mando) o **se quedan** (posición). Al final: lo que solo cambia **con** pedal, y
los **candidatos al bit del pedal** (cambian al pisar y al soltar).

**Lo que buscamos, en orden de importancia:**
1. **El bit del pedal**: para probar el emulador del pedal sin moverse.
2. **El ángulo de la rueda de dirección** (timón izquierda / derecha / centro): para cerrar el lazo del
   timón emulado y para la odometría.
3. **La velocidad de tracción** (joystick con pedal): odometría.
4. Qué hace cada botón con el pedal (N S E W, palanca): el resto del vocabulario del multipiloto.

No interpretes de más: anotá lo que `descifrar.py` dice, y lo que maje vio que pasó en el equipo en cada
paso (qué se movió). La interpretación se hace después, con los dos.
