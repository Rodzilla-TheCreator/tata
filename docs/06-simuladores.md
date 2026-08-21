# Los dos simuladores

Son cosas distintas y conviene no confundirlas.

| | Web (three.js) | Isaac Sim |
|---|---|---|
| Para qué | Enseñar, demostrar, que el cliente lo maneje | Probar sensores y algoritmos |
| Corre en | Cualquier navegador, celular incluido | RTX con 8 GB+ de VRAM |
| Física | Cinemática y colisiones OBB | PhysX, ray tracing de sensores |
| Estado | Funcionando y desplegado | Escena lista, falta articulación |

## Simulador web

Fuente en `sim-web/`. Se construye con `build.py` y `build_operador.py`, que inyectan three.js,
la geometría y las texturas dentro de un solo HTML autocontenido.

Dos salidas:

- **`Almacen_RETHINK_3D.html`** — completo, con capas, parámetros y sectores.
- **`Manejo_Montacargas.html`** — vista de operador: sólo sectores, modo y referencia. Sin
  parámetros editables. Es el que se le manda a un operador para que juegue.

### Modos de manejo

**Clásico** — W/S acelera, A/D volante como posición, flechas separan las uñas.

**Modo Obed** — llamado así por el operador del taller que propuso el esquema. Carga
automáticamente la ficha del EDR18N2.

| Mando | Función |
|---|---|
| RT | acelerador, analógico |
| LT | freno, analógico y progresivo — le gana al acelerador |
| B | cambia adelante ↔ reversa |
| Palanca izq. ←→ | gira el timón por **velocidad**, no por posición |
| Palanca izq. ↑↓ | sube y baja de nivel, un empujón un nivel |
| Flechas ↑↓ | pantógrafo: a tope / recogido, sólo detenido |
| Flechas ←→ | desplazador lateral ±12 cm |

**El pantógrafo está enclavado.** Es binario — a tope o recogido, nunca a medias. Con el
pantógrafo afuera la máquina no acelera, y si se mueve se recoge solo. Tomar y dejar exige que
esté a tope. Esa es la secuencia real del operador y el simulador la obliga.

**El timón se queda donde lo dejás.** No se autocentra, y tiene tope real de 1.5 vueltas a cada
lado. Cuánto estirás la palanca es a qué velocidad gira. Eso importa: el mando de la máquina real
es un timón con memoria y con tope, no un eje que vuelve solo al centro — da igual si al final se
mueve por CAN o por un motor sobre la columna.

Hay también selector de tracción trasera/delantera e inversión de ejes, para probar esquemas.

### Modo cabina

Sigue en tercera persona, pero aparecen controles táctiles y una ventana con la **cámara frontal**
del montacargas. La carga tapa la cámara cuando las uñas están arriba, igual que en la máquina real.

## Banco de Isaac Sim

Ver `sim-isaac/README_SIM.md` y `README_MULTILIDAR.md`.

`PropuestaIT_RETHINK.usda` es la bodega del sector C: Z-up, metros, con colisión, 10 filas de
rack, 790 maxicubos como PointInstancer y 293 muros reales. Verificada contra el visor web.

### La filosofía del banco

**En simulación los sensores no cuestan dinero, cuestan GPU.** Por eso el banco no simula un nivel
de BOM: simula el conjunto completo y va **apagando sensores hasta que algo se rompe**. El que
rompe la misión es el que hay que comprar.

Regla operativa: **geometría en producción, ruido en scrappy.** Se modela con la resolución del
sensor bueno pero con el ruido del que se va a comprar primero.

### LiDAR disponibles

Vienen de fábrica: Ouster OS0-128 y OS1-64, Hesai XT32, y los genéricos rotativo y 2D.

**No viene el Livox Mid-360**, que es el más barato del BOM y el más caro de simular: tiene patrón
no repetitivo y hay que extraer el patrón real de disparo de una grabación del sensor físico.
Es un proyecto, no un archivo de configuración.

Por eso el primer experimento se hace con el **OS0-128**: es el sensor optimista. Si con él hay
problema, es geometría y no sensor, y nos ahorramos construir el modelo del Livox.
