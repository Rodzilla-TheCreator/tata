# La máquina objetivo y su geometría

## Mitsubishi EDR18N2

Reach truck pantográfico de **operador parado**, con reach y cámara en las uñas de fábrica.

| | | Fuente |
|---|---|---|
| Capacidad | 1.58 t (3,500 lb) | ficha |
| Largo total con uñas | **2.91 m** | medido en sitio |
| Largo hasta cara de uñas | 1.70 m | derivado |
| Largo de uña | 1.21 m | medido — igual que el maxicubo |
| Ancho | 1.054 m | ficha |
| Entre ejes | 1.562 m | ficha |
| Radio de giro (Wa) | 1.797 m | ficha |
| Techo de protección | 2.413 m | ficha |
| Pantógrafo | 0.61 m | ficha |
| Inclinación | 4° atrás / 3° adelante | ficha |
| Desplazador lateral | ±0.12 m | estándar del equipo |
| Velocidad de catálogo | 12 km/h | ficha |
| **Velocidad de trabajo** | **7.9 km/h** | tope del taller, no de la máquina |

El taller limita a 5–8 km/h por política propia. Ese límite coincide con lo que exige la norma
de seguridad — ver `04-seguridad-y-normativa.md`.

## ¿Cabe el giro en 3.00 m?

Cálculo en `analisis/geometria_giro.py`, figura en `analisis/figuras/geometria_giro_edr.png`.

**Los 2.91 m son con el pantógrafo RECOGIDO.** Extendido son 2.91 + 0.61 = **3.52 m**.

El pivote es el **eje de las ruedas de carga**, a **1.91 m del culo**. Se comprobó por dos
caminos independientes que coinciden:

1. Entre ejes de ficha 1.562 m + rueda motriz a ~0.35 m del culo = 1.91 m
2. Despejándolo de que la máquina **sí trabaja hoy** en pasillos de 3.00 m

| Configuración | Punta a | Barrido | Ast (barrido + holgura) | En 3.00 m |
|---|---|---|---|---|
| Pantógrafo recogido | 2.91 m | 2.80 m | **3.00 m** | cabe |
| Pantógrafo extendido | 3.52 m | 3.41 m | **3.61 m** | faltan 41 cm de barrido |
| Baoli KBE 20 | — | — | 3.82 m | no entra |

### Cómo leerlo bien

**El Ast ya trae adentro la holgura de norma de 20 cm.** El barrido real de la máquina recogida
son **2.80 m**, y los 20 cm que quedan en un pasillo de 3.00 m son justamente esa holgura.

No es margen cero: **es margen normal, sin extra.** Cabe como cabe cualquier reach truck en el
pasillo para el que fue elegido. Los golpes del taller no son culpa de la geometría — son de
manejar rápido en un espacio normal-apretado.

## El pantógrafo es de dos estados, no continuo

Así trabaja el operador y así va a trabajar el kit:

- **En tránsito, siempre recogido.** Con carga o sin carga, sin excepción.
- **Se extiende sólo ya alineado con el maxicubo, y siempre a tope.** Nunca a medias.

Eso convierte el pantógrafo en un actuador de **dos posiciones**, no en un servo. No hace falta
control proporcional ni realimentación de posición: dos finales de carrera alcanzan. Es más
barato y hay menos que sintonizar.

En el simulador está implementado como enclavamiento: con el pantógrafo afuera la máquina no
acelera, y si se mueve se recoge solo.

## La profundidad: no se empuja nada

Hay **riel de seguridad detrás del maxicubo en todos los niveles menos el primero**. En el
primero no hace falta: el peso alcanza para que no se deslice al topar con la torre.

**Pero el riel es respaldo mecánico, no la referencia de trabajo.** Empujar el maxicubo contra
el riel es exactamente lo que hay que evitar: es lo que raya, lo que descuadra y lo que genera
el llamado *error de empuje*.

La profundidad se resuelve sin tocar nada:

1. **El pantógrafo siempre va a su propio tope.** Recorrido fijo, 0.61 m, siempre igual.
2. Entonces la profundidad final la decide **dónde se para el chasis**, no cuánto se empuja.
3. Y esa distancia la da la marca, con precisión de milímetros.

