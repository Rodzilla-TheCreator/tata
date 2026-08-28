# Producto, costos y modelo

Los números vivos están en `producto/TaTa_Escala_EDR18N2.xlsx` — tres hojas: la escala, la placa
de intercepción pieza por pieza, y la ingeniería.

## La escala de madurez

Cinco niveles. **No son cinco calidades: son cinco preguntas distintas.**

| Nivel | Qué contesta | Piezas | Ingeniería en efectivo |
|---|---|---|---|
| **Ingenio** | ¿Puede el software? Percibe, localiza y avisa. No interviene. | $3,273 | $0 |
| **Piloto** | ¿No choca? Interviene dirección y tracción en pasillo real. | **$8,458** | $0 |
| **Serie** | Lo que se le vende al cliente. Sensores propios, bumper. | $11,258 | $0 |
| **Flota** | Tres turnos y capa de seguridad certificable. | $41,169 | $60,250 |
| **Homologado** | Redundancia completa, desatendido con auditoría. | $96,880 | $197,500 |

**Piloto es el que se recomienda.**

Dos cosas que salen de la tabla:

- Entre Piloto y Serie hay poca distancia. **Entre Serie y Flota hay muchísima, y es casi toda
  seguridad certificada.** Llegar a vender algo útil está cerca; operar sin nadie arriba está lejos.
- Hasta Serie el efectivo en ingeniería es **cero**, porque la pone el equipo. Desde Flota ya no:
  entran consultoría de seguridad funcional y aranceles con tercero, y eso **no se puede aportar**.

## El EDR abarata el retrofit

Tres líneas concretas donde la máquina ya trae la función:

- **Cámara en las uñas** de fábrica.
- **Dirección eléctrica** — se intercepta el EPS, no hay que montar servo sobre la columna.
- **Mando electrohidráulico proporcional** para reach, elevación, desplazador e inclinación — no
  hace falta bloque de válvulas propio.

Y frena solo al soltar, así que no hay actuador de freno hasta el nivel Flota.

## Piezas vs ingeniería: no mezclarlas

Error que hubo que corregir: se estaban cobrando como hardware cosas que eran ingeniería.

**Emular las señales cuesta $198 de piezas.** Una sola placa cubre dirección, tracción e
hidráulica: MCU con CAN-FD, transceptores aislados, DAC de 16 bits que emula el mando, ADC que lee
al operador, multiplexores que conmutan operador ↔ robot, relés de doble contacto y drivers de
válvula. Con ensamble y prueba, **$270 de lista**.

Lo caro es **descubrir qué señal es cada cable**, y eso es ingeniería no recurrente: una vez para
todo el modelo, no por unidad.

Mezclar NRE con BOM infla el costo por unidad y hace que el producto parezca peor de lo que es.

## Ingeniería por nivel

| Nivel | Horas | Semanas-persona |
|---|---|---|
| Ingenio | 640 | 16 |
| Piloto | 650 | 16 |
| Serie | 950 | 24 |
| Flota | 1,300 | 33 |
| Homologado | 1,800 | 45 |

**Acumulado a Homologado: 5,340 h = 2.7 años-persona.**

### El comparable de fábrica

