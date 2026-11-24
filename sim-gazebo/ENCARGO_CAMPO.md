# Encargo para el Claude de campo · dejar la sim de Gazebo corriendo en superspeed (24-nov-2026)

**Quién lo corre:** el Claude Code de la **i3** (Windows, usuario `rodm_`), que llega a superspeed por ssh.
**Qué quiere maje:** ver el turno del pasillo **en 3D**, con las marcas ArUco puestas, las cámaras con su campo de visión
real, y las llaves de **odometría** y **ArUco** para correr la secuencia con una, con la otra, con las dos o con ninguna.
Qué es y qué mide: `sim-gazebo/LEEME.md`. **Leelo primero.**

La nube lo armó y lo probó en un contenedor Ubuntu 24.04 **sin pantalla** (Gazebo Harmonic 8, render por software). Lo que
no pudo probar: **una pantalla de verdad, la RTX 4070, y Ubuntu 22.04**. Eso es lo que falta.

No se toca nada del equipo ni del rig. Es solo software.

## 0 · Dónde corre

| Opción | Cuándo |
|---|---|
| **superspeed** (Ubuntu 22.04, la RTX 4070, `ssh rodz@superspeed`, sudo sin contraseña) | **la buena** |
| maquinon por WSL2 (`ssh maquinon`, Ubuntu 22.04) | solo si superspeed no está: la ventana sale en el escritorio de Windows (WSLg), con `lanzar.sh ogre` |
| la i3 | **no** (Windows con Intel UHD). Se usa solo para mandar por ssh |

maquinon y superspeed son el mismo fierro: **nunca están los dos a la vez**. Si `ssh rodz@superspeed` no contesta, pedirle a
maje que arranque desde el SSD (`docs/14`).

## 1 · Traer el repo (en la i3 y en superspeed)

```
cd C:\Users\rodm_\Desktop\tata_repo
git pull origin main
ssh rodz@superspeed "hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader; ls -d ~/tata 2>/dev/null"
```

- Si `~/tata` no existe en superspeed: `ssh rodz@superspeed "git clone https://github.com/Rodzilla-TheCreator/tata.git ~/tata"`
  (el repo es público: no hace falta llave).
- Si existe: `ssh rodz@superspeed "cd ~/tata && git pull origin main"`.
  Si el clon está en otra carpeta (`find ~ -maxdepth 3 -name CLAUDE.md`), usar esa en lo que sigue.

## 2 · Instalar (una vez, ~10 min)

```
ssh rodz@superspeed "cd ~/tata && bash sim-gazebo/instalar.sh"
```

Agrega el repositorio de OSRF, instala `gz-harmonic`, `python3-gz-transport13`, `python3-gz-msgs10`, `python3-tk` y, con
pip `--user`, `opencv-contrib-python-headless<4.11` y `numpy<2`. **No toca ROS** (Harmonic convive con lo que haya).
Tiene que terminar en `listo: gz-transport13 y OpenCV 4.10…` y la versión de Gazebo.

Si falla:

| Error | Qué hacer |
|---|---|
| `gz.transport13 no aparece en ningún python3` | `apt list --installed 2>/dev/null \| grep gz-transport`: si está, ¿hay un venv activo? (`deactivate`). Los bindings de apt van al Python del sistema, `/usr/bin/python3` |
| pip choca con el numpy del sistema | se quedan los de `--user`; probar `python3 -c "import numpy, cv2; print(numpy.__version__, cv2.__version__)"` |
| `cv2.aruco` sin `ArucoDetector` | está ganando el OpenCV 4.5 de apt (`python3-opencv`): ver `python3 -c "import cv2; print(cv2.__file__)"`. Tiene que salir de `~/.local` |

## 3 · Las pruebas sin pantalla (validan la instalación)

