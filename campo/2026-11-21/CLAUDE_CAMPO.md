# Instrucciones para el Claude Code de campo (i3, usuario rodm_) · 21-nov-2026

Estás en la compu de maje (Windows, `C:\Users\rodm_\Desktop\tata_repo`), con el ESP32 enchufado por USB y
maje en el banco. **Tu trabajo hoy: guiar las 4 pruebas de `LEEME.md` (esta carpeta), una a la vez,
cargar los sketches, y anotar los resultados.** No hay montacargas hoy.

## Cómo trabajar

1. `cd C:\Users\rodm_\Desktop\tata_repo` y `git pull origin main`.
2. Leé `LEEME.md` de esta carpeta entero, y `herramientas/rig/LEEME.md`.
3. Averiguá el puerto del ESP (`arduino-cli board list`, o el Administrador de dispositivos). Hasta ahora
   fue **COM6**.
4. Para cargar: si hay `arduino-cli` (`arduino-cli version`), usá
   `arduino-cli compile --upload -p COM6 --fqbn esp32:esp32:esp32 <carpeta del sketch>` con el core
   **esp32 3.3.12** (con el que compiló `pie.ino` el 19-nov). Si no hay, maje carga con el Arduino IDE.
5. **Una prueba a la vez.** Decile qué hacer y qué tiene que medir, **esperá su número**, anotalo, y
   recién ahí la siguiente. Frases cortas: maje está con las manos ocupadas.
6. Cada prueba tiene un **control**. Si no se hizo el control, la prueba **no pasó**: anotala como
   «sin control».
7. Al terminar cada prueba: los números a `resultados.md` y `git commit` + `git push origin main`.
   Así nada se pierde si se corta algo.

## Reglas

- **No conectes nada al montacargas.** Hoy es banco.
- **No cambies la lógica de seguridad** de `rig.ino` o `pie.ino` (watchdog, rearme, paro, la regla del pie
  ARMADO) sin decírselo a maje y anotarlo. Si algo falla, primero anotá **qué pasó exacto** (los mensajes
  `EV` y `S` del ESP); después, si hace falta, una corrección mínima con su «decía / es».
- **Si `rig.ino` no compila con el core del ESP32**, pegá el error completo en `resultados.md`, corregí lo
  mínimo para que compile y anotalo. La lógica ya está probada en `prueba_host/` (23/23); esa prueba corre
  en Linux (maquinon), no en Windows.
- Lo que no se pueda probar (por ejemplo el SH-C30G en Windows), queda **«pendiente»**, nunca como pasado.
- Si maje se traba o se frustra, **simplificá**: un solo paso, el siguiente número. No le cargues todo de
  una.

## Si el SH-C30G no aparece

- Si sale como **puerto COM**: es slcan → `py herramientas\rig\master_falso_can.py --slcan COMx`.
- Si **no** sale como COM: es candleLight (gs_usb). En Windows pide `pip install python-can gs_usb pyusb`
  y el driver **WinUSB con Zadig**. Si se complica más de 15 min, **dejalo pendiente**: la prueba 4.4 se
  hace en maquinon (Linux, `can0`, directo). El resto de la prueba 4 no lo necesita.
- Antes de usarlo, el **control C0**: óhmetro entre la carcasa del USB y su borne GND. Abierto = aislado.

## Al terminar

- `resultados.md` completo (tabla por prueba: valor medido, ¿pasa?, ¿control hecho?).
- En `CLAUDE.md`, la sección **«▶ Tarea para el Claude de campo (21-nov)»** pasa a **«✔ Hecha»** con una
  línea de resultado (o qué quedó pendiente).
- Commit + push a `main`.