[Third Wave Automation](https://www.prnewswire.com/news-releases/third-wave-automation-closes-27-million-series-c-funding-to-scale-autonomous-forklifts-302290953.html)
construye un reach truck autónomo — el mismo formato que el EDR. Levantó **$97 millones desde
2018**. Si el 60% va a nómina de ingeniería son ~$58M, o sea **≈291 años-persona**.

TaTa hasta Homologado es **0.9% de eso**.

La explicación no es que seamos más rápidos: **no estamos construyendo la máquina**. El mástil,
la hidráulica, la tracción, el chasis y la homologación del vehículo base ya existen y ya los pagó
Mitsubishi. Nosotros le agregamos percepción y decisión a algo que ya funciona.

> Cuando alguien paga $90,000–$120,000 por un autónomo de fábrica, no está pagando hardware:
> está pagando la amortización de esos 291 años-persona.

## Comparación de costos para el cliente

Cálculo en `analisis/comparativa_costos.py`. Base: 3 montacargas, 2 turnos, operador certificado
cargado a **$10,309/año** (salario mínimo de manufactura Honduras 2026 L 12,349/mes, operador a
L 18,000 + 27% de cargas, TC 26.61).

| Opción | Inversión | Anual | A 3 años |
|---|---|---|---|
| Seguir con operadores | $0 | $61,853 | $185,560 |
| Autónomos de fábrica | $352,500 | $12,750 | $390,750 |
| Kit TaTa nivel 3 | $97,009 | $12,000 | $133,009 |

**Se paga en 1.9 años.** Un autónomo de fábrica tardaría 7.2.

### La parte honesta

En Honduras la mano de obra es barata y eso **debilita el argumento laboral**. Hay que decirlo
antes de que lo diga el cliente.

| Operación | Ahorro/año | Retorno |
|---|---|---|
| 1 turno | $18,927 | 5.1 años |
| 2 turnos | $49,854 | 1.9 años |
| 3 turnos | $80,781 | 1.2 años |

El mismo kit en EE.UU., con operador a $55,000/año, se paga en **0.3 años**. Aquí tarda seis veces
más. **El retorno de verdad no es el salario:** es exactitud de inventario, daño a rack y producto,
y poder operar turnos que hoy no se cubren por falta de gente.

## El escáner de seguridad y el salto comercial

*Anotado el 27-ago-2026, de la conversación con maje.*

**El valor del escáner certificado es poder decir «lo hacemos con equipo oficial».** No es una
capacidad técnica que falte: es la credencial. Y eso es exactamente lo que le importa a Omar,
que vende certificaciones y respaldo de marca.

El plan comercial que se sigue:

1. Se construye el **Piloto** y se entrega funcionando.
2. Se le agrega encima el escáner industrial de seguridad.
3. Ese agregado es lo que marca el salto de nivel y justifica el salto de precio.
4. **La certificación en sí llega hasta arriba de la escala**, no con el sensor.

### La parte que hay que decir bien

El escáner es **necesario pero no suficiente**. La certificación pide validación de seguridad
funcional, análisis de riesgos, arquitectura de categoría y auditoría de tercero — el sensor es
una pieza de eso, no el trámite completo. `docs/04` ya lo explica.

Entonces al cliente se le vende, literalmente, **el sensor y su función**: hay un escáner
certificado, aislado de la navegación, que detiene el equipo por su cuenta. Eso es cierto y es
vendible.

Lo que **no** se dice es que el equipo esté certificado, ni homologado, ni que cumpla ISO 3691-4
como sistema. Decirlo sería falso mientras no exista la auditoría, y el día que alguien lo
verifique el costo no es comercial. Es la misma disciplina que la regla de no llamarle "freno
automático" a la asistencia de frenado en Ingenio.

### El número de RETHINK

Dos TaTa Piloto por **$20,000**.

| | |
|---|---|
| Piezas, dos unidades | $16,916 |
| Sobre piezas | **$3,084** |
| Ingeniería cobrada | $0 |

Ese margen del 15% sobre piezas es lo que queda, y **toda la ingeniería se está regalando**.
Puede ser la decisión correcta —es el cliente de referencia, y el que produce el caso que se le
enseña al siguiente— pero conviene que esté escrito antes y no descubierto después. El precio
del segundo cliente no tiene por qué parecerse a este.

## La filosofía

> "No lo necesitan. Menos hardware, más software."

Lo dijo el profesor del proyecto de graduación cuando el equipo quería agregarle otra cámara al
robot. Salieron adelante con una Jetson de $250 sobre un PuzzleBot, en un almacén de 170
posiciones, con pick and place en todas, recogiendo del piso y de racks a distintas alturas,
reconstruyendo su ruta para no chocar.

### Pero era una restricción de aula, no doctrina

*Anotado el 27-ago-2026.*

Esa frase era **pedagógica**. El profesor la imponía para obligar a resolver con ingenio lo
que parecía pedir hardware, y funcionó: el equipo de maje fue uno de dos que lo lograron, con
tres personas donde los demás tenían cinco, sobre un kit usado de $250.

**TaTa no es una clase.** No hay nota, no hay que demostrarle nada a nadie, y hay presupuesto.
Si hacen falta dos cámaras se ponen dos, y la justificación es la geometría del giro — no que
alcance el dinero.

Lo que sí sobrevive de la lección, con otra razón: **cada pieza tiene que ganarse el puesto, y
la moneda no son dólares.** Una segunda cámara USB cuesta lo que cuesta un almuerzo; lo que
cuesta de verdad es superficie de integración — otra cosa que calibrar, montar, alimentar,
cablear, diagnosticar y que se puede romper a las dos de la mañana en una bodega de químicos.

Dos cámaras se ganan el puesto porque en el giro de 90° intercambian papeles y nunca queda el
equipo a ciegas. Cinco no se lo ganarían. Ese es el criterio, y no tiene nada que ver con la
austeridad.

Tres patas del argumento:

- **El hardware pone el techo; el software decide cuánto de ese techo alcanzás.** Los proyectos de
  robótica no fracasan por sensores baratos: fracasan por software flojo.
- **Cada sensor es un modo de falla nuevo.** Una calibración más, un cable más, una superficie más
  que se ensucia.
- **El sensor es commodity; el software es el foso.** Cualquiera compra un LiDAR. Lo que Montasa
  sería dueña es del software que lo hace funcionar en pasillos de 3 m con maxicubos.
