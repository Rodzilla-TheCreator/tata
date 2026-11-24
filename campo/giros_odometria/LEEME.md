# Giros con solo la odometría, en piso abierto, con tiza (preparado el 24-nov-2026)

**Para el Claude de campo (i3).** maje, en el **EDR18N2 funcional prestado**, con el mismo montaje del teleop del 23-nov
(`herramientas/rig/teleop_wasd.ino` en el ESP, la cadena CAN aislada al DB9, el timón emulado). **maje parado en el
pedal real: el pedal es el paro.** Guiá una prueba a la vez y anotá cada una en `resultados.md` apenas termina.

## Qué se quiere saber

**¿El equipo puede dar las vueltas con solo la odometría?** Concretamente: si se le dice «girá 90°» con la rueda en la
receta, ¿termina donde la odometría cree, al centímetro y al grado? En el pasillo la receta deja **8 cm por lado**. Si
el giro con odometría sola se equivoca menos de **3 cm en el medio del eje y 1° en el rumbo** (1° son 3 cm en el culo),
la vuelta entra sin ver marcas.

Y de paso se miden los cuatro números del modelo que nadie midió directamente. Son los que la sim de Gazebo
(`sim-gazebo/`) **supone** como errores de la odometría:

| Número | Hoy en `percepcion/odometria.py` | Qué prueba lo mide |
|---|---|---|
| dónde está la recta del `0x184` | +1.20° (rueda recta **a ojo**, 23-nov) | **T1** (recta) |
| escala de la marcha `0x188` | 7.30e-4 m/s por unidad (3.19 m de flexómetro; 3.443 contra «~3.4») | **T1** |
| corrimiento de la motriz `e` | 0.325 (motriz ↔ apoyo 0.65 / 2, supone el apoyo simétrico) | **T2, T3** (pivotes) |
| entre ejes × escala, en el giro | 1.688 (flexómetro) | **T2–T5** (cuánto gira por metro de rueda) |

## Lo que lleva

- flexómetro de 5 m o más (mejor 8 m), **tiza** (dos colores si hay), cinta de enmascarar, marcador
- **plomada** (o una tuerca en un hilo), una escuadra
- la i3 con el teleop, el ESP y el cable **fijos** (el 21-nov los cortes fueron el cable flojo)
- alguien que marque y mida (el Chino) mientras maje está en el equipo

## Seguridad, antes de nada

- **Piso abierto, plano, sin rampas ni canaletas**, de una misma superficie. Mínimo **6 × 9 m libres**: 5 m de recta más
  el largo del equipo, y un círculo de **2.5 m de radio** alrededor del eje de carga en los pivotes (el culo barre a
  ~2 m del centro de giro).
- **Nadie a menos de 2.5 m mientras maje esté en el pedal.** Quien marca entra solo con **maje fuera del pedal** (freno
  puesto) y sale antes de que vuelva a subir.
- **Vacío, uñas abajo (a unos cm del piso), pantógrafo retraído, marcha lenta (tortuga).** El slider de marcha bajo.
- La rueda se pone en su ángulo **con el equipo quieto**, y recién ahí se anda.
- El 23-nov la rueda se fue sola de 1° a 35° y volvió, sin objetivo (`teleop_wasd_20261123-131323.log`, sin explicar).
  **Si la rueda se mueve sin que nadie la mande: pie fuera del pedal**, y se anota la hora.
- Es el mismo nivel que el 23-nov (`docs/25`, «movimiento»): manejo normal del equipo, con nuestro mando y el pedal
  real como cadena de paro. **Nada se corta ni se queda conectado al terminar.**

## T0 · Preparación (equipo quieto)

1. En la i3:
   ```
   cd C:\Users\rodm_\Desktop\tata_repo
   git pull origin main
   py herramientas\rig\odometria_log.py --prueba
   ```
   Tiene que decir **PASA**. Si no, no se sigue.