### La secuencia correcta

El maxicubo **nunca se desliza**:

1. Parar el chasis a la distancia que dice la marca
2. Subir el carro unos centímetros **por encima** de la altura de la viga
3. Extender el pantógrafo a tope
4. **Bajar** el maxicubo sobre la viga
5. Recoger el pantógrafo y salir

Se entra en alto, se baja, se recoge. El cubo se apoya, no se arrastra. El error de empuje
desaparece porque no hay empuje.

## Sobre el transductor de presión

Se sacó de los niveles Ingenio y Piloto. No hace falta:

- **¿Hay carga en las uñas?** Lo ve la cámara, y de respaldo la fotocélula de $90.
- **¿Topó contra algo?** No aplica, porque no se empuja contra nada.
- **¿Cuánto pesa?** Eso sí lo da el transductor, pero es dato de inventario y control de
  sobrecarga — útil desde Serie, prescindible antes.

Ahorro: $180 por unidad en los dos primeros niveles.

## Dónde está de verdad la tolerancia

Esto contradice la intuición y es importante:

- **En el pasillo sobran 90 cm a cada lado** del maxicubo. Ahí no hay problema de precisión.
- **La bahía deja 4.5 cm por lado** (bahía 1.29 m, maxicubo 1.20 m). Ese es el requisito real.
- **El desplazador de ±12 cm cubre ese error 2.7 veces**, sin mover el chasis.

**Requisito de precisión lateral para la navegación: ±4.5 cm.** No "alinear perfecto" — quedar
dentro de esa ventana y dejar que el desplazador termine el trabajo. Para eso existe.

## Alturas de trabajo

El operador no busca una altura cualquiera, selecciona un nivel. El kit hace lo mismo.

`piso 0.12` · `1 → 0.70` · `2 → 2.15` · `3 → 3.60` · `4 → 5.05` · `5 → 6.50` m

## ArUco en las uñas: la alineación deja de ser el problema

La cámara de uñas ya viene de fábrica. Poniéndole un ArUco a cada bahía —o a cada maxicubo— se
obtiene **pose relativa de 6 grados de libertad** a corta distancia, que es exactamente lo que
hace falta para el ajuste final.

Cálculo en `analisis/aruco_precision.py`, con error de esquina de 0.4 px:

| Cámara | Marca | Distancia | Lateral | Profundidad | Angular |
|---|---|---|---|---|---|
| USB 5 MP (nivel Ingenio) | 15 cm | 1.2 m | **1.3 mm** | **10.4 mm** | 1.24° |
| USB 5 MP | 20 cm | 1.2 m | 1.3 mm | 7.8 mm | 0.93° |
| Basler dart 5 MP | 20 cm | 1.2 m | 0.4 mm | 2.2 mm | 0.27° |

La profundidad es la peor de las tres porque sale del tamaño aparente de la marca. Aun así
**10 mm con la cámara barata**, contra una tolerancia de bahía de centímetros. Con dos marcas
separadas en la bahía mejora otro tanto: la línea de base entre ellas da escala directa.

**El requisito es ±45 mm.** Hasta la cámara más barata lo cumple por un factor de 28.

Lo que manda no es el lateral sino el **ángulo**, y el ángulo mejora con marcas grandes. Con
15–20 cm de lado sobra en todos los casos.

### Consecuencia para el diseño

La secuencia final queda así, y ninguna parte es difícil:

1. Llegar a la bahía correcta — navegación, la resuelven los marcadores de pasillo
2. Leer el ArUco de la bahía con la cámara de uñas — pose relativa en milímetros
3. Parar el chasis a la distancia que dice la marca
4. Anular el error lateral con el desplazador, sin mover el chasis
5. Subir unos centímetros por encima de la viga
6. Extender el pantógrafo a tope
7. Bajar sobre la viga, recoger y salir

**El ajuste fino es un servo visual sobre un fiducial a corta distancia.** Eso es un problema
resuelto, no una investigación — y no hace falta entrenar ningún modelo: la pose del ArUco sale
por geometría, con solución cerrada.