```
ssh rodz@superspeed "cd ~/tata/sim-gazebo && python3 nucleo.py --prueba"
ssh rodz@superspeed "cd ~/tata/sim-gazebo && python3 generar_mundo.py && python3 correr.py --prueba-vision"
ssh rodz@superspeed "cd ~/tata/sim-gazebo && python3 correr.py --sin-gui --modo ambos --hasta 90"
```

Lo que dio en la nube (tiene que dar parecido; el ruido cambia un poco con la gráfica):

| Prueba | En la nube |
|---|---|
| `nucleo.py --prueba` | odometría + ArUco: **0 de 24** llegadas fuera de ±4.5 cm, uñas máx 0.4 cm; solo odometría 24 de 24 fuera; a ciegas 24 de 24 |
| `--prueba-vision` | 16 lecturas, error de pose **mediana ~1.9 cm**, máx ~6 cm, rumbo ~0.2° |
| `--sin-gui --modo ambos --hasta 90` | cree vs real ~1.5 cm, uñas ~0.2 cm de lado, cientos de ArUco aceptados |

- Si `--prueba-vision` da **0 lecturas** o se cuelga: probar con el otro motor, `python3 generar_mundo.py --motor ogre` y repetir.
- Si `correr.py` dice que no encuentra `gz`: repetir como sesión de login, con el PATH completo:
  `ssh -t rodz@superspeed "bash -lc '...'"`.

## 4 · Que maje lo vea

**Lo más simple: maje frente a la máquina** (superspeed arrancado), abre una terminal y:

```
~/tata/sim-gazebo/lanzar.sh
```

Desde la i3, con la sesión gráfica de maje abierta en superspeed:

```
ssh rodz@superspeed "cd ~/tata && DISPLAY=:0 XAUTHORITY=/home/rodz/.Xauthority nohup bash sim-gazebo/lanzar.sh > /tmp/gz.log 2>&1 &"
```

(si no abre, `ls -la /home/rodz/.Xauthority /run/user/$(id -u rodz)/` para encontrar el `XAUTHORITY` de la sesión de XFCE.)

Abre **dos ventanas**: Gazebo (la 3D, con las dos cámaras a la derecha) y la consola (START verde, STOP rojo, las llaves
ODOMETRÍA y ARUCO, velocidad ×1 a ×8, **«seguir al equipo»**: la cámara 3D va detrás del equipo, por encima del pasillo).

- Se ve mal, negro o se cae: `lanzar.sh ogre`.
- Va lento: `lanzar.sh --liviano` (el ArUco sale de la geometría con el ruido medido, sin procesar imágenes).
- Las cámaras de la derecha vacías: en cada panel, el botón naranja de recargar y elegir `/tata/cam_lateral` o
  `/tata/cam_trasera` en la lista.

**Qué pedirle a maje que mire:** correr el turno con las cuatro combinaciones de llaves. Con las dos prendidas llega a
las bahías al milímetro; con solo odometría se va corriendo (el fantasma azul, que es donde CREE estar, se separa del
amarillo); con solo ArUco se pierde en la alineación final y en las zonas, donde ninguna cámara ve marcas.

## 5 · Al terminar

Anotar en **`sim-gazebo/resultados_superspeed.md`** (nuevo):

- versiones: `gz sim --versions`, `nvidia-smi` (driver), `python3 -c "import cv2; print(cv2.__version__)"`;
- las tres pruebas de la sección 3, con lo que dieron;
- con pantalla: si abrió, con qué motor (ogre2 / ogre), si se veía fluido, qué dijo maje;
- cualquier cosa que haya habido que cambiar (y por qué).

```
cd C:\Users\rodm_\Desktop\tata_repo
git pull origin main
git add sim-gazebo\resultados_superspeed.md
git commit -m "sim-gazebo: corrida en superspeed"
git push origin main
```

Si hubo que cambiar código para que corra en superspeed, el cambio se hace **en superspeed**, se prueba ahí y se sube desde
ahí (o se copia el diff a la i3). Y en `CLAUDE.md`, la tarea de Gazebo a «✔ Hecha» con una línea.