2. **Dos marcas en el equipo, una en cada pata, sobre la línea del eje de carga.** Cinta de enmascarar en la cara de
   afuera de cada pata, a la altura del centro de la rueda de carga (el eje se ve desde el costado). Una cruz con
   marcador, **I** en la pata izquierda (mirando del culo hacia las uñas: el lado del timón) y **D** en la derecha.
   - Si no se ve el eje, poner las cruces en el mismo lugar en las dos patas y medir **cuánto quedan por delante del
     eje** (hacia las uñas). Ese número va como `--adelante` (en cm; negativo si quedan hacia el culo).
3. Medir **I ↔ D** (de cruz a cruz, en el equipo): es el `--ancho`. Anotarlo en `resultados.md`.
4. En la i3, lo que se espera de la receta (para tener la cuenta antes de mover nada):
   ```
   py herramientas\rig\odometria_log.py --objetivo -95.4 90 --ancho <I-D en cm> --retro 7
   ```
5. Abrir el teleop (`py herramientas\rig\teleop_wasd.py COM6`), **ARMAR** con la llave en OFF, subir la llave, esperar
   **OPERACIONAL**. Comprobar que la etiqueta morada «desde la MARCA» cambia al apretar **M**.

## Cómo se hace cada prueba (el ciclo)

1. Equipo quieto. **Rueda al ángulo** con el botón de la prueba. Esperar a que la rueda roja llegue a la verde.
2. **Pie fuera del pedal.** Quien marca baja la plomada desde la cruz **I** y hace una cruz de tiza en el piso: **I1**.
   Lo mismo con **D**: **D1**. Escribir al lado, en el piso, el número de la prueba («T2»).
3. **M** en la i3 (MARCA). La etiqueta queda en cero.
4. maje sube al pedal y anda con **W** (o S) hasta que la etiqueta diga lo de la prueba (giro +90.0, avance +5.000…).
   **No hace falta parar exacto**: lo que el equipo hizo de más o de menos queda en el log. Parar suave.
5. **Pie fuera del pedal.** Cruces **I2** y **D2** desde las mismas marcas del equipo. Anotar lo que dice la etiqueta.
6. **Seis distancias** con el flexómetro, de cruz a cruz en el piso, **dos veces cada una** (si difieren más de 3 mm,
   una tercera):

   | | | |
   |---|---|---|
   | I1 ↔ D1 | I2 ↔ D2 | |
   | I1 ↔ I2 | D1 ↔ D2 | |
   | I1 ↔ D2 | D1 ↔ I2 | |

7. Correr la comparación (la hace el Claude de campo):
   ```
   py herramientas\rig\odometria_log.py herramientas\rig\logs\teleop_wasd_<fecha>.log --marca <n> --tiza I1D1 I2D2 I1I2 D1D2 I1D2 D1I2 [--centro X] [--adelante cm]
   ```
   Las seis en **cm**, en ese orden. El «cierre» tiene que dar **menos de 1 cm**; si no, alguna medida está mal:
   volver a medir antes de mover el equipo.

`n` es el número de la MARCA que se apretó al empezar la prueba (la etiqueta lo dice: «desde la MARCA n»). Sin
argumentos, `odometria_log.py <log>` lista todos los tramos.

## Las pruebas, en este orden

**El orden importa:** el centro de la rueda (T1) cambia el centro de giro 3 cm por grado cerca del tope, así que T2 y
T3 se comparan **con el centro que dio T1** (`--centro`). `odometria_log.py --prueba` tiene un control que lo muestra.

