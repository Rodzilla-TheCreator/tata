# Runbook — primera prueba del emulador en el equipo

Para seguirlo con la máquina enfrente. Objetivo del día: **ver la rueda directriz dar vuelta
comandada por el emulador**, con la GUI del timón en la laptop. Nada más. No navegación, no CAN.

**Equipo:** un EDR18N2 **parado**. Si es el de Las Palmas (nuestro, ya en cero), se puede ser
más suelto. **Si es un equipo de cliente que vino por mantenimiento, todo reversible, cero
cortes, se restituye idéntico.**

> El emulador ya está **validado en banco** (27-oct): reproduce el sensor real (Vo≈2.47,
> Va≈1.98, radio parejo, estable a comando fijo). Ver `LEEME.md`. Lo que falta es solo enchufar.

---

## Antes de salir (en casa / banco)

- [ ] Sketch **calibrado** flasheado (`emulador_timon.ino`, k/o del 26-oct). Confirmar que a
      comando fijo la salida queda quieta.
- [ ] Laptop con `rueda_timon.py` y el puerto del ESP conocido (COM6). Probar la GUI en modo
      demo o contra el caracterizador: que al girar el timón de pantalla cambien verde/café.
- [ ] **Paro físico** (e-stop) en mano. Caja de herramientas: multímetro, puntas de
      retro-sondeo, gato, el conector/arnés del sensor, cinta.
- [ ] Power bank cargado.

---

## Paso 0 — confirmar que el timón REAL mueve la rueda (línea base)

**Antes de tocar nada nuestro.** Con el equipo encendido y el timón real conectado, girar el
timón a mano y ver que la rueda directriz responde. Esto prueba que node 4 + el motor de
dirección están vivos **hoy**. Si no responde el timón real, el problema no es nuestro y el día
se va en diagnosticar eso, no el emulador.

- [ ] Timón real gira → rueda gira. Anotar sentido: timón a la izquierda → rueda a ___.

---

## Paso 1 — gato y seguridad

- [ ] Rueda directriz **en el aire** (gato). Que pueda girar sin arrastrar el equipo.
- [ ] **Hombre-muerto SIN puentear** todavía. Se puentea solo para la prueba de movimiento, y
      lo hace el Chino/Miguel, no nosotros.
- [ ] Paro físico en mano.

---

## Paso 2 — la medición de grounds (5 min, decide el cableado)

El emulador necesita **una sola tierra**: el **amarillo** del conector (la referencia de node 4
para leer verde/café). Antes de enchufar, con el multímetro resolver dónde está esa tierra:

- [ ] **amarillo del conector ↔ negativo de batería** — ¿mismo punto (~0 V) o hay offset?
- [ ] **amarillo ↔ chasis** — por si el chasis no es el negativo de batería (ya nos mordió).

**Para la prueba de hoy (solo dirección) el TJA/CAN NO se conecta.** No hace falta: la
retroalimentación es la rueda girando y el display. Así que el conflicto de dos tierras
(emulador en amarillo vs. CAN en común-modo del bus) **no aplica hoy**. Se resuelve el día del
kit integrado, con esta misma medición: si amarillo ≈ negativo de batería, todo a una tierra;
si hay offset, aislar el lado CAN (ADM3053 / CA-IS3050G) o correr por separado.

- [ ] TJA **desconectado del bus** hoy. ESP GND = amarillo. Punto.

---

## Paso 3 — conectar el emulador

Orden importa: **el emulador prende y da una salida válida ANTES** de quitar el sensor real.

1. [ ] Power bank → ESP. ESP corriendo, GUI centrada (θ=0 → verde=Vo+Va, café=Vo).
2. [ ] Tap de **+11 V del blanco** al Vcc del LM358 (pin 8). (El blanco queda libre al
       desconectar el sensor real; medir que de verdad da ~11 V antes.)
3. [ ] **Desconectar el sensor real** del conector de node 4.
4. [ ] Conectar al conector: **verde** (señal), **café** (señal), **amarillo** → GND común del
       emulador. Dejar el blanco como fuente de +11 V.
5. [ ] Con las puntas de retro-sondeo, confirmar en el conector: verde ≈ 4.45 V y café ≈ 2.47 V
       con la GUI en θ=0. Si no, parar y revisar antes de que node 4 lo lea.

---

## Paso 4 — leer la reacción de node 4 (sin mover todavía)

- [ ] Encender / que node 4 lea. **¿Tira falla de dirección?** Vigilar la pantalla y, si hay
      forma de escuchar el bus en paralelo (segundo instrumento, no el nuestro), los eventos
      `1.54` / `1.55` / `1.56` y `0x284`.
- [ ] Si **no** hay falla: node 4 aceptó la señal como sensor válido. Buena señal.
- [ ] Si **sí** hay falla: **volver el sensor real de inmediato** (ver regla de abajo) y anotar
      el código antes de que se vaya.

---

## Paso 5 — mover

Solo si node 4 aceptó la señal y con hombre-muerto puenteado por el Chino/Miguel:

- [ ] Girar el timón de la GUI despacio (A/D). θ debe **barrer** — node 4 deriva velocidad del
      cambio de θ; θ quieto = recto.
- [ ] **Ver la rueda girar.** Comparar sentido contra el Paso 0.
- [ ] Centrar (C). La rueda debe volver a recto.

**Si el sentido está invertido:** se corrige en software (signo de θ), no recableando.

---

## Reglas no negociables

- **No se pueden borrar códigos de falla todavía** (licencia de Judit vencida). Si node 4
  late una falla, puede quedar **enganchada** y bloquear la dirección hasta reset. Por eso:
  **ante cualquier falla, el sensor real vuelve al conector de inmediato.** Tenerlo a la mano,
  no enterrado.
- **Paro físico en mano** todo el tiempo.
- **Hombre-muerto se puentea solo para el Paso 5**, y lo hace quien opera el equipo.
- **Equipo de cliente = cero cortes, todo reversible, se restituye idéntico.**
- El emulador va **cableado directo** (sin relé de handoff). En parado de desarrollo está bien.
  Para un equipo en operación habría que poner el selector/handoff de vuelta.

---

## Qué anotar para el repo

- Sentido timón↔rueda (Paso 0 y Paso 5): ¿coincide el signo de θ?
- amarillo ↔ negativo de batería ↔ chasis: los tres voltajes.
- ¿node 4 aceptó la señal sin falla? Si no, el código exacto.
- Voltajes reales en el conector con la GUI en θ=0 y en los extremos.
- Vueltas de timón tope a tope contadas a mano (corrige el 5.5 de `0x2414` / el 2.6 del Obed).