| | Rueda (botón) | Marcha | Hasta que la etiqueta diga | Qué predice el modelo | Qué mide |
|---|---|---|---|---|---|
| **T1a** | **+1.2 recta del modelo** | W | avance **+5.000** | giro 0°, el medio del eje 5 m adelante | la recta del `0x184` y la escala de la marcha |
| **T1b** | **rueda recta (0°)** | W | avance **+5.000** | (con el centro en +1.2) gira ~3.6° y se corre ~15 cm | lo mismo, del otro lado: entre las dos se interpola la recta |
| **T2** | **+78 tope corto** | W | giro **−90.0** | 2.72 m de rueda; el medio del eje se mueve **(+7, −7) cm** | `e` y la escala del giro |
| **T3** | **−100 tope largo** | W | giro **+90.0** | 2.70 m de rueda; el medio del eje se mueve **(−1, −1) cm**: rota casi en el lugar | `e` otra vez (tiene que coincidir con T2) |
| **T4** | **receta −95.4** | primero **S** hasta avance **−0.070**, rueda a −95.4, después **W** | giro **+90.0** | el medio del eje termina en **(+6, +13) cm** | **la receta del pasillo con odometría sola** |
| **T5** | **−100 tope largo** | W | giro **+360.0** (una vuelta entera) | el medio del eje casi quieto | el error del giro, ×4 |
| **T6** | **+30 arco** | W | giro **−45.0** | 2.75 m de rueda; el centro de giro a 2.75 m a la derecha | la escala del ángulo de la rueda (0.01 °/unidad) |

- Si sobra tiempo: **T2, T3 y T4 otra vez**. Que salgan iguales dos veces vale tanto como el número.
- En **T4** la receta es la del pasillo (`analisis/giro_opciones.py`): retroceder 7 cm recto, rueda a −96.6° de modelo
  (−95.4 en el `0x184`), girar 90° sin retroceder. En el pasillo ese giro deja 8 cm por lado.
- **T5:** con el equipo quieto, la tiza da una vuelta entera como «casi 0°»; `odometria_log.py` la desenrolla contra el log.
- **T6** necesita más lugar: el culo barre a ~3.8 m del centro del arco. Si no hay, se salta.
- Con W la rueda en −95.4 / −100 gira **a la izquierda** y en +78 / +30 **a la derecha** (lo dice el signo de la
  tabla). Si gira al revés, **LADO_MOTRIZ está mal**: parar y anotarlo, es lo primero que hay que saber.

## Qué hacer con los números

Lo hace el Claude de campo, en `resultados.md`, con una tabla por prueba (lo que dijo la etiqueta, las seis medidas,
lo que imprimió `odometria_log.py`).

| Si sale… | Quiere decir | Qué se hace |
|---|---|---|
| T1a y T1b dan la recta en el mismo valor (±0.2°) | la recta del `0x184` está ahí | si difiere de +1.20 en más de 0.3°: `CENTRO_184` |
| T1 da la escala de la marcha a menos de 0.5 % de 1 | 7.30e-4 está bien | si no: `M_S_188` × la escala |
| T2 y T3 dan `e` iguales (±2 cm) | el corrimiento de la motriz es ese | si difiere de 0.325 en más de 2 cm: `E_MAG` |
| T2 y T3 dan `e` distintos | algo del modelo falta (¿la rueda patina al pivotar? ¿el tope no es el ángulo que lee?) | anotar, **no** cambiar `E_MAG` |
| T2–T5 dan la escala del giro igual (±0.5 %) y T1 dio la marcha bien | el entre ejes efectivo es 1.688 / esa escala | anotarlo junto al 1.69 del flexómetro |
| T4: el medio del eje a < 3 cm de lo predicho y el giro a < 1° | **la vuelta del pasillo se puede hacer con odometría sola** | — |
| T4 peor que eso | la vuelta necesita ArUco (o una tercera cámara) en la alineación | anotar por cuánto |

**No se borra el camino:** si un número de `percepcion/odometria.py` cambia, la línea vieja queda en el comentario con
*decía / es / qué lo tumbó*, y se cambia **solo si las dos repeticiones coinciden**. Después, correr
`python3 percepcion/prueba_ekf_rueda.py` (tiene que seguir pasando) y avisar que `sim-gazebo/nucleo.py` supone 0.6° de
sesgo y 1.5 % de escala: con los números medidos, esos supuestos se cambian por lo que de verdad quedó de error.

## Al terminar

```
git add herramientas\rig\logs campo\giros_odometria
git commit -m "giros con odometria: T1-T6 con tiza"
git push origin main
```

Y en `CLAUDE.md`, la sección de la tarea a «✔ Hecha» con una línea de resultado.
